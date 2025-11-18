"""
PDF Processing Service for EngineIQ
Handles PDF content extraction and indexing using Gemini multimodal parsing
"""

import os
import logging
import hashlib
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class PdfProcessor:
    """Process PDFs with Gemini multimodal parsing"""
    
    def __init__(self, gemini_service, qdrant_service):
        self.gemini = gemini_service
        self.qdrant = qdrant_service
        self.supported_formats = ['.pdf']
    
    def process_pdf(
        self, 
        file_path: str, 
        title: Optional[str] = None,
        uploaded_by: str = "admin",
        source_url: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a PDF file and index to Qdrant
        
        Args:
            file_path: Path to PDF file
            title: Document title (extracted from filename if not provided)
            uploaded_by: User who uploaded
            source_url: Original URL if downloaded
            metadata: Additional metadata
            
        Returns:
            Dict with processing results
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing PDF: {file_path}")
            
            # Extract title from filename if not provided
            if not title:
                title = os.path.basename(file_path).replace('.pdf', '')
            
            # Get file info
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            
            # Try Gemini first, fallback to PyPDF2
            content = ""
            
            try:
                # Upload to Gemini for processing
                logger.info("Uploading PDF to Gemini...")
                gemini_file = self.gemini.upload_file(file_path)
                logger.info(f"✅ Upload successful: {gemini_file.name}")
                
                # Extract content using Gemini multimodal parsing
                logger.info("Extracting content with Gemini multimodal parsing...")
                content = self._extract_pdf_content(gemini_file)
                logger.info(f"✅ Extraction complete: {len(content)} characters")
            except Exception as e:
                logger.error(f"❌ GEMINI FAILED: {type(e).__name__}: {str(e)}")
                logger.error(f"   This means File API is not working properly")
                content = ""
            
            # If Gemini failed or returned too little, use PyPDF2
            if not content or len(content) < 100 or "extraction" in content.lower():
                logger.warning(f"⚠️  Gemini returned insufficient content ({len(content)} chars)")
                logger.info("🔄 Using PyPDF2 fallback for text extraction...")
                content = self._extract_pdf_with_pypdf(file_path)
                
                if not content or len(content) < 100:
                    raise Exception(f"Both Gemini and PyPDF2 failed to extract content from PDF")
            
            # Generate page count estimate
            page_count = self._estimate_page_count(content)
            
            # Chunk content for embeddings
            # For large PDFs, use bigger chunks to reduce processing time
            chunk_size = 2000 if len(content) > 100000 else 1000
            chunks = self._chunk_text(content, chunk_size=chunk_size)
            logger.info(f"Created {len(chunks)} chunks from PDF (chunk_size: {chunk_size})")
            
            # Process each chunk
            doc_id = str(uuid.uuid4())
            indexed_count = 0
            
            for i, chunk in enumerate(chunks):
                try:
                    # Progress logging for large PDFs
                    if i % 10 == 0 and i > 0:
                        logger.info(f"Processing chunk {i}/{len(chunks)} ({(i/len(chunks)*100):.1f}%)")
                    
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
                        "content_type": "pdf",
                        "file_type": "pdf",
                        "page_count": page_count,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "created_at": now,
                        "indexed_at": now,
                        "modified_at": now,
                        "uploaded_by": uploaded_by,
                        "upload_source": "admin_dashboard",
                        "file_size_mb": round(file_size, 2),
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
                "type": "pdf",
                "chunks_indexed": indexed_count,
                "total_chunks": len(chunks),
                "page_count": page_count,
                "file_size_mb": round(file_size, 2),
                "processing_time_seconds": round(processing_time, 2),
                "indexed_at": int(time.time()),
                "uploaded_by": uploaded_by,
                "message": f"Successfully processed PDF with {indexed_count} chunks"
            }
            
            logger.info(f"PDF processing complete: {result}")
            return result
            
        except Exception as e:
            logger.error("="*70)
            logger.error(f"❌ PDF PROCESSING FAILED: {title}")
            logger.error(f"   Error Type: {type(e).__name__}")
            logger.error(f"   Error Message: {str(e)}")
            logger.error("="*70)
            
            import traceback
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": f"Failed to process PDF: {str(e)}"
            }
    
    def _extract_pdf_content(self, gemini_file) -> str:
        """Extract text content from PDF using Gemini"""
        try:
            # Use Gemini to parse PDF content
            prompt = """Extract all text content from this PDF document. 
            Provide a comprehensive extraction including:
            - Main text content
            - Headings and sections
            - Technical details
            - Code snippets if present
            - Important notes
            
            Format the output as clean, readable text."""
            
            response = self.gemini.generate_content_with_file(gemini_file, prompt)
            
            # Check if response is meaningful
            if response and len(response) > 100:
                return response
            else:
                logger.warning(f"Gemini extraction too short ({len(response)} chars), trying PyPDF2 fallback")
                # Fall through to PyPDF2 fallback
                
        except Exception as e:
            logger.error(f"Gemini extraction failed: {e}, trying PyPDF2 fallback")
        
        # Fallback: Use PyPDF2 to extract text directly
        return "PDF content extraction in progress..."
    
    def _extract_pdf_with_pypdf(self, file_path: str) -> str:
        """Fallback: Extract text using PyPDF2"""
        try:
            from PyPDF2 import PdfReader
            
            reader = PdfReader(file_path)
            text = ""
            
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            
            if len(text.strip()) > 100:
                logger.info(f"PyPDF2 extracted {len(text)} characters")
                return text
            else:
                return "PDF appears to be empty or image-based"
                
        except Exception as e:
            logger.error(f"PyPDF2 extraction also failed: {e}")
            return "PDF content extraction failed"
    
    def _estimate_page_count(self, content: str) -> int:
        """Estimate page count from content length"""
        # Rough estimate: ~3000 chars per page
        return max(1, len(content) // 3000)
    
    def _chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """
        Split text into chunks for embedding generation
        
        Args:
            text: Text to chunk
            chunk_size: Target size per chunk (characters)
            
        Returns:
            List of text chunks
        """
        if not text:
            return [""]
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            # If adding this paragraph exceeds chunk size, start new chunk
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text[:chunk_size]]
    
    def download_pdf(self, url: str, save_path: str) -> str:
        """
        Download PDF from URL
        
        Args:
            url: URL to download from
            save_path: Path to save file
            
        Returns:
            Path to downloaded file
        """
        import requests
        
        try:
            logger.info(f"Downloading PDF from {url}")
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"PDF downloaded to {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"Failed to download PDF: {e}")
            raise
