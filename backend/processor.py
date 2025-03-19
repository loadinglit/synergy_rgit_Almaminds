from twelvelabs import TwelveLabs
import os
from pytube import YouTube
import logging
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
import subprocess
from datetime import datetime
import json
import time
from urllib.parse import urlparse, parse_qs
import yt_dlp
from pymongo import MongoClient
from minio import Minio
from minio.error import S3Error


@dataclass
class VideoHighlight:
    text: str
    start_time: float
    end_time: float
    clip_path: str


@dataclass
class VideoAnalysis:
    video_id: str
    title: str
    summary: str
    highlights: List[VideoHighlight]
    # chapters: List[dict]
    keywords: List[str]
    marketing_insights: dict


class YouTubeProcessor:
    def __init__(
        self,
        api_key: str,
        output_dir: str = "processed_videos",
        mongo_uri: str = "mongodb+srv://dhruvpatel:dhruv77@cluster0.sedmq.mongodb.net/",
    ):
        self.client = TwelveLabs(api_key=api_key)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client["video_analysis"]
        self.collection = self.db["video_metadata"]
        self.setup_logging()
        self.minio_client = Minio(
            "192.168.1.111:9000",  # MinIO server URL
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False,  # Set to True if using HTTPS
        )
        self.bucket_name = "video-highlights"  # Change as needed
        self.create_bucket_if_not_exists()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    def create_bucket_if_not_exists(self):
        try:
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
        except S3Error as e:
            print("Error creating bucket:", e)

    def download_youtube_video(
        self, url: str, cookies_path: Optional[str] = None
    ) -> Path:
        """Download YouTube video using yt-dlp with optional authentication."""
        try:
            video_dir = self.output_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
            video_dir.mkdir(parents=True, exist_ok=True)
            video_path = video_dir / "source_video.mp4"

            ydl_opts = {
                "format": "best[ext=mp4]",
                "outtmpl": str(video_path),
                "retries": 10,
                "fragment_retries": 10,
                "retry_sleep": lambda attempt: 2**attempt,
                "ignoreerrors": False,
                "no_warnings": False,
                "quiet": False,
                "verbose": True,
                "progress_hooks": [self._download_progress_hook],
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                },
                "nocheckcertificate": True,
            }

            # Add cookies if provided
            if cookies_path and os.path.exists(cookies_path):
                ydl_opts["cookiefile"] = cookies_path

            # Try different formats if the best quality fails
            formats_to_try = [
                "best[ext=mp4]",
                "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
                "22/18/17",
            ]

            for video_format in formats_to_try:
                try:
                    ydl_opts["format"] = video_format
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        self.logger.info(
                            f"Attempting download with format: {video_format}"
                        )
                        ydl.download([url])
                        if video_path.exists() and video_path.stat().st_size > 0:
                            self.logger.info(
                                f"Successfully downloaded video to {video_path}"
                            )
                            return video_path
                except Exception as e:
                    self.logger.warning(f"Format {video_format} failed: {str(e)}")
                    continue

            raise ValueError("All download attempts failed")

        except Exception as e:
            error_msg = f"Error downloading YouTube video: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

    def _download_progress_hook(self, d):
        """Progress hook for download status."""
        if d["status"] == "downloading":
            try:
                percent = d["_percent_str"]
                speed = d["_speed_str"]
                self.logger.info(f"Downloading... {percent} at {speed}")
            except KeyError:
                pass
        elif d["status"] == "finished":
            self.logger.info("Download completed")
        elif d["status"] == "error":
            self.logger.error(f"Download error: {d.get('error')}")

    def create_index_and_process_video(self, video_path: Path) -> str:
        """Create index and process video, return video_id."""
        try:
            # Create index
            models = [
                {"name": "marengo2.7", "options": ["visual", "audio"]},
                {"name": "pegasus1.2", "options": ["visual", "audio"]},
            ]

            index = self.client.index.create(
                name=f"video_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                models=models,
                addons=["thumbnail"],
            )

            # Upload and process video
            task = self.client.task.create(
                index_id=index.id,
                file=str(video_path),
            )

            self.logger.info("Processing video...")
            task.wait_for_done(sleep_interval=5)

            if task.status != "ready":
                raise RuntimeError(f"Indexing failed with status {task.status}")

            return task.video_id

        except Exception as e:
            self.logger.error(f"Error processing video: {str(e)}")
            raise

    def extract_highlights(
        self, video_id: str, source_video_path: Path
    ) -> List[VideoHighlight]:
        """Extract and create video highlights."""
        highlights = []
        try:
            # Custom prompt to identify the most important key moments
            key_moments_prompt = """Analyze this video and identify EXACTLY 3-5 high-engagement moments 
            that would be PERFECT FOR YOUTUBE SHORTS (vertical, 30-second content).

            
            For each moment, provide:
            {
            "key_moments": [
                {
                "description": "Why this makes a great YouTube Short",
                "start_time": start_time_in_seconds,
                "end_time": end_time_in_seconds
                }
            ]
            }

            STRICTLY SELECT ONLY MOMENTS THAT:
            - Are EXACTLY 15-30 seconds long
            - Have attention-grabbing first 3 seconds
            - Contain emotional impact or clear value
            - Would work well vertically without context
            - Have viral potential (surprising elements)
            - Would generate high engagement (comments, shares)
            - Align with current YouTube Shorts trends
            - Include clear call-to-action opportunity

            PRIORITIZE moments with:
            - Strong emotional reactions
            - Surprising revelations
            - Valuable demonstrations
            - Narrative completeness within 30 seconds
            - Potential for trending sounds/music

            """

            # Get AI-identified key moments using custom prompt
            self.logger.info("Identifying key moments using custom prompt...")
            custom_response = self.client.generate.text(
                video_id=video_id, prompt=key_moments_prompt
            )

            # Also get standard highlights as backup/additional content
            self.logger.info("Getting standard highlights...")
            standard_highlights = self.client.generate.summarize(
                video_id=video_id, type="highlight"
            )

            # Process custom key moments
            key_moments = []
            try:
                # Try to parse the JSON response
                response_data = json.loads(custom_response.data)
                if "key_moments" in response_data:
                    key_moments = response_data["key_moments"]
            except json.JSONDecodeError:
                self.logger.warning(
                    "Failed to parse JSON from custom prompt response, using standard highlights only"
                )

            # Create directory for highlights
            highlights_dir = source_video_path.parent / "highlights"
            highlights_dir.mkdir(exist_ok=True)

            # Process custom key moments first
            for i, moment in enumerate(key_moments):
                try:
                    description = moment.get("description", "Key moment")
                    start_time = float(moment.get("start_time", 0))
                    end_time = float(moment.get("end_time", 0))

                    if end_time <= start_time or end_time - start_time < 1:
                        self.logger.warning(
                            f"Invalid time range for moment: {description}"
                        )
                        continue

                    if duration < 15 or duration > 30:
                        self.logger.warning(
                            f"Short {i+1} has invalid duration ({duration}s). Adjusting to 30s maximum."
                        )
                    # If too long, cap at 30 seconds
                    if duration > 30:
                        end_time = start_time + 30

                    safe_text = "".join(
                        c for c in description if c.isalnum() or c in " "
                    ).strip()[:30]
                    output_file = (
                        ads_dir
                        / f"{ad_format['type']}_{safe_headline}_{int(datetime.now().timestamp())}.mp4"
                    )

                    # For vertical cropping optimized for YouTube Shorts
                    cmd = [
                        "ffmpeg",
                        "-i",
                        str(source_video_path),
                        "-ss",
                        str(start_time),
                        "-to",
                        str(end_time),
                        "-vf",
                        "crop=ih*9/16:ih,scale=1080:1920",  # Crop to 9:16 aspect ratio, scale to 1080x1920
                        "-c:a",
                        "copy",
                        str(output_file),
                        "-y",
                    ]
                    subprocess.run(cmd, check=True, capture_output=True)

                    # Upload to MinIO
                    self.upload_to_minio(output_file)

                    highlights.append(
                        VideoHighlight(
                            text=description,
                            start_time=start_time,
                            end_time=end_time,
                            clip_path=str(output_file),
                        )
                    )
                    self.logger.info(f"Created key moment clip: {output_file}")
                except Exception as e:
                    self.logger.error(f"Error processing custom key moment: {str(e)}")

            # If no custom key moments were successfully processed, fall back to standard highlights
            if not highlights:
                self.logger.info(
                    "No custom key moments were successfully processed, using standard highlights"
                )
                for i, highlight in enumerate(standard_highlights.highlights):
                    try:
                        safe_text = "".join(
                            c for c in highlight.highlight if c.isalnum() or c in " "
                        ).strip()[:30]
                        output_file = (
                            highlights_dir / f"highlight_{i+1}_{safe_text}.mp4"
                        )

                        cmd = [
                            "ffmpeg",
                            "-i",
                            str(source_video_path),
                            "-ss",
                            str(highlight.start),
                            "-to",
                            str(highlight.end),
                            "-c:v",
                            "copy",
                            "-c:a",
                            "copy",
                            str(output_file),
                            "-y",
                        ]
                        subprocess.run(cmd, check=True, capture_output=True)

                        # Upload to MinIO
                        self.upload_to_minio(output_file)

                        highlights.append(
                            VideoHighlight(
                                text=highlight.highlight,
                                start_time=highlight.start,
                                end_time=highlight.end,
                                clip_path=str(output_file),
                            )
                        )
                        self.logger.info(
                            f"Created standard highlight clip: {output_file}"
                        )
                    except subprocess.CalledProcessError as e:
                        self.logger.error(f"FFmpeg error: {e.stderr.decode()}")
                        continue

            return highlights
        except Exception as e:
            self.logger.error(f"Error extracting highlights: {str(e)}")
            raise

    def upload_to_minio(self, file_path: Path):
        try:
            self.minio_client.fput_object(
                self.bucket_name, file_path.name, str(file_path)
            )
            self.logger.info(f"Uploaded {file_path.name} to MinIO")
        except S3Error as e:
            self.logger.error(f"Error uploading to MinIO: {str(e)}")

    def get_enhanced_keywords(self, video_id: str) -> dict:
        """Get enhanced keywords and marketing insights."""
        try:
            # Shortened prompt for marketing insights
            marketing_prompt = """Provide JSON with:
                {
                    "shorts_keywords": ["keyword1", "keyword2", "keyword3"],
                    "shorts_target_audience": "description",
                    "shorts_hooks": ["hook1", "hook2"],
                    "shorts_music_recommendations": ["sound1", "sound2"],
                    "shorts_engagement_triggers": ["prompt1", "prompt2"],
                    "shorts_call_to_actions": ["CTA1"],
                    "shorts_popular_formats": ["format1"],       
                    "emotional_triggers": ["trigger1"]
                }
                Focus on YouTube Shorts performance metrics.
            """

            response = self.client.generate.text(
                video_id=video_id, prompt=marketing_prompt
            )

            try:
                # First try to parse as JSON directly
                return json.loads(response.data)
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON from the text
                self.logger.warning(
                    "Direct JSON parsing failed, attempting to extract JSON from response"
                )

                # Create a default structure
                default_response = {
                    "seo_keywords": [],
                    "target_audience": "",
                    "ad_copy_themes": [],
                    "content_elements": [],
                    "campaign_objectives": [],
                    "content_marketing_opportunities": [],
                    "emotional_triggers": [],
                }

                # If we can't parse JSON, extract information manually
                text_response = str(response.data)

                # Try to extract information using simple text parsing
                try:
                    # Extract keywords
                    if "seo_keywords" in text_response.lower():
                        keywords = [
                            word.strip(' "[](),.')
                            for word in text_response.split("keywords")[1]
                            .split("\n")[0]
                            .split(",")
                            if word.strip()
                        ]
                        default_response["seo_keywords"] = keywords[
                            :5
                        ]  # Take up to 5 keywords

                    # Extract other information (simplified version)
                    for key in default_response.keys():
                        if key in text_response.lower():
                            section = text_response.split(key)[1].split("\n")[0]
                            values = [
                                item.strip(' "[](),.')
                                for item in section.split(",")
                                if item.strip()
                            ]
                            default_response[key] = values

                    return default_response

                except Exception as parsing_error:
                    self.logger.error(f"Error parsing response text: {parsing_error}")
                    return default_response

        except Exception as e:
            self.logger.error(f"Error getting keywords: {str(e)}")
            raise

    def save_video_analysis_to_mongo(self, video_analysis: VideoAnalysis):
        """Save video analysis data to MongoDB, excluding chapters."""
        data_to_save = {
            "video_id": video_analysis.video_id,
            "title": video_analysis.title,
            "summary": video_analysis.summary,
            "highlights": [
                {
                    "text": highlight.text,
                    "start_time": highlight.start_time,
                    "end_time": highlight.end_time,
                    "clip_path": highlight.clip_path,
                }
                for highlight in video_analysis.highlights
            ],
            "keywords": video_analysis.keywords,
            "marketing_insights": video_analysis.marketing_insights,
        }
        self.collection.insert_one(data_to_save)
        self.logger.info(f"Video analysis saved to MongoDB: {data_to_save}")

    def process_youtube_url(self, url: str) -> VideoAnalysis:
        """Main pipeline to process YouTube URL and return analysis."""
        try:
            # Download video
            video_path = self.download_youtube_video(url)

            # Process video
            video_id = self.create_index_and_process_video(video_path)

            # Get summary
            summary = self.client.generate.summarize(
                video_id=video_id, type="summary"
            ).summary

            # Get highlights
            highlights = self.extract_highlights(video_id, video_path)

            # Get enhanced keywords and marketing insights
            marketing_data = self.get_enhanced_keywords(video_id)

            # Get title (without using pytube)
            try:
                with yt_dlp.YoutubeDL() as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get("title", "Unknown Title")
            except Exception as e:
                self.logger.warning(f"Error getting title: {e}")
                title = "Unknown Title"

            video_analysis = VideoAnalysis(
                video_id=video_id,
                title=title,
                summary=summary,
                highlights=highlights,
                keywords=marketing_data.get("seo_keywords", []),
                marketing_insights=marketing_data,
            )

            # Save to MongoDB
            self.save_video_analysis_to_mongo(video_analysis)

            return video_analysis

        except Exception as e:
            self.logger.error(f"Error in processing pipeline: {str(e)}")
            raise
