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
