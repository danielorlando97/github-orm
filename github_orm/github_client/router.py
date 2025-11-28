from typing import Optional, Union
from github_orm.base.string_property import Field


class GitHubRouter:
    """GitHubRouter class for models."""
    
    def __init__(
        self, 
        owner: Optional[Union[str, Field]] = None, 
        repo: Optional[Union[str, Field]] = None, 
        branch: Optional[Union[str, Field]] = None, 
        folder_path: Optional[Union[str, Field]] = None, 
        file_name: Optional[Union[str, Field]] = None, 
    ) -> None:
        self.owner = Field.create_field(getattr(self, 'owner', owner))
        self.repo = Field.create_field(getattr(self, 'repo', repo))
        self.branch = Field.create_field(getattr(self, 'branch', branch))
        self.folder_path = Field.create_field(getattr(self, 'folder_path', folder_path))
        self.file_name = Field.create_field(getattr(self, 'file_name', file_name))
    
    def __add__(self, other: 'GitHubRouter') -> 'GitHubRouter':
        if other is None:
            return self
        
        return GitHubRouter(
            owner=self.owner or other.owner,
            repo=self.repo or other.repo,
            branch=self.branch or other.branch,
            folder_path=self.folder_path or other.folder_path,
            file_name=self.file_name or other.file_name,
        )
    
    @staticmethod
    def from_class(meta) -> 'GitHubRouter':
        if meta is None:
            return GitHubRouter()
        
        return GitHubRouter(
            owner=getattr(meta, 'owner', None),
            repo=getattr(meta, 'repo', None),
            branch=getattr(meta, 'branch', None),
            folder_path=getattr(meta, 'folder_path', None),
            file_name=getattr(meta, 'file_name', None),
        )