"""
EngineIQ Base Connector

Abstract base class for all EngineIQ connectors.
All connectors must extend this class and implement abstract methods.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional
import uuid
import time
import logging
import re

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """Abstract base class for all EngineIQ connectors"""

    def __init__(
        self,
        credentials: dict,
        gemini_service,
        qdrant_service,
    ):
        """
        Initialize base connector.

        Args:
            credentials: Authentication credentials for the source
            gemini_service: GeminiService instance for embeddings
            qdrant_service: QdrantService instance for indexing
        """
        self.credentials = credentials
        self.gemini = gemini_service
        self.qdrant = qdrant_service
        self.source_name = self.__class__.__name__.replace("Connector", "").lower()
        logger.info(f"Initialized {self.source_name} connector")

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the external service.

        Returns:
            bool: True if authentication successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_content(
        self, since: Optional[int] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        Yield content items from the source.

        Args:
            since: Unix timestamp to fetch content modified after this time

        Yields:
            dict: Content item with standardized structure:
                {
                    "id": str,
                    "title": str,
                    "raw_content": str,
                    "content_type": str,  # text|code|image|pdf|video|audio
                    "file_type": str,
                    "url": str,
                    "created_at": int,
                    "modified_at": int,
                    "owner": str,
                    "contributors": [str],
                    "permissions": dict,
                    "metadata": dict
                }
        """
        pass

    async def extract_content(self, item: dict) -> str:
        """
        Extract text content from various file types using Gemini.

        Args:
            item: Content item with raw_content and content_type

        Returns:
            str: Extracted text content
        """
        content_type = item.get("content_type", "text")
        raw_content = item.get("raw_content", "")

        try:
            if content_type == "code":
                # Use Gemini to analyze code semantically
                result = await self.gemini.analyze_code(
                    code=raw_content, language=item.get("file_type", "")
                )
                return f"{result.get('purpose', '')}. Concepts: {', '.join(result.get('concepts', []))}. Code:\n{raw_content}"

            elif content_type == "image":
                # Use Gemini Vision
                result = await self.gemini.analyze_image(raw_content)
                return result.get("semantic_description", "")

            elif content_type == "pdf":
                # Use Gemini multimodal PDF parsing
                result = await self.gemini.parse_pdf(raw_content)
                return result.get("text", "")

            elif content_type == "video":
                # Use Gemini video understanding
                result = await self.gemini.analyze_video(raw_content)
                transcript = result.get("transcript", "")
                moments = result.get("key_moments", [])
                moments_text = "\n".join(
                    [f"[{m['timestamp']}] {m['description']}" for m in moments]
                )
                return f"{transcript}\n\nKey Moments:\n{moments_text}"

            elif content_type == "audio":
                # Use Gemini audio transcription
                result = await self.gemini.transcribe_audio(raw_content)
                return result.get("transcript", "")

            else:  # text (default)
                return raw_content

        except Exception as e:
            logger.error(f"Error extracting content from {item.get('id')}: {e}")
            # Fallback to raw content
            return raw_content

    async def generate_embedding(self, content: str) -> List[float]:
        """
        Generate Gemini embedding with caching.

        Args:
            content: Text content to embed

        Returns:
            List[float]: 768-dimensional embedding vector
        """
        return await self.gemini.generate_embedding(
            content=content, task_type="retrieval_document"
        )

    async def index_item(self, item: dict):
        """
        Process and index a single item to Qdrant.

        Args:
            item: Content item to index
        """
        try:
            # Extract content
            content = await self.extract_content(item)

            # Chunk if too large (>10k chars)
            chunks = (
                self.chunk_content(content) if len(content) > 10000 else [content]
            )

            for idx, chunk in enumerate(chunks):
                # Generate embedding
                embedding = await self.generate_embedding(chunk)

                # Prepare payload
                doc_id = (
                    f"{item['id']}_chunk_{idx}" if len(chunks) > 1 else item["id"]
                )

                payload = {
                    "source": self.source_name,
                    "content_type": item["content_type"],
                    "file_type": item["file_type"],
                    "title": item["title"],
                    "content": chunk,
                    "url": item["url"],
                    "created_at": item["created_at"],
                    "modified_at": item["modified_at"],
                    "owner": item["owner"],
                    "contributors": item["contributors"],
                    "permissions": item["permissions"],
                    "metadata": item["metadata"],
                    "tags": self.extract_tags(chunk),
                    "language": self.detect_language(chunk),
                    "embedding_model": "gemini-text-embedding-004",
                    "embedding_version": "v1",
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                }

                # Index to Qdrant knowledge_base
                self.qdrant.index_document(
                    collection_name="knowledge_base",
                    doc_id=doc_id,
                    vector=embedding,
                    payload=payload,
                )

                # Update expertise map
                await self.update_expertise_map(item, chunk, embedding)

        except Exception as e:
            logger.error(f"Error indexing item {item.get('id')}: {e}")
            raise

    async def sync(self, since: Optional[int] = None):
        """
        Full sync - index all content.

        Args:
            since: Unix timestamp to sync content modified after this time
        """
        count = 0
        errors = 0

        logger.info(f"Starting {self.source_name} sync...")

        async for item in self.get_content(since):
            try:
                await self.index_item(item)
                count += 1
                if count % 10 == 0:
                    logger.info(f"✓ Indexed {count} items from {self.source_name}")
            except Exception as e:
                logger.error(f"✗ Error indexing {item.get('id')}: {e}")
                errors += 1
                continue

        logger.info(
            f"✓ Synced {count} total items from {self.source_name} ({errors} errors)"
        )
        return count

    @abstractmethod
    async def watch_for_changes(self):
        """
        Set up webhooks or polling for real-time updates.

        Implementation depends on the source API capabilities.
        """
        pass

    def chunk_content(self, content: str, chunk_size: int = 8000) -> List[str]:
        """
        Smart chunking with overlap.

        Args:
            content: Text content to chunk
            chunk_size: Maximum characters per chunk

        Returns:
            List[str]: List of text chunks
        """
        if len(content) <= chunk_size:
            return [content]

        chunks = []
        overlap = 500

        for i in range(0, len(content), chunk_size - overlap):
            chunk = content[i : i + chunk_size]
            chunks.append(chunk)

        return chunks

    def extract_tags(self, content: str) -> List[str]:
        """
        Extract relevant tags from content.

        Args:
            content: Text content

        Returns:
            List[str]: Extracted tags
        """
        # Common tech terms and topics
        tech_terms = [
            "kubernetes",
            "k8s",
            "docker",
            "python",
            "javascript",
            "typescript",
            "react",
            "vue",
            "angular",
            "database",
            "postgres",
            "mysql",
            "mongodb",
            "redis",
            "api",
            "rest",
            "graphql",
            "authentication",
            "auth",
            "oauth",
            "deployment",
            "cicd",
            "ci/cd",
            "testing",
            "unit-test",
            "integration",
            "monitoring",
            "observability",
            "prometheus",
            "grafana",
            "security",
            "vulnerability",
            "performance",
            "optimization",
            "aws",
            "azure",
            "gcp",
            "cloud",
            "terraform",
            "ansible",
            "jenkins",
            "gitlab",
            "github",
            "actions",
            "migration",
            "schema",
            "backup",
            "recovery",
        ]

        content_lower = content.lower()
        return [term for term in tech_terms if term in content_lower]

    def detect_language(self, content: str) -> str:
        """
        Detect content language.

        Args:
            content: Text content

        Returns:
            str: Language code (e.g., "en", "es", "fr")
        """
        # Simple detection based on common words
        # In production, use langdetect or similar library
        spanish_words = ["el", "la", "los", "las", "de", "que", "en", "y", "es"]
        french_words = ["le", "la", "les", "de", "un", "une", "et", "est", "dans"]

        content_lower = content.lower()
        words = content_lower.split()[:100]  # Check first 100 words

        spanish_count = sum(1 for word in words if word in spanish_words)
        french_count = sum(1 for word in words if word in french_words)

        if spanish_count > 10:
            return "es"
        elif french_count > 10:
            return "fr"
        else:
            return "en"

    async def update_expertise_map(
        self, item: dict, content: str, embedding: List[float]
    ):
        """
        Track contributor expertise in expertise_map collection.

        Args:
            item: Content item
            content: Extracted text content
            embedding: Content embedding vector
        """
        try:
            for contributor in item["contributors"]:
                score = self.calculate_contribution_score(item)
                action_type = self.get_action_type(item)

                expertise_id = f"{contributor}_{item['id']}"

                payload = {
                    "user_id": contributor,
                    "user_name": contributor,  # Override in subclass if name available
                    "topic": item["title"],
                    "expertise_score": score,
                    "evidence": [
                        {
                            "source": self.source_name,
                            "action": action_type,
                            "doc_id": item["id"],
                            "doc_title": item["title"],
                            "doc_url": item["url"],
                            "timestamp": item["modified_at"],
                            "contribution_score": score,
                        }
                    ],
                    "last_contribution": item["modified_at"],
                    "contribution_count": 1,
                    "tags": self.extract_tags(content),
                    "trend": "stable",
                }

                self.qdrant.index_document(
                    collection_name="expertise_map",
                    doc_id=expertise_id,
                    vector=embedding,
                    payload=payload,
                )

        except Exception as e:
            logger.warning(f"Error updating expertise map: {e}")

    def calculate_contribution_score(self, item: dict) -> float:
        """
        Calculate contribution score based on action type.
        Override in subclasses for source-specific scoring.

        Args:
            item: Content item

        Returns:
            float: Contribution score (default: 1.0)
        """
        return 1.0

    def get_action_type(self, item: dict) -> str:
        """
        Get action type (authored, reviewed, answered, etc.).
        Override in subclasses.

        Args:
            item: Content item

        Returns:
            str: Action type (default: "authored")
        """
        return "authored"

    def should_trigger_approval(self, item: dict) -> bool:
        """
        Determine if item should trigger human-in-loop approval.

        Args:
            item: Content item

        Returns:
            bool: True if approval needed
        """
        # Check for confidential in title or metadata
        title_lower = item.get("title", "").lower()
        confidential_keywords = [
            "confidential",
            "secret",
            "private",
            "restricted",
            "sensitive",
        ]

        if any(keyword in title_lower for keyword in confidential_keywords):
            return True

        # Check permissions
        permissions = item.get("permissions", {})
        if permissions.get("sensitivity") in ["confidential", "restricted"]:
            return True

        return False
