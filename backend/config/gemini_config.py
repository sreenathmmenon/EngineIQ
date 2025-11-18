"""
EngineIQ Gemini Configuration

Configuration settings for Gemini API integration across all modalities.
"""

import os
from typing import Dict


class GeminiConfig:
    """Configuration for Gemini API integration"""

    # API settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Model settings
    EMBEDDING_MODEL = "text-embedding-004"
    EMBEDDING_DIMENSION = 768
    TEXT_MODEL = "gemini-2.0-flash-exp"
    VISION_MODEL = "gemini-2.0-flash-exp"
    
    # Rate limiting
    MAX_REQUESTS_PER_MINUTE = 60
    RATE_LIMIT_WINDOW_SECONDS = 60
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 1.0
    RETRY_EXPONENTIAL_BASE = 2
    RETRY_MAX_DELAY = 60.0
    
    # Batch processing
    MAX_BATCH_SIZE = 100
    EMBEDDING_BATCH_SIZE = 100
    
    # Content limits (characters)
    MAX_TEXT_LENGTH = 10000
    MAX_CODE_LENGTH = 20000
    
    # Cache settings
    CACHE_ENABLED = True
    CACHE_TTL_SECONDS = 3600
    MAX_CACHE_SIZE = 1000
    
    # Request timeouts (seconds)
    EMBEDDING_TIMEOUT = 30
    TEXT_GENERATION_TIMEOUT = 60
    VISION_TIMEOUT = 90
    VIDEO_TIMEOUT = 300
    
    # Generation parameters
    GENERATION_CONFIG: Dict = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 2048,
    }
    
    # Code analysis prompts
    CODE_ANALYSIS_PROMPT = """Analyze the following {language} code and provide:
1. A brief summary of what it does
2. Key functions/classes and their purposes
3. Any potential issues or improvements
4. Dependencies and external libraries used

Code:
{code}"""
    
    FUNCTION_EXTRACTION_PROMPT = """Extract all function/method signatures from this {language} code.
For each function provide:
- Name
- Parameters with types (if available)
- Return type (if available)
- Brief description

Code:
{code}"""
    
    # Query understanding prompt
    QUERY_UNDERSTANDING_PROMPT = """Analyze this search query and extract:
1. Primary intent (search|question|command|clarification)
2. Key entities and concepts
3. Suggested search keywords
4. Required data sources (if identifiable)

Query: {query}

Respond in JSON format."""
    
    # Image analysis prompts
    IMAGE_ANALYSIS_PROMPT = """Analyze this image and describe:
1. Main content and purpose
2. Text visible in the image (if any)
3. Key visual elements
4. Relevant technical details"""
    
    DIAGRAM_EXTRACTION_PROMPT = """This is a technical diagram. Extract:
1. Type of diagram (architecture/flowchart/sequence/etc)
2. Main components and their relationships
3. Data flows or process steps
4. Key annotations or labels"""
    
    # Multimodal PDF prompt
    PDF_MULTIMODAL_PROMPT = """Extract content from this PDF page:
1. All text content
2. Descriptions of images, diagrams, or charts
3. Table structures (if any)
4. Key formatting that conveys meaning"""
    
    # Video/Audio prompts
    VIDEO_TRANSCRIPTION_PROMPT = """Transcribe this video and provide:
1. Full transcript with timestamps
2. Key topics discussed
3. Important visual elements shown
4. Action items or conclusions"""
    
    AUDIO_TRANSCRIPTION_PROMPT = """Transcribe this audio and provide:
1. Full transcript
2. Speaker identification (if multiple speakers)
3. Key topics and timestamps
4. Action items or important points"""
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        if cls.EMBEDDING_DIMENSION != 768:
            raise ValueError("EMBEDDING_DIMENSION must be 768 for text-embedding-004")
        
        if cls.MAX_BATCH_SIZE > 100:
            raise ValueError("MAX_BATCH_SIZE cannot exceed 100")
        
        return True
    
    @classmethod
    def get_model_for_task(cls, task: str) -> str:
        """Get appropriate model for specific task"""
        model_mapping = {
            "embedding": cls.EMBEDDING_MODEL,
            "text": cls.TEXT_MODEL,
            "code": cls.TEXT_MODEL,
            "vision": cls.VISION_MODEL,
            "video": cls.VISION_MODEL,
            "audio": cls.VISION_MODEL,
        }
        return model_mapping.get(task, cls.TEXT_MODEL)
