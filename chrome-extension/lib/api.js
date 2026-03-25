/**
 * Fetch wrapper for RealCRM backend API.
 * v2: login() removed (replaced by pairing flow).
 */
const Api = {
  /**
   * Push profiles and/or messages to the backend.
   *
   * @param {Object[]} profiles - Array of profile objects
   * @param {Object[]} messages - Array of message objects
   * @returns {Promise<Object>} Parsed JSON response
   * @throws {Error} "AUTH_EXPIRED" on 401, or "Push failed: <status>" on other errors
   */
  async push(profiles, messages) {
    const config = await Storage.getConfig();
    if (!config.apiUrl || !config.token) {
      throw new Error("Not configured: missing API URL or token");
    }

    const response = await fetch(`${config.apiUrl}/api/v1/linkedin/push`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${config.token}`,
      },
      body: JSON.stringify({ profiles, messages }),
    });

    if (response.status === 401) {
      await Storage.clearToken();
      throw new Error("AUTH_EXPIRED");
    }

    if (!response.ok) {
      throw new Error(`Push failed: ${response.status}`);
    }

    return response.json();
  },
};
