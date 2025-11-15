# Glorious Agents — Step-by-Step Implementation Plan (Skills Framework)

## 0) Outcomes

* Modular CLI where each capability is a **discoverable skill** (notes, issues, cache, planner, linker, etc.).
* **Shared per-agent SQLite DB** (one DB per active agent; all skills share it).
* **Auto-init schemas** from skills; **auto-discovery** from local folders and pip/uv entry points.
* **Background daemon** (FastAPI/Uvicorn) for long-running efficiency + optional RPC.
* **Dependency graph** for skills (`requires`), **runtime context injection**, **event bus** for inter-skill reuse.
* Scaffolding: `agent skills create <name>` (local) and external plugin template.

---

## 1) Repo Layout

```
glorious_agents/
  cli.py
  pyproject.toml
  agent_schema.sql              # base tables (optional)
  core/
    db.py                       # shared DB connection + pragmas
    loader.py                   # discover, resolve deps, load skills
    registry.py                 # in-proc registry
    runtime.py                  # singleton SkillContext
    context.py                  # EventBus + SkillContext
    daemon.py                   # FastAPI service
  skills_cli.py                 # manage/reload/create/export skills
  skills/
    notes/
      skill.json                # manifest (entry_point, requires, schema_file, docs)
      schema.sql                # per-skill schema
      skill.py                  # Typer app + callable API + init_context(ctx)
      instructions.md           # internal (agent)
      usage.md                  # external (human)
    issues/
      ...
  orchestrator.py               # optional: parallel run, aggregate, distill
```

---

## 2) Base Dependencies

* Python 3.11+, Typer, Rich, FastAPI, Uvicorn.
* SQLite (builtin) + FTS5 (enabled in system sqlite).
* Optional: `sqlite-vss` or external vector DB later.

**Install (dev):** `uv pip install -e .`

---

## 3) Shared Database (per active agent)

* Active agent code lives in `~/.agent/active_agent`.
* DB path: `~/.agent/agents/<code>/agent.db`.
* One DB per agent; all skills share this DB.

**`core/db.py`**

* `get_agent_db_path()` → resolves/creates DB.
* `get_connection(check_same_thread=False)`; set `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`.
* `init_skill_schema(skill_name, schema_path)` → exec schema per skill.

---

## 4) Skill Manifests

**`skills/<name>/skill.json`**

```json
{
  "name": "notes",
  "version": "0.1.0",
  "description": "Persistent notes.",
  "entry_point": "glorious_agents.skills.notes.skill:app",
  "schema_file": "schema.sql",
  "requires": ["issues"],        // optional
  "requires_db": true,
  "internal_doc": "instructions.md",
  "external_doc": "usage.md"
}
```

---

## 5) Skill Discovery + Dependency Resolution

**`core/loader.py`**

1. `discover_local_skills()` → scan `skills/*/skill.json`.
2. `discover_entrypoint_skills("glorious_agents.skills")` → load pip/uv plugins (entry points).
3. Merge local+entrypoint (local wins on name).
4. `resolve_dependencies(skills)` → topological sort by `requires` (error on missing/cycles).
5. `init_schemas(sorted_skills)` → run each `schema.sql` once at startup.
6. `load_skill_entry(entry_point)` → import module, return Typer app; if module defines `init_context(ctx)`, call it.

---

## 6) Runtime Context + Event Bus

**`core/context.py`**

* `EventBus` (in-proc pub/sub; thread-backed).
* `SkillContext`: shared DB connection, `publish/subscribe`, `get_skill(name)` to access another skill app, process-local cache.

**`core/runtime.py`**

* `get_ctx()` returns singleton `SkillContext`.

**Context injection**

* Loader detects `init_context(ctx)` in module and calls it with `get_ctx()`.

---

## 7) Skill Coding Pattern

* Typer app for CLI + optional **callable functions** for programmatic reuse.
* Emit/subscribe to events for loose coupling.

**Example: notes**

```python
# skills/notes/skill.py
app = typer.Typer(help="Notes"); _ctx=None
def init_context(ctx): 
  global _ctx; _ctx=ctx
def add_note(content:str,tags:str="")->int:
  conn=get_connection()
  cur=conn.execute("INSERT INTO notes(content,tags) VALUES(?,?)",(content,tags))
  conn.commit(); nid=cur.lastrowid
  _ctx.publish("note_created", {"id":nid,"tags":tags})
  return nid
@app.command("add")
def add(content:str,tags:str=""): nid=add_note(content,tags); print(f"Note {nid} added")
```

**Example: issues depends on notes**

```python
# skills/issues/skill.py
def init_context(ctx):
  ctx.subscribe("note_created", lambda d: create_issue(f"Follow-up for note {d['id']}", "Auto"))
def create_issue(title,desc)->int: ...; return issue_id
```

---

## 8) CLI Root + Skills Management

**`cli.py`**

* Typer root `agent`.
* On import: `discover_skills` → `resolve_dependencies` → `init_schemas` → `load_skill_entry` (+ `init_context`) → `app.add_typer(entry, name=<skill_name>)`.

**`skills_cli.py`** (`agent skills ...`)

* `agent skills reload` → re-run discovery/init/load.
* `agent skills list` → table with name/version/origin/reqs.
* `agent skills describe <skill>` → manifest + docs.
* `agent skills export --format json|md`.
* `agent skills create <name>` → scaffold skill folder (manifest+schema+docs+skill.py).

**One-liners**

* Reload: `agent skills reload`
* List: `agent skills list`
* Create: `agent skills create acme-skill`

---

## 9) Daemon (efficiency + RPC)

**`core/daemon.py`**

* FastAPI app, `/skills` to enumerate loaded skills.
* `startup`: discover → resolve deps → init schemas → load + inject context.
* Optional RPC: `/rpc/{skill}/{method}` to invoke callable API methods (JSON params).
* Run: `agent daemon --host 127.0.0.1 --port 8765`.

**One-liners**

* Start: `agent daemon --host 127.0.0.1 --port 8765`
* Check: `curl http://127.0.0.1:8765/skills`

---

## 10) Per-Agent Identity (optional but recommended)

* Global registry `~/.agent/master.db` with agents (name, code, role, db_path).
* Commands: `agent register --name <n>`, `agent use <name>`, `agent whoami`, `agent list`.
* When switching active agent, all skills automatically use the new DB.

**One-liners**

* Register: `agent register --name planner --role "Task Planner" --project-id proj`
* Use: `agent use planner`
* Whoami: `agent whoami`

---

## 11) Orchestration (optional)

* `agent-orchestrator orchestrate --agents a1,a2,a3 --merge --distill`.
* `aggregate`: merge DB objects into a temporary or new agent DB (preserve provenance).
* `distill`: LLM summarization/compaction into a “distiller” agent; produce unified prioritized plan.

---

## 12) Search + FTS + (Optional) Vectors

* Use FTS5 virtual tables + triggers for skills that store text (notes, issues, docs).
* Add optional `note_embeddings` when needed; hybrid ranking (BM25 + ANN) later.

---

## 13) Skill Dependencies — Enforcement

* Loader fails fast if `requires` missing or cycle detected.
* Present clear error: which dependency not found / version mismatch (optional semver in future).
* `agent skills list` shows dependency graph; `agent skills describe` displays `requires`.

---

## 14) External Skills (pip/uv plugins)

* Support entry points: `[project.entry-points."glorious_agents.skills"]`

  * e.g., `acme = "acme_skill.skill:app"`
* After install: `agent skills reload` → auto-loaded.
* Daemon startup also picks them up.

**External template includes:**

* `pyproject.toml`, `skill.py`, `schema.sql`, `instructions.md`, `usage.md`, MIT license, GitHub CI (optional).

---

## 15) Event Bus Patterns

* Canonical topics: `note_created`, `issue_created`, `issue_updated`, `plan_enqueued`, `scan_ready`, `vacuum_done`.
* Skills subscribe to topics relevant to their workflow.
* Use small payloads (IDs + tags); fetch heavy data from DB by ID.

---

## 16) Security + Safety

* Daemon binds to `127.0.0.1` by default; optional token for RPC.
* `.agent/` permissions 0700; redact secrets in logs.
* System notes / rule notes: immutable policy enforced at skill layer.

---

## 17) Performance

* SQLite WAL + in-proc shared connection.
* Batch writes for vacuum/compaction; limit `SELECT` columns on list.
* Add per-skill read/write indices; FTS5 for text.

---

## 18) Testing

* Unit: loader (deps, manifest), db init, event bus, context injection.
* Integration: CLI load → skill commands → DB assertions.
* Contract tests for skill API callables (e.g., `create_issue`, `add_note`).
* E2E: start daemon → call RPC → verify DB + events.

**One-liners**

* Run tests: `pytest -q`
* Lint: `ruff check .`

---

## 19) Packaging & Distribution

* `pyproject.toml` declares `agent` script entry point.
* External skill template ready for `uv build` / `uv publish`.
* Semver versioning for core + skill manifests.

---

## 20) Rollout Plan

1. **Core**: db.py, registry.py, context.py (EventBus), runtime.py.
2. **Loader**: discovery (local + entry point), dep resolve, schema init, context injection.
3. **CLI**: `agent` root; mount `skills_cli`; autoload skills; `register/use/whoami` (optional).
4. **Daemon**: FastAPI app; `/skills`; optional `/rpc/{skill}/{method}`.
5. **Skills**: implement `notes` and `issues` as reference (with FTS + events).
6. **Scaffold**: `agent skills create` generator; external plugin template.
7. **Orchestrator** (optional): parallel runs, aggregate, distill.
8. **Docs**: README, skill author guide, event topic catalog.

---

## 21) Minimal Milestones

### v0.1 (MVP)

* Shared DB, loader (local), schema init, notes+issues skills, context injection, event bus, `agent skills create`, `agent skills list`, daemon `/skills`.

### v0.2

* Entry point discovery (pip/uv), dependency resolution, `skills describe/export`, base FTS5 in notes, register/use agents, simple RPC.

### v0.3

* Planner/linker/cache skills, vacuum/compaction job, telemetry/events-to-DB, orchestrator (aggregate/distill), optional embeddings.

---

## 22) Example End-to-End Session (one-liners)

* Create + load skills: `agent skills create notes-ext && agent skills reload`
* Start daemon: `agent daemon --host 127.0.0.1 --port 8765`
* Register + activate agent: `agent register --name dev --role "Developer" --project-id demo && agent use dev`
* Add note: `agent notes add "Refactor parser" --tags refactor,parser`
* Auto issue via subscription (issues skill listening to `note_created`).
* List skills: `agent skills list`
* Describe notes: `agent skills describe notes`
* Orchestrate (optional): `agent-orchestrator orchestrate --agents a1,a2 --merge --distill`

---