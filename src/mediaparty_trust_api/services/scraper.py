"""News article scraping service using LLM extraction."""

import os
import logging
from typing import Optional
from urllib.parse import urlparse

import requests
import dspy
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when there's a configuration error (e.g., missing API key)."""
    pass


class OpenRouterLM(dspy.LM):
    """Custom DSPy LM that uses OpenRouter API directly."""

    DEFAULT_MODEL = "google/gemma-4-31b-it:free"

    def __init__(self, model: str | None = None, **kwargs):
        self.model = model or os.getenv("OPENROUTER_MODEL", self.DEFAULT_MODEL)
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        self.kwargs = kwargs
        super().__init__(model=self.model)

    def __call__(self, prompt=None, messages=None, **kwargs):
        if messages is None:
            messages = [{"role": "user", "content": prompt}]

        print(f"🤖 Calling OpenRouter API with model: {self.model}")

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.getenv("SITE_URL", ""),
                "X-Title": os.getenv("SITE_NAME", "MediaParty Trust API"),
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.1),
                "top_p": kwargs.get("top_p", 0.9),
                "max_tokens": kwargs.get("max_tokens", 2000),
            },
            timeout=120  # Timeout de 2 minutos para modelos gratuitos lentos
        )

        print(f"📡 OpenRouter response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print("✅ OpenRouter API call successful")
                return [content]
            else:
                raise ValueError("No response from model")
        else:
            print(f"❌ OpenRouter API error: {response.status_code} - {response.text}")
            raise ValueError(f"API error: {response.status_code} - {response.text}")


class ArticleExtractor(dspy.Signature):
    """Extract article information from pre-processed HTML content.

    The input contains clearly marked sections:
    - TITLE: (pre-extracted if available)
    - AUTHOR: (pre-extracted if available)
    - --- MAIN CONTENT ---: Article body
    - --- FOOTER / PARATEXTO ---: Footer with editor/media info

    Extract:
    - title: Use pre-extracted TITLE or find in main content. Never empty.
    - body: From MAIN CONTENT section. Never empty.
    - author: Use pre-extracted AUTHOR or find bylines. Empty string "" if not found.
    - editor: From FOOTER section ("Director: X"). Empty string "" if not found.
    - media_group: From FOOTER (company names like "Grupo X S.A."). Empty string "" if not found.

    Return empty strings "" for missing fields, never null.
    """
    html_content: str = dspy.InputField(desc="Pre-processed HTML with TITLE, AUTHOR, MAIN CONTENT, FOOTER sections")
    url: str = dspy.InputField(desc="URL of the article for context")
    title: str = dspy.OutputField(desc="Article title/headline - never empty")
    body: str = dspy.OutputField(desc="Main article content - never empty")
    author: str = dspy.OutputField(desc="Author name, empty string if not found")
    editor: str = dspy.OutputField(desc="Editor name from footer, empty string if not found")
    media_group: str = dspy.OutputField(desc="Media group name from footer, empty string if not found")


def fetch_html(url: str) -> str:
    """Fetch HTML content from URL with proper headers."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    try:
        # Create a session to handle cookies
        session = requests.Session()
        # First request to get cookies
        session.get("https://www.perfil.com/", headers=headers, timeout=10, allow_redirects=True)

        # Actual request to the target URL
        response = session.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()

        # Handle encoding properly
        if response.encoding is None:
            response.encoding = response.apparent_encoding or 'utf-8'

        content = response.text
        logger.info(f"Fetched URL: {url}, encoding: {response.encoding}, length: {len(content)}")

        # Quick validation - should contain HTML tags
        if '<html' not in content.lower() and '<!' not in content[:100]:
            logger.warning(f"Response may not be valid HTML. Preview: {content[:200]}")

        return content
    except requests.RequestException as e:
        logger.error(f"Failed to fetch URL {url}: {e}")
        raise ValueError(f"Failed to fetch URL: {str(e)}")


def clean_html_for_llm(html: str, max_chars: int = 50000) -> str:
    """Clean and prepare HTML for LLM processing, preserving structure."""
    # Check if content looks like binary/corrupted
    if not html or len(html.strip()) == 0:
        raise ValueError("Empty HTML content received")

    # Check for binary content (high ratio of non-printable chars)
    sample = html[:1000]
    printable_chars = sum(1 for c in sample if c.isprintable() or c.isspace())
    if len(sample) > 0 and printable_chars / len(sample) < 0.8:
        # Try to re-decode as latin-1 fallback
        try:
            if isinstance(html, bytes):
                html = html.decode('utf-8', errors='replace')
        except:
            pass

    soup = BeautifulSoup(html, 'html.parser')

    # Remove unwanted elements but keep structure
    for element in soup.find_all(['script', 'style', 'nav', 'aside', 'iframe', 'svg', 'canvas']):
        element.decompose()

    # Try to find main content area - common patterns
    content_selectors = [
        'article', 'main', '[role="main"]',
        '.article-body', '.article-content', '.content-body',
        '.nota-content', '.news-body',  # Common in Argentine media
        '#article-body', '#content',
        'section.content', 'div.content'
    ]

    main_content = None
    for selector in content_selectors:
        main_content = soup.select_one(selector)
        if main_content:
            break

    # Also try to find footer for editor/media info
    footer_selectors = ['footer', '.footer', '#footer', '.site-footer', '.pie']
    footer_content = None
    for selector in footer_selectors:
        footer_content = soup.select_one(selector)
        if footer_content:
            break

    # Extract title from meta or h1
    title = ""
    title_meta = soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'twitter:title'})
    if title_meta:
        title = title_meta.get('content', '')
    if not title:
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)

    # Extract author from meta tags
    author = ""
    author_meta = soup.find('meta', attrs={'name': 'author'}) or soup.find('meta', property='og:author')
    if author_meta:
        author = author_meta.get('content', '')

    # Build structured content
    parts = []

    if title:
        parts.append(f"TITLE: {title}")
    if author:
        parts.append(f"AUTHOR: {author}")

    parts.append("\n--- MAIN CONTENT ---\n")

    if main_content:
        # Get text from main content, preserving some structure
        text = main_content.get_text(separator='\n', strip=True)
    else:
        # Fallback to body or whole document
        body = soup.find('body') or soup
        text = body.get_text(separator='\n', strip=True)

    # Clean up whitespace but preserve paragraphs
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = '\n'.join(lines)

    parts.append(text)

    if footer_content:
        parts.append("\n\n--- FOOTER / PARATEXTO ---\n")
        footer_text = footer_content.get_text(separator='\n', strip=True)
        footer_lines = [line.strip() for line in footer_text.splitlines() if line.strip()]
        parts.append('\n'.join(footer_lines[:50]))  # Limit footer content

    result = '\n'.join(parts)

    # Truncate if too long
    if len(result) > max_chars:
        result = result[:max_chars] + "\n\n...[content truncated]"

    return result


def scrape_article(url: str) -> dict:
    """
    Scrape a news article from URL using LLM extraction.

    Args:
        url: The URL of the news article

    Returns:
        dict with keys: title, body, author, editor, media_group, url
    """
    print(f"📥 Scraping article from URL: {url}")

    # Validate URL
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Invalid URL provided")

    # Fetch HTML
    print("📡 Fetching HTML...")
    html = fetch_html(url)
    print(f"✅ HTML fetched: {len(html)} chars")

    # Clean HTML for LLM
    print("🧹 Cleaning HTML...")
    cleaned_content = clean_html_for_llm(html)
    print(f"✅ Cleaned content: {len(cleaned_content)} chars")

    # Use LLM to extract structured data
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ConfigurationError("OPENROUTER_API_KEY not configured for scraping")

    try:
        print("🤖 Calling OpenRouter LLM...")
        lm = OpenRouterLM()
        with dspy.context(lm=lm):
            module = dspy.ChainOfThought(ArticleExtractor)
            result = module(html_content=cleaned_content, url=url)
        print("✅ LLM response received")

        # Helper to clean optional fields (empty -> None)
        def clean_optional(value: str) -> Optional[str]:
            if not value:
                return None
            stripped = value.strip()
            return stripped if stripped else None

        return {
            "title": result.title.strip() if result.title else "",
            "body": result.body.strip() if result.body else "",
            "author": clean_optional(result.author),
            "editor": clean_optional(result.editor),
            "media_group": clean_optional(result.media_group),
            "url": url,
        }
    except Exception as e:
        print(f"❌ LLM extraction failed: {e}")
        raise ValueError(f"Failed to extract article content: {str(e)}")
