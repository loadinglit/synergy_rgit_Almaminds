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
                        "end_time": 20.5,
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


class AdCreative(BaseModel):
    ad_type: str
    headline: str
    description: str
    call_to_action: str
    target_audience: str
    clip_path: str
    start_time: float
    end_time: float


class AdStrategy(BaseModel):
    campaign_objective: str
    audience_segments: List[str]
    bidding_strategy: str
    targeting_recommendations: List[str]
    performance_metrics: List[str]


class GoogleAdsResponse(BaseModel):
    video_id: str
    title: str
    ad_creatives: List[AdCreative]
    ad_strategy: AdStrategy

    class Config:
        schema_extra = {
            "example": {
                "video_id": "abc123",
                "title": "Sample Video Title",
                "ad_creatives": [
                    {
                        "ad_type": "bumper",
                        "headline": "Amazing Product",
                        "description": "Transform your life with our revolutionary solution",
                        "call_to_action": "Shop Now",
                        "target_audience": "Tech enthusiasts",
                        "clip_path": "/path/to/ad.mp4",
                        "start_time": 45.2,
                        "end_time": 51.2,
                    }
                ],
                "ad_strategy": {
                    "campaign_objective": "Brand awareness",
                    "audience_segments": ["Males 25-34", "Tech enthusiasts"],
                    "bidding_strategy": "Maximize impressions",
                    "targeting_recommendations": [
                        "Content targeting",
                        "Affinity audiences",
                    ],
                    "performance_metrics": ["View rate", "Click-through rate"],
                },
            }
        }
