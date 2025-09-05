#!/usr/bin/env python3
"""
Test script for the resume generation pipeline.
Tests Step 1 (relevance filtering) without requiring OpenAI API key.
"""

import subprocess
import sys
from pathlib import Path


def test_step1():
    """Test Step 1: Relevance filtering."""
    print("🧪 Testing Step 1: Relevance Filtering")

    script_dir = Path(__file__).parent
    step1_script = script_dir / "step1_relevance_filter.py"
    job_desc = script_dir.parent / "job-applications" / "example_software_engineer.txt"

    if not job_desc.exists():
        print(f"❌ Job description not found: {job_desc}")
        return False

    cmd = [
        sys.executable,
        str(step1_script),
        str(job_desc),
        "--output", "intermediate-outputs/test_step1_output.json"
    ]

    try:
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True)
        print("✅ Step 1 completed successfully")
        print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Step 1 failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def test_pipeline_help():
    """Test that the main pipeline script shows help."""
    print("🧪 Testing Pipeline Help")

    script_dir = Path(__file__).parent
    pipeline_script = script_dir / "resume_pipeline.py"

    cmd = [sys.executable, str(pipeline_script), "--help"]

    try:
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True)
        print("✅ Pipeline help works")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Pipeline help failed: {e}")
        return False


def main():
    print("🚀 Testing Resume Generation Pipeline")
    print("=" * 50)

    success = True

    # Test pipeline help
    if not test_pipeline_help():
        success = False

    print()

    # Test step 1
    if not test_step1():
        success = False

    print()
    print("=" * 50)
    if success:
        print("🎉 All tests passed!")
        print("\nNext steps:")
        print("1. Set your OpenAI API key: export OPENAI_API_KEY='your-key'")
        print("2. Run the full pipeline: python scripts/resume_pipeline.py job-applications/example_software_engineer.txt")
    else:
        print("❌ Some tests failed. Check the output above.")

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
