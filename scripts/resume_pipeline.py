#!/usr/bin/env python3
"""
Resume Generation Pipeline
Orchestrates the 4-step resume optimization and generation process:
1. Relevance filtering based on job description
2. LLM optimization for better alignment
3. PDF generation using LaTeX templates
4. Cover letter generation (optional)
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_step(script_name: str, args: list, step_name: str) -> bool:
    """Run a pipeline step and return success status."""
    script_path = Path(__file__).parent / script_name
    cmd = [sys.executable, str(script_path)] + args

    print(f"\n{'='*60}")
    print(f"STEP: {step_name}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, check=True)
        print(f"✅ {step_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {step_name} failed with exit code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Run the complete resume generation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline
  python resume_pipeline.py job-applications/software-engineer.txt
  
  # Run complete pipeline with cover letter
  python resume_pipeline.py job-applications/software-engineer.txt --generate-cover-letter
  
  # Run only step 1 (relevance filtering)
  python resume_pipeline.py job-applications/software-engineer.txt --step 1
  
  # Run steps 2-3 (optimization + PDF generation)
  python resume_pipeline.py job-applications/software-engineer.txt --step 2-3
  
  # Run all steps including cover letter
  python resume_pipeline.py job-applications/software-engineer.txt --step 1-4
  
  # Custom output paths and company name
  python resume_pipeline.py job-applications/job.txt --output-dir custom-outputs --company-name "Google"
        """
    )

    parser.add_argument(
        "job_description",
        type=str,
        help="Path to job description text file"
    )
    parser.add_argument(
        "--step",
        type=str,
        choices=["1", "2", "3", "4", "1-2", "2-3", "3-4", "1-3", "1-4", "all"],
        default="all",
        help="Which step(s) to run (default: all)"
    )
    parser.add_argument(
        "--source-dir",
        type=str,
        default="about-me",
        help="Directory containing source resume JSON files"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="intermediate-outputs",
        help="Directory for intermediate outputs"
    )
    parser.add_argument(
        "--final-output",
        type=str,
        help="Final PDF output path (default: output/resume_TIMESTAMP.pdf)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key for step 2 (or set OPENAI_API_KEY environment variable)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip LLM calls in step 2 (for testing)"
    )
    parser.add_argument(
        "--max-experiences",
        type=int,
        default=3,
        help="Maximum experiences to include (step 1)"
    )
    parser.add_argument(
        "--max-projects",
        type=int,
        default=2,
        help="Maximum projects to include (step 1)"
    )
    parser.add_argument(
        "--concise",
        action="store_true",
        help="Generate more concise resume (fewer bullet points, shorter content)"
    )
    parser.add_argument(
        "--generate-cover-letter",
        action="store_true",
        help="Generate cover letter along with resume (step 4)"
    )
    parser.add_argument(
        "--company-name",
        type=str,
        help="Company name for cover letter (extracted from job description if not provided)"
    )

    args = parser.parse_args()

    # Validate job description file
    job_desc_path = Path(args.job_description)
    if not job_desc_path.exists():
        print(f"Error: Job description file not found: {job_desc_path}")
        return 1

    # Setup output paths
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_name = job_desc_path.stem

    step1_output = output_dir / f"{job_name}_step1_filtered_{timestamp}.json"
    step2_output = output_dir / f"{job_name}_step2_optimized_{timestamp}.json"

    if args.final_output:
        final_output = args.final_output
    else:
        final_output = f"output/{job_name}_resume_{timestamp}.pdf"

    # Cover letter output path
    cover_letter_output = f"output/{job_name}_cover_letter_{timestamp}.pdf"

    # Determine which steps to run
    steps_to_run = []
    if args.step == "all":
        steps_to_run = ["1", "2", "3"]
        if args.generate_cover_letter:
            steps_to_run.append("4")
    elif args.step == "1-4":
        steps_to_run = ["1", "2", "3", "4"]
    elif args.step == "1-3":
        steps_to_run = ["1", "2", "3"]
    elif args.step == "1-2":
        steps_to_run = ["1", "2"]
    elif args.step == "2-3":
        steps_to_run = ["2", "3"]
    elif args.step == "3-4":
        steps_to_run = ["3", "4"]
    elif "-" not in args.step:
        steps_to_run = [args.step]

    print(f"🚀 Starting Resume Generation Pipeline")
    print(f"Job Description: {job_desc_path}")
    print(f"Steps to run: {', '.join(steps_to_run)}")
    print(f"Final Output: {final_output}")

    success = True

    # Step 1: Relevance Filtering
    if "1" in steps_to_run:
        step1_args = [
            str(job_desc_path),
            "--source-dir", args.source_dir,
            "--output", str(step1_output),
            "--max-experiences", str(args.max_experiences),
            "--max-projects", str(args.max_projects)
        ]

        if args.api_key:
            step1_args.extend(["--api-key", args.api_key])

        if args.dry_run:
            step1_args.append("--dry-run")

        success = run_step("step1_relevance_filter.py",
                           step1_args, "Step 1: LLM-Based Relevance Filtering")
        if not success:
            return 1

    # Step 2: LLM Optimization
    if "2" in steps_to_run and success:
        # Determine input file for step 2
        if "1" in steps_to_run:
            step2_input = str(step1_output)
        else:
            # Look for existing step 1 output
            existing_files = list(output_dir.glob(
                f"{job_name}_step1_filtered_*.json"))
            if existing_files:
                step2_input = str(sorted(existing_files)
                                  [-1])  # Use most recent
                print(f"Using existing step 1 output: {step2_input}")
            else:
                print(
                    "Error: No step 1 output found. Run step 1 first or provide existing filtered resume.")
                return 1

        step2_args = [
            step2_input,
            str(job_desc_path),
            "--output", str(step2_output)
        ]

        if args.api_key:
            step2_args.extend(["--api-key", args.api_key])

        if args.dry_run:
            step2_args.append("--dry-run")

        if args.concise:
            step2_args.append("--concise")

        success = run_step("step2_llm_optimize.py",
                           step2_args, "Step 2: LLM Optimization")
        if not success:
            return 1

    # Step 3: PDF Generation
    if "3" in steps_to_run and success:
        # Determine input file for step 3
        if "2" in steps_to_run:
            step3_input = str(step2_output)
        else:
            # Look for existing step 2 output
            existing_files = list(output_dir.glob(
                f"{job_name}_step2_optimized_*.json"))
            if existing_files:
                step3_input = str(sorted(existing_files)
                                  [-1])  # Use most recent
                print(f"Using existing step 2 output: {step3_input}")
            else:
                print(
                    "Error: No step 2 output found. Run steps 1-2 first or provide existing optimized resume.")
                return 1

        step3_args = [
            step3_input,
            "--output", final_output
        ]

        success = run_step("step3_generate_pdf.py",
                           step3_args, "Step 3: PDF Generation")
        if not success:
            return 1

    # Step 4: Cover Letter Generation (optional)
    if "4" in steps_to_run and success:
        # Determine input file for step 4 (needs step 2 output)
        if "2" in steps_to_run:
            step4_input = str(step2_output)
        else:
            # Look for existing step 2 output
            existing_files = list(output_dir.glob(
                f"{job_name}_step2_optimized_*.json"))
            if existing_files:
                step4_input = str(sorted(existing_files)
                                  [-1])  # Use most recent
                print(
                    f"Using existing step 2 output for cover letter: {step4_input}")
            else:
                print(
                    "Error: No step 2 output found for cover letter generation. Run steps 1-2 first.")
                return 1

        step4_args = [
            step4_input,
            str(job_desc_path),
            "--output", cover_letter_output
        ]

        if args.api_key:
            step4_args.extend(["--api-key", args.api_key])

        if args.company_name:
            step4_args.extend(["--company-name", args.company_name])

        if args.dry_run:
            step4_args.append("--dry-run")

        success = run_step("step4_generate_cover_letter.py",
                           step4_args, "Step 4: Cover Letter Generation")
        if not success:
            return 1

    if success:
        print(f"\n🎉 Pipeline completed successfully!")
        print(f"📄 Final resume: {final_output}")

        if "4" in steps_to_run:
            print(f"📝 Cover letter: {cover_letter_output}")

        # Show intermediate files
        if step1_output.exists():
            print(f"📋 Filtered resume: {step1_output}")
        if step2_output.exists():
            print(f"✨ Optimized resume: {step2_output}")

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
