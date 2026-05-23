"""Small web system to analyze journalist signatures in articles."""

import json
import os
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Load .env variables
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
PROMPTS_DIR = BASE_DIR.parents[2] / "prompts"

# Load prompt text
SIGNATURE_PROMPT_PATH = PROMPTS_DIR / "prompt-signatures.txt"
SIGNATURE_PROMPT = SIGNATURE_PROMPT_PATH.read_text(encoding="utf-8").strip()

app = FastAPI(
    title="Laiaton - Signature Analyzer",
    description="Web system to evaluate the presence or absence of signatures in journalistic articles.",
    version="0.1.0",
)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-2-9b-it:free")
SITE_URL = os.getenv("SITE_URL", "")
SITE_NAME = os.getenv("SITE_NAME", "Laiaton Signature Analyzer")


class SignatureResult(BaseModel):
    signature_type: str = Field(
        ..., description="Type of signature found: 'name', 'initials', 'nobody'"
    )
    recognized: bool | None = Field(
        None, description="Whether the signature is recognized (appears in 25+ articles)"
    )
    responsible: str = Field(
        ..., description="Who is responsible for the article"
    )
    explanation: str = Field(
        ..., description="Detailed explanation of the analysis"
    )


def fetch_article(url: str) -> tuple[str, str]:
    """Fetch article title and text from a URL."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Try to get title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # Remove script and style elements
    for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
        element.decompose()

    # Get text
    text = soup.get_text(separator="\n", strip=True)
    # Clean up excessive blank lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)

    return title, text


def analyze_with_openrouter(title: str, text: str) -> dict:
    """Call OpenRouter to analyze signatures using the prompt."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not configured in environment")

    system_prompt = (
        "You are a journalistic analysis assistant. "
        "Analyze the provided article and respond ONLY with a valid JSON object. "
        "Do not include markdown formatting, explanations, or anything outside the JSON."
    )

    user_prompt = f"""{SIGNATURE_PROMPT}

Article Title:
{title}

Article Body:
{text[:4000]}

Respond ONLY with a JSON object matching this schema:
{{
  "signature_type": "name" | "initials" | "nobody",
  "recognized": true | false | null,
  "responsible": "string describing who is responsible",
  "explanation": "string with detailed reasoning"
}}
"""

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": SITE_URL,
            "X-Title": SITE_NAME,
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "top_p": 0.9,
            "max_tokens": 800,
        },
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]

    # Clean possible markdown fences
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```", 2)[-1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip("`\n ")

    return json.loads(content)


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main page with the URL input form."""
    return templates.TemplateResponse("index.html", {"request": {}})


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(url: str = Form(...)):
    """Receive a URL, fetch the article, and analyze signatures."""
    try:
        title, text = fetch_article(url)
    except Exception as exc:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": {},
                "error": f"Failed to fetch article: {exc}",
                "url": url,
            },
        )

    try:
        result = analyze_with_openrouter(title, text)
    except Exception as exc:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": {},
                "error": f"Analysis failed: {exc}",
                "url": url,
                "title": title,
                "text_preview": text[:500] + "..." if len(text) > 500 else text,
            },
        )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": {},
            "url": url,
            "title": title,
            "result": result,
            "text_preview": text[:500] + "..." if len(text) > 500 else text,
        },
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "openrouter_configured": bool(OPENROUTER_API_KEY)}
