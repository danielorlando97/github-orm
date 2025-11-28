import logging
from functools import singledispatchmethod
from typing import Optional, Union, Dict, Iterator, Type, TYPE_CHECKING
from github_orm.github_client.router import GitHubRouter
from github_orm.base.string_property import Field
from github_orm import github_client as GitHubClient

if TYPE_CHECKING:
    from github_orm.base.model import GitHubModel
    from github_orm.tools.github_handler_base import GitHubFile

logger = logging.getLogger(__name__)


class GitHubQueryBuilder:
    """Query builder for all GitHub queries"""
    
    def __init__(
        self, model: Type['GitHubModel'], 
        meta: Optional[GitHubRouter] = None, 
        files: Optional[Dict[str, 'GitHubFile']] = None
    ) -> None:
        self.model = model
        self.meta = meta
        self.files = files or {}
    
    def all(self) -> Iterator['GitHubModel']:
        for data in self._build_iterator():
            yield self.model(**data)
    
    def _build_iterator(self) -> Iterator[dict]:
        if self.meta is None or self.meta.owner is None or self.meta.repo is None:
            return iter([])
        
        return self._build_iterator_for_repo(self.meta.repo, self.meta.owner)
    
    @singledispatchmethod
    def _build_iterator_for_repo(self, repo, owner) -> Iterator[dict]:
        raise NotImplementedError("This method is not implemented")

    @_build_iterator_for_repo.register
    def _(self, repo: str, owner: str) -> Iterator[dict]:  
        logger.debug(f"Building iterator for string repo: {repo}")
        data = {
            'repo': repo,
        }
          
        if self.meta.branch is None:
            yield data
        else:
            for branch in self._build_iterator_for_branch(
                self.meta.branch, repo, owner
            ):
                yield data | branch

    @_build_iterator_for_repo.register
    def _(self, repo:  Field, owner: str) -> Iterator[dict]:
        logger.debug(f"Building iterator for field repo: {repo.format}")
        repos = GitHubClient.get_repos(owner)
        for repo_name in repos:
            if data := repo.match(repo_name):            
                for item in self._build_iterator_for_repo(repo_name, owner):
                    yield item | data

    @singledispatchmethod
    def _build_iterator_for_branch(self, branch, repo, owner) -> Iterator[dict]:
        raise NotImplementedError("This method is not implemented")

    @_build_iterator_for_branch.register
    def _(self, branch: str, repo: str, owner: str) -> Iterator[dict]:
        logger.debug(f"Building iterator for string branch: {branch}")
        data = {
            'branch': branch,
        }
        
        if self.meta.folder_path is None:
            yield data
        else:
            for folder in self._build_iterator_for_folder(
                self.meta.folder_path, branch, repo, owner 
            ):
                yield data | folder
                
    @_build_iterator_for_branch.register
    def _(self, branch: Field, repo: str, owner: str) -> Iterator[dict]:
        logger.debug(f"Building iterator for field branch: {branch.format}")
        branches = GitHubClient.get_branches(owner, repo)
        for branch_name in branches:
            if data := branch.match(branch_name):
                for item in self._build_iterator_for_branch(branch_name, repo, owner):
                    yield item | data
    
    def _build_iterator_for_folder(
        self, folder: Union[str, Field], branch: str, repo: str, owner: str
    ) -> Iterator[dict]:
        pattern = self.meta.folder_path
        if self.meta.file_name is not None:
            pattern = pattern + self.meta.file_name
        
        logger.debug(f"Building iterator for folder: {pattern}")
        
        matches = {}
        folders = GitHubClient.get_paths(owner, repo, branch)
        for folder_path in folders:
            logger.debug(f"Folder path: {folder_path}")
            if isinstance(pattern, str):
                if folder_path.startswith(pattern):
                    matches[folder_path] = {}
            else:
                if data := pattern.match(folder_path):
                    matches[pattern.build_path(data)] = data
        
        for match, data in matches.items():
            yield {
                'folder': match,
                **data,
                'meta' : {
                    'owner': owner,
                    'repo': repo,
                    'branch': branch,
                    'folder_path': match
                }
            }
