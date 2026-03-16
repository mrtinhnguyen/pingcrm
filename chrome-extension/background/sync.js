/**
 * Voyager sync orchestrator for PingCRM LinkedIn Companion.
 *
 * Reads LinkedIn session cookies, fetches conversations and messages via the
 * Voyager API, and pushes results to the PingCRM backend.
 *
 * Storage keys used (chrome.storage.local):
 *   watermark        - ISO timestamp of the newest message processed (delta cursor)
 *   lastVoyagerSync  - ISO timestamp of when the last sync completed
 *   nextRetryAt      - ISO timestamp; block syncs until this time (rate-limit backoff)
 *   cookiesValid     - boolean; set to false when AUTH_EXPIRED is received
 */

const SYNC_THROTTLE_MS = 2 * 60 * 60 * 1000; // 2 hours between auto-syncs
const RATE_LIMIT_DELAY_MS = 1000;             // 1 second between Voyager calls
const BACKFILL_WINDOW_MS = 30 * 24 * 60 * 60 * 1000; // 30 days for first-sync full fetch

// ── Cookie helpers ────────────────────────────────────────────────────────────

/**
 * Read all LinkedIn cookies fresh from the browser.
 * Returns { liAt, jsessionid } or throws if required cookies are missing.
 *
 * @returns {Promise<{liAt: string, jsessionid: string}>}
 * @throws {Error} "MISSING_COOKIES" if li_at or JSESSIONID are not found
 */
async function _readLinkedInCookies() {
  const cookies = await chrome.cookies.getAll({ domain: ".linkedin.com" });
  const map = Object.fromEntries(cookies.map(c => [c.name, c.value]));
  const liAt = map["li_at"];
  const jsessionid = map["JSESSIONID"];
  if (!liAt || !jsessionid) throw new Error("MISSING_COOKIES");
  return { liAt, jsessionid };
}

// ── Delay helper ──────────────────────────────────────────────────────────────

function _delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ── Voyager response parsers ──────────────────────────────────────────────────

/**
 * Extract conversations from a Voyager normalized response.
 * Voyager uses an `included` array with $type discriminators.
 *
 * @param {Object} raw - Raw Voyager JSON response
 * @returns {Array<Object>} Conversation objects
 */
function _parseConversations(raw) {
  const included = raw?.included ?? [];
  return included.filter(
    item => item?.$type === "com.linkedin.voyager.messaging.Conversation"
  );
}

/**
 * Extract message events from a Voyager normalized response.
 *
 * @param {Object} raw - Raw Voyager JSON response
 * @returns {Array<Object>} Event objects
 */
function _parseEvents(raw) {
  const included = raw?.included ?? [];
  return included.filter(
    item => item?.$type === "com.linkedin.voyager.messaging.Event"
  );
}

/**
 * Extract participant info from a conversation object.
 * Returns an array of { publicIdentifier, firstName, lastName } objects.
 *
 * @param {Object} conversation - A parsed Voyager conversation object
 * @returns {Array<{publicIdentifier: string, firstName: string, lastName: string}>}
 */
function _parseParticipants(conversation) {
  const participants = conversation?.participants ?? [];
  return participants
    .map(p => {
      const mini = p?.miniProfile ?? p?.com_linkedin_voyager_identity_shared_MiniProfile ?? {};
      return {
        publicIdentifier: mini?.publicIdentifier ?? null,
        firstName: mini?.firstName ?? null,
        lastName: mini?.lastName ?? null,
      };
    })
    .filter(p => p.publicIdentifier);
}

/**
 * Convert a Voyager event into the shape expected by the backend's /linkedin/push.
 *
 * @param {Object} event - A parsed Voyager event object
 * @param {string} conversationUrn - Parent conversation URN
 * @param {string|null} partnerPublicId - The partner's publicIdentifier
 * @returns {Object} Message payload for the backend
 */
function _eventToMessage(event, conversationUrn, partnerPublicId) {
  const body = event?.eventContent?.com_linkedin_voyager_messaging_event_MessageEvent?.attributedBody;
  const text = body?.text ?? event?.eventContent?.body ?? "";
  const createdAt = event?.createdAt ?? null;
  const sender = event?.from?.com_linkedin_voyager_messaging_MessagingMember?.miniProfile;
  const senderPublicId = sender?.publicIdentifier ?? null;

  return {
    conversation_id: conversationUrn,
    profile_id: partnerPublicId,
    direction: senderPublicId === partnerPublicId ? "inbound" : "outbound",
    content_preview: String(text).substring(0, 500),
    timestamp: createdAt ? new Date(createdAt).toISOString() : new Date().toISOString(),
    source: "voyager",
  };
}

// ── Main sync function ────────────────────────────────────────────────────────

/**
 * Run a Voyager sync cycle.
 *
 * @param {string} apiUrl - PingCRM backend base URL
 * @param {string} token  - Bearer token for the backend
 * @param {boolean} [force=false] - Skip throttle check and run immediately
 * @returns {Promise<{
 *   skipped: boolean,
 *   conversations: number,
 *   messages: number,
 *   backfilled: number,
 *   error: string|null
 * }>}
 */
async function runSync(apiUrl, token, force = false) {
  const result = { skipped: false, conversations: 0, messages: 0, backfilled: 0, error: null };

  // ── Throttle check ──
  if (!force) {
    const stored = await chrome.storage.local.get(["lastVoyagerSync", "nextRetryAt"]);

    if (stored.nextRetryAt && Date.now() < new Date(stored.nextRetryAt).getTime()) {
      result.skipped = true;
      return result;
    }

    if (stored.lastVoyagerSync) {
      const elapsed = Date.now() - new Date(stored.lastVoyagerSync).getTime();
      if (elapsed < SYNC_THROTTLE_MS) {
        result.skipped = true;
        return result;
      }
    }
  }

  // ── Read cookies ──
  let liAt, jsessionid;
  try {
    ({ liAt, jsessionid } = await _readLinkedInCookies());
  } catch (e) {
    result.error = e.message;
    await chrome.storage.local.set({ cookiesValid: false });
    return result;
  }

  await chrome.storage.local.set({ cookiesValid: true });

  // ── Determine sync mode (first sync vs delta) ──
  const { watermark } = await chrome.storage.local.get(["watermark"]);
  const isFirstSync = !watermark;
  const cutoffMs = isFirstSync
    ? Date.now() - BACKFILL_WINDOW_MS
    : new Date(watermark).getTime();

  // ── Fetch conversations ──
  let conversationsRaw;
  try {
    conversationsRaw = await voyagerGetConversations(liAt, jsessionid, null);
    await _delay(RATE_LIMIT_DELAY_MS);
  } catch (e) {
    return await _handleSyncError(e, result);
  }

  const conversations = _parseConversations(conversationsRaw);
  result.conversations = conversations.length;

  const allMessages = [];
  let newestTimestamp = watermark ? new Date(watermark).getTime() : 0;

  // ── Process each conversation ──
  for (const conv of conversations) {
    const convUrn = conv?.entityUrn ?? conv?.["*id"] ?? null;
    if (!convUrn) continue;

    const lastActivityAt = conv?.lastActivityAt ?? 0;

    // Delta sync: skip conversations with no new activity
    if (!isFirstSync && lastActivityAt <= cutoffMs) continue;

    const participants = _parseParticipants(conv);
    const partnerPublicId = participants.length > 0 ? participants[0].publicIdentifier : null;

    // For first sync: fetch full events only for recent conversations (within 30 days)
    // For older first-sync conversations: use the lastMessage from the conversation object
    const isRecent = lastActivityAt >= cutoffMs;

    if (!isFirstSync || isRecent) {
      // Fetch full event history for this conversation
      let eventsRaw;
      try {
        eventsRaw = await voyagerGetConversationEvents(liAt, jsessionid, convUrn);
        await _delay(RATE_LIMIT_DELAY_MS);
      } catch (e) {
        if (e.message === "RATE_LIMITED") {
          return await _handleSyncError(e, result);
        }
        if (e.message === "AUTH_EXPIRED") {
          return await _handleSyncError(e, result);
        }
        // Non-fatal error for this conversation — skip and continue
        console.warn("[PingCRM Voyager] Failed to fetch events for", convUrn, e.message);
        continue;
      }

      const events = _parseEvents(eventsRaw);
      for (const event of events) {
        const createdAt = event?.createdAt ?? 0;
        if (!isFirstSync && createdAt <= cutoffMs) continue;

        const msg = _eventToMessage(event, convUrn, partnerPublicId);
        allMessages.push(msg);

        if (createdAt > newestTimestamp) newestTimestamp = createdAt;
      }
    } else {
      // First sync, older conversation: use only the last message preview
      const lastMsg = conv?.lastMessage ?? conv?.lastEvent ?? null;
      if (lastMsg) {
        const previewMsg = _eventToMessage(lastMsg, convUrn, partnerPublicId);
        allMessages.push(previewMsg);
      }
    }
  }

  result.messages = allMessages.length;

  // ── Push to backend ──
  if (allMessages.length > 0) {
    try {
      const pushResp = await fetch(`${apiUrl}/api/v1/linkedin/push`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ profiles: [], messages: allMessages }),
      });

      if (!pushResp.ok) {
        if (pushResp.status === 401) {
          result.error = "AUTH_EXPIRED";
          return result;
        }
        result.error = `PUSH_FAILED:${pushResp.status}`;
        return result;
      }

      const pushData = (await pushResp.json())?.data ?? {};

      // Handle backfill request: fetch profiles for contacts missing data
      const backfillIds = pushData?.backfill_needed ?? [];
      if (backfillIds.length > 0) {
        result.backfilled = await _backfillProfiles(
          backfillIds, liAt, jsessionid, apiUrl, token
        );
      }
    } catch (e) {
      result.error = e.message;
      return result;
    }
  }

  // ── Persist watermark and sync timestamp ──
  const updates = { lastVoyagerSync: new Date().toISOString(), nextRetryAt: null };
  if (newestTimestamp > 0) {
    updates.watermark = new Date(newestTimestamp).toISOString();
  }
  await chrome.storage.local.set(updates);

  return result;
}

// ── Backfill helper ───────────────────────────────────────────────────────────

/**
 * Fetch profiles for LinkedIn public IDs and push them to the backend.
 * Called when the backend signals that certain contacts are missing profile data.
 *
 * @param {string[]} publicIds
 * @param {string} liAt
 * @param {string} jsessionid
 * @param {string} apiUrl
 * @param {string} token
 * @returns {Promise<number>} Number of profiles successfully fetched and pushed
 */
async function _backfillProfiles(publicIds, liAt, jsessionid, apiUrl, token) {
  let backfilled = 0;
  const profiles = [];

  for (const publicId of publicIds) {
    try {
      const raw = await voyagerGetProfile(liAt, jsessionid, publicId);
      await _delay(RATE_LIMIT_DELAY_MS);

      // Extract the first profile from the normalized response
      const profileObj = (raw?.included ?? []).find(
        item => item?.$type === "com.linkedin.voyager.dash.identity.profile.Profile"
          || item?.$type === "com.linkedin.voyager.identity.shared.MiniProfile"
      );

      if (profileObj) {
        profiles.push({
          profile_id: publicId,
          profile_url: `https://www.linkedin.com/in/${publicId}`,
          full_name: [profileObj?.firstName, profileObj?.lastName].filter(Boolean).join(" ") || null,
          headline: profileObj?.headline ?? null,
          company: profileObj?.position?.companyName ?? null,
          location: profileObj?.location?.basicLocation?.countryCode ?? null,
        });
        backfilled++;
      }
    } catch (e) {
      if (e.message === "RATE_LIMITED" || e.message === "AUTH_EXPIRED") break;
      console.warn("[PingCRM Voyager] Backfill failed for", publicId, e.message);
    }
  }

  if (profiles.length > 0) {
    try {
      await fetch(`${apiUrl}/api/v1/linkedin/push`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ profiles, messages: [] }),
      });
    } catch (e) {
      console.warn("[PingCRM Voyager] Backfill push failed:", e.message);
    }
  }

  return backfilled;
}

// ── Error handler ─────────────────────────────────────────────────────────────

/**
 * Handle a Voyager-level error and update storage state accordingly.
 *
 * @param {Error} e
 * @param {Object} result - Mutable result object to annotate
 * @returns {Object} The annotated result
 */
async function _handleSyncError(e, result) {
  result.error = e.message;

  if (e.message === "RATE_LIMITED") {
    const waitMs = (e.retryAfter ?? 900) * 1000;
    const nextRetryAt = new Date(Date.now() + waitMs).toISOString();
    await chrome.storage.local.set({ nextRetryAt });
  } else if (e.message === "AUTH_EXPIRED") {
    await chrome.storage.local.set({ cookiesValid: false });
  }

  return result;
}
