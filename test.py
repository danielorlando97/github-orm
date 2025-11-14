# from github_orm.tools.github_handler_base import Meta, GitHubHandlerManager, GitHubModel
# from github_orm.tools.property_base import Field

# meta = Meta(
#     owner="Foris",
#     repo="foris-ml",
#     branch="develop",
#     folder_path="images/{image}",
# )
# manager = GitHubHandlerManager(GitHubModel, meta)
# for data in manager.all():
#     print(data)
# import inspect

# class PiperIntegrationConfig:
#     class Meta:
#         file_name = "piper_config.json"
    
# class ConcurrencyConfig:
#     class Meta:
#         file_name = "concurrency_config.json"

# class MopsConfig:
#     class Meta:
#         owner = "myorg"
#         repo = "myrepo"
#         branch = r'config/mops/{tenant_code}'
#         folder_path = r'configs/mops/{operation_code}/piper_integration/'
        
#     tenant: str = None
#     operation: str
#     piper_integration_config: PiperIntegrationConfig
#     concurrency_config: ConcurrencyConfig

# for property in inspect.getmembers(MopsConfig):
#     print(property)
# print("--------------------------------")
# for property, value in inspect.get_annotations(MopsConfig).items():
#     print(property, value)

