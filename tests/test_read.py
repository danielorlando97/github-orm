"""Minimalist tests for GitHub ORM read layer."""
import pytest
from github_orm.base import GitHubFileProperty, GitHubModel


class DbConfig(GitHubFileProperty):
    """Database configuration file."""
    class Meta:
        file_name = 'db_config.json'


class TropicalizationConfig(GitHubFileProperty):
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
            db_content = config.db_config.read()
            assert db_content is not None
            assert len(db_content) > 0
            # JSON files should contain db_name or be valid JSON
            assert 'db_name' in db_content or '{' in db_content
            
            # Test reading tropicalization file
            trop_content = config.tropicalization_config.read()
            assert trop_content is not None
            assert len(trop_content) > 0
            # YAML files should contain 'tropicalization' or ':'
            assert 'tropicalization' in trop_content or ':' in trop_content
    
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
        db_content = first_config.db_config.read()
        assert isinstance(db_content, str)
        assert len(db_content) > 0
        
        # Test tropicalization read
        trop_content = first_config.tropicalization_config.read()
        assert isinstance(trop_content, str)
        assert len(trop_content) > 0
    
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
            assert isinstance(config.db_config, DbConfig)
            assert isinstance(
                config.tropicalization_config,
                TropicalizationConfig
            )

