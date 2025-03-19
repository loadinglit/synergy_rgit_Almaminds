from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import subprocess
import logging
from twelvelabs import TwelveLabs
import os
import time
from datetime import datetime
from minio import Minio
from minio.error import S3Error


@dataclass
class AdCreative:
    ad_type: str  # "bumper", "non-skippable", "skippable"
    headline: str
    description: str
    call_to_action: str
    target_audience: str
    clip_path: str
    start_time: float
    end_time: float


class GoogleAdsProcessor:
    def __init__(
        self,
        api_key: str,
        mongo_uri: Optional[str] = None,
    ):
        self.client = TwelveLabs(api_key=api_key)

        self.setup_logging()
        self.minio_client = Minio(
            "192.168.1.111:9000",  # MinIO server URL
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False,  # Set to True if using HTTPS
        )
        self.bucket_name = "video-ads"  # Change as needed
        self.create_bucket_if_not_exists()

        # MongoDB setup can be added if needed similar to YouTubeProcessor

    def create_bucket_if_not_exists(self):
        try:
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
        except S3Error as e:
            print("Error creating bucket:", e)

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    def create_ad_creatives(
        self, video_id: str, source_video_path: Path
    ) -> List[AdCreative]:
        """Extract and create Google Ads video creatives with meaningful segment boundaries."""
        ad_creatives = []
        try:
            # First, get video scene transitions and key moments
            scene_analysis_prompt = """
            Identify the most impactful and memorable moments in this video, including:
            1. Key story/message highlights
            2. Strong emotional moments
            3. Clear value propositions
            4. Brand moments
            5. Natural scene transitions around these key moments
            
            Return in JSON format:
            {
              "scene_transitions": [
            {
              "time": seconds,
              "importance_score": 1-10,
              "description": "description of key moment/transition",
              "rationale": "why this moment is impactful for ads"
            },
            ...
              ]
            }
            
            Focus on moments that would make compelling ad content rather than just scene changes.
            """
            
            self.logger.info("Analyzing video for scene transitions...")
            transitions_response = self.client.generate.text(
                video_id=video_id, prompt=scene_analysis_prompt
            )
            
            try:
                transitions_data = json.loads(transitions_response.data)
                scene_transitions = transitions_data.get("scene_transitions", [])
                transition_times = [t["time"] for t in scene_transitions]
                
                # Add video start and approximate end to transitions
                video_info = self._get_video_duration(source_video_path)
                video_duration = video_info.get("duration", 0)
                transition_times = [0] + transition_times + [video_duration]
                self.logger.info(f"Detected {len(transition_times)} scene transitions")
                
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse scene transitions")
                # Fallback to basic timestamps if scene detection fails
                video_info = self._get_video_duration(source_video_path)
                video_duration = video_info.get("duration", 0)
                # Create some basic segments at 25% intervals as fallback
                transition_times = [0, video_duration * 0.25, video_duration * 0.5, video_duration * 0.75, video_duration]
                self.logger.info(f"Using fallback transition times: {transition_times}")
                
            # Define ad formats to generate
            ad_formats = [
                # {"type": "bumper", "duration": 10},  # 6-second bumper ad
                {"type": "non-skippable", "duration": 15},  # 15-second non-skippable ad
                # {"type": "skippable", "duration": 20},  # 30-second skippable ad
            ]

            for ad_format in ad_formats:
                # Modified prompt to identify segments with natural boundaries
                ad_prompt = f"""Identify the best {ad_format['duration']}-second segment for a Google {ad_format['type']} ad.
                Use these scene transitions as potential start/end points: {transition_times}
                
                Return JSON format:
                {{
                  "ad_segment": {{
                    "headline": "compelling headline (<30 chars)",
                    "description": "ad description (<90 chars)",
                    "call_to_action": "clear CTA (<15 chars)",
                    "target_audience": "specific audience segment",
                    "start_time": transition_time_closest_to_optimal_start,
                    "end_time": transition_time_closest_to_optimal_end,
                    "segment_rationale": "why this segment makes a complete, coherent ad"
                  }}
                }}
                
                SELECTION CRITERIA:
                - As close as possible to {ad_format['duration']} seconds (within ±2 seconds)
                - MUST start and end at natural scene transitions for clean cuts
                - Complete narrative arc with beginning, middle, and end
                - Clear value proposition in first 3 seconds
                - No distracting elements
                - Strong hook and clear CTA
                - Segment must make sense as a standalone advertisement"""
                
                # Get AI-identified ad segments
                self.logger.info(f"Identifying {ad_format['type']} ad segments at natural boundaries...")
                try:
                    response = self.client.generate.text(
                        video_id=video_id, prompt=ad_prompt
                    )

                    # Parse the response
                    try:
                        result = json.loads(response.data)
                        if "ad_segment" in result:
                            ad_data = result["ad_segment"]

                            # Get timestamps from response
                            start_time = float(ad_data.get("start_time", 0))
                            end_time = float(ad_data.get("end_time", start_time + ad_format["duration"]))
                            segment_rationale = ad_data.get("segment_rationale", "")
                            
                            # Validate duration and adjust if needed
                            actual_duration = end_time - start_time
                            if abs(actual_duration - ad_format["duration"]) > 2:
                                self.logger.warning(f"Duration mismatch: {actual_duration}s vs expected {ad_format['duration']}s")
                                
                                # Find closest transition points that give us the right duration
                                best_start = start_time
                                best_end = end_time
                                best_diff = abs(actual_duration - ad_format["duration"])
                                
                                for t_start in transition_times:
                                    for t_end in transition_times:
                                        if t_end <= t_start:
                                            continue
                                        diff = abs((t_end - t_start) - ad_format["duration"])
                                        if diff < best_diff:
                                            best_start = t_start
                                            best_end = t_end
                                            best_diff = diff
                                
                                start_time = best_start
                                end_time = best_end
                                self.logger.info(f"Adjusted timestamps to {start_time}-{end_time} (duration: {end_time-start_time}s)")
                            
                            # Validate segment makes sense with a second prompt
                            segment_validation_prompt = f"""
                            Review the video segment from {start_time} to {end_time} seconds.
                            Does this segment make a coherent, standalone advertisement?
                            Consider: Does it have a beginning, middle, and end? Is any important content cut off?
                            
                            Return JSON:
                            {{
                              "is_coherent": true/false,
                              "improved_start": better_start_time_if_needed,
                              "improved_end": better_end_time_if_needed,
                              "reason": "explanation of why changes were needed or why segment is good"
                            }}
                            """
                            
                            self.logger.info(f"Validating segment coherence...")
                            validation_response = self.client.generate.text(
                                video_id=video_id, prompt=segment_validation_prompt
                            )
                            
                            try:
                                validation_data = json.loads(validation_response.data)
                                if not validation_data.get("is_coherent", True):
                                    # Update timestamps if needed
                                    new_start = validation_data.get("improved_start")
                                    new_end = validation_data.get("improved_end")
                                    reason = validation_data.get("reason", "")
                                    
                                    if new_start is not None and new_end is not None:
                                        start_time = float(new_start)
                                        end_time = float(new_end)
                                        self.logger.info(f"Adjusted timestamps for coherence: {start_time}-{end_time}")
                                        self.logger.info(f"Reason: {reason}")
                                
                            except json.JSONDecodeError:
                                self.logger.warning(f"Failed to parse validation response")

                            # Create directory for ad creatives
                            ads_dir = source_video_path.parent / "ads"
                            ads_dir.mkdir(exist_ok=True)

                            # Create a safe filename from headline
                            safe_headline = "".join(
                                c
                                for c in ad_data.get("headline", "")
                                if c.isalnum() or c in " "
                            ).strip()[:20]

                            output_file = (
                                ads_dir / f"{ad_format['type']}_{safe_headline}.mp4"
                            )

                            # Extract the clip with accurate timestamps
                            cmd = [
                                "ffmpeg",
                                "-i",
                                str(source_video_path),
                                "-ss",
                                str(start_time),
                                "-to",
                                str(end_time),
                                "-c:v",
                                "copy",
                                "-c:a",
                                "copy",
                                str(output_file),
                                "-y",
                            ]
                            self.logger.info(f"Extracting clip from {start_time}s to {end_time}s...")
                            subprocess.run(cmd, check=True, capture_output=True)

                            # Upload to MinIO
                            self.upload_to_minio(output_file)

                            # Create ad creative object
                            ad_creative = AdCreative(
                                ad_type=ad_format["type"],
                                headline=ad_data.get("headline", ""),
                                description=ad_data.get("description", ""),
                                call_to_action=ad_data.get("call_to_action", ""),
                                target_audience=ad_data.get("target_audience", ""),
                                clip_path=str(
                                    output_file
                                ),  # Keep local path for logging
                                start_time=start_time,
                                end_time=end_time,
                            )

                            ad_creatives.append(ad_creative)
                            self.logger.info(
                                f"Created {ad_format['type']} ad creative: {output_file} ({end_time-start_time:.1f}s)"
                            )
                            self.logger.info(f"Headline: {ad_data.get('headline', '')}")
                            self.logger.info(f"CTA: {ad_data.get('call_to_action', '')}")

                    except json.JSONDecodeError:
                        self.logger.warning(
                            f"Failed to parse JSON response for {ad_format['type']}"
                        )

                except Exception as e:
                    self.logger.error(
                        f"Error processing {ad_format['type']} ad: {str(e)}"
                    )

            return ad_creatives

        except Exception as e:
            self.logger.error(f"Error extracting ad creatives: {str(e)}")
            raise

    def upload_to_minio(self, file_path: Path):
        try:
            self.minio_client.fput_object(
                self.bucket_name, file_path.name, str(file_path)
            )
            self.logger.info(f"Uploaded {file_path.name} to MinIO")
        except S3Error as e:
            self.logger.error(f"Error uploading to MinIO: {str(e)}")

    def _get_video_duration(self, video_path: Path) -> Dict[str, Any]:
        """Get video duration using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                str(video_path)
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            data = json.loads(result.stdout)
            return {"duration": float(data["format"]["duration"])}
        except Exception as e:
            self.logger.error(f"Error getting video duration: {str(e)}")
            return {"duration": 0}

    def get_ad_strategy(self, video_id: str) -> Dict[str, Any]:
        """Get ad campaign strategy recommendations."""
        try:
            strategy_prompt = """Provide Google Ads campaign strategy recommendations in JSON:
{
  "campaign_objective": "primary objective",
  "audience_segments": ["segment1", "segment2", "segment3"],
  "bidding_strategy": "recommended strategy",
  "targeting_recommendations": ["recommendation1", "recommendation2"],
  "performance_metrics": ["key metric1", "key metric2"]
}

Focus on:
1. Clear campaign objective based on content
2. Specific audience segmentation
3. Appropriate bidding strategy
4. Targeting recommendations
5. Key performance metrics to track"""

            response = self.client.generate.text(
                video_id=video_id, prompt=strategy_prompt
            )

            try:
                return json.loads(response.data)
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse JSON from strategy response")
                # Return a simplified structure if parsing fails
                return {
                    "campaign_objective": "Brand awareness",
                    "audience_segments": ["General audience"],
                    "bidding_strategy": "Maximize impressions",
                    "targeting_recommendations": ["Content targeting"],
                    "performance_metrics": ["Views", "Impressions"],
                }

        except Exception as e:
            self.logger.error(f"Error getting ad strategy: {str(e)}")
            raise

    def process_video_for_ads(
        self, video_id: str, source_video_path: Path
    ) -> Dict[str, Any]:
        """Process video for Google Ads creatives."""
        try:
            # Create ad creatives
            ad_creatives = self.create_ad_creatives(video_id, source_video_path)

            # Get ad strategy recommendations
            ad_strategy = self.get_ad_strategy(video_id)

            # Create results dictionary
            result = {
                "ad_creatives": [
                    {
                        "ad_type": creative.ad_type,
                        "headline": creative.headline,
                        "description": creative.description,
                        "call_to_action": creative.call_to_action,
                        "target_audience": creative.target_audience,
                        "clip_path": creative.clip_path,
                        "start_time": creative.start_time,
                        "end_time": creative.end_time,
                    }
                    for creative in ad_creatives
                ],
                "ad_strategy": ad_strategy,
            }

            return result

        except Exception as e:
            self.logger.error(f"Error in ad processing pipeline: {str(e)}")
            raise