# 🧭 RepoPilot

An MCP (Model Context Protocol) server that gives Claude — or any MCP-compatible AI client — direct, guarded access to GitHub repository data: open issues, pull request summaries, CI status, and code search. Includes a lightweight REST API and web dashboard for human-facing use of the same tools.

## Why this exists

AI assistants are increasingly expected to act on real developer workflows — triaging issues, reviewing PRs, checking build health — without a human copy-pasting data back and forth. RepoPilot demonstrates that pattern end-to-end: a working MCP server that a real AI client (Claude Desktop) can call live, backed by input validation, rate-limit handling, and sane guardrails rather than a naive API wrapper.

## Demo

Claude Desktop calling RepoPilot's `list_open_issues` tool live:

![Claude Desktop using RepoPilot](docs/demo-screenshot.png)

*(Add your screenshot here — see "Adding the demo screenshot" below)*

## Features

| Tool | Description |
|---|---|
| `list_open_issues` | Lists open issues for a repo, filtered to exclude PRs |
| `get_pr_summary` | Summarizes a pull request: author, state, branch, files changed, diff stats |
| `get_ci_status` | Reports the latest CI/check-run status for a branch or commit |
| `search_code` | Searches code within a specific repository |

All four tools are also exposed as REST endpoints (`/api/issues`, `/api/pr`, `/api/ci`, `/api/search`) via a small FastAPI layer, with a browser dashboard (`static/index.html`) for manual use.

## Architecture
