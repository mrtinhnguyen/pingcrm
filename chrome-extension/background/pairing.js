/**
 * Pairing code generation and polling for RealCRM LinkedIn Companion.
 *
 * Flow:
 *   1. User opens popup and sets their RealCRM instance URL.
 *   2. startPairing() generates a REALCRM-XXXXXX code and starts polling the backend.
 *   3. Backend marks the code as redeemed when the user visits Settings → Extensions.
 *   4. On 200, the token and apiUrl are persisted; polling stops automatically.
 *
 * Code format: "REALCRM-" + 6 chars from an unambiguous alphanumeric charset.
 * Expiry: 10 minutes (backend enforces this; extension auto-regenerates on 410).
 *
 * Storage keys written:
 *   apiUrl   - RealCRM instance URL (set before pairing begins)
 *   token    - Bearer token received on successful pairing
 */

const PAIRING_CHARSET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"; // 31 chars, no O/0/I/1/L
const PAIRING_CODE_LENGTH = 6;
const PAIRING_PREFIX = "REALCRM-";
const PAIRING_POLL_INTERVAL_MS = 3000;   // Poll every 3 seconds
const PAIRING_EXPIRY_MS = 10 * 60 * 1000; // 10 minutes

// Module-level state (survives within the service worker's lifetime)
let _pollIntervalId = null;
let _currentCode = null;
let _codeGeneratedAt = null;

// ── Code generation ───────────────────────────────────────────────────────────

/**
 * Generate a cryptographically random pairing code.
 * Uses crypto.getRandomValues() with rejection sampling to eliminate modulo bias.
 * The charset has 31 characters; we accept only values in [0, 31*8) = [0, 248)
 * so that each character maps to exactly 8 raw byte values.
 *
 * @returns {string} e.g. "REALCRM-K7R2MQ"
 */
function generatePairingCode() {
  const charsetLen = PAIRING_CHARSET.length; // 31
  const maxUnbiased = 256 - (256 % charsetLen); // 248 — highest multiple of 31 within [0,256)
  let code = PAIRING_PREFIX;
  let collected = 0;
  while (collected < PAIRING_CODE_LENGTH) {
    // Generate a fresh batch each time to allow rejection without complex indexing
    const batch = new Uint8Array(PAIRING_CODE_LENGTH * 2);
    crypto.getRandomValues(batch);
    for (let i = 0; i < batch.length && collected < PAIRING_CODE_LENGTH; i++) {
      if (batch[i] < maxUnbiased) {
        code += PAIRING_CHARSET[batch[i] % charsetLen];
        collected++;
      }
      // Values >= maxUnbiased are rejected (bias elimination)
    }
  }
  return code;
}

// ── Storage helpers ───────────────────────────────────────────────────────────

/**
 * Read the stored RealCRM instance URL.
 * Returns null if not yet configured (user must enter URL in popup first).
 *
 * @returns {Promise<string|null>}
 */
async function getStoredApiUrl() {
  const { apiUrl } = await chrome.storage.local.get(["apiUrl"]);
  return apiUrl ? apiUrl.replace(/\/+$/, "") : null;
}

// ── Polling ───────────────────────────────────────────────────────────────────

/**
 * Check a single poll cycle against the backend pairing endpoint.
 * Handles 200 (paired), 404 (pending), 410 (expired), 429 (skip cycle).
 *
 * @param {string} apiUrl - RealCRM backend base URL
 * @param {string} code   - Current pairing code, e.g. "REALCRM-K7R2MQ"
 * @returns {Promise<"paired"|"pending"|"expired"|"rate_limited"|"error">}
 */
async function _pollOnce(apiUrl, code) {
  try {
    const resp = await fetch(
      `${apiUrl}/api/v1/extension/pair?code=${encodeURIComponent(code)}`,
      { method: "GET" }
    );

    if (resp.status === 200) {
      const body = await resp.json();
      const token = body?.data?.token ?? body?.token ?? null;
      const returnedApiUrl = body?.data?.api_url ?? apiUrl;

      if (token) {
        await chrome.storage.local.set({
          token,
          apiUrl: returnedApiUrl.replace(/\/+$/, ""),
        });
      }
      return "paired";
    }

    if (resp.status === 404) return "pending";
    if (resp.status === 410) return "expired";
    if (resp.status === 429) return "rate_limited";

    // Any other non-2xx — log but keep polling
    console.warn("[RealCRM Pairing] Unexpected poll status:", resp.status);
    return "error";
  } catch (e) {
    console.warn("[RealCRM Pairing] Poll network error:", e.message);
    return "error";
  }
}

/**
 * Start the pairing process.
 *
 * Generates a new code, begins polling every 3 seconds.
 * Automatically regenerates the code on expiry (410) or after PAIRING_EXPIRY_MS.
 * Stops and resolves when the backend confirms pairing (200).
 *
 * If no apiUrl is stored yet, throws synchronously — the popup must save the
 * instance URL via chrome.storage.local before calling startPairing().
 *
 * @returns {{code: string, done: Promise<void>}}
 *   code - The initial pairing code to display in the popup.
 *   done - Resolves when pairing completes (token stored).
 */
function startPairing() {
  // Stop any existing poll loop
  stopPolling();

  _currentCode = generatePairingCode();
  _codeGeneratedAt = Date.now();

  // done resolves when pairing succeeds; reject is intentionally not exposed
  // (errors are surfaced via chrome.storage changes the popup can observe).
  let resolveDone;
  const done = new Promise(resolve => { resolveDone = resolve; });

  _pollIntervalId = setInterval(async () => {
    // Auto-regenerate if code has exceeded local expiry window
    if (Date.now() - _codeGeneratedAt >= PAIRING_EXPIRY_MS) {
      _currentCode = generatePairingCode();
      _codeGeneratedAt = Date.now();
      // Notify any listeners (popup may be listening for storage changes)
      await chrome.storage.local.set({ _pairingCode: _currentCode });
      console.log("[RealCRM Pairing] Code regenerated (expiry):", _currentCode);
    }

    const apiUrl = await getStoredApiUrl();
    if (!apiUrl) {
      // No URL yet — wait for the user to enter it
      return;
    }

    const outcome = await _pollOnce(apiUrl, _currentCode);

    if (outcome === "paired") {
      console.log("[RealCRM Pairing] Paired successfully");
      stopPolling();
      await chrome.storage.local.remove(["_pairingCode"]);
      resolveDone();
    } else if (outcome === "expired") {
      // Backend says code is expired — generate a new one immediately
      _currentCode = generatePairingCode();
      _codeGeneratedAt = Date.now();
      await chrome.storage.local.set({ _pairingCode: _currentCode });
      console.log("[RealCRM Pairing] Code regenerated (server 410):", _currentCode);
    }
    // "pending", "rate_limited", "error" — no action, keep polling
  }, PAIRING_POLL_INTERVAL_MS);

  // Persist initial code so the popup can read it even after a service worker restart
  chrome.storage.local.set({ _pairingCode: _currentCode });

  return { code: _currentCode, done };
}

/**
 * Stop the pairing poll interval and clear state.
 * Safe to call multiple times or when no poll is active.
 */
function stopPolling() {
  if (_pollIntervalId !== null) {
    clearInterval(_pollIntervalId);
    _pollIntervalId = null;
  }
  _currentCode = null;
  _codeGeneratedAt = null;
}
