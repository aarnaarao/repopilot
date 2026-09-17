"""
RepoPilot - An MCP server that gives Claude guarded, read-only access
to GitHub repo data: open issues, PR summaries, CI status, and code search.

Run with:
    python server.py
"""

import os
import re
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API = "https://api.github.com"

mcp = FastMCP("RepoPilot")

# Basic guardrail: only allow well-formed "owner/repo" strings.
# This blocks path traversal / injection attempts before we ever hit the API.
REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _headers():
    if not GITHUB_TOKEN:
        raise RuntimeError(
            "GITHUB_TOKEN is not set. Copy .env.example to .env and add your token."
        )
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _validate_repo(repo: str) -> str:
    """Guardrail: reject anything that isn't a clean owner/repo string."""
    if not REPO_PATTERN.match(repo):
        raise ValueError(
            f"Invalid repo format: '{repo}'. Expected 'owner/repo' (e.g. 'facebook/react')."
        )
    return repo


def _get(url: str, params: dict | None = None) -> dict:
    """Wrapper around requests.get with GitHub-aware error handling."""
    resp = requests.get(url, headers=_headers(), params=params, timeout=15)

    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        reset = resp.headers.get("X-RateLimit-Reset", "unknown")
        raise RuntimeError(
            f"GitHub API rate limit exceeded. Resets at epoch time {reset}."
        )
    if resp.status_code == 404:
        raise ValueError("Not found. Check the repo name, issue/PR number, or that your token has access.")
    if resp.status_code == 401:
        raise RuntimeError("GitHub authentication failed. Check your GITHUB_TOKEN in .env.")

    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def list_open_issues(repo: str, limit: int = 10) -> str:
    """
    List open issues for a GitHub repository.

    Args:
        repo: Repository in 'owner/repo' format, e.g. 'facebook/react'.
        limit: Max number of issues to return (default 10, max 30).
    """
    repo = _validate_repo(repo)
    limit = max(1, min(limit, 30))  # guardrail: cap requests to avoid abuse

    data = _get(
        f"{GITHUB_API}/repos/{repo}/issues",
        params={"state": "open", "per_page": limit},
    )

    # Filter out PRs, which GitHub's issues endpoint also returns
    issues = [i for i in data if "pull_request" not in i]

    if not issues:
        return f"No open issues found in {repo}."

    lines = [f"Open issues in {repo} (showing {len(issues)}):\n"]
    for issue in issues:
        lines.append(
            f"#{issue['number']} - {issue['title']} "
            f"(opened by {issue['user']['login']}, {issue['comments']} comments)"
        )
    return "\n".join(lines)


@mcp.tool()
def get_pr_summary(repo: str, pr_number: int) -> str:
    """
    Get a summary of a pull request: title, author, status, and file changes.

    Args:
        repo: Repository in 'owner/repo' format.
        pr_number: The pull request number.
    """
    repo = _validate_repo(repo)
    if pr_number <= 0:
        raise ValueError("pr_number must be a positive integer.")

    pr = _get(f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}")
    files = _get(f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}/files")

    summary = [
        f"PR #{pr_number}: {pr['title']}",
        f"Author: {pr['user']['login']}",
        f"State: {pr['state']}{' (merged)' if pr.get('merged') else ''}",
        f"Branch: {pr['head']['ref']} -> {pr['base']['ref']}",
        f"Changes: +{pr['additions']} / -{pr['deletions']} across {pr['changed_files']} files",
        "\nFiles changed:",
    ]
    for f in files[:15]:  # guardrail: don't dump huge PRs into context
        summary.append(f"  - {f['filename']} ({f['status']}, +{f['additions']}/-{f['deletions']})")

    if len(files) > 15:
        summary.append(f"  ...and {len(files) - 15} more files")

    return "\n".join(summary)


@mcp.tool()
def get_ci_status(repo: str, ref: str = "main") -> str:
    """
    Get the latest CI/check status for a branch or commit SHA.

    Args:
        repo: Repository in 'owner/repo' format.
        ref: Branch name or commit SHA (default 'main').
    """
    repo = _validate_repo(repo)
    data = _get(f"{GITHUB_API}/repos/{repo}/commits/{ref}/check-runs")

    runs = data.get("check_runs", [])
    if not runs:
        return f"No CI check runs found for {repo}@{ref}."

    lines = [f"CI status for {repo}@{ref}:\n"]
    for run in runs:
        status = run["status"]
        conclusion = run.get("conclusion") or "pending"
        lines.append(f"  - {run['name']}: {status} ({conclusion})")

    return "\n".join(lines)


@mcp.tool()
def search_code(repo: str, query: str) -> str:
    """
    Search for code within a specific repository.

    Args:
        repo: Repository in 'owner/repo' format.
        query: Search terms, e.g. 'def authenticate'.
    """
    repo = _validate_repo(repo)
    if not query.strip():
        raise ValueError("query cannot be empty.")

    full_query = f"{query} repo:{repo}"
    data = _get(f"{GITHUB_API}/search/code", params={"q": full_query, "per_page": 10})

    items = data.get("items", [])
    if not items:
        return f"No code matches found for '{query}' in {repo}."

    lines = [f"Code search results for '{query}' in {repo}:\n"]
    for item in items:
        lines.append(f"  - {item['path']}")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()