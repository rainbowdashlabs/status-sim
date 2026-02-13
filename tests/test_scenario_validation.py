"""Test script to validate all scenario JSON files using Pydantic models."""

import json
import sys
from pathlib import Path
from typing import List, Tuple

# Add src to path to import scenario_models
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scenario_models import Scenario


def find_scenario_files(scenarios_dir: Path) -> List[Path]:
    """Find all scenario JSON files in the scenarios directory."""
    return sorted(scenarios_dir.glob("scenario_*.json"))


def validate_scenario_file(file_path: Path) -> Tuple[bool, str]:
    """
    Validate a single scenario file.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate using Pydantic model
        scenario = Scenario(**data)
        
        return True, f"✓ {file_path.name}: Valid"
    
    except json.JSONDecodeError as e:
        return False, f"✗ {file_path.name}: JSON syntax error - {e}"
    
    except Exception as e:
        return False, f"✗ {file_path.name}: Validation error - {e}"


def main():
    """Main validation function."""
    # Find scenarios directory
    project_root = Path(__file__).parent.parent
    scenarios_dir = project_root / "src" / "static" / "scenarios"
    
    if not scenarios_dir.exists():
        print(f"Error: Scenarios directory not found at {scenarios_dir}")
        sys.exit(1)
    
    # Find all scenario files
    scenario_files = find_scenario_files(scenarios_dir)
    
    if not scenario_files:
        print(f"Warning: No scenario files found in {scenarios_dir}")
        sys.exit(0)
    
    print(f"Found {len(scenario_files)} scenario files to validate\n")
    
    # Validate each file
    results = []
    for file_path in scenario_files:
        success, message = validate_scenario_file(file_path)
        results.append((success, message))
        print(message)
    
    # Summary
    successful = sum(1 for success, _ in results if success)
    failed = len(results) - successful
    
    print(f"\n{'='*60}")
    print(f"Validation Summary:")
    print(f"  Total files: {len(results)}")
    print(f"  ✓ Valid: {successful}")
    print(f"  ✗ Invalid: {failed}")
    print(f"{'='*60}")
    
    # Exit with error code if any validation failed
    if failed > 0:
        sys.exit(1)
    else:
        print("\n✓ All scenario files are valid!")
        sys.exit(0)


if __name__ == "__main__":
    main()
