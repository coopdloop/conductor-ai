"""Basic tests for Conductor platform."""

import pytest


def test_python_version():
    """Test that we're running on a supported Python version."""
    import sys

    assert sys.version_info >= (3, 9), "Python 3.9+ is required"


def test_imports():
    """Test that core modules can be imported."""
    # Test basic imports work
    import os
    import sys
    import json

    assert True  # If we get here, basic imports work


def test_conductor_structure():
    """Test that the conductor package structure exists."""
    import os
    from pathlib import Path

    # Check that src directory exists
    src_dir = Path(__file__).parent.parent / "src"
    assert src_dir.exists(), "src directory should exist"

    # Check that key directories exist
    ai_dir = src_dir / "ai"
    core_dir = src_dir / "core"

    assert ai_dir.exists(), "AI module directory should exist"
    assert core_dir.exists(), "Core module directory should exist"


@pytest.mark.asyncio
async def test_async_support():
    """Test that async functionality works."""
    import asyncio

    async def dummy_async():
        await asyncio.sleep(0.001)
        return "async_works"

    result = await dummy_async()
    assert result == "async_works"