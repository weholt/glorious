# Glorious AI Skill

LLM integration with embeddings and semantic search for the Glorious Agents framework.

## Features

- **Multi-Provider LLM Support**: OpenAI and Anthropic
- **Embeddings**: Generate and store vector embeddings
- **Semantic Search**: Find similar content using cosine similarity
- **History Tracking**: Track all completions with token usage

## Installation

```bash
cd example-skills/ai
uv pip install -e .
```

## Quick Start

```bash
# Set API keys
export OPENAI_API_KEY="your-key"
# Or for Anthropic
export ANTHROPIC_API_KEY="your-key"

# Generate completion
uv run agent ai complete "Explain AI agents"

# With Anthropic/Claude
uv run agent ai complete "Explain AI agents" --provider anthropic --model claude-3-sonnet-20240229

# Create embeddings
uv run agent ai embed "Some content"

# Semantic search (finds similar embedded content)
uv run agent ai semantic "agent frameworks"

# View history
uv run agent ai history
```

## Universal Search Integration

The AI skill integrates with the universal search system:

```bash
# Search across all skills (includes AI completions)
uv run agent search "LLM integration"
```

The `search()` function searches AI completion prompts and responses.

## Requirements

- Python 3.11+
- OpenAI API key (for OpenAI models)
- Anthropic API key (for Claude models)

## Commands

### `agent ai complete`
Generate LLM completions with OpenAI or Anthropic models.

**Options:**
- `--model, -m`: Model name (default: gpt-4)
- `--provider, -p`: Provider (openai/anthropic, default: openai)
- `--max-tokens, -t`: Maximum tokens (default: 1000)
- `--json`: Output as JSON

**Examples:**
```bash
# OpenAI GPT-4
uv run agent ai complete "What is an agentic workflow?"

# Anthropic Claude
uv run agent ai complete "Explain embeddings" --provider anthropic --model claude-3-sonnet-20240229

# JSON output
uv run agent ai complete "Hello" --json
```

### `agent ai embed`
Generate vector embeddings for content using OpenAI's embedding models.

**Options:**
- `--model, -m`: Embedding model (default: text-embedding-ada-002)
- `--json`: Output as JSON

**Examples:**
```bash
# Generate embedding
uv run agent ai embed "Documentation about AI agents"

# JSON output with full vector
uv run agent ai embed "Some text" --json
```

### `agent ai semantic`
Semantic search across embedded content using cosine similarity.

**Options:**
- `--model, -m`: Embedding model (default: text-embedding-ada-002)
- `--top-k, -k`: Number of results (default: 5)
- `--json`: Output as JSON

**Examples:**
```bash
# Find similar content
uv run agent ai semantic "agent architecture"

# Top 10 results
uv run agent ai semantic "LLM integration" --top-k 10
```

### `agent ai history`
View completion history with token usage.

**Options:**
- `--limit, -l`: Number of records (default: 10)
- `--json`: Output as JSON

**Examples:**
```bash
# Recent completions
uv run agent ai history

# Last 20
uv run agent ai history --limit 20
```

## Models

### OpenAI
- **Completions**: gpt-4, gpt-4-turbo, gpt-3.5-turbo
- **Embeddings**: text-embedding-ada-002, text-embedding-3-small, text-embedding-3-large

### Anthropic
- **Completions**: claude-3-opus-20240229, claude-3-sonnet-20240229, claude-3-haiku-20240307

## License

MIT
