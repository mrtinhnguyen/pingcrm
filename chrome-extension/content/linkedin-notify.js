/**
 * Minimal content script for LinkedIn pages.
 * Notifies the service worker on every LinkedIn page load
 * so it can refresh cookies and trigger a throttled sync.
 */
try {
  chrome.runtime.sendMessage({ type: "LINKEDIN_PAGE_VISIT" });
} catch (e) {
  // Extension context may not be ready yet
}
