"""Repository for prompts data access."""

from sqlmodel import select

from glorious_agents.core.repository import BaseRepository

from .models import Prompt


class PromptsRepository(BaseRepository[Prompt]):
    """Repository for prompts with domain-specific queries."""

    def get_latest_version(self, name: str) -> Prompt | None:
        """Get the latest version of a prompt by name.

        Args:
            name: Prompt name

        Returns:
            Latest prompt version or None if not found
        """
        statement = (
            select(Prompt).where(Prompt.name == name).order_by(Prompt.version.desc()).limit(1)
        )
        return self.session.exec(statement).first()

    def get_max_version(self, name: str) -> int:
        """Get the maximum version number for a prompt name.

        Args:
            name: Prompt name

        Returns:
            Maximum version number or 0 if no versions exist
        """
        statement = (
            select(Prompt.version)
            .where(Prompt.name == name)
            .order_by(Prompt.version.desc())
            .limit(1)
        )
        result = self.session.exec(statement).first()
        return result if result is not None else 0

    def get_all_versions(self, name: str) -> list[Prompt]:
        """Get all versions of a prompt.

        Args:
            name: Prompt name

        Returns:
            List of all prompt versions ordered by version desc
        """
        statement = select(Prompt).where(Prompt.name == name).order_by(Prompt.version.desc())
        return list(self.session.exec(statement))

    def get_by_name_version(self, name: str, version: int) -> Prompt | None:
        """Get a specific version of a prompt.

        Args:
            name: Prompt name
            version: Version number

        Returns:
            Prompt or None if not found
        """
        statement = select(Prompt).where(
            Prompt.name == name,
            Prompt.version == version,
        )
        return self.session.exec(statement).first()

    def list_prompt_names(self) -> list[dict[str, int]]:
        """List all unique prompt names with their version counts.

        Returns:
            List of dicts with name, latest_version, and total_versions
        """
        # Use raw SQL for GROUP BY since SQLModel doesn't handle it well
        sql = """
            SELECT name, MAX(version) as latest_version, COUNT(*) as total_versions
            FROM prompts
            GROUP BY name
            ORDER BY name
        """
        result = self.session.exec(sql)

        names = []
        for row in result:
            names.append(
                {
                    "name": row[0],
                    "latest_version": row[1],
                    "total_versions": row[2],
                }
            )

        return names

    def search_prompts(self, query: str, limit: int = 10) -> list[Prompt]:
        """Search prompts by name or template content.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching prompts ordered by creation date
        """
        query_pattern = f"%{query.lower()}%"
        statement = (
            select(Prompt)
            .where((Prompt.name.like(query_pattern)) | (Prompt.template.like(query_pattern)))
            .order_by(Prompt.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def delete_by_name(self, name: str) -> int:
        """Delete all versions of a prompt by name.

        Args:
            name: Prompt name

        Returns:
            Number of deleted prompts
        """
        prompts = self.get_all_versions(name)
        count = len(prompts)
        for prompt in prompts:
            if prompt.id:
                self.delete(prompt.id)
        return count
