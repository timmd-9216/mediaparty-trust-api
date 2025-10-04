const DEFAULT_OPTIONS = {
  apiEndpoint: 'https://your.api.endpoint/analyze',
  homepageArticles: 5
};

chrome.runtime.onInstalled.addListener(async () => {
  const stored = await chrome.storage.sync.get(['apiEndpoint', 'homepageArticles']);
  const updates = {};

  if (!stored.apiEndpoint) {
    updates.apiEndpoint = DEFAULT_OPTIONS.apiEndpoint;
  }

  if (!isValidHomepageArticles(stored.homepageArticles)) {
    updates.homepageArticles = DEFAULT_OPTIONS.homepageArticles;
  }

  if (Object.keys(updates).length > 0) {
    await chrome.storage.sync.set(updates);
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type !== 'analyzeArticle') {
    return false;
  }

  let articlePayload;
  let apiEndpoint;

  (async () => {
    try {
      articlePayload = message.payload;
      if (!articlePayload || !articlePayload.body) {
        throw new Error('Missing article payload body');
      }

      const settings = await ensureSettings();
      apiEndpoint = settings.apiEndpoint;
      if (!apiEndpoint) {
        throw new Error('API endpoint is not configured. Please set it in the extension options.');
      }

      const apiResponse = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(articlePayload)
      });

      if (!apiResponse.ok) {
        const errorText = await apiResponse.text();
        throw new Error(`API responded with ${apiResponse.status}: ${errorText}`);
      }

      const result = await apiResponse.json();
      sendResponse({ success: true, data: result });
    } catch (error) {
      console.error('Metricas Periodismo: analysis failed', {
        error,
        endpoint: apiEndpoint,
        articleTitle: articlePayload?.title,
        url: articlePayload?.url
      });
      sendResponse({ success: false, error: error.message || 'Unknown error' });
    }
  })();

  return true; // keep the message channel open for the async work above
});

async function ensureSettings() {
  const stored = await chrome.storage.sync.get(['apiEndpoint', 'homepageArticles']);
  return {
    apiEndpoint: stored.apiEndpoint || DEFAULT_OPTIONS.apiEndpoint,
    homepageArticles: isValidHomepageArticles(stored.homepageArticles)
      ? Number(stored.homepageArticles)
      : DEFAULT_OPTIONS.homepageArticles
  };
}

function isValidHomepageArticles(value) {
  if (value === undefined) {
    return false;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 1 && parsed <= 20;
}
