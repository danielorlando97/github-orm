import os
import base64
import requests
from typing import List
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

class GitHubClient:
    """Client for GitHub API."""
    def __init__(self):
        self.token = GITHUB_TOKEN
    
    def get_repos(self, owner: str) -> List[dict]:
        """Get all repos from owner."""
        page = 1
        while True:
            response = requests.get(
                f"https://api.github.com/users/{owner}/repos?page={page}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response_json = response.json()
            for repo in response_json:
                yield repo['name']
                
            if len(response_json) < 30:
                break
            
            page += 1
    
    def get_branches(self, owner: str, repo: str) -> List[dict]:
        """Get all branches from repository."""
        page = 1
        while True:
            response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/branches?page={page}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response_json = response.json()
            for branch in response_json:
                yield branch['name']
                
            if len(response_json) < 30:
                break
                
            page += 1

    def get_path(self, owner: str, repo: str, branch: str) -> List[dict]:
        """Get all paths from repository."""
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        response_json = response.json()
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
    print(list(client.get_repos("danielorlando97")))
    print(list(client.get_branches("danielorlando97", "github-orm")))
    print(client.get_path("danielorlando97", "github-orm", "data/test/client_2"))
    print(client.get_file_content(
       "danielorlando97", 
       "github-orm", 
       "data/test/client_2", 
       "service_2/db_config.json"
    ))