"""Minimalist tests for GitHub ORM read layer."""
import pytest
from dotmap import DotMap
from github_orm.base import GitHubModel, GitHubFileProperty
from github_orm.base.file_property import GitHubJsonProperty, GitHubYamlProperty


class ConfigFile(GitHubFileProperty):
    """Base class for configuration files."""
    class Meta:
        file_name = 'db_config.json'

class DbConfig(GitHubJsonProperty):
    """Database configuration file."""
    class Meta:
        file_name = 'db_config.json'


class TropicalizationConfig(GitHubYamlProperty):
    """Tropicalization configuration file."""
    class Meta:
        file_name = 'tropicalization.yaml'


class TestConfig(GitHubModel):
    """Test configuration model."""
    class Meta:
        owner = 'danielorlando97'
        repo = 'github-orm'
        branch = 'data/test/{client}'
        folder_path = '{service}/'
    
    client: str
    service: str
    db_config: DbConfig
    config_file: ConfigFile
    tropicalization_config: TropicalizationConfig


class TestReadLayer:
    """Minimalist tests for read operations."""
    
    def test_read_all_configs(self):
        """Test reading all configurations from GitHub."""
        configs = list(TestConfig.objects.all())
        
        assert len(configs) > 0, (
            "Should find at least one config. "
            "Make sure branches data/test/client_1 and "
            "data/test/client_2 exist in the repository."
        )
        
        # Verify we have expected clients
        clients = {c.client for c in configs}
        assert 'client_1' in clients or 'client_2' in clients
        
        for config in configs:
            assert hasattr(config, 'client')
            assert hasattr(config, 'service')
            assert config.client is not None
            assert config.service is not None
            assert config.client.startswith('client_')
            assert config.service.startswith('service_')
            
            # Test reading db_config file
            db_content = config.db_config
            assert db_content is not None
            assert db_content.db_name is not None
            
            # Test reading tropicalization file
            trop_content = config.tropicalization_config
            assert trop_content is not None
            assert trop_content.tropicalization is not None
    
    def test_read_specific_client_branch(self):
        """Test reading from a specific client branch."""
        all_configs = list(TestConfig.objects.all())
        
        if not all_configs:
            pytest.skip("No configs found in repository")
        
        client_1_configs = [
            c for c in all_configs
            if c.client == 'client_1'
        ]
        
        if not client_1_configs:
            pytest.skip("client_1 branch not found in repository")
        
        assert len(client_1_configs) > 0
        
        # Verify we have services for client_1
        services = {c.service for c in client_1_configs}
        assert len(services) > 0
        assert 'service_1' in services or 'service_2' in services
        
        # Verify all configs are for client_1
        for config in client_1_configs:
            assert config.client == 'client_1'
    
    def test_file_property_read(self):
        """Test reading a single file property."""
        configs = list(TestConfig.objects.all())
        
        if not configs:
            pytest.skip("No configs found in repository")
        
        first_config = configs[0]
        
        # Test db_config read
        db_content = first_config.db_config
        assert isinstance(db_content, DotMap)
        assert db_content.db_name is not None
        
        # Test tropicalization read
        trop_content = first_config.tropicalization_config
        assert isinstance(trop_content, DotMap)
        assert trop_content.tropicalization is not None
    
    def test_model_properties(self):
        """Test that model properties are correctly populated."""
        configs = list(TestConfig.objects.all())
        
        if not configs:
            pytest.skip("No configs found in repository")
        
        for config in configs:
            # Verify dynamic properties from branch pattern
            assert hasattr(config, 'client')
            assert config.client is not None
            
            # Verify dynamic properties from folder pattern
            assert hasattr(config, 'service')
            assert config.service is not None
            
            # Verify file properties are instances
            assert isinstance(config.db_config, DotMap)
            assert isinstance(config.tropicalization_config, DotMap)
            assert isinstance(config.config_file, str)

