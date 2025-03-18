import os
from fastapi import FastAPI, HTTPException, status, Body
from fastapi.middleware.cors import CORSMiddleware
from schemas import VideoRequest, VideoResponse
from processor import YouTubeProcessor
from pydantic import BaseModel
from pathlib import Path
from google_ads_processor import GoogleAdsProcessor  # Import the new processor
from schemas import VideoRequest, VideoResponse, GoogleAdsResponse
from dotenv import load_dotenv
import logging
from typing import Dict, Any
import yt_dlp  # Import yt_dlp for video information extraction
from pydantic import BaseModel
from minio import Minio
from minio.error import S3Error


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


# Initialize processors
youtube_processor = YouTubeProcessor(
    api_key=os.getenv("TL_API_KEY"), output_dir="processed_videos"
)

google_ads_processor = GoogleAdsProcessor(
    api_key=os.getenv("TL_API_KEY"), output_dir="processed_ads"
)

# Initialize MinIO client
minio_client = Minio(
    "192.168.1.111:9000",  # Update with your MinIO server address
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,  # Set to True if using HTTPS
)

bucket_name = "video-highlights"  # Change to your bucket name


@app.get("/files/")
async def list_files():
    """Retrieve the list of files from the MinIO bucket."""
    try:
        # List objects in the specified bucket
        objects = minio_client.list_objects(bucket_name)
        file_list = [obj.object_name for obj in objects]
        return {"files": file_list}
    except S3Error as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-for-ads/", response_model=GoogleAdsResponse)
async def analyze_for_ads(request: VideoRequest) -> Dict[str, Any]:
    """
    Analyze a YouTube video and generate Google Ads creatives
    """
    try:
        url = str(request.url)
        logger.info(f"Processing video URL for Google Ads: {url}")

        # Validate YouTube URL
        if "youtube.com" not in url and "youtu.be" not in url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid YouTube URL provided",
            )

        # Download and process the video using the YouTube processor methods
        video_path = youtube_processor.download_youtube_video(url)
        video_id = youtube_processor.create_index_and_process_video(video_path)

        # Get video title
        try:
            with yt_dlp.YoutubeDL() as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "Unknown Title")
        except Exception as e:
            logger.warning(f"Error getting title: {e}")
            title = "Unknown Title"

        # Process for Google Ads
        ads_result = google_ads_processor.process_video_for_ads(video_id, video_path)

        return GoogleAdsResponse(
            video_id=video_id,
            title=title,
            ad_creatives=ads_result["ad_creatives"],
            ad_strategy=ads_result["ad_strategy"],
        )

    except ValueError as e:
        logger.error(f"Value Error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing video for ads: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing video for ads: {str(e)}",
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
                detail="Invalid YouTube URL provided",
            )

        processor = YouTubeProcessor(
            api_key=os.getenv("TL_API_KEY"), output_dir="processed_videos"
        )
        result = processor.process_youtube_url(url)

        return VideoResponse(
            video_id=result.video_id,
            title=result.title,
            summary=result.summary,
            highlights=[
                {
                    "text": h.text,
                    "start_time": h.start_time,
                    "end_time": h.end_time,
                    "clip_path": h.clip_path,
                }
                for h in result.highlights
            ],
            # chapters=result.chapters,
            keywords=result.keywords,
            marketing_insights=result.marketing_insights,
        )

    except ValueError as e:
        logger.error(f"Value Error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing video: {str(e)}",
        )


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}


class LocalVideoRequest(BaseModel):
    file_path: str


@app.post("/process-local-video/")
async def process_local_video(request: LocalVideoRequest):
    """Process a local video file and generate ads"""
    try:
        file_path = Path(request.file_path)
        
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Video file not found: {file_path}"
            )
        
        logger.info(f"Processing local video: {file_path}")
        
        # Create video ID for processing (could be the filename)
        video_id = f"local_{file_path.stem}"
        
        # Index the video (assuming your processor can handle local files)
        # If not, you may need to adapt this part
        video_id = youtube_processor.create_index_and_process_video(file_path)
        
        # Process for Google Ads
        ads_result = google_ads_processor.process_video_for_ads(video_id, file_path)
        
        return {
            "video_id": video_id,
            "title": file_path.stem,
            "ad_creatives": ads_result["ad_creatives"],
            "ad_strategy": ads_result["ad_strategy"]
        }
        
    except Exception as e:
        logger.error(f"Error processing local video: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing video: {str(e)}"
        )
