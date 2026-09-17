"""
RepoPilot API - a thin REST layer over the same tool functions used by the
MCP server, so the web dashboard can call them too.

Run with:
    uvicorn api:app --reload
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from server import list_open_issues, get_pr_summary, get_ci_status, search_code

app = FastAPI(title="RepoPilot API")

# Allow the local dashboard (served from the same app, but keep this
# permissive for local dev) to call these endpoints from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _safe_call(fn, *args, **kwargs):
    """Run a tool function and convert its errors into proper HTTP responses."""
    try:
        return {"result": fn(*args, **kwargs)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@app.get("/api/issues")
def api_list_issues(repo: str = Query(...), limit: int = Query(10)):
    return _safe_call(list_open_issues, repo, limit)


@app.get("/api/pr")
def api_pr_summary(repo: str = Query(...), pr_number: int = Query(...)):
    return _safe_call(get_pr_summary, repo, pr_number)


@app.get("/api/ci")
def api_ci_status(repo: str = Query(...), ref: str = Query("main")):
    return _safe_call(get_ci_status, repo, ref)


@app.get("/api/search")
def api_search_code(repo: str = Query(...), query: str = Query(...)):
    return _safe_call(search_code, repo, query)


# Serve the dashboard's static files at the root URL.
# This must be mounted last so it doesn't swallow the /api/* routes above.
app.mount("/", StaticFiles(directory="static", html=True), name="static")