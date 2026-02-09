"""CLI entry point and evaluator-optimizer orchestrator loop."""

import os
from datetime import datetime
from pathlib import Path

import click
from dotenv import load_dotenv

from resume_agent.parser import parse_resume
from resume_agent.scraper import scrape_job_description, prompt_for_job_description
from resume_agent.generator import generate_resume
from resume_agent.evaluator import evaluate_resume, EvaluationResult
from resume_agent.writer import write_resume_docx


load_dotenv()


@click.command()
@click.argument("resume_path", type=click.Path(exists=True))
@click.option("--job-url", "-u", help="LinkedIn job posting URL")
@click.option(
    "--job-text", "-t",
    type=click.Path(exists=True),
    help="Path to a text file containing the job description",
)
@click.option("--max-iterations", "-n", default=3, help="Maximum optimization iterations")
@click.option("--threshold", default=8.0, help="Score threshold to pass (1-10)")
@click.option(
    "--output-dir", "-o",
    default="output",
    help="Output directory for generated resumes",
)
def cli(resume_path, job_url, job_text, max_iterations, threshold, output_dir):
    """Transform any resume into a DevOps Engineering Manager resume.

    RESUME_PATH is the path to a PDF or DOCX resume file.
    """
    try:
        _validate_api_keys()

        # Step 1: Parse the resume
        click.echo(f"Parsing resume: {resume_path}")
        original_resume = parse_resume(resume_path)
        click.echo(f"Extracted {len(original_resume)} characters from resume.\n")

        # Step 2: Get job description (optional)
        job_description = _resolve_job_description(job_url, job_text)
        if job_description:
            click.echo(f"Job description loaded ({len(job_description)} chars).\n")
        else:
            click.echo("No job description provided. Generating a general DevOps EM resume.\n")

        # Step 3: Run the optimization loop
        best_resume, best_result = run_optimization_loop(
            original_resume=original_resume,
            job_description=job_description,
            max_iterations=max_iterations,
            threshold=threshold,
        )

        # Step 4: Write the final DOCX
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(Path(output_dir) / f"optimized_resume_{timestamp}.docx")
        write_resume_docx(best_resume, output_path)

        click.echo(f"\nResume saved to: {output_path}")
        click.echo(f"Final score: {best_result.score}/10 ({best_result.verdict})")

    except (ValueError, SystemExit) as e:
        raise
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


def run_optimization_loop(
    original_resume: str,
    job_description: str | None,
    max_iterations: int,
    threshold: float,
) -> tuple[str, EvaluationResult]:
    """Run the generate-evaluate loop until quality threshold or max iterations.

    Returns (best_resume_markdown, best_evaluation_result).
    """
    best_resume = ""
    best_result = EvaluationResult(score=0.0, feedback="", verdict="NEEDS_IMPROVEMENT")
    evaluator_feedback = None

    for iteration in range(1, max_iterations + 1):
        click.echo(f"{'='*50}")
        click.echo(f"Iteration {iteration}/{max_iterations}")
        click.echo(f"{'='*50}")

        # Generate
        click.echo("Generating resume with GPT-4o...")
        generated = generate_resume(
            original_resume=original_resume,
            job_description=job_description,
            evaluator_feedback=evaluator_feedback,
            iteration=iteration,
        )

        # Evaluate
        click.echo("Evaluating with Claude...")
        result = evaluate_resume(
            generated_resume=generated,
            original_resume=original_resume,
            job_description=job_description,
        )

        # Print scores
        click.echo(f"\nScore: {result.score}/10 — {result.verdict}")
        if result.criteria_scores:
            for criterion, score in result.criteria_scores.items():
                click.echo(f"  {criterion}: {score}/10")
        click.echo("")

        # Track best
        if result.score > best_result.score:
            best_resume = generated
            best_result = result

        # Check exit condition
        if result.verdict == "PASS" or result.score >= threshold:
            click.echo("Quality threshold met!")
            break

        # Feed back for next iteration
        evaluator_feedback = result.feedback
        if iteration < max_iterations:
            click.echo("Feeding evaluation back for next iteration...\n")

    return best_resume, best_result


def _validate_api_keys():
    """Ensure required API keys are set."""
    if not os.environ.get("OPENAI_API_KEY"):
        click.echo("Error: OPENAI_API_KEY not set. Add it to your .env file.", err=True)
        raise SystemExit(1)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        click.echo("Error: ANTHROPIC_API_KEY not set. Add it to your .env file.", err=True)
        raise SystemExit(1)


def _resolve_job_description(job_url: str | None, job_text: str | None) -> str | None:
    """Resolve job description from URL, file, or manual input."""
    # Prefer text file if provided
    if job_text:
        return Path(job_text).read_text().strip()

    # Try scraping URL
    if job_url:
        click.echo(f"Scraping job description from: {job_url}")
        description = scrape_job_description(job_url)
        if description:
            return description
        # Fallback to manual paste
        return prompt_for_job_description()

    return None


if __name__ == "__main__":
    cli()
