# Build Scripts

## Prerequisites
- Python 3.9+
- TeX toolchain: latexmk (preferred) or pdflatex
- Install Python deps:

```bash
pip install -r requirements.txt
```

## Build Resume

```bash
python scripts/build_resume.py about-me/optimized_resume.json --out output/resume.pdf
```

- The input JSON must adhere to `context/protocol.schema.json`.
- The script validates the JSON, computes display fields, renders Mustache templates in `latex-template/sections/`, and compiles to PDF.
- If `latexmk` is not installed, the script falls back to running `pdflatex` twice.

## Notes
- Rendered sections are written to `.build/latex/src/*.tex`.
- The LaTeX entry point is `latex-template/resume.tex` (copied into the build dir).