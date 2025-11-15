# Glorious Agents — Implementation Task List (Atomic Steps)

This task list turns `chat.md` into actionable steps, guided by `focused-testing-architecture.md`. It assumes Windows and uses `uv` for all Python operations.

---

## 0) Global Assumptions & Variables

- `PROJECT_NAME`: `glorious-agents`
- `PY_MIN`: `3.13`
- `COVERAGE_TARGET`: `75` (adjust later)
- `DOMAIN_DIR`: `src/glorious_agents/domain`
- `APP_DIRS_IGNORED_FOR_COVERAGE`: `api,cli,web,models,schemas,migrations`

---

## 1) Environment Setup (Windows)

- [ ] Install Python (>= `PY_MIN`).
  - Acceptance: `python --version` shows >= 3.13.
- [ ] Install `uv` using system Python.
  - Command:
    
    ```powershell
    python -m pip install --upgrade uv
    ```
    
  - Acceptance: `uv --version` works.
- [ ] Install Git + GitHub CLI + VS Code with Python extension.
  - Acceptance: `git --version`, `gh --version`, VS Code opens.
- [ ] Configure global `.gitignore` per architecture.
  - Create `/.gitignore` including `.work/agent/` and Python/pytest artifacts.
  - Acceptance: File present matching guidelines.

---

## 2) Repository Bootstrap

- [ ] Create repo root structure.
  - Paths:
    - `glorious_agents/` (package root)
    - `pyproject.toml`
    - `.pre-commit-config.yaml`
    - `.github/workflows/ci.yml`
    - `README.md`
    - `.work/agent/notes/` (gitignored)
  - Acceptance: All paths exist.
- [ ] Initialize Git repository.
  - Command:
    
    ```powershell
    git init
    git add .
    git commit -m "chore: bootstrap repo"
    ```
    
  - Acceptance: Initial commit created.

---

## 3) pyproject & Tooling Config

- [ ] Author `pyproject.toml` with project metadata and tools.
  - Include: pytest config, coverage, ruff, mypy.
  - Acceptance: File contains sections as in architecture doc; `requires-python` set to `>=PY_MIN`.
- [ ] Add development dependencies to `pyproject.toml` (pytest, coverage, ruff, mypy, typer, rich, fastapi, uvicorn).
  - Acceptance: `uv sync` completes successfully.
- [ ] Run `uv sync` to install dependencies.
  - Command:
    
    ```powershell
    uv sync
    ```
    
  - Acceptance: Env created; packages installed.
- [ ] Configure `pre-commit` hooks.
  - File: `.pre-commit-config.yaml` (Ruff fix + lint, MyPy).
  - Command:
    
    ```powershell
    uv run pre-commit install
    ```
    
  - Acceptance: Hooks installed.

---

## 4) Package Layout & Core Modules

- [ ] Create package skeleton.
  - Paths:
    - `src/glorious_agents/__init__.py`
    - `src/glorious_agents/cli.py`
    - `src/glorious_agents/skills_cli.py`
    - `src/glorious_agents/core/db.py`
    - `src/glorious_agents/core/loader.py`
    - `src/glorious_agents/core/registry.py`
    - `src/glorious_agents/core/runtime.py`
    - `src/glorious_agents/core/context.py`
    - `src/glorious_agents/core/daemon.py`
  - Acceptance: Files exist with docstrings and typed function/class skeletons.
- [ ] Implement `core/db.py`.
  - `get_agent_db_path()`, `get_connection(check_same_thread=False)`, `init_skill_schema(skill_name, schema_path)`.
  - Acceptance: Unit tests for path resolution and WAL pragmas pass.
- [ ] Implement `core/context.py`.
  - `EventBus` (in-proc pub/sub) + `SkillContext` (shared DB, publish/subscribe, cache, `get_skill`).
  - Acceptance: Unit tests verify subscribe/publish semantics and context singleton.
- [ ] Implement `core/runtime.py`.
  - `get_ctx()` returns process-local singleton `SkillContext`.
  - Acceptance: Unit test ensures single instance.
- [ ] Implement `core/registry.py`.
  - In-proc registry for loaded skills and manifests; methods to add/get/list.
  - Acceptance: Unit tests for registry operations.

---

## 5) Loader & Dependency Resolution

- [ ] Implement `core/loader.py::discover_local_skills()`.
  - Scan `skills/*/skill.json`, validate schema.
  - Acceptance: Returns dict of manifests with origins.
- [ ] Implement `core/loader.py::discover_entrypoint_skills(ep_group="glorious_agents.skills")`.
  - Use Python entry points; merge with local (local wins).
  - Acceptance: Detects installed plugins.
- [ ] Implement `core/loader.py::resolve_dependencies(skills)`.
  - Topological sort by `requires`; error on missing or cycles.
  - Acceptance: Unit tests cover DAG resolution + cycles.
- [ ] Implement `core/loader.py::init_schemas(sorted_skills)`.
  - Exec each manifest `schema.sql` once; idempotent.
  - Acceptance: Creates tables; skips if already applied.
- [ ] Implement `core/loader.py::load_skill_entry(entry_point)`.
  - Import module, return Typer app; if `init_context(ctx)` exists, call with `get_ctx()`.
  - Acceptance: Loads app; context injection verified by unit tests.

---

## 6) Runtime Wiring & Event Bus

- [ ] Wire loader results into registry and context.
  - On app startup, create `SkillContext`, register skills, inject context.
  - Acceptance: Integration test confirms loaded skills accessible via context.
- [ ] Define canonical topics.
  - `note_created`, `issue_created`, `issue_updated`, `plan_enqueued`, `scan_ready`, `vacuum_done`.
  - Acceptance: Event constants exported; bus routes functioning.

---

## 7) CLI Root & Skills Management

- [ ] Implement `src/glorious_agents/cli.py` Typer root `agent`.
  - On import: discover → resolve deps → init schemas → load + inject → `app.add_typer(entry, name=<skill>)`.
  - Acceptance: `uv run agent --help` lists skills.
- [ ] Implement `skills_cli.py` commands.
  - `agent skills reload`, `list`, `describe <skill>`, `export --format json|md`, `create <name>`.
  - Acceptance: Commands produce expected output; e2e tests pass.

---

## 8) Daemon (FastAPI/Uvicorn)

- [ ] Implement `core/daemon.py` FastAPI app.
  - Endpoints: `GET /skills`; optional `POST /rpc/{skill}/{method}` with JSON params.
  - Acceptance: `uv run agent daemon --host 127.0.0.1 --port 8765` starts; `GET /skills` returns loaded skills.
- [ ] Add security defaults.
  - Bind `127.0.0.1`; optional token auth for RPC.
  - Acceptance: Configurable via env/args; e2e test validates RPC guarded when enabled.

---

## 9) Shared Database (Per-Agent)

- [ ] Implement active agent pathing.
  - Active code under default folder `.agent\active_agent`.
  - DB path: `.agent\agents\<code>\agent.db`.
  - Note: Default agent folder `.agent` can be overridden via `AGENT_FOLDER` in `.env`.
  - Acceptance: Switching active agent changes DB path in context.
- [ ] Implement base registry (optional): `.agent\master.db`.
  - Commands: `agent register`, `agent use`, `agent whoami`, `agent list`.
  - Acceptance: CLI updates master registry and context.

---

## 10) Reference Skills — Notes

- [ ] Scaffold `skills/notes`.
  - Files: `skill.json`, `schema.sql`, `skill.py`, `instructions.md`, `usage.md`.
  - Acceptance: Manifest valid; schema applies; `agent notes --help` works.
- [ ] Implement `schema.sql` for notes.
  - Table with `id`, `content`, `tags`, timestamps; add FTS5 virtual table + triggers.
  - Acceptance: Inserts populate FTS index; search works.
- [ ] Implement `skill.py`.
  - Typer app; `init_context(ctx)`; callable APIs: `add_note(content, tags) -> int`, `search_notes(query)`.
  - Publish `note_created` on add.
  - Acceptance: Unit tests for APIs; integration tests via CLI.

---

## 11) Reference Skills — Issues (depends on notes)

- [ ] Scaffold `skills/issues` similarly.
  - Acceptance: Manifest valid; dependency on `notes` declared.
- [ ] Implement `schema.sql` for issues.
  - Table with `id`, `title`, `description`, `status`, timestamps.
  - Acceptance: CRUD works; indices present.
- [ ] Implement `skill.py`.
  - Subscribes to `note_created` → `create_issue` with auto title.
  - Callable APIs: `create_issue(title, desc) -> int`, `update_issue(...)`.
  - Acceptance: Event-triggered issue creation confirmed in integration tests.

---

## 12) Entry Point Discovery (External Skills)

- [ ] Add `pyproject.toml` entry points group `[project.entry-points."glorious_agents.skills"]`.
  - Example: `acme = "acme_skill.skill:app"`.
  - Acceptance: After `uv pip install acme-skill`, `agent skills reload` lists it.
- [ ] Implement external skill template generator (`agent skills create`).
  - Files: `pyproject.toml`, `skill.py`, `schema.sql`, docs, license.
  - Acceptance: Generated project builds with `uv build`, installs, and loads.

---

## 13) Orchestrator (Optional)

- [ ] Implement `orchestrator.py`.
  - Command: `agent orchestrate --agents a1,a2,a3 --merge --distill`.
  - Acceptance: Aggregates DB content; optional distiller pipeline runs.

---

## 14) Performance

- [ ] Enable SQLite WAL + `PRAGMA synchronous=NORMAL`.
  - Acceptance: Pragmas set at connection init.
- [ ] Batch writes for vacuum/compaction; limit `SELECT` columns in list operations.
  - Acceptance: Profiling shows improved throughput.

---

## 15) Security & Safety

- [ ] Enforce `.agent/` permissions and redact secrets in logs.
  - Acceptance: Windows ACLs applied; sensitive fields omitted.
- [ ] Implement immutable system notes/rules policy at skill layer.
  - Acceptance: Attempts to modify system notes are rejected.

---

## 16) Testing Strategy

- [ ] Set up tests structure.
  - Paths: `tests/unit/`, `tests/integration/`, `tests/conftest.py`.
  - Acceptance: Test discovery works.
- [ ] Unit tests — domain/services with fakes.
  - Example: `tests/unit/test_user_photos.py` pattern adapted for skills.
  - Acceptance: Fast, deterministic tests; marker `@pytest.mark.logic`.
- [ ] Integration tests — real adapters and I/O.
  - Use temp DB; CLI invocations; daemon RPC.
  - Marker `@pytest.mark.integration`.
  - Acceptance: Run separately and pass.
- [ ] Configure coverage threshold in `pyproject.toml`.
  - `--cov-fail-under={COVERAGE_TARGET}`; omit non-domain directories.
  - Acceptance: Fails build if below target.

---

## 17) CI Pipeline (GitHub Actions)

- [ ] Add `.github/workflows/ci.yml` with uv-based jobs.
  - Steps: checkout, setup-python, install uv, `uv sync`, `uv run ruff check .`, `uv run mypy src`, `uv run pytest`.
  - Acceptance: CI green on main; fails on lint/type/coverage errors.
- [ ] Optional matrix for Python versions.
  - Acceptance: Multiple versions tested if desired.

---

## 18) Pre-commit Quality Gates

- [ ] Validate Ruff and MyPy hooks.
  - Command:
    
    ```powershell
    uv run pre-commit run --all-files
    ```
    
  - Acceptance: Hooks auto-fix and report; no blocking issues.

---

## 19) Packaging & Distribution

- [ ] Define `agent` script entry point in `pyproject.toml`.
  - Acceptance: `uv run agent --help` works (via console script).
- [ ] Build and publish (optional).
  - Commands:
    
    ```powershell
    uv build
    uv publish
    ```
    
  - Acceptance: Package builds; publish to chosen index (optional).

---

## 20) Documentation

- [ ] Write `README.md` and skill author guide.
  - Include quickstart, event topic catalog, CLI usage, daemon RPC guide.
  - Acceptance: Docs cover setup, usage, extension.
- [ ] Ensure `.work/agent/notes/analysis-*.md` captures agent design decisions.
  - Acceptance: Notes organized and gitignored.

---

## 21) Rollout (Milestones)

- [ ] v0.1 (MVP): shared DB, loader (local), schema init, notes+issues, context injection, event bus, `agent skills create`, `agent skills list`, daemon `/skills`.
  - Acceptance: End-to-end session from `chat.md` examples works.
- [ ] v0.2: entry point discovery, dependency resolution, `skills describe/export`, base FTS5 in notes, register/use agents, simple RPC.
  - Acceptance: External skills load; describe/export functional.
- [ ] v0.3: planner/linker/cache skills, vacuum/compaction job, telemetry/events-to-DB, orchestrator, optional embeddings.
  - Acceptance: Extended features operational.

---

## 22) Try-It Commands (Windows)

- Install & sync:
  
  ```powershell
  python -m pip install -U uv
  uv sync
  uv run pre-commit install
  ```
  
- Run tests:
  
  ```powershell
  uv run pytest -q
  uv run pytest -m logic -q
  uv run pytest -m integration -q
  ```
  
- Lint & type:
  
  ```powershell
  uv run ruff check .
  uv run mypy src
  ```
  
- Start daemon:
  
  ```powershell
  uv run agent daemon --host 127.0.0.1 --port 8765
  ```
  
- Use CLI:
  
  ```powershell
  uv run agent skills list
  uv run agent skills create notes-ext
  uv run agent notes add "Refactor parser" --tags refactor,parser
  ```
  

---

## Acceptance Criteria Summary

- High coverage (>= `COVERAGE_TARGET`) on domain/services.
- Strict type-check passes (`mypy --strict`).
- Lint clean (Ruff) and formatted.
- CI green across steps; pre-commit hooks effective.
- CLI and daemon expose and load skills; events flow between skills.
- Notes and Issues skills fully functional with persistence and FTS5.
