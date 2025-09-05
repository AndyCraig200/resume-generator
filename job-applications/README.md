# Job Applications Directory

This directory contains job description files used by the resume generation pipeline.

## File Format

Job descriptions should be saved as plain text files (`.txt`) with descriptive names.

## Examples

- `example_software_engineer.txt` - Full-stack software engineer position
- `example_ml_engineer.txt` - Machine learning engineer position

## Usage

```bash
# Use with the pipeline
python scripts/resume_pipeline.py job-applications/your_job_description.txt

# Or with individual steps
python scripts/step1_relevance_filter.py job-applications/your_job_description.txt
```

## Tips

- Include the complete job description for better keyword matching
- Save files with descriptive names (company_position.txt)
- The pipeline will use the filename for organizing outputs
