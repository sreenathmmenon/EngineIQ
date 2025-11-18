"""
EngineIQ Gemini Service

Unified service for all Gemini API operations across 5 modalities:
- TEXT: Embeddings and query understanding
- CODE: Analysis and function extraction
- IMAGES: Vision analysis and diagram extraction
- PDF: Multimodal parsing
- VIDEO/AUDIO: Transcription and content extraction
"""

import json
import logging
import time
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple, Any
import hashlib
import google.generativeai as genai

from ..config.gemini_config import GeminiConfig


logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple token bucket rate limiter"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    def acquire(self) -> bool:
        """Attempt to acquire a token for making a request"""
        now = time.time()
        
        # Remove old requests outside the window
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.window_seconds]
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False
    
    def wait_if_needed(self) -> None:
        """Wait until a request can be made"""
        while not self.acquire():
            sleep_time = 1.0
            logger.debug(f"Rate limit reached, waiting {sleep_time}s")
            time.sleep(sleep_time)


class LRUCache:
    """Simple LRU cache implementation"""
    
    def __init__(self, max_size: int, ttl_seconds: int):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key not in self.cache:
            return None
        
        # Check if expired
        if time.time() - self.timestamps[key] > self.ttl_seconds:
            self.cache.pop(key)
            self.timestamps.pop(key)
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key: str, value: Any) -> None:
        """Put value in cache"""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                self.cache.pop(oldest_key)
                self.timestamps.pop(oldest_key)
            self.cache[key] = value
        
        self.timestamps[key] = time.time()
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.timestamps.clear()


class GeminiService:
    """
    Unified Gemini service for all modalities.
    
    Features:
    - Rate limiting (60 req/min)
    - Retry logic with exponential backoff
    - In-memory caching
    - Batch processing
    - Comprehensive error handling
    """
    
    def __init__(self, config: Optional[GeminiConfig] = None):
        """Initialize Gemini service with configuration"""
        self.config = config or GeminiConfig()
        
        # Initialize Gemini API
        if self.config.GEMINI_API_KEY:
            genai.configure(api_key=self.config.GEMINI_API_KEY)
            # CRITICAL: File API also needs GOOGLE_API_KEY env var set
            import os
            if not os.getenv("GOOGLE_API_KEY"):
                os.environ["GOOGLE_API_KEY"] = self.config.GEMINI_API_KEY
                logger.info("Set GOOGLE_API_KEY environment variable for File API")
        else:
            logger.warning("GEMINI_API_KEY not set, service will fail on API calls")
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            self.config.MAX_REQUESTS_PER_MINUTE,
            self.config.RATE_LIMIT_WINDOW_SECONDS
        )
        
        # Initialize cache
        self.cache = None
        if self.config.CACHE_ENABLED:
            self.cache = LRUCache(
                self.config.MAX_CACHE_SIZE,
                self.config.CACHE_TTL_SECONDS
            )
        
        logger.info("GeminiService initialized")
    
    def _get_cache_key(self, prefix: str, *args) -> str:
        """Generate cache key from arguments"""
        content = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _retry_with_backoff(self, func, *args, **kwargs) -> Any:
        """Execute function with exponential backoff retry logic"""
        last_exception = None
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                self.rate_limiter.wait_if_needed()
                return func(*args, **kwargs)
            
            except Exception as e:
                last_exception = e
                
                # Don't retry on certain errors
                error_msg = str(e).lower()
                if any(term in error_msg for term in ["invalid api key", "permission denied", "quota exceeded"]):
                    logger.error(f"Non-retryable error: {e}")
                    raise
                
                if attempt < self.config.MAX_RETRIES - 1:
                    delay = min(
                        self.config.RETRY_BASE_DELAY * (self.config.RETRY_EXPONENTIAL_BASE ** attempt),
                        self.config.RETRY_MAX_DELAY
                    )
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
        
        logger.error(f"All {self.config.MAX_RETRIES} attempts failed")
        raise last_exception
    
    # ==================== TEXT MODALITY ====================
    
    def generate_embedding(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """
        Generate embedding for a single text using text-embedding-004.
        
        Args:
            text: Input text (max 10k chars)
            task_type: Task type (RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, etc.)
        
        Returns:
            List of 768 float values
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Truncate if needed
        if len(text) > self.config.MAX_TEXT_LENGTH:
            logger.warning(f"Text truncated from {len(text)} to {self.config.MAX_TEXT_LENGTH} chars")
            text = text[:self.config.MAX_TEXT_LENGTH]
        
        # Check cache
        if self.cache:
            cache_key = self._get_cache_key("embedding", text, task_type)
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug("Embedding cache hit")
                return cached
        
        # Generate embedding
        def _generate():
            result = genai.embed_content(
                model=f"models/{self.config.EMBEDDING_MODEL}",
                content=text,
                task_type=task_type
            )
            return result['embedding']
        
        embedding = self._retry_with_backoff(_generate)
        
        # Cache result
        if self.cache:
            self.cache.put(cache_key, embedding)
        
        logger.info(f"Generated embedding (dim={len(embedding)})")
        return embedding
    
    def batch_generate_embeddings(
        self,
        texts: List[str],
        task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of input texts
            task_type: Task type for embeddings
        
        Returns:
            List of embeddings (768-dim each)
        """
        if not texts:
            return []
        
        embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), self.config.EMBEDDING_BATCH_SIZE):
            batch = texts[i:i + self.config.EMBEDDING_BATCH_SIZE]
            
            # Check cache first
            batch_embeddings = []
            uncached_texts = []
            uncached_indices = []
            
            for idx, text in enumerate(batch):
                if not text or not text.strip():
                    batch_embeddings.append(None)
                    continue
                
                # Truncate if needed
                if len(text) > self.config.MAX_TEXT_LENGTH:
                    text = text[:self.config.MAX_TEXT_LENGTH]
                    batch[idx] = text
                
                if self.cache:
                    cache_key = self._get_cache_key("embedding", text, task_type)
                    cached = self.cache.get(cache_key)
                    if cached:
                        batch_embeddings.append(cached)
                        continue
                
                batch_embeddings.append(None)
                uncached_texts.append(text)
                uncached_indices.append(idx)
            
            # Generate embeddings for uncached texts
            if uncached_texts:
                def _batch_generate():
                    result = genai.embed_content(
                        model=f"models/{self.config.EMBEDDING_MODEL}",
                        content=uncached_texts,
                        task_type=task_type
                    )
                    return result['embedding']
                
                try:
                    new_embeddings = self._retry_with_backoff(_batch_generate)
                    
                    # Place embeddings in correct positions
                    for text, embedding, idx in zip(uncached_texts, new_embeddings, uncached_indices):
                        batch_embeddings[idx] = embedding
                        
                        # Cache each embedding
                        if self.cache:
                            cache_key = self._get_cache_key("embedding", text, task_type)
                            self.cache.put(cache_key, embedding)
                
                except Exception as e:
                    logger.error(f"Batch embedding failed: {e}")
                    # Fall back to individual generation
                    for text, idx in zip(uncached_texts, uncached_indices):
                        try:
                            embedding = self.generate_embedding(text, task_type)
                            batch_embeddings[idx] = embedding
                        except Exception as e2:
                            logger.error(f"Individual embedding failed for text at index {idx}: {e2}")
                            batch_embeddings[idx] = [0.0] * self.config.EMBEDDING_DIMENSION
            
            embeddings.extend(batch_embeddings)
            
            logger.info(f"Processed batch {i // self.config.EMBEDDING_BATCH_SIZE + 1}: {len(batch)} texts")
        
        return embeddings
    
    def understand_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze user query to extract intent, entities, and keywords.
        
        Args:
            query: User's search query
        
        Returns:
            Dict with intent, entities, keywords, and data sources
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Check cache
        if self.cache:
            cache_key = self._get_cache_key("query_understanding", query)
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug("Query understanding cache hit")
                return cached
        
        # Generate response
        prompt = self.config.QUERY_UNDERSTANDING_PROMPT.format(query=query)
        
        def _generate():
            model = genai.GenerativeModel(self.config.TEXT_MODEL)
            response = model.generate_content(
                prompt,
                generation_config=self.config.GENERATION_CONFIG
            )
            return response.text
        
        response_text = self._retry_with_backoff(_generate)
        
        # Parse JSON response
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback structure if JSON parsing fails
            logger.warning("Failed to parse query understanding response as JSON")
            result = {
                "intent": "search",
                "entities": [],
                "keywords": query.split(),
                "data_sources": [],
                "raw_response": response_text
            }
        
        # Cache result
        if self.cache:
            self.cache.put(cache_key, result)
        
        logger.info(f"Query understood: intent={result.get('intent', 'unknown')}")
        return result
    
    # ==================== CODE MODALITY ====================
    
    def analyze_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Analyze code for semantic understanding.
        
        Args:
            code: Source code to analyze
            language: Programming language
        
        Returns:
            Dict with summary, functions, issues, and dependencies
        """
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")
        
        # Truncate if needed
        if len(code) > self.config.MAX_CODE_LENGTH:
            logger.warning(f"Code truncated from {len(code)} to {self.config.MAX_CODE_LENGTH} chars")
            code = code[:self.config.MAX_CODE_LENGTH]
        
        # Check cache
        if self.cache:
            cache_key = self._get_cache_key("code_analysis", code, language)
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug("Code analysis cache hit")
                return cached
        
        # Generate analysis
        prompt = self.config.CODE_ANALYSIS_PROMPT.format(code=code, language=language)
        
        def _generate():
            model = genai.GenerativeModel(self.config.TEXT_MODEL)
            response = model.generate_content(
                prompt,
                generation_config=self.config.GENERATION_CONFIG
            )
            return response.text
        
        analysis_text = self._retry_with_backoff(_generate)
        
        result = {
            "language": language,
            "analysis": analysis_text,
            "code_length": len(code),
            "timestamp": time.time()
        }
        
        # Cache result
        if self.cache:
            self.cache.put(cache_key, result)
        
        logger.info(f"Code analyzed: {language}, {len(code)} chars")
        return result
    
    def extract_code_functions(self, code: str, language: str = "python") -> List[Dict[str, Any]]:
        """
        Extract function signatures and descriptions from code.
        
        Args:
            code: Source code
            language: Programming language
        
        Returns:
            List of function dictionaries with name, params, return type, description
        """
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")
        
        # Truncate if needed
        if len(code) > self.config.MAX_CODE_LENGTH:
            code = code[:self.config.MAX_CODE_LENGTH]
        
        # Check cache
        if self.cache:
            cache_key = self._get_cache_key("function_extraction", code, language)
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug("Function extraction cache hit")
                return cached
        
        # Generate extraction
        prompt = self.config.FUNCTION_EXTRACTION_PROMPT.format(code=code, language=language)
        
        def _generate():
            model = genai.GenerativeModel(self.config.TEXT_MODEL)
            response = model.generate_content(
                prompt,
                generation_config=self.config.GENERATION_CONFIG
            )
            return response.text
        
        extraction_text = self._retry_with_backoff(_generate)
        
        # Parse response (attempt structured extraction)
        functions = []
        try:
            # Try to parse as JSON first
            functions = json.loads(extraction_text)
        except json.JSONDecodeError:
            # Fallback: treat as plain text response
            functions = [{
                "extraction": extraction_text,
                "language": language
            }]
        
        # Cache result
        if self.cache:
            self.cache.put(cache_key, functions)
        
        logger.info(f"Extracted {len(functions)} functions from {language} code")
        return functions
    
    # ==================== IMAGE MODALITY ====================
    
    def analyze_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        """
        Analyze image using Gemini Vision.
        
        Args:
            image_bytes: Image data
            mime_type: MIME type (image/jpeg, image/png, etc.)
        
        Returns:
            Dict with image analysis
        """
        if not image_bytes:
            raise ValueError("Image bytes cannot be empty")
        
        # Check cache
        if self.cache:
            image_hash = hashlib.md5(image_bytes).hexdigest()
            cache_key = self._get_cache_key("image_analysis", image_hash)
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug("Image analysis cache hit")
                return cached
        
        # Analyze image
        def _generate():
            model = genai.GenerativeModel(self.config.VISION_MODEL)
            
            # Upload image
            image_part = {
                "mime_type": mime_type,
                "data": image_bytes
            }
            
            response = model.generate_content(
                [self.config.IMAGE_ANALYSIS_PROMPT, image_part],
                generation_config=self.config.GENERATION_CONFIG
            )
            return response.text
        
        analysis_text = self._retry_with_backoff(_generate)
        
        result = {
            "analysis": analysis_text,
            "mime_type": mime_type,
            "size_bytes": len(image_bytes),
            "timestamp": time.time()
        }
        
        # Cache result
        if self.cache:
            self.cache.put(cache_key, result)
        
        logger.info(f"Image analyzed: {mime_type}, {len(image_bytes)} bytes")
        return result
    
    def extract_diagram_content(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        """
        Extract structured content from technical diagrams.
        
        Args:
            image_bytes: Diagram image data
            mime_type: MIME type
        
        Returns:
            Dict with diagram type, components, relationships
        """
        if not image_bytes:
            raise ValueError("Image bytes cannot be empty")
        
        # Check cache
        if self.cache:
            image_hash = hashlib.md5(image_bytes).hexdigest()
            cache_key = self._get_cache_key("diagram_extraction", image_hash)
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug("Diagram extraction cache hit")
                return cached
        
        # Extract diagram content
        def _generate():
            model = genai.GenerativeModel(self.config.VISION_MODEL)
            
            image_part = {
                "mime_type": mime_type,
                "data": image_bytes
            }
            
            response = model.generate_content(
                [self.config.DIAGRAM_EXTRACTION_PROMPT, image_part],
                generation_config=self.config.GENERATION_CONFIG
            )
            return response.text
        
        extraction_text = self._retry_with_backoff(_generate)
        
        result = {
            "extraction": extraction_text,
            "mime_type": mime_type,
            "size_bytes": len(image_bytes),
            "timestamp": time.time()
        }
        
        # Cache result
        if self.cache:
            self.cache.put(cache_key, result)
        
        logger.info(f"Diagram extracted: {mime_type}, {len(image_bytes)} bytes")
        return result
    
    # ==================== PDF MODALITY ====================
    
    def parse_pdf_multimodal(self, pdf_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Parse PDF with multimodal understanding (text + images).
        
        Args:
            pdf_bytes: PDF file data
        
        Returns:
            List of page dictionaries with content
        """
        if not pdf_bytes:
            raise ValueError("PDF bytes cannot be empty")
        
        # Check cache
        if self.cache:
            pdf_hash = hashlib.md5(pdf_bytes).hexdigest()
            cache_key = self._get_cache_key("pdf_parsing", pdf_hash)
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug("PDF parsing cache hit")
                return cached
        
        # Parse PDF
        def _generate():
            model = genai.GenerativeModel(self.config.VISION_MODEL)
            
            pdf_part = {
                "mime_type": "application/pdf",
                "data": pdf_bytes
            }
            
            response = model.generate_content(
                [self.config.PDF_MULTIMODAL_PROMPT, pdf_part],
                generation_config=self.config.GENERATION_CONFIG
            )
            return response.text
        
        extraction_text = self._retry_with_backoff(_generate)
        
        # Structure result
        result = [{
            "content": extraction_text,
            "size_bytes": len(pdf_bytes),
            "timestamp": time.time()
        }]
        
        # Cache result
        if self.cache:
            self.cache.put(cache_key, result)
        
        logger.info(f"PDF parsed: {len(pdf_bytes)} bytes")
        return result
    
    # ==================== VIDEO/AUDIO MODALITY ====================
    
    def transcribe_video(self, video_bytes: bytes, mime_type: str = "video/mp4") -> Dict[str, Any]:
        """
        Transcribe and extract content from video.
        
        Args:
            video_bytes: Video file data
            mime_type: MIME type (video/mp4, video/webm, etc.)
        
        Returns:
            Dict with transcript, topics, and visual elements
        """
        if not video_bytes:
            raise ValueError("Video bytes cannot be empty")
        
        # Check cache
        if self.cache:
            video_hash = hashlib.md5(video_bytes).hexdigest()
            cache_key = self._get_cache_key("video_transcription", video_hash)
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug("Video transcription cache hit")
                return cached
        
        # Transcribe video
        def _generate():
            model = genai.GenerativeModel(self.config.VISION_MODEL)
            
            video_part = {
                "mime_type": mime_type,
                "data": video_bytes
            }
            
            response = model.generate_content(
                [self.config.VIDEO_TRANSCRIPTION_PROMPT, video_part],
                generation_config=self.config.GENERATION_CONFIG
            )
            return response.text
        
        transcription_text = self._retry_with_backoff(_generate)
        
        result = {
            "transcription": transcription_text,
            "mime_type": mime_type,
            "size_bytes": len(video_bytes),
            "timestamp": time.time()
        }
        
        # Cache result
        if self.cache:
            self.cache.put(cache_key, result)
        
        logger.info(f"Video transcribed: {mime_type}, {len(video_bytes)} bytes")
        return result
    
    def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/mpeg") -> Dict[str, Any]:
        """
        Transcribe audio content.
        
        Args:
            audio_bytes: Audio file data
            mime_type: MIME type (audio/mpeg, audio/wav, etc.)
        
        Returns:
            Dict with transcript, speakers, and topics
        """
        if not audio_bytes:
            raise ValueError("Audio bytes cannot be empty")
        
        # Check cache
        if self.cache:
            audio_hash = hashlib.md5(audio_bytes).hexdigest()
            cache_key = self._get_cache_key("audio_transcription", audio_hash)
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug("Audio transcription cache hit")
                return cached
        
        # Transcribe audio
        def _generate():
            model = genai.GenerativeModel(self.config.VISION_MODEL)
            
            audio_part = {
                "mime_type": mime_type,
                "data": audio_bytes
            }
            
            response = model.generate_content(
                [self.config.AUDIO_TRANSCRIPTION_PROMPT, audio_part],
                generation_config=self.config.GENERATION_CONFIG
            )
            return response.text
        
        transcription_text = self._retry_with_backoff(_generate)
        
        result = {
            "transcription": transcription_text,
            "mime_type": mime_type,
            "size_bytes": len(audio_bytes),
            "timestamp": time.time()
        }
        
        # Cache result
        if self.cache:
            self.cache.put(cache_key, result)
        
        logger.info(f"Audio transcribed: {mime_type}, {len(audio_bytes)} bytes")
        return result
    
    # ==================== UTILITY METHODS ====================
    
    def clear_cache(self) -> None:
        """Clear all cached results"""
        if self.cache:
            self.cache.clear()
            logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.cache:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "size": len(self.cache.cache),
            "max_size": self.cache.max_size,
            "ttl_seconds": self.cache.ttl_seconds
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        health = {
            "service": "GeminiService",
            "status": "unknown",
            "api_configured": bool(self.config.GEMINI_API_KEY),
            "cache_enabled": self.config.CACHE_ENABLED,
            "rate_limit": f"{self.config.MAX_REQUESTS_PER_MINUTE}/min",
        }
        
        # Try a simple API call
        try:
            if self.config.GEMINI_API_KEY:
                test_embedding = self.generate_embedding("health check")
                health["status"] = "healthy"
                health["embedding_dimension"] = len(test_embedding)
            else:
                health["status"] = "degraded"
                health["error"] = "API key not configured"
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
        
        return health
    
    def upload_file(self, file_path: str):
        """
        Upload a file to Gemini for processing
        
        Args:
            file_path: Path to file
            
        Returns:
            Gemini file object
        """
        try:
            logger.info(f"Uploading file to Gemini: {file_path}")
            
            # Check if API key is configured
            if not self.config.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not configured! Cannot upload file.")
            
            # Check if GOOGLE_API_KEY env var is set (needed for File API)
            import os
            if not os.getenv("GOOGLE_API_KEY"):
                logger.error("❌ GOOGLE_API_KEY environment variable not set!")
                logger.error("   File API requires GOOGLE_API_KEY to be set")
                logger.error("   This should have been set automatically in __init__")
                raise ValueError("GOOGLE_API_KEY environment variable not set for File API")
            
            uploaded_file = genai.upload_file(file_path)
            logger.info(f"✅ File uploaded successfully: {uploaded_file.name}")
            return uploaded_file
            
        except Exception as e:
            logger.error("="*70)
            logger.error(f"❌ FILE UPLOAD FAILED")
            logger.error(f"   File: {file_path}")
            logger.error(f"   Error Type: {type(e).__name__}")
            logger.error(f"   Error Message: {str(e)}")
            logger.error("="*70)
            raise
    
    def generate_content_with_file(self, file_obj, prompt: str) -> str:
        """
        Generate content using uploaded file and prompt
        
        Args:
            file_obj: Uploaded Gemini file object
            prompt: Text prompt for generation
            
        Returns:
            Generated text content
        """
        try:
            model = genai.GenerativeModel(self.config.TEXT_MODEL)
            response = model.generate_content([file_obj, prompt])
            return response.text
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise
