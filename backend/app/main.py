from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from schemas import VideoRequest, VideoResponse
from processor import YouTubeProcessor
import os
from dotenv import load_dotenv
import logging
from typing import Dict, Any


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Video Analysis API",
    description="API for analyzing YouTube videos using TwelveLabs",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processor
processor = YouTubeProcessor(
    api_key=os.getenv("TL_API_KEY"), output_dir="processed_videos"
)


@app.post("/analyze/", response_model=VideoResponse)
async def analyze_video(request: VideoRequest) -> Dict[str, Any]:
    """
    Analyze a YouTube video and return insights
    """
    try:
        url = str(request.url)
        logger.info(f"Processing video URL: {url}")
        
        # Validate YouTube URL
        if "youtube.com" not in url and "youtu.be" not in url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid YouTube URL provided"
            )
        
        result = processor.process_youtube_url(url)
        
        return VideoResponse(
            video_id=result.video_id,
            title=result.title,
            summary=result.summary,
            highlights=[{
                "text": h.text,
                "start_time": h.start_time,
                "end_time": h.end_time,
                "clip_path": h.clip_path
            } for h in result.highlights],
            # chapters=result.chapters,
            keywords=result.keywords,
            marketing_insights=result.marketing_insights
        )
    
    except ValueError as e:
        logger.error(f"Value Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing video: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}
