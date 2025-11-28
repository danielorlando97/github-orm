class GitHubFileProperty:
    
    def __init__(self, meta: Optional[Meta]) -> None:
        self.meta = meta + Meta.from_class(getattr(self, 'Meta', None))
    
    def read(self):
        content = GitHubClient.get_file_content(
            self.meta.owner,
            self.meta.repo,
            self.meta.branch,
            self.meta.folder_path + self.meta.file_name,
        )
        return content