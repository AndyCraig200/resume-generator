#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import chevron  # Mustache renderer
except ImportError:
    print("Missing dependency: chevron. Please run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

try:
    import jsonschema
except ImportError:
    print("Missing dependency: jsonschema. Please run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
LATEX_TEMPLATE_DIR = ROOT / "latex-template"
SECTIONS_DIR = LATEX_TEMPLATE_DIR / "sections"
CONTEXT_DIR = ROOT / "about-me"
SCHEMA_PATH = ROOT / "context" / "protocol.schema.json"
OUTPUT_DIR = ROOT / "output"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_payload(payload: dict, schema_path: Path):
    schema = load_json(schema_path)
    jsonschema.validate(instance=payload, schema=schema)


def join_display_fields(payload: dict) -> dict:
    # Mutates copies with *_display fields required by templates
    data = json.loads(json.dumps(payload))  # deep copy

    # Helper function to handle LaTeX special characters
    def handle_latex_chars(text):
        if not isinstance(text, str):
            return text
        # Escape LaTeX special characters (order matters - backslash first!)
        replacements = [
            ('\\', '\\textbackslash{}'),
            ('$', '\\$'),
            ('%', '\\%'),
            ('&', '\\&'),
            ('#', '\\#'),
            ('_', '\\_'),
            ('{', '\\{'),
            ('}', '\\}'),
            ('^', '\\textasciicircum{}'),
            ('~', '\\textasciitilde{}')
        ]
        for char, replacement in replacements:
            text = text.replace(char, replacement)
        return text

    # Helper function to handle list items
    def handle_list(items):
        if not isinstance(items, list):
            return items
        return [handle_latex_chars(item) for item in items]

    # skills
    skills = data.get("skills") or {}
    if isinstance(skills.get("languages"), list):
        skills["languages_display"] = ", ".join(
            skills["languages"]) if skills["languages"] else ""
    if isinstance(skills.get("technologies"), list):
        skills["technologies_display"] = ", ".join(
            skills["technologies"]) if skills["technologies"] else ""
    if isinstance(skills.get("concepts"), list):
        skills["concepts_display"] = ", ".join(
            skills["concepts"]) if skills["concepts"] else ""
    data["skills"] = skills

    # projects
    projects = data.get("projects") or []
    for p in projects:
        if isinstance(p.get("tech"), list):
            p["tech_display"] = ", ".join(p["tech"]) if p["tech"] else ""
        if isinstance(p.get("bullets"), list):
            p["bullets"] = handle_list(p["bullets"])
    data["projects"] = projects

    # experience
    experience = data.get("experience") or []
    for e in experience:
        if isinstance(e.get("bullets"), list):
            e["bullets"] = handle_list(e["bullets"])
    data["experience"] = experience

    # education
    education = data.get("education") or []
    for e in education:
        if isinstance(e.get("relevant_coursework"), list):
            e["coursework_display"] = ", ".join(
                e["relevant_coursework"]) if e["relevant_coursework"] else ""
    data["education"] = education

    return data


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def render_sections(data: dict, build_src: Path):
    ensure_dir(build_src)
    # Map section -> template file
    mapping = {
        "heading": SECTIONS_DIR / "heading.tex",
        "experience": SECTIONS_DIR / "experience.tex",
        "projects": SECTIONS_DIR / "projects.tex",
        "skills": SECTIONS_DIR / "skills.tex",
        "education": SECTIONS_DIR / "education.tex",
    }

    # Prepare Mustache contexts per section
    ctx_heading = data.get("personal_info", {})
    ctx_experience = {"experience": data.get("experience", [])}
    ctx_projects = {"projects": data.get("projects", [])}
    ctx_skills = data.get("skills", {})
    ctx_education = {"education": data.get("education", [])}

    contexts = {
        "heading": ctx_heading,
        "experience": ctx_experience,
        "projects": ctx_projects,
        "skills": ctx_skills,
        "education": ctx_education,
    }

    for name, template_path in mapping.items():
        with template_path.open("r", encoding="utf-8") as f:
            rendered = chevron.render(f, contexts[name])
        # Write to build/src with names expected by resume.tex
        out_name = "src/heading.tex" if name == "heading" else f"src/{name}.tex"
        out_path = build_src.parent / out_name
        ensure_dir(out_path.parent)
        with out_path.open("w", encoding="utf-8") as wf:
            wf.write(rendered)


def copy_template_static(build_dir: Path):
    # Copy the entire template folder, then our rendered src files overwrite
    if build_dir.exists():
        shutil.rmtree(build_dir)
    shutil.copytree(LATEX_TEMPLATE_DIR, build_dir)


def compile_pdf(build_dir: Path, output_path: Path):
    # Prefer latexmk
    entry = build_dir / "resume.tex"
    cmd_latexmk = ["latexmk", "-pdf", "-interaction=nonstopmode", str(entry)]
    cmd_pdflatex = ["pdflatex", "-interaction=nonstopmode", str(entry)]
    try:
        subprocess.run(cmd_latexmk, cwd=build_dir, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to running pdflatex twice for references
        subprocess.run(cmd_pdflatex, cwd=build_dir, check=True)
        subprocess.run(cmd_pdflatex, cwd=build_dir, check=True)

    produced = build_dir / "resume.pdf"
    ensure_dir(output_path.parent)
    shutil.copy2(produced, output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Build resume PDF from JSON using LaTeX templates")
    parser.add_argument(
        "json", type=str, help="Path to versioned JSON (adhering to protocol.schema.json)")
    parser.add_argument(
        "--out", type=str, default=str(OUTPUT_DIR / "resume.pdf"), help="Output PDF path")
    args = parser.parse_args()

    payload = load_json(Path(args.json))
    # Optionally support versioning in the input
    _ = payload.get("version")  # accepted but not required here

    # Validate
    validate_payload(payload, SCHEMA_PATH)

    # Precompute display fields
    data = join_display_fields(payload)

    # Prepare build directory
    build_dir = ROOT / ".build" / "latex"
    copy_template_static(build_dir)

    # Render sections into build/src/*.tex
    render_sections(data, build_dir / "src")

    # Compile
    output_path = Path(args.out)
    compile_pdf(build_dir, output_path)
    print(f"Written: {output_path}")


if __name__ == "__main__":
    main()
