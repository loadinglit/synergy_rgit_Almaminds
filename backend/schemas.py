from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional


class VideoRequest(BaseModel):
    url: HttpUrl


class Highlight(BaseModel):
    text: str
    start_time: float
    end_time: float
    clip_path: str


class Chapter(BaseModel):
    number: int
    title: str
    start: float
    end: float


class VideoResponse(BaseModel):
    video_id: str
    title: str
    summary: str
    highlights: List[Highlight]
    # chapters: List[Chapter]
    keywords: List[str]
    marketing_insights: Dict

    class Config:
        schema_extra = {
            "example": {
                "video_id": "abc123",
                "title": "Sample Video Title",
                "summary": "A comprehensive summary of the video content...",
                "highlights": [
                    {
                        "text": "Key moment description",
                        "start_time": 10.5,
                        "end_time": 30.5,
                        "clip_path": "/path/to/highlight.mp4",
                    }
                ],
                # "chapters": [
                #     {"number": 1, "title": "Introduction", "start": 0.0, "end": 60.0}
                # ],
                "keywords": ["keyword1", "keyword2", "keyword3"],
                "marketing_insights": {
                    "target_audience": "Description of target audience",
                    "ad_copy_themes": ["theme1", "theme2"],
                    "content_opportunities": ["opportunity1", "opportunity2"],
                },
            }
        }
