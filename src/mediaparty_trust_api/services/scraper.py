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

        logger.info(f"Calling OpenRouter API with model: {self.model}")

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
            }
        )

        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                logger.info(f"OpenRouter API call successful")
                return [content]
            else:
                raise ValueError("No response from model")
        else:
            logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
            raise ValueError(f"API error: {response.status_code} - {response.text}")


class ArticleExtractor(dspy.Signature):
    """Extract article information from raw HTML content.

    Given the HTML content of a news article page, extract the following:
    - title: The article title/headline
    - body: The main article content (clean text, no HTML)
    - author: The article author name if found (null if not found)
    - editor: The editor responsible or director name if found in footer/paratext (null if not found)
    - media_group: The media group, company, or publisher name if found in footer/paratext (null if not found)

    Return only a valid JSON object with these fields.
    """
    html_content: str = dspy.InputField(desc="Raw HTML content of the news article page")
    url: str = dspy.InputField(desc="URL of the article for context")
    title: str = dspy.OutputField(desc="Article title/headline")
    body: str = dspy.OutputField(desc="Main article content as clean text")
    author: Optional[str] = dspy.OutputField(desc="Author name or null if not found")
    editor: Optional[str] = dspy.OutputField(desc="Editor responsible name from footer or null")
    media_group: Optional[str] = dspy.OutputField(desc="Media group/publisher name from footer or null")


def fetch_html(url: str) -> str:
    """Fetch HTML content from URL with proper headers."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()
        # Ensure proper encoding
        if response.encoding is None:
            response.encoding = 'utf-8'
        return response.text
    except requests.RequestException as e:
        logger.error(f"Failed to fetch URL {url}: {e}")
        raise ValueError(f"Failed to fetch URL: {str(e)}")


def clean_html_for_llm(html: str, max_chars: int = 50000) -> str:
    """Clean and truncate HTML for LLM processing."""
    soup = BeautifulSoup(html, 'html.parser')

    # Remove script and style elements
    for script in soup(["script", "style", "nav", "header"]):
        script.decompose()

    # Get text
    text = soup.get_text(separator='\n', strip=True)

    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)

    # Truncate if too long
    if len(text) > max_chars:
        text = text[:max_chars] + "\n...[content truncated]"

    return text


def scrape_article(url: str) -> dict:
    """
    Scrape a news article from URL using LLM extraction.

    Args:
        url: The URL of the news article

    Returns:
        dict with keys: title, body, author, editor, media_group, url
    """
    logger.info(f"Scraping article from URL: {url}")

    # Validate URL
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Invalid URL provided")

    # Fetch HTML
    html = fetch_html(url)

    # Clean HTML for LLM
    cleaned_content = clean_html_for_llm(html)

    # Use LLM to extract structured data
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ConfigurationError("OPENROUTER_API_KEY not configured for scraping")

    try:
        lm = OpenRouterLM()
        with dspy.context(lm=lm):
            module = dspy.ChainOfThought(ArticleExtractor)
            result = module(html_content=cleaned_content, url=url)

        return {
            "title": result.title.strip() if result.title else "",
            "body": result.body.strip() if result.body else "",
            "author": result.author.strip() if result.author else None,
            "editor": result.editor.strip() if result.editor else None,
            "media_group": result.media_group.strip() if result.media_group else None,
            "url": url,
        }
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        raise ValueError(f"Failed to extract article content: {str(e)}")
