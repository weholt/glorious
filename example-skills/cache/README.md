# Cache Skill

Short-term ephemeral storage with TTL (time-to-live) support for Glorious Agents.

## Features

- Store and retrieve cached values with optional TTL
- Support for different cache kinds (ast, symbols, deps, embeddings, search results)
- Warmup cache with project-specific data
- Prune expired entries
- Key patterns for organized storage

## Usage

```bash
# Set a cache value with TTL
agent cache set my-key "my-value" --ttl 3600

# Get a cache value
agent cache get my-key

# Warmup cache for a project
agent cache warmup --project-id myproject --kinds ast,symbols,deps

# Prune expired entries
agent cache prune --expired-only

# List all cache entries
agent cache list
```

## Schema

The skill uses a SQLite table with the following structure:

- `key`: Unique cache key
- `value`: Stored value (BLOB for flexibility)
- `kind`: Cache type (ast, symbols, deps, etc.)
- `created_at`: Timestamp
- `ttl_seconds`: Time-to-live in seconds
- `meta`: JSON metadata
