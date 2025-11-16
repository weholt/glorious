"""Code-atlas skill for Glorious Agents."""

from code_atlas.cli import app

# Export the existing Typer app
# Glorious will load this automatically

__all__ = ["app", "search"]


def search(query: str, limit: int = 10) -> list["SearchResult"]:
    """Universal search API for code atlas.
    
    Searches across classes, functions, and file names.
    
    Args:
        query: Search query string
        limit: Maximum number of results
        
    Returns:
        List of SearchResult objects
    """
    from glorious_agents.core.search import SearchResult
    from code_atlas.query import CodeIndex
    from pathlib import Path
    
    # Load code index
    index_path = Path.cwd() / "code_index.json"
    if not index_path.exists():
        return []
    
    try:
        index = CodeIndex(index_path)
    except Exception:
        return []
    
    results = []
    query_lower = query.lower()
    
    # Search through all entities
    for file_data in index.data.get("files", []):
        file_path = file_data["path"]
        
        # Check if file name matches
        if query_lower in file_path.lower():
            results.append(SearchResult(
                skill="atlas",
                id=file_path,
                type="file",
                content=f"File: {file_path}",
                metadata={"lines": file_data.get("lines", 0)},
                score=0.6
            ))
        
        # Search entities (classes, functions)
        for entity in file_data.get("entities", []):
            score = 0.0
            matched = False
            
            # Name exact match
            if query_lower == entity["name"].lower():
                score = 1.0
                matched = True
            # Name contains query
            elif query_lower in entity["name"].lower():
                score = 0.8
                matched = True
            # Docstring match
            elif entity.get("docstring") and query_lower in entity["docstring"].lower():
                score = 0.5
                matched = True
            
            if matched:
                results.append(SearchResult(
                    skill="atlas",
                    id=f"{file_path}:{entity['name']}",
                    type=entity["type"],
                    content=f"{entity['type']}: {entity['name']} in {file_path}",
                    metadata={
                        "lineno": entity.get("lineno"),
                        "docstring": entity.get("docstring", "")[:100],
                    },
                    score=score
                ))
    
    # Sort by score and limit
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]
