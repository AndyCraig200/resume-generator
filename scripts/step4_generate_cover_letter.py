#!/usr/bin/env python3
"""
Step 4: Cover Letter Generation
Uses OpenAI API to generate a personalized cover letter based on the optimized resume 
and job description, then renders it using LaTeX template.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any
import subprocess
import tempfile

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

try:
    import chevron
except ImportError:
    print("Missing dependency: chevron. Please run: pip install chevron",
          file=sys.stderr)
    sys.exit(1)


def load_json(path: Path) -> dict:
    """Load JSON data from file."""
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def setup_openai_client(api_key: str = None) -> openai.OpenAI:
    """Setup OpenAI client with API key."""
    if api_key:
        return openai.OpenAI(api_key=api_key)
    elif os.getenv('OPENAI_API_KEY'):
        return openai.OpenAI()
    else:
        raise ValueError(
            "OpenAI API key not provided. Set OPENAI_API_KEY environment variable or pass --api-key")


def generate_cover_letter_content(client: openai.OpenAI, resume_data: Dict[str, Any], job_description: str, company_name: str = None) -> Dict[str, str]:
    """Generate cover letter content using OpenAI API."""

    # Extract key information from resume
    personal_info = resume_data.get('personal_info', {})
    experiences = resume_data.get('experience', [])
    projects = resume_data.get('projects', [])
    skills = resume_data.get('skills', {})

    # Build resume summary for context
    resume_summary = f"Name: {personal_info.get('name', 'Unknown')}\n"

    if experiences:
        resume_summary += "\nKey Experiences:\n"
        for exp in experiences[:2]:  # Top 2 experiences
            resume_summary += f"- {exp.get('role', 'Unknown')} at {exp.get('company', 'Unknown')}\n"
            for bullet in exp.get('bullets', [])[:2]:  # Top 2 bullets per experience
                resume_summary += f"  • {bullet}\n"

    if projects:
        resume_summary += "\nKey Projects:\n"
        for proj in projects[:2]:  # Top 2 projects
            resume_summary += f"- {proj.get('name', 'Unknown')}\n"
            for bullet in proj.get('bullets', [])[:1]:  # Top bullet per project
                resume_summary += f"  • {bullet}\n"

    # Determine company name from job description if not provided
    if not company_name:
        company_name = "the company"

    prompt = f"""You are a professional career counselor writing a compelling cover letter. 

JOB DESCRIPTION:
{job_description}

CANDIDATE'S RESUME SUMMARY:
{resume_summary}

TASK: Write a professional cover letter that:
1. Shows genuine interest in the specific role and company
2. Highlights 2-3 most relevant experiences/achievements from the resume
3. Demonstrates clear alignment between candidate's skills and job requirements
4. Shows enthusiasm and personality while remaining professional
5. Is concise (3-4 paragraphs maximum)

STRUCTURE:
- Opening paragraph: Express interest and briefly mention most relevant qualification
- Body paragraph(s): Highlight specific experiences and achievements that align with the role
- Closing paragraph: Express enthusiasm for next steps

GUIDELINES:
- Use a confident, professional tone
- Be specific about achievements (use numbers/metrics when available)
- Avoid generic statements
- Don't repeat everything from the resume
- Keep it under 400 words
- Use "the company" if company name is unclear from job description

Return a JSON object with the following structure:
{{
  "intro": "Opening paragraph text",
  "body_paragraphs": ["Body paragraph 1", "Body paragraph 2 (if needed)"],
  "closing": "Closing paragraph text",
  "company_name": "Company name extracted from job description or 'Hiring Manager'",
  "recipient_name": "Hiring Manager"
}}

Do not include any explanation, just the JSON object."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional career counselor who writes compelling, personalized cover letters. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,  # Slightly higher for more personality
            max_tokens=1000
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
            cover_letter_data = json.loads(result_text)

            # Validate required fields
            required_fields = ['intro', 'body_paragraphs',
                               'closing', 'company_name', 'recipient_name']
            for field in required_fields:
                if field not in cover_letter_data:
                    raise ValueError(f"Missing required field: {field}")

            # Ensure body_paragraphs is a list
            if not isinstance(cover_letter_data['body_paragraphs'], list):
                cover_letter_data['body_paragraphs'] = [
                    cover_letter_data['body_paragraphs']]

            return cover_letter_data

        except (json.JSONDecodeError, ValueError) as e:
            print(
                f"Warning: Could not parse LLM response for cover letter: {e}")
            print(f"Response was: {result_text}")

            # Fallback to basic template
            return {
                "intro": f"I am writing to express my strong interest in the position described in your job posting.",
                "body_paragraphs": [
                    f"With my background in {', '.join(list(skills.get('technologies', []))[:3]) if skills.get('technologies') else 'software development'}, I am confident I would be a valuable addition to your team.",
                    f"In my recent role as {experiences[0].get('role', 'Software Engineer') if experiences else 'Software Engineer'}, I have developed skills that directly align with your requirements."
                ],
                "closing": "I would welcome the opportunity to discuss how my experience and enthusiasm can contribute to your team's success.",
                "company_name": company_name or "Hiring Manager",
                "recipient_name": "Hiring Manager"
            }

    except Exception as e:
        print(f"Error generating cover letter content: {e}")
        # Return basic fallback
        return {
            "intro": f"I am writing to express my interest in the position at your company.",
            "body_paragraphs": [
                "My experience and skills align well with the requirements outlined in your job description.",
                "I am excited about the opportunity to contribute to your team and would welcome the chance to discuss my qualifications further."
            ],
            "closing": "Thank you for considering my application. I look forward to hearing from you.",
            "company_name": company_name or "Hiring Manager",
            "recipient_name": "Hiring Manager"
        }


def render_cover_letter_latex(cover_letter_data: Dict[str, str], personal_info: Dict[str, Any], template_path: Path, output_path: Path) -> bool:
    """Render cover letter using LaTeX template."""

    try:
        # Read template
        with template_path.open('r', encoding='utf-8') as f:
            template_content = f.read()

        # Prepare template data
        template_data = {
            'date': 'Today',  # You could make this dynamic
            'name': personal_info.get('name', 'Your Name'),
            'recipient_name': cover_letter_data.get('recipient_name', 'Hiring Manager'),
            'company_name': cover_letter_data.get('company_name', 'Company Name'),
            'intro': cover_letter_data.get('intro', ''),
            'body_paragraphs': cover_letter_data.get('body_paragraphs', []),
            'closing': cover_letter_data.get('closing', '')
        }

        # Render template
        rendered_content = chevron.render(template_content, template_data)

        # Write to temporary .tex file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(rendered_content)
            temp_tex_path = Path(temp_file.name)

        try:
            # Compile LaTeX to PDF
            output_dir = output_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)

            # Run pdflatex
            result = subprocess.run([
                'pdflatex',
                '-interaction=nonstopmode',
                '-output-directory', str(output_dir),
                '-jobname', output_path.stem,
                str(temp_tex_path)
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"LaTeX compilation failed:")
                print(result.stdout)
                print(result.stderr)
                return False

            print(f"Cover letter generated successfully: {output_path}")
            return True

        finally:
            # Clean up temporary file
            temp_tex_path.unlink(missing_ok=True)

            # Clean up LaTeX auxiliary files
            aux_files = [
                output_dir / f"{output_path.stem}.aux",
                output_dir / f"{output_path.stem}.log",
                output_dir / f"{output_path.stem}.out"
            ]
            for aux_file in aux_files:
                aux_file.unlink(missing_ok=True)

    except Exception as e:
        print(f"Error rendering cover letter: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate personalized cover letter using optimized resume and job description"
    )
    parser.add_argument(
        "optimized_resume",
        type=str,
        help="Path to optimized resume JSON from step 2"
    )
    parser.add_argument(
        "job_description",
        type=str,
        help="Path to job description text file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/cover_letter.pdf",
        help="Output path for cover letter PDF"
    )
    parser.add_argument(
        "--template",
        type=str,
        default="templates/cover_letter_template.tex",
        help="Path to LaTeX cover letter template"
    )
    parser.add_argument(
        "--company-name",
        type=str,
        help="Company name (will be extracted from job description if not provided)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (or set OPENAI_API_KEY environment variable)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip LLM calls and generate basic template (for testing)"
    )

    args = parser.parse_args()

    # Load optimized resume
    resume_path = Path(args.optimized_resume)
    if not resume_path.exists():
        print(f"Error: Optimized resume file not found: {resume_path}")
        return 1

    resume_data = load_json(resume_path)

    # Load job description
    job_desc_path = Path(args.job_description)
    if not job_desc_path.exists():
        print(f"Error: Job description file not found: {job_desc_path}")
        return 1

    with job_desc_path.open('r', encoding='utf-8') as f:
        job_description = f.read()

    # Check template
    template_path = Path(args.template)
    if not template_path.exists():
        print(f"Error: Cover letter template not found: {template_path}")
        return 1

    print(f"Generating cover letter...")
    print(f"Resume: {resume_path}")
    print(f"Job Description: {job_desc_path}")
    print(f"Template: {template_path}")

    if args.dry_run:
        print("Dry run mode: Using basic template")
        cover_letter_data = {
            "intro": "I am writing to express my interest in the position at your company.",
            "body_paragraphs": [
                "My experience and skills align well with the requirements outlined in your job description.",
                "I am excited about the opportunity to contribute to your team."
            ],
            "closing": "Thank you for considering my application. I look forward to hearing from you.",
            "company_name": args.company_name or "Company Name",
            "recipient_name": "Hiring Manager"
        }
    else:
        # Setup OpenAI client
        try:
            client = setup_openai_client(args.api_key)
        except ValueError as e:
            print(f"Error: {e}")
            return 1

        # Generate cover letter content
        cover_letter_data = generate_cover_letter_content(
            client, resume_data, job_description, args.company_name)

    # Render cover letter
    output_path = Path(args.output)
    personal_info = resume_data.get('personal_info', {})

    success = render_cover_letter_latex(
        cover_letter_data, personal_info, template_path, output_path)

    if success:
        print(f"\n✅ Cover letter generated successfully: {output_path}")
        return 0
    else:
        print(f"\n❌ Cover letter generation failed")
        return 1


if __name__ == "__main__":
    exit(main())
