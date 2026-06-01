from dotenv import load_dotenv
load_dotenv()

import os
import sys
from pathlib import Path
from services import JiraClient, capture_dom
from agents import ReviewAgent, TestCaseAgent, AutomationAgent

OUTPUT_ROOT = Path(__file__).resolve().parent / "outputs"


def load_or_run(cache_path: Path, run_fn, label: str) -> str:
    if cache_path.exists():
        print(f"[cache] {label} — {cache_path.name}")
        return cache_path.read_text(encoding="utf-8")
    print(f"[run]   {label} — đang generate...")
    return run_fn()


def run_pipeline(issue_key: str) -> None:
    print(f"\n{'='*50}\n  {issue_key}\n{'='*50}")

    # ── DOM snapshots (chạy 1 lần, cache theo tên snapshot) ────────────────
    try:
        from config.capture_flows import FLOWS
        if FLOWS:
            capture_dom(FLOWS)
    except ImportError:
        pass

    # ── Lazy Jira: chỉ kết nối khi stage thực sự cần run ───────────────────
    _story: dict | None = None

    def get_story() -> dict:
        nonlocal _story
        if _story is None:
            _story = JiraClient().get_issue(issue_key)
        return _story

    load_or_run(
        OUTPUT_ROOT / "reviews" / f"{issue_key}.md",
        lambda: ReviewAgent().run(get_story(), issue_key),
        "Review",
    )

    testcases = load_or_run(
        OUTPUT_ROOT / "testcases" / f"{issue_key}.csv",
        lambda: TestCaseAgent().run(get_story(), issue_key),
        "Test cases",
    )

    load_or_run(
        OUTPUT_ROOT / "automations" / f"{issue_key}.md",
        lambda: AutomationAgent().run(testcases, issue_key),
        "Automation",
    )


def resolve_issue_keys() -> list[str]:
    if len(sys.argv) > 1:
        return [k.strip() for k in sys.argv[1:] if k.strip()]

    env_keys = os.getenv("ISSUE_KEYS", "")
    keys = [k.strip() for k in env_keys.split(",") if k.strip()]
    if keys:
        return keys

    print("Không tìm thấy issue key .env")
    sys.exit(1)


if __name__ == "__main__":
    issue_keys = resolve_issue_keys()
    print(f"Sẽ xử lý {len(issue_keys)} issue(s): {', '.join(issue_keys)}")

    failed = []
    for key in issue_keys:
        try:
            run_pipeline(key)
        except Exception as e:
            print(f"[error] {key}: {e}")
            failed.append(key)

    if failed:
        print(f"\n[done] Thất bại: {', '.join(failed)}")
