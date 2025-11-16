# Template: Codebase Analysis

**Description**: Comprehensive codebase analysis workflow for understanding project structure, patterns, and improvement opportunities

## Overview
Systematic approach to analyze a codebase through multiple lenses: architecture, code quality, testing, documentation, and technical debt.

## Tasks

### 1. Project Structure Analysis
**Priority**: high
**Estimated Effort**: medium

**Description**: Map out the project structure, dependencies, and architectural patterns

**Subtasks**:
- [ ] Document folder structure and organization
- [ ] Identify main entry points and execution flows
- [ ] Map external dependencies and their usage
- [ ] Identify configuration files and their purposes
- [ ] Document build/deployment scripts

**Acceptance Criteria**:
- Complete directory tree documented
- All major components identified
- Dependency graph created
- Configuration patterns documented

---

### 2. Code Quality Assessment
**Priority**: high
**Estimated Effort**: large

**Description**: Analyze code quality metrics, patterns, and potential issues

**Subtasks**:
- [ ] Run linters and static analysis tools
- [ ] Identify code complexity hotspots
- [ ] Check for code duplication
- [ ] Review error handling patterns
- [ ] Assess type safety coverage
- [ ] Identify security vulnerabilities
- [ ] Check for deprecated patterns

**Acceptance Criteria**:
- Linting report generated
- Complexity metrics documented
- Duplication analysis complete
- Security scan performed
- List of quality issues prioritized

---

### 3. Testing Coverage Analysis
**Priority**: high
**Estimated Effort**: medium

**Description**: Evaluate current test coverage and identify gaps

**Subtasks**:
- [ ] Generate coverage report
- [ ] Identify untested critical paths
- [ ] Review test quality and patterns
- [ ] Check for integration/e2e tests
- [ ] Identify flaky or slow tests
- [ ] Document testing infrastructure

**Acceptance Criteria**:
- Coverage report analyzed (target: 70%+)
- Critical untested areas identified
- Test quality issues documented
- Test improvement plan created

---

### 4. Documentation Review
**Priority**: medium
**Estimated Effort**: medium

**Description**: Assess documentation quality and completeness

**Subtasks**:
- [ ] Review README and setup guides
- [ ] Check inline code documentation
- [ ] Verify API documentation exists
- [ ] Review architectural decision records
- [ ] Identify undocumented features
- [ ] Check for outdated documentation

**Acceptance Criteria**:
- Documentation inventory complete
- Gaps and outdated docs identified
- Documentation improvement plan created

---

### 5. Technical Debt Identification
**Priority**: medium
**Estimated Effort**: large

**Description**: Catalog technical debt and improvement opportunities

**Subtasks**:
- [ ] Review TODO/FIXME comments
- [ ] Identify design pattern violations
- [ ] Check for outdated dependencies
- [ ] Review performance bottlenecks
- [ ] Identify tight coupling issues
- [ ] Document migration needs
- [ ] Prioritize debt by impact

**Acceptance Criteria**:
- Technical debt inventory created
- Issues prioritized by severity
- Quick wins identified
- Long-term improvements planned

---

### 6. Architecture Documentation
**Priority**: medium
**Estimated Effort**: medium

**Description**: Document the current architecture and design patterns

**Subtasks**:
- [ ] Create architecture diagram
- [ ] Document data flow patterns
- [ ] Identify architectural patterns used
- [ ] Map service boundaries
- [ ] Document state management
- [ ] Identify coupling points

**Acceptance Criteria**:
- Architecture diagram created
- Key patterns documented
- Design decisions recorded
- Improvement opportunities noted

---

### 7. Dependency Analysis
**Priority**: low
**Estimated Effort**: small

**Description**: Review and optimize project dependencies

**Subtasks**:
- [ ] Audit direct dependencies
- [ ] Check for outdated packages
- [ ] Identify unused dependencies
- [ ] Review security advisories
- [ ] Check license compatibility
- [ ] Document upgrade paths

**Acceptance Criteria**:
- Dependency inventory complete
- Update recommendations provided
- Security issues flagged
- Cleanup opportunities identified

---

## Final Deliverables

1. **Analysis Report**: Comprehensive findings document
2. **Issue Backlog**: Prioritized list of improvements
3. **Architecture Docs**: Diagrams and design documentation
4. **Improvement Roadmap**: Phased plan for addressing findings

## Notes

- Break large codebases into modules and analyze separately
- Focus on high-impact areas first
- Document findings continuously
- Use automated tools where possible
- Validate findings with team members
