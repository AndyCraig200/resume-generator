#!/usr/bin/env python3
"""
Step 1: LLM-Based Relevance Filtering
Uses OpenAI to intelligently analyze job descriptions and select the most relevant 
experiences, projects, and skills from the complete resume data without rewriting any content.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
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


def llm_rank_experiences(client: openai.OpenAI, experiences: List[Dict], job_description: str, max_count: int) -> List[Dict]:
    """Use LLM to rank and select the most relevant experiences, respecting priority levels."""

    if len(experiences) <= max_count:
        return experiences

    # Separate experiences by priority
    high_priority = [
        exp for exp in experiences if exp.get('priority') == 'high']
    medium_priority = [
        exp for exp in experiences if exp.get('priority') == 'medium']
    low_priority = [exp for exp in experiences if exp.get('priority') == 'low']
    no_priority = [exp for exp in experiences if 'priority' not in exp]

    # Always include all high priority experiences
    selected_experiences = high_priority.copy()
    remaining_slots = max_count - len(selected_experiences)

    if remaining_slots <= 0:
        # If high priority experiences exceed max_count, return first max_count high priority ones
        return selected_experiences[:max_count]

    # Combine medium, low, and no-priority experiences for LLM ranking
    remaining_experiences = medium_priority + low_priority + no_priority

    if not remaining_experiences:
        return selected_experiences

    if len(remaining_experiences) <= remaining_slots:
        # If we have space for all remaining experiences
        return selected_experiences + remaining_experiences

    # Prepare experience summaries for the LLM (only for remaining experiences)
    exp_summaries = []
    for i, exp in enumerate(remaining_experiences):
        priority_note = f" [Priority: {exp.get('priority', 'unset')}]"
        summary = f"Experience {i+1}:\n"
        summary += f"Company: {exp.get('company', 'Unknown')}\n"
        summary += f"Role: {exp.get('role', 'Unknown')}\n"
        summary += f"Duration: {exp.get('start_date', '')} - {exp.get('end_date', '')}{priority_note}\n"
        summary += f"Key achievements:\n"
        for bullet in exp.get('bullets', []):
            summary += f"• {bullet}\n"
        exp_summaries.append(summary)

    prompt = f"""You are a career counselor helping to select the most relevant work experiences for a specific job application.

NOTE: High priority experiences have already been selected. You are choosing from the remaining experiences.

JOB DESCRIPTION:
{job_description}

AVAILABLE EXPERIENCES (remaining {remaining_slots} slots):
{chr(10).join(exp_summaries)}

TASK: Select the {remaining_slots} most relevant experiences for this job application. Consider:
1. Technical skills alignment
2. Industry relevance  
3. Role responsibilities match
4. Seniority level appropriateness
5. Transferable skills
6. Priority level (medium priority experiences are preferred over low priority when relevance is similar)

Return ONLY a JSON array with the experience numbers (1-based) in order of relevance.
Example format: [1, 3, 2]

Do not include any explanation, just the JSON array."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional career counselor who selects the most relevant work experiences for job applications. Always respond with only a JSON array of numbers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=100
        )

        result_text = response.choices[0].message.content.strip()

        # Parse the JSON response
        try:
            selected_indices = json.loads(result_text)
            if not isinstance(selected_indices, list):
                raise ValueError("Response is not a list")

            # Convert to 0-based indices and validate (for remaining_experiences)
            llm_selected = []
            for idx in selected_indices[:remaining_slots]:
                if isinstance(idx, int) and 1 <= idx <= len(remaining_experiences):
                    llm_selected.append(remaining_experiences[idx - 1])

            # If we don't have enough, fill with remaining experiences
            if len(llm_selected) < remaining_slots:
                remaining = [
                    exp for exp in remaining_experiences if exp not in llm_selected]
                llm_selected.extend(
                    remaining[:remaining_slots - len(llm_selected)])

            # Combine high priority + LLM selected
            final_selection = selected_experiences + llm_selected
            return final_selection[:max_count]

        except (json.JSONDecodeError, ValueError) as e:
            print(
                f"Warning: Could not parse LLM response for experiences: {e}")
            print(f"Response was: {result_text}")
            # Fallback: high priority + first N remaining
            fallback_selection = selected_experiences + \
                remaining_experiences[:remaining_slots]
            return fallback_selection[:max_count]

    except Exception as e:
        print(f"Error using LLM for experience ranking: {e}")
        # Fallback: high priority + first N remaining
        fallback_selection = selected_experiences + \
            remaining_experiences[:remaining_slots]
        return fallback_selection[:max_count]


def llm_rank_projects(client: openai.OpenAI, projects: List[Dict], job_description: str, max_count: int) -> List[Dict]:
    """Use LLM to rank and select the most relevant projects, respecting priority levels."""

    if len(projects) <= max_count:
        return projects

    # Separate projects by priority
    high_priority = [
        proj for proj in projects if proj.get('priority') == 'high']
    medium_priority = [
        proj for proj in projects if proj.get('priority') == 'medium']
    low_priority = [proj for proj in projects if proj.get('priority') == 'low']
    no_priority = [proj for proj in projects if 'priority' not in proj]

    # Always include all high priority projects
    selected_projects = high_priority.copy()
    remaining_slots = max_count - len(selected_projects)

    if remaining_slots <= 0:
        # If high priority projects exceed max_count, return first max_count high priority ones
        return selected_projects[:max_count]

    # Combine medium, low, and no-priority projects for LLM ranking
    remaining_projects = medium_priority + low_priority + no_priority

    if not remaining_projects:
        return selected_projects

    if len(remaining_projects) <= remaining_slots:
        # If we have space for all remaining projects
        return selected_projects + remaining_projects

    # Prepare project summaries for the LLM (only for remaining projects)
    proj_summaries = []
    for i, proj in enumerate(remaining_projects):
        priority_note = f" [Priority: {proj.get('priority', 'unset')}]"
        summary = f"Project {i+1}:\n"
        summary += f"Name: {proj.get('name', 'Unknown')}\n"
        summary += f"Technologies: {', '.join(proj.get('tech', []))}{priority_note}\n"
        summary += f"Description:\n"
        for bullet in proj.get('bullets', []):
            summary += f"• {bullet}\n"
        proj_summaries.append(summary)

    prompt = f"""You are a career counselor helping to select the most relevant projects for a specific job application.

NOTE: High priority projects have already been selected. You are choosing from the remaining projects.

JOB DESCRIPTION:
{job_description}

AVAILABLE PROJECTS (remaining {remaining_slots} slots):
{chr(10).join(proj_summaries)}

TASK: Select the {remaining_slots} most relevant projects for this job application. Consider:
1. Technology stack alignment
2. Project complexity and scope
3. Relevant problem-solving approaches
4. Demonstrable skills
5. Industry relevance
6. Priority level (medium priority projects are preferred over low priority when relevance is similar)

Return ONLY a JSON array with the project numbers (1-based) in order of relevance.
Example format: [2, 1]

Do not include any explanation, just the JSON array."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional career counselor who selects the most relevant projects for job applications. Always respond with only a JSON array of numbers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=100
        )

        result_text = response.choices[0].message.content.strip()

        # Parse the JSON response
        try:
            selected_indices = json.loads(result_text)
            if not isinstance(selected_indices, list):
                raise ValueError("Response is not a list")

            # Convert to 0-based indices and validate (for remaining_projects)
            llm_selected = []
            for idx in selected_indices[:remaining_slots]:
                if isinstance(idx, int) and 1 <= idx <= len(remaining_projects):
                    llm_selected.append(remaining_projects[idx - 1])

            # If we don't have enough, fill with remaining projects
            if len(llm_selected) < remaining_slots:
                remaining = [
                    proj for proj in remaining_projects if proj not in llm_selected]
                llm_selected.extend(
                    remaining[:remaining_slots - len(llm_selected)])

            # Combine high priority + LLM selected
            final_selection = selected_projects + llm_selected
            return final_selection[:max_count]

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Could not parse LLM response for projects: {e}")
            print(f"Response was: {result_text}")
            # Fallback: high priority + first N remaining
            fallback_selection = selected_projects + \
                remaining_projects[:remaining_slots]
            return fallback_selection[:max_count]

    except Exception as e:
        print(f"Error using LLM for project ranking: {e}")
        # Fallback: high priority + first N remaining
        fallback_selection = selected_projects + \
            remaining_projects[:remaining_slots]
        return fallback_selection[:max_count]


def llm_filter_skills(client: openai.OpenAI, skills: Dict[str, Any], job_description: str, max_per_category: int) -> Dict[str, Any]:
    """Use LLM to filter skills by relevance to job description."""

    filtered_skills = {}

    for category in ['languages', 'technologies', 'concepts']:
        if category not in skills or not isinstance(skills[category], list):
            continue

        skill_list = skills[category]
        if len(skill_list) <= max_per_category:
            # No need to filter if we have fewer skills than the limit
            filtered_skills[category] = skill_list
            continue

        prompt = f"""You are a career counselor helping to select the most relevant skills for a specific job application.

JOB DESCRIPTION:
{job_description}

SKILL CATEGORY: {category.title()}
AVAILABLE SKILLS: {', '.join(skill_list)}

TASK: Select the {max_per_category} most relevant {category} for this job application. Consider:
1. Direct mentions in the job description
2. Related/complementary technologies
3. Industry standard requirements
4. Transferable skills value

Return ONLY a JSON array with the exact skill names from the list above.
Example format: ["Python", "JavaScript", "React"]

Do not include any explanation, just the JSON array."""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are a professional career counselor who selects the most relevant {category} for job applications. Always respond with only a JSON array of skill names."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )

            result_text = response.choices[0].message.content.strip()

            # Clean up any markdown formatting
            if result_text.startswith('```json'):
                result_text = result_text.replace(
                    '```json', '').replace('```', '').strip()
            elif result_text.startswith('```'):
                result_text = result_text.replace('```', '').strip()

            # Parse the JSON response
            try:
                selected_skills = json.loads(result_text)
                if not isinstance(selected_skills, list):
                    raise ValueError("Response is not a list")

                # Validate that selected skills are in the original list
                valid_skills = [
                    skill for skill in selected_skills if skill in skill_list]

                # If we don't have enough, fill with remaining skills
                if len(valid_skills) < max_per_category:
                    remaining = [
                        skill for skill in skill_list if skill not in valid_skills]
                    valid_skills.extend(
                        remaining[:max_per_category - len(valid_skills)])

                filtered_skills[category] = valid_skills[:max_per_category]

            except (json.JSONDecodeError, ValueError) as e:
                print(
                    f"Warning: Could not parse LLM response for {category}: {e}")
                print(f"Response was: {result_text}")
                # Fallback to first N skills
                filtered_skills[category] = skill_list[:max_per_category]

        except Exception as e:
            print(f"Error using LLM for {category} filtering: {e}")
            # Fallback to first N skills
            filtered_skills[category] = skill_list[:max_per_category]

        # Small delay to respect rate limits
        time.sleep(0.3)

    return filtered_skills


def main():
    parser = argparse.ArgumentParser(
        description="Filter resume content based on job description relevance using LLM"
    )
    parser.add_argument(
        "job_description",
        type=str,
        help="Path to job description text file"
    )
    parser.add_argument(
        "--source-dir",
        type=str,
        default="about-me",
        help="Directory containing source resume JSON files"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="intermediate-outputs/step1_filtered_resume.json",
        help="Output path for filtered resume JSON"
    )
    parser.add_argument(
        "--max-experiences",
        type=int,
        default=3,
        help="Maximum number of experiences to include"
    )
    parser.add_argument(
        "--max-projects",
        type=int,
        default=2,
        help="Maximum number of projects to include"
    )
    parser.add_argument(
        "--max-skills-per-category",
        type=int,
        default=8,
        help="Maximum skills per category to include"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (or set OPENAI_API_KEY environment variable)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip LLM calls and use simple selection (for testing)"
    )

    args = parser.parse_args()

    # Load job description
    job_desc_path = Path(args.job_description)
    if not job_desc_path.exists():
        print(f"Error: Job description file not found: {job_desc_path}")
        return 1

    with job_desc_path.open('r', encoding='utf-8') as f:
        job_description = f.read()

    print(f"Loaded job description from: {job_desc_path}")

    # Setup OpenAI client (unless dry run)
    if not args.dry_run:
        try:
            client = setup_openai_client(args.api_key)
            print("OpenAI client initialized successfully")
        except ValueError as e:
            print(f"Error: {e}")
            return 1
    else:
        print("Dry run mode: Skipping LLM calls")
        client = None

    # Load source resume data
    source_dir = Path(args.source_dir)

    # Load individual JSON files
    resume_data = {}

    # Load personal info (always included)
    personal_info_path = source_dir / "personal_info.json"
    if personal_info_path.exists():
        personal_data = load_json(personal_info_path)
        resume_data["personal_info"] = personal_data

    # Load education (always included)
    education_path = source_dir / "education.json"
    if education_path.exists():
        education_data = load_json(education_path)
        resume_data["education"] = education_data.get(
            "education", education_data)

    # Load and filter experiences
    experience_path = source_dir / "experience.json"
    if experience_path.exists():
        experience_data = load_json(experience_path)
        experiences = experience_data.get("experience", experience_data)
        if isinstance(experiences, list):
            if args.dry_run or client is None:
                # Simple selection for dry run
                filtered_experiences = experiences[:args.max_experiences]
            else:
                print(
                    f"Using LLM to select {args.max_experiences} most relevant experiences from {len(experiences)} available...")
                filtered_experiences = llm_rank_experiences(
                    client, experiences, job_description, args.max_experiences)

            resume_data["experience"] = filtered_experiences
            print(
                f"Selected experiences: {len(experiences)} -> {len(filtered_experiences)}")
            for exp in filtered_experiences:
                print(
                    f"  - {exp.get('company', 'Unknown')}: {exp.get('role', 'Unknown')}")

    # Load and filter projects
    projects_path = source_dir / "projects.json"
    if projects_path.exists():
        projects_data = load_json(projects_path)
        projects = projects_data.get("projects", projects_data)
        if isinstance(projects, list):
            if args.dry_run or client is None:
                # Simple selection for dry run
                filtered_projects = projects[:args.max_projects]
            else:
                print(
                    f"Using LLM to select {args.max_projects} most relevant projects from {len(projects)} available...")
                filtered_projects = llm_rank_projects(
                    client, projects, job_description, args.max_projects)

            resume_data["projects"] = filtered_projects
            print(
                f"Selected projects: {len(projects)} -> {len(filtered_projects)}")
            for proj in filtered_projects:
                print(f"  - {proj.get('name', 'Unknown')}")

    # Load and filter skills
    skills_path = source_dir / "skills.json"
    if skills_path.exists():
        skills_data = load_json(skills_path)
        # Handle both nested and flat skill structures
        if "languages" in skills_data:
            skills = skills_data
        else:
            skills = skills_data.get("skills", skills_data)

        if args.dry_run or client is None:
            # Simple selection for dry run
            filtered_skills = {}
            for category in ['languages', 'technologies', 'concepts']:
                if category in skills and isinstance(skills[category], list):
                    filtered_skills[category] = skills[category][:args.max_skills_per_category]
        else:
            print(f"Using LLM to filter skills by relevance...")
            filtered_skills = llm_filter_skills(
                client, skills, job_description, args.max_skills_per_category)

        resume_data["skills"] = filtered_skills

        for category, skill_list in filtered_skills.items():
            original_count = len(skills.get(category, []))
            print(
                f"Selected {category}: {original_count} -> {len(skill_list)}")

    # Save filtered resume
    output_path = Path(args.output)
    save_json(resume_data, output_path)
    print(f"\nFiltered resume saved to: {output_path}")

    return 0


if __name__ == "__main__":
    exit(main())
