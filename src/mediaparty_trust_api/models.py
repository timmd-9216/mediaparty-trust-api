from typing import Literal

from pydantic import BaseModel, Field


class ArticleInput(BaseModel):
    """
    Input model for article analysis endpoint.
    """

    body: str = Field(..., description="The main content/body of the article")
    title: str = Field(..., description="The title of the article")
    author: str = Field(..., description="The author of the article")
    link: str = Field(..., description="The URL/link to the article")
    date: str = Field(..., description="The publication date of the article")
    media_type: str = Field(
        ..., description="The type of media (e.g., 'news', 'blog', 'social')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "body": "This is the main content of the article...",
                "title": "Example Article Title",
                "author": "John Doe",
                "link": "https://example.com/article",
                "date": "2025-10-04",
                "media_type": "news",
            }
        }


class Metric(BaseModel):
    """
    Individual metric result from article analysis.
    """

    id: int = Field(..., description="Unique identifier for the metric")
    criteria_name: str = Field(..., description="Name of the criteria being evaluated")
    explanation: str = Field(
        ..., description="Detailed explanation of the metric result"
    )
    flag: Literal[-1, 0, 1] = Field(
        ...,
        description="Flag indicating the result: -1 (negative), 0 (neutral), 1 (positive)",
    )
    score: float = Field(..., ge=0.0, le=1.0, description="Score between 0.0 and 1.0")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 0,
                "criteria_name": "Pyramid",
                "explanation": "The inverted pyramid criteria for good journalism is not respected.",
                "flag": -1,
                "score": 0.2,
            }
        }
