from app.config import GITHUB_ORG


def construct_github_url(repo_name: str) -> str:
    return f"https://github.com/{GITHUB_ORG}/{repo_name}"