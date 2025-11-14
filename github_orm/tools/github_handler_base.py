import inspect
from functools import cached_property, singledispatchmethod
from dataclasses import dataclass
from typing import Optional, List, Union, Dict, Iterator, Type
from github_orm.tools.github_client import GitHubClient
from github_orm.tools.utils import classproperty
from github_orm.tools.property_base import Field


class Meta:
    """Metadata class for models."""
    
    def __init__(
        self, 
        owner: Optional[Union[str, Field]] = None, 
        repo: Optional[Union[str, Field]] = None, 
        branch: Optional[Union[str, Field]] = None, 
        folder_path: Optional[Union[str, Field]] = None, 
        file_name: Optional[Union[str, Field]] = None, 
    ) -> None:
        self.owner = Field.create_field(owner)
        self.repo = Field.create_field(repo)
        self.branch = Field.create_field(branch)
        self.folder_path = Field.create_field(folder_path)
        self.file_name = Field.create_field(file_name)
    
    def __add__(self, other: 'Meta') -> 'Meta':
        if other is None:
            return self
        
        return Meta(
            owner=self.owner or other.owner,
            repo=self.repo or other.repo,
            branch=self.branch or other.branch,
            folder_path=self.folder_path or other.folder_path,
            file_name=self.file_name or other.file_name,
        )

class GitHubFile:
    pass

class GitHubOrmError(Exception):
    """Base exception for GitHub ORM"""
    pass

class GitHubModel:

    def __init__(self, **kwargs) -> None:
        for property, annotation in inspect.get_annotations(self.__class__).items():
            if isinstance(annotation, GitHubFile):
                continue
            
            if property in kwargs:
                property_value = kwargs[property]
            else:
                try:
                    property_value = getattr(self, property)
                except AttributeError:
                    raise GitHubOrmError(f"Property {property} not found in {self.__class__.__name__}")
            
            try:
                property_value = annotation(property_value)
            except Exception:
                pass
            
            setattr(self, property, property_value)

    @classproperty
    def objects(cls) -> 'GitHubHandlerManager':
        meta = None
        if hasattr(cls, 'Meta'):
            meta = Meta(
                owner=getattr(cls.Meta, 'owner', None),
                repo=getattr(cls.Meta, 'repo', None),
                branch=getattr(cls.Meta, 'branch', None),
                folder_path=getattr(cls.Meta, 'folder_path', None),
                file_name=getattr(cls.Meta, 'file_name', None),
                file_type=getattr(cls.Meta, 'file_type', None),
            )
        
        files = {}
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, GitHubFile):
                cls._properties[attr_name] = attr.objects
        
        return GitHubModelManager(cls, meta, files)


class GitHubHandlerManager:
    """Manager for all GitHub handlers"""
    
    _github_client: Optional[GitHubClient] = GitHubClient()
    
    def __init__(
        self, model: Type[GitHubModel], 
        meta: Optional[Meta] = None, 
        files: Optional[Dict[str, 'GitHubFile']] = None
    ) -> None:
        self.model = model
        self.meta = meta
        self.files = files or {}
    
    def all(self) -> Iterator[GitHubModel]:
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
        repos = self._github_client.get_repos(owner)
        for repo_name in repos:
            return self._build_iterator_for_repo(repo_name, owner)

    @singledispatchmethod
    def _build_iterator_for_branch(self, branch, repo, owner) -> Iterator[dict]:
        raise NotImplementedError("This method is not implemented")

    @_build_iterator_for_branch.register
    def _(self, branch: str, repo: str, owner: str) -> Iterator[dict]:
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
        branches = self._github_client.get_branches(owner, repo)
        for branch_name in branches:
            return self._build_iterator_for_branch(branch_name, repo, owner)
    
    def _build_iterator_for_folder(
        self, folder: Union[str, Field], branch: str, repo: str, owner: str
    ) -> Iterator[dict]:
        pattern = self.meta.folder_path
        if self.meta.file_name is not None:
            pattern = pattern + self.meta.file_name
        
        matches = {}
        folders = self._github_client.get_path(owner, repo, branch)
        for folder_path in folders:
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
            }

