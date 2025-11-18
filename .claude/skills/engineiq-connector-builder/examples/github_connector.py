"""
EngineIQ GitHub Connector Example

Complete implementation of a GitHub connector with semantic code understanding.
"""

from typing import AsyncGenerator, Dict, List
from github import Github
from github.GithubException import GithubException
from connectors.base_connector import BaseConnector


class GitHubConnector(BaseConnector):
    """GitHub connector for indexing repos, code files, PRs, and issues"""

    def __init__(self, credentials: dict, gemini_service, qdrant_service):
        super().__init__(credentials, gemini_service, qdrant_service)
        self.client = Github(credentials["access_token"])
        self.org = credentials.get("org")
        self.repos_filter = credentials.get("repos", [])  # Optional: specific repos only

    async def authenticate(self) -> bool:
        """Authenticate with GitHub using access token"""
        try:
            user = self.client.get_user()
            user.login  # Trigger API call
            return True
        except GithubException as e:
            print(f"GitHub authentication failed: {e}")
            return False

    async def get_content(self, since: int = None) -> AsyncGenerator[Dict, None]:
        """
        Fetch content from GitHub:
        - Code files from repositories
        - Pull requests with reviews
        - Issues with comments
        """
        # Get repositories
        if self.org:
            repos = self.client.get_organization(self.org).get_repos()
        else:
            repos = self.client.get_user().get_repos()

        for repo in repos:
            # Filter repos if specified
            if self.repos_filter and repo.name not in self.repos_filter:
                continue

            print(f"Processing repo: {repo.full_name}...")

            # 1. Index code files
            async for file_item in self.get_repo_files(repo):
                yield file_item

            # 2. Index pull requests
            async for pr_item in self.get_pull_requests(repo, since):
                yield pr_item

            # 3. Index issues
            async for issue_item in self.get_issues(repo, since):
                yield issue_item

    async def get_repo_files(self, repo) -> AsyncGenerator[Dict, None]:
        """Get all code files from repository"""
        try:
            contents = repo.get_contents("")

            while contents:
                file_content = contents.pop(0)

                if file_content.type == "dir":
                    # Recursively process directories
                    try:
                        contents.extend(repo.get_contents(file_content.path))
                    except:
                        continue  # Skip inaccessible directories
                else:
                    # Only index code files
                    if self.is_code_file(file_content.name):
                        try:
                            code = file_content.decoded_content.decode('utf-8')

                            # Get contributors (commits for this file)
                            try:
                                commits = repo.get_commits(path=file_content.path)
                                contributors = list(set([c.author.login for c in commits[:10] if c.author]))
                            except:
                                contributors = [repo.owner.login]

                            yield {
                                "id": f"github_{repo.full_name}_{file_content.sha}",
                                "title": f"{repo.name}/{file_content.path}",
                                "raw_content": code,
                                "content_type": "code",
                                "file_type": file_content.name.split(".")[-1],
                                "url": file_content.html_url,
                                "created_at": int(repo.created_at.timestamp()),
                                "modified_at": int(repo.updated_at.timestamp()),
                                "owner": repo.owner.login,
                                "contributors": contributors[:10],  # Limit to 10
                                "permissions": {
                                    "public": not repo.private,
                                    "teams": [],
                                    "users": [],
                                    "sensitivity": "internal" if repo.private else "public",
                                    "offshore_restricted": False,
                                    "third_party_restricted": repo.private
                                },
                                "metadata": {
                                    "github_repo": repo.full_name,
                                    "github_path": file_content.path,
                                    "github_branch": repo.default_branch,
                                    "github_stars": repo.stargazers_count,
                                    "github_language": repo.language
                                }
                            }
                        except Exception as e:
                            # Skip binary files or files that can't be decoded
                            continue

        except Exception as e:
            print(f"Error processing repo {repo.full_name}: {e}")

    async def get_pull_requests(self, repo, since: int = None) -> AsyncGenerator[Dict, None]:
        """Get pull requests with reviews and comments"""
        try:
            prs = repo.get_pulls(state="all", sort="updated", direction="desc")

            for pr in prs:
                # Skip if older than 'since'
                if since and int(pr.updated_at.timestamp()) < since:
                    break

                # Combine PR description + review comments
                full_text = f"# {pr.title}\n\n{pr.body or ''}\n\n## Reviews\n"
                reviewers = [pr.user.login]

                try:
                    for review in pr.get_reviews():
                        if review.body:
                            full_text += f"**{review.user.login}** ({review.state}):\n{review.body}\n\n"
                            reviewers.append(review.user.login)
                except:
                    pass  # Reviews might not be accessible

                # Add comments
                try:
                    comments = pr.get_comments()
                    if comments.totalCount > 0:
                        full_text += "\n## Comments\n"
                        for comment in comments[:20]:  # Limit to 20 comments
                            full_text += f"**{comment.user.login}**: {comment.body}\n\n"
                            reviewers.append(comment.user.login)
                except:
                    pass

                yield {
                    "id": f"github_pr_{repo.full_name}_{pr.number}",
                    "title": f"PR #{pr.number}: {pr.title}",
                    "raw_content": full_text,
                    "content_type": "text",
                    "file_type": "md",
                    "url": pr.html_url,
                    "created_at": int(pr.created_at.timestamp()),
                    "modified_at": int(pr.updated_at.timestamp()),
                    "owner": pr.user.login,
                    "contributors": list(set(reviewers)),
                    "permissions": {
                        "public": not repo.private,
                        "teams": [],
                        "users": [],
                        "sensitivity": "internal",
                        "offshore_restricted": False,
                        "third_party_restricted": False
                    },
                    "metadata": {
                        "github_repo": repo.full_name,
                        "github_pr_number": pr.number,
                        "github_pr_state": pr.state,
                        "github_pr_merged": pr.merged,
                        "github_pr_labels": [label.name for label in pr.labels]
                    }
                }

        except Exception as e:
            print(f"Error fetching PRs from {repo.full_name}: {e}")

    async def get_issues(self, repo, since: int = None) -> AsyncGenerator[Dict, None]:
        """Get issues with comments"""
        try:
            issues = repo.get_issues(state="all", sort="updated", direction="desc")

            for issue in issues:
                # Skip pull requests (they appear in issues too)
                if issue.pull_request:
                    continue

                # Skip if older than 'since'
                if since and int(issue.updated_at.timestamp()) < since:
                    break

                # Combine issue description + comments
                full_text = f"# {issue.title}\n\n{issue.body or ''}\n\n## Comments\n"
                contributors = [issue.user.login]

                try:
                    for comment in issue.get_comments():
                        full_text += f"**{comment.user.login}**: {comment.body}\n\n"
                        contributors.append(comment.user.login)
                except:
                    pass

                yield {
                    "id": f"github_issue_{repo.full_name}_{issue.number}",
                    "title": f"Issue #{issue.number}: {issue.title}",
                    "raw_content": full_text,
                    "content_type": "text",
                    "file_type": "md",
                    "url": issue.html_url,
                    "created_at": int(issue.created_at.timestamp()),
                    "modified_at": int(issue.updated_at.timestamp()),
                    "owner": issue.user.login,
                    "contributors": list(set(contributors)),
                    "permissions": {
                        "public": not repo.private,
                        "teams": [],
                        "users": [],
                        "sensitivity": "internal",
                        "offshore_restricted": False,
                        "third_party_restricted": False
                    },
                    "metadata": {
                        "github_repo": repo.full_name,
                        "github_issue_number": issue.number,
                        "github_issue_state": issue.state,
                        "github_issue_labels": [label.name for label in issue.labels]
                    }
                }

        except Exception as e:
            print(f"Error fetching issues from {repo.full_name}: {e}")

    def is_code_file(self, filename: str) -> bool:
        """Check if file is a code file"""
        code_extensions = [
            "py", "js", "ts", "tsx", "jsx", "java", "go", "rs",
            "cpp", "c", "h", "hpp", "rb", "php", "swift", "kt",
            "scala", "sh", "bash", "sql", "r", "m", "cs", "vb"
        ]
        ext = filename.split(".")[-1].lower()
        return ext in code_extensions

    def get_action_type(self, item: dict) -> str:
        """Determine action type for expertise tracking"""
        if "github_pr" in item["id"]:
            return "reviewed"
        elif "github_issue" in item["id"]:
            return "commented"
        else:  # Code file
            return "authored"

    def calculate_contribution_score(self, item: dict) -> float:
        """Calculate contribution score based on action type"""
        action = self.get_action_type(item)

        scores = {
            "authored": 2.0,  # Writing code is most valuable
            "reviewed": 1.5,  # Reviewing code is valuable
            "commented": 1.0  # Commenting on issues
        }

        return scores.get(action, 1.0)

    async def watch_for_changes(self):
        """
        Set up real-time updates using GitHub webhooks.

        In production, register webhooks for push, pull_request, and issues events.
        For development/testing, use polling.
        """
        import asyncio

        print(f"Starting GitHub change watcher (polling mode)...")

        while True:
            try:
                # Get last sync time
                last_sync = await self.get_last_sync_time()

                # Sync updated content
                await self.sync(since=last_sync)

                # Save current time
                await self.save_last_sync_time(int(asyncio.get_event_loop().time()))

            except Exception as e:
                print(f"Error in GitHub watcher: {e}")

            # Poll every 10 minutes (GitHub has lower rate limits)
            await asyncio.sleep(600)

    async def get_last_sync_time(self) -> int:
        """Get timestamp of last sync"""
        # Implement based on your storage (Redis, DB, etc.)
        return 0

    async def save_last_sync_time(self, timestamp: int):
        """Save timestamp of current sync"""
        # Implement based on your storage
        pass


# Example usage
if __name__ == "__main__":
    import asyncio
    from services.gemini_service import GeminiService
    from services.qdrant_service import QdrantService

    async def main():
        # Initialize services
        gemini = GeminiService(api_key="your_gemini_key")
        qdrant = QdrantService(url="your_qdrant_url", api_key="your_qdrant_key")

        # Initialize connector
        github = GitHubConnector(
            credentials={
                "access_token": "ghp_your_token",
                "org": "your-org",  # Optional
                "repos": ["repo1", "repo2"]  # Optional: specific repos only
            },
            gemini_service=gemini,
            qdrant_service=qdrant
        )

        # Authenticate
        if await github.authenticate():
            print("✓ Authenticated with GitHub")

            # Sync all content
            await github.sync()

            print("✓ Sync complete!")
        else:
            print("✗ Authentication failed")

    asyncio.run(main())
