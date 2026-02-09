"""Claude resume evaluator with structured scoring."""

import re
import time
from dataclasses import dataclass, field

import click
import anthropic

from resume_agent.prompts import EVALUATOR_SYSTEM_PROMPT, build_evaluator_user_prompt


@dataclass
class EvaluationResult:
    score: float
    feedback: str
    verdict: str
    criteria_scores: dict[str, float] = field(default_factory=dict)
    raw_response: str = ""


def evaluate_resume(
    generated_resume: str,
    original_resume: str,
    job_description: str | None = None,
) -> EvaluationResult:
    """Evaluate a generated resume using Claude.

    Returns an EvaluationResult with score, feedback, and verdict.
    """
    client = anthropic.Anthropic()
    user_prompt = build_evaluator_user_prompt(
        generated_resume, original_resume, job_description
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            system=EVALUATOR_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = response.content[0].text
        return _parse_evaluation(raw)
    except anthropic.AuthenticationError:
        click.echo("Error: Invalid Anthropic API key. Check your ANTHROPIC_API_KEY.", err=True)
        raise SystemExit(1)
    except anthropic.RateLimitError:
        click.echo("Rate limited by Anthropic. Retrying in 5 seconds...", err=True)
        time.sleep(5)
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            system=EVALUATOR_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = response.content[0].text
        return _parse_evaluation(raw)
    except Exception as e:
        click.echo(f"Evaluator error: {e}. Returning NEEDS_IMPROVEMENT.", err=True)
        return EvaluationResult(
            score=0.0,
            feedback=f"Evaluation failed: {e}",
            verdict="NEEDS_IMPROVEMENT",
        )


def _parse_evaluation(raw: str) -> EvaluationResult:
    """Parse the structured evaluation response from Claude.

    Falls back to score=0 / NEEDS_IMPROVEMENT if parsing fails.
    """
    criteria_scores = {}
    score_patterns = {
        "role_relevance": r"role_relevance:\s*(\d+(?:\.\d+)?)/10",
        "ats_compatibility": r"ats_compatibility:\s*(\d+(?:\.\d+)?)/10",
        "achievement_quantification": r"achievement_quantification:\s*(\d+(?:\.\d+)?)/10",
        "keyword_optimization": r"keyword_optimization:\s*(\d+(?:\.\d+)?)/10",
        "clarity": r"clarity:\s*(\d+(?:\.\d+)?)/10",
        "leadership": r"leadership:\s*(\d+(?:\.\d+)?)/10",
    }

    for name, pattern in score_patterns.items():
        match = re.search(pattern, raw)
        if match:
            criteria_scores[name] = float(match.group(1))

    # Extract weighted score
    weighted_match = re.search(r"<weighted_score>\s*(\d+(?:\.\d+)?)\s*</weighted_score>", raw)
    if weighted_match:
        score = float(weighted_match.group(1))
    elif criteria_scores:
        # Calculate weighted score from individual scores
        weights = {
            "role_relevance": 0.25,
            "ats_compatibility": 0.20,
            "achievement_quantification": 0.20,
            "keyword_optimization": 0.15,
            "clarity": 0.10,
            "leadership": 0.10,
        }
        score = sum(
            criteria_scores.get(k, 0) * w for k, w in weights.items()
        )
    else:
        score = 0.0

    # Extract verdict
    verdict_match = re.search(r"<verdict>\s*(PASS|NEEDS_IMPROVEMENT)\s*</verdict>", raw)
    verdict = verdict_match.group(1) if verdict_match else "NEEDS_IMPROVEMENT"

    # Extract feedback
    feedback_match = re.search(r"<feedback>\s*(.*?)\s*</feedback>", raw, re.DOTALL)
    feedback = feedback_match.group(1).strip() if feedback_match else raw

    return EvaluationResult(
        score=round(score, 2),
        feedback=feedback,
        verdict=verdict,
        criteria_scores=criteria_scores,
        raw_response=raw,
    )
