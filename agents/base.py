from openai import OpenAI
from pathlib import Path
import os

_ROOT = Path(__file__).resolve().parents[1]


class BaseAgent:
    _prompt_name: str
    _output_subdir: str
    _output_ext: str

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._root = _ROOT
        self.prompt_file = _ROOT / "prompts" / self._prompt_name
        self.output_dir = _ROOT / "outputs" / self._output_subdir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _call_llm(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=os.getenv("MODEL"),
            input=prompt,
        )
        text = (response.output_text or "").strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if len(lines) >= 2 and lines[-1].strip() == "```":
                text = "\n".join(lines[1:-1]).strip()
        return text

    def _save(self, issue_key: str, text: str) -> str:
        (self.output_dir / f"{issue_key}{self._output_ext}").write_text(text, encoding="utf-8")
        return text
