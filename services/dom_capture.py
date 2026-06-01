"""
Flow-based DOM capture service.

Flow được định nghĩa trong config/capture_flows.py — mỗi step là 1 action:
  {"goto": url}                             — navigate
  {"wait_for": selector}                    — chờ element xuất hiện
  {"wait_for_url": regex_pattern}           — chờ URL khớp pattern
  {"click": selector}                       — click element
  {"fill": selector, "value": text}         — điền text
  {"wait_ms": ms}                           — sleep
  {"capture": name}                         — lưu HTML snapshot
"""

from playwright.sync_api import sync_playwright, Page
from pathlib import Path
import os
import re

SNAPSHOTS_DIR = Path(__file__).resolve().parents[1] / "outputs" / "snapshots"
MAX_CHARS = 80_000


def _clean_html(html: str) -> str:
    for tag in ("script", "style", "noscript", "svg"):
        html = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'\s(on\w+|data-v-\w+)="[^"]*"', "", html)
    return html[:MAX_CHARS]


def _is_on_login_page(page: Page) -> bool:
    url = page.url
    return any(kw in url for kw in ("login", "sign-in", "signin", "auth"))


def _do_login(page: Page) -> None:
    username = os.getenv("APP_USERNAME", "")
    password = os.getenv("APP_PASSWORD", "")

    if not username or not password:
        raise RuntimeError(
            "Session hết hạn nhưng chưa set APP_USERNAME / APP_PASSWORD trong .env"
        )

    print(f"[auth]  Đang login với {username}...")

    # Dùng placeholder thay vì role — input[name=email] không có type="text"
    page.get_by_placeholder("Username or Email*").fill(username)
    page.get_by_placeholder("Password*").fill(password)
    page.get_by_role("button", name="Sign in").click()

    # Chờ redirect về trang chính sau login
    page.wait_for_url(
        lambda url: not any(k in url for k in ("login", "sign-in", "signin")),
        timeout=15_000,
    )
    page.wait_for_load_state("networkidle", timeout=15_000)
    print(f"[auth]  Login thành công — {page.url}")


def _run_step(page: Page, step: dict) -> str | None:
    """
    Thực thi 1 step. Trả về tên snapshot nếu là capture step.

    Step types:
      goto, wait_for, wait_for_url, wait_ms, capture  — như cũ
      click          — page.locator(selector).click()
      fill           — page.locator(selector).fill(value)
      click_role     — page.get_by_role(role, name=name).click()
      fill_role      — page.get_by_role(role, name=name).fill(value)
      click_text     — page.get_by_text(text).click()
    """
    if "goto" in step:
        page.goto(step["goto"], timeout=30_000)
        page.wait_for_load_state("networkidle", timeout=15_000)
        if _is_on_login_page(page):
            _do_login(page)

    elif "wait_for" in step:
        page.wait_for_selector(step["wait_for"], timeout=15_000)

    elif "wait_for_url" in step:
        page.wait_for_url(re.compile(step["wait_for_url"]), timeout=15_000)

    elif "click" in step:
        page.locator(step["click"]).first.click()

    elif "fill" in step:
        page.locator(step["fill"]).first.fill(step["value"])

    elif "click_role" in step:
        page.get_by_role(step["click_role"], name=step["name"]).first.click()

    elif "fill_role" in step:
        page.get_by_role(step["fill_role"], name=step["name"]).first.fill(step["value"])

    elif "click_text" in step:
        page.get_by_text(step["click_text"], exact=step.get("exact", False)).first.click()

    elif "wait_ms" in step:
        page.wait_for_timeout(step["wait_ms"])

    elif "capture" in step:
        return step["capture"]

    return None


def capture(flows: list[dict], force: bool = False) -> dict[str, str]:
    """
    Chạy flow-based capture. `flows` là list step từ config/capture_flows.py.
    Trả về {snapshot_name: html}.
    """
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    capture_names = [s["capture"] for s in flows if "capture" in s]
    results: dict[str, str] = {}

    to_run = []
    for name in capture_names:
        path = SNAPSHOTS_DIR / f"{name}.html"
        if path.exists() and not force:
            print(f"[cache] snapshot — {name}.html")
            results[name] = path.read_text(encoding="utf-8")
        else:
            to_run.append(name)

    if not to_run:
        return results

    e2e_root = Path(os.getenv("E2E_PROJECT_ROOT", Path(__file__).resolve().parents[2] / "e2e"))
    auth_file = Path(os.getenv("E2E_AUTH_FILE", e2e_root / "playwright" / ".auth" / "user.json"))
    headful = os.getenv("CAPTURE_HEADFUL", "").lower() in ("1", "true", "yes")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headful)
        context = browser.new_context(
            storage_state=str(auth_file) if auth_file.exists() else None,
            ignore_https_errors=True,
            viewport={"width": 1440, "height": 900},
        )
        page = context.new_page()

        for step in flows:
            action = next(iter(step))
            print(f"[flow]  {action}: {list(step.values())[0]}")

            capture_name = _run_step(page, step)

            if capture_name and capture_name in to_run:
                html = _clean_html(page.content())
                snap_path = SNAPSHOTS_DIR / f"{capture_name}.html"
                snap_path.write_text(html, encoding="utf-8")
                results[capture_name] = html
                print(f"[done]  {snap_path.name} ({len(html):,} chars)")

        browser.close()

    return results


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from config.capture_flows import FLOWS
    capture(FLOWS, force="--force" in sys.argv)
