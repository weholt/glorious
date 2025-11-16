# Template: Best Practices Analysis

**Description**: Comprehensive analysis of Python codebase against industry best practices for code quality, design, testing, documentation, security, and maintainability

## Overview

This template provides a systematic approach to evaluate a Python project against established best practices. The analysis covers code style, design principles, architecture, testing, documentation, security, performance, and tooling. Results should be documented as enhancement issues in `.work/agent/issues/medium.md` following the specified format.

## Tasks

### 1. Code Style and Readability Assessment

**Priority**: high
**Estimated Effort**: medium

**Description**: Evaluate code style compliance with PEP 8 and readability standards

**Subtasks**:

- [ ] Run automated formatters and linters (Black, Ruff) on codebase
- [ ] Check PEP 8 compliance across all Python files
- [ ] Verify naming conventions (snake_case, CamelCase usage)
- [ ] Assess line length consistency (88-120 chars)
- [ ] Review import organization and ordering
- [ ] Check for OS-specific code that should be portable
- [ ] Identify verbose or unclear variable names
- [ ] Document style violations by severity

**Acceptance Criteria**:

- Linting report generated with all violations categorized
- Style guide compliance percentage calculated
- List of files requiring formatting created
- Naming convention violations documented
- Import organization issues identified

**Issue Template for Findings**:

```markdown
---
id: "STYLE-XXX"
title: "Style violation description"
description: "Brief summary"
created: YYYY-MM-DD
section: code-style
tags: [style, pep8, readability]
type: enhancement
priority: medium
status: proposed
---

Detailed description of the style issue, affected files, and recommended fixes.
```

---

### 2. Design Principles Evaluation

**Priority**: high
**Estimated Effort**: large

**Description**: Analyze adherence to SOLID principles, DRY, KISS, and separation of concerns

**Subtasks**:

- [ ] Identify functions exceeding 15 lines (SRP violations)
- [ ] Find code duplication instances (DRY violations)
- [ ] Check for over-engineered solutions (KISS violations)
- [ ] Evaluate SOLID principle adherence
- [ ] Review dependency injection usage
- [ ] Assess separation of concerns (UI/Logic/Data layers)
- [ ] Identify tight coupling between modules
- [ ] Check for stateful design where stateless would work
- [ ] Document design principle violations

**Acceptance Criteria**:

- List of oversized functions created
- Code duplication report generated
- SOLID violations documented
- Coupling issues identified
- Recommended refactoring patterns provided

**Issue Template for Findings**:

```markdown
---
id: "DESIGN-XXX"
title: "Design principle violation"
description: "Brief summary"
created: YYYY-MM-DD
section: design
tags: [solid, dry, kiss, architecture]
type: enhancement
priority: medium
status: proposed
---

Detailed analysis of design issue, impact on maintainability, and refactoring approach.
```

---

### 3. Architecture and Modularity Review

**Priority**: high
**Estimated Effort**: large

**Description**: Evaluate project structure, layering, and architectural patterns

**Subtasks**:

- [ ] Map current project structure and layers
- [ ] Identify architectural pattern in use (if any)
- [ ] Check for proper layer separation
- [ ] Verify high cohesion within modules
- [ ] Assess coupling between modules
- [ ] Review dependency directions (no circular deps)
- [ ] Identify missing abstractions or interfaces
- [ ] Check for hexagonal/clean architecture principles
- [ ] Document architectural issues

**Acceptance Criteria**:

- Architecture diagram created
- Layer violations documented
- Module coupling analysis complete
- Dependency graph generated
- Architectural improvements prioritized

**Issue Template for Findings**:

```markdown
---
id: "ARCH-XXX"
title: "Architectural issue"
description: "Brief summary"
created: YYYY-MM-DD
section: architecture
tags: [structure, modularity, layers]
type: enhancement
priority: medium
status: proposed
---

Description of architectural concern, impact on scalability/maintainability, and recommended solution.
```

---

### 4. Testing and Quality Assurance Audit

**Priority**: critical
**Estimated Effort**: medium

**Description**: Assess test coverage, quality, and testing infrastructure

**Subtasks**:

- [ ] Generate test coverage report
- [ ] Identify untested critical paths
- [ ] Review test quality (unit vs integration balance)
- [ ] Check for test fixtures and factories usage
- [ ] Verify CI/CD pipeline runs tests
- [ ] Assess test execution speed
- [ ] Identify flaky or brittle tests
- [ ] Check for missing edge case tests
- [ ] Document testing gaps

**Acceptance Criteria**:

- Coverage report analyzed (target: 70%+)
- Critical untested code identified
- Test quality issues documented
- CI integration verified
- Test improvement roadmap created

**Issue Template for Findings**:

```markdown
---
id: "TEST-XXX"
title: "Testing gap or issue"
description: "Brief summary"
created: YYYY-MM-DD
section: testing
tags: [coverage, quality-assurance, unit-tests]
type: enhancement
priority: high
status: proposed
---

Description of testing gap, risk level, and recommended test additions.
```

---

### 5. Documentation Quality Review

**Priority**: medium
**Estimated Effort**: medium

**Description**: Evaluate documentation completeness and quality

**Subtasks**:

- [ ] Check docstring presence on public functions/classes
- [ ] Verify docstring format consistency (Google/NumPy style)
- [ ] Review README completeness
- [ ] Check for API documentation
- [ ] Assess inline comment quality
- [ ] Verify type annotations usage
- [ ] Check for mkdocs or similar doc framework
- [ ] Identify undocumented complex logic
- [ ] Document documentation gaps

**Acceptance Criteria**:

- Docstring coverage percentage calculated
- README quality assessed
- Missing documentation identified
- Type annotation coverage measured
- Documentation improvement plan created

**Issue Template for Findings**:

```markdown
---
id: "DOC-XXX"
title: "Documentation gap"
description: "Brief summary"
created: YYYY-MM-DD
section: documentation
tags: [docs, docstrings, readme]
type: enhancement
priority: medium
status: proposed
---

Description of missing or inadequate documentation and recommended additions.
```

---

### 6. Security and Configuration Audit

**Priority**: critical
**Estimated Effort**: medium

**Description**: Identify security vulnerabilities and configuration issues

**Subtasks**:

- [ ] Scan for hardcoded secrets (passwords, API keys)
- [ ] Run Bandit security analyzer
- [ ] Check for insecure functions (eval, exec)
- [ ] Verify input validation practices
- [ ] Review error handling for information leaks
- [ ] Check dependency vulnerabilities (pip-audit)
- [ ] Assess configuration management (.env usage)
- [ ] Review logging for sensitive data exposure
- [ ] Document security issues

**Acceptance Criteria**:

- Security scan report generated
- Hardcoded secrets identified and flagged
- Vulnerable dependencies listed
- Configuration issues documented
- Security improvements prioritized

**Issue Template for Findings**:

```markdown
---
id: "SEC-XXX"
title: "Security issue"
description: "Brief summary"
created: YYYY-MM-DD
section: security
tags: [security, vulnerability, configuration]
type: enhancement
priority: critical
status: proposed
---

Description of security risk, potential impact, and remediation steps.
```

---

### 7. Performance and Optimization Analysis

**Priority**: medium
**Estimated Effort**: medium

**Description**: Identify performance bottlenecks and optimization opportunities

**Subtasks**:

- [ ] Review algorithmic complexity of critical paths
- [ ] Identify inefficient data structures usage
- [ ] Check for unnecessary memory allocations
- [ ] Review database query efficiency (if applicable)
- [ ] Identify missing caching opportunities
- [ ] Check for blocking I/O in async code
- [ ] Review generator vs list usage patterns
- [ ] Profile hot paths if performance critical
- [ ] Document performance issues

**Acceptance Criteria**:

- Performance bottlenecks identified
- Algorithm complexity issues documented
- Caching opportunities listed
- Memory optimization areas identified
- Performance improvement roadmap created

**Issue Template for Findings**:

```markdown
---
id: "PERF-XXX"
title: "Performance issue"
description: "Brief summary"
created: YYYY-MM-DD
section: performance
tags: [optimization, efficiency, bottleneck]
type: enhancement
priority: medium
status: proposed
---

Description of performance issue, measured impact, and optimization approach.
```

---

### 8. Tooling and Automation Assessment

**Priority**: medium
**Estimated Effort**: small

**Description**: Review development tooling and automation setup

**Subtasks**:

- [ ] Verify linters configuration (Ruff, mypy)
- [ ] Check formatter setup (Black)
- [ ] Review pre-commit hooks configuration
- [ ] Assess CI/CD pipeline completeness
- [ ] Verify dependency management setup
- [ ] Check for automated release process
- [ ] Review development environment documentation
- [ ] Identify missing automation opportunities
- [ ] Document tooling gaps

**Acceptance Criteria**:

- Tooling inventory created
- CI/CD pipeline assessed
- Missing automation identified
- Pre-commit hooks verified
- Tooling improvement plan created

**Issue Template for Findings**:

```markdown
---
id: "TOOL-XXX"
title: "Tooling gap"
description: "Brief summary"
created: YYYY-MM-DD
section: tooling
tags: [automation, ci-cd, development]
type: enhancement
priority: medium
status: proposed
---

Description of missing or inadequate tooling and recommended additions.
```

---

## Issue Management Guidelines

### Breaking Down Large Analysis Tasks

When conducting this analysis, create issues systematically:

1. **Parent Epic**: Create an epic for "Codebase Best Practices Analysis"
   ```bash
   uv run issues create "Best Practices Analysis 2025" --type epic --priority high
   ```

2. **Task-Level Issues**: Create one issue per major task above
   ```bash
   uv run issues create "Code Style Assessment" --deps subtask-of:EPIC-ID --priority high
   ```

3. **Finding Issues**: Document each specific finding in `.work/agent/issues/medium.md`
   - Use the format specified in each task section
   - Include unique IDs following pattern: `CATEGORY-XXX`
   - Link related findings with tags

4. **Sub-Issue Creation**: For large findings, create sub-issues
   ```bash
   uv run issues create "Refactor UserService (SRP violation)" --deps subtask-of:DESIGN-001
   ```

### Issue Workflow

1. **Discovery Phase**: Run analysis, document findings in `.work/agent/issues/`
2. **Prioritization**: Review all findings, adjust priorities based on impact
3. **Issue Creation**: Create trackable issues for high/critical items
4. **Batch Processing**: Group related small fixes into single issues
5. **Progressive Work**: Address issues incrementally, not all at once
6. **Completion**: Move completed items to `.work/agent/issues/history.md`

### Priority Guidelines

- **Critical**: Security vulnerabilities, data loss risks, broken functionality
- **High**: Test coverage gaps, major design violations, architectural issues
- **Medium**: Code style issues, documentation gaps, minor refactoring
- **Low**: Aesthetic improvements, nice-to-have optimizations

### Working with Issue Files

All findings append to: `.work/agent/issues/medium.md` (default priority)

For critical/high findings, move to appropriate file:
- `.work/agent/issues/critical.md`
- `.work/agent/issues/high.md`

When resolved, move entire issue block to `.work/agent/issues/history.md`

---

## Anti-Patterns to Flag

- Direct imports from `src/` (use package imports)
- Class names with library suffixes (e.g., `SQLModelUser`)
- Inlined imports (imports inside functions)
- HTML in Python code (should be in templates)
- Long methods (>15 lines)
- Large classes (>200 lines or >10 methods)
- Over-engineering simple solutions

---

## Final Deliverables

1. **Analysis Report**: Comprehensive findings documented in `.work/agent/issues/`
2. **Issue Backlog**: Prioritized list of improvements
3. **Metrics Summary**: Coverage, style compliance, security scan results
4. **Improvement Roadmap**: Phased plan organized by priority
5. **Quick Wins List**: Easy fixes that provide immediate value

---

## Notes

- Focus on actionable findings, not general observations
- Ignore test files, migrations, docs, scripts, .work folders
- Target main source code in `src/` directory
- Use automated tools where possible (Ruff, Bandit, pytest-cov)
- Be extremely critical and nitpicky - goal is excellence
- Document specific files, line numbers, and code examples
- Provide concrete refactoring suggestions
- Consider maintainability impact of each finding
- Balance perfect code with practical delivery
