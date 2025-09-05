#!/usr/bin/env python3
"""
Step 3: PDF Generation
Wrapper around the existing build_resume.py script for the 3-step pipeline.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Generate PDF resume from optimized JSON (Step 3 of pipeline)"
    )
    parser.add_argument(
        "optimized_resume",
        type=str,
        help="Path to optimized resume JSON from step 2"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/resume.pdf",
        help="Output path for generated PDF"
    )

    args = parser.parse_args()

    # Validate input file exists
    optimized_resume_path = Path(args.optimized_resume)
    if not optimized_resume_path.exists():
        print(
            f"Error: Optimized resume file not found: {optimized_resume_path}")
        return 1

    # Get the directory containing this script
    script_dir = Path(__file__).parent
    build_script = script_dir / "build_resume.py"

    if not build_script.exists():
        print(f"Error: build_resume.py not found at: {build_script}")
        return 1

    # Call the existing build_resume.py script
    cmd = [
        sys.executable,
        str(build_script),
        str(optimized_resume_path),
        "--out", args.output
    ]

    print(f"Generating PDF: {args.output}")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
        print(f"\nPDF generated successfully: {args.output}")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error generating PDF: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return 1


if __name__ == "__main__":
    exit(main())
