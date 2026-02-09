# Resume Agent

An evaluator-optimizer CLI tool that transforms any resume into a DevOps resume. GPT-4o generates the resume, Claude evaluates it and provides feedback, and the loop repeats until a quality threshold is met.

## How It Works

```
resume file ──→ parser ──→ resume text
                                │
job description (optional) ─────┤
                                ▼
                ┌─────────────────────────────┐
                │   EVALUATOR-OPTIMIZER LOOP  │
                │                             │
                │  1. GPT-4o generates resume │
                │  2. Claude scores & reviews │
                │                             │
                │  score >= 8? → done         │
                │  else → feed back to step 1 │
                └─────────────────────────────┘
                                │
                                ▼
                output/optimized_resume_TIMESTAMP.docx
```

Claude scores on six weighted criteria:

| Criteria | Weight |
|----------|--------|
| Role Relevance | 25% |
| ATS Compatibility | 20% |
| Achievement Quantification | 20% |
| Keyword Optimization | 15% |
| Clarity & Conciseness | 10% |
| Leadership & Impact | 10% |

## Setup

```bash
# Clone and enter the project
cd resume-agent

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in dev mode
pip install -e .

# Configure API keys
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and ANTHROPIC_API_KEY
```

## Usage

```bash
# Basic — uses default 3 iterations, threshold 8.0
resume-agent input/resume.pdf

# With a job description file (recommended for targeted output)
resume-agent input/resume.docx --job-text input/job_description.txt

# With a LinkedIn job URL
resume-agent input/resume.pdf --job-url "https://linkedin.com/jobs/view/123"

# Custom iterations and threshold
resume-agent input/resume.pdf -t input/jd.txt -n 5 --threshold 9.0

# Custom output directory
resume-agent input/resume.pdf -o results/
```

### Options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--job-url` | `-u` | — | LinkedIn job posting URL |
| `--job-text` | `-t` | — | Path to a text file with the job description |
| `--max-iterations` | `-n` | 3 | Maximum optimization loop iterations |
| `--threshold` | | 8.0 | Score (1-10) needed to pass |
| `--output-dir` | `-o` | `output/` | Where to save the generated DOCX |

## Project Structure

```
resume-agent/
├── pyproject.toml
├── .env.example
├── .gitignore
├── src/
│   └── resume_agent/
│       ├── main.py         # CLI entry point + orchestrator loop
│       ├── parser.py       # PDF/DOCX text extraction
│       ├── scraper.py      # LinkedIn job description scraper
│       ├── generator.py    # GPT-4o resume generator
│       ├── evaluator.py    # Claude resume evaluator
│       ├── writer.py       # Markdown → DOCX converter
│       └── prompts.py      # All LLM prompts
├── input/                  # Place resumes and job descriptions here
└── output/                 # Generated resumes appear here
```

## Requirements

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys) (for GPT-4o)
- An [Anthropic API key](https://console.anthropic.com/) (for Claude)
