/**
 * Content script for LinkedIn messaging pages (/messaging/*).
 * Passively captures message data when the user views conversations.
 */
(function () {
  'use strict';

  const capturedConversations = new Set(); // per browser session

  function getConversationId() {
    const match = window.location.pathname.match(/\/messaging\/thread\/([^/]+)/);
    return match ? match[1] : null;
  }

  function extractMessages() {
    if (document.visibilityState !== 'visible') return null;

    const conversationId = getConversationId();
    if (!conversationId) return null;
    if (capturedConversations.has(conversationId)) return null;

    // Get conversation partner info
    const partnerNameEl = querySelector('conversationPartnerName');
    const partnerLinkEl = querySelector('conversationPartnerLink');
    if (!partnerNameEl) return null;

    const partnerName = partnerNameEl.textContent.trim();
    let profileId = null;
    if (partnerLinkEl) {
      const href = partnerLinkEl.getAttribute('href') || '';
      const match = href.match(/\/in\/([^/]+)/);
      if (match) profileId = match[1].toLowerCase();
    }

    if (!profileId) return null;

    // Extract visible messages
    const messageEls = querySelectorAll('messageItem');
    const messages = [];
    let currentSender = null;

    for (const msgEl of messageEls) {
      // Check for sender name (appears at start of message group)
      const senderEl = msgEl.querySelector(
        SELECTORS.messageSender.join(', ')
      );
      if (senderEl) {
        currentSender = senderEl.textContent.trim();
      }

      const bodyEl = msgEl.querySelector(
        SELECTORS.messageBody.join(', ')
      );
      const timeEl = msgEl.querySelector(
        SELECTORS.messageTimestamp.join(', ')
      );

      if (bodyEl) {
        const content = bodyEl.textContent.trim();
        if (!content) continue;

        const isOutbound = currentSender === 'You' ||
          (currentSender && currentSender.toLowerCase().includes('you'));

        messages.push({
          profile_id: profileId,
          profile_name: partnerName,
          direction: isOutbound ? 'outbound' : 'inbound',
          content_preview: content.substring(0, 500),
          timestamp: timeEl
            ? timeEl.getAttribute('datetime') || new Date().toISOString()
            : new Date().toISOString(),
          conversation_id: conversationId,
        });
      }
    }

    if (messages.length === 0) return null;
    capturedConversations.add(conversationId);
    return messages;
  }

  function captureAndSend() {
    try {
      const messages = extractMessages();
      if (!messages) return;

      chrome.runtime.sendMessage({
        type: 'MESSAGES_CAPTURED',
        data: messages,
      });
    } catch (e) {
      console.debug('[PingCRM] Message capture error:', e.message);
    }
  }

  // Wait for messages to load before capturing
  function waitForMessages() {
    const conversationId = getConversationId();
    if (!conversationId) return;
    if (capturedConversations.has(conversationId)) return;

    const messageEls = querySelectorAll('messageItem');
    if (messageEls.length > 0) {
      setTimeout(captureAndSend, 1000);
      return;
    }

    const observer = new MutationObserver((_mutations, obs) => {
      const els = querySelectorAll('messageItem');
      if (els.length > 0) {
        obs.disconnect();
        setTimeout(captureAndSend, 1000);
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
    setTimeout(() => observer.disconnect(), 10000);
  }

  // Detect SPA navigation for conversation changes
  let lastUrl = window.location.href;
  const urlObserver = new MutationObserver(() => {
    if (window.location.href !== lastUrl) {
      lastUrl = window.location.href;
      if (window.location.pathname.startsWith('/messaging/')) {
        setTimeout(waitForMessages, 1000);
      }
    }
  });
  urlObserver.observe(document.body, { childList: true, subtree: true });

  // Capture when tab becomes visible
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      waitForMessages();
    }
  });

  // Initial capture
  waitForMessages();
})();
