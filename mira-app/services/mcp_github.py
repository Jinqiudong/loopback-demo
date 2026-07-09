"""
GitHub integration — Tier 2 search source.

Reads files from the configured analytics repo using the GitHub REST API.
Used when the Vault has no answer: Claude reads actual SQL schema and docs
to surface root causes rather than guessing from keywords.

Set GITHUB_TOKEN and GITHUB_ANALYTICS_REPO in .env to enable.
If GITHUB_TOKEN is absent, all calls return empty results silently.
"""

import base64
import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)

_GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
_ANALYTICS_REPO = os.environ.get("GITHUB_ANALYTICS_REPO", "")
_BASE_URL = "https://api.github.com"
_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _auth_headers() -> dict:
    if _GITHUB_TOKEN:
        return {**_HEADERS, "Authorization": f"Bearer {_GITHUB_TOKEN}"}
    return _HEADERS


def search_codebase(query: str) -> list[dict[str, Any]]:
    """Search the analytics repo for files relevant to the query."""
    if not _GITHUB_TOKEN or not _ANALYTICS_REPO:
        return []

    try:
        resp = requests.get(
            f"{_BASE_URL}/search/code",
            headers=_auth_headers(),
            params={"q": f"{query} repo:{_ANALYTICS_REPO}", "per_page": 5},
            timeout=10,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])

        results = []
        for item in items[:3]:
            content = read_file(item["path"])
            if content:
                results.append({
                    "filename": item["name"],
                    "path": item["path"],
                    "excerpt": _extract_relevant(content, query),
                    "html_url": item["html_url"],
                })
        return results
    except Exception:
        logger.warning("GitHub codebase search failed", exc_info=True)
        return []


def read_file(path: str) -> str:
    """Fetch raw file content from the analytics repo."""
    if not _GITHUB_TOKEN or not _ANALYTICS_REPO:
        return ""
    try:
        resp = requests.get(
            f"{_BASE_URL}/repos/{_ANALYTICS_REPO}/contents/{path}",
            headers=_auth_headers(),
            params={"ref": "main"},
            timeout=10,
        )
        if resp.status_code == 404:
            return ""
        resp.raise_for_status()
        encoded = resp.json().get("content", "")
        return base64.b64decode(encoded).decode("utf-8")
    except Exception:
        logger.warning(f"Failed to read {path} from GitHub", exc_info=True)
        return ""


def _extract_relevant(content: str, query: str, max_chars: int = 800) -> str:
    """Return the most relevant portion of a file for the given query."""
    lines = content.splitlines()
    query_words = set(query.lower().split())

    scored = []
    for i, line in enumerate(lines):
        score = sum(1 for w in query_words if w in line.lower())
        if score > 0:
            scored.append((score, i))

    if not scored:
        return content[:max_chars]

    best_idx = max(scored, key=lambda x: x[0])[1]
    start = max(0, best_idx - 5)
    end = min(len(lines), best_idx + 15)
    return "\n".join(lines[start:end])[:max_chars]
