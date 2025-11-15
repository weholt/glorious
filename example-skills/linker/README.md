# Linker Skill

Semantic cross-references between issues, notes, files, and other entities.

## Features

- Create bidirectional links between entities
- Auto-discover links from issue bodies and notes
- Build context bundles for related items
- Query by entity or link type

## Usage

```bash
# Add a manual link
agent linker add --kind issue->note --a issue:#42 --b note:123

# Rebuild links from existing data
agent linker rebuild --project-id myproject

# Get context bundle for an issue
agent linker context issue:#42

# List all links
agent linker list
```
