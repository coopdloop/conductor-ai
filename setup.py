#!/usr/bin/env python3
"""Setup script for Conductor - AI-native workflow orchestrator."""

from pathlib import Path

from setuptools import find_packages, setup

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = (
    readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""
)

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="conductor-ai",
    version="2.0.0",
    description="AI-native workflow orchestration platform with persistent context and intelligent automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Conductor Project",
    author_email="conductor@example.com",
    url="https://github.com/your-org/conductor",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Scheduling",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Project Management",
    ],
    keywords="ai workflow automation documentation orchestrator assistant productivity",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.12",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "conductor=conductor:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    zip_safe=False,
    project_urls={
        "Bug Reports": "https://github.com/your-org/conductor/issues",
        "Source": "https://github.com/your-org/conductor",
        "Documentation": "https://github.com/your-org/conductor/blob/main/README.md",
    },
)
