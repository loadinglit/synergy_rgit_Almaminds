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
        output_dir: str = "processed_ads",
        mongo_uri: Optional[str] = None,
    ):
        self.client = TwelveLabs(api_key=api_key)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.setup_logging()

        # MongoDB setup can be added if needed similar to YouTubeProcessor

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    def create_ad_creatives(
        self, video_id: str, source_video_path: Path
    ) -> List[AdCreative]:
        """Extract and create Google Ads video creatives."""
        ad_creatives = []
        try:
            # Define ad formats to generate
            ad_formats = [
                {"type": "bumper", "duration": 6},  # 6-second bumper ad
                {"type": "non-skippable", "duration": 15},  # 15-second non-skippable ad
                {"type": "skippable", "duration": 30},  # 30-second skippable ad
            ]

            for ad_format in ad_formats:
                # Custom prompt for each ad format
                ad_prompt = f"""Identify the best {ad_format['duration']}-second segment for a Google {ad_format['type']} ad.

Return JSON format:
{{
  "ad_segment": {{
    "headline": "compelling headline (<30 chars)",
    "description": "ad description (<90 chars)",
    "call_to_action": "clear CTA (<15 chars)",
    "target_audience": "specific audience segment",
    "start_time": start_time_in_seconds,
    "end_time": start_time_in_seconds + {ad_format['duration']}
  }}
}}

SELECTION CRITERIA:
- EXACTLY {ad_format['duration']} seconds long
- Clear value proposition in first 3 seconds
- Complete narrative arc
- No distracting elements
- Follows Google Ads guidelines
- Strong hook and clear CTA"""

                # Get AI-identified ad segments
                self.logger.info(f"Identifying {ad_format['type']} ad segments...")
                try:
                    response = self.client.generate.text(
                        video_id=video_id, prompt=ad_prompt
                    )

                    # Parse the response
                    try:
                        result = json.loads(response.data)
                        if "ad_segment" in result:
                            ad_data = result["ad_segment"]

                            # Validate duration
                            start_time = float(ad_data.get("start_time", 0))
                            end_time = float(
                                ad_data.get(
                                    "end_time", start_time + ad_format["duration"]
                                )
                            )

                            # If duration doesn't match expected, adjust end_time
                            if round(end_time - start_time) != ad_format["duration"]:
                                end_time = start_time + ad_format["duration"]

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

                            # Extract the clip
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
                            subprocess.run(cmd, check=True, capture_output=True)

                            # Create ad creative object
                            ad_creative = AdCreative(
                                ad_type=ad_format["type"],
                                headline=ad_data.get("headline", ""),
                                description=ad_data.get("description", ""),
                                call_to_action=ad_data.get("call_to_action", ""),
                                target_audience=ad_data.get("target_audience", ""),
                                clip_path=str(output_file),
                                start_time=start_time,
                                end_time=end_time,
                            )

                            ad_creatives.append(ad_creative)
                            self.logger.info(
                                f"Created {ad_format['type']} ad creative: {output_file}"
                            )

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
