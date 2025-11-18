"""
Video Processing Service for EngineIQ
Handles video content extraction and indexing with Gemini transcription
"""

import os
import logging
import time
from typing import Dict, List, Optional, Any
import uuid

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Process videos with Gemini transcription"""
    
    def __init__(self, gemini_service, qdrant_service):
        self.gemini = gemini_service
        self.qdrant = qdrant_service
        self.supported_formats = ['.mp4', '.mov', '.avi', '.webm', '.mp3', '.wav', '.m4a']
    
    def process_video_file(
        self,
        file_path: str,
        title: Optional[str] = None,
        uploaded_by: str = "admin",
        source_url: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process actual video/audio file with Gemini transcription
        
        Args:
            file_path: Path to video/audio file
            title: Video title (extracted from filename if not provided)
            uploaded_by: User who uploaded
            source_url: Original URL if downloaded
            metadata: Additional metadata
            
        Returns:
            Dict with processing results
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing video file: {file_path}")
            
            # Extract title from filename if not provided
            if not title:
                title = os.path.basename(file_path)
                # Remove extension and video ID prefix if present
                title = title.rsplit('.', 1)[0]
                if '_' in title and len(title.split('_')[0]) == 11:
                    title = '_'.join(title.split('_')[1:])
            
            # Get file info
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Determine if audio or video
            is_audio = file_ext in ['.mp3', '.wav', '.m4a']
            content_type = "audio" if is_audio else "video"
            
            logger.info(f"File type: {content_type}, Size: {file_size:.2f} MB")
            
            # Read file for Gemini
            logger.info("Reading file for Gemini transcription...")
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            
            # Determine MIME type
            mime_types = {
                '.mp4': 'video/mp4',
                '.mov': 'video/quicktime',
                '.avi': 'video/x-msvideo',
                '.webm': 'video/webm',
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.m4a': 'audio/mp4'
            }
            mime_type = mime_types.get(file_ext, 'video/mp4')
            
            # Transcribe with Gemini
            logger.info(f"Transcribing with Gemini ({mime_type})...")
            transcription_result = self.gemini.transcribe_audio(file_bytes, mime_type)
            
            if not transcription_result or not transcription_result.get('transcription'):
                raise Exception("Gemini transcription returned empty result")
            
            transcript = transcription_result['transcription']
            logger.info(f"✅ Transcription complete: {len(transcript)} characters")
            
            # Estimate duration (rough estimate from transcript length)
            # Avg speaking rate: ~150 words/min, ~5 chars/word = 750 chars/min
            estimated_duration = max(60, len(transcript) // 750 * 60)  # seconds
            duration_string = self._format_duration(estimated_duration)
            
            # Chunk transcript for embeddings
            chunks = self._chunk_transcript(transcript, chunk_size=1000)
            logger.info(f"Created {len(chunks)} chunks from transcript")
            
            # Process each chunk
            doc_id = str(uuid.uuid4())
            indexed_count = 0
            
            for i, chunk in enumerate(chunks):
                try:
                    # Generate embedding
                    embedding = self.gemini.generate_embedding(chunk)
                    
                    # Create chunk ID
                    chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_id}_chunk_{i}"))
                    
                    # Prepare payload
                    now = int(time.time())
                    payload = {
                        "id": chunk_id,
                        "parent_doc_id": doc_id,
                        "title": f"{title} (Part {i+1}/{len(chunks)})",
                        "raw_content": chunk,
                        "content_type": content_type,
                        "file_type": file_ext[1:],
                        "duration": estimated_duration,
                        "duration_string": duration_string,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "created_at": now,
                        "indexed_at": now,
                        "modified_at": now,
                        "uploaded_by": uploaded_by,
                        "upload_source": "admin_dashboard",
                        "file_size_mb": round(file_size, 2),
                        "source_url": source_url or "",
                        "transcription_source": "gemini",
                        "permissions": {
                            "public": True,
                            "teams": ["engineering"],
                            "sensitivity": "internal",
                        }
                    }
                    
                    # Add custom metadata
                    if metadata:
                        payload.update(metadata)
                    
                    # Index to Qdrant
                    self.qdrant.index_document(
                        collection_name="knowledge_base",
                        doc_id=chunk_id,
                        vector=embedding,
                        payload=payload
                    )
                    
                    indexed_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to index chunk {i}: {e}")
                    continue
            
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "doc_id": doc_id,
                "title": title,
                "type": content_type,
                "chunks_indexed": indexed_count,
                "total_chunks": len(chunks),
                "duration": estimated_duration,
                "duration_string": duration_string,
                "file_size_mb": round(file_size, 2),
                "transcript_length": len(transcript),
                "processing_time_seconds": round(processing_time, 2),
                "indexed_at": int(time.time()),
                "uploaded_by": uploaded_by,
                "message": f"Successfully processed {content_type} with {indexed_count} chunks"
            }
            
            logger.info(f"✅ Video processing complete: {result}")
            return result
            
        except Exception as e:
            logger.error("="*70)
            logger.error(f"❌ VIDEO PROCESSING FAILED: {title}")
            logger.error(f"   Error Type: {type(e).__name__}")
            logger.error(f"   Error Message: {str(e)}")
            logger.error("="*70)
            
            import traceback
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": f"Failed to process {content_type}: {str(e)}"
            }
    
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
    
    def process_video_metadata(
        self,
        title: str,
        transcript: str,
        duration: str,
        speakers: List[str],
        key_moments: List[Dict],
        uploaded_by: str = "admin",
        source_url: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process video metadata and transcript
        
        Args:
            title: Video title
            transcript: Full transcript text
            duration: Duration string (e.g., "15 minutes")
            speakers: List of speaker names
            key_moments: List of {timestamp, content} dicts
            uploaded_by: User who uploaded
            source_url: Source URL if applicable
            metadata: Additional metadata
            
        Returns:
            Dict with processing results
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing video metadata: {title}")
            
            # Chunk transcript for embeddings
            chunks = self._chunk_transcript(transcript, chunk_size=1000)
            logger.info(f"Created {len(chunks)} chunks from transcript")
            
            # Process each chunk
            doc_id = str(uuid.uuid4())
            indexed_count = 0
            
            for i, chunk in enumerate(chunks):
                try:
                    # Generate embedding
                    embedding = self.gemini.generate_embedding(chunk)
                    
                    # Create chunk ID
                    chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_id}_chunk_{i}"))
                    
                    # Prepare payload
                    now = int(time.time())
                    payload = {
                        "id": chunk_id,
                        "parent_doc_id": doc_id,
                        "title": f"{title} (Part {i+1}/{len(chunks)})",
                        "raw_content": chunk,
                        "content_type": "video",
                        "file_type": "video",
                        "duration": duration,
                        "speakers": speakers,
                        "key_moments": key_moments if i == 0 else [],  # Only first chunk gets key moments
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "created_at": now,
                        "indexed_at": now,
                        "modified_at": now,
                        "uploaded_by": uploaded_by,
                        "upload_source": "admin_dashboard",
                        "source_url": source_url or "",
                        "permissions": {
                            "public": True,
                            "teams": ["engineering"],
                            "users": [],
                            "sensitivity": "internal",
                            "offshore_restricted": False,
                            "third_party_restricted": False,
                        },
                        "metadata": metadata or {},
                    }
                    
                    # Index to Qdrant
                    self.qdrant.index_document(
                        collection_name="knowledge_base",
                        doc_id=chunk_id,
                        vector=embedding,
                        payload=payload
                    )
                    
                    indexed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing chunk {i}: {e}")
                    continue
            
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "doc_id": doc_id,
                "title": title,
                "type": "video",
                "chunks_indexed": indexed_count,
                "total_chunks": len(chunks),
                "duration": duration,
                "speakers": speakers,
                "key_moments_count": len(key_moments),
                "processing_time_seconds": round(processing_time, 2),
                "indexed_at": int(time.time()),
                "uploaded_by": uploaded_by,
                "message": f"Successfully processed video with {indexed_count} chunks"
            }
            
            logger.info(f"Video processing complete: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Video processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to process video: {str(e)}"
            }
    
    def _chunk_transcript(self, transcript: str, chunk_size: int = 1000) -> List[str]:
        """
        Split transcript into chunks
        
        Args:
            transcript: Full transcript text
            chunk_size: Target size per chunk
            
        Returns:
            List of transcript chunks
        """
        if not transcript:
            return [""]
        
        # Split by sentences or paragraphs
        chunks = []
        current_chunk = ""
        
        sentences = transcript.split('. ')
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += ". " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [transcript[:chunk_size]]
