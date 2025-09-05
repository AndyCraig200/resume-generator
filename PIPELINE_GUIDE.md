# 🚀 Resume Generation Pipeline Guide

## Quick Start

1. **Setup Environment**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   export OPENAI_API_KEY="your-api-key-here"
   ```

2. **Run Complete Pipeline**
   ```bash
   python scripts/resume_pipeline.py job-applications/example_software_engineer.txt
   ```

3. **Check Output**
   - PDF: `output/example_software_engineer_resume_TIMESTAMP.pdf`
   - Intermediate files: `intermediate-outputs/`

## Pipeline Steps Explained

### Step 1: Relevance Filtering 📊
**Script:** `step1_relevance_filter.py`

**What it does:**
- Extracts keywords from job description
- Scores experiences, projects, and skills by relevance
- Selects top 3 experiences, top 2 projects
- Filters skills to most relevant 8 per category
- **Preserves original text exactly** - no rewriting

**Example:**
```bash
python scripts/step1_relevance_filter.py job-applications/job.txt \
  --max-experiences 3 \
  --max-projects 2 \
  --output intermediate-outputs/filtered.json
```

### Step 2: LLM Optimization ✨
**Script:** `step2_llm_optimize.py`

**What it does:**
- Uses OpenAI GPT-4o-mini for cost-effective optimization
- Makes **minor tweaks** to align with job requirements
- Adjusts terminology and emphasizes relevant skills
- **Maintains original achievements and facts**
- Includes rate limiting and error handling

**Example:**
```bash
python scripts/step2_llm_optimize.py \
  intermediate-outputs/filtered.json \
  job-applications/job.txt \
  --output intermediate-outputs/optimized.json
```

**Dry Run Mode:**
```bash
# Skip LLM calls for testing
python scripts/step2_llm_optimize.py filtered.json job.txt --dry-run
```

### Step 3: PDF Generation 📄
**Script:** `step3_generate_pdf.py`

**What it does:**
- Wrapper around existing `build_resume.py`
- Uses LaTeX templates for professional formatting
- Generates ATS-friendly PDF output

**Example:**
```bash
python scripts/step3_generate_pdf.py \
  intermediate-outputs/optimized.json \
  --output output/resume.pdf
```

## Advanced Usage

### Run Individual Steps
```bash
# Only relevance filtering
python scripts/resume_pipeline.py job.txt --step 1

# Only optimization + PDF
python scripts/resume_pipeline.py job.txt --step 2-3

# Only PDF generation
python scripts/resume_pipeline.py job.txt --step 3
```

### Custom Parameters
```bash
python scripts/resume_pipeline.py job.txt \
  --max-experiences 4 \
  --max-projects 3 \
  --output-dir custom-outputs \
  --final-output custom-resume.pdf
```

### Multiple Job Applications
```bash
# Organize by job/company
python scripts/resume_pipeline.py job-applications/google_swe.txt
python scripts/resume_pipeline.py job-applications/meta_ml.txt
python scripts/resume_pipeline.py job-applications/startup_fullstack.txt
```

## File Organization

### Input Files
- **Job Descriptions:** `job-applications/*.txt`
- **Resume Data:** `about-me/*.json`

### Output Files
- **Intermediate:** `intermediate-outputs/JOBNAME_stepN_TYPE_TIMESTAMP.json`
- **Final PDFs:** `output/JOBNAME_resume_TIMESTAMP.pdf`

### Example Output Structure
```
intermediate-outputs/
├── google_swe_step1_filtered_20240115_143022.json
├── google_swe_step2_optimized_20240115_143045.json
├── meta_ml_step1_filtered_20240115_150312.json
└── meta_ml_step2_optimized_20240115_150335.json

output/
├── google_swe_resume_20240115_143067.pdf
└── meta_ml_resume_20240115_150358.pdf
```

## Troubleshooting

### Common Issues

**OpenAI API Key Error:**
```bash
export OPENAI_API_KEY="your-key-here"
# Or pass directly:
python scripts/resume_pipeline.py job.txt --api-key "your-key"
```

**LaTeX Compilation Error:**
- Ensure LaTeX is installed: `brew install --cask mactex` (macOS)
- Check build logs in `.build/latex/` directory

**Missing Dependencies:**
```bash
pip install -r requirements.txt
```

### Testing
```bash
# Test pipeline components
python scripts/test_pipeline.py

# Test individual steps
python scripts/step1_relevance_filter.py --help
python scripts/step2_llm_optimize.py --help
python scripts/step3_generate_pdf.py --help
```

## Cost Optimization

### OpenAI API Usage
- Uses `gpt-4o-mini` for cost efficiency (~$0.15 per 1M tokens)
- Typical resume optimization: ~$0.01-0.05 per job application
- Rate limiting included (0.5s between calls)

### Batch Processing
```bash
# Process multiple jobs efficiently
for job in job-applications/*.txt; do
  echo "Processing $job..."
  python scripts/resume_pipeline.py "$job"
done
```

## Integration Tips

### Version Control
- All outputs include timestamps for tracking
- Keep intermediate files for debugging and iteration
- Use git to track changes to source data

### Workflow Optimization
1. **Prepare job descriptions** in `job-applications/`
2. **Update resume data** in `about-me/` as needed
3. **Run pipeline** for each application
4. **Review and manually adjust** if needed
5. **Submit optimized resume**

### Quality Assurance
- Always review LLM-optimized content before submission
- Compare filtered vs. original content to ensure relevance
- Test PDF generation on different systems/viewers
