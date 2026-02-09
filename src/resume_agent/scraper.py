"""LinkedIn job description scraper with manual fallback."""

import click
import requests
from bs4 import BeautifulSoup


def scrape_job_description(url: str) -> str | None:
    """Attempt to scrape a job description from a LinkedIn URL.

    Returns the job description text, or None on any failure.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Try known LinkedIn selectors for job descriptions
        selectors = [
            "div.description__text",
            "div.show-more-less-html__markup",
            "section.description",
            'div[class*="description"]',
            'div[class*="job-description"]',
        ]
        for selector in selectors:
            el = soup.select_one(selector)
            if el and el.get_text(strip=True):
                return el.get_text(separator="\n", strip=True)

        # Fallback: look for large text blocks
        for div in soup.find_all("div"):
            text = div.get_text(strip=True)
            if len(text) > 500 and any(
                kw in text.lower()
                for kw in ["responsibilities", "requirements", "qualifications"]
            ):
                return text

        return None
    except Exception:
        return None


def prompt_for_job_description() -> str | None:
    """Open an editor for the user to paste a job description manually.

    Returns the pasted text, or None if the user cancels.
    """
    click.echo("Could not scrape the job description automatically.")
    text = click.edit(
        text="# Paste the job description below and save this file:\n\n"
    )
    if text and text.strip():
        return text.strip()
    return None
