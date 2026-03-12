#!/usr/bin/env python3
"""
Enhanced Conductor - CLI Entry Point

Main entry point for the conductor CLI when installed as a package.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import conductor.py
conductor_root = Path(__file__).parent.parent
sys.path.insert(0, str(conductor_root))

# Import the CLI from the main conductor.py file
try:
    from conductor import cli
except ImportError as e:
    print(f"Error importing conductor CLI: {e}")
    print("Please ensure conductor is properly installed.")
    sys.exit(1)

if __name__ == "__main__":
    cli()