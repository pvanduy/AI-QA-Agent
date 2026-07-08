"""
Standalone DOM capture flows — chạy độc lập qua services/dom_capture.py.

Thêm node mới: thêm 1 entry vào NODE_REGISTRY với:
  - "keywords": list keyword để match với story/testcase (lowercase)
  - "steps": list step để navigate đến node và capture DOM
"""

import os
from pathlib import Path

BASE_URL = os.getenv("APP_URL", "https://stage.a2zflow.ai").rstrip("/")
OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "outputs"


# ── Base steps: tạo workflow + chọn Schedule Trigger ──────────────────────────
_BASE_STEPS = [
    {"goto": f"{BASE_URL}/en/overview"},
    {"wait_for": "button:has-text('Create New Workflow'), table"},
    {"capture": "overview"},

    {"click_role": "button", "name": "Create New Workflow"},
    {"wait_for": "[role='dialog'], form"},
    {"fill_role": "textbox", "name": "Workflow Name *", "value": "QA_Capture"},
    {"click_role": "button", "name": "Create Workflow"},
    {"wait_for_url": r"workflow"},
    {"wait_ms": 1500},
    {"capture": "workflow-editor"},

    {"click": ".empty-editor-content-plus-inner-icon"},
    {"wait_for": "[role='option']"},
    {"capture": "node-type-selector"},
    {"click_role": "option", "name": "Schedule"},
    {"wait_for": "[role='menuitem']"},
    {"capture": "node-schedule-submenu"},
    {"click_role": "menuitem", "name": "Schedule Trigger"},
    {"wait_ms": 1500},
    {"capture": "node-schedule-trigger"},
    {"click_role": "button", "name": "Close", "exact": True},
    {"wait_ms": 500},
]


# ── Node Registry ─────────────────────────────────────────────────────────────
# Mỗi node bắt đầu bằng {"click_nth": "rect", "n": 2} để mở node selector
# từ connector output của node trước trên canvas.
NODE_REGISTRY: dict[str, dict] = {

    "human_input_web_form": {
        "keywords": [
            "human input", "web form", "form trigger", "form submission",
            "form title", "form field", "button label", "draft", "published url",
        ],
        "steps": [
            {"click_nth": "rect", "n": 2},
            {"wait_for": "[role='option']"},
            {"capture": "node-type-selector"},

            {"click_role": "option", "name": "Human Input"},
            {"wait_for": "[role='menuitem']"},
            {"capture": "node-submenu"},

            {"click_role": "menuitem", "name": "Web Form"},
            {"wait_ms": 1500},
            {"capture": "node-human-input-connect"},

            {"click_role": "tab", "name": "Configure"},
            {"wait_ms": 1000},
            {"capture": "node-human-input-configure"},
        ],
    },

}


# ── Node selection ─────────────────────────────────────────────────────────────
def _select_nodes(issue_key: str) -> list[str]:
    text = ""
    for path in [
        OUTPUT_ROOT / "reviews"   / f"{issue_key}.md",
        OUTPUT_ROOT / "testcases" / f"{issue_key}.csv",
    ]:
        if path.exists():
            text += path.read_text(encoding="utf-8")[:5000].lower()

    if not text:
        return list(NODE_REGISTRY.keys())

    matched = [
        node_id
        for node_id, info in NODE_REGISTRY.items()
        if any(kw in text for kw in info["keywords"])
    ]
    return matched or list(NODE_REGISTRY.keys())


def get_flows(issue_key: str = "") -> list[dict]:
    selected = _select_nodes(issue_key) if issue_key else list(NODE_REGISTRY.keys())
    flows: list[dict] = list(_BASE_STEPS)
    for node_id in selected:
        flows.extend(NODE_REGISTRY[node_id]["steps"])
    return flows


FLOWS = get_flows("")
