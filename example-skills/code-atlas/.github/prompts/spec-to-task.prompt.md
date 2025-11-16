# Spec to tasks

## Introduction

Your goal is to take a specified specification and turn into a set of files indicating the priority of the tasks in the implentation.

## Instructions

- Always use Context7 mcp tool to get up to date documentation and information before create the tasks
- Always use Sequential Thinking mcp tool to break the tasks into small, atomic tasks
- Always use requests library to test API endpoints in integrationtests
- Always create unittests, starting with application logic
- Add # noqa to files that should not be tested or added to coverage, like `__init__.py` etc.
- Break tasks into groups of no more than 10-12 tasks per group
- Always end the group with running the build script `uv run scripts/build.py --verbose`
- Always fix bugs before proceeding to the next group of tasks - add this as a validation step for each group
- Always match the global test coverage setting before continuing
- Web UI code should be covered with integrationtests using Playwright
- **MANDATORY** Reference these documents during development of tasks:
  - `.github\prompts\best-practices-check.prompt.md`
  - `.github\prompts\code-analysis.prompt.md`
  - `.work\focused-testing-architecture.md`
- If the tasks need extensive documentation, create a reference document in the `.work/agent/notes/` folder

## Input

- The specification files

## Output

- Create tasks as issues using `uv run issues create`:

```bash
uv run issues create "Task title" \
  --description "Context: <detailed instructions>

Files: <list of affected files>

Acceptance Criteria: <testing requirements>

Dependencies: <blockers or dependencies>" \
  --priority <critical|high|medium|low> \
  --labels task,implementation \
  --status proposed
```

- Tasks should be sorted by priority
- Group related tasks using labels or epic features if available
