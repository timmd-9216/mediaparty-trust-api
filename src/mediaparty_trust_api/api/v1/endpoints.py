"""Article analysis endpoints."""

from typing import List

from fastapi import APIRouter, HTTPException, status

from mediaparty_trust_api.models import ArticleInput, Metric
from mediaparty_trust_api.services.metrics import (
    get_adjective_count,
    get_sentence_complexity,
    get_verb_tense_analysis,
    get_word_count,
)
from mediaparty_trust_api.services.stanza_service import stanza_service

router = APIRouter()


@router.post("/analyze", status_code=status.HTTP_200_OK, response_model=List[Metric])
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
        # Check if Stanza is initialized
        if not stanza_service.is_initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="NLP service not initialized. Please try again later.",
            )

        # Combine title and body for full text analysis
        full_text = f"{article.title}. {article.body}"

        # Create Stanza document
        doc = stanza_service.create_doc(full_text)

        # Calculate metrics using Stanza analysis
        metrics = [
            get_adjective_count(doc, metric_id=0),
            get_word_count(doc, metric_id=1),
            get_sentence_complexity(doc, metric_id=2),
            get_verb_tense_analysis(doc, metric_id=3),
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
