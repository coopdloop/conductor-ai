#!/usr/bin/env python3
"""Main entry point for conductor CLI when installed as a package."""

import os
import sys
from pathlib import Path

# Add the conductor directory to Python path
conductor_dir = Path(__file__).parent.parent
sys.path.insert(0, str(conductor_dir))

# Import and run the main CLI
try:
    # Try to import from the root conductor.py file
    conductor_script = conductor_dir / "conductor.py"
    if conductor_script.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("conductor", conductor_script)
        conductor_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(conductor_module)
        cli = conductor_module.cli
    else:
        print("Error: Could not find conductor.py", file=sys.stderr)
        sys.exit(1)
except Exception as e:
    print(f"Error importing conductor: {e}", file=sys.stderr)
    sys.exit(1)


def main():
    """Main entry point for the conductor command."""
    cli()


if __name__ == "__main__":
    main()