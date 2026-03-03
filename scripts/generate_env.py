#!/usr/bin/env python3
"""
WARNING: DO NOT USE THE SCRIPT!
This script is used to set env for remote AI agent.

Generate .env file from .env.example
Extract all environment variable names and create an empty .env file
"""

import os
import re
import shutil
from pathlib import Path


def extract_env_vars(env_example_path: str) -> list[str]:
    """
    Extract environment variable names from .env.example file

    Args:
        env_example_path: Path to .env.example file

    Returns:
        List of environment variable names
    """
    env_vars = []

    with open(env_example_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comment lines
            if not line or line.startswith("#"):
                continue

            # Match variable name (part before equals sign)
            match = re.match(r"^([A-Z0-9_]+)\s*=", line)
            if match:
                env_vars.append(match.group(1))

    return env_vars


def generate_env_file(env_vars: list[str], output_path: str) -> None:
    """
    Generate .env file

    Args:
        env_vars: List of environment variable names
        output_path: Output file path
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Generated from .env.example\n")
        f.write("# Fill in the values for your environment\n\n")

        for var in env_vars:
            f.write(f"{var}={os.getenv(var, '')}\n")

    print(f"✓ Generated {output_path} successfully")
    print(f"  Extracted {len(env_vars)} environment variables")


def main():
    """Main function"""
    env_example_path = ".env.example"
    output_path = ".env"

    # Check if .env.example exists
    if not Path(env_example_path).exists():
        print(f"✗ Error: {env_example_path} file not found")
        return

    # Check if .env already exists
    if Path(output_path).exists():
        print(f"⚠ Warning: {output_path} already exists")
        # Backup existing file
        shutil.copy2(".env", ".env.bak")
        print("✓ Backed up existing file to .env.bak")

    # Extract environment variable names
    env_vars = extract_env_vars(env_example_path)

    if not env_vars:
        print("✗ No environment variables found")
        return

    # Generate .env file
    generate_env_file(env_vars, output_path)


if __name__ == "__main__":
    main()
