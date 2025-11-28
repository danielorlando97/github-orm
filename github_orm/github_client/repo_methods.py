import os
import base64
import requests
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

def get_repos(owner: str) -> List[dict]:
    """Get all repos from owner."""
    page = 1
    while True:
        response = requests.get(
            f"https://api.github.com/users/{owner}/repos?page={page}",
            headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}
        )
        response_json = response.json()
        for repo in response_json:
            yield repo['name']
            
        if len(response_json) < 30:
            break
        
        page += 1

def create_repo(
    name: str, description: str = "", private: bool = False, auto_init: bool = True
) -> bool:
    """Create a new repository for authenticated user."""
    response = requests.post(
        "https://api.github.com/user/repos",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        },
        json={
            "name": name,
            "description": description,
            "private": private,
            "auto_init": auto_init
        }
    )
    return response.status_code == 201

def delete_repo(owner: str, repo: str) -> bool:
    """Delete a repository."""
    response = requests.delete(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
    )
    return response.status_code == 204

def rename_repo(owner: str, repo: str, new_name: str) -> bool:
    """Rename a repository."""
    response = requests.patch(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        },
        json={"name": new_name}
    )
    return response.status_code == 200

if __name__ == "__main__":
    repos = list(get_repos("danielorlando97"))
    print(repos)
    
    if create_repo("test_repo", "This is a test repository"):
        repos_1 = list(get_repos("danielorlando97"))
        print("New repo created", set(repos_1) - set(repos))
    
    if rename_repo("danielorlando97", "test_repo", "test_repo_1"):
        repos_2 = list(get_repos("danielorlando97"))
        print("Repo renamed", set(repos_2) - set(repos))
        
    if delete_repo("danielorlando97", "test_repo_1"):
        repos_3 = list(get_repos("danielorlando97"))
        print("Repo deleted", set(repos_3) - set(repos))

