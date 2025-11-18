"""
EngineIQ GitHub Connector

Connector for indexing GitHub repositories, code, commits, pull requests, and issues.
Integrates with GeminiService for code understanding and QdrantService for indexing.
"""

import asyncio
import logging
import time
from typing import AsyncGenerator, Dict, List, Optional, Any
from github import Github, GithubException
from github.Repository import Repository
from github.ContentFile import ContentFile
from github.Commit import Commit
from github.PullRequest import PullRequest
from github.Issue import Issue
import re

from .base_connector import BaseConnector

logger = logging.getLogger(__name__)


class GitHubConnector(BaseConnector):
    """
    GitHub connector for EngineIQ.
    
    Features:
    - Authenticate with Personal Access Token
    - List accessible repositories
    - Extract code files with language detection
    - Analyze code using GeminiService
    - Extract commits, PRs, and issues
    - Track contributions for expertise mapping
    - Watch for changes via webhooks
    """
    
    # File extensions to language mapping
    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.go': 'go',
        '.java': 'java',
        '.rb': 'ruby',
        '.php': 'php',
        '.c': 'c',
        '.cpp': 'cpp',
        '.cs': 'csharp',
        '.rs': 'rust',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'bash',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.json': 'json',
        '.xml': 'xml',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sql': 'sql',
        '.md': 'markdown',
        '.txt': 'text',
    }
    
    # Binary/large file extensions to skip
    SKIP_EXTENSIONS = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
        '.mp4', '.avi', '.mov', '.wmv',
        '.mp3', '.wav', '.flac',
        '.zip', '.tar', '.gz', '.rar', '.7z',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx',
        '.exe', '.dll', '.so', '.dylib',
        '.pyc', '.class', '.o',
        '.lock', '.log',
    }
    
    # Max file size to process (1MB)
    MAX_FILE_SIZE = 1024 * 1024
    
    def __init__(
        self,
        credentials: dict,
        gemini_service,
        qdrant_service,
        repo_filter: Optional[List[str]] = None
    ):
        """
        Initialize GitHub connector.
        
        Args:
            credentials: Dict with 'token' key for GitHub PAT
            gemini_service: GeminiService for code analysis
            qdrant_service: QdrantService for indexing
            repo_filter: Optional list of repo names to index (e.g., ['owner/repo'])
        """
        super().__init__(credentials, gemini_service, qdrant_service)
        self.github = None
        self.repo_filter = repo_filter
        logger.info(f"Initialized GitHub connector (repo_filter={repo_filter})")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with GitHub using Personal Access Token.
        
        Returns:
            bool: True if authentication successful
        """
        try:
            token = self.credentials.get('token')
            if not token:
                logger.error("GitHub token not provided in credentials")
                return False
            
            # Initialize PyGithub
            self.github = Github(token)
            
            # Test authentication by getting user
            user = self.github.get_user()
            logger.info(f"✓ Authenticated as GitHub user: {user.login}")
            return True
        
        except GithubException as e:
            logger.error(f"GitHub authentication failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during GitHub authentication: {e}")
            return False
    
    async def get_repositories(self) -> List[Repository]:
        """
        Get list of accessible repositories.
        
        Returns:
            List[Repository]: List of PyGithub Repository objects
        """
        if not self.github:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        try:
            repos = []
            
            # Get all repos user has access to
            for repo in self.github.get_user().get_repos():
                # Apply filter if specified
                if self.repo_filter:
                    full_name = repo.full_name
                    if full_name not in self.repo_filter:
                        continue
                
                repos.append(repo)
                logger.debug(f"Found repo: {repo.full_name}")
            
            logger.info(f"✓ Found {len(repos)} accessible repositories")
            return repos
        
        except GithubException as e:
            logger.error(f"Error fetching repositories: {e}")
            return []
    
    async def get_files(self, repo: Repository, path: str = "") -> AsyncGenerator[ContentFile, None]:
        """
        Recursively get all files from a repository.
        
        Args:
            repo: PyGithub Repository object
            path: Path within repo to start from
        
        Yields:
            ContentFile: PyGithub ContentFile objects
        """
        try:
            contents = repo.get_contents(path)
            
            # Handle single file
            if not isinstance(contents, list):
                contents = [contents]
            
            for content in contents:
                if content.type == "dir":
                    # Recursively get files from directory
                    async for file in self.get_files(repo, content.path):
                        yield file
                else:
                    # Check if we should process this file
                    file_ext = self._get_file_extension(content.name)
                    
                    if file_ext in self.SKIP_EXTENSIONS:
                        logger.debug(f"Skipping binary/large file: {content.path}")
                        continue
                    
                    if content.size > self.MAX_FILE_SIZE:
                        logger.debug(f"Skipping large file ({content.size} bytes): {content.path}")
                        continue
                    
                    yield content
        
        except GithubException as e:
            logger.warning(f"Error accessing path {path} in {repo.full_name}: {e}")
    
    async def get_commits(self, repo: Repository, since: Optional[int] = None) -> List[Commit]:
        """
        Get commits from a repository.
        
        Args:
            repo: PyGithub Repository object
            since: Unix timestamp to get commits after
        
        Returns:
            List[Commit]: List of commit objects
        """
        try:
            kwargs = {}
            if since:
                kwargs['since'] = time.gmtime(since)
            
            commits = list(repo.get_commits(**kwargs))
            logger.info(f"✓ Found {len(commits)} commits in {repo.full_name}")
            return commits
        
        except GithubException as e:
            logger.error(f"Error fetching commits from {repo.full_name}: {e}")
            return []
    
    async def get_pull_requests(
        self,
        repo: Repository,
        state: str = "all",
        since: Optional[int] = None
    ) -> List[PullRequest]:
        """
        Get pull requests from a repository.
        
        Args:
            repo: PyGithub Repository object
            state: PR state (open, closed, all)
            since: Unix timestamp to get PRs after
        
        Returns:
            List[PullRequest]: List of PR objects
        """
        try:
            prs = []
            
            for pr in repo.get_pulls(state=state):
                # Filter by date if specified
                if since and pr.created_at.timestamp() < since:
                    continue
                
                prs.append(pr)
            
            logger.info(f"✓ Found {len(prs)} pull requests in {repo.full_name}")
            return prs
        
        except GithubException as e:
            logger.error(f"Error fetching pull requests from {repo.full_name}: {e}")
            return []
    
    async def get_issues(
        self,
        repo: Repository,
        state: str = "all",
        since: Optional[int] = None
    ) -> List[Issue]:
        """
        Get issues from a repository.
        
        Args:
            repo: PyGithub Repository object
            state: Issue state (open, closed, all)
            since: Unix timestamp to get issues after
        
        Returns:
            List[Issue]: List of issue objects
        """
        try:
            issues = []
            
            for issue in repo.get_issues(state=state):
                # Skip pull requests (they're also returned as issues)
                if issue.pull_request:
                    continue
                
                # Filter by date if specified
                if since and issue.created_at.timestamp() < since:
                    continue
                
                issues.append(issue)
            
            logger.info(f"✓ Found {len(issues)} issues in {repo.full_name}")
            return issues
        
        except GithubException as e:
            logger.error(f"Error fetching issues from {repo.full_name}: {e}")
            return []
    
    async def extract_content(self, item: dict) -> str:
        """
        Extract content from GitHub items with code understanding.
        
        Args:
            item: Content item with raw_content and content_type
        
        Returns:
            str: Extracted and analyzed content
        """
        content_type = item.get("content_type", "text")
        raw_content = item.get("raw_content", "")
        
        try:
            if content_type == "code":
                # Use GeminiService for semantic code analysis
                language = item.get("file_type", "")
                
                # Get code analysis
                analysis = self.gemini.analyze_code(raw_content, language)
                analysis_text = analysis.get("analysis", "")
                
                # Get function signatures
                functions = self.gemini.extract_code_functions(raw_content, language)
                functions_text = self._format_functions(functions)
                
                # Combine analysis with raw code
                return f"""Code Analysis:
{analysis_text}

Functions/Methods:
{functions_text}

Raw Code:
{raw_content}"""
            
            else:
                # For non-code content (PRs, issues, commits), return as-is
                return raw_content
        
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return raw_content
    
    def _format_functions(self, functions: List[Dict[str, Any]]) -> str:
        """Format function list for readability"""
        if not functions:
            return "No functions extracted"
        
        lines = []
        for func in functions:
            if isinstance(func, dict):
                if 'name' in func:
                    name = func.get('name', 'unknown')
                    params = func.get('parameters', func.get('params', []))
                    desc = func.get('description', '')
                    lines.append(f"- {name}({', '.join(map(str, params))}): {desc}")
                else:
                    lines.append(f"- {func.get('extraction', str(func))}")
            else:
                lines.append(f"- {str(func)}")
        
        return '\n'.join(lines)
    
    async def get_content(self, since: Optional[int] = None) -> AsyncGenerator[Dict, None]:
        """
        Yield all content items from GitHub repositories.
        
        Args:
            since: Unix timestamp to fetch content modified after
        
        Yields:
            dict: Standardized content items
        """
        if not self.github:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        repos = await self.get_repositories()
        
        for repo in repos:
            logger.info(f"Processing repository: {repo.full_name}")
            
            # 1. Index code files
            async for file in self.get_files(repo):
                try:
                    # Get file content
                    content = file.decoded_content.decode('utf-8', errors='ignore')
                    
                    # Detect language
                    language = self.detect_language(file.name, content)
                    
                    # Get last commit for this file
                    commits = list(repo.get_commits(path=file.path))
                    last_commit = commits[0] if commits else None
                    
                    # Filter by date if specified
                    if since and last_commit:
                        if last_commit.commit.author.date.timestamp() < since:
                            continue
                    
                    # Extract contributors
                    contributors = list(set([c.author.login for c in commits[:10] if c.author]))
                    
                    yield {
                        "id": f"{repo.full_name}/{file.path}",
                        "title": f"{file.name} - {repo.name}",
                        "raw_content": content,
                        "content_type": "code",
                        "file_type": language,
                        "url": file.html_url,
                        "created_at": int(repo.created_at.timestamp()),
                        "modified_at": int(last_commit.commit.author.date.timestamp()) if last_commit else int(time.time()),
                        "owner": repo.owner.login,
                        "contributors": contributors,
                        "permissions": {
                            "public": not repo.private,
                            "teams": [],
                            "users": [],
                            "sensitivity": "internal" if repo.private else "public",
                            "offshore_restricted": False,
                            "third_party_restricted": False,
                        },
                        "metadata": {
                            "repo": repo.full_name,
                            "path": file.path,
                            "size": file.size,
                            "sha": file.sha,
                            "language": language,
                            "stars": repo.stargazers_count,
                            "forks": repo.forks_count,
                        }
                    }
                
                except Exception as e:
                    logger.error(f"Error processing file {file.path}: {e}")
                    continue
            
            # 2. Index pull requests
            prs = await self.get_pull_requests(repo, since=since)
            for pr in prs:
                try:
                    # Combine PR description with comments
                    comments = list(pr.get_issue_comments())
                    review_comments = list(pr.get_review_comments())
                    
                    content_parts = [f"# Pull Request: {pr.title}", f"\n{pr.body or ''}"]
                    
                    if comments:
                        content_parts.append("\n## Comments:")
                        for comment in comments:
                            content_parts.append(f"\n**{comment.user.login}**: {comment.body}")
                    
                    if review_comments:
                        content_parts.append("\n## Review Comments:")
                        for comment in review_comments:
                            content_parts.append(f"\n**{comment.user.login}** on {comment.path}: {comment.body}")
                    
                    content = '\n'.join(content_parts)
                    
                    # Get all participants
                    participants = [pr.user.login]
                    participants.extend([c.user.login for c in comments if c.user])
                    participants.extend([c.user.login for c in review_comments if c.user])
                    contributors = list(set(participants))
                    
                    yield {
                        "id": f"{repo.full_name}/pr/{pr.number}",
                        "title": f"PR #{pr.number}: {pr.title}",
                        "raw_content": content,
                        "content_type": "text",
                        "file_type": "markdown",
                        "url": pr.html_url,
                        "created_at": int(pr.created_at.timestamp()),
                        "modified_at": int(pr.updated_at.timestamp()),
                        "owner": pr.user.login,
                        "contributors": contributors,
                        "permissions": {
                            "public": not repo.private,
                            "teams": [],
                            "users": [],
                            "sensitivity": "internal" if repo.private else "public",
                            "offshore_restricted": False,
                            "third_party_restricted": False,
                        },
                        "metadata": {
                            "repo": repo.full_name,
                            "type": "pull_request",
                            "number": pr.number,
                            "state": pr.state,
                            "merged": pr.merged,
                            "comments_count": pr.comments,
                            "review_comments_count": pr.review_comments,
                            "changed_files": pr.changed_files,
                        }
                    }
                
                except Exception as e:
                    logger.error(f"Error processing PR #{pr.number}: {e}")
                    continue
            
            # 3. Index issues
            issues = await self.get_issues(repo, since=since)
            for issue in issues:
                try:
                    # Combine issue description with comments
                    comments = list(issue.get_comments())
                    
                    content_parts = [f"# Issue: {issue.title}", f"\n{issue.body or ''}"]
                    
                    if comments:
                        content_parts.append("\n## Discussion:")
                        for comment in comments:
                            content_parts.append(f"\n**{comment.user.login}**: {comment.body}")
                    
                    content = '\n'.join(content_parts)
                    
                    # Get all participants
                    participants = [issue.user.login]
                    participants.extend([c.user.login for c in comments if c.user])
                    contributors = list(set(participants))
                    
                    yield {
                        "id": f"{repo.full_name}/issue/{issue.number}",
                        "title": f"Issue #{issue.number}: {issue.title}",
                        "raw_content": content,
                        "content_type": "text",
                        "file_type": "markdown",
                        "url": issue.html_url,
                        "created_at": int(issue.created_at.timestamp()),
                        "modified_at": int(issue.updated_at.timestamp()),
                        "owner": issue.user.login,
                        "contributors": contributors,
                        "permissions": {
                            "public": not repo.private,
                            "teams": [],
                            "users": [],
                            "sensitivity": "internal" if repo.private else "public",
                            "offshore_restricted": False,
                            "third_party_restricted": False,
                        },
                        "metadata": {
                            "repo": repo.full_name,
                            "type": "issue",
                            "number": issue.number,
                            "state": issue.state,
                            "comments_count": issue.comments,
                            "labels": [label.name for label in issue.labels],
                        }
                    }
                
                except Exception as e:
                    logger.error(f"Error processing issue #{issue.number}: {e}")
                    continue
    
    def detect_language(self, filename: str, content: str = "") -> str:
        """
        Detect programming language from file extension and content.
        
        Args:
            filename: File name with extension
            content: File content (optional, for better detection)
        
        Returns:
            str: Detected language
        """
        ext = self._get_file_extension(filename)
        
        # Try extension mapping first
        if ext in self.LANGUAGE_MAP:
            return self.LANGUAGE_MAP[ext]
        
        # Fallback to content-based detection for shebang
        if content:
            first_line = content.split('\n')[0].lower()
            if first_line.startswith('#!'):
                if 'python' in first_line:
                    return 'python'
                elif 'bash' in first_line or 'sh' in first_line:
                    return 'bash'
                elif 'node' in first_line:
                    return 'javascript'
        
        return 'text'
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension including dot"""
        parts = filename.rsplit('.', 1)
        if len(parts) == 2:
            return f".{parts[1].lower()}"
        return ""
    
    def calculate_contribution_score(self, item: dict) -> float:
        """
        Calculate contribution score based on item type and metadata.
        
        Args:
            item: Content item
        
        Returns:
            float: Contribution score
        """
        metadata = item.get("metadata", {})
        item_type = metadata.get("type", "file")
        
        scores = {
            "file": 2.0,  # Code commits
            "pull_request": 1.5 if metadata.get("merged") else 1.0,
            "issue": 0.5,
        }
        
        return scores.get(item_type, 1.0)
    
    def get_action_type(self, item: dict) -> str:
        """
        Get action type for expertise tracking.
        
        Args:
            item: Content item
        
        Returns:
            str: Action type
        """
        metadata = item.get("metadata", {})
        item_type = metadata.get("type", "file")
        
        actions = {
            "file": "committed",
            "pull_request": "pull_request",
            "issue": "issue_discussion",
        }
        
        return actions.get(item_type, "authored")
    
    async def watch_for_changes(self):
        """
        Set up webhook for real-time GitHub updates.
        
        Note: This requires webhook setup on GitHub and a web server endpoint.
        For now, this is a placeholder for the webhook handler logic.
        """
        logger.info("GitHub webhook watching not yet implemented")
        logger.info("To enable real-time updates:")
        logger.info("1. Set up webhook on GitHub repo settings")
        logger.info("2. Configure webhook URL to point to EngineIQ API")
        logger.info("3. Subscribe to: push, pull_request, issues events")
        logger.info("4. Implement webhook receiver endpoint")
        
        # In production, this would set up webhook handlers
        # For now, use polling with sync() method
