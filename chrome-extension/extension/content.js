(() => {
  if (window.__metricasPeriodismoInitialized) {
    return;
  }
  window.__metricasPeriodismoInitialized = true;

  loadSettings()
    .then((settings) => {
      const pageType = detectPageType();

      if (pageType === 'article') {
        handleArticlePage(settings).catch((error) => {
          console.error('Metricas Periodismo: error handling article page', error);
        });
        return;
      }

      if (pageType === 'homepage') {
        handleHomepage(settings).catch((error) => {
          console.error('Metricas Periodismo: error handling homepage', error);
        });
        return;
      }

      console.info('Metricas Periodismo: no matching page context detected.');
    })
    .catch((error) => {
      console.error('Metricas Periodismo: failed to initialize settings', error);
    });
})();

const SETTINGS_DEFAULTS = Object.freeze({
  homepageArticles: 5
});

const UNKNOWN_AUTHOR_PLACEHOLDER = 'Autor desconocido';

const HOMEPAGE_ARTICLES_MIN = 1;
const HOMEPAGE_ARTICLES_MAX = 20;

async function loadSettings() {
  try {
    const stored = await chrome.storage.sync.get(['homepageArticles']);
    return {
      homepageArticles: normalizeHomepageArticles(stored.homepageArticles)
    };
  } catch (error) {
    console.warn('Metricas Periodismo: failed to load settings from storage, using defaults.', error);
    return { ...SETTINGS_DEFAULTS };
  }
}

function normalizeHomepageArticles(value) {
  const parsed = Number(value);
  if (
    Number.isFinite(parsed) &&
    parsed >= HOMEPAGE_ARTICLES_MIN &&
    parsed <= HOMEPAGE_ARTICLES_MAX
  ) {
    return Math.floor(parsed);
  }

  return SETTINGS_DEFAULTS.homepageArticles;
}

function detectPageType() {
  if (document.querySelector('article') && document.querySelector('h1')) {
    return 'article';
  }

  if (isHomepage(window.location)) {
    return 'homepage';
  }

  return 'unknown';
}

function isHomepage(locationObj) {
  const path = (locationObj.pathname || '').replace(/\/+/g, '/').replace(/\/$/, '');
  return path === '' || path === '/';
}

async function handleArticlePage() {
  const articleData = extractArticleData(document);
  const articleElement = articleData.primaryContainer;

  if (!articleElement || !articleData.body) {
    console.warn('Metricas Periodismo: No article body found on this page.');
    return;
  }

  const panel = injectPanel(articleElement);
  setPanelState(panel, {
    status: 'loading',
    message: 'Analizando la nota…'
  });

  const payload = {
    title: articleData.title,
    body: articleData.body,
    author: articleData.author || UNKNOWN_AUTHOR_PLACEHOLDER,
    date: "2025-10-04",
    link: window.location.href,
    media_type: "news"
  };

  try {
    const criteriaList = await requestAnalysis(payload);

    if (!Array.isArray(criteriaList) || criteriaList.length === 0) {
      setPanelState(panel, {
        status: 'empty',
        message: 'El servicio no devolvió criterios para mostrar.'
      });
      return;
    }

    renderResults(panel, criteriaList);
    renderBadges(articleElement, criteriaList);
  } catch (error) {
    setPanelState(panel, {
      status: 'error',
      message: error.message || 'No se pudo analizar la nota.'
    });
  }
}

async function handleHomepage(settings) {
  const homepageLimit = normalizeHomepageArticles(settings?.homepageArticles);
  const homepageCards = collectHomepageArticleLinks(homepageLimit).slice(0, homepageLimit);

  if (homepageCards.length === 0) {
    console.info('Metricas Periodismo: no homepage article links detected.');
    return;
  }

  console.info(
    `Metricas Periodismo: processing ${homepageCards.length} homepage articles (limit ${homepageLimit}).`
  );

  for (const [index, cardInfo] of homepageCards.entries()) {
    console.info('Metricas Periodismo: fetching homepage article', {
      position: index + 1,
      link: cardInfo.link
    });
    // eslint-disable-next-line no-await-in-loop -- sequential requests avoid overloading the API
    await annotateHomepageCard(cardInfo);
  }
}

function collectHomepageArticleLinks(desiredCount = SETTINGS_DEFAULTS.homepageArticles) {
  const limit = normalizeHomepageArticles(desiredCount);
  const root = getHomepageRoot();
  const cardSelectors = [
    'article',
    'section article',
    '.story-card',
    '.news-card',
    '.headline',
    '.nota',
    '[data-component*="card"], [data-component*="story"]',
    '[data-module*="card"], [data-module*="story"]'
  ];

  const seenUrls = new Set();
  const cards = [];

  cardSelectors.forEach((selector) => {
    root.querySelectorAll(selector).forEach((cardElement) => {
      addHomepageCard(cardElement, seenUrls, cards);
    });
  });

  if (cards.length < limit) {
    console.warn(
      `Metricas Periodismo: card-based selection found ${cards.length} articles. Using fallback scanning.`
    );
    const fallbackCards = collectHomepageAnchorsFallback(seenUrls, cards.length, limit);
    cards.push(...fallbackCards);
  }

  return cards;
}

function isEligibleHomepageAnchor(anchor) {
  if (!anchor || !anchor.isConnected) {
    return false;
  }

  const root = getHomepageRoot();
  if (!root.contains(anchor)) {
    return false;
  }

  if (anchor.closest('nav, header, footer, aside, [role="navigation"], [aria-label="breadcrumb"]')) {
    return false;
  }

  if (anchor.closest('[data-section="quicklinks"], [data-section="trends"], .trends, .quicklinks, .ctn-quicklinks')) {
    return false;
  }

  const text = anchor.textContent ? anchor.textContent.replace(/\s+/g, ' ').trim() : '';
  const hasMedia = Boolean(anchor.querySelector('img, picture, video'));

  return text.length > 0 || hasMedia;
}

function collectHomepageAnchorsFallback(seenUrls, currentCount, desiredCount) {
  const root = getHomepageRoot();
  const anchors = Array.from(root.querySelectorAll('a[href]'));
  const fallbackCards = [];
  const limit = normalizeHomepageArticles(desiredCount);

  anchors.forEach((anchor) => {
    if (fallbackCards.length + currentCount >= Math.min(limit * 2, HOMEPAGE_ARTICLES_MAX * 2)) {
      return;
    }

    if (!isEligibleHomepageAnchor(anchor)) {
      return;
    }

    const normalizedUrl = normalizeInfobaeUrl(anchor.getAttribute('href'));
    if (!normalizedUrl || seenUrls.has(normalizedUrl) || !isLikelyArticleUrl(normalizedUrl)) {
      return;
    }

    const cardElement =
      anchor.closest('article, .story-card, .news-card, .headline, .nota, [data-component*="card"], [data-module*="card"], li, section, div') ||
      anchor.parentElement;
    if (!cardElement || !root.contains(cardElement)) {
      return;
    }

    seenUrls.add(normalizedUrl);
    fallbackCards.push({ anchor, cardElement, link: normalizedUrl });
  });

  return fallbackCards;
}

function addHomepageCard(cardElement, seenUrls, cards) {
  if (!cardElement || !cardElement.isConnected) {
    return;
  }

  const anchor = findPrimaryAnchor(cardElement);
  if (!anchor || !isEligibleHomepageAnchor(anchor)) {
    return;
  }

  const normalizedUrl = normalizeInfobaeUrl(anchor.getAttribute('href'));
  if (!normalizedUrl || seenUrls.has(normalizedUrl) || !isLikelyArticleUrl(normalizedUrl)) {
    return;
  }

  seenUrls.add(normalizedUrl);
  cards.push({ anchor, cardElement, link: normalizedUrl });
}

function findPrimaryAnchor(cardElement) {
  const anchorSelectors = ['a[href*="/202" i]', 'a[href*="/20" i]', 'a[href]'];

  for (const selector of anchorSelectors) {
    const anchor = cardElement.querySelector(selector);
    if (anchor) {
      return anchor;
    }
  }

  return null;
}

function getHomepageRoot() {
  return document.querySelector('main') || document.body;
}

function normalizeInfobaeUrl(rawHref) {
  if (!rawHref) {
    return null;
  }

  try {
    const url = new URL(rawHref, window.location.origin);
    if (!/\.infobae\.com$/i.test(url.hostname)) {
      return null;
    }

    url.hash = '';
    url.search = '';
    return url.toString();
  } catch (error) {
    return null;
  }
}

function isLikelyArticleUrl(urlString) {
  try {
    const url = new URL(urlString);
    const path = url.pathname || '';

    if (path === '/' || path === '') {
      return false;
    }

    if (/\/videos\//.test(path) || /\/podcast/.test(path) || /\/minute/.test(path)) {
      return false;
    }

    return /\/\d{4}\/\d{2}\/\d{2}\//.test(path);
  } catch (error) {
    return false;
  }
}

async function annotateHomepageCard({ cardElement, link }) {
  const overlay = ensureCardOverlay(cardElement);
  setCardOverlayState(overlay, {
    status: 'loading',
    message: 'Analizando…'
  });

  try {
    const articleDocument = await fetchArticleDocument(link);
    const articleData = extractArticleData(articleDocument);

    if (!articleData.body) {
      throw new Error('No se pudo extraer el cuerpo de la nota.');
    }

  const payload = {
    title: articleData.title,
    body: articleData.body,
    author: articleData.author || UNKNOWN_AUTHOR_PLACEHOLDER,
    date: "2025-10-04",
    link: window.location.href,
    media_type: "news"
  };

    

    const criteriaList = await requestAnalysis(payload);

    if (!Array.isArray(criteriaList) || criteriaList.length === 0) {
      setCardOverlayState(overlay, {
        status: 'empty',
        message: 'Sin criterios disponibles.'
      });
      console.warn('Metricas Periodismo: API returned no criteria for homepage article', url);
      return;
    }

    populateOverlayWithBadges(overlay, criteriaList);
    console.info('Metricas Periodismo: annotated homepage article', {
      url: link,
      criteriaCount: criteriaList.length
    });
  } catch (error) {
    setCardOverlayState(overlay, {
      status: 'error',
      message: error.message || 'Error al analizar la nota.'
    });
    console.error('Metricas Periodismo: failed to annotate homepage article', {
      url,
      error
    });
  }
}

async function fetchArticleDocument(url) {
  const response = await fetch(url, {
    credentials: 'include'
  });

  if (!response.ok) {
    throw new Error(`No se pudo cargar la nota (${response.status}).`);
  }

  const text = await response.text();
  const parser = new DOMParser();
  return parser.parseFromString(text, 'text/html');
}

function ensureCardOverlay(cardElement) {
  cardElement.classList.add('metricas-card');
  let overlay = cardElement.querySelector('.metricas-card-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'metricas-card-overlay metricas-card-overlay--loading';
    cardElement.appendChild(overlay);
  }
  return overlay;
}

function setCardOverlayState(overlay, { status, message }) {
  overlay.className = `metricas-card-overlay metricas-card-overlay--${status}`;
  overlay.innerHTML = `<span class="metricas-card-overlay__message">${escapeHtml(message)}</span>`;
}

function populateOverlayWithBadges(overlay, criteriaList) {
  overlay.className = 'metricas-card-overlay metricas-card-overlay--ready';
  overlay.innerHTML = '';

  criteriaList.forEach((criterion) => {
    overlay.appendChild(createBadgeElement(criterion));
  });
}

async function requestAnalysis(payload) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(
      {
        type: 'analyzeArticle',
        payload
      },
      (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(`No se pudo contactar la extensión: ${chrome.runtime.lastError.message}`));
          return;
        }

        if (!response?.success) {
          reject(new Error(response?.error || 'Error desconocido en el análisis'));
          return;
        }

        resolve(response.data);
      }
    );
  });
}

function extractArticleData(rootDocument = document) {
  const candidateArticle = rootDocument.querySelector('article');
  const container =
    candidateArticle || rootDocument.querySelector('[data-type="article-body"], .article-detail, .article-body');

  const titleEl = rootDocument.querySelector('h1') || container?.querySelector('h1');
  const paragraphScope = container || rootDocument;
  const paragraphs = Array.from(paragraphScope.querySelectorAll('p'));

  const paragraphTexts = paragraphs
    .map((p) => p.textContent?.trim() || '')
    .filter((text) => text.length > 0);

  const bodyText = paragraphTexts.join('\n\n');
  const wordCount = bodyText ? bodyText.split(/\s+/).filter(Boolean).length : 0;

  const author = extractArticleAuthor(rootDocument);

  return {
    primaryContainer: rootDocument === document ? container : null,
    title: titleEl?.textContent?.trim() || '',
    body: bodyText,
    wordCount,
    author
  };
}

function extractArticleAuthor(rootDocument) {
  const authorFromMeta = findAuthorInMeta(rootDocument);
  if (authorFromMeta) {
    return authorFromMeta;
  }

  const authorFromStructuredData = findAuthorInStructuredData(rootDocument);
  if (authorFromStructuredData) {
    return authorFromStructuredData;
  }

  const authorFromByline = findAuthorInBylineElements(rootDocument);
  if (authorFromByline) {
    return authorFromByline;
  }

  return '';
}

function normalizeAuthorText(rawText) {
  if (!rawText) {
    return '';
  }

  let cleaned = String(rawText)
    .replace(/[\n\r\t]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  cleaned = cleaned
    .replace(/^(por|por\s+el|por\s+la|por\s+los|por\s+las|by|de)\s+/i, '')
    .replace(/^autor[:\-\s]+/i, '')
    .replace(/\s*\|\s*.*$/, '')
    .replace(/\s*[–-]\s+.*$/, '');

  if (cleaned.length > 120) {
    return '';
  }

  if (/https?:\/\//i.test(cleaned)) {
    return '';
  }

  return cleaned.trim();
}

function findAuthorInMeta(rootDocument) {
  const selectors = [
    'meta[name="author"]',
    'meta[name="byline"]',
    'meta[name="parsely-author"]',
    'meta[name="dc.creator"]',
    'meta[name="DC.creator"]',
    'meta[name="dcterms.creator"]',
    'meta[property="author"]',
    'meta[property="article:author"]',
    'meta[property="og:article:author"]'
  ];

  for (const selector of selectors) {
    const meta = rootDocument.querySelector(selector);
    const content = normalizeAuthorText(meta?.getAttribute('content'));
    if (content) {
      return content;
    }
  }

  return '';
}

function findAuthorInStructuredData(rootDocument) {
  const scripts = Array.from(rootDocument.querySelectorAll('script[type="application/ld+json"]'));

  for (const script of scripts) {
    try {
      const jsonText = script.textContent;
      if (!jsonText) {
        continue;
      }

      const data = JSON.parse(jsonText);
      const authorName = extractAuthorNameFromStructuredData(data);
      const normalized = normalizeAuthorText(authorName);
      if (normalized) {
        return normalized;
      }
    } catch (error) {
      // Ignore malformed JSON-LD blocks
    }
  }

  return '';
}

function extractAuthorNameFromStructuredData(data) {
  if (!data) {
    return '';
  }

  if (Array.isArray(data)) {
    for (const item of data) {
      const extracted = extractAuthorNameFromStructuredData(item);
      if (extracted) {
        return extracted;
      }
    }
    return '';
  }

  if (typeof data !== 'object') {
    return '';
  }

  if ('@graph' in data) {
    return extractAuthorNameFromStructuredData(data['@graph']);
  }

  const author = data.author || data.creator;
  if (!author) {
    return '';
  }

  if (typeof author === 'string') {
    return author;
  }

  if (Array.isArray(author)) {
    for (const entry of author) {
      const extracted = extractAuthorNameFromStructuredData(entry);
      if (extracted) {
        return extracted;
      }
    }
    return '';
  }

  if (typeof author === 'object') {
    return author.name || author['@name'] || '';
  }

  return '';
}

function findAuthorInBylineElements(rootDocument) {
  const selectors = [
    '[itemprop="author"] [itemprop="name"]',
    '[itemprop="author"], [itemtype*="Person" i] [itemprop="name"]',
    '.author, .author-name, .byline, .byline__author, .byline__name, .byline__names, .nota-autor',
    '.article-author, .article__author, .story-author, .post-author'
  ];

  const seen = new Set();

  for (const selector of selectors) {
    const elements = Array.from(rootDocument.querySelectorAll(selector));

    for (const element of elements) {
      const text = normalizeAuthorText(element?.textContent);

      if (!text || seen.has(text)) {
        continue;
      }

      seen.add(text);
      return text;
    }
  }

  return '';
}

function injectPanel(anchorElement) {
  const existing = document.getElementById('metricas-periodismo-panel');
  if (existing) {
    return existing;
  }

  const panel = document.createElement('section');
  panel.id = 'metricas-periodismo-panel';

  const targetParent = anchorElement.parentElement || document.body;
  targetParent.insertBefore(panel, anchorElement);

  return panel;
}

function setPanelState(panel, { status, message }) {
  panel.className = `metricas-panel metricas-panel--${status}`;
  panel.innerHTML = `<div class="metricas-panel__message">${escapeHtml(message)}</div>`;
}

function renderResults(panel, criteriaList) {
  panel.className = 'metricas-panel metricas-panel--ready';
  panel.innerHTML = `
    <header class="metricas-panel__header">
      <h2 class="metricas-panel__title">Calidad periodística</h2>
      <span class="metricas-panel__subtitle">${criteriaList.length} criterios evaluados</span>
    </header>
    <ul class="metricas-panel__list"></ul>
  `;

  const listEl = panel.querySelector('.metricas-panel__list');

  criteriaList.forEach((criterion) => {
    const item = document.createElement('li');
    const flagClass = flagToClass(criterion.flag);
    const scoreText = formatScore(criterion.score);
    const explanation = criterion.explanation || '';

    item.className = `metricas-panel__item ${flagClass}`;
    item.innerHTML = `
      <div class="metricas-panel__item-header">
        <span class="metricas-panel__item-name">${escapeHtml(criterion.criteria_name || 'Criterio')}</span>
        <span class="metricas-panel__score">${scoreText}</span>
      </div>
      <p class="metricas-panel__explanation">${escapeHtml(criterion.explanation || '')}</p>
    `;

    if (explanation) {
      item.setAttribute('title', explanation);
    }

    listEl.appendChild(item);
  });
}

function renderBadges(articleElement, criteriaList) {
  const header =
    articleElement.querySelector('header') ||
    articleElement.querySelector('h1')?.parentElement ||
    articleElement;

  if (!header) {
    return;
  }

  let badgesRow = header.querySelector('.metricas-badges');
  if (!badgesRow) {
    badgesRow = document.createElement('div');
    badgesRow.className = 'metricas-badges';
    header.insertBefore(badgesRow, header.firstChild);
  }

  badgesRow.innerHTML = '';

  criteriaList.forEach((criterion) => {
    badgesRow.appendChild(createBadgeElement(criterion));
  });
}

function createBadgeElement(criterion) {
  const badge = document.createElement('span');
  badge.className = `metricas-badge ${flagToClass(criterion.flag)}`;

  const scoreText = formatScore(criterion.score);
  const name = criterion.criteria_name || 'Criterio';
  const explanation = criterion.explanation || '';

  badge.innerHTML = `
    <span class="metricas-badge__shape">
      <span class="metricas-badge__name">${escapeHtml(name)}</span>
      <span class="metricas-badge__score">${scoreText}</span>
    </span>
  `;

  if (explanation) {
    badge.dataset.description = explanation;
    badge.setAttribute('aria-label', `${name}. ${explanation}`);
  }

  return badge;
}

function flagToClass(flag) {
  if (flag === -1) {
    return 'metricas--negative';
  }
  if (flag === 1) {
    return 'metricas--positive';
  }
  return 'metricas--neutral';
}

function formatScore(score) {
  if (typeof score !== 'number' || Number.isNaN(score)) {
    return '—';
  }
  return `${Math.round(score * 100)}`;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
