# Resume & Cover Letter Generator

A comprehensive LaTeX-based resume generation system that creates professional PDFs from structured JSON data using Mustache templating. The system supports modular resume sections, JSON schema validation, and automated PDF compilation.

## 🚀 What's Implemented

### Core Build System
- **`scripts/build_resume.py`** - Main build script that compiles JSON data into PDF resumes
  - JSON schema validation using `protocol.schema.json`
  - Mustache template rendering for LaTeX sections
  - Automated PDF compilation with `latexmk` or `pdflatex` fallback
  - Display field preprocessing (joins arrays into comma-separated strings)
  - Build directory management with `.build/latex/` workspace

### Data Management
- **`scripts/combine_json.py`** - Utility to merge separate JSON files into a single resume dataset
- **Structured JSON Data** in `about-me/` directory:
  - `personal_info.json` - Contact information and links
  - `experience.json` - Work experience with bullet points
  - `projects.json` - Project descriptions with tech stacks
  - `education.json` - Academic background and coursework
  - `skills.json` - Programming languages, technologies, and concepts
  - `optimized_resume.json` - Combined output file ready for PDF generation

### LaTeX Template System
- **Professional LaTeX Resume Template** (`latex-template/`)
  - Modern, ATS-friendly design using Lato font
  - Modular section-based architecture
  - Custom LaTeX commands for consistent formatting
  - Mustache templating integration for dynamic content
  - **Sections**: heading, experience, projects, education, skills

### Schema Validation
- **`context/protocol.schema.json`** - JSON Schema defining the resume data structure
  - Validates required fields and data types
  - Ensures consistency across resume versions
  - Supports optional fields for flexibility

### Dependencies & Environment
- **Python Virtual Environment** (`venv/`) with required packages:
  - `chevron==0.14.0` - Mustache template rendering
  - `jsonschema==4.23.0` - JSON schema validation
- **LaTeX Dependencies**: Requires LaTeX distribution with `latexmk` or `pdflatex`

## 📁 Project Structure

```
resume-generator/
├── about-me/              # Personal resume data (JSON files)
│   ├── personal_info.json
│   ├── experience.json
│   ├── projects.json
│   ├── education.json
│   ├── skills.json
│   └── optimized_resume.json  # Combined output
├── job-applications/      # Job description files for targeting
│   ├── example_software_engineer.txt
│   ├── example_ml_engineer.txt
│   └── README.md
├── intermediate-outputs/  # Pipeline intermediate files
│   ├── *_step1_filtered_*.json
│   ├── *_step2_optimized_*.json
│   └── ...
├── scripts/               # Build and pipeline scripts
│   ├── resume_pipeline.py      # 🆕 Main 3-step pipeline orchestrator
│   ├── step1_relevance_filter.py  # 🆕 Relevance filtering
│   ├── step2_llm_optimize.py     # 🆕 LLM optimization
│   ├── step3_generate_pdf.py     # 🆕 PDF generation wrapper
│   ├── build_resume.py          # Original PDF generator
│   └── combine_json.py          # JSON file merger
├── latex-template/        # LaTeX template system
│   ├── resume.tex         # Main LaTeX document
│   ├── custom-commands.tex # Custom LaTeX commands
│   └── sections/          # Mustache template sections
│       ├── heading.tex
│       ├── experience.tex
│       ├── projects.tex
│       ├── education.tex
│       └── skills.tex
├── context/
│   └── protocol.schema.json  # JSON schema validation
├── output/                # Generated PDF files
│   └── resume.pdf
├── templates/             # Alternative template storage
└── .build/                # Temporary build directory
```

## 🔧 Usage

### 🚀 New: 3-Step Intelligent Resume Pipeline

The system now includes an intelligent 3-step pipeline that optimizes your resume for specific job applications:

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup your OpenAI API key (interactive setup)
python setup_env.py

# Or manually create .env file with:
# OPENAI_API_KEY=your_actual_api_key_here

# Run the complete pipeline
python scripts/resume_pipeline.py job-applications/example_software_engineer.txt

# Run individual steps
python scripts/resume_pipeline.py job-applications/job.txt --step 1    # Relevance filtering only
python scripts/resume_pipeline.py job-applications/job.txt --step 2-3  # Optimization + PDF generation
```

#### Step-by-Step Process:

**Step 1: Relevance Filtering** 📊
- Analyzes job description keywords
- Selects top 3 most relevant experiences
- Filters skills and projects by relevance
- Preserves original content word-for-word

**Step 2: LLM Optimization** ✨ 
- Uses OpenAI GPT-4 to make minor tweaks
- Adjusts terminology to match job requirements
- Emphasizes relevant technologies and skills
- Maintains original achievements and facts

**Step 3: PDF Generation** 📄
- Uses existing LaTeX pipeline
- Generates professional, ATS-friendly PDF
- Maintains consistent formatting

### 📁 Pipeline Outputs

All intermediate files are saved with timestamps for version control:
```
intermediate-outputs/
├── jobname_step1_filtered_20240115_143022.json
├── jobname_step2_optimized_20240115_143045.json
└── ...

output/
└── jobname_resume_20240115_143067.pdf
```

### 🔧 Legacy Usage (Direct PDF Generation)

```bash
# Build resume from combined JSON (original method)
python scripts/build_resume.py about-me/optimized_resume.json

# Combine individual JSON files
python scripts/combine_json.py
```

## 🎯 Current Capabilities

✅ **🆕 Intelligent 3-Step Pipeline** - Job-targeted resume optimization  
✅ **🆕 AI-Powered Content Optimization** - OpenAI GPT-4 integration for subtle improvements  
✅ **🆕 Relevance Filtering** - Automatic selection of most relevant experiences/skills  
✅ **🆕 Modular Pipeline Execution** - Run individual steps or complete workflow  
✅ **Fully Functional PDF Generation** - Complete LaTeX-to-PDF pipeline  
✅ **Modular JSON Data Structure** - Separate files for each resume section  
✅ **Schema Validation** - Ensures data integrity and consistency  
✅ **Professional LaTeX Styling** - ATS-friendly, modern resume design  
✅ **Mustache Templating** - Dynamic content rendering with logic support  
✅ **Automated Build Process** - Single command PDF generation  
✅ **Display Field Processing** - Automatic formatting for arrays and lists  
✅ **Version Control Integration** - Timestamped outputs for tracking changes  

## 🚧 Future Enhancement Opportunities

- Cover letter generation integration with job-specific optimization
- Multiple resume template options with AI-driven selection
- Web interface for JSON editing and pipeline management
- Integration with job board APIs for automatic application
- Advanced analytics on resume performance and optimization effectiveness
- Multi-language resume generation and localization