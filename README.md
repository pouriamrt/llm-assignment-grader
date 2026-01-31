# AI Grader

AI-powered assignment grader that reads various file formats from a `data` folder, combines them into context, and uses an LLM to grade each submission based on a custom prompt in a markdown file.

## Features

- **Multi-format support**: PDF, DOCX, PPTX, Python, text, Markdown, JSON, HTML, CSV, YAML, Jupyter notebooks, and more
- **Folder-based submissions**: Each subfolder under `data/` is treated as one assignment (e.g., one per student)
- **Custom grading prompt**: Define grading criteria in `prompts/grading_prompt.md`
- **LangChain integration**: Uses LangChain with OpenAI or Anthropic (Claude)

## Project Structure

```
AI_Grader/
├── ai_grader/
│   ├── loaders/       # Document loaders (PDF, DOCX, PPTX, etc.)
│   ├── scanner/       # Scans data folder, builds context
│   └── grader/        # LLM grading logic
├── data/              # Put assignment subfolders here (one per submission)
├── data_example/      # Example structure (copy to data/ for testing)
├── prompts/
│   └── grading_prompt.md   # Your grading criteria
├── output/            # Grading feedback (written here)
├── main.py            # Entry point
└── pyproject.toml
```

## Setup

1. **Install dependencies** (from project root):

   ```bash
   pip install -e .
   ```

2. **Set API key** in `.env`:

   ```
   OPENAI_API_KEY=sk-...    # or
   ANTHROPIC_API_KEY=sk-ant-...
   ```

   The grader uses OpenAI by default if `OPENAI_API_KEY` is set, otherwise Anthropic.

3. **Prepare data**:

   - Create a `data` folder
   - Add one subfolder per submission (e.g., `data/student_01/`, `data/student_02/`)
   - Put all files for each submission in that folder (recursive)

   You can copy `data_example` to `data` for a quick test.

4. **Edit grading prompt**: Customize `prompts/grading_prompt.md` with your criteria.

## Usage

```bash
python main.py
```

With custom paths:

```bash
python main.py --data data_example --prompt prompts/grading_prompt.md --output output
```

Control concurrency (default: 5):

```bash
python main.py --concurrency 3
# or
python main.py -j 10
```

Output is written to `output/<folder_name>_feedback.md` for each submission.

## Supported File Types

| Extension | Format          |
|----------|-----------------|
| .pdf     | PDF             |
| .docx    | Word            |
| .pptx    | PowerPoint      |
| .py      | Python          |
| .txt, .md| Text / Markdown |
| .json, .yaml, .yml | Config      |
| .html, .htm, .xml | Web / XML   |
| .csv     | CSV             |
| .ipynb   | Jupyter notebook|

## License

MIT
