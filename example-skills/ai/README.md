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

# Generate completion
agent ai complete "Explain AI agents"

# Create embeddings
agent ai embed "Some content"

# Semantic search
agent ai search "agent frameworks"

# View history
agent ai history
```

## Requirements

- Python 3.11+
- OpenAI API key (for OpenAI models)
- Anthropic API key (for Claude models)

## Models

### OpenAI
- gpt-4, gpt-3.5-turbo (completions)
- text-embedding-ada-002 (embeddings)

### Anthropic
- claude-3-opus, claude-3-sonnet (completions)

## License

MIT
