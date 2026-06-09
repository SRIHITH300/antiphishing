// Background service worker - handles redirect-safe URL capture
const API_BASE_URL = 'http://localhost:8000';
const CACHE_DURATION = 3600000; // 1 hour in milliseconds

// In-memory cache for analyzed URLs
const urlCache = new Map();

// Track tabs and their final URLs
const tabUrlMap = new Map();

/**
 * CRITICAL: Use webNavigation.onCompleted to capture FINAL destination URL
 * This ensures we get the URL AFTER all redirects are complete
 */
chrome.webNavigation.onCompleted.addListener(async (details) => {
  // Only process main frame (not iframes)
  if (details.frameId !== 0) return;
  
  const tabId = details.tabId;
  const finalUrl = details.url;
  
  // Store the final URL for this tab
  tabUrlMap.set(tabId, finalUrl);
  
  // Analyze the URL
  await analyzeUrl(finalUrl, tabId);
});

/**
 * Clean up when tabs are closed
 */
chrome.tabs.onRemoved.addListener((tabId) => {
  tabUrlMap.delete(tabId);
});

/**
 * Analyze URL using backend API
 */
async function analyzeUrl(url, tabId) {
  // Skip non-http(s) URLs
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    return;
  }
  // Require login for all analysis
  const { user_id } = await chrome.storage.local.get('user_id');
  if (!user_id) {
    await updateTabStatus(tabId, {
      status: 'require_login',
      url: url,
      error: 'Login required to analyze URLs',
      timestamp: Date.now()
    });
    return;
  }
  // Check cache only if logged in
  const cached = getCachedResult(url);
  if (cached) {
    await updateTabStatus(tabId, cached);
    return;
  }
  
  try {
    // Set analyzing status
    await updateTabStatus(tabId, {
      status: 'analyzing',
      url: url,
      timestamp: Date.now()
    });
    
    const response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url: url, user_id: user_id || null })
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const result = await response.json();
    
    // Cache the result
    cacheResult(url, result);
    
    // Update tab status
    await updateTabStatus(tabId, {
      status: result.is_phishing ? 'phishing' : 'legitimate',
      url: url,
      confidence: result.confidence,
      details: result.details,
      found_in_main_db: !!result.found_in_main_db,
      found_in_user_db: !!result.found_in_user_db,
      timestamp: Date.now()
    });
    
  } catch (error) {
    console.error('Error analyzing URL:', error);
    
    // Set error status
    await updateTabStatus(tabId, {
      status: 'error',
      url: url,
      error: 'Unable to verify URL safety. Please proceed with caution.',
      timestamp: Date.now()
    });
  }
}

/**
 * Update tab status in storage
 */
async function updateTabStatus(tabId, statusData) {
  const key = `tab_${tabId}`;
  await chrome.storage.local.set({ [key]: statusData });
  if (statusData && statusData.status && statusData.status !== 'analyzing') {
    await maybeAutoPopup(tabId, statusData);
  }
}

/**
 * Cache result
 */
function cacheResult(url, result) {
  urlCache.set(url, {
    data: result,
    timestamp: Date.now()
  });
  
  // Clean old cache entries periodically
  if (urlCache.size > 1000) {
    cleanCache();
  }
}

/**
 * Get cached result if still valid
 */
function getCachedResult(url) {
  const cached = urlCache.get(url);
  if (!cached) return null;
  
  const age = Date.now() - cached.timestamp;
  if (age > CACHE_DURATION) {
    urlCache.delete(url);
    return null;
  }
  
  return {
    status: cached.data.is_phishing ? 'phishing' : 'legitimate',
    url: url,
    confidence: cached.data.confidence,
    details: cached.data.details,
    found_in_main_db: !!cached.data.found_in_main_db,
    found_in_user_db: !!cached.data.found_in_user_db,
    timestamp: cached.timestamp,
    cached: true
  };
}

/**
 * Clean old cache entries
 */
function cleanCache() {
  const now = Date.now();
  for (const [url, entry] of urlCache.entries()) {
    if (now - entry.timestamp > CACHE_DURATION) {
      urlCache.delete(url);
    }
  }
}

/**
 * Auto open popup window to show result
 */
async function maybeAutoPopup(tabId, statusData) {
  try {
    const { last_popup_url, last_popup_ts } = await chrome.storage.local.get(['last_popup_url', 'last_popup_ts']);
    const now = Date.now();
    if (last_popup_url === statusData.url && last_popup_ts && (now - last_popup_ts) < 10000) {
      return;
    }
    await chrome.storage.local.set({ last_popup_url: statusData.url, last_popup_ts: now, last_auto_open_ts: now });
    if (chrome.action && chrome.action.openPopup) {
      try {
        await chrome.action.openPopup();
        return;
      } catch (e) {
        // Fallback to a small popup window if action.openPopup not available
      }
    }
    const popupUrl = chrome.runtime.getURL('popup.html');
    await chrome.windows.create({
      url: popupUrl,
      type: 'popup',
      width: 380,
      height: 520,
      focused: false
    });
  } catch (e) {
    console.warn('Auto-popup failed:', e);
  }
}
/**
 * Listen for messages from popup
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getStatus') {
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
      if (tabs[0]) {
        const tabId = tabs[0].id;
        const key = `tab_${tabId}`;
        const result = await chrome.storage.local.get(key);
        sendResponse(result[key] || { status: 'unknown' });
      } else {
        sendResponse({ status: 'unknown' });
      }
    });
    return true; // Keep channel open for async response
  }
  
  if (request.action === 'recheck') {
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
      if (tabs[0]) {
        const url = tabs[0].url;
        // Clear cache
        urlCache.delete(url);
        // Reanalyze
        await analyzeUrl(url, tabs[0].id);
        sendResponse({ success: true });
      }
    });
    return true;
  }
});

/**
 * Initialize on install
 */
chrome.runtime.onInstalled.addListener(() => {
  console.log('Phishing Shield installed and active');
});
