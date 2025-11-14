import base64
import requests
from typing import List
import pprint


class GitHubClient:
    """Client for GitHub API."""
    def __init__(self):
        self.token = GITHUB_TOKEN
    
    def get_repos(self, owner: str) -> List[dict]:
        """Get all repos from owner."""
        response = requests.get(
            f"https://api.github.com/users/{owner}/repos",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        return [repo['name'] for repo in response.json()]
    
    def get_branches(self, owner: str, repo: str) -> List[dict]:
        """Get all branches from repository."""
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/branches",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        return [branch['name'] for branch in response.json()]

    def get_path(self, owner: str, repo: str, branch: str) -> List[dict]:
        """Get all paths from repository."""
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        response_json = response.json()
        print(response_json)
        return [item['path'] for item in response_json['tree'] if item['type'] == 'blob']

    def get_file_content(self, owner: str, repo: str, branch: str, path: str) -> str:
        """Get content of file from repository."""
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        response_json = response.json()
        return base64.b64decode(response_json['content']).decode('utf-8')

if __name__ == "__main__":
    client = GitHubClient()
    print(client.get_repos("Foris"))
    print(client.get_branches("Foris", "foris-ml"))
    print(client.get_path("Foris", "foris-ml", "develop"))
    print(client.get_file_content(
        "Foris", "foris-ml", "develop", "images/preprocessing/transformers/encodings.py"
    ))