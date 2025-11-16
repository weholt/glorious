# Template: Code Quality and Structure Analysis

**Description**: Deep analysis for code duplication, structural violations, anti-patterns, and quality issues with focus on architecture and maintainability

## Overview

Systematic analysis targeting code duplication, misplaced code, protocol violations, anti-patterns, and structural issues. This template focuses on detecting issues that impact maintainability, testability, and adherence to architectural patterns. All findings are documented as issues in `.work/agent/issues/` organized by priority.

## Tasks

### 1. Code Duplication Detection

**Priority**: high
**Estimated Effort**: medium

**Description**: Identify duplicated or near-duplicated code across the codebase

**Subtasks**:

- [ ] Scan for exact duplicate functions
- [ ] Detect near-duplicate code blocks (>70% similarity)
- [ ] Compare similar logic across different modules
- [ ] Identify copy-pasted classes with minor variations
- [ ] Check for duplicated validation logic
- [ ] Find repeated error handling patterns
- [ ] Detect duplicated data transformation code
- [ ] Document all duplication instances with similarity %

**Acceptance Criteria**:

- Duplication report with similarity percentages
- Each duplicate pair documented with file paths
- Consolidation recommendations provided
- Priority assigned based on maintenance burden
- Target module identified for consolidation

**Issue Template**:

```markdown
---
id: "DUPL-XXX"
title: "Duplicated [function/class name]"
description: "[X]% similar code in [count] locations"
created: YYYY-MM-DD
section: code-quality
tags: [duplication, refactor, dry]
type: duplication
priority: high
status: proposed
---

**Files**:
- `path/to/file1.py:line_number`
- `path/to/file2.py:line_number`

**Similarity**: X%

**Description**: Detailed description of duplicated code and differences.

**Impact**: Maintenance burden, potential for divergent behavior, increased bug surface.

**Recommended Fix**: Consolidate into `recommended/path/module.py` with unified interface. Update all X import locations.

**Example Refactoring**:
```python
# Consolidated implementation
```
```

---

### 2. Structural and Architectural Violations

**Priority**: critical
**Estimated Effort**: large

**Description**: Detect violations of expected folder structure and architectural patterns

**Subtasks**:

- [ ] Map expected folder structure (protocols/, domain/, services/, infra/, adapters/, api/)
- [ ] Identify business logic in transport layers (api/, cli/, routes/)
- [ ] Find persistence code in domain or service layers
- [ ] Detect UI/presentation logic in business layer
- [ ] Check for cross-layer violations
- [ ] Identify misplaced implementations
- [ ] Find circular dependencies between layers
- [ ] Document all structural violations with severity

**Acceptance Criteria**:

- Complete structural violation inventory
- Layer boundary violations documented
- Misplaced files identified with target locations
- Circular dependency graph created
- Refactoring plan with move operations

**Issue Template**:

```markdown
---
id: "STRUCT-XXX"
title: "Structural violation: [description]"
description: "[Component] in wrong layer/folder"
created: YYYY-MM-DD
section: architecture
tags: [structure, layers, separation-of-concerns]
type: structural-violation
priority: high
status: proposed
---

**Current Location**: `path/to/file.py`
**Expected Location**: `correct/path/to/file.py`

**Description**: Detailed explanation of why this is misplaced.

**Violation Type**: [Business logic in API layer | Persistence in domain | etc.]

**Impact**: Violates separation of concerns, reduces testability, creates tight coupling.

**Recommended Fix**: Move to correct location and update imports.

**Affected Imports**: List of files importing this module.
```

---

### 3. Protocol and Interface Violations

**Priority**: high
**Estimated Effort**: medium

**Description**: Verify proper implementation and placement of protocols and interfaces

**Subtasks**:

- [ ] Find all Protocol and ABC definitions
- [ ] Identify all implementing classes
- [ ] Verify protocols are in correct folder (protocols/)
- [ ] Check implementations are in appropriate folders (adapters/, infra/)
- [ ] Detect partial implementations (missing methods)
- [ ] Find unused protocols
- [ ] Identify protocols without implementations
- [ ] Check for concrete types where protocols should be used
- [ ] Document all protocol violations

**Acceptance Criteria**:

- Complete protocol inventory
- Implementation completeness verified
- Misplaced protocols identified
- Missing implementations documented
- Unused protocols flagged for removal

**Issue Template**:

```markdown
---
id: "PROTO-XXX"
title: "Protocol violation: [description]"
description: "[Implementation/Protocol] incorrectly placed or incomplete"
created: YYYY-MM-DD
section: architecture
tags: [protocol, interface, abstraction]
type: structural-violation
priority: medium
status: proposed
---

**Protocol**: `ProtocolName` in `path/to/protocol.py`
**Implementation**: `ImplName` in `path/to/impl.py`

**Issue**: [Misplaced | Incomplete | Unused | etc.]

**Description**: Detailed explanation of the violation.

**Impact**: Breaks abstraction pattern, reduces flexibility, complicates testing.

**Recommended Fix**: [Move to correct folder | Implement missing methods | Remove unused protocol]
```

---

### 4. Anti-Patterns and Code Smells

**Priority**: high
**Estimated Effort**: large

**Description**: Identify common anti-patterns and code smells that reduce maintainability

**Subtasks**:

- [ ] Find large functions (>40 lines) and classes (>200 lines or >10 methods)
- [ ] Detect deep nesting (>3 levels)
- [ ] Identify high cyclomatic complexity
- [ ] Find catch-all exception handlers
- [ ] Detect magic strings and numbers
- [ ] Identify global variable misuse
- [ ] Find shared mutable state
- [ ] Check for god classes/objects
- [ ] Detect feature envy (method using another class's data extensively)
- [ ] Find inappropriate intimacy (classes too tightly coupled)
- [ ] Document all anti-patterns with severity

**Acceptance Criteria**:

- Complete anti-pattern inventory
- Complexity metrics calculated
- Large functions/classes documented
- Exception handling issues identified
- Refactoring patterns recommended

**Issue Template**:

```markdown
---
id: "SMELL-XXX"
title: "Code smell: [type]"
description: "[Function/Class] exhibits [anti-pattern]"
created: YYYY-MM-DD
section: code-quality
tags: [code-smell, anti-pattern, complexity]
type: enhancement
priority: medium
status: proposed
---

**Location**: `path/to/file.py:ClassName.method_name`
**Anti-Pattern**: [Large function | Deep nesting | God class | etc.]
**Metrics**: [Lines: X | Complexity: Y | Nesting depth: Z]

**Description**: Detailed explanation of the issue.

**Impact**: Reduced readability, harder to test, increased bug risk.

**Recommended Fix**: [Extract methods | Simplify conditionals | Split class | etc.]

**Refactoring Strategy**: Step-by-step approach to resolve.
```

---

### 5. Unused and Unreachable Code

**Priority**: medium
**Estimated Effort**: medium

**Description**: Identify dead code, unused imports, and unreachable logic

**Subtasks**:

- [ ] Find unused functions and classes
- [ ] Detect unused imports
- [ ] Identify unreachable code branches
- [ ] Find always-true/false conditions
- [ ] Detect functions never called
- [ ] Identify unused constants
- [ ] Find orphaned files (not imported anywhere)
- [ ] Document all unused code for removal

**Acceptance Criteria**:

- Complete unused code inventory
- Import usage analyzed
- Unreachable branches identified
- Safe-to-remove list created
- Removal priority assigned

**Issue Template**:

```markdown
---
id: "DEAD-XXX"
title: "Unused code: [component name]"
description: "[Function/Class/Import] never used"
created: YYYY-MM-DD
section: code-quality
tags: [dead-code, cleanup, unused]
type: enhancement
priority: low
status: proposed
---

**Location**: `path/to/file.py:name`
**Type**: [Function | Class | Import | Constant | File]

**Description**: This code appears to be unused throughout the codebase.

**Verification**: No imports or references found in project.

**Impact**: Code bloat, maintenance overhead, confusion.

**Recommended Fix**: Remove safely after final verification.

**Caution**: [Any notes about potential dynamic usage or public API]
```

---

### 6. Dependency and Coupling Issues

**Priority**: high
**Estimated Effort**: medium

**Description**: Analyze dependency direction and coupling between modules

**Subtasks**:

- [ ] Map all module dependencies
- [ ] Identify dependency inversion violations
- [ ] Find high-level modules depending on low-level
- [ ] Detect domain code importing infrastructure
- [ ] Check for circular dependencies
- [ ] Identify tight coupling between unrelated modules
- [ ] Find missing abstractions
- [ ] Detect concrete types used where interfaces should be
- [ ] Document all dependency violations

**Acceptance Criteria**:

- Dependency graph generated
- DIP violations documented
- Circular dependencies identified
- Coupling metrics calculated
- Abstraction recommendations provided

**Issue Template**:

```markdown
---
id: "DEP-XXX"
title: "Dependency violation: [description]"
description: "Improper dependency direction in [modules]"
created: YYYY-MM-DD
section: architecture
tags: [dependency, coupling, dip]
type: structural-violation
priority: high
status: proposed
---

**From**: `module/path/a.py`
**To**: `module/path/b.py`

**Issue**: [High-level depends on low-level | Circular dependency | Domain imports infra]

**Description**: Detailed explanation of dependency issue.

**Impact**: Reduces flexibility, complicates testing, violates clean architecture.

**Recommended Fix**: Introduce abstraction layer or invert dependency direction.

**Refactoring Approach**: Concrete steps to resolve.
```

---

### 7. Configuration and Constants Audit

**Priority**: medium
**Estimated Effort**: small

**Description**: Identify hard-coded values that should be configurable

**Subtasks**:

- [ ] Find hard-coded URLs and endpoints
- [ ] Detect hard-coded credentials or secrets
- [ ] Identify magic numbers in code
- [ ] Find hard-coded file paths
- [ ] Detect hard-coded timeout values
- [ ] Identify configuration scattered across modules
- [ ] Check for missing .env usage
- [ ] Document all hard-coded values

**Acceptance Criteria**:

- Hard-coded value inventory complete
- Security issues flagged (secrets)
- Configuration extraction plan created
- .env migration approach defined
- Constants module design proposed

**Issue Template**:

```markdown
---
id: "CONFIG-XXX"
title: "Hard-coded [type]: [description]"
description: "Configuration value should be externalized"
created: YYYY-MM-DD
section: configuration
tags: [hard-coded, configuration, constants]
type: enhancement
priority: medium
status: proposed
---

**Location**: `path/to/file.py:line_number`
**Value**: `"hard-coded-value"`
**Type**: [URL | Secret | Timeout | Path | etc.]

**Description**: This value is hard-coded and should be configurable.

**Impact**: Reduces flexibility, complicates deployment, potential security issue.

**Recommended Fix**: Move to config.py or .env file.

**Suggested Implementation**:
```python
# config.py or .env
SETTING_NAME = os.getenv("SETTING_NAME", "default_value")
```
```

---

### 8. API and Interface Clarity

**Priority**: medium
**Estimated Effort**: small

**Description**: Identify unclear or inappropriate public interfaces

**Subtasks**:

- [ ] Find public functions not used externally
- [ ] Identify functions that should be private (_prefixed)
- [ ] Detect inconsistent function naming
- [ ] Find unclear parameter names
- [ ] Check for missing type hints on public APIs
- [ ] Identify functions with too many parameters
- [ ] Detect boolean trap patterns
- [ ] Document all interface clarity issues

**Acceptance Criteria**:

- Public API inventory complete
- Private candidates identified
- Naming inconsistencies documented
- Type hint gaps identified
- API improvement recommendations provided

**Issue Template**:

```markdown
---
id: "API-XXX"
title: "API clarity issue: [description]"
description: "Public interface needs improvement"
created: YYYY-MM-DD
section: api-design
tags: [interface, naming, public-api]
type: enhancement
priority: low
status: proposed
---

**Location**: `path/to/file.py:function_name`

**Issue**: [Should be private | Unclear naming | Missing types | Too many params]

**Description**: Detailed explanation of the interface issue.

**Impact**: Confusion for users, maintenance burden, unclear contract.

**Recommended Fix**: [Make private | Rename | Add types | Refactor signature]
```

---

## Issue Management for Large Analysis

### Workflow for Breaking Down Work

1. **Create Analysis Epic**:
   ```bash
   uv run issues create "Code Quality Analysis 2025" --type epic --priority high
   ```

2. **Create Task Issues**: One per major analysis task
   ```bash
   uv run issues create "Code Duplication Detection" \
     --deps subtask-of:EPIC-ID --priority high
   ```

3. **Document Findings**: Write to `.work/agent/issues/[priority].md`
   - Use templates above
   - Assign unique IDs
   - Include all context

4. **Create Trackable Issues**: For significant findings
   ```bash
   uv run issues create "Consolidate parse_date functions" \
     --deps subtask-of:DUPL-001 --priority high \
     --description "Found in 3 modules, 92% similar"
   ```

5. **Batch Small Fixes**: Group related minor issues
   ```bash
   uv run issues create "Remove unused imports (batch)" \
     --description "15 files with unused imports to clean"
   ```

6. **Track Progress**: Move completed issues to history
   ```bash
   # Manually move from .work/agent/issues/medium.md 
   # to .work/agent/issues/history.md
   ```

### Priority Assignment Logic

**Critical**:
- Security vulnerabilities
- Data corruption risks
- Circular dependencies breaking builds

**High**:
- Major structural violations
- High-impact duplication
- Dependency inversion violations

**Medium**:
- Code smells
- Minor duplication
- Misplaced files (low impact)

**Low**:
- Dead code removal
- Naming improvements
- Public/private adjustments

---

## Analysis Tools and Commands

### Automated Detection

```bash
# Run linters
uv run ruff check src/

# Type checking
uv run mypy src/

# Security scan
uv run bandit -r src/

# Complexity analysis
uv run radon cc src/ -a -nb

# Duplicate code detection
uv run pylint src/ --disable=all --enable=duplicate-code
```

### Manual Inspection Focus

- AST-level similarity for duplication
- Import graph for dependencies
- File location vs. responsibility mismatch
- Exception handling patterns
- State management approaches

---

## Exclusions

**Do Not Analyze**:
- `tests/` - Test code has different rules
- `.github/` - CI/CD configurations
- `docs/` - Documentation files
- `scripts/` - Build and utility scripts
- `migrations/` - Database migrations (generated)
- `.work/` - Agent working directory

**Focus Analysis On**:
- `src/` - Main source code
- `pyproject.toml` - Project configuration
- `setup.py` - If present
- Main application entry points

---

## Final Deliverables

1. **Issue Files**: Complete findings in `.work/agent/issues/`
2. **Priority Breakdown**: Issues organized by severity
3. **Refactoring Roadmap**: Phased plan for addressing issues
4. **Quick Wins**: Easy fixes providing immediate value
5. **Architecture Diagram**: Current vs. desired structure
6. **Metrics Dashboard**: Counts of issues by type/priority

---

## Notes

- Be extremely critical and nitpicky
- Focus on maintainability impact
- Provide specific file paths and line numbers
- Include code examples in issue descriptions
- Suggest concrete refactoring approaches
- Consider testing impact of changes
- Balance perfection with pragmatism
- Document assumptions and edge cases
- Link related issues with tags
