from jira import JIRA
import os


class JiraClient:
    def __init__(self):
        self.client = JIRA(
            server=os.getenv("JIRA_URL"),
            basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_TOKEN")),
        )

    def get_issue(self, issue_key: str) -> dict:
        issue = self.client.issue(issue_key)
        return {
            "key": issue.key,
            "summary": issue.fields.summary,
            "description": issue.fields.description or "",
        }


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print(JiraClient().get_issue("MART-1897"))
