/**
 * LinkedIn Voyager API client for Chrome extension service worker.
 * All calls happen from the user's browser — cookies never leave.
 */

const VOYAGER_BASE = "https://www.linkedin.com/voyager/api";
// Reserved for future schema-version negotiation with LinkedIn's API versioning.
// eslint-disable-next-line no-unused-vars
const VOYAGER_SCHEMA_VERSION = "2026-03-v1";

// liAt is passed for API symmetry (callers already have it); the browser sends
// it automatically via credentials:"include". jsessionid doubles as the CSRF token.
// eslint-disable-next-line no-unused-vars
function _voyagerHeaders(liAt, jsessionid) {
  return {
    "Csrf-Token": jsessionid.replace(/"/g, ""),
    "X-Restli-Protocol-Version": "2.0.0",
    "Accept": "application/vnd.linkedin.normalized+json+2.1",
  };
}

/**
 * Core fetch wrapper for Voyager endpoints.
 *
 * @param {string} path - API path, e.g. "/messaging/conversations"
 * @param {string} liAt - Value of the li_at cookie (session token)
 * @param {string} jsessionid - Value of the JSESSIONID cookie (CSRF token)
 * @param {Object} [params] - Query string parameters
 * @returns {Promise<Object>} Parsed JSON response
 * @throws {Error} "RATE_LIMITED" (with .retryAfter), "AUTH_EXPIRED", or "VOYAGER_ERROR:<status>"
 */
async function voyagerFetch(path, liAt, jsessionid, params = {}) {
  const url = new URL(VOYAGER_BASE + path);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined) url.searchParams.set(k, String(v));
  });

  const resp = await fetch(url.toString(), {
    headers: _voyagerHeaders(liAt, jsessionid),
    credentials: "include",
  });

  if (resp.status === 429) {
    const error = new Error("RATE_LIMITED");
    error.retryAfter = parseInt(resp.headers.get("Retry-After") || "900", 10);
    throw error;
  }
  if (resp.status === 401 || resp.status === 403) throw new Error("AUTH_EXPIRED");
  if (!resp.ok) throw new Error(`VOYAGER_ERROR:${resp.status}`);

  return resp.json();
}

/**
 * Fetch conversation list. Paginate by passing `createdBefore` timestamp.
 *
 * @param {string} liAt
 * @param {string} jsessionid
 * @param {number|null} [createdBefore] - Unix ms timestamp for pagination cursor
 * @returns {Promise<Object>} Normalized Voyager response
 */
async function voyagerGetConversations(liAt, jsessionid, createdBefore = null) {
  const params = { keyVersion: "LEGACY_INBOX" };
  if (createdBefore) params.createdBefore = createdBefore;
  return voyagerFetch("/messaging/conversations", liAt, jsessionid, params);
}

/**
 * Fetch message events for a specific conversation.
 *
 * @param {string} liAt
 * @param {string} jsessionid
 * @param {string} conversationUrn - e.g. "urn:li:fs_conversation:2-xxx"
 * @returns {Promise<Object>} Normalized Voyager response
 */
async function voyagerGetConversationEvents(liAt, jsessionid, conversationUrn) {
  const encoded = encodeURIComponent(conversationUrn);
  return voyagerFetch(`/messaging/conversations/${encoded}/events`, liAt, jsessionid);
}

/**
 * Fetch a LinkedIn profile by public identifier (slug).
 *
 * @param {string} liAt
 * @param {string} jsessionid
 * @param {string} publicId - LinkedIn public profile slug, e.g. "john-doe-123"
 * @returns {Promise<Object>} Normalized Voyager response
 */
async function voyagerGetProfile(liAt, jsessionid, publicId) {
  return voyagerFetch("/identity/dash/profiles", liAt, jsessionid, {
    q: "memberIdentity",
    memberIdentity: publicId,
  });
}
