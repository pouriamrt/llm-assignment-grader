# AI Grader

> Grade assignments at scale using AI. Drop submissions into folders, define your rubric in Markdown, and let the LLM do the rest.

---

## Features

| Feature | Description |
|--------|-------------|
| **Multi-format** | PDF, DOCX, PPTX, Python, text, Markdown, JSON, HTML, CSV, YAML, Jupyter notebooks |
| **Multimodal** | Images (PNG, JPEG, GIF, WebP, BMP) are read and sent to the LLM with text |
| **Folder-based** | One subfolder per submission—simple and flexible |
| **Custom rubrics** | Write grading criteria in Markdown; use different prompts per assignment |
| **Async & fast** | Concurrent grading with configurable limits |
| **LLM-ready** | LangChain with OpenAI or Anthropic (Claude) |
| **Grade guardrails** | Total clamped into a valid range (`--min-grade`/`--max-grade`) after grading |
| **CSV export** | `export` command turns feedback files into a per-criterion grade sheet |

---

## Quick Start

```bash
# 1. Install (requires uv: https://docs.astral.sh/uv/)
uv sync

# 2. Add your API key to .env
echo "OPENAI_API_KEY=sk-..." >> .env   # or ANTHROPIC_API_KEY

# 3. Run (uses data/ and prompts/grading_prompt.md by default)
uv run python main.py
```

---

## Project Structure

```
AI_Grader/
├── ai_grader/              # Core package
│   ├── loaders/            # Extract text and images (multimodal) from files
│   ├── scanner/            # Scan data folder, build context per submission
│   └── grader/             # LLM grading logic
├── data/                   # 📁 Put submission subfolders here
├── data_example/           # Sample structure for testing
├── prompts/
│   └── grading_prompt.md   # Default grading criteria
├── my_prompts/             # Assignment-specific prompts
├── output/                 # Feedback files written here
├── main.py                 # Entry point
└── pyproject.toml
```

---

## Setup

### 1. Install dependencies

[uv](https://docs.astral.sh/uv/) is required. Install it, then from the project root:

```bash
uv sync
```

### 2. Configure API key

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
```

The grader prefers OpenAI when `OPENAI_API_KEY` is set; otherwise it uses Anthropic.

### 3. Prepare submissions

- Create a `data/` folder
- Add one subfolder per submission (e.g. `data/student_01/`, `data/student_02/`)
- Place all files for each submission in that folder (subfolders are scanned recursively)
- **ZIP files:** Any `.zip` in a submission folder is extracted automatically, then the zip is removed. Extracted files are used for grading.
- **Excluding files:** Put a `.graderignore` or `.gitignore` in the **data folder** (global, applies to all submissions) and/or in **each submission folder**. Use gitignore-style patterns. You can also use `--exclude` / `-x` to add patterns from the CLI.

Use `data_example/` as a reference, or copy it to `data/` for a quick test.

### 4. Choose a grading prompt

- Default: `prompts/grading_prompt.md`
- Or use an assignment-specific prompt:

  ```bash
  uv run python main.py -p my_prompts/my_grading_prompt.md
  ```

---

## Usage

### Basic

```bash
uv run python main.py
```

### CLI options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--data` | `-d` | `./data` | Folder with submission subfolders |
| `--prompt` | `-p` | `./prompts/grading_prompt.md` | Grading criteria (Markdown) |
| `--output` | `-o` | `./output` | Where to write feedback files |
| `--concurrency` | `-j` | `5` | Max concurrent grading tasks |
| `--log-level` | `-l` | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |
| `--exclude` | `-x` | *(none)* | Gitignore-style pattern to exclude (can repeat). Also uses `.graderignore` and `.gitignore` in each submission folder. |
| `--min-grade` | | `0` | Floor for the total grade (e.g. `10` for a 10–20 rubric). Enforced after grading. |
| `--max-grade` | | *(scale)* | Ceiling for the total grade. Defaults to the rubric's own scale; grades can never exceed it. |
| `--provider` | | `auto` | LLM provider: `openai`, `anthropic`, or `auto`. |
| `--model` | `-m` | *(provider default)* | Model name override. |
| `--force` | `-f` | `false` | Re-grade submissions even if a feedback file already exists. |

### Examples

```bash
# Test with sample data
uv run python main.py -d data_example

# Custom paths and 10 concurrent workers
uv run python main.py -d ./submissions -o ./grades -j 10

# Verbose logging
uv run python main.py -l DEBUG

# Exclude files/folders (gitignore-style)
uv run python main.py -x "*.pyc" -x "__pycache__" -x "*.log"

# Enforce a 10-20 grade range and re-grade everything
uv run python main.py -p my_prompts/text_clustering_grading.md --min-grade 10 --force
```

Feedback is written to `output/<folder_name>_feedback.md` for each submission.

> **Large data files** (e.g. multi-MB CSV datasets) are sampled to a preview before grading so they can't crowd the actual deliverables (notebook, report, slides) out of the model's context window. Each file's text is also capped as a backstop.

### Excluding files and folders

- **Global (data folder):** Put a `.graderignore` or `.gitignore` in the **data folder** (the one containing submission subfolders). Its patterns apply to every submission.
- **Per submission:** Put a `.graderignore` or `.gitignore` in a **submission folder**. Use standard gitignore syntax (e.g. `__pycache__/`, `*.pyc`, `notes.txt`). Matching files and folders are skipped when building context.
- **From CLI:** Use `--exclude` / `-x` to add patterns that apply to all submissions (e.g. `-x "*.pyc" -x "__pycache__"`).

### Analyze grading stats (run after grading)

```bash
uv run python main.py analyze
uv run python main.py analyze -o output
uv run python main.py analyze --save   # also save stats to output/stats.md
```

Shows: mean/median/min/max scores, std dev, score distribution, and error count.

### Export grades to a spreadsheet (run after grading)

```bash
uv run python main.py export                          # writes output/grades.csv
uv run python main.py export -o output --dest grades.csv
```

Produces a CSV grade sheet with one row per submission and one column per rubric
criterion (parsed from each feedback file's table), ending in the Total. Opens
directly in Excel. Point `-o` at a single assignment's output directory so the
columns match one rubric.

---

## Supported File Types

| Extension | Format |
|-----------|--------|
| `.pdf` | PDF |
| `.docx` | Word |
| `.pptx` | PowerPoint |
| `.py` | Python |
| `.txt`, `.md` | Text, Markdown |
| `.json`, `.yaml`, `.yml` | Config |
| `.html`, `.htm`, `.xml` | Web, XML |
| `.csv` | CSV |
| `.ipynb` | Jupyter notebook |
| `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp` | Images (sent to LLM as multimodal input) |

---

## License

MIT
