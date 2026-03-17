/**
 * Service worker for PingCRM LinkedIn Companion v2.
 * Message router — delegates to imported modules.
 *
 * importScripts loads modules synchronously at service worker startup.
 * Each module exposes its public functions as globals (no ES module syntax).
 */

importScripts("../lib/storage.js", "voyager-client.js", "sync.js", "pairing.js");

// ── Badge helper ──────────────────────────────────────────────────────────────

function setBadge(text, color) {
  chrome.action.setBadgeText({ text });
  if (color) {
    chrome.action.setBadgeBackgroundColor({ color });
  }
}

// ── Throttle state for post-profile-capture Voyager sync ─────────────────────

let _lastProfileSyncAt = 0;
const PROFILE_SYNC_THROTTLE_MS = 5 * 60 * 1000; // 5 minutes

async function _maybeRunVoyagerSync() {
  if (Date.now() - _lastProfileSyncAt < PROFILE_SYNC_THROTTLE_MS) return;
  _lastProfileSyncAt = Date.now();

  const { apiUrl, token } = await chrome.storage.local.get(["apiUrl", "token"]);
  if (!apiUrl || !token) return;

  const result = await runSync(apiUrl, token, false);
  if (result.skipped) return;

  if (result.error) {
    console.warn("[PingCRM SW] Post-capture Voyager sync error:", result.error);
    return;
  }

  await Storage.recordSync({
    profilesSynced: result.backfilled,
    messagesSynced: result.messages,
  });

  setBadge("OK", "#4CAF50");
  setTimeout(() => setBadge("", ""), 3000);
}

// ── Message router ────────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {

  // LINKEDIN_PAGE_VISIT — user visited any LinkedIn page, refresh cookies
  if (message.type === "LINKEDIN_PAGE_VISIT") {
    (async () => {
      try {
        const cookies = await chrome.cookies.getAll({ domain: ".linkedin.com" });
        const liAt = cookies.find(c => c.name === "li_at")?.value;
        const jsid = cookies.find(c => c.name === "JSESSIONID")?.value;
        const valid = !!(liAt && jsid);
        await chrome.storage.local.set({ cookiesValid: valid });
        console.log("[PingCRM SW] Cookie refresh:", valid ? "valid" : "missing", "li_at:", !!liAt, "JSESSIONID:", !!jsid);

        if (valid) {
          // Trigger throttled sync in background
          _maybeRunVoyagerSync().catch(e =>
            console.warn("[PingCRM SW] Auto-sync after page visit failed:", e.message)
          );
        }
      } catch (e) {
        console.warn("[PingCRM SW] Cookie refresh failed:", e.message);
      }
      sendResponse({ ok: true });
    })();
    return true;
  }

  // SYNC_NOW — force Voyager sync (from popup)
  if (message.type === "SYNC_NOW") {
    (async () => {
      try {
        const { apiUrl, token } = await chrome.storage.local.get(["apiUrl", "token"]);
        if (!apiUrl || !token) {
          sendResponse({ ok: false, error: "Not paired" });
          return;
        }

        setBadge("...", "#64748b");
        console.log("[SW] SYNC_NOW starting...");

        const result = await runSync(apiUrl, token, true);
        console.log("[SW] SYNC_NOW result:", JSON.stringify(result).substring(0, 200));

        if (result.error) {
          setBadge("X", "#FF9800");
          sendResponse({ ok: false, error: result.error });
          return;
        }

        await Storage.recordSync({
          profilesSynced: result.backfilled,
          messagesSynced: result.messages,
        });

        setBadge("OK", "#4CAF50");
        setTimeout(() => setBadge("", ""), 3000);

        sendResponse({
          ok: true,
          conversations: result.conversations,
          messages: result.messages,
          backfilled: result.backfilled,
        });

        // Run backfill in the background after responding to popup
        _runPendingBackfill().catch(e =>
          console.warn("[SW] Background backfill failed:", e.message)
        );
      } catch (e) {
        console.error("[SW] SYNC_NOW crashed:", e.message, e.stack);
        setBadge("X", "#FF9800");
        sendResponse({ ok: false, error: e.message });
      }
    })();
    return true;
  }

  // START_PAIRING — generate code, start polling, return code to popup
  if (message.type === "START_PAIRING") {
    (async () => {
      const apiUrl = (message.apiUrl || "").replace(/\/+$/, "");
      if (!apiUrl) {
        sendResponse({ ok: false, error: "Instance URL is required" });
        return;
      }

      // Save the apiUrl so pairing.js polling can read it
      await chrome.storage.local.set({ apiUrl });

      const { code } = startPairing();
      sendResponse({ ok: true, code });
    })();
    return true;
  }

  // DISCONNECT — clear storage and notify backend
  if (message.type === "DISCONNECT") {
    (async () => {
      stopPolling();

      const { apiUrl, token } = await chrome.storage.local.get(["apiUrl", "token"]);

      // Best-effort DELETE — do not block on response
      if (apiUrl && token) {
        fetch(`${apiUrl}/api/v1/extension/pair`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }).catch(e => console.debug("[PingCRM SW] Disconnect notify failed:", e.message));
      }

      await chrome.storage.local.clear();
      setBadge("", "");
      sendResponse({ ok: true });
    })();
    return true;
  }

  return false;
});

// ── Pending backfill processor ────────────────────────────────────────────────

async function _runPendingBackfill() {
  const { _pendingBackfill, apiUrl, token } = await chrome.storage.local.get([
    "_pendingBackfill", "apiUrl", "token",
  ]);
  if (!_pendingBackfill || _pendingBackfill.length === 0 || !apiUrl || !token) return;

  // Read cookies fresh
  const cookies = await chrome.cookies.getAll({ domain: ".linkedin.com" });
  const liAt = cookies.find(c => c.name === "li_at")?.value;
  const jsid = cookies.find(c => c.name === "JSESSIONID")?.value;
  if (!liAt || !jsid) return;

  console.log("[SW] Running pending backfill for", _pendingBackfill.length, "profiles");

  // Process one at a time to stay within SW lifetime
  const remaining = [..._pendingBackfill];
  let processed = 0;

  for (const item of remaining.splice(0, 10)) { // max 10 per run
    const publicId = item.linkedin_profile_id;
    if (!publicId) continue;
    // Skip URN member IDs (start with ACo or aco) — they won't work with the profile endpoint
    if (/^[Aa][Cc][Oo]/i.test(publicId)) {
      console.log("[Backfill] Skipping URN member ID:", publicId);
      continue;
    }
    try {
      console.log("[Backfill] Fetching:", publicId);
      const raw = await voyagerGetProfile(liAt, jsid, publicId);
      console.log("[Backfill] Got response for:", publicId);

      const profileObj = (raw?.included ?? []).find(
        i => i?.$type?.includes("Profile") || i?.$type?.includes("MiniProfile")
      );
      if (!profileObj) {
        console.log("[Backfill] No profile object in response for:", publicId);
        continue;
      }

      // Extract avatar
      let avatarUrl = null;
      const artifacts = profileObj?.profilePicture?.displayImageReference?.vectorImage?.artifacts ?? [];
      if (artifacts.length > 0) {
        const largest = artifacts[artifacts.length - 1];
        const rootUrl = profileObj?.profilePicture?.displayImageReference?.vectorImage?.rootUrl ?? "";
        if (rootUrl && largest?.fileIdentifyingUrlPathSegment) {
          avatarUrl = rootUrl + largest.fileIdentifyingUrlPathSegment;
        }
      }

      // Push profile to backend
      await fetch(`${apiUrl}/api/v1/linkedin/push`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          profiles: [{
            profile_id: publicId,
            profile_url: `https://www.linkedin.com/in/${publicId}`,
            full_name: [profileObj?.firstName, profileObj?.lastName].filter(Boolean).join(" ") || null,
            headline: profileObj?.headline ?? null,
            location: profileObj?.geoLocationName ?? null,
            avatar_url: avatarUrl,
          }],
          messages: [],
        }),
      });
      console.log("[Backfill] Pushed profile for:", publicId, "avatar:", !!avatarUrl);
      processed++;
    } catch (e) {
      // Only stop on rate limiting — individual profile 401/403/404 are expected for bad IDs
      if (e.message === "RATE_LIMITED") {
        console.warn("[Backfill] Rate limited, stopping");
        break;
      }
      console.warn("[Backfill] Failed for:", publicId, e.message);
    }
  }

  // Save remaining for next run
  if (remaining.length > 0) {
    await chrome.storage.local.set({ _pendingBackfill: remaining });
    console.log("[Backfill]", remaining.length, "remaining for next sync");
  } else {
    await chrome.storage.local.remove("_pendingBackfill");
    console.log("[Backfill] All done,", processed, "profiles pushed");
  }

  if (processed > 0) {
    await Storage.recordSync({ profilesSynced: processed, messagesSynced: 0 });
  }
}

// ── Startup ───────────────────────────────────────────────────────────────────

chrome.runtime.onInstalled.addListener(() => {
  const manifest = chrome.runtime.getManifest();
  console.log(`[PingCRM] LinkedIn Companion v${manifest.version} installed`);
});
