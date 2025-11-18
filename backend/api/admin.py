"""
Admin API for EngineIQ
Content upload and management endpoints
"""

import os
import sys
import logging
from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.services.qdrant_service import QdrantService
from backend.services.gemini_service import GeminiService
from backend.services.pdf_processor import PdfProcessor
from backend.services.image_processor import ImageProcessor
from backend.services.video_processor import VideoProcessor
from backend.services.youtube_downloader import YouTubeDownloader

logger = logging.getLogger(__name__)

# Initialize services
qdrant = QdrantService()
try:
    gemini = GeminiService()
except Exception as e:
    logger.warning(f"GeminiService initialization failed: {e}")
    gemini = None

# Initialize processors
pdf_processor = PdfProcessor(gemini, qdrant) if gemini else None
image_processor = ImageProcessor(gemini, qdrant) if gemini else None
video_processor = VideoProcessor(gemini, qdrant) if gemini else None
youtube_downloader = YouTubeDownloader()

# Create router
router = APIRouter(prefix="/api/admin", tags=["admin"])

# Upload directory
UPLOAD_DIR = "/tmp/engineiq_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class UploadResponse(BaseModel):
    success: bool
    doc_id: Optional[str] = None
    title: str
    type: str
    message: str
    indexed_at: Optional[int] = None
    uploaded_by: Optional[str] = None
    processing_time_seconds: Optional[float] = None


class YouTubeUploadRequest(BaseModel):
    url: str
    uploaded_by: str = "admin"


class StatusResponse(BaseModel):
    total: int
    pdfs: int
    images: int
    videos: int
    docs: int
    recent: list


@router.post("/upload", response_model=UploadResponse)
async def upload_content(
    file: UploadFile = File(...),
    uploaded_by: str = Form("admin")
):
    """
    Upload and process content (PDF, Video, Audio, Image, or Document)
    
    Accepts:
    - PDF files (.pdf)
    - Videos (.mp4, .mov, .avi, .webm)
    - Audio (.mp3, .wav, .m4a)
    - Images (.png, .jpg, .jpeg, .webp)
    - Documents (.txt, .md)
    """
    try:
        logger.info(f"Received upload: {file.filename}")
        
        if not gemini:
            raise HTTPException(status_code=503, detail="Gemini service not available")
        
        # Get file extension
        ext = os.path.splitext(file.filename)[1].lower()
        
        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Saved file to {file_path}")
        
        # Process based on type
        if ext == '.pdf':
            if not pdf_processor:
                raise HTTPException(status_code=503, detail="PDF processor not available")
            
            result = pdf_processor.process_pdf(
                file_path=file_path,
                title=file.filename,
                uploaded_by=uploaded_by
            )
            
        elif ext in ['.mp4', '.mov', '.avi', '.webm', '.mp3', '.wav', '.m4a']:
            # Video or audio file
            if not video_processor:
                raise HTTPException(status_code=503, detail="Video processor not available")
            
            logger.info(f"Processing video/audio file: {file.filename}")
            result = video_processor.process_video_file(
                file_path=file_path,
                title=file.filename,
                uploaded_by=uploaded_by
            )
            
        elif ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif']:
            if not image_processor:
                raise HTTPException(status_code=503, detail="Image processor not available")
            
            result = image_processor.process_image(
                file_path=file_path,
                title=file.filename,
                uploaded_by=uploaded_by
            )
            
        elif ext in ['.txt', '.md']:
            # Simple text document processing
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Generate embedding
            embedding = gemini.generate_embedding(content[:5000])
            
            # Index to Qdrant
            import uuid
            doc_id = str(uuid.uuid4())
            now = int(time.time())
            
            qdrant.index_document(
                collection_name="knowledge_base",
                doc_id=doc_id,
                vector=embedding,
                payload={
                    "id": doc_id,
                    "title": file.filename,
                    "raw_content": content,
                    "content_type": "document",
                    "file_type": ext[1:],
                    "created_at": now,
                    "indexed_at": now,
                    "uploaded_by": uploaded_by,
                    "upload_source": "admin_dashboard",
                    "permissions": {
                        "public": True,
                        "teams": ["engineering"],
                        "sensitivity": "internal",
                    }
                }
            )
            
            result = {
                "success": True,
                "doc_id": doc_id,
                "title": file.filename,
                "type": "document",
                "indexed_at": now,
                "uploaded_by": uploaded_by,
                "message": "Document processed successfully"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
        
        # Clean up file
        try:
            os.remove(file_path)
        except:
            pass
        
        return UploadResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/youtube", response_model=UploadResponse)
async def upload_youtube_video(request: YouTubeUploadRequest):
    """
    Download and process YouTube video
    
    Accepts:
    - YouTube URL (https://youtube.com/watch?v=... or youtu.be/...)
    
    Process:
    1. Download video/audio with yt-dlp
    2. Transcribe with Gemini
    3. Generate embeddings
    4. Index to Qdrant
    """
    try:
        logger.info(f"Received YouTube URL: {request.url}")
        
        if not gemini:
            raise HTTPException(status_code=503, detail="Gemini service not available")
        
        if not video_processor:
            raise HTTPException(status_code=503, detail="Video processor not available")
        
        # Validate URL
        if not ("youtube.com" in request.url or "youtu.be" in request.url):
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        # Get video info first (fast check)
        try:
            video_info = youtube_downloader.get_video_info(request.url)
            logger.info(f"Video: {video_info['title']} ({video_info['duration_string']})")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to get video info: {str(e)}")
        
        # Check duration (max 2 hours)
        max_duration = 7200
        if video_info['duration'] > max_duration:
            raise HTTPException(
                status_code=400,
                detail=f"Video too long ({video_info['duration_string']}). Maximum: 2 hours"
            )
        
        # Download (audio only for faster processing)
        try:
            logger.info("Downloading audio from YouTube...")
            download_result = youtube_downloader.download_video(
                url=request.url,
                audio_only=True,
                max_duration=max_duration
            )
            file_path = download_result['file_path']
            logger.info(f"✅ Downloaded: {file_path} ({download_result['file_size_mb']} MB)")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
        
        # Process video file with Gemini
        try:
            logger.info("Processing with Gemini...")
            result = video_processor.process_video_file(
                file_path=file_path,
                title=video_info['title'],
                uploaded_by=request.uploaded_by,
                source_url=request.url,
                metadata={
                    "uploader": video_info.get('uploader', 'Unknown'),
                    "upload_date": video_info.get('upload_date', ''),
                    "view_count": video_info.get('view_count', 0),
                    "source": "youtube",
                    "video_id": video_info.get('video_id', '')
                }
            )
            
            if not result.get('success'):
                raise Exception(result.get('message', 'Processing failed'))
            
            logger.info(f"✅ Processing complete: {result['chunks_indexed']} chunks")
            
        finally:
            # Clean up downloaded file
            try:
                youtube_downloader.cleanup_file(file_path)
            except:
                pass
        
        return UploadResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"YouTube upload failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get system statistics and recent activity
    """
    try:
        # Get collection stats
        stats = {
            "total": 0,
            "pdfs": 0,
            "images": 0,
            "videos": 0,
            "docs": 0
        }
        
        # Query Qdrant for counts by type
        try:
            # Get all points and count by type
            result = qdrant.client.scroll(
                collection_name="knowledge_base",
                limit=1000,  # Adjust based on your data size
                with_payload=True
            )
            
            for point in result[0]:
                stats["total"] += 1
                content_type = point.payload.get("content_type", "")
                
                if content_type == "pdf":
                    stats["pdfs"] += 1
                elif content_type == "image":
                    stats["images"] += 1
                elif content_type == "video":
                    stats["videos"] += 1
                elif content_type in ["document", "text"]:
                    stats["docs"] += 1
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
        
        # Get recent uploads (handled in /recent endpoint)
        return StatusResponse(
            total=stats["total"],
            pdfs=stats["pdfs"],
            images=stats["images"],
            videos=stats["videos"],
            docs=stats["docs"],
            recent=[]
        )
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_uploads(limit: int = 10):
    """
    Get recent uploads
    """
    try:
        # Query recent items from Qdrant
        result = qdrant.client.scroll(
            collection_name="knowledge_base",
            limit=limit,
            with_payload=True
        )
        
        recent = []
        for point in result[0]:
            payload = point.payload
            
            # Only include admin uploads
            if payload.get("upload_source") == "admin_dashboard":
                recent.append({
                    "title": payload.get("title", "Untitled"),
                    "type": payload.get("content_type", "unknown"),
                    "uploaded_by": payload.get("uploaded_by", "Unknown"),
                    "indexed_at": payload.get("indexed_at", 0),
                    "status": "processed"
                })
        
        # Sort by indexed_at (newest first)
        recent.sort(key=lambda x: x["indexed_at"], reverse=True)
        
        return recent[:limit]
        
    except Exception as e:
        logger.error(f"Failed to get recent uploads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# For testing
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
