# Glorious Agents Documentation

This directory contains documentation resources for the Glorious Agents framework.

## AGENT-TOOLS.md Generation

The `AGENT-TOOLS.md` file is **dynamically generated** by the `agent init` command.

### How It Works

1. Run `agent init` to generate AGENT-TOOLS.md
2. System scans all **installed skills**
3. For each skill:
   - If `usage.md` exists → includes its content directly
   - If missing → generates basic command list as fallback

### For Skill Developers

To properly document your skill:

1. Create `usage.md` in your skill directory
2. Add to `skill.json`:
   ```json
   {
     "external_doc": "usage.md",
     "internal_doc": "instructions.md"
   }
   ```
3. Write comprehensive documentation

### Only Installed Skills

AGENT-TOOLS.md includes **only successfully loaded skills**.
Skills with errors are automatically skipped.
