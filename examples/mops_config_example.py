import github_orm as gorm

class PiperIntegrationConfig:
    class Meta:
        file_name = "piper_config.json"
    
class ConcurrencyConfig:
    class Meta:
        file_name = "concurrency_config.json"

class MopsConfig:
    class Meta:
        owner = "myorg"
        repo = "myrepo"
        branch = r'config/mops/{tenant_code}'
        folder_path = r'configs/mops/{operation_code}/piper_integration/'
        
    tenant: str
    operation: str
    piper_integration_config: PiperIntegrationConfig
    concurrency_config: ConcurrencyConfig
    