"""Comment management commands."""

import json
import logging

import typer

logger = logging.getLogger(__name__)

app = typer.Typer(name="comments", help="Manage issue comments")

__all__ = ["app", "add", "list_comments", "delete"]


@app.command(name="add")
def add(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    text: str = typer.Argument(..., help="Comment text"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Add a comment to an issue."""
    from issue_tracker.cli.app import get_issue_service

    try:
        logger.debug("CLI: add comment command: issue_id=%s", issue_id)
        service = get_issue_service()

        # Add comment through service
        logger.debug("CLI: adding comment to issue: id=%s", issue_id)
        comment = service.add_comment(
            issue_id=issue_id,
            text=text,
            author=None,  # Could be set from config/env
        )

        # Convert Comment entity to dict
        comment_data = {
            "id": comment.id,
            "issue_id": comment.issue_id,
            "text": comment.text,
            "author": comment.author,
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
            "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
        }

        logger.info("CLI: comment added: id=%s, issue_id=%s", comment.id, issue_id)
        if not json_output:
            typer.echo(f"Added comment to {issue_id}")
        else:
            typer.echo(json.dumps(comment_data))
    except typer.Exit:
        raise
    except Exception as e:
        logger.error("CLI: error adding comment: %s", str(e))
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="list")
def list_comments(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List comments on an issue."""
    from issue_tracker.cli.app import get_issue_service

    try:
        logger.debug("CLI: list comments command: issue_id=%s", issue_id)
        service = get_issue_service()

        # Get comments through service
        logger.debug("CLI: fetching comments for issue: id=%s", issue_id)
        comments_list = service.list_comments(issue_id)

        # Convert Comment entities to dicts
        comments = [
            {
                "id": comment.id,
                "issue_id": comment.issue_id,
                "text": comment.text,
                "author": comment.author,
                "created_at": comment.created_at.isoformat() if comment.created_at else None,
                "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
            }
            for comment in comments_list
        ]

        logger.debug("CLI: found %d comments for issue: id=%s", len(comments), issue_id)
        if json_output:
            typer.echo(json.dumps(comments))
        else:
            if not comments:
                typer.echo(f"No comments on {issue_id}")
            else:
                for i, comment in enumerate(comments, 1):
                    typer.echo(f"[{i}] {comment['id']}: {comment['text']}")
    except typer.Exit:
        raise
    except Exception as e:
        logger.error("CLI: error listing comments: %s", str(e))
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="delete")
def delete(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    comment_index: int = typer.Argument(..., help="Comment index (1-based)"),
    force: bool = typer.Option(False, "--force", help="Force delete without confirmation"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Delete a comment."""
    from issue_tracker.cli.app import get_issue_service

    try:
        logger.debug("CLI: delete comment command: issue_id=%s, comment_index=%d", issue_id, comment_index)
        service = get_issue_service()

        if not force:
            logger.warning("CLI: delete comment attempted without --force flag")
            typer.echo("Error: --force flag required for deletion", err=True)
            raise typer.Exit(1)

        # Get comments to find the one to delete
        logger.debug("CLI: fetching comments for deletion: issue_id=%s", issue_id)
        comments_list = service.list_comments(issue_id)

        if not comments_list:
            logger.warning("CLI: no comments found for issue: id=%s", issue_id)
            typer.echo(f"Error: No comments on issue {issue_id}", err=True)
            raise typer.Exit(1)

        # Validate index
        if comment_index < 1 or comment_index > len(comments_list):
            logger.warning(
                "CLI: invalid comment index: issue_id=%s, index=%d, count=%d",
                issue_id,
                comment_index,
                len(comments_list),
            )
            typer.echo(f"Error: Invalid comment index {comment_index}. Valid range: 1-{len(comments_list)}", err=True)
            raise typer.Exit(1)

        # Get the comment ID (convert to 0-based index)
        comment_to_delete = comments_list[comment_index - 1]
        comment_id = comment_to_delete.id

        # Delete through service
        logger.debug("CLI: deleting comment: id=%s, issue_id=%s", comment_id, issue_id)
        service.delete_comment(comment_id)

        logger.info("CLI: comment deleted: id=%s, issue_id=%s", comment_id, issue_id)
        if not json_output:
            typer.echo(f"Deleted comment {comment_id} from {issue_id}")
        else:
            typer.echo(json.dumps({"id": comment_id, "issue_id": issue_id, "deleted": True}))
    except typer.Exit:
        raise
    except Exception as e:
        logger.error("CLI: error deleting comment: %s", str(e))
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
