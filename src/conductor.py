#!/usr/bin/env python3
"""
Re-export conductor CLI from the root directory
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import conductor.py
conductor_root = Path(__file__).parent.parent
sys.path.insert(0, str(conductor_root))

# Import the CLI function specifically to avoid circular imports
import importlib.util

spec = importlib.util.spec_from_file_location("conductor_main", conductor_root / "conductor.py")
conductor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(conductor_module)

# Export the cli function
cli = conductor_module.cli