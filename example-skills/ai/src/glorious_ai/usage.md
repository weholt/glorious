# AI Skill Usage

Generate LLM completions, create embeddings, and perform semantic search.

## Commands

### complete
Generate LLM completion from a prompt:
```bash
agent ai complete "Explain quantum computing"
agent ai complete "Write a poem" --model gpt-4 --provider openai
agent ai complete "Analyze this code" --max-tokens 2000
```

### embed
Generate embeddings for content:
```bash
agent ai embed "Some text to embed"
agent ai embed "Document content" --model text-embedding-ada-002
```

### search
Semantic search using embeddings:
```bash
agent ai search "quantum physics" --top-k 5
agent ai search "machine learning" --model text-embedding-ada-002
```

### history
View completion history:
```bash
agent ai history --limit 20
agent ai history --json
```

## Environment Setup

Set API keys:
```bash
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
```

## JSON Output

All commands support `--json` flag for programmatic use:
```bash
agent ai complete "Hello" --json
agent ai search "test" --json
```
