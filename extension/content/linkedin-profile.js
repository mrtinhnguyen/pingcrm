/**
 * Content script for LinkedIn profile pages (/in/*).
 * Passively captures profile data when the user browses profiles.
 */
(function () {
  'use strict';

  const DEBOUNCE_MS = 5 * 60 * 1000; // 5 minutes per profile
  const recentCaptures = new Map(); // profile_id -> timestamp

  function getProfileId() {
    const path = window.location.pathname;
    const match = path.match(/^\/in\/([^/]+)/);
    return match ? match[1].toLowerCase() : null;
  }

  function extractProfile() {
    const profileId = getProfileId();
    if (!profileId) return null;

    const nameEl = querySelector('profileName');
    if (!nameEl) return null;

    const name = nameEl.textContent.trim();
    if (!name) return null;

    const headlineEl = querySelector('headline');
    const companyEl = querySelector('company');
    const locationEl = querySelector('location');
    const aboutEl = querySelector('about');
    const avatarEl = querySelector('avatarUrl');

    return {
      profile_id: profileId,
      profile_url: `https://www.linkedin.com/in/${profileId}`,
      full_name: name,
      headline: headlineEl ? headlineEl.textContent.trim() : null,
      company: companyEl ? companyEl.textContent.trim() : null,
      location: locationEl ? locationEl.textContent.trim() : null,
      about: aboutEl ? aboutEl.textContent.trim() : null,
      avatar_url: avatarEl ? avatarEl.src : null,
    };
  }

  function shouldCapture(profileId) {
    const lastCapture = recentCaptures.get(profileId);
    if (lastCapture && Date.now() - lastCapture < DEBOUNCE_MS) {
      return false;
    }
    return true;
  }

  function captureAndSend() {
    try {
      const profile = extractProfile();
      if (!profile) return;
      if (!shouldCapture(profile.profile_id)) return;

      recentCaptures.set(profile.profile_id, Date.now());
      chrome.runtime.sendMessage({
        type: 'PROFILE_CAPTURED',
        data: profile,
      });
    } catch (e) {
      console.debug('[PingCRM] Profile capture error:', e.message);
    }
  }

  // Wait for profile content to load, then capture
  function waitForProfile() {
    const nameEl = querySelector('profileName');
    if (nameEl) {
      captureAndSend();
      return;
    }

    const observer = new MutationObserver((_mutations, obs) => {
      const el = querySelector('profileName');
      if (el) {
        obs.disconnect();
        // Small delay to let other fields render
        setTimeout(captureAndSend, 500);
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });

    // Timeout after 10 seconds
    setTimeout(() => observer.disconnect(), 10000);
  }

  // Detect SPA navigation (LinkedIn is a SPA)
  let lastUrl = window.location.href;
  const urlObserver = new MutationObserver(() => {
    if (window.location.href !== lastUrl) {
      lastUrl = window.location.href;
      if (window.location.pathname.startsWith('/in/')) {
        setTimeout(waitForProfile, 1000);
      }
    }
  });
  urlObserver.observe(document.body, { childList: true, subtree: true });

  // Initial capture
  waitForProfile();
})();
