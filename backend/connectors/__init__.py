"""
EngineIQ Connectors

Data source connectors for indexing content into EngineIQ.
"""

from .base_connector import BaseConnector
from .slack_connector import SlackConnector
from .github_connector import GitHubConnector

# Try to import BoxConnector (requires boxsdk)
try:
    from .box_connector import BoxConnector
    __all__ = ["BaseConnector", "SlackConnector", "GitHubConnector", "BoxConnector"]
except ImportError:
    __all__ = ["BaseConnector", "SlackConnector", "GitHubConnector"]
