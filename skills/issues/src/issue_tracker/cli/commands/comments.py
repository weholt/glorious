"""Comment management commands."""

import json

import typer

app = typer.Typer(name="comments", help="Manage issue comments")


@app.command(name="add")
def add(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    text: str = typer.Argument(..., help="Comment text"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Add a comment to an issue."""
    from issue_tracker.cli.app import get_issue_service

    try:
        service = get_issue_service()

        # Add comment through service
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

        if not json_output:
            typer.echo(f"Added comment to {issue_id}")
        else:
            typer.echo(json.dumps(comment_data))
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="list")
def list_comments(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List comments on an issue."""
    from issue_tracker.cli.app import get_issue_service

    try:
        service = get_issue_service()

        # Get comments through service
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
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command(name="delete")
def delete(
    issue_id: str = typer.Argument(..., help="Issue ID"),
    comment_index: int = typer.Argument(..., help="Comment index (1-based)"),
    force: bool = typer.Option(False, "--force", help="Force delete without confirmation"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Delete a comment."""
    from issue_tracker.cli.app import get_issue_service

    try:
        service = get_issue_service()

        if not force:
            typer.echo("Error: --force flag required for deletion", err=True)
            raise typer.Exit(1)

        # Get comments to find the one to delete
        comments_list = service.list_comments(issue_id)

        if not comments_list:
            typer.echo(f"Error: No comments on issue {issue_id}", err=True)
            raise typer.Exit(1)

        # Validate index
        if comment_index < 1 or comment_index > len(comments_list):
            typer.echo(f"Error: Invalid comment index {comment_index}. Valid range: 1-{len(comments_list)}", err=True)
            raise typer.Exit(1)

        # Get the comment ID (convert to 0-based index)
        comment_to_delete = comments_list[comment_index - 1]
        comment_id = comment_to_delete.id

        # Delete through service
        service.delete_comment(comment_id)

        if not json_output:
            typer.echo(f"Deleted comment {comment_id} from {issue_id}")
        else:
            typer.echo(json.dumps({"id": comment_id, "issue_id": issue_id, "deleted": True}))
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
