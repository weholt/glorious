# AI Skill - Internal Documentation

## Purpose

The AI skill provides LLM integration with embeddings and semantic search capabilities for the agent system.

## Features

- **LLM Completions**: Generate text using OpenAI or Anthropic models
- **Embeddings**: Create vector embeddings for semantic understanding
- **Semantic Search**: Find similar content using vector similarity
- **History Tracking**: Track all completions and embeddings

## API Keys Required

Set environment variables:
- `OPENAI_API_KEY` - For OpenAI models
- `ANTHROPIC_API_KEY` - For Anthropic models

## Database Schema

### ai_completions
Stores LLM completion history with tokens used.

### ai_embeddings
Stores embeddings with content and metadata.

## Usage in Code

```python
from glorious_ai.skill import complete, embed, semantic_search

# Generate completion
result = complete("Explain quantum computing", model="gpt-4")

# Create embedding
embedding = embed("Some content to embed")

# Semantic search
results = semantic_search("quantum physics", top_k=5)
```

## Providers

- **OpenAI**: GPT-4, GPT-3.5-turbo, text-embedding-ada-002
- **Anthropic**: Claude models
