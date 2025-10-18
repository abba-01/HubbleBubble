"""
JSON Schema Validation for HubbleBubble outputs

Ensures all result files have required fields with correct types.
"""
import json
import sys
from pathlib import Path
from jsonschema import validate, ValidationError

LOAO_SCHEMA = {
    "type": "object",
    "required": ["scenarios", "max_z_planck", "gate_a_engineering", "gate_b_sidak"],
    "properties": {
        "scenarios": {"type": "object"},
        "max_z_planck": {"type": "number"},
        "gate_a_engineering": {
            "type": "object",
            "required": ["threshold", "passed"],
            "properties": {
                "threshold": {"type": "number"},
                "passed": {"type": "boolean"}
            }
        },
        "gate_b_sidak": {
            "type": "object",
            "required": ["alpha", "K", "threshold", "passed"],
            "properties": {
                "alpha": {"type": "number"},
                "K": {"type": "integer"},
                "threshold": {"type": "number"},
                "passed": {"type": "boolean"}
            }
        }
    }
}

BOOTSTRAP_SCHEMA = {
    "type": "object",
    "required": ["n_iterations", "statistics", "gate", "passed"],
    "properties": {
        "n_iterations": {"type": "integer"},
        "statistics": {"type": "object"},
        "gate": {"type": "number"},
        "passed": {"type": "boolean"}
    }
}

GRID_SCHEMA = {
    "type": "object",
    "required": ["grid", "surface"],
    "properties": {
        "grid": {"type": "object"},
        "surface": {"type": "array"}
    }
}

INJECT_SCHEMA = {
    "type": "object",
    "required": ["n_trials", "statistics", "gates", "passed"],
    "properties": {
        "n_trials": {"type": "integer"},
        "statistics": {"type": "object"},
        "gates": {"type": "object"},
        "passed": {"type": "boolean"}
    }
}

def validate_file(filepath, schema, name):
    """Validate a JSON file against a schema"""
    try:
        with open(filepath) as f:
            data = json.load(f)
        validate(instance=data, schema=schema)
        print(f"✓ {name}: Schema valid")
        return True
    except FileNotFoundError:
        print(f"✗ {name}: File not found: {filepath}")
        return False
    except ValidationError as e:
        print(f"✗ {name}: Validation error: {e.message}")
        return False
    except Exception as e:
        print(f"✗ {name}: Error: {e}")
        return False

def main():
    """Validate all output JSONs"""
    results_dir = Path("outputs/results")

    tests = [
        (results_dir / "loao.json", LOAO_SCHEMA, "LOAO"),
        (results_dir / "bootstrap.json", BOOTSTRAP_SCHEMA, "Bootstrap"),
        (results_dir / "grids.json", GRID_SCHEMA, "Grid-scan"),
        (results_dir / "inject.json", INJECT_SCHEMA, "Injection")
    ]

    all_passed = True
    for filepath, schema, name in tests:
        if not validate_file(filepath, schema, name):
            all_passed = False

    if all_passed:
        print("\n✓ All schemas validated")
        return 0
    else:
        print("\n✗ Some schemas failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
