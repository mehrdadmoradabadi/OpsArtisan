"""Setup configuration for OpsArtisan."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""

setup(
    name="opsartisan",
    version="2.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="CLI-first assistant for sysadmins and DevOps engineers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/opsartisan",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Code Generators",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "jinja2>=3.0.0",
        "pyyaml>=5.4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "interactive": [
            "questionary>=1.10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "opsartisan=opsartisan.cli:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)