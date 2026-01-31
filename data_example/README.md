# Example data for AI Grader

This folder contains sample **submission subfolders** for testing the grader. Each subfolder represents one student submission and can include code, documents, or other supported files.

## Structure

- **One subfolder per submission** (e.g., `student_01`, `student_02`).
- Each subfolder can contain any supported files: `.py`, `.md`, `.txt`, `.pdf`, `.docx`, `.pptx`, `.ipynb`, etc.
- The grader scans all files in each subfolder and builds context for the LLM.

## Sample submissions

| Folder       | Description                          |
|-------------|--------------------------------------|
| `student_01` | Strong submission: clear code + README |
| `student_02` | Adequate submission: works but less polished |
| `student_03` | Minimal submission: incomplete or with issues |

## Usage

Run the grader on this example data:

```bash
python main.py --data data_example
```

Output will be written to the `output/` directory (one feedback file per submission).
