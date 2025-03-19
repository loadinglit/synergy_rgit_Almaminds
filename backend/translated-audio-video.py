from twelvelabs import TwelveLabs
from pathlib import Path
import subprocess
import logging
import os
import json
import base64
import requests
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class VideoTranslator:
    def __init__(
        self,
        twelvelabs_api_key: str,
        sarvam_api_key: str,
        output_dir: str = "translated_videos",
        target_language: str = "en-IN",  # Default to Hindi
    ):
        self.twelvelabs_client = TwelveLabs(api_key=twelvelabs_api_key)
        self.sarvam_api_key = sarvam_api_key
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.target_language = target_language
        self.sarvam_tts_url = "https://api.sarvam.ai/text-to-speech"
        
    def get_transcript(self, video_id: str) -> str:
        """Extract transcript from a video using Twelve Labs API"""
        try:
            transcript_prompt = "Provide a complete, verbatim transcript of all spoken words in this video."
            
            # Generate transcript using Twelve Labs
            logger.info(f"Generating transcript for video ID: {video_id}")
            transcript_response = self.twelvelabs_client.generate.text(
                video_id=video_id, prompt=transcript_prompt
            )
            
            return transcript_response.data
            
        except Exception as e:
            logger.error(f"Error extracting transcript: {str(e)}")
            raise
    
    def translate_text(self, text: str, target_language: Optional[str] = None) -> str:
        """
        Translate text to target language.
        
        Note: This is a placeholder - you would need to implement an actual translation service.
        Options include Google Translate API, Microsoft Translator, DeepL, etc.
        """
        # PLACEHOLDER - Replace with actual translation API call
        # For now we'll return the original text
        language = target_language or self.target_language
        logger.info(f"Would translate text to {language}")
        return text
    
    def generate_speech(self, text: str, target_language: Optional[str] = None) -> bytes:
        """Generate speech using Sarvam AI's TTS API"""
        language = target_language or self.target_language
        
        payload = {
            "inputs": [text],
            "target_language_code": language,
            "eng_interpolation_wt": 0.5,
            "enable_preprocessing": True,
            "speaker": "meera",  # Default speaker
            "pitch": 0,
            "pace": 1.0,
            "loudness": 1.5,
        }
        
        headers = {
            "api-subscription-key": self.sarvam_api_key,
            "Content-Type": "application/json",
        }
        
        try:
            logger.info(f"Generating speech for {len(text)} characters in {language}")
            response = requests.post(
                self.sarvam_tts_url,
                json=payload,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            response_data = response.json()
            
            if "audios" not in response_data or not response_data["audios"]:
                raise ValueError("No audio data in response")
            
            # Decode base64 audio (combining all chunks if multiple)
            audio_bytes = b""
            for audio_base64 in response_data["audios"]:
                audio_bytes += base64.b64decode(audio_base64)
            
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}")
            raise
    
    def save_audio_to_file(self, audio_bytes: bytes, output_path: Path) -> Path:
        """Save audio bytes to a file"""
        try:
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            logger.info(f"Saved audio to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving audio: {str(e)}")
            raise
    
    def merge_video_and_audio(self, video_path: Path, audio_path: Path, output_path: Path) -> Path:
        """Merge video with new audio track using FFmpeg"""
        try:
            # Calculate durations
            video_duration_cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "json", str(video_path)
            ]
            video_info = json.loads(subprocess.check_output(video_duration_cmd).decode())
            video_duration = float(video_info["format"]["duration"])
            
            audio_duration_cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "json", str(audio_path)
            ]
            audio_info = json.loads(subprocess.check_output(audio_duration_cmd).decode())
            audio_duration = float(audio_info["format"]["duration"])
            
            logger.info(f"Video duration: {video_duration:.2f}s, Audio duration: {audio_duration:.2f}s")
            
            # Strategy: Adjust audio speed if durations are significantly different
            audio_filter = ""
            if abs(video_duration - audio_duration) > 1.0:  # More than 1 second difference
                speed_factor = video_duration / audio_duration
                if 0.5 <= speed_factor <= 2.0:  # Reasonable speed adjustment range
                    logger.info(f"Adjusting audio speed by factor of {speed_factor:.2f}")
                    audio_filter = f",atempo={speed_factor}"
            
            # Create temporary file for adjusted audio if needed
            if audio_filter:
                temp_audio = audio_path.with_name(f"{audio_path.stem}_adjusted{audio_path.suffix}")
                adjust_cmd = [
                    "ffmpeg", "-y", "-i", str(audio_path),
                    "-filter:a", f"asetrate=24000{audio_filter}", 
                    "-ar", "24000", str(temp_audio)
                ]
                subprocess.run(adjust_cmd, check=True, capture_output=True)
                audio_path = temp_audio
            
            # Merge video and audio
            cmd = [
                "ffmpeg", "-y", 
                "-i", str(video_path),
                "-i", str(audio_path),
                "-map", "0:v",  # Take video from first input
                "-map", "1:a",  # Take audio from second input
                "-c:v", "copy",  # Copy video stream without re-encoding
                "-shortest",     # End when the shortest input ends
                str(output_path)
            ]
            
            logger.info(f"Merging video and audio to: {output_path}")
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Clean up temporary files if created
            if audio_filter and os.path.exists(temp_audio):
                os.remove(temp_audio)
                
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error merging video and audio: {str(e)}")
            raise

    def translate_highlight(self, highlight_path: str, video_id: str) -> str:
        """Translate a single video highlight, retrieving video_id if needed"""
        try:
            video_path = Path(highlight_path)
            language = self.target_language
            
            # Create output directory
            highlight_dir = video_path.parent
            translations_dir = highlight_dir / "translations"
            translations_dir.mkdir(exist_ok=True)
            
            # Output paths
            audio_path = translations_dir / f"{video_path.stem}_{language}_audio.wav"
            output_video_path = translations_dir / f"{video_path.stem}_{language}.mp4"
            
            # If output already exists, return it
            if output_video_path.exists():
                logger.info(f"Translated video already exists: {output_video_path}")
                return str(output_video_path)
            
            # Get transcript, translate, generate speech
            transcript = self.get_transcript(video_id)
            translated_text = self.translate_text(transcript)
            audio_bytes = self.generate_speech(translated_text)
            
            # Save audio and merge with video
            self.save_audio_to_file(audio_bytes, audio_path)
            self.merge_video_and_audio(video_path, audio_path, output_video_path)
            
            logger.info(f"Successfully translated video to {language}: {output_video_path}")
            return str(output_video_path)
            
        except Exception as e:
            logger.error(f"Error translating highlight: {str(e)}")
            raise

def translate_all_highlights(video_analysis_result, twelvelabs_api_key, sarvam_api_key, target_language="en-IN"):
    """
    Translate all highlights from a video analysis result.
    
    Args:
        video_analysis_result: The result from YouTubeProcessor.process_youtube_url()
        twelvelabs_api_key: Twelve Labs API key
        sarvam_api_key: Sarvam AI API key
        target_language: Target language code
        
    Returns:
        List of paths to translated videos
    """
    video_id = video_analysis_result.video_id
    highlights = video_analysis_result.highlights
    
    translator = VideoTranslator(
        twelvelabs_api_key=twelvelabs_api_key,
        sarvam_api_key=sarvam_api_key,
        target_language=target_language
    )
    
    translated_paths = []
    for highlight in highlights:
        try:
            translated_path = translator.translate_highlight(highlight.clip_path, video_id)
            translated_paths.append(translated_path)
        except Exception as e:
            logger.error(f"Failed to translate highlight {highlight.clip_path}: {e}")
    
    return translated_paths

# Example usage
if __name__ == "__main__":
    import argparse
    from processor import YouTubeProcessor
    

    # Process YouTube URL to get highlights
    youtube_processor = YouTubeProcessor(api_key="tlk_24AHH762K3MK1B2KT0X5W2ST0AZK")
    video_analysis = youtube_processor.process_youtube_url("https://youtu.be/VhvNXSLGQi0?si=hhDBkphtQelE3qay")
    
    # Translate all highlights
    translated_videos = translate_all_highlights(
        video_analysis,
        twelvelabs_api_key="tlk_24AHH762K3MK1B2KT0X5W2ST0AZK",
        sarvam_api_key="da99b3bb-5a5e-4931-91a6-40c063de438d",
        target_language="en-IN" 
    )
    
    print(f"Successfully translated {len(translated_videos)} highlights:")
    for path in translated_videos:
        print(f"  - {path}")