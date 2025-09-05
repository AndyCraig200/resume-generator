#!/usr/bin/env python3
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def main():
    # Get the root directory
    root = Path(__file__).resolve().parents[1]
    about_me_dir = root / 'about-me'

    # Load all JSON files
    combined = {}
    json_files = {
        'personal_info.json': 'personal_info',
        'education.json': 'education',
        'experience.json': 'experience',
        'projects.json': 'projects',
        'skills.json': 'skills'
    }

    for filename, key in json_files.items():
        file_path = about_me_dir / filename
        if file_path.exists():
            data = load_json(file_path)
            # Handle nested arrays (like in projects.json and experience.json)
            if isinstance(data, dict) and key in data:
                combined[key] = data[key]
            # For arrays (education, experience, projects), ensure we have a list
            elif key in ['education', 'experience', 'projects']:
                combined[key] = data if isinstance(data, list) else [data]
            else:
                combined[key] = data

    # Write the combined JSON
    output_path = about_me_dir / 'optimized_resume.json'
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(combined, f, indent=2)

    print(f"Created combined resume at: {output_path}")


if __name__ == '__main__':
    main()
