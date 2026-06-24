"""
GitHub MCP — Tier 2 search source.

Reads files from the loopback-analytics repo (or any configured repo) using the
GitHub REST API. Used when Vault and Slack history have no answer: Mira reads the
actual SQL schema, data dictionary, and known issues to surface root causes.

Set GITHUB_TOKEN and GITHUB_ANALYTICS_REPO in .env to enable.
If GITHUB_TOKEN is absent, GitHub search is silently skipped.
"""

import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)

_GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
_ANALYTICS_REPO = os.environ.get("GITHUB_ANALYTICS_REPO", "Jinqiudong/loopback-analytics")
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
    """
    Search the analytics repo for files relevant to the query.
    Returns a list of {filename, path, excerpt} dicts.
    """
    if not _GITHUB_TOKEN:
        logger.debug("GITHUB_TOKEN not set — skipping GitHub MCP search")
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
        for item in items[:3]:  # top 3 most relevant files
            content = _read_file(item["path"])
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


def read_data_dictionary() -> str:
    """
    Always read the full data dictionary — it contains field definitions
    and business terms that are directly relevant to any data question.
    """
    if not _GITHUB_TOKEN:
        return ""
    content = _read_file("data_dictionary.md")
    return content or ""


def read_known_issues() -> str:
    """Read the known issues doc — often contains root cause for data anomalies."""
    if not _GITHUB_TOKEN:
        return ""
    content = _read_file("docs/known_issues.md")
    return content or ""


def _read_file(path: str) -> str:
    """Fetch raw file content from the analytics repo."""
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
        import base64
        encoded = resp.json().get("content", "")
        return base64.b64decode(encoded).decode("utf-8")
    except Exception:
        logger.warning(f"Failed to read {path} from GitHub", exc_info=True)
        return ""


def _extract_relevant(content: str, query: str, max_chars: int = 800) -> str:
    """Return the most relevant portion of a file for the given query."""
    lines = content.splitlines()
    query_words = set(query.lower().split())

    # Score each line by how many query words it contains
    scored = []
    for i, line in enumerate(lines):
        score = sum(1 for w in query_words if w in line.lower())
        if score > 0:
            scored.append((score, i))

    if not scored:
        return content[:max_chars]

    # Return window around the highest-scoring line
    best_idx = max(scored, key=lambda x: x[0])[1]
    start = max(0, best_idx - 5)
    end = min(len(lines), best_idx + 15)
    excerpt = "\n".join(lines[start:end])
    return excerpt[:max_chars]


def gather_context(query: str) -> dict[str, Any]:
    """
    Main entry point: gather all relevant context from the analytics repo
    for a given question. Returns a dict with findings from each source.
    """
    if not _GITHUB_TOKEN:
        return {}

    findings: dict[str, Any] = {}

    code_results = search_codebase(query)
    if code_results:
        findings["code_files"] = code_results

    data_dict = read_data_dictionary()
    if data_dict:
        # Extract the section most relevant to this specific query
        findings["data_dictionary"] = _extract_relevant(data_dict, query, max_chars=1000)

    known_issues = read_known_issues()
    if known_issues:
        # Extract the section most relevant to this specific query
        findings["known_issues"] = _extract_relevant(known_issues, query, max_chars=1000)

    return findings
