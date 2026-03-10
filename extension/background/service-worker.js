/**
 * Service worker for PingCRM LinkedIn Companion.
 * Batches captured profiles and messages, pushes to backend.
 */

importScripts('../lib/storage.js', '../lib/api.js');

const BATCH_DELAY_MS = 3000; // 3-second debounce

let pendingProfiles = [];
let pendingMessages = [];
let batchTimer = null;

function scheduleBatch() {
  if (batchTimer) clearTimeout(batchTimer);
  batchTimer = setTimeout(flushBatch, BATCH_DELAY_MS);
}

async function flushBatch() {
  batchTimer = null;
  const profiles = pendingProfiles.splice(0);
  const messages = pendingMessages.splice(0);

  if (profiles.length === 0 && messages.length === 0) return;

  const configured = await Storage.isConfigured();
  if (!configured) {
    setBadge('!', '#F44336');
    return;
  }

  try {
    const result = await Api.push(profiles, messages);
    const data = result.data || {};

    await Storage.recordSync({
      profilesSynced: (data.contacts_created || 0) + (data.contacts_updated || 0),
      messagesSynced: data.interactions_created || 0,
    });

    setBadge('✓', '#4CAF50');
    // Clear badge after 3 seconds
    setTimeout(() => setBadge('', ''), 3000);
  } catch (e) {
    console.error('[PingCRM] Push failed:', e.message);
    if (e.message === 'AUTH_EXPIRED') {
      setBadge('!', '#F44336');
    } else {
      setBadge('✗', '#FF9800');
      // Retry: put items back
      pendingProfiles.unshift(...profiles);
      pendingMessages.unshift(...messages);
      // Retry after 30 seconds
      setTimeout(scheduleBatch, 30000);
    }
  }
}

function setBadge(text, color) {
  chrome.action.setBadgeText({ text });
  if (color) {
    chrome.action.setBadgeBackgroundColor({ color });
  }
}

// Listen for messages from content scripts
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === 'PROFILE_CAPTURED') {
    pendingProfiles.push(message.data);
    scheduleBatch();
    sendResponse({ ok: true });
  } else if (message.type === 'MESSAGES_CAPTURED') {
    pendingMessages.push(...(Array.isArray(message.data) ? message.data : [message.data]));
    scheduleBatch();
    sendResponse({ ok: true });
  }
  return false;
});

// Show status on install
chrome.runtime.onInstalled.addListener(() => {
  console.log('[PingCRM] LinkedIn Companion installed');
});
