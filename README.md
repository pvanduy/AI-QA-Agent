# AI QA Agent

Project Python hỗ trợ QA workflow theo luồng:
1) Lấy Jira story
2) Review requirement bằng AI
3) Sinh test case CSV bằng AI
4) (Tùy chọn) Sinh Playwright script

## Cấu trúc thư mục

```text
ai-qa-agent/
├─ agents/
│  ├─ __init__.py
│  ├─ review_agent.py
│  ├─ testcase_agent.py
│  └─ automation_agent.py
├─ services/
│  ├─ __init__.py
│  └─ jira_client.py
├─ prompts/
│  ├─ review.txt
│  ├─ testcase.txt
│  └─ playwright.txt
├─ outputs/
├─ main.py
└─ requirements.txt
```

## Yêu cầu

- Python 3.9+
- Tài khoản Jira + API token
- OpenAI API key

## Cài đặt

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Cấu hình biến môi trường

Tạo file `.env`:

```env
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_TOKEN=your_jira_api_token
OPENAI_API_KEY=your_openai_api_key
MODEL=gpt-5
```

Nạp biến môi trường trước khi chạy:

```bash
set -a
source .env
set +a
```

## Chạy project

Mặc định `main.py` đang xử lý issue key `MART-1897`.

```bash
python main.py
```

Luồng hiện tại:
- `JiraClient` lấy `summary` + `description` từ Jira
- `ReviewAgent` đọc prompt `prompts/review.txt` và sinh review markdown
- `TestCaseAgent` đọc prompt `prompts/testcase.txt` và sinh test cases dạng CSV text
- `AutomationAgent` đang để sẵn, chưa bật trong `main.py`

## Import package nội bộ

Project đã setup package:
- `services`: `from services import JiraClient`
- `agents`: `from agents import ReviewAgent, TestCaseAgent, AutomationAgent`

## Prompt engineering

Bạn có thể chỉnh trực tiếp:
- `prompts/review.txt`
- `prompts/testcase.txt`
- `prompts/playwright.txt`

Mẹo:
- Giữ placeholder `{requirement}` để agent bơm dữ liệu Jira vào prompt.
- Với output CSV, giữ ràng buộc format để import Google Sheets ổn định.

## Lưu ý hiện tại

- `ReviewAgent` ghi file vào `outputs/reviews/<issue_key>.md`
- `TestCaseAgent` ghi file vào `outputs/testcases/{issue_key}.csv` (đúng theo code hiện tại)
- Nếu chưa có folder con trong `outputs`, hãy tạo trước:

```bash
mkdir -p outputs/reviews outputs/testcases
```

## Dependencies

```txt
jira==3.10.5
openai==2.38.0
```
