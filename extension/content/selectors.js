/**
 * Centralized DOM selectors for LinkedIn pages.
 * When LinkedIn changes their DOM, only this file needs updating.
 */
const SELECTORS = {
  profileName: [
    'h1.text-heading-xlarge',
    '[data-anonymize="person-name"]',
    '.pv-text-details__left-panel h1',
    'section.pv-top-card h1',
  ],
  headline: [
    '.text-body-medium[data-anonymize="headline"]',
    '.pv-text-details__left-panel .text-body-medium',
    'section.pv-top-card .text-body-medium',
  ],
  company: [
    '[data-anonymize="company-name"]',
    'div[aria-label="Current company"] span',
    '.pv-text-details__right-panel .inline-show-more-text',
  ],
  location: [
    '.text-body-small[data-anonymize="location"]',
    '.pv-text-details__left-panel .pb2 .text-body-small',
    'section.pv-top-card .text-body-small.t-black--light',
  ],
  about: [
    '#about ~ .display-flex .inline-show-more-text',
    'section.pv-about-section .pv-about__summary-text',
    '[data-anonymize="person-summary"]',
  ],
  avatarUrl: [
    'img.pv-top-card-profile-picture__image--show',
    '.pv-top-card__photo img',
    'img[data-anonymize="headshot-photo"]',
  ],
  // Messaging selectors
  conversationPartnerName: [
    'h2.msg-entity-lockup__entity-title',
    '.msg-thread__link-to-profile',
    '.msg-conversation-card__participant-names',
  ],
  conversationPartnerLink: [
    'a.msg-thread__link-to-profile',
    '.msg-entity-lockup__entity-title a',
  ],
  messageItem: [
    '.msg-s-message-list__event',
    '.msg-s-event-listitem',
  ],
  messageSender: [
    '.msg-s-message-group__name',
    '.msg-s-event-listitem__link span.visually-hidden',
  ],
  messageBody: [
    '.msg-s-event-listitem__body',
    '.msg-s-event__content p',
  ],
  messageTimestamp: [
    'time.msg-s-message-list__time-heading',
    '.msg-s-message-group__timestamp',
  ],
};

/**
 * Query the DOM using fallback selectors.
 * @param {string} key - Key from SELECTORS
 * @returns {Element|null}
 */
function querySelector(key) {
  const selectors = SELECTORS[key];
  if (!selectors) return null;
  for (const sel of selectors) {
    const el = document.querySelector(sel);
    if (el) return el;
  }
  return null;
}

/**
 * Query all matching elements using fallback selectors.
 * @param {string} key - Key from SELECTORS
 * @returns {Element[]}
 */
function querySelectorAll(key) {
  const selectors = SELECTORS[key];
  if (!selectors) return [];
  for (const sel of selectors) {
    const els = document.querySelectorAll(sel);
    if (els.length > 0) return Array.from(els);
  }
  return [];
}
