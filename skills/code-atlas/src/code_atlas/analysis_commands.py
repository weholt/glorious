"""Analysis commands for CodeAtlas (rank, check, agent)."""

import json
from pathlib import Path

import typer

from code_atlas.agent_adapter import AgentAdapter
from code_atlas.query import CodeIndex
from code_atlas.rules import RuleEngine
from code_atlas.scoring import ScoringEngine


def rank(
    rules: str = typer.Option("rules.yaml", help="Rules configuration file"),
    top: int = typer.Option(20, help="Number of top results to show"),
    index_file: str = typer.Option("code_index.json", help="Code index file"),
    output: str = typer.Option("refactor_rank.json", help="Output file"),
) -> None:
    """Rank files by refactor priority."""
    # Load code index
    code_index = CodeIndex(index_file)

    # Create scoring engine
    scoring_engine = ScoringEngine(rules)

    # Rank files
    rankings = scoring_engine.rank(code_index.data)

    # Write top N to output file
    top_rankings = rankings[:top]
    Path(output).write_text(json.dumps(top_rankings, indent=2), encoding="utf-8")

    typer.echo(f"\nTop {len(top_rankings)} refactor priorities:")
    for i, item in enumerate(top_rankings, 1):
        typer.echo(
            f"{i}. {item['file']} - Score: {item['score']:.3f} "
            f"(complexity: {item['complexity']:.1f}, LOC: {item['loc']})"
        )

    typer.echo(f"\nFull rankings written to {output}")


def check(
    rules: str = typer.Option("rules.yaml", help="Rules configuration file"),
    index_file: str = typer.Option("code_index.json", help="Code index file"),
    output: str = typer.Option("violations.json", help="Output file"),
) -> None:
    """Check code against quality rules."""
    # Load code index
    code_index = CodeIndex(index_file)

    # Create rule engine
    rule_engine = RuleEngine(rules)

    # Evaluate all files
    all_violations = []
    for file_data in code_index.data.get("files", []):
        violations = rule_engine.evaluate(file_data)
        all_violations.extend(violations)

    # Write to output file
    Path(output).write_text(json.dumps(all_violations, indent=2), encoding="utf-8")

    typer.echo(f"\nFound {len(all_violations)} rule violations")

    if all_violations:
        typer.echo("\nSample violations:")
        for violation in all_violations[:5]:
            typer.echo(f"  [{violation['id']}] {violation['file']}: {violation['message']}")

    typer.echo(f"\nAll violations written to {output}")


def agent(
    index_file: str = typer.Option("code_index.json", help="Code index file"),
    rules: str = typer.Option("rules.yaml", help="Rules configuration file"),
    summary: bool = typer.Option(False, "--summary", help="Show codebase summary"),
    symbol: str = typer.Option(None, help="Find symbol location"),
    top: int = typer.Option(0, help="Show top N refactor priorities"),
    complex_threshold: int = typer.Option(0, help="Find functions above complexity threshold"),
    hotspots: int = typer.Option(0, help="Find dependency hotspots (min edges)"),
    poor_docs: float = typer.Option(0.0, help="Find files below comment ratio threshold"),
) -> None:
    """Query codebase for agent integration (outputs JSON)."""
    # Initialize adapter
    adapter = AgentAdapter(Path.cwd(), index_file, rules)

    result = {}

    # Handle different query modes
    if summary:
        result = adapter.summarize_state()
    elif symbol:
        symbol_result = adapter.get_symbol_location(symbol)
        if symbol_result is None:
            typer.echo(json.dumps({"error": f"Symbol '{symbol}' not found"}, indent=2))
            raise typer.Exit(1)
        result = symbol_result
    elif top > 0:
        result = {"refactor_priorities": adapter.get_top_refactors(limit=top)}
    elif complex_threshold > 0:
        result = {"complex_functions": adapter.get_complex_functions(threshold=complex_threshold)}
    elif hotspots > 0:
        result = {"dependency_hotspots": adapter.get_dependency_hotspots(min_edges=hotspots)}
    elif poor_docs > 0:
        result = {"poor_documentation": adapter.get_untyped_or_poor_docs(min_comment_ratio=poor_docs)}
    else:
        # Default: return summary + violations
        result = {
            "summary": adapter.summarize_state(),
            "violations": adapter.get_rule_violations(),
        }

    # Output JSON for subprocess consumption
    typer.echo(json.dumps(result, indent=2))
