/**
 * Fetch wrapper for PingCRM backend API.
 */
const Api = {
  async push(profiles, messages) {
    const config = await Storage.getConfig();
    if (!config.apiUrl || !config.token) {
      throw new Error('Not configured: missing API URL or token');
    }

    const response = await fetch(`${config.apiUrl}/api/v1/linkedin/push`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${config.token}`,
      },
      body: JSON.stringify({ profiles, messages }),
    });

    if (response.status === 401) {
      await Storage.clearToken();
      throw new Error('AUTH_EXPIRED');
    }

    if (!response.ok) {
      throw new Error(`Push failed: ${response.status}`);
    }

    return response.json();
  },
};
