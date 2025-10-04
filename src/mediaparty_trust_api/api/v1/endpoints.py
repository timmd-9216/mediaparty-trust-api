"""Article analysis endpoints."""

from typing import List

from fastapi import APIRouter, HTTPException, status

from mediaparty_trust_api.models import ArticleInput, Metric

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
        # TODO: Implement actual analysis logic
        # For now, return mock metrics based on the output.json structure
        metrics = [
            Metric(
                id=0,
                criteria_name="Pyramid",
                explanation="The inverted pyramid criteria for good journalism is not respected.",
                flag=-1,
                score=0.2,
            ),
            Metric(
                id=1,
                criteria_name="Adjectives",
                explanation="The adjective ratio is good and healthy.",
                flag=1,
                score=0.9,
            ),
        ]

        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing article: {str(e)}",
        )
