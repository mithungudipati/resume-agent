"""GPT-4o resume generator."""

import time

import click
from openai import OpenAI, AuthenticationError, RateLimitError

from resume_agent.prompts import GENERATOR_SYSTEM_PROMPT, build_generator_user_prompt


def generate_resume(
    original_resume: str,
    job_description: str | None = None,
    evaluator_feedback: str | None = None,
    iteration: int = 1,
) -> str:
    """Generate or revise a DevOps EM resume using GPT-4o.

    Returns the generated resume as Markdown text.
    """
    client = OpenAI()
    user_prompt = build_generator_user_prompt(
        original_resume, job_description, evaluator_feedback, iteration
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.7,
            messages=[
                {"role": "system", "content": GENERATOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content
    except AuthenticationError:
        click.echo("Error: Invalid OpenAI API key. Check your OPENAI_API_KEY.", err=True)
        raise SystemExit(1)
    except RateLimitError:
        click.echo("Rate limited by OpenAI. Retrying in 5 seconds...", err=True)
        time.sleep(5)
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.7,
            messages=[
                {"role": "system", "content": GENERATOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content
