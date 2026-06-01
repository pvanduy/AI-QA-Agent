from openai import OpenAI
from pathlib import Path
import os


class AutomationAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        project_root = Path(__file__).resolve().parents[1]
        self.prompt_file = project_root / "prompts" / "playwright.txt"
        self.output_dir = project_root / "outputs" / "automations"
        self.snapshots_dir = project_root / "outputs" / "snapshots"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        e2e_env = os.getenv("E2E_PROJECT_ROOT")
        self.e2e_root = Path(e2e_env) if e2e_env else project_root.parent / "e2e"

    def _get_project_structure(self) -> str:
        exclude = {"node_modules", ".git", "target", "dist", ".cache", ".auth"}
        lines = []
        for path in sorted(self.e2e_root.rglob("*")):
            if any(ex in path.parts for ex in exclude):
                continue
            depth = len(path.relative_to(self.e2e_root).parts) - 1
            indent = "  " * depth
            suffix = "/" if path.is_dir() else ""
            lines.append(f"{indent}{path.name}{suffix}")
        return "\n".join(lines)

    def _read_sample_spec(self) -> str:
        sample = self.e2e_root / "tests" / "testcases" / "auth" / "login-success.spec.ts"
        return sample.read_text(encoding="utf-8") if sample.exists() else ""

    def _load_snapshots(self) -> str:
        """Đọc tất cả HTML snapshot đã capture, format thành context cho LLM."""
        if not self.snapshots_dir.exists():
            return ""
        files = sorted(self.snapshots_dir.glob("*.html"))
        if not files:
            return ""
        sections = []
        for f in files:
            sections.append(f"### [{f.name}]\n{f.read_text(encoding='utf-8')}")
        return "\n\n".join(sections)

    def run(self, testcases: str, issue_key: str) -> str:
        snapshots = self._load_snapshots()

        prompt = (
            self.prompt_file.read_text(encoding="utf-8")
            .replace("{issue_key}", issue_key)
            .replace("{project_structure}", self._get_project_structure())
            .replace("{csv_content}", testcases)
            .replace("{sample_spec}", self._read_sample_spec())
            .replace("{dom_snapshots}", snapshots)
        )

        response = self.client.responses.create(
            model=os.getenv("MODEL"),
            input=prompt,
        )

        output_text = response.output_text.strip()
        if output_text.startswith("```"):
            lines = output_text.splitlines()
            if len(lines) >= 2 and lines[-1].strip() == "```":
                output_text = "\n".join(lines[1:-1]).strip()

        (self.output_dir / f"{issue_key}.md").write_text(output_text, encoding="utf-8")
        return output_text


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    load_dotenv()

    key = sys.argv[1] if len(sys.argv) > 1 else "MART-1897"
    csv_path = Path(__file__).resolve().parents[1] / "outputs" / "testcases" / f"{key}.csv"
    testcases = csv_path.read_text(encoding="utf-8")
    print(AutomationAgent().run(testcases, key))
