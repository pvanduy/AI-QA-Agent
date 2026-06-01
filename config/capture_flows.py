import os
import time

BASE_URL = os.getenv("APP_URL", "https://stage.a2zflow.ai").rstrip("/")

# Tên workflow tạm để capture (dùng timestamp tránh conflict)
_WF_NAME = f"QA_Capture_{int(time.time())}"

FLOWS = [
    # ── 1. Overview ───────────────────────────────────────────────────────────
    {"goto": f"{BASE_URL}/en/overview"},
    {"wait_for": "button:has-text('Create New Workflow'), table"},
    {"capture": "overview"},

    # ── 2. Tạo workflow mới ───────────────────────────────────────────────────
    {"click_role": "button", "name": "Create New Workflow"},
    {"wait_for": "[role='dialog'], form"},
    {"fill_role": "textbox", "name": "Workflow Name *", "value": _WF_NAME},
    {"click_role": "button", "name": "Create Workflow"},
    {"wait_for_url": r"workflow"},
    {"wait_ms": 1500},
    {"capture": "workflow-editor"},

    # ── 3. Thêm node Human Input ──────────────────────────────────────────────
    {"click": ".empty-editor-content-plus"},
    {"wait_for": "[role='option']"},
    {"capture": "node-type-selector"},

    {"click_role": "option", "name": "Human Input"},
    {"wait_for": "[role='menuitem']"},
    {"capture": "node-submenu"},

    {"click_role": "menuitem", "name": "Human Input Collect data from"},
    {"wait_ms": 1500},
    {"capture": "node-config-connect-tab"},

    # ── 4. Mở tab Configure (chứa các field và ℹ️ icon) ──────────────────────
    {"click_role": "tab", "name": "Configure"},
    {"wait_ms": 1000},
    {"capture": "node-config-configure-tab"},
]
