"""AI Grader - Main entry point."""

import asyncio
from pathlib import Path

import typer
from dotenv import load_dotenv
from loguru import logger
from tqdm.asyncio import tqdm

from ai_grader.analyzer import analyze_outputs, format_stats_report
from ai_grader.grader import grade_assignment_async
from ai_grader.grader.grader import load_grading_prompt
from ai_grader.guardrails import apply_grade_guardrails
from ai_grader.logging_config import configure_logging
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
            feedback = apply_grade_guardrails(feedback, min_grade=1.0, max_grade=2.0)
            output_path = output_dir / f"{name}_feedback.md"
            output_path.write_text(feedback, encoding="utf-8")
            logger.debug("Graded {} -> {}", name, output_path)
        except Exception as e:
            logger.error("Grading failed for {name}: {err}", name=name, err=e)
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
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    ),
) -> None:
    """Grade assignments using AI."""
    if ctx.invoked_subcommand is not None:
        return

    load_dotenv()
    configure_logging(level=log_level.upper())

    project_root = Path(__file__).resolve().parent
    data_folder = data or project_root / "data"
    prompt_file = prompt or project_root / "prompts" / "grading_prompt.md"
    output_dir = output or project_root / "output"

    if not data_folder.exists():
        logger.error("Data folder not found: {}", data_folder)
        example = project_root / "data_example"
        if example.exists():
            logger.info("Try: python main.py --data data_example")
        else:
            logger.info("Create a 'data' folder and add subfolders (one per submission).")
        raise typer.Exit(1)

    if not prompt_file.exists():
        logger.error("Grading prompt not found: {}", prompt_file)
        logger.info("Create prompts/grading_prompt.md with your grading criteria.")
        raise typer.Exit(1)

    grading_prompt = load_grading_prompt(prompt_file)
    assignments = scan_assignments(data_folder)

    if not assignments:
        logger.warning("No assignments found in data folder")
        logger.info(
            "Add subfolders under data/ with supported files "
            "(PDF, DOCX, PPTX, .py, .txt, .md, etc)."
        )
        raise typer.Exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    n = len(assignments)
    logger.info("Found {} assignment(s), grading with concurrency={}", n, concurrency)

    semaphore = asyncio.Semaphore(concurrency)

    async def run_grading() -> None:
        with tqdm(total=n, desc="Grading", unit="submission") as pbar:
            tasks = [
                _grade_one(a, grading_prompt, output_dir, semaphore, pbar) for a in assignments
            ]
            await asyncio.gather(*tasks)

    asyncio.run(run_grading())

    logger.info("Grading complete")


@app.command()
def analyze(
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        path_type=Path,
        help="Output directory containing feedback files",
    ),
    save: bool = typer.Option(
        False,
        "--save",
        "-s",
        help="Save stats report to output/stats.md",
    ),
) -> None:
    """Analyze grading outputs and display statistics."""
    project_root = Path(__file__).resolve().parent
    output_dir = output or project_root / "output"

    if not output_dir.exists():
        typer.echo(f"Output directory not found: {output_dir}", err=True)
        raise typer.Exit(1)

    result = analyze_outputs(output_dir)
    report = format_stats_report(result, output_dir)

    typer.echo(report)

    if save:
        stats_path = output_dir / "stats.md"
        stats_path.write_text(report, encoding="utf-8")
        typer.echo(f"\nStats saved to {stats_path}")


if __name__ == "__main__":
    app()
