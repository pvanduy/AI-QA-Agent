from .base import BaseAgent


class TestCaseAgent(BaseAgent):
    _prompt_name = "testcase.txt"
    _output_subdir = "testcases"
    _output_ext = ".csv"

    def run(self, story: dict, issue_key: str) -> str:
        prompt = self.prompt_file.read_text(encoding="utf-8").format(requirement=story)
        return self._save(issue_key, self._call_llm(prompt))


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    from services import JiraClient
    story = JiraClient().get_issue("MART-1897")
    print(TestCaseAgent().run(story, "MART-1897"))
