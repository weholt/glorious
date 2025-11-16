## Issue Creation Workflow - Best Practices

### Problem: Long descriptions fail when passed directly via command line

PowerShell has limitations parsing long multi-line strings in command arguments.

### Solution: File-Based Descriptions

**Step 1: Create description file**
```powershell
# Save description to temp file
$content | Out-File .work/agent/temp/desc-<issue-id>.txt -Encoding UTF8
```

**Step 2: Load and apply**
```powershell
$desc = Get-Content .work/agent/temp/desc-<issue-id>.txt -Raw
uv run issues update <issue-id> -d $desc
```

**Step 3: Verify with JSON output**
```powershell
uv run issues show <issue-id> --json | ConvertFrom-Json | Select-Object description
```

### Why This Works

- Avoids PowerShell quote escaping issues
- Handles arbitrary length text
- Preserves formatting (newlines, markdown)
- `-Raw` parameter loads entire file as single string

### Current Limitation

The `issues show` command's default output doesn't display descriptions.  
**Workaround:** Use `--json` flag to see full data:
```powershell
uv run issues show issue-123 --json
```

See enhancement issue for fixing this UX problem.
