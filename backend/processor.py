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

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

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

    def extract_highlights(self, video_id: str, source_video_path: Path) -> List[VideoHighlight]:
       
        """Extract meaningful video highlights based on content importance rather than fixed durations."""
        highlights = []
        try:
            # Create directory for highlights
            highlights_dir = source_video_path.parent / "highlights"
            highlights_dir.mkdir(exist_ok=True)
            
            # Use a more direct prompt focused on finding important moments
            key_moments_prompt = """
            Find the 3 most important moments in this video that would be valuable for viewers or marketing.
            For each moment:
            1. Identify a natural segment with clear beginning and end points
            2. Ensure the segment contains complete thoughts and coherent content
            3. Focus on the most informative, engaging, or persuasive parts
            4. Vary your selections to capture different aspects of the video
            
            Return your analysis in JSON format:
            {
                "key_moments": [
                    {
                        "description": "Clear description of what makes this moment important",
                        "start_time": start_time_in_seconds,
                        "end_time": end_time_in_seconds,
                        "importance_score": score_from_1_to_10,
                        "key_takeaway": "The main point or value of this segment"
                    }
                ]
            }
            """
            
            # Get content analysis
            self.logger.info("Finding key moments based on content importance...")
            content_analysis = self.client.generate.text(
                video_id=video_id, prompt=key_moments_prompt
            )
            
            # Parse content analysis
            key_moments = []
            try:
                analysis_data = json.loads(content_analysis.data)
                if "key_moments" in analysis_data:
                    key_moments = analysis_data["key_moments"]
                    self.logger.info(f"Found {len(key_moments)} key moments")
                else:
                    self.logger.warning("No key moments found in content analysis")
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse content analysis results")
                # Try to extract anything that looks like JSON
                try:
                    text = content_analysis.data
                    json_start = text.find('{')
                    json_end = text.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_text = text[json_start:json_end]
                        analysis_data = json.loads(json_text)
                        if "key_moments" in analysis_data:
                            key_moments = analysis_data["key_moments"]
                            self.logger.info(f"Extracted {len(key_moments)} key moments from partial JSON")
                except:
                    self.logger.warning("Failed to extract partial JSON")
            
            # If no key moments found, try a backup approach
            if not key_moments:
                self.logger.info("Using standard highlights as fallback...")
                standard_highlights = self.client.generate.summarize(
                    video_id=video_id, type="highlight"
                )
                
                # Process each standard highlight
                for i, highlight in enumerate(standard_highlights.highlights[:5]):  # Limit to 5
                    start_time = float(highlight.start)
                    
                    # Find a natural endpoint for this segment
                    segment_prompt = f"""
                    A key moment in this video starts at {start_time} seconds. 
                    Find the natural ending point for this segment where the thought or idea completes.
                    The segment should be between 15-30 seconds for optimal engagement.
                    
                    Return only: {{"end_time": natural_end_time_in_seconds}}
                    """
                    
                    segment_response = self.client.generate.text(
                        video_id=video_id, prompt=segment_prompt
                    )
                    
                    try:
                        segment_data = json.loads(segment_response.data)
                        end_time = float(segment_data.get("end_time", start_time + 30))
                    except:
                        # If parsing fails, use a reasonable default duration
                        end_time = start_time + 30
                    
                    # Ensure minimum and maximum durations
                    if end_time - start_time < 10:
                        end_time = start_time + 15
                    elif end_time - start_time > 30:
                        end_time = start_time + 30
                    
                    key_moments.append({
                        "description": highlight.highlight,
                        "start_time": start_time,
                        "end_time": end_time,
                        "importance_score": 8,  # Default high score for fallback
                        "key_takeaway": highlight.highlight
                    })
            
            # Sort key moments by importance score
            key_moments.sort(key=lambda x: x.get("importance_score", 0), reverse=True)
            
            # Process key moments
            for i, moment in enumerate(key_moments):
                try:
                    start_time = float(moment.get("start_time", 0))
                    end_time = float(moment.get("end_time", 0))
                    description = moment.get("description", f"Key Moment {i+1}")
                    
                    # Enforce duration between 15-30 seconds
                    duration = end_time - start_time
                    if duration < 15:
                        # If too short, extend to at least 15 seconds
                        self.logger.info(f"Clip {i+1} too short ({duration:.1f}s), extending to 15s")
                        end_time = start_time + 15
                    elif duration > 30:
                        # If too long, limit to 30 seconds
                        self.logger.info(f"Clip {i+1} too long ({duration:.1f}s), trimming to 30s")
                        end_time = start_time + 30
                    
                    # Recalculate duration after adjustments
                    duration = end_time - start_time
                    
                    # Create a safe filename
                    safe_text = "".join(c for c in description if c.isalnum() or c in " ").strip()[:30]
                    output_file = highlights_dir / f"key_moment_{i+1}_{int(duration)}sec_{safe_text}.mp4"
                    
                    self.logger.info(f"Creating clip {i+1}: {start_time:.1f}s to {end_time:.1f}s ({duration:.1f}s)")
                    
                    # Extract the clip with re-encoding for more precise cuts
                    cmd = [
                        "ffmpeg",
                        "-i", str(source_video_path),
                        "-ss", str(start_time),
                        "-to", str(end_time),
                        "-c:v", "libx264",  # Re-encode video instead of copy
                        "-c:a", "aac",      # Re-encode audio
                        "-b:a", "192k",     # Set audio bitrate
                        "-preset", "fast",  # Faster encoding
                        str(output_file),
                        "-y",
                    ]
                    subprocess.run(cmd, check=True, capture_output=True)
                    
                    # Add to highlights
                    highlights.append(
                        VideoHighlight(
                            text=description,
                            start_time=start_time,
                            end_time=end_time,
                            clip_path=str(output_file),
                        )
                    )
                    self.logger.info(f"Created clip: {output_file} - Duration: {duration:.1f}s")
                except Exception as e:
                    self.logger.error(f"Error processing moment: {str(e)}")
            
            return highlights
        except Exception as e:
            self.logger.error(f"Error extracting highlights: {str(e)}")
            raise

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
