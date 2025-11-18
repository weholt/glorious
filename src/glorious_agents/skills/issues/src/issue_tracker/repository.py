"""Repository layer wrapper for issues skill.

Provides unified access to existing domain repositories while maintaining
the new framework's interface conventions.
"""

from issue_tracker.adapters.db.repositories import (
    CommentRepository,
    IssueGraphRepository,
    IssueRepository,
)

# Re-export existing repositories for framework compatibility
__all__ = [
    "IssueRepository",
    "CommentRepository",
    "IssueGraphRepository",
]
