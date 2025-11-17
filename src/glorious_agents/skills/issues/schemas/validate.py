#!/usr/bin/env python3
"""Validate issue import JSON against schema.

Usage:
    python validate.py <json-file>
    python validate.py example-auth-system.json
"""

import json
import sys
from pathlib import Path

from jsonschema import validate, ValidationError


def load_schema() -> dict:
    """Load the issue import schema."""
    schema_path = Path(__file__).parent / "issue-import-schema.json"
    with open(schema_path) as f:
        return json.load(f)


def validate_file(json_file: str | Path) -> bool:
    """Validate a JSON file against the schema.
    
    Args:
        json_file: Path to JSON file to validate
        
    Returns:
        True if valid, False otherwise
    """
    schema = load_schema()
    
    try:
        with open(json_file) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ File not found: {json_file}")
        return False
    
    try:
        validate(instance=data, schema=schema)
        print(f"✅ Valid! File conforms to issue import schema")
        
        # Print summary
        print(f"\n📊 Summary:")
        print(f"   Project ID: {data.get('project_id')}")
        print(f"   Total items: {len(data.get('items', []))}")
        
        # Count by type
        items = data.get('items', [])
        types = {}
        for item in items:
            item_type = item.get('type', 'unknown')
            types[item_type] = types.get(item_type, 0) + 1
        
        if types:
            print(f"   By type:")
            for type_name, count in sorted(types.items()):
                print(f"     - {type_name}: {count}")
        
        return True
        
    except ValidationError as e:
        print(f"❌ Validation failed:")
        print(f"   Path: {' > '.join(str(p) for p in e.path)}")
        print(f"   Error: {e.message}")
        return False


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python validate.py <json-file>")
        print("\nExample:")
        print("  python validate.py example-auth-system.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    success = validate_file(json_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
