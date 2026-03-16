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

  // PROFILE_CAPTURED — push single profile to backend, then throttled Voyager sync
  if (message.type === "PROFILE_CAPTURED") {
    (async () => {
      const { apiUrl, token } = await chrome.storage.local.get(["apiUrl", "token"]);
      if (!apiUrl || !token) {
        setBadge("!", "#F44336");
        sendResponse({ ok: false, error: "Not paired" });
        return;
      }

      try {
        const response = await fetch(`${apiUrl}/api/v1/linkedin/push`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ profiles: [message.data], messages: [] }),
        });

        if (response.status === 401) {
          await Storage.clearToken();
          sendResponse({ ok: false, error: "AUTH_EXPIRED" });
          return;
        }

        if (!response.ok) {
          sendResponse({ ok: false, error: `Push failed: ${response.status}` });
          return;
        }

        const result = await response.json();
        const data = result.data || {};
        const profilesSynced = (data.contacts_created || 0) + (data.contacts_updated || 0);
        await Storage.recordSync({ profilesSynced, messagesSynced: 0 });

        setBadge("OK", "#4CAF50");
        setTimeout(() => setBadge("", ""), 3000);

        sendResponse({ ok: true, profiles: profilesSynced });

        // Trigger throttled Voyager sync in background (do not await)
        _maybeRunVoyagerSync().catch(e =>
          console.warn("[PingCRM SW] Background Voyager sync failed:", e.message)
        );
      } catch (e) {
        console.error("[PingCRM SW] PROFILE_CAPTURED push failed:", e.message);
        setBadge("X", "#FF9800");
        sendResponse({ ok: false, error: e.message });
      }
    })();
    return true;
  }

  // SYNC_NOW — force Voyager sync (from popup)
  if (message.type === "SYNC_NOW") {
    (async () => {
      const { apiUrl, token } = await chrome.storage.local.get(["apiUrl", "token"]);
      if (!apiUrl || !token) {
        sendResponse({ ok: false, error: "Not paired" });
        return;
      }

      setBadge("...", "#64748b");

      const result = await runSync(apiUrl, token, true);

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
    })();
    return true;
  }

  // DOWNLOAD_AVATAR — fetch LinkedIn CDN image with cookies (unchanged from v1)
  if (message.type === "DOWNLOAD_AVATAR") {
    (async () => {
      try {
        const headers = {};
        try {
          const cookies = await chrome.cookies.getAll({ domain: ".linkedin.com" });
          if (cookies.length) {
            headers["Cookie"] = cookies.map(c => `${c.name}=${c.value}`).join("; ");
          }
        } catch (e) {
          console.debug("[PingCRM SW] Could not get cookies:", e.message);
        }

        const resp = await fetch(message.url, { headers });
        if (!resp.ok) {
          console.debug("[PingCRM SW] Avatar download HTTP", resp.status);
          sendResponse({ data: null });
          return;
        }
        const blob = await resp.blob();
        const reader = new FileReader();
        reader.onloadend = () => sendResponse({ data: reader.result });
        reader.onerror = () => sendResponse({ data: null });
        reader.readAsDataURL(blob);
      } catch (e) {
        console.debug("[PingCRM SW] Avatar download failed:", e.message);
        sendResponse({ data: null });
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

// ── Startup ───────────────────────────────────────────────────────────────────

chrome.runtime.onInstalled.addListener(() => {
  console.log("[PingCRM] LinkedIn Companion v1.0.0 installed");
});
