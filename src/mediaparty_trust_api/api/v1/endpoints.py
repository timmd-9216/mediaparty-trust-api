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
        # Combine title and body for full text analysis
        full_text = f"{article.title}. {article.body}"

        # Create Stanza document if available; metrics degrade gracefully without it
        doc = stanza_service.create_doc(full_text) if stanza_service.is_initialized else None

        # Calculate metrics; each function accepts text + optional doc
        metrics = [
            get_adjective_count(full_text, metric_id=0, doc=doc),
            get_word_count(full_text, metric_id=1, doc=doc),
            get_sentence_complexity(full_text, metric_id=2, doc=doc),
            get_verb_tense_analysis(full_text, metric_id=3, doc=doc),
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
