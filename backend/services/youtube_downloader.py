"""
YouTube Downloader Service for EngineIQ
Downloads YouTube videos and extracts audio for processing
"""

import os
import logging
import yt_dlp
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """Download YouTube videos and extract metadata"""
    
    def __init__(self, download_dir: str = "/tmp/engineiq_youtube"):
        """
        Initialize YouTube downloader
        
        Args:
            download_dir: Directory to save downloaded videos
        """
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
    
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        Get video metadata without downloading
        
        Args:
            url: YouTube video URL
            
        Returns:
            Dict with video metadata
            
        Raises:
            ValueError: If URL is invalid or video not accessible
        """
        try:
            logger.info(f"Fetching video info: {url}")
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            
            if not info:
                raise ValueError("Could not extract video information")
            
            # Extract key metadata
            metadata = {
                "title": info.get("title", "Unknown"),
                "duration": info.get("duration", 0),
                "duration_string": self._format_duration(info.get("duration", 0)),
                "uploader": info.get("uploader", "Unknown"),
                "upload_date": info.get("upload_date", ""),
                "view_count": info.get("view_count", 0),
                "description": info.get("description", ""),
                "thumbnail": info.get("thumbnail", ""),
                "video_id": info.get("id", ""),
                "url": url
            }
            
            logger.info(f"✅ Video info retrieved: {metadata['title']} ({metadata['duration_string']})")
            return metadata
            
        except Exception as e:
            logger.error(f"❌ Failed to get video info: {type(e).__name__}: {str(e)}")
            raise ValueError(f"Failed to get video info: {str(e)}")
    
    def download_video(
        self,
        url: str,
        audio_only: bool = True,
        max_duration: int = 7200  # 2 hours default
    ) -> Dict[str, Any]:
        """
        Download YouTube video
        
        Args:
            url: YouTube video URL
            audio_only: If True, download audio only (faster, smaller)
            max_duration: Maximum video duration in seconds
            
        Returns:
            Dict with file_path and metadata
            
        Raises:
            ValueError: If video too long or download fails
        """
        try:
            # Get video info first
            info = self.get_video_info(url)
            
            # Check duration
            duration = info.get("duration", 0)
            if duration > max_duration:
                raise ValueError(
                    f"Video too long ({self._format_duration(duration)}). "
                    f"Maximum: {self._format_duration(max_duration)}"
                )
            
            video_id = info["video_id"]
            title = info["title"]
            
            logger.info(f"Downloading: {title}")
            
            # Configure download options
            if audio_only:
                output_template = os.path.join(
                    self.download_dir,
                    f"{video_id}_%(title)s.%(ext)s"
                )
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': output_template,
                    'quiet': False,
                    'no_warnings': False,
                    # Fix for 403 errors
                    'nocheckcertificate': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'referer': 'https://www.youtube.com/',
                    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
            else:
                output_template = os.path.join(
                    self.download_dir,
                    f"{video_id}_%(title)s.%(ext)s"
                )
                ydl_opts = {
                    'format': 'best[height<=720]',  # Max 720p to save space
                    'outtmpl': output_template,
                    'quiet': False,
                    'no_warnings': False,
                    # Fix for 403 errors
                    'nocheckcertificate': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'referer': 'https://www.youtube.com/',
                    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
                }
            
            # Download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                download_info = ydl.extract_info(url, download=True)
                
                # Get actual filename (yt-dlp may modify it)
                if audio_only:
                    # Audio extraction changes extension to mp3
                    filename = ydl.prepare_filename(download_info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
                else:
                    filename = ydl.prepare_filename(download_info)
            
            # Verify file exists
            if not os.path.exists(filename):
                raise ValueError(f"Download succeeded but file not found: {filename}")
            
            file_size = os.path.getsize(filename) / (1024 * 1024)  # MB
            
            result = {
                "success": True,
                "file_path": filename,
                "file_size_mb": round(file_size, 2),
                "duration": duration,
                "duration_string": self._format_duration(duration),
                "title": title,
                "video_id": video_id,
                "audio_only": audio_only,
                "metadata": info
            }
            
            logger.info(f"✅ Download complete: {filename} ({file_size:.1f} MB)")
            return result
            
        except Exception as e:
            logger.error("="*70)
            logger.error(f"❌ YOUTUBE DOWNLOAD FAILED")
            logger.error(f"   URL: {url}")
            logger.error(f"   Error Type: {type(e).__name__}")
            logger.error(f"   Error Message: {str(e)}")
            logger.error("="*70)
            raise ValueError(f"Download failed: {str(e)}")
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def cleanup_file(self, file_path: str) -> bool:
        """
        Delete downloaded file
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to cleanup {file_path}: {e}")
            return False
