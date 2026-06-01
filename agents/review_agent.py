from openai import OpenAI
from pathlib import Path
import os


class ReviewAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.prompt_file = Path(__file__).resolve().parents[1] / "prompts" / "review.txt"
        self.output_dir = Path(__file__).resolve().parents[1] / "outputs" / "reviews"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, story: dict, issue_key: str) -> str:
        prompt = self.prompt_file.read_text(encoding="utf-8").format(requirement=story)

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
    from dotenv import load_dotenv
    load_dotenv()
    from services import JiraClient
    story = JiraClient().get_issue("MART-1897")
    print(ReviewAgent().run(story, "MART-1897"))
