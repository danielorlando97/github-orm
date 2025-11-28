import os
import json
import base64
import requests
import logging
from typing import List, Optional
from dotenv import load_dotenv

try:
    from github_orm.github_client.branch_methods import create_branch, delete_branch
except ImportError:
    from branch_methods import create_branch, delete_branch


load_dotenv()
logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

def get_file_content(owner: str, repo: str, branch: str, path: str) -> str:
    """Get content of file from repository."""
    response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}",
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}
    )
    
    response_json = response.json()
    return base64.b64decode(response_json['content']).decode('utf-8')

def create_or_update_file(
    owner: str,
    repo: str,
    branch: str,
    path: str,
    content: str,
    message: str,
):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    sha_actual = None
    actual_content = None
    try:
        response_get = requests.get(url, headers=headers, params={"ref": branch})
        if response_get.status_code == 200:
            sha_actual = response_get.json().get('sha')
            actual_content = base64.b64decode(response_get.json().get('content')).decode('utf-8')
            logger.info(f"File exists. SHA actual: {sha_actual}")
        elif response_get.status_code == 404:
            logger.info("File does not exist. It will be created.")
        else:
            response_get.raise_for_status()

    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting file content: {e}")
        return {"error": str(e), "details": response_get.json()}

    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    if actual_content == content:
        logger.info("File content is the same. No changes needed.")
        return {"success": True, "message": "File content is the same. No changes needed."}

    payload = {
        "message": message,
        "content": encoded_content,
        "branch": branch,
    }
    
    if sha_actual:
        payload["sha"] = sha_actual

    response_put = requests.put(url, headers=headers, data=json.dumps(payload))
    
    if response_put.status_code in [200, 201]:
        logger.info(f"Commit successful: {response_put.json().get('commit', {}).get('sha')}")
        return response_put.json()
    else:
        logger.error(f"Error in commit. Status code: {response_put.status_code}")
        try:
            return {"error": "Error in PUT request", "details": response_put.json()}
        except json.JSONDecodeError:
            return {"error": "Error in PUT request", "details": response_put.text}

def create_pull_request(
    owner: str, 
    repo: str, 
    title: str, 
    head: str,
    base: str, 
    body: str = ""
) -> Optional[int]:
    """Create a pull request. Returns PR number if successful."""
    response = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        },
        json={
            "title": title,
            "head": head,
            "base": base,
            "body": body
        }
    )
    if response.status_code == 201:
        return response.json()['number']
    return None

def delete_pull_request(
    owner: str, 
    repo: str, 
    pr_number: int
) -> bool:
    """Delete a pull request."""
    response = requests.delete(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
    )
    return response.status_code == 204

def merge_pull_request(
    owner: str, 
    repo: str, 
    pr_number: int,
    merge_method: str = "merge"
) -> bool:
    """Merge a pull request."""
    response = requests.put(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/merge",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        },
        json={"merge_method": merge_method}
    )
    return response.status_code == 200



if __name__ == "__main__":
    repo = "github-orm"
    branch = "data/test/client_2"
    path_1 = "service_1/db_config.json"
    path_2 = "service_1/tropicalization-2.yaml"
    content_1 = "This is a test file for service 1"
    content_2 = "This is a test file for service 2"
    
    
    # crear_o_actualizar_archivo_en_github("danielorlando97", repo, "test_branch_1", path_1, content_1, "Test file creation")
    # crear_o_actualizar_archivo_en_github("danielorlando97", repo, "test_branch_1", path_2, content_2, "Test file creation")
    
    pr_number =create_pull_request("danielorlando97", repo, "Test pull request", "test_branch_1", branch, "This is a test pull request")
    if pr_number:
        delete_pull_request("danielorlando97", repo, pr_number)
    # print(get_file_content("danielorlando97", repo, branch, path_1))
    # print("--------------------------------")
    # print(get_file_content("danielorlando97", repo, branch, path_2))
    # print("--------------------------------")
    # if create_branch("danielorlando97", repo, "test_branch_1", branch):
    #     print("Branch created")
    #     create_or_update_file("danielorlando97", repo, "test_branch_1", path_1, content_1, "Test file creation", None)
    #     create_or_update_file("danielorlando97", repo, "test_branch_1", path_2, content_2, "Test file creation", None)
        
    #     create_pull_request("danielorlando97", repo, "Test pull request", "test_branch_1", branch, "This is a test pull request")

    #     delete_branch("danielorlando97", repo, "test_branch_1")
    # print(create_or_update_file("danielorlando97", repo, branch, path_2, content_2, "Test file creation", None))
    # print("--------------------------------")
    # print(get_file_content("danielorlando97", repo, branch, path_1))
    # print("--------------------------------")
    # print(get_file_content("danielorlando97", repo, branch, path_2))
    # print("--------------------------------")
    # print(create_pull_request("danielorlando97", repo, "Test pull request", branch, "main", "This is a test pull request"))
    # print(merge_pull_request("danielorlando97", repo, 1))