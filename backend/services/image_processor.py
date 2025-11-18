"""
Image Processing Service for EngineIQ
Handles image analysis using Gemini Vision API
"""

import os
import logging
import time
from typing import Dict, Optional, Any
import uuid

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Process images with Gemini Vision API"""
    
    def __init__(self, gemini_service, qdrant_service):
        self.gemini = gemini_service
        self.qdrant = qdrant_service
        self.supported_formats = ['.png', '.jpg', '.jpeg', '.webp', '.gif']
    
    def process_image(
        self,
        file_path: str,
        title: Optional[str] = None,
        uploaded_by: str = "admin",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process an image file and index to Qdrant
        
        Args:
            file_path: Path to image file
            title: Image title
            uploaded_by: User who uploaded
            metadata: Additional metadata
            
        Returns:
            Dict with processing results
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing image: {file_path}")
            
            # Extract title from filename if not provided
            if not title:
                title = os.path.basename(file_path)
            
            # Get file info
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            
            # Upload to Gemini
            logger.info("Uploading image to Gemini...")
            gemini_file = self.gemini.upload_file(file_path)
            
            # Analyze image with Gemini Vision
            logger.info("Analyzing image with Gemini Vision...")
            analysis = self._analyze_image(gemini_file)
            
            # Detect image type
            image_type = self._detect_image_type(analysis)
            
            # Extract detected objects
            detected_objects = self._extract_objects(analysis)
            
            # Extract any text in image
            extracted_text = self._extract_text(analysis)
            
            # Generate embedding from analysis
            embedding_text = f"{title}. {analysis}"
            embedding = self.gemini.generate_embedding(embedding_text)
            
            # Create document
            doc_id = str(uuid.uuid4())
            now = int(time.time())
            
            payload = {
                "id": doc_id,
                "title": title,
                "raw_content": analysis,
                "content_type": "image",
                "file_type": os.path.splitext(file_path)[1][1:],  # Remove dot
                "image_type": image_type,
                "detected_objects": detected_objects,
                "extracted_text": extracted_text,
                "created_at": now,
                "indexed_at": now,
                "modified_at": now,
                "uploaded_by": uploaded_by,
                "upload_source": "admin_dashboard",
                "file_size_mb": round(file_size, 2),
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
                doc_id=doc_id,
                vector=embedding,
                payload=payload
            )
            
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "doc_id": doc_id,
                "title": title,
                "type": "image",
                "image_type": image_type,
                "detected_objects": detected_objects,
                "extracted_text": extracted_text,
                "file_size_mb": round(file_size, 2),
                "processing_time_seconds": round(processing_time, 2),
                "indexed_at": now,
                "uploaded_by": uploaded_by,
                "message": f"Successfully processed {image_type} image"
            }
            
            logger.info(f"Image processing complete: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to process image: {str(e)}"
            }
    
    def _analyze_image(self, gemini_file) -> str:
        """Analyze image using Gemini Vision"""
        try:
            prompt = """Analyze this image in detail. Provide:
            1. What type of image is this? (diagram, chart, screenshot, photo, etc.)
            2. Main objects or components visible
            3. Any text present in the image
            4. Technical details if applicable (e.g., architecture components, data flows)
            5. Overall description and context
            
            Be thorough and technical in your analysis."""
            
            response = self.gemini.generate_content_with_file(gemini_file, prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return "Image analysis in progress..."
    
    def _detect_image_type(self, analysis: str) -> str:
        """Detect image type from analysis"""
        analysis_lower = analysis.lower()
        
        if any(word in analysis_lower for word in ['diagram', 'architecture', 'flowchart', 'system']):
            return "diagram"
        elif any(word in analysis_lower for word in ['chart', 'graph', 'plot', 'data visualization']):
            return "chart"
        elif any(word in analysis_lower for word in ['screenshot', 'screen capture', 'ui', 'interface']):
            return "screenshot"
        else:
            return "photo"
    
    def _extract_objects(self, analysis: str) -> list:
        """Extract detected objects from analysis"""
        # Simple keyword extraction
        objects = []
        keywords = ['database', 'server', 'api', 'load balancer', 'gateway', 
                   'microservice', 'cache', 'queue', 'storage', 'network']
        
        analysis_lower = analysis.lower()
        for keyword in keywords:
            if keyword in analysis_lower:
                objects.append(keyword)
        
        return objects[:10]  # Limit to 10
    
    def _extract_text(self, analysis: str) -> str:
        """Extract any text mentioned in the analysis"""
        # Look for text in quotes or after "text:" markers
        # For now, return first 200 chars of analysis as text summary
        if 'text' in analysis.lower():
            return analysis[:200]
        return ""
