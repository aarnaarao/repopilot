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


Both the MCP server and the REST API call the *same* underlying tool functions in `server.py` — no logic duplication between the AI-facing and human-facing interfaces.

## Guardrails & design decisions

- **Repo name validation** — a regex whitelist blocks malformed or path-traversal-style input before any API call is made.
- **Result capping** — issue lists and PR file lists are capped (e.g. max 30 issues, 15 files shown) to avoid flooding an LLM's context window with a single tool call.
- **GitHub-aware error handling** — rate limits, 404s, and auth failures are caught and returned as clear, actionable messages instead of raw stack traces.
- **Known limitation**: GitHub's code search API can return `incomplete_results: true` on very large repositories (e.g. facebook/react) even when the query is valid — this is a documented constraint of GitHub's search index, not a bug in this project. Verified against smaller repos to confirm correct behavior.

## Setup

### Prerequisites
- Python 3.10+
- A free [GitHub Personal Access Token](https://github.com/settings/tokens) (classic, `repo` scope is sufficient)

### Installation

```bash
git clone https://github.com/aarnaarao/repopilot.git
cd repopilot
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
cp .env.example .env         # then add your GitHub token to .env
```

### Running the MCP server standalone

```bash
python server.py
```


### Connecting to Claude Desktop

Add this to your Claude Desktop config file (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "repopilot": {
      "command": "C:\\path\\to\\repopilot\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\repopilot\\server.py"],
      "env": {
        "GITHUB_TOKEN": "your_token_here"
      }
    }
  }
}
```

Restart Claude Desktop, then check **Settings → Developer → Local MCP servers** to confirm it shows as "Running."

## Testing

```bash
python test_tools.py
```

Runs all four tools against a real public repo and prints the results, including verifying error handling on invalid input.

## Tech stack

- **fastmcp** — MCP server framework
- **FastAPI** + **uvicorn** — REST API layer
- **requests** — GitHub API client
- Vanilla HTML/CSS/JS — dashboard (no build step required)

## License

MIT
