"""AI Grader - Main entry point."""

import asyncio
from pathlib import Path

import typer
from dotenv import load_dotenv
from tqdm.asyncio import tqdm

from ai_grader.grader import grade_assignment_async
from ai_grader.grader.grader import load_grading_prompt
from ai_grader.scanner import scan_assignments

app = typer.Typer(help="Grade assignments using AI")


async def _grade_one(
    assignment: dict,
    grading_prompt: str,
    output_dir: Path,
    semaphore: asyncio.Semaphore,
    pbar: tqdm,
) -> None:
    """Grade a single assignment with semaphore-limited concurrency."""
    async with semaphore:
        name = assignment["folder_name"]
        pbar.set_postfix_str(name, refresh=True)

        try:
            feedback = await grade_assignment_async(assignment["context"], grading_prompt)
            output_path = output_dir / f"{name}_feedback.md"
            output_path.write_text(feedback, encoding="utf-8")
        except Exception as e:
            error_path = output_dir / f"{name}_error.txt"
            error_path.write_text(str(e), encoding="utf-8")
            pbar.write(f"Error ({name}): {e}")
        finally:
            pbar.update(1)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    data: Path = typer.Option(
        None,
        "--data",
        "-d",
        path_type=Path,
        help="Data folder with submission subfolders",
    ),
    prompt: Path = typer.Option(
        None,
        "--prompt",
        "-p",
        path_type=Path,
        help="Grading prompt markdown file",
    ),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        path_type=Path,
        help="Output directory for feedback",
    ),
    concurrency: int = typer.Option(
        5,
        "--concurrency",
        "-j",
        help="Max concurrent grading tasks",
        min=1,
    ),
) -> None:
    """Grade assignments using AI."""
    if ctx.invoked_subcommand is not None:
        return

    load_dotenv()

    project_root = Path(__file__).resolve().parent
    data_folder = data or project_root / "data"
    prompt_file = prompt or project_root / "prompts" / "grading_prompt.md"
    output_dir = output or project_root / "output"

    if not data_folder.exists():
        typer.echo(f"Data folder not found: {data_folder}", err=True)
        example = project_root / "data_example"
        if example.exists():
            typer.echo("Try: python main.py --data data_example", err=True)
        else:
            typer.echo("Create a 'data' folder and add subfolders (one per submission).", err=True)
        raise typer.Exit(1)

    if not prompt_file.exists():
        typer.echo(f"Grading prompt not found: {prompt_file}", err=True)
        typer.echo("Create prompts/grading_prompt.md with your grading criteria.", err=True)
        raise typer.Exit(1)

    grading_prompt = load_grading_prompt(prompt_file)
    assignments = scan_assignments(data_folder)

    if not assignments:
        typer.echo("No assignments found in data folder.")
        typer.echo(
            "Add subfolders under data/ with supported files "
            "(PDF, DOCX, PPTX, .py, .txt, .md, etc)."
        )
        raise typer.Exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    n = len(assignments)
    print(f"Found {n} assignment(s). Grading with concurrency={concurrency}...\n")

    semaphore = asyncio.Semaphore(concurrency)

    async def run_grading() -> None:
        with tqdm(total=n, desc="Grading", unit="submission") as pbar:
            tasks = [
                _grade_one(a, grading_prompt, output_dir, semaphore, pbar) for a in assignments
            ]
            await asyncio.gather(*tasks)

    asyncio.run(run_grading())

    print("\nGrading complete.")


if __name__ == "__main__":
    app()
