"""Service layer wrapper for issues skill.

Provides unified access to existing domain services while maintaining
the new framework's interface conventions.
"""

from issue_tracker.services.issue_graph_service import IssueGraphService
from issue_tracker.services.issue_service import IssueService
from issue_tracker.services.issue_stats_service import IssueStatsService
from issue_tracker.services.search_service import SearchService

# Re-export existing services for framework compatibility
__all__ = [
    "IssueService",
    "IssueGraphService",
    "IssueStatsService",
    "SearchService",
]
