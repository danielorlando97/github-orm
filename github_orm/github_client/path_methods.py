import os
import base64
import requests
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

def get_paths(owner: str, repo: str, branch: str) -> List[dict]:
    """Get all paths from repository."""
    response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}
    )
    
    response_json = response.json()
    return [item['path'] for item in response_json['tree'] if item['type'] == 'blob']


def create_multiple_files_in_path(token, owner, repo, file_dict, target_path, branch="main", commit_message="FEAT: Adding new files via Git Trees API"):
    """
    Creates multiple files with specified content inside a target path (which can be new).

    :param token: Your GitHub Personal Access Token (PAT).
    :param owner: The account or organization owner of the repository.
    :param repo: The name of the repository.
    :param file_dict: A dictionary where key is the filename and value is the content string.
    :param target_path: The directory where files will be created (e.g., 'data/new_files').
    :param branch: The branch to commit the changes to (default: 'main').
    :param commit_message: The commit message for this operation.
    :return: A dictionary with the status and the commit URL.
    """
    base_url = f"https://api.github.com/repos/{owner}/{repo}"
    target_path = target_path.strip('/')
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }

    # --- 1. GET HEAD REFERENCE AND BASE TREE ---
    
    ref_url = f"{base_url}/git/refs/heads/{branch}"
    response = requests.get(ref_url, headers=headers)
    if response.status_code != 200:
        return {"status": "Error", "message": f"Failed to get branch reference: {response.json().get('message', response.text)}"}
        
    head_commit_sha = response.json()["object"]["sha"]
    
    commit_url = f"{base_url}/git/commits/{head_commit_sha}"
    response = requests.get(commit_url, headers=headers)
    base_tree_sha = response.json()["tree"]["sha"]
    
    # --- 2. PRE-CREATE BLOBS (File Content) ---
    # We must create the content (blobs) first to get their SHA, 
    # as the tree object must reference content by SHA, not by raw content.
    
    blob_shas = {}
    print(f"-> Creating {len(file_dict)} content blobs...")
    
    for filename, content in file_dict.items():
        # Encode content to Base64
        content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        blob_payload = {
            "content": content_b64,
            "encoding": "base64"
        }
        
        blob_post_url = f"{base_url}/git/blobs"
        response = requests.post(blob_post_url, headers=headers, data=json.dumps(blob_payload))
        
        if response.status_code != 201:
            return {"status": "Error", "message": f"Failed to create blob for {filename}: {response.json().get('message', response.text)}"}
            
        blob_shas[filename] = response.json()["sha"]
        
    # --- 3. BUILD THE CHANGES FOR THE NEW TREE (Creation) ---

    tree_changes = []
    
    for filename, sha in blob_shas.items():
        # Creation/Addition entry
        tree_changes.append({
            "path": f"{target_path}/{filename}",
            "mode": "100644", # Standard file mode
            "type": "blob",
            "sha": sha # Reference the newly created content blob
        })

    # --- 4. CREATE THE NEW GIT TREE, COMMIT, AND UPDATE REF (Steps 5-7) ---
    
    new_tree_payload = {
        "base_tree": base_tree_sha,
        "tree": tree_changes
    }
    
    tree_post_url = f"{base_url}/git/trees"
    print("-> Creating new Git Tree (Adding files)...")
    response = requests.post(tree_post_url, headers=headers, data=json.dumps(new_tree_payload))
    if response.status_code != 201:
        return {"status": "Error", "message": f"Failed to create new tree: {response.json().get('message', response.text)}"}
        
    new_tree_sha = response.json()["sha"]

    new_commit_payload = {
        "message": commit_message,
        "tree": new_tree_sha,
        "parents": [head_commit_sha]
    }
    
    commit_post_url = f"{base_url}/git/commits"
    print("-> Creating new Commit...")
    response = requests.post(commit_post_url, headers=headers, data=json.dumps(new_commit_payload))
    if response.status_code != 201:
        return {"status": "Error", "message": f"Failed to create new commit: {response.json().get('message', response.text)}"}
        
    new_commit_sha = response.json()["sha"]
    new_commit_url = response.json()["html_url"]

    update_ref_payload = {
        "sha": new_commit_sha
    }
    
    print(f"-> Updating branch reference '{branch}'...")
    response = requests.patch(ref_url, headers=headers, data=json.dumps(update_ref_payload))
    if response.status_code != 200:
        return {"status": "Error", "message": f"Failed to update branch reference: {response.json().get('message', response.text)}"}

    return {
        "status": "Success",
        "message": f"Successfully created {len(file_dict)} files in '{target_path}'.",
        "commit_sha": new_commit_sha,
        "commit_url": new_commit_url
    }

def rename_github_folder(token, owner, repo, old_path, new_path, branch="main", commit_message="REFACTOR: Renaming folder via Git Trees API"):
    """
    Renames a folder (directory) in a GitHub repository using the Git Trees API.

    :param token: Your GitHub Personal Access Token (PAT).
    :param owner: The account or organization owner of the repository.
    :param repo: The name of the repository.
    :param old_path: The current path of the folder to rename (e.g., 'src/config').
    :param new_path: The new path for the folder (e.g., 'src/settings').
    :param branch: The branch to commit the changes to (default: 'main').
    :param commit_message: The commit message for this operation.
    :return: A dictionary with the status and the commit URL.
    """
    base_url = f"https://api.github.com/repos/{owner}/{repo}"
    
    # 1. Setup authentication headers
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }

    # Ensure paths do not end with '/'
    old_path = old_path.strip('/')
    new_path = new_path.strip('/')
    
    # --- 2. GET HEAD REFERENCE AND BASE TREE ---
    
    # Get the SHA of the current latest commit
    ref_url = f"{base_url}/git/refs/heads/{branch}"
    print(f"-> Fetching branch reference for '{branch}'...")
    response = requests.get(ref_url, headers=headers)
    if response.status_code != 200:
        return {"status": "Error", "message": f"Failed to get branch reference: {response.json().get('message', response.text)}"}
        
    head_commit_sha = response.json()["object"]["sha"]
    
    # Get the SHA of the base tree associated with the commit
    commit_url = f"{base_url}/git/commits/{head_commit_sha}"
    response = requests.get(commit_url, headers=headers)
    base_tree_sha = response.json()["tree"]["sha"]
    
    # --- 3. GET RECURSIVE TREE TO FIND FILES ---

    # Get the recursive tree to find all files and their SHAs within the old folder
    tree_url = f"{base_url}/git/trees/{base_tree_sha}?recursive=1"
    print("-> Getting recursive file structure...")
    response = requests.get(tree_url, headers=headers)
    repo_tree = response.json().get("tree", [])

    # Filter for blob (file) entries that are inside the 'old_path'
    files_to_move = [
        item for item in repo_tree 
        if item["type"] == "blob" and item["path"].startswith(f"{old_path}/")
    ]
    
    if not files_to_move:
        # Check if the folder exists and contains files
        return {"status": "Warning", "message": f"No files found in path '{old_path}'. Renaming aborted."}

    print(f"-> Found {len(files_to_move)} files to move.")
    
    # --- 4. BUILD THE CHANGES FOR THE NEW TREE ---

    tree_changes = []
    
    for file in files_to_move:
        # 1. Calculate the relative path (e.g., 'file.txt')
        relative_path = file["path"][len(old_path) + 1:]
        
        # 2. DELETE Entry (sets 'sha': null at the old path)
        # This removes the file from the new tree's view
        tree_changes.append({
            "path": file["path"],
            "mode": file["mode"],
            "type": file["type"],
            "sha": None # Null SHA = Delete operation
        })

        # 3. CREATE/MOVE Entry (adds the file at the new path)
        tree_changes.append({
            "path": f"{new_path}/{relative_path}",
            "mode": file["mode"],
            "type": file["type"],
            "sha": file["sha"] # Use the existing content SHA (no change in content)
        })

    # --- 5. CREATE THE NEW GIT TREE ---
    
    new_tree_payload = {
        "base_tree": base_tree_sha,
        "tree": tree_changes
    }
    
    tree_post_url = f"{base_url}/git/trees"
    print("-> Creating new Git Tree...")
    response = requests.post(tree_post_url, headers=headers, data=json.dumps(new_tree_payload))
    if response.status_code != 201:
        return {"status": "Error", "message": f"Failed to create new tree: {response.json().get('message', response.text)}"}
        
    new_tree_sha = response.json()["sha"]

    # --- 6. CREATE THE NEW COMMIT ---
    
    new_commit_payload = {
        "message": commit_message,
        "tree": new_tree_sha,
        "parents": [head_commit_sha]
    }
    
    commit_post_url = f"{base_url}/git/commits"
    print("-> Creating new Commit...")
    response = requests.post(commit_post_url, headers=headers, data=json.dumps(new_commit_payload))
    if response.status_code != 201:
        return {"status": "Error", "message": f"Failed to create new commit: {response.json().get('message', response.text)}"}
        
    new_commit_sha = response.json()["sha"]
    new_commit_url = response.json()["html_url"]

    # --- 7. UPDATE THE BRANCH REFERENCE (PUSH) ---
    
    update_ref_payload = {
        "sha": new_commit_sha
    }
    
    print(f"-> Updating branch reference '{branch}' to the new commit...")
    response = requests.patch(ref_url, headers=headers, data=json.dumps(update_ref_payload))
    if response.status_code != 200:
        return {"status": "Error", "message": f"Failed to update branch reference: {response.json().get('message', response.text)}"}

    return {
        "status": "Success",
        "message": f"Folder '{old_path}' successfully renamed to '{new_path}'.",
        "commit_sha": new_commit_sha,
        "commit_url": new_commit_url
    }


def delete_github_path(token, owner, repo, target_path, branch="main", commit_message="DELETE: Removing path via Git Trees API"):
    """
    Deletes a file or all contents within a folder recursively in a GitHub repository 
    by setting the SHA to null in the Git Tree.

    :param token: Your GitHub Personal Access Token (PAT).
    :param owner: The account or organization owner of the repository.
    :param repo: The name of the repository.
    :param target_path: The path (file or folder) to be deleted (e.g., 'src/old_file.txt' or 'docs/temp').
    :param branch: The branch to commit the changes to (default: 'main').
    :param commit_message: The commit message for this operation.
    :return: A dictionary with the status and the commit URL.
    """
    base_url = f"https://api.github.com/repos/{owner}/{repo}"
    target_path = target_path.strip('/')
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }

    # --- 1. GET HEAD REFERENCE AND BASE TREE ---
    
    ref_url = f"{base_url}/git/refs/heads/{branch}"
    response = requests.get(ref_url, headers=headers)
    if response.status_code != 200:
        return {"status": "Error", "message": f"Failed to get branch reference: {response.json().get('message', response.text)}"}
        
    head_commit_sha = response.json()["object"]["sha"]
    
    commit_url = f"{base_url}/git/commits/{head_commit_sha}"
    response = requests.get(commit_url, headers=headers)
    base_tree_sha = response.json()["tree"]["sha"]
    
    # --- 2. GET RECURSIVE TREE TO FIND ITEMS TO DELETE ---

    # Get the recursive tree to find all files and their SHAs
    tree_url = f"{base_url}/git/trees/{base_tree_sha}?recursive=1"
    print("-> Getting recursive file structure to identify targets...")
    response = requests.get(tree_url, headers=headers)
    repo_tree = response.json().get("tree", [])

    # Identify targets:
    # If the target is a file, find an exact match.
    # If the target is a folder, find all items starting with the folder path.
    items_to_delete = [
        item for item in repo_tree 
        if item["path"] == target_path or item["path"].startswith(f"{target_path}/")
    ]
    
    if not items_to_delete:
        return {"status": "Warning", "message": f"Path '{target_path}' not found or is empty. Deletion aborted."}

    print(f"-> Found {len(items_to_delete)} item(s) to delete.")
    
    # --- 3. BUILD THE CHANGES FOR THE NEW TREE (Deletion) ---

    tree_changes = []
    
    for item in items_to_delete:
        # Deletion is achieved by setting the SHA to None (null)
        tree_changes.append({
            "path": item["path"],
            "mode": item["mode"],
            "type": item["type"],
            "sha": None # Null SHA = Delete operation
        })

    # --- 4. CREATE THE NEW GIT TREE, COMMIT, AND UPDATE REF (Steps 5-7 from previous function) ---
    
    new_tree_payload = {
        "base_tree": base_tree_sha,
        "tree": tree_changes
    }
    
    tree_post_url = f"{base_url}/git/trees"
    print("-> Creating new Git Tree (Deletion)...")
    response = requests.post(tree_post_url, headers=headers, data=json.dumps(new_tree_payload))
    if response.status_code != 201:
        return {"status": "Error", "message": f"Failed to create new tree: {response.json().get('message', response.text)}"}
        
    new_tree_sha = response.json()["sha"]

    new_commit_payload = {
        "message": commit_message,
        "tree": new_tree_sha,
        "parents": [head_commit_sha]
    }
    
    commit_post_url = f"{base_url}/git/commits"
    print("-> Creating new Commit...")
    response = requests.post(commit_post_url, headers=headers, data=json.dumps(new_commit_payload))
    if response.status_code != 201:
        return {"status": "Error", "message": f"Failed to create new commit: {response.json().get('message', response.text)}"}
        
    new_commit_sha = response.json()["sha"]
    new_commit_url = response.json()["html_url"]

    update_ref_payload = {
        "sha": new_commit_sha
    }
    
    print(f"-> Updating branch reference '{branch}'...")
    response = requests.patch(ref_url, headers=headers, data=json.dumps(update_ref_payload))
    if response.status_code != 200:
        return {"status": "Error", "message": f"Failed to update branch reference: {response.json().get('message', response.text)}"}

    return {
        "status": "Success",
        "message": f"Path '{target_path}' successfully deleted.",
        "commit_sha": new_commit_sha,
        "commit_url": new_commit_url
    }



# --- USAGE EXAMPLE (REPLACE WITH YOUR VALUES) ---

# # Make sure you have the 'requests' library installed: pip install requests
# GITHUB_TOKEN = "YOUR_PERSONAL_GITHUB_TOKEN"
# REPO_OWNER = "the-user-or-organization"
# REPO_NAME = "the-repository-name"
# OLD_FOLDER = "old_documentation"
# NEW_FOLDER = "new_docs"
# BRANCH = "main"

# # result = rename_github_folder(
# #     token=GITHUB_TOKEN,
# #     owner=REPO_OWNER,
# #     repo=REPO_NAME,
# #     old_path=OLD_FOLDER,
# #     new_path=NEW_FOLDER,
# #     branch=BRANCH,
# #     commit_message=f"REFACTOR: Renaming {OLD_FOLDER} to {NEW_FOLDER} via API"
# # )

# # print("\nFinal Result:")
# # print(json.dumps(result, indent=2))