# Housekeeping

- Definitions:
    - **issues** : managed via `uv run issues` command
    - **agent notes** : `.work/agent/notes/` folder

- When the user asks you to do some house-cleaning, that is a keyword for you to:
    - List all open issues using `uv run issues list --status open`
    - Validate the current source code against all open issues
    - Close any completed issues using `uv run issues close ISSUE-ID --reason "Description of fix"`
    - Read all your agent notes, consolidate them, remove outdated, redundant or duplicated information, and create a distilled and optimized version of your notes for easier consumption

- Based on these prompts, create new issues using `uv run issues create`:
  - `.github\prompts\best-practices-check.prompt.md`
  - `.github\prompts\code-analysis.prompt.md`
  - `.github\prompts\pythonic-code.prompt.md`
  - `.github\prompts\task-assesment.prompt.md`

**MANDATORY RULES**
- Use `uv run issues` commands for all issue management
- Do **NOT** create markdown files for tracking issues
- Agent notes should be kept in `.work/agent/notes/` folder only