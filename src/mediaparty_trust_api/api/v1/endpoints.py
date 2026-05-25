"""Article analysis endpoints."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from mediaparty_trust_api.models import ArticleInput, Metric
from mediaparty_trust_api.services.metrics import (
    get_adjective_count,
    get_sentence_complexity,
    get_signature_analysis,
    get_titular_content_relation,
    get_verb_tense_analysis,
    get_word_count,
)
from mediaparty_trust_api.services.stanza_service import stanza_service
from mediaparty_trust_api.services.scraper import scrape_article, ConfigurationError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ScrapeResponse(BaseModel):
    """Response model for article scraping."""
    title: str = Field(..., description="Article title/headline")
    body: str = Field(..., description="Main article content")
    author: Optional[str] = Field(None, description="Article author if found")
    editor: Optional[str] = Field(None, description="Editor responsible from footer if found")
    media_group: Optional[str] = Field(None, description="Media group/publisher from footer if found")
    url: str = Field(..., description="Source URL")


@router.get(
    "/scrape",
    status_code=status.HTTP_200_OK,
    response_model=ScrapeResponse,
    summary="Scrape article from URL",
    description="Fetches and extracts article content (title, body, author, editor, media group) from a given URL using LLM extraction.",
    response_description="Extracted article data",
    responses={
        200: {
            "description": "Successful extraction",
            "content": {
                "application/json": {
                    "example": {
                        "title": "Example News Title",
                        "body": "Article content here...",
                        "author": "John Doe",
                        "editor": "Jane Smith",
                        "media_group": "MediaCorp Inc.",
                        "url": "https://example.com/news/article"
                    }
                }
            },
        },
        400: {
            "description": "Invalid URL",
            "content": {
                "application/json": {"example": {"detail": "Invalid URL provided"}}
            },
        },
        500: {
            "description": "Extraction failed",
            "content": {
                "application/json": {"example": {"detail": "Failed to extract article content"}}
            },
        },
    },
    tags=["Scraping"],
)
async def scrape_article_endpoint(url: str = Query(..., description="URL of the news article to scrape")) -> ScrapeResponse:
    """
    Scrape a news article from the provided URL.

    Uses LLM-based extraction to identify:
    - Article title and body content
    - Author name (if present)
    - Editor responsible (from footer/paratext)
    - Media group/publisher (from footer/paratext)

    Args:
        url: The URL of the news article

    Returns:
        ScrapeResponse with extracted article data
    """
    try:
        result = scrape_article(url)
        return ScrapeResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Scraping service not configured: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract article: {str(e)}"
        )


@router.post(
    "/analyze",
    status_code=status.HTTP_200_OK,
    response_model=List[Metric],
    summary="Analyze article for trust and credibility",
    description="Receives article data and returns NLP-based analysis results as a list of metrics including adjective count, word count, sentence complexity, and verb tense analysis.",
    response_description="List of metrics with analysis results for different criteria",
    responses={
        200: {
            "description": "Successful analysis",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 0,
                            "criteria_name": "Adjective Count",
                            "explanation": "Article contains a moderate number of adjectives.",
                            "flag": 0,
                            "score": 0.5,
                        },
                        {
                            "id": 1,
                            "criteria_name": "Word Count",
                            "explanation": "Article length is appropriate for the topic.",
                            "flag": 1,
                            "score": 0.8,
                        },
                    ]
                }
            },
        },
        503: {
            "description": "Service Unavailable - NLP service not initialized",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "NLP service not initialized. Please try again later."
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"detail": "Error processing article: <error message>"}
                }
            },
        },
    },
    tags=["Analysis"],
)
async def analyze_article(article: ArticleInput) -> List[Metric]:
    """
    Analyze an article for trust and credibility.

    This endpoint receives article data and returns analysis results as a list of metrics.

    Args:
        article: ArticleInput model containing article details

    Returns:
        List of Metric objects with analysis results for different criteria
    """
    try:
        # Debug logging
        logger.info(f"Analyze article - author: {article.author!r}, editor: {getattr(article, 'editor', None)!r}, media_group: {getattr(article, 'media_group', None)!r}")

        # Combine title and body for full text analysis
        full_text = f"{article.title}. {article.body}"

        # Create Stanza document if available; metrics degrade gracefully without it
        doc = stanza_service.create_doc(full_text) if stanza_service.is_initialized else None

        # Calculate metrics; each function accepts text + optional doc
        metrics = [
            get_adjective_count(full_text, metric_id=0, doc=doc),
            get_word_count(full_text, metric_id=1, doc=doc),
            get_sentence_complexity(full_text, metric_id=2, doc=doc),
            get_titular_content_relation(article.title, article.body, metric_id=3),
            get_verb_tense_analysis(full_text, metric_id=4, doc=doc),
            get_signature_analysis(
                author=article.author if hasattr(article, 'author') else None,
                editor=getattr(article, 'editor', None),
                media_group=getattr(article, 'media_group', None),
                metric_id=5,
            ),
        ]

        return metrics

    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing article: {str(e)}",
        )
