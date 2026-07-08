from pathlib import Path
import csv
import io
import os
import re
from .base import BaseAgent


class AutomationAgent(BaseAgent):
    _prompt_name = "playwright.txt"
    _output_subdir = "automations"
    _output_ext = ".md"

    def __init__(self):
        super().__init__()
        e2e_env = os.getenv("E2E_PROJECT_ROOT")
        self.e2e_root = Path(e2e_env) if e2e_env else self._root.parent / "e2e"

    def _get_project_structure(self) -> str:
        exclude = {"node_modules", ".git", "target", "dist", ".cache", ".auth"}
        lines = []
        for path in sorted(self.e2e_root.rglob("*")):
            if any(ex in path.parts for ex in exclude):
                continue
            depth = len(path.relative_to(self.e2e_root).parts) - 1
            lines.append(f"{'  ' * depth}{path.name}{'/' if path.is_dir() else ''}")
        return "\n".join(lines)

    def _read_sample_spec(self) -> str:
        sample = self.e2e_root / "tests" / "testcases" / "auth" / "login-success.spec.ts"
        return sample.read_text(encoding="utf-8") if sample.exists() else ""

    def _load_dom_files(self) -> str:
        """Đọc DOM HTML từ outputs/dom/ — user paste thủ công từ DevTools."""
        dom_dir = self._root / "outputs" / "dom"
        if not dom_dir.exists():
            return ""
        files = sorted(dom_dir.glob("*.html"))
        if not files:
            return ""
        sections = []
        for f in files:
            html = f.read_text(encoding="utf-8")
            for tag in ("svg", "script", "style", "noscript"):
                html = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'\s(on\w+|data-v-\w+)="[^"]*"', "", html)
            sections.append(f"### [{f.stem}]\n{html[:15_000]}")
        return "\n\n".join(sections)

    def _filter_automation_csv(self, csv_text: str) -> str:
        """Lọc chỉ giữ header + các dòng có Automation Candidate = Automation."""
        reader = csv.DictReader(io.StringIO(csv_text))
        rows = [r for r in reader if (r.get("Automation Candidate") or "").strip() == "Automation"]
        if not rows:
            return csv_text
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return out.getvalue()

    def run(self, testcases: str, issue_key: str) -> str:
        automation_csv = self._filter_automation_csv(testcases)
        prompt = (
            self.prompt_file.read_text(encoding="utf-8")
            .replace("{issue_key}", issue_key)
            .replace("{project_structure}", self._get_project_structure())
            .replace("{csv_content}", automation_csv)
            .replace("{sample_spec}", self._read_sample_spec())
            .replace("{dom_context}", self._load_dom_files())
        )
        return self._save(issue_key, self._call_llm(prompt))


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()

    key = sys.argv[1] if len(sys.argv) > 1 else "MART-1897"
    csv_path = Path(__file__).resolve().parents[1] / "outputs" / "testcases" / f"{key}.csv"
    print(AutomationAgent().run(csv_path.read_text(encoding="utf-8"), key))
