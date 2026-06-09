// Popup UI controller
document.addEventListener('DOMContentLoaded', () => {
  const loginTab = document.getElementById('tab-login');
  const registerTab = document.getElementById('tab-register');
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  const authMsg = document.getElementById('auth-msg');
  const accountBar = document.getElementById('account-bar');
  const accountEmail = document.getElementById('account-email');
  const logoutBtn = document.getElementById('logout-btn');
  const profileBtn = document.getElementById('profile-btn');
  const accountDetails = document.getElementById('account-details');
  const accountUserId = document.getElementById('account-userid');
  const accountEmailDetail = document.getElementById('account-email-detail');
  const authTitle = document.querySelector('.auth-title');
  
  chrome.storage.local.get(['last_auto_open_ts']).then(({ last_auto_open_ts }) => {
    if (last_auto_open_ts && (Date.now() - last_auto_open_ts) < 8000) {
      setTimeout(() => {
        window.close();
      }, 5000);
    }
  });

  function switchTab(tab) {
    if (tab === 'login') {
      loginTab.classList.add('active');
      registerTab.classList.remove('active');
      loginForm.classList.remove('hidden');
      registerForm.classList.add('hidden');
    } else {
      registerTab.classList.add('active');
      loginTab.classList.remove('active');
      registerForm.classList.remove('hidden');
      loginForm.classList.add('hidden');
    }
  }

  if (loginTab) loginTab.addEventListener('click', () => switchTab('login'));
  if (registerTab) registerTab.addEventListener('click', () => switchTab('register'));
  
  async function updateAuthUI() {
    const { user_id, email } = await chrome.storage.local.get(['user_id', 'email']);
    if (user_id && email) {
      accountBar.classList.remove('hidden');
      accountEmail.textContent = email;
      accountUserId.textContent = user_id;
      accountEmailDetail.textContent = email;
      document.querySelector('.tabs').classList.add('hidden');
      loginForm.classList.add('hidden');
      registerForm.classList.add('hidden');
      if (authTitle) authTitle.classList.add('hidden');
    } else {
      accountBar.classList.add('hidden');
      document.querySelector('.tabs').classList.remove('hidden');
      switchTab('login');
      if (authTitle) authTitle.classList.remove('hidden');
    }
  }

  const loginBtn = document.getElementById('login-btn');
  if (loginBtn) {
    loginBtn.addEventListener('click', async () => {
      const email = document.getElementById('login-email').value.trim();
      const password = document.getElementById('login-password').value.trim();
      authMsg.textContent = '';
      if (!email || !password) {
        authMsg.textContent = 'Enter email and password';
        return;
      }
      try {
        const res = await fetch('http://localhost:8000/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        if (!res.ok) {
          authMsg.textContent = 'Login failed';
          return;
        }
        const data = await res.json();
        await chrome.storage.local.set({ user_id: data.user_id, email: data.email });
        authMsg.textContent = 'Logged in';
        updateAuthUI();
        chrome.runtime.sendMessage({ action: 'recheck' }, () => {});
        setTimeout(loadStatus, 200);
      } catch (e) {
        authMsg.textContent = 'Login error';
      }
    });
  }

  const registerBtn = document.getElementById('register-btn');
  if (registerBtn) {
    registerBtn.addEventListener('click', async () => {
      const email = document.getElementById('register-email').value.trim();
      const password = document.getElementById('register-password').value.trim();
      authMsg.textContent = '';
      if (!email || !password || password.length < 8) {
        authMsg.textContent = 'Use a valid email and 8+ char password';
        return;
      }
      try {
        const res = await fetch('http://localhost:8000/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        if (!res.ok) {
          authMsg.textContent = 'Register failed';
          return;
        }
        const data = await res.json();
        await chrome.storage.local.set({ user_id: data.user_id, email: data.email });
        authMsg.textContent = 'Registered';
        updateAuthUI();
        chrome.runtime.sendMessage({ action: 'recheck' }, () => {});
        setTimeout(loadStatus, 200);
      } catch (e) {
        authMsg.textContent = 'Register error';
      }
    });
  }
  
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      await chrome.storage.local.remove(['user_id','email']);
      authMsg.textContent = 'Logged out';
      updateAuthUI();
      setTimeout(loadStatus, 200);
    });
  }
  
  if (profileBtn) {
    profileBtn.addEventListener('click', () => {
      accountDetails.classList.toggle('hidden');
    });
  }

  const flagBtn = document.getElementById('flag-btn');
  const recheckBtn = document.getElementById('recheck-btn');
  const statusCard = document.getElementById('status-section');
  if (flagBtn) {
    flagBtn.addEventListener('click', async () => {
      const obj = await chrome.storage.local.get(['user_id']);
      const user_id = obj.user_id;
      if (!user_id) {
        authMsg.textContent = 'Login to flag';
        displayStatus('require_login');
        return;
      }
      chrome.runtime.sendMessage({ action: 'getStatus' }, async (status) => {
        if (!status || !status.url) return;
        try {
          const res = await fetch('http://localhost:8000/api/flags/flag', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id, url: status.url })
          });
          const data = await res.json();
          setTimeout(loadStatus, 300);
        } catch (e) {}
      });
    });
  }
  if (recheckBtn) {
    recheckBtn.addEventListener('click', () => {
      chrome.storage.local.get(['user_id']).then(({ user_id }) => {
        if (!user_id) {
          authMsg.textContent = 'Login to recheck';
          displayStatus('require_login');
          return;
        }
        displayStatus('analyzing');
        recheckBtn.disabled = true;
        chrome.runtime.sendMessage({ action: 'recheck' }, () => {
          setTimeout(() => {
            recheckBtn.disabled = false;
            loadStatus();
          }, 800);
        });
      });
    });
  }

  loadStatus();
  updateAuthUI();
});

/**
 * Load current tab status
 */
function loadStatus() {
  try {
    chrome.runtime.sendMessage({ action: 'getStatus' }, (status) => {
      if (!status || typeof status !== 'object' || !status.status) {
        displayStatus('unknown', {});
        return;
      }
      try {
        displayStatus(status.status, status);
      } catch (e) {
        console.error('Render error:', e);
        displayStatus('error', { error: 'UI render error' });
      }
    });
  } catch (e) {
    console.error('Status load error:', e);
    displayStatus('error', { error: 'Failed to load status' });
  }
}

/**
 * Display status in UI
 */
function displayStatus(statusType, data = {}) {
  const statusCard = document.getElementById('status-section');
  const badge = document.getElementById('status-badge');
  const desc = document.getElementById('status-desc');
  const foundInfo = document.getElementById('found-info');
  const flagBtn = document.getElementById('flag-btn');
  const presence = document.getElementById('presence-badges');
  document.body.classList.remove('bg-legitimate','bg-phishing','bg-analyzing','bg-unable');

  badge.className = 'badge';
  foundInfo.textContent = '';
  if (presence) presence.innerHTML = '';
  
  const foundMain = !!data.found_in_main_db;
  const foundUser = !!data.found_in_user_db;
  const labels = [];

  if (statusType === 'legitimate') {
    badge.classList.add('legitimate');
    badge.textContent = 'Legitimate';
    desc.textContent = 'Website looks safe';
    document.body.classList.add('bg-legitimate');
    if (statusCard) {
      statusCard.classList.remove('card-phishing','card-analyzing','card-unable');
      statusCard.classList.add('card-legitimate');
    }
    if (foundMain) labels.push('Master DB: Yes');
    if (foundUser) labels.push('User DB: Yes');
    foundInfo.textContent = labels.join(' | ');
    if (presence) {
      if (foundMain) {
        const el = document.createElement('span');
        el.className = 'pill pill-main';
        el.textContent = 'Master DB';
        presence.appendChild(el);
      }
      if (foundUser) {
        const el = document.createElement('span');
        el.className = 'pill pill-user';
        el.textContent = 'User DB';
        presence.appendChild(el);
      }
    }
    if (flagBtn) flagBtn.disabled = true;
  } else if (statusType === 'phishing') {
    badge.classList.add('phishing');
    badge.textContent = 'Phishing';
    desc.textContent = 'Suspicious activity detected';
    document.body.classList.add('bg-phishing');
    if (statusCard) {
      statusCard.classList.remove('card-legitimate','card-analyzing','card-unable');
      statusCard.classList.add('card-phishing');
    }
    if (foundMain) labels.push('Master DB: Yes');
    if (foundUser) labels.push('User DB: Yes');
    foundInfo.textContent = labels.join(' | ');
    if (presence) {
      if (foundMain) {
        const el = document.createElement('span');
        el.className = 'pill pill-main';
        el.textContent = 'Master DB';
        presence.appendChild(el);
      }
      if (foundUser) {
        const el = document.createElement('span');
        el.className = 'pill pill-user';
        el.textContent = 'User DB';
        presence.appendChild(el);
      }
    }
    if (flagBtn) {
      const disable = foundMain || foundUser;
      flagBtn.disabled = disable;
    }
  } else if (statusType === 'analyzing') {
    badge.classList.add('analyzing');
    badge.textContent = 'Analyzing';
    desc.textContent = 'Checking databases and running models';
    document.body.classList.add('bg-analyzing');
    if (statusCard) {
      statusCard.classList.remove('card-legitimate','card-phishing','card-unable');
      statusCard.classList.add('card-analyzing');
    }
    foundInfo.textContent = '';
    if (presence) presence.innerHTML = '';
    if (flagBtn) flagBtn.disabled = true;
    setTimeout(loadStatus, 1000);
  } else if (statusType === 'error') {
    badge.classList.add('unable');
    badge.textContent = 'Error';
    desc.textContent = data.error || 'Unable to verify';
    document.body.classList.add('bg-unable');
    if (statusCard) {
      statusCard.classList.remove('card-legitimate','card-phishing','card-analyzing');
      statusCard.classList.add('card-unable');
    }
    foundInfo.textContent = '';
    if (presence) presence.innerHTML = '';
    if (flagBtn) flagBtn.disabled = true;
  } else if (statusType === 'require_login') {
    badge.classList.add('unable');
    badge.textContent = 'Login Required';
    desc.textContent = 'Please login to analyze this URL';
    document.body.classList.add('bg-unable');
    if (statusCard) {
      statusCard.classList.remove('card-legitimate','card-phishing','card-analyzing');
      statusCard.classList.add('card-unable');
    }
    foundInfo.textContent = '';
    if (presence) presence.innerHTML = '';
    if (flagBtn) flagBtn.disabled = true;
  } else {
    badge.classList.add('unable');
    badge.textContent = 'Unknown';
    desc.textContent = 'Navigate to a page to check its safety';
    document.body.classList.add('bg-unable');
    if (statusCard) {
      statusCard.classList.remove('card-legitimate','card-phishing','card-analyzing');
      statusCard.classList.add('card-unable');
    }
    foundInfo.textContent = '';
    if (presence) presence.innerHTML = '';
    if (flagBtn) flagBtn.disabled = true;
  }
}

/**
 * Format confidence percentage
 */
function formatConfidence(confidence) {
  if (typeof confidence === 'number') {
    return `${Math.round(confidence * 100)}%`;
  }
  return '-';
}

/**
 * Truncate long URLs
 */
function truncateUrl(url) {
  if (!url) return '-';
  if (url.length <= 40) return url;
  return url.substring(0, 37) + '...';
}
