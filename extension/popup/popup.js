/**
 * Popup script for PingCRM LinkedIn Companion settings.
 */
(function () {
  'use strict';

  const setupSection = document.getElementById('setup-section');
  const statusSection = document.getElementById('status-section');
  const apiUrlInput = document.getElementById('api-url');
  const tokenInput = document.getElementById('token');
  const saveBtn = document.getElementById('save-btn');
  const disconnectBtn = document.getElementById('disconnect-btn');
  const autoSyncToggle = document.getElementById('auto-sync');
  const profileCountEl = document.getElementById('profile-count');
  const messageCountEl = document.getElementById('message-count');
  const lastSyncEl = document.getElementById('last-sync');
  const statusDot = document.getElementById('status-dot');
  const statusText = document.getElementById('status-text');

  async function render() {
    const config = await Storage.getConfig();

    if (config.apiUrl && config.token) {
      setupSection.classList.add('hidden');
      statusSection.classList.remove('hidden');

      profileCountEl.textContent = config.profileCount;
      messageCountEl.textContent = config.messageCount;
      autoSyncToggle.checked = config.autoSync;

      if (config.lastSync) {
        const ago = timeAgo(new Date(config.lastSync));
        lastSyncEl.textContent = `Last sync: ${ago}`;
      } else {
        lastSyncEl.textContent = 'Never synced';
      }

      statusDot.classList.remove('error');
      statusText.textContent = 'Connected';
    } else {
      setupSection.classList.remove('hidden');
      statusSection.classList.add('hidden');

      if (config.apiUrl) {
        apiUrlInput.value = config.apiUrl;
      }
    }
  }

  function timeAgo(date) {
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
    if (seconds < 60) return 'just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }

  saveBtn.addEventListener('click', async () => {
    const apiUrl = apiUrlInput.value.trim();
    const token = tokenInput.value.trim();

    if (!apiUrl || !token) {
      alert('Please fill in both fields.');
      return;
    }

    await Storage.saveConfig({ apiUrl, token });
    await render();
  });

  disconnectBtn.addEventListener('click', async () => {
    await Storage.clearToken();
    await render();
  });

  autoSyncToggle.addEventListener('change', async () => {
    await Storage.setAutoSync(autoSyncToggle.checked);
  });

  // Live updates when storage changes
  chrome.storage.onChanged.addListener((_changes, _area) => {
    render();
  });

  // Initial render
  render();
})();
