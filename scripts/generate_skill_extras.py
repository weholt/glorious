#!/usr/bin/env python3
"""Generate pyproject.toml extras for skills."""
from pathlib import Path

skills_dir = Path("src/glorious_agents/skills")
skills = []

for pyproject in sorted(skills_dir.glob("*/pyproject.toml")):
    skill_name = pyproject.parent.name
    rel_path = pyproject.parent.relative_to(Path.cwd())
    skills.append((skill_name, rel_path))

print("# Individual skills")
for name, path in skills:
    print(f'{name} = ["{{{path}}}"]')

print("\n# Convenience group")
print("all-skills = [")
for name, path in skills:
    print(f'    "{{{path}}}",')
print("]")
