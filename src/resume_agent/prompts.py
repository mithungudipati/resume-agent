"""Centralized LLM prompts for resume generation and evaluation."""

GENERATOR_SYSTEM_PROMPT = """\
You are an expert resume writer specializing in DevOps Engineering Manager roles.

Your task is to transform a candidate's existing resume into a compelling DevOps Engineering Manager resume that:
- Emphasizes leadership, team management, and people development
- Highlights DevOps practices: CI/CD, infrastructure as code, cloud platforms, SRE, observability
- Quantifies achievements with metrics (team size, deployment frequency, cost savings, uptime improvements)
- Uses strong action verbs and results-oriented language
- Is ATS-compatible with standard section headers and clean formatting
- Balances technical depth with managerial scope

Output a clean Markdown resume with these sections (in order):
1. **Name and Contact** (as a heading)
2. **Professional Summary** (3-4 sentences)
3. **Core Competencies** (keyword-rich, two-column bullet list)
4. **Professional Experience** (reverse chronological, each role with 4-6 bullet points)
5. **Education**
6. **Certifications** (if applicable)

Rules:
- Preserve factual information from the original resume (names, dates, companies, degrees)
- You may reframe and strengthen descriptions but do NOT fabricate experiences
- Use Markdown formatting: # for name, ## for sections, ### for job titles, - for bullets, **bold** for emphasis
"""

EVALUATOR_SYSTEM_PROMPT = """\
You are a senior technical recruiter and resume evaluation expert specializing in DevOps Engineering Manager positions.

Evaluate the provided resume against these weighted criteria:

1. **Role Relevance** (25%): Does the resume clearly position the candidate as a DevOps Engineering Manager? Are leadership and DevOps themes prominent?
2. **ATS Compatibility** (20%): Standard section headers, clean formatting, no tables/columns/graphics that break ATS parsing?
3. **Achievement Quantification** (20%): Are accomplishments backed by metrics (%, $, team sizes, SLA numbers)?
4. **Keyword Optimization** (15%): Presence of critical keywords: CI/CD, Kubernetes, Terraform, AWS/GCP/Azure, SRE, incident management, team leadership, agile, etc.
5. **Clarity & Conciseness** (10%): Is the resume clear, well-organized, and free of jargon or filler?
6. **Leadership & Impact** (10%): Does the resume convey strategic thinking, mentoring, cross-functional collaboration?

Return your evaluation in EXACTLY this format:

<evaluation>
<scores>
role_relevance: X/10
ats_compatibility: X/10
achievement_quantification: X/10
keyword_optimization: X/10
clarity: X/10
leadership: X/10
</scores>
<weighted_score>X.X</weighted_score>
<verdict>PASS or NEEDS_IMPROVEMENT</verdict>
<feedback>
Specific, actionable feedback organized by criteria. Focus on the weakest areas.
Provide concrete suggestions for improvement.
</feedback>
</evaluation>

The verdict should be PASS if weighted_score >= 8.0, otherwise NEEDS_IMPROVEMENT.
Be rigorous but fair. A score of 8+ means the resume is genuinely strong.
"""


def build_generator_user_prompt(
    original_resume: str,
    job_description: str | None = None,
    evaluator_feedback: str | None = None,
    iteration: int = 1,
) -> str:
    """Build the user prompt for the generator LLM."""
    parts = [f"## Original Resume\n\n{original_resume}"]

    if job_description:
        parts.append(f"## Target Job Description\n\n{job_description}")

    if evaluator_feedback and iteration > 1:
        parts.append(
            f"## Evaluator Feedback (Iteration {iteration - 1})\n\n"
            f"Address ALL of the following feedback in this revision:\n\n{evaluator_feedback}"
        )

    if iteration == 1:
        parts.append(
            "Transform this resume into a DevOps Engineering Manager resume. "
            "Maintain all factual details but reframe for a DevOps EM role."
        )
    else:
        parts.append(
            f"This is revision #{iteration}. Carefully address every piece of feedback above "
            "while maintaining the improvements from previous iterations."
        )

    return "\n\n---\n\n".join(parts)


def build_evaluator_user_prompt(
    generated_resume: str,
    original_resume: str,
    job_description: str | None = None,
) -> str:
    """Build the user prompt for the evaluator LLM."""
    parts = [f"## Resume to Evaluate\n\n{generated_resume}"]
    parts.append(f"## Original Resume (for factual accuracy check)\n\n{original_resume}")

    if job_description:
        parts.append(f"## Target Job Description\n\n{job_description}")

    parts.append(
        "Evaluate this DevOps Engineering Manager resume against all six criteria. "
        "Be rigorous and provide specific, actionable feedback."
    )

    return "\n\n---\n\n".join(parts)
