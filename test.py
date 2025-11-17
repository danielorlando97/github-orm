import logging
logging.basicConfig(level=logging.DEBUG)

from github_orm.tools.github_handler_base import GitHubModel, GitHubFile

class DbConfig(GitHubFile):
    class Meta:
        file_name = 'db_config.json'

class TropicalizationConfig(GitHubFile):
    class Meta:
        file_name = 'tropicalization.yaml'

class TestConfig(GitHubModel):
    class Meta:
        owner = 'danielorlando97'
        repo = 'github-orm'
        branch = 'data/test/{client}'
        folder_path = '{service}/'
        
    client: str
    service: str
    db_config: DbConfig
    tropicalization_config: TropicalizationConfig

for config in TestConfig.objects.all():
    print("--------------------------------")
    print(config.client)
    print(config.service)
    print(config.db_config.read())
    print(config.tropicalization_config.read())

