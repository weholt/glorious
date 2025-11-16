---
description: 'Analyze codebase for duplication, structural violations, anti-patterns, and quality issues'
tags: [code-quality, static-analysis, refactor, mcp-agent, bugs, analysis]
---

# Prompt: Analyze Codebase for Duplication, Structural Violations, and Quality Issues

**IMPORTANT** Before proceeding any further, read `.github/copilot-instructions.md` and follow those instructions while you process the codebase.

## Objective
Analyze the given codebase to identify and document:

1. **Duplicated or near-duplicated code**
2. **Violations of expected folder structure**
3. **Incorrect or missing protocol/interface implementations**
4. **Anti-patterns and code smells**
5. **Functions or classes with too many responsibilities**
6. **Improper exception handling**
7. **Unreachable or unused code**
8. **Improper dependency direction (violations of Dependency Inversion Principle)**
9. **Overuse of concrete types where interfaces should be used**
10. **Hard-coded constants where configuration should be used - .env / dotenv**
11. **Public functions or classes not used outside their module (should be private/internal)**
12. **Performance issues or bottlenecks**
13. **HTML in code - HTML should always be in templates**
14. **Inlined imports**
15. **Pure utility methods outside utility library**
16. **Over-engineering - prefer simplicity over complexity**
17. **Long methods or functions - >15 lines should be considered for refactoring**
18. **Large classes - >200 lines or >10 methods should be considered for refactoring**
19. **MANDATORY**: Be extremly critical and nitpicky - the goal is to make the codebase as clean, maintainable, and high-quality as possible.
---

## Instructions for Agent

### 1. Search for Duplicated Code
- Use structural, token, and AST-level similarity to find duplicated or nearly duplicated:
  - Functions
  - Classes
  - Blocks of logic
- Compare across folders (`utils/`, `services/`, `api/`, etc.)
- Detect minor changes between copies (e.g., parameter names, small edits)

### 2. Check for Protocol/Interface Violations
- Identify all `Protocol`, `ABC`, or interface-like definitions (e.g., base classes with abstract methods).
- Find all classes implementing these protocols.
- Ensure implementations are in appropriate folders:
  - Protocols → `protocols/`
  - Implementations → `adapters/`, `services/`, `infra/`, etc.
- Detect:
  - Implementations scattered across folders
  - Unused or unimplemented protocols
  - Interfaces implemented with only partial compliance (missing methods)

### 3. Detect Misplaced Code
- Infer expected folder structure: `protocols/`, `domain/`, `services/`, `infra/`, `adapters/`, `api/`, `tests/`
- Detect:
  - Business logic in `api/`, `cli/`, `routes/`
  - Transport code in `domain/`
  - Persistence-specific code in `services/`
  - Cross-layer violations (e.g., DB code calling domain logic directly)

### 4. Detect Code Smells and Anti-patterns
- Large functions/classes (>40 lines or >10 methods)
- Nested control flow >3 levels
- Functions with high cyclomatic complexity
- Catch-all `except:` blocks
- Magic strings and numbers
- Overuse of global variables or shared state
- Mutating shared data in unexpected places

### 5. Unused or Unreachable Code
- Functions, classes, constants, or files not imported or used
- Conditions that are always true/false
- Branches never executed due to earlier returns

### 6. Dependency Violations
- Check for inversion violations:
  - High-level modules importing low-level infrastructure directly
  - Domain code importing from `api/`, `cli/`, `infra/`
- Suggest introducing interfaces where needed

### 7. Poor Abstractions or Tight Coupling
- Concrete types passed around where interfaces could be used
- Single class doing DB access, parsing, and business logic
- Multiple unrelated concerns in one module

### 8. Hard-coded Configuration
- Detect use of hard-coded strings, URLs, keys, tokens, and constants
- Suggest extracting into `config/`, environment variables, or `.env`

### 9. Unclear Public APIs
- Public functions/classes (`not _prefixed`) that are not imported or used by other modules
- Suggest marking them internal

---

## Output Format

Create issues using `uv run issues create` for each finding:

```bash
uv run issues create "Duplicated parse_date logic" \
  --description "The parse_date function is 92% similar to get_date in services/time.py. This creates maintenance burden and potential for divergent behavior. Recommended fix: Consolidate both functions into utils/datetime.py and update all imports." \
  --priority high \
  --labels duplication,refactor \
  --status proposed
```

Example commands to create issues:

```bash
# Duplicated code
uv run issues create "Duplicated parse_date logic" \
  --description "utils/date.py:parse_date is 92% similar to services/time.py:get_date. Consolidate into utils/datetime.py." \
  --priority high --labels duplication,refactor --status proposed

# Structural violation
uv run issues create "UserRepoImpl in wrong folder" \
  --description "services/user_repo_impl.py implements UserRepository protocol but should be in infra/. Move to infra/repositories/ and update imports." \
  --priority medium --labels structure,protocol --status proposed

# Misplaced code
uv run issues create "Business logic in route handler" \
  --description "api/routes.py:create_user_with_subscriptions() contains business logic. Move to domain/user_service.py." \
  --priority high --labels structure,separation-of-concerns --status proposed
```
---

## Housekeeping

- **IMPORTANT** Close completed issues using `uv run issues close ISSUE-ID --reason "Description of fix"`.


## Notes

* Use `ast`, `tokenize`, and language-specific static analysis tools.
* Be conservative in refactor suggestions; focus on clear violations or smells.
* When in doubt, prefer modularity, abstraction, and separation of concerns.
* DO NOT WRITE VERBOSE SUMMARIES - actionable items only.
* Do not add information about what has been solved - this document is about things that are not working, missing, doing something wrong - things that needs to be fixed.