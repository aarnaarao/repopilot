"""
Quick manual test script for RepoPilot's tools.
This calls the underlying tool functions directly (not through the MCP
protocol) so you can verify they work before wiring up a real MCP client.

Run with:
    python test_tools.py
"""

from server import list_open_issues, get_pr_summary, get_ci_status, search_code

TEST_REPO = "facebook/react"  # any public repo works

def run(label, fn, *args, **kwargs):
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print("=" * 60)
    try:
        result = fn(*args, **kwargs)
        print(result)
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    run("list_open_issues", list_open_issues, TEST_REPO, limit=5)
    run("get_ci_status", get_ci_status, TEST_REPO, ref="main")
    run("search_code", search_code, TEST_REPO, "useState")

    # get_pr_summary needs a real, currently-open PR number, so this will
    # likely 404 on a random guess - that's expected and fine, it proves
    # our error handling works. Replace 1 with a real PR number to see
    # a full summary.
    run("get_pr_summary", get_pr_summary, TEST_REPO, 1)
    