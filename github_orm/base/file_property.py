import json
import yaml
from dotmap import DotMap
from typing import Optional
from github_orm.github_client.router import GitHubRouter
from github_orm import github_client as GitHubClient


class GitHubFileProperty:
    
    def __init__(self, meta: Optional[GitHubRouter] = None) -> None:
        class_meta = GitHubRouter.from_class(getattr(self, 'Meta', None))
        if meta is None:
            self.meta = class_meta
        else:
            self.meta = meta + class_meta
    
    def read(self):
        content = GitHubClient.get_file_content(
            self.meta.owner,
            self.meta.repo,
            self.meta.branch,
            self.meta.folder_path + self.meta.file_name,
        )
        return content

class GitHubJsonProperty(GitHubFileProperty):
    def read(self):
        try:
            return getattr(self, '__dot_map_content')
        except AttributeError:
            content = super().read()
            self.__current_content = json.loads(content)
            self.__dot_map_content = DotMap(self.__current_content)
            return self.__dot_map_content
    
class GitHubYamlProperty(GitHubFileProperty):
    def read(self):
        try:
            return getattr(self, '__dot_map_content')
        except AttributeError:
            content = super().read()
            self.__current_content = yaml.load(content, Loader=yaml.FullLoader)
            self.__dot_map_content = DotMap(self.__current_content)
            return self.__dot_map_content