/**
 * Chrome storage wrapper for PingCRM LinkedIn Companion v2.
 *
 * Keys:
 *   token           - Bearer token received on successful pairing
 *   apiUrl          - PingCRM instance base URL (no trailing slash)
 *   watermark       - ISO timestamp of the newest Voyager message processed
 *   cookiesValid    - boolean; false when LinkedIn cookies are missing/expired
 *   _pairingCode    - active pairing code (removed on successful pair)
 *   lastVoyagerSync - ISO timestamp of when the last Voyager sync completed
 *   profileCount    - cumulative number of profiles synced
 *   messageCount    - cumulative number of messages synced
 */
const Storage = {
  async get(keys) {
    return chrome.storage.local.get(keys);
  },

  async set(data) {
    return chrome.storage.local.set(data);
  },

  async getConfig() {
    const {
      token,
      apiUrl,
      watermark,
      cookiesValid,
      _pairingCode,
      lastVoyagerSync,
      profileCount,
      messageCount,
    } = await this.get([
      "token",
      "apiUrl",
      "watermark",
      "cookiesValid",
      "_pairingCode",
      "lastVoyagerSync",
      "profileCount",
      "messageCount",
    ]);

    return {
      token: token || "",
      apiUrl: apiUrl || "",
      watermark: watermark || null,
      cookiesValid: cookiesValid !== false,
      pairingCode: _pairingCode || null,
      lastVoyagerSync: lastVoyagerSync || null,
      profileCount: profileCount || 0,
      messageCount: messageCount || 0,
    };
  },

  async recordSync({ profilesSynced = 0, messagesSynced = 0 }) {
    const { profileCount = 0, messageCount = 0 } = await this.get([
      "profileCount",
      "messageCount",
    ]);
    await this.set({
      lastVoyagerSync: new Date().toISOString(),
      profileCount: profileCount + profilesSynced,
      messageCount: messageCount + messagesSynced,
    });
  },

  async clearToken() {
    await this.set({ token: "" });
  },

  async isConfigured() {
    const { token, apiUrl } = await this.getConfig();
    return Boolean(token && apiUrl);
  },
};
