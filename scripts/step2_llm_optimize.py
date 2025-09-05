#!/usr/bin/env python3
"""
Step 2: LLM Optimization
Uses OpenAI API to make minor tweaks to resume content to better align with job description
while preserving the original meaning and structure.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import time

try:
    import openai
except ImportError:
    print("Missing dependency: openai. Please run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()
except ImportError:
    print("Missing dependency: python-dotenv. Please run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)


def load_json(path: Path) -> dict:
    """Load JSON data from file."""
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: dict, path: Path) -> None:
    """Save JSON data to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def setup_openai_client(api_key: str = None) -> openai.OpenAI:
    """Setup OpenAI client with API key."""
    if api_key:
        return openai.OpenAI(api_key=api_key)
    elif os.getenv('OPENAI_API_KEY'):
        return openai.OpenAI()
    else:
        raise ValueError(
            "OpenAI API key not provided. Set OPENAI_API_KEY environment variable or pass --api-key")


def optimize_bullet_points(client: openai.OpenAI, bullets: List[str], job_description: str, context: str, concise: bool = False, priority: str = None) -> List[str]:
    """Optimize bullet points using OpenAI API."""

    priority_note = ""
    if priority:
        priority_note = f"\n\nNOTE: This is a {priority} priority item. "
        if priority == "high":
            priority_note += "This should always be included and represents a key strength, so ensure optimization maintains strong impact."
        elif priority == "medium":
            priority_note += "This is moderately important and should be optimized for relevance to the job description."
        elif priority == "low":
            priority_note += "This is lower priority and should be optimized to maximize relevance to justify its inclusion."

    prompt = f"""You are helping optimize resume bullet points for a specific job application. 

JOB DESCRIPTION:
{job_description}

CONTEXT: {context}{priority_note}

ORIGINAL BULLET POINTS:
{chr(10).join(f"• {bullet}" for bullet in bullets)}

INSTRUCTIONS:
1. Make MINOR tweaks to better align these bullet points with the job description
2. KEEP BULLET POINTS CONCISE - aim for 1-2 lines maximum per bullet point
3. DO NOT rewrite the bullet points completely - preserve the original meaning and achievements
4. You may:
   - Adjust terminology to match job description language
   - Emphasize relevant skills/technologies mentioned in the job posting
   - Remove unnecessary words while preserving impact
   - Add relevant keywords naturally but concisely
5. DO NOT:
   - Change the core accomplishments or facts
   - Add false information
   - Make bullet points longer than the original
   - Change the number of bullet points

CRITICAL: Keep each bullet point under {"80 characters" if concise else "120 characters"} when possible. Focus on impact over verbosity.
{"EXTRA CONCISE MODE: Remove all unnecessary words. Use strong action verbs. Aim for maximum impact in minimum words." if concise else ""}

Return ONLY the optimized bullet points in the same format, one per line with bullet symbols."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using the more cost-effective model
            messages=[
                {"role": "system", "content": "You are a professional resume writer who makes subtle, targeted improvements to align resume content with job requirements."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent results
            max_tokens=1000
        )

        optimized_text = response.choices[0].message.content.strip()

        # Parse the response back into a list
        optimized_bullets = []
        for line in optimized_text.split('\n'):
            line = line.strip()
            if line and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                # Remove bullet symbol and clean up
                bullet = line[1:].strip()
                if bullet:
                    optimized_bullets.append(bullet)

        # Fallback: if parsing failed, return original
        if len(optimized_bullets) != len(bullets):
            print(
                f"Warning: LLM returned {len(optimized_bullets)} bullets instead of {len(bullets)}. Using original.")
            return bullets

        return optimized_bullets

    except Exception as e:
        print(f"Error optimizing bullet points: {e}")
        return bullets  # Return original on error


def optimize_experience_entry(client: openai.OpenAI, experience: Dict[str, Any], job_description: str, concise: bool = False) -> Dict[str, Any]:
    """Optimize a single experience entry."""
    optimized_exp = experience.copy()

    if 'bullets' in experience and isinstance(experience['bullets'], list):
        context = f"Experience at {experience.get('company', 'Unknown')} as {experience.get('role', 'Unknown')}"
        priority = experience.get('priority')
        optimized_bullets = optimize_bullet_points(
            client,
            experience['bullets'],
            job_description,
            context,
            concise,
            priority
        )
        optimized_exp['bullets'] = optimized_bullets

    return optimized_exp


def optimize_project_entry(client: openai.OpenAI, project: Dict[str, Any], job_description: str, concise: bool = False) -> Dict[str, Any]:
    """Optimize a single project entry."""
    optimized_proj = project.copy()

    if 'bullets' in project and isinstance(project['bullets'], list):
        context = f"Project: {project.get('name', 'Unknown')} using {', '.join(project.get('tech', []))}"
        priority = project.get('priority')
        optimized_bullets = optimize_bullet_points(
            client,
            project['bullets'],
            job_description,
            context,
            concise,
            priority
        )
        optimized_proj['bullets'] = optimized_bullets

    return optimized_proj


def optimize_resume_content(client: openai.OpenAI, resume_data: Dict[str, Any], job_description: str, concise: bool = False) -> Dict[str, Any]:
    """Optimize entire resume content using LLM."""
    optimized_resume = resume_data.copy()

    print("Optimizing resume content with LLM...")

    # Optimize experiences
    if 'experience' in resume_data and isinstance(resume_data['experience'], list):
        optimized_experiences = []
        for i, exp in enumerate(resume_data['experience']):
            print(
                f"  Optimizing experience {i+1}/{len(resume_data['experience'])}: {exp.get('company', 'Unknown')}")
            optimized_exp = optimize_experience_entry(
                client, exp, job_description, concise)
            optimized_experiences.append(optimized_exp)
            time.sleep(0.5)  # Rate limiting
        optimized_resume['experience'] = optimized_experiences

    # Optimize projects
    if 'projects' in resume_data and isinstance(resume_data['projects'], list):
        optimized_projects = []
        for i, proj in enumerate(resume_data['projects']):
            print(
                f"  Optimizing project {i+1}/{len(resume_data['projects'])}: {proj.get('name', 'Unknown')}")
            optimized_proj = optimize_project_entry(
                client, proj, job_description, concise)
            optimized_projects.append(optimized_proj)
            time.sleep(0.5)  # Rate limiting
        optimized_resume['projects'] = optimized_projects

    # Keep other sections unchanged (personal_info, education, skills)
    # These typically don't need LLM optimization

    return optimized_resume


def main():
    parser = argparse.ArgumentParser(
        description="Optimize resume content using LLM based on job description"
    )
    parser.add_argument(
        "filtered_resume",
        type=str,
        help="Path to filtered resume JSON from step 1"
    )
    parser.add_argument(
        "job_description",
        type=str,
        help="Path to job description text file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="intermediate-outputs/step2_optimized_resume.json",
        help="Output path for optimized resume JSON"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (or set OPENAI_API_KEY environment variable)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip LLM calls and just copy the input (for testing)"
    )
    parser.add_argument(
        "--concise",
        action="store_true",
        help="Generate more concise bullet points (shorter, punchier)"
    )

    args = parser.parse_args()

    # Load filtered resume
    filtered_resume_path = Path(args.filtered_resume)
    if not filtered_resume_path.exists():
        print(f"Error: Filtered resume file not found: {filtered_resume_path}")
        return 1

    resume_data = load_json(filtered_resume_path)

    # Load job description
    job_desc_path = Path(args.job_description)
    if not job_desc_path.exists():
        print(f"Error: Job description file not found: {job_desc_path}")
        return 1

    with job_desc_path.open('r', encoding='utf-8') as f:
        job_description = f.read()

    if args.dry_run:
        print("Dry run mode: Skipping LLM optimization")
        optimized_resume = resume_data
    else:
        # Setup OpenAI client
        try:
            client = setup_openai_client(args.api_key)
        except ValueError as e:
            print(f"Error: {e}")
            return 1

        # Optimize resume content
        optimized_resume = optimize_resume_content(
            client, resume_data, job_description, args.concise)

    # Save optimized resume
    output_path = Path(args.output)
    save_json(optimized_resume, output_path)
    print(f"\nOptimized resume saved to: {output_path}")

    return 0


if __name__ == "__main__":
    exit(main())
