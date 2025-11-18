"""
EngineIQ Box Connector

Complete Box integration showcasing Gemini multimodal capabilities.
Handles PDFs, images, documents with advanced content extraction.
"""

from typing import AsyncGenerator, Dict, List, Optional
from boxsdk import Client, OAuth2
from boxsdk.exception import BoxAPIException
from .base_connector import BaseConnector
import logging
import os
import tempfile
import mimetypes

logger = logging.getLogger(__name__)


class BoxConnector(BaseConnector):
    """
    Box connector for indexing files with multimodal content extraction.

    Features:
    - PDF extraction using Gemini multimodal parsing
    - Image analysis using Gemini Vision
    - Document extraction (DOCX, TXT, etc.)
    - File permission handling
    - Sensitivity detection (confidential, restricted)
    - Comment extraction
    - Version tracking (latest only)
    - Folder hierarchy preservation
    """

    # File type to content type mapping
    CONTENT_TYPE_MAP = {
        # Images
        ".jpg": "image",
        ".jpeg": "image",
        ".png": "image",
        ".gif": "image",
        ".bmp": "image",
        ".tiff": "image",
        ".webp": "image",
        # Documents
        ".pdf": "pdf",
        ".doc": "text",
        ".docx": "text",
        ".txt": "text",
        ".md": "text",
        ".rtf": "text",
        # Spreadsheets
        ".xls": "text",
        ".xlsx": "text",
        ".csv": "text",
        # Presentations
        ".ppt": "text",
        ".pptx": "text",
        # Code
        ".py": "code",
        ".js": "code",
        ".java": "code",
        ".cpp": "code",
        ".go": "code",
        ".rb": "code",
        ".php": "code",
        ".sql": "code",
        ".yaml": "code",
        ".yml": "code",
        ".json": "code",
        ".xml": "code",
    }

    # Sensitive keywords for detection
    SENSITIVE_KEYWORDS = [
        "confidential",
        "restricted",
        "internal-only",
        "private",
        "secret",
        "classified",
        "sensitive",
    ]

    def __init__(self, credentials: dict, gemini_service, qdrant_service):
        """
        Initialize Box connector.

        Args:
            credentials: Dict with:
                - access_token: Box OAuth2 access token OR
                - client_id, client_secret: For OAuth2 OR
                - jwt_key_id, jwt_key: For JWT auth
        """
        super().__init__(credentials, gemini_service, qdrant_service)

        # Initialize Box client based on auth method
        if "access_token" in credentials:
            # Direct token authentication
            oauth = OAuth2(
                client_id=credentials.get("client_id", ""),
                client_secret=credentials.get("client_secret", ""),
                access_token=credentials["access_token"],
            )
            self.client = Client(oauth)
        else:
            # Would implement JWT auth here for production
            raise ValueError(
                "Box connector requires 'access_token' in credentials"
            )

        self.folder_cache = {}  # Cache folder paths

    async def authenticate(self) -> bool:
        """
        Authenticate with Box.

        Returns:
            bool: True if authentication successful
        """
        try:
            # Test authentication by getting current user
            user = self.client.user().get()
            logger.info(f"✓ Authenticated with Box as {user.name} ({user.login})")
            return True
        except BoxAPIException as e:
            logger.error(f"Box authentication failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Box authentication error: {e}")
            return False

    async def get_content(
        self, since: Optional[int] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        Fetch all files from all accessible folders.

        Args:
            since: Unix timestamp to fetch files modified after this time

        Yields:
            dict: Standardized content item
        """
        # Get all folders recursively
        folders = await self.get_folders()
        logger.info(f"Found {len(folders)} accessible Box folders")

        for folder in folders:
            logger.info(f"Fetching files from {folder['path']}...")

            async for file in self.get_files(folder["id"], since):
                try:
                    # Get file details
                    file_obj = self.client.file(file["id"]).get()

                    # Download file content for extraction
                    content = await self._download_file(file_obj)

                    if content is None:
                        logger.warning(f"Could not download {file_obj.name}")
                        continue

                    # Determine content type
                    file_extension = os.path.splitext(file_obj.name)[1].lower()
                    content_type = self.CONTENT_TYPE_MAP.get(
                        file_extension, "text"
                    )

                    # Extract metadata
                    metadata = await self.extract_metadata(file_obj, folder)

                    # Get permissions
                    permissions = await self._get_permissions(file_obj, metadata)

                    # Get owner and contributors
                    owner = file_obj.owned_by.login if file_obj.owned_by else "unknown"
                    contributors = await self._get_contributors(file_obj)

                    yield {
                        "id": f"box_{file_obj.id}",
                        "title": file_obj.name,
                        "raw_content": content,
                        "content_type": content_type,
                        "file_type": file_extension[1:] if file_extension else "unknown",
                        "url": f"https://app.box.com/file/{file_obj.id}",
                        "created_at": int(file_obj.created_at.timestamp()),
                        "modified_at": int(file_obj.modified_at.timestamp()),
                        "owner": owner,
                        "contributors": contributors,
                        "permissions": permissions,
                        "metadata": metadata,
                    }

                except Exception as e:
                    logger.error(f"Error processing file {file.get('name', 'unknown')}: {e}")
                    continue

    async def get_folders(self, folder_id: str = "0", path: str = "/") -> List[dict]:
        """
        Get all folders recursively.

        Args:
            folder_id: Starting folder ID (0 = root)
            path: Current path for tracking

        Returns:
            List[dict]: List of folders with id and path
        """
        folders = []

        try:
            folder = self.client.folder(folder_id).get()

            # Add current folder
            folders.append({"id": folder_id, "path": path, "name": folder.name})

            # Cache path
            self.folder_cache[folder_id] = path

            # Get subfolders
            items = folder.get_items()
            for item in items:
                if item.type == "folder":
                    subfolder_path = f"{path}{item.name}/"
                    subfolders = await self.get_folders(item.id, subfolder_path)
                    folders.extend(subfolders)

        except BoxAPIException as e:
            logger.warning(f"Could not access folder {folder_id}: {e}")

        return folders

    async def get_files(
        self, folder_id: str, since: Optional[int] = None
    ) -> AsyncGenerator[dict, None]:
        """
        Get all files from a folder.

        Args:
            folder_id: Box folder ID
            since: Unix timestamp to filter files

        Yields:
            dict: File info
        """
        try:
            folder = self.client.folder(folder_id).get()
            items = folder.get_items(limit=100, offset=0)

            for item in items:
                if item.type == "file":
                    # Filter by modification time if specified
                    if since and item.modified_at:
                        if int(item.modified_at.timestamp()) < since:
                            continue

                    yield {
                        "id": item.id,
                        "name": item.name,
                        "size": item.size,
                        "modified_at": item.modified_at,
                    }

        except BoxAPIException as e:
            logger.warning(f"Could not access files in folder {folder_id}: {e}")

    async def extract_content(self, item: dict) -> str:
        """
        Extract content using appropriate method based on file type.

        Args:
            item: Content item with raw_content and content_type

        Returns:
            str: Extracted text content
        """
        content_type = item.get("content_type", "text")
        raw_content = item.get("raw_content", "")

        try:
            if content_type == "pdf":
                # Use Gemini multimodal PDF parsing
                logger.info(f"Parsing PDF with Gemini multimodal: {item.get('title')}")
                result = await self.gemini.parse_pdf_multimodal(raw_content)
                
                # Combine text and image descriptions
                text = result.get("text", "")
                images = result.get("image_descriptions", [])
                
                if images:
                    images_text = "\n\n=== Images ===\n" + "\n".join(
                        [f"- {desc}" for desc in images]
                    )
                    return f"{text}{images_text}"
                return text

            elif content_type == "image":
                # Use Gemini Vision for image analysis
                logger.info(f"Analyzing image with Gemini Vision: {item.get('title')}")
                result = await self.gemini.analyze_image(raw_content)
                
                # Return comprehensive description
                return f"""Image Analysis:
Type: {result.get('type', 'unknown')}
Main Components: {', '.join(result.get('main_components', []))}
Concepts: {', '.join(result.get('concepts', []))}

Description:
{result.get('semantic_description', '')}"""

            elif content_type == "code":
                # Use Gemini code analysis
                result = await self.gemini.analyze_code(
                    code=raw_content, language=item.get("file_type", "")
                )
                return f"{result.get('purpose', '')}. Concepts: {', '.join(result.get('concepts', []))}. Code:\n{raw_content}"

            else:
                # Text or document - return as-is
                return raw_content

        except Exception as e:
            logger.error(f"Error extracting content from {item.get('title')}: {e}")
            # Fallback to raw content
            return raw_content if isinstance(raw_content, str) else ""

    async def extract_metadata(self, file_obj, folder: dict) -> dict:
        """
        Extract Box-specific metadata.

        Args:
            file_obj: Box File object
            folder: Folder info dict

        Returns:
            dict: Metadata dictionary
        """
        # Get comments
        comments = []
        try:
            for comment in file_obj.get_comments():
                comments.append(
                    {
                        "user": comment.created_by.login if comment.created_by else "unknown",
                        "text": comment.message,
                        "created_at": int(comment.created_at.timestamp()) if comment.created_at else 0,
                    }
                )
        except Exception as e:
            logger.warning(f"Could not fetch comments: {e}")

        # Get tags
        tags = []
        try:
            tags_obj = file_obj.get(fields=["tags"])
            if hasattr(tags_obj, "tags") and tags_obj.tags:
                tags = tags_obj.tags
        except Exception as e:
            logger.warning(f"Could not fetch tags: {e}")

        return {
            "box_folder_id": folder["id"],
            "box_folder_path": folder["path"],
            "box_file_id": file_obj.id,
            "box_version": file_obj.version_number if hasattr(file_obj, "version_number") else "1",
            "box_comments": comments,
            "box_tags": tags,
            "box_file_size": file_obj.size,
            "box_sha1": file_obj.sha1 if hasattr(file_obj, "sha1") else None,
        }

    async def check_sensitivity(self, item: dict) -> str:
        """
        Check file sensitivity level.

        Args:
            item: Content item

        Returns:
            str: Sensitivity level (public, internal, confidential, restricted)
        """
        # Check file name
        title_lower = item.get("title", "").lower()
        
        # Confidential markers
        if any(keyword in title_lower for keyword in ["confidential", "secret", "classified"]):
            return "confidential"
        
        # Restricted markers
        if any(keyword in title_lower for keyword in ["restricted", "internal-only"]):
            return "restricted"
        
        # Check folder path
        folder_path = item.get("metadata", {}).get("box_folder_path", "").lower()
        if any(keyword in folder_path for keyword in self.SENSITIVE_KEYWORDS):
            return "confidential" if "confidential" in folder_path else "restricted"
        
        # Check tags
        tags = item.get("metadata", {}).get("box_tags", [])
        tags_lower = [tag.lower() for tag in tags]
        if any(keyword in tags_lower for keyword in self.SENSITIVE_KEYWORDS):
            return "confidential"
        
        # Default to internal for private files, public for shared
        if item.get("permissions", {}).get("public", False):
            return "public"
        
        return "internal"

    def should_trigger_approval(self, item: dict) -> bool:
        """
        Determine if file should trigger human-in-loop approval.

        Args:
            item: Content item

        Returns:
            bool: True if approval needed
        """
        # Check sensitivity level
        sensitivity = item.get("permissions", {}).get("sensitivity", "internal")
        if sensitivity in ["confidential", "restricted"]:
            logger.info(f"Human-in-loop triggered for {sensitivity} file: {item.get('title')}")
            return True

        # Check for sensitive keywords in title
        title_lower = item.get("title", "").lower()
        if any(keyword in title_lower for keyword in self.SENSITIVE_KEYWORDS):
            logger.info(f"Human-in-loop triggered for sensitive file: {item.get('title')}")
            return True

        # Check folder path
        folder_path = item.get("metadata", {}).get("box_folder_path", "").lower()
        if "confidential" in folder_path or "restricted" in folder_path:
            return True

        return super().should_trigger_approval(item)

    async def watch_for_changes(self):
        """
        Set up Box webhook for real-time file updates.

        In production, this would register a webhook endpoint.
        For now, use polling.
        """
        import asyncio

        logger.info("Starting Box change watcher (polling mode)...")

        last_sync = int(asyncio.get_event_loop().time())

        while True:
            try:
                await asyncio.sleep(600)  # 10 minutes

                logger.info("Checking for new Box files...")
                count = await self.sync(since=last_sync)
                logger.info(f"✓ Synced {count} new files")

                last_sync = int(asyncio.get_event_loop().time())

            except Exception as e:
                logger.error(f"Error in Box watcher: {e}")
                await asyncio.sleep(60)

    # Private helper methods

    async def _download_file(self, file_obj) -> Optional[bytes]:
        """Download file content."""
        try:
            # Download to temp file
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_path = tmp_file.name
                
            with open(tmp_path, "wb") as f:
                file_obj.download_to(f)
            
            # Read content
            with open(tmp_path, "rb") as f:
                content = f.read()
            
            # Clean up
            os.unlink(tmp_path)
            
            return content

        except Exception as e:
            logger.error(f"Error downloading file {file_obj.name}: {e}")
            return None

    async def _get_permissions(self, file_obj, metadata: dict) -> dict:
        """Build permissions structure for file."""
        # Check if file is shared publicly
        shared_link = None
        try:
            shared_link = file_obj.get_shared_link()
        except:
            pass

        is_public = shared_link is not None and shared_link.get("access") == "open"

        # Get collaborators
        users = []
        try:
            collaborations = file_obj.get_collaborations()
            for collab in collaborations:
                if collab.accessible_by:
                    users.append(collab.accessible_by.login)
        except:
            pass

        # Check sensitivity
        sensitivity = await self.check_sensitivity({
            "title": file_obj.name,
            "metadata": metadata,
            "permissions": {"public": is_public}
        })

        # Determine restrictions
        offshore_restricted = sensitivity in ["confidential", "restricted"]
        third_party_restricted = sensitivity in ["confidential", "restricted"]

        return {
            "public": is_public,
            "teams": [],  # Box doesn't have team concept like Slack
            "users": users,
            "sensitivity": sensitivity,
            "offshore_restricted": offshore_restricted,
            "third_party_restricted": third_party_restricted,
        }

    async def _get_contributors(self, file_obj) -> List[str]:
        """Get all contributors (owner + collaborators)."""
        contributors = set()

        # Add owner
        if file_obj.owned_by:
            contributors.add(file_obj.owned_by.login)

        # Add collaborators
        try:
            collaborations = file_obj.get_collaborations()
            for collab in collaborations:
                if collab.accessible_by:
                    contributors.add(collab.accessible_by.login)
        except:
            pass

        # Add commenters
        try:
            for comment in file_obj.get_comments():
                if comment.created_by:
                    contributors.add(comment.created_by.login)
        except:
            pass

        return list(contributors)

    def get_action_type(self, item: dict) -> str:
        """Get action type for expertise tracking."""
        # File authors are considered "authored"
        return "authored"

    def calculate_contribution_score(self, item: dict) -> float:
        """
        Calculate contribution score for Box files.

        Scoring:
        - Base: 2.0 (creating documents is valuable)
        - PDFs/Images: +1.0 (multimodal content)
        - Comments: +0.1 per comment (up to +1.0)
        - Large files: +0.5 if > 100KB
        """
        base_score = 2.0

        # Multimodal bonus
        content_type = item.get("content_type", "text")
        multimodal_bonus = 1.0 if content_type in ["pdf", "image"] else 0.0

        # Comments indicate engagement
        comments = item.get("metadata", {}).get("box_comments", [])
        comment_bonus = min(len(comments) * 0.1, 1.0)

        # Size bonus for substantial documents
        file_size = item.get("metadata", {}).get("box_file_size", 0)
        size_bonus = 0.5 if file_size > 100000 else 0.0  # 100KB

        return base_score + multimodal_bonus + comment_bonus + size_bonus
