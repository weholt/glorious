#!/usr/bin/env python3
"""Migrate legacy markdown issues to glorious-skill-issues JSONL format."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("Error: PyYAML not installed. Run: pip install pyyaml")
    exit(1)


def parse_markdown_issue(content: str, priority_override: int = None) -> dict[str, Any] | None:
    """Parse YAML frontmatter and markdown content."""
    # Split frontmatter and content
    parts = content.split('---', 2)
    if len(parts) < 3:
        return None
    
    try:
        frontmatter = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        print(f"Warning: YAML parse error: {e}")
        return None
    
    if not frontmatter or not isinstance(frontmatter, dict):
        return None
    
    markdown_content = parts[2].strip()
    
    # Map status
    status = map_status(frontmatter.get('status', 'proposed'))
    
    # Get priority (use override if provided, otherwise from frontmatter)
    if priority_override:
        priority = priority_override
    else:
        priority_str = frontmatter.get('priority', 'medium')
        priority = map_priority_to_int(priority_str)
    
    # Handle tags - can be list or comma-separated string
    tags = frontmatter.get('tags', [])
    if isinstance(tags, list):
        tags_list = [str(t) for t in tags]
    else:
        tags_list = [str(tags)] if tags else []
    
    # Map issue type
    issue_type = str(frontmatter.get('type', 'enhancement'))
    type_mapping = {
        'bug': 'bug',
        'enhancement': 'enhancement',
        'feature': 'feature',
        'architectural-violation': 'task',
        'security': 'bug',
        'duplication': 'task',
        'cleanup': 'task',
        'code-duplication': 'task',
    }
    mapped_type = type_mapping.get(issue_type.lower(), 'task')
    
    # Generate issue ID from external_id
    external_id = str(frontmatter.get('id', ''))
    if external_id:
        issue_id = external_id.lower().replace('_', '-')
    else:
        issue_id = f"issue-{datetime.now().timestamp()}"
    
    # Combine description and content
    full_description = str(frontmatter.get('description', ''))
    if markdown_content:
        full_description += '\n\n' + markdown_content
    
    # Format dates
    created_at = frontmatter.get('created', '')
    if created_at and 'T' not in str(created_at):
        created_at = f"{created_at}T00:00:00"
    else:
        created_at = datetime.now().isoformat()
    
    updated_at = frontmatter.get('updated', created_at)
    if updated_at and 'T' not in str(updated_at):
        updated_at = f"{updated_at}T00:00:00"
    
    # Add metadata to labels for preservation
    if external_id:
        tags_list.append(f"ext_id:{external_id}")
    section = str(frontmatter.get('section', ''))
    if section:
        tags_list.append(f"section:{section}")
    
    return {
        'id': issue_id,
        'title': str(frontmatter.get('title', 'Untitled'))[:500],  # Truncate to 500 chars
        'description': full_description,
        'type': mapped_type,
        'priority': priority,
        'status': status,
        'assignee': None,
        'epic_id': None,
        'labels': tags_list,
        'created_at': created_at,
        'updated_at': updated_at,
        'closed_at': None,
        'project_id': 'default',
    }


def map_status(old_status: str) -> str:
    """Map legacy status to new schema."""
    if not old_status:
        return 'open'
    
    mapping = {
        'proposed': 'open',
        'in progress': 'in_progress',
        'in_progress': 'in_progress',
        'completed': 'closed',
        "won't fix": 'closed',
        'wont fix': 'closed',
        'blocked': 'blocked',
        'recommended': 'open',
        'shortlisted': 'open',
    }
    return mapping.get(old_status.lower(), 'open')


def map_priority_from_file(filename: str) -> int:
    """Extract priority from filename and map to integer (1=low, 2=medium, 3=high, 4=critical)."""
    filename_lower = filename.lower()
    if 'critical' in filename_lower:
        return 4
    elif 'high' in filename_lower:
        return 3
    elif 'medium' in filename_lower:
        return 2
    elif 'low' in filename_lower:
        return 1
    return 2  # default to medium


def map_priority_to_int(priority_str: str) -> int:
    """Map priority string to integer (1=low, 2=medium, 3=high, 4=critical)."""
    mapping = {
        'low': 1,
        'medium': 2,
        'high': 3,
        'critical': 4,
    }
    return mapping.get(priority_str.lower(), 2)


def migrate_issues_from_markdown(issues_dir: Path, output_file: Path, dry_run: bool = True):
    """Migrate all markdown issues to JSONL."""
    issues = []
    skipped = []
    
    # Files to skip
    skip_files = {'history.md', 'README.md'}
    
    for md_file in sorted(issues_dir.glob('*.md')):
        if md_file.name in skip_files:
            print(f"Skipping {md_file.name}")
            continue
        
        print(f"Processing {md_file.name}...")
        priority_from_file = map_priority_from_file(md_file.name)
        
        with open(md_file, encoding='utf-8') as f:
            content = f.read()
        
        # Split on issue boundaries (---)
        # Match lines with just --- possibly with whitespace
        issue_blocks = re.split(r'\n---\s*\n', content)
        
        for i, block in enumerate(issue_blocks):
            block = block.strip()
            if not block or block.startswith('#'):
                continue
            
            # Check if this looks like an issue (has id: in it)
            if 'id:' not in block and 'title:' not in block:
                continue
            
            # Add back the --- delimiters for parsing
            issue_text = f'---\n{block}\n---'
            issue = parse_markdown_issue(issue_text, priority_from_file)
            
            if issue and issue.get('id'):
                issues.append(issue)
            else:
                if block[:50]:  # Only show first 50 chars
                    skipped.append(f"{md_file.name}:block_{i}")
    
    # Write JSONL
    with open(output_file, 'w', encoding='utf-8') as f:
        for issue in issues:
            f.write(json.dumps(issue, ensure_ascii=False) + '\n')
    
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Migrated {len(issues)} issues to {output_file}")
    
    if skipped:
        print(f"Skipped {len(skipped)} blocks (no valid issue data)")
    
    # Statistics
    by_priority = {}
    by_type = {}
    by_status = {}
    
    for issue in issues:
        p = issue.get('priority', 'unknown')
        t = issue.get('issue_type', 'unknown')
        s = issue.get('status', 'unknown')
        
        by_priority[p] = by_priority.get(p, 0) + 1
        by_type[t] = by_type.get(t, 0) + 1
        by_status[s] = by_status.get(s, 0) + 1
    
    print("\nStatistics:")
    print(f"  By Priority: {by_priority}")
    print(f"  By Type: {by_type}")
    print(f"  By Status: {by_status}")
    
    return issues


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Migrate markdown issues to glorious-skill-issues JSONL format'
    )
    parser.add_argument(
        '--issues-dir',
        type=Path,
        default=Path('.work/agent/issues'),
        help='Path to issues directory (default: .work/agent/issues)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('.work/agent/issues_migration.jsonl'),
        help='Output JSONL file (default: .work/agent/issues_migration.jsonl)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate without creating output file'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute migration (creates output file)'
    )
    
    args = parser.parse_args()
    
    if not args.issues_dir.exists():
        print(f"Error: Issues directory not found: {args.issues_dir}")
        return 1
    
    if not args.dry_run and not args.execute:
        print("Note: Running in dry-run mode. Use --execute to create output file.")
        args.dry_run = True
    
    print(f"Migration started at {datetime.now()}")
    print(f"Source: {args.issues_dir}")
    print(f"Output: {args.output}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'EXECUTE'}\n")
    
    issues = migrate_issues_from_markdown(args.issues_dir, args.output, dry_run=args.dry_run)
    
    if not args.dry_run and args.execute and issues:
        print("\n✓ Migration complete!")
        print(f"✓ Created: {args.output}")
        print("\nNext steps:")
        print(f"  1. Review the output file: less {args.output}")
        print("  2. Initialize issues skill if needed: agent issues init")
        print(f"  3. Import issues: agent issues import {args.output}")
        print("  4. Validate: agent issues stats")
    
    return 0


if __name__ == '__main__':
    exit(main())
