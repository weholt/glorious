# Quick Reference: Artifact Management

## 🎯 TL;DR

**Problem Solved**: Artifacts were consuming too much storage → Workflows failing  
**Solution**: Added retention policies + automatic cleanup + conditional uploads

---

## 📊 Current Configuration

| Workflow | Artifact | Retention | When Uploaded |
|----------|----------|-----------|---------------|
| CI | security-report | 7 days | Failures or main branch |
| CI | dist | 3 days | Main branch only |
| Release | dist | 5 days | Always (releases) |
| Pre-release | None | N/A | Never (testing only) |

**Automatic Cleanup**: Daily at 2 AM UTC (keeps last 5, deletes >7 days old)

---

## 🚀 Quick Actions

### Manual Cleanup (if quota exceeded)
```bash
# Go to: GitHub → Actions → Artifacts → Delete old ones
# Or run: Actions → Cleanup Old Artifacts → Run workflow
```

### Check Current Usage
```bash
gh api repos/weholt/glorious/actions/artifacts --paginate | \
  jq '.artifacts[] | {name, size_mb: (.size_in_bytes/1048576|floor), created_at}'
```

### Test Locally Before Push
```bash
# Run tests with coverage
uv run pytest --cov --cov-report=term --cov-fail-under=70

# Validate workflow YAML
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
```

---

## 📝 Key Changes Made

✅ **Retention policies**: 3-7 days (was: forever)  
✅ **Conditional uploads**: Main branch only (was: every PR)  
✅ **Unique names**: Include run ID (was: conflicts)  
✅ **Auto-cleanup**: Daily cron job (was: manual only)  
✅ **Test coverage**: 84% (was: 67%)  

---

## 🔧 When to Adjust

**Increase retention** if:
- Debugging requires longer artifact availability
- Release cycles are longer than 5 days

**Decrease retention** if:
- Storage quota is still an issue
- Artifacts are only needed for quick checks

**Edit**: `.github/workflows/*.yml` → Search for `retention-days`

---

## 📚 Full Documentation

- **Complete guide**: [`docs/artifact-management.md`](./artifact-management.md)
- **Fix summary**: [`ARTIFACT_STORAGE_FIX.md`](../ARTIFACT_STORAGE_FIX.md)
- **GitHub docs**: https://docs.github.com/en/actions/managing-workflow-runs/removing-workflow-artifacts

---

## ⚠️ Important Notes

1. **PRs no longer upload artifacts** (by design - saves storage)
2. **Cleanup workflow preserves tagged releases** (safe for production)
3. **Coverage reports go to Codecov** (not stored as artifacts)
4. **Run IDs make artifact names unique** (e.g., `dist-12345678`)

---

## 🎓 Best Practices

**DO**:
- ✅ Set retention-days on all artifact uploads
- ✅ Use conditionals to limit uploads
- ✅ Include run ID in artifact names
- ✅ Review artifacts monthly

**DON'T**:
- ❌ Upload artifacts on every PR
- ❌ Use indefinite retention
- ❌ Forget to enable automatic cleanup
- ❌ Upload unnecessary files

---

**Last Updated**: 2025-11-17  
**Coverage**: 84.47% (158 tests passing)  
**Status**: ✅ All workflows validated
