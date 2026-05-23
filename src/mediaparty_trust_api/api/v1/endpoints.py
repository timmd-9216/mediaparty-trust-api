"""Article analysis endpoints."""

from typing import List

from fastapi import APIRouter, HTTPException, status

from mediaparty_trust_api.models import ArticleInput, Metric
from mediaparty_trust_api.services.metrics import (
    get_adjective_count,
    get_sentence_complexity,
    get_titular_content_relation,
    get_verb_tense_analysis,
    get_word_count,
)
from mediaparty_trust_api.services.stanza_service import stanza_service

router = APIRouter()


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
