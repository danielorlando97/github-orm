import os
import base64
import requests
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

def get_branches(owner: str, repo: str) -> List[dict]:
    """Get all branches from repository."""
    page = 1
    while True:
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/branches?page={page}",
            headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}
        )
        response_json = response.json()
        for branch in response_json:
            yield branch['name']
            
        if len(response_json) < 30:
            break
            
        page += 1

def _get_branch_sha(owner: str, repo: str, branch: str) -> Optional[str]:
    """Get SHA of branch head."""
    try:
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}",
            headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}
        )
        if response.status_code == 200:
            return response.json()['object']['sha']
    except Exception:
        pass
    return None

def create_branch(owner: str, repo: str, branch: str, from_branch: str = "main") -> bool:
    """Create a new branch from base branch."""
    base_sha = _get_branch_sha(owner, repo, from_branch)
    if not base_sha:
        return False
    
    response = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/git/refs",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        },
        json={
            "ref": f"refs/heads/{branch}",
            "sha": base_sha
        }
    )
    return response.status_code == 201

def delete_branch(owner: str, repo: str, branch: str) -> bool:
    """Delete a branch."""
    response = requests.delete(
        f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
    )
    return response.status_code == 204

def rename_branch(owner: str, repo: str, branch: str, new_name: str) -> bool:
    """Rename a branch."""
    return create_branch(owner, repo, new_name, branch) and delete_branch(owner, repo, branch)

if __name__ == "__main__":
    repo = "github-orm"
    branches = list(get_branches("danielorlando97", repo))
    print(branches)
    
    if create_branch("danielorlando97", repo, "test_branch"):
        branches_1 = list(get_branches("danielorlando97", repo))
        print("New branch created", set(branches_1) - set(branches))
    
    if rename_branch("danielorlando97", repo, "test_branch", "test_branch_1"):
        branches_1 = list(get_branches("danielorlando97", repo))
        print("Branch renamed", set(branches_1) - set(branches))
        
    if delete_branch("danielorlando97", repo, "test_branch_1"):
        branches_2 = list(get_branches("danielorlando97", repo))
        print("Branch deleted", set(branches_2) - set(branches_1))