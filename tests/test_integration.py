"""Integration tests for GitHub ORM."""
import pytest
from unittest.mock import Mock, patch
from github_orm.tools.github_handler_base import GitHubModel, GitHubFile


class TestIntegration:
    """Integration tests for complete ORM workflow."""
    
    @patch('github_orm.tools.github_client.GitHubClient')
    def test_full_workflow_example(self, mock_client_class):
        """Test complete workflow similar to test.py example."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Setup mocks
        mock_client.get_branches.return_value = iter([
            'data/test/client_1',
            'data/test/client_2'
        ])
        mock_client.get_path.return_value = [
            'service_1/db_config.json',
            'service_1/tropicalization.yaml',
            'service_2/db_config.json',
            'service_2/tropicalization.yaml',
        ]
        mock_client.get_file_content.return_value = '{"key": "value"}'
        
        class DbConfig(GitHubFile):
            class Meta:
                file_name = 'db_config.json'
        
        class TropicalizationConfig(GitHubFile):
            class Meta:
                file_name = 'tropicalization.yaml'
        
        class TestConfig(GitHubModel):
            class Meta:
                owner = 'testowner'
                repo = 'testrepo'
                branch = 'data/test/{client}'
                folder_path = '{service}/'
            
            client: str
            service: str
            db_config: DbConfig
            tropicalization_config: TropicalizationConfig
        
        # Get manager and set mock client
        manager = TestConfig.objects
        manager._github_client = mock_client
        
        results = list(TestConfig.objects.all())
        assert len(results) == 4  # 2 clients * 2 services
        
        # Verify first result
        first = results[0]
        assert first.client in ['client_1', 'client_2']
        assert first.service in ['service_1', 'service_2']
        assert isinstance(first.db_config, DbConfig)
        assert isinstance(first.tropicalization_config, TropicalizationConfig)
        
        # Test reading file content
        content = first.db_config.read()
        assert content == '{"key": "value"}'
    
    @patch('github_orm.tools.github_client.GitHubClient')
    def test_mops_config_example(self, mock_client_class):
        """Test MopsConfig example from mops_config_example.py."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_client.get_branches.return_value = iter([
            'config/mops/tenant1',
            'config/mops/tenant2'
        ])
        mock_client.get_path.return_value = [
            'configs/mops/op1/piper_integration/piper_config.json',
            'configs/mops/op1/piper_integration/concurrency_config.json',
            'configs/mops/op2/piper_integration/piper_config.json',
        ]
        mock_client.get_file_content.return_value = '{"key": "value"}'
        
        class PiperIntegrationConfig(GitHubFile):
            class Meta:
                file_name = "piper_config.json"
        
        class ConcurrencyConfig(GitHubFile):
            class Meta:
                file_name = "concurrency_config.json"
        
        class MopsConfig(GitHubModel):
            class Meta:
                owner = "myorg"
                repo = "myrepo"
                branch = 'config/mops/{tenant_code}'
                folder_path = 'configs/mops/{operation_code}/piper_integration/'
            
            tenant: str
            operation: str
            piper_integration_config: PiperIntegrationConfig
            concurrency_config: ConcurrencyConfig
        
        manager = MopsConfig.objects
        manager._github_client = mock_client
        
        results = list(MopsConfig.objects.all())
        assert len(results) >= 2
        
        # Verify structure
        for config in results:
            assert config.tenant in ['tenant1', 'tenant2']
            assert config.operation in ['op1', 'op2']
            assert isinstance(config.piper_integration_config, PiperIntegrationConfig)
    
    @patch('github_orm.tools.github_client.GitHubClient')
    def test_nested_file_access(self, mock_client_class):
        """Test accessing nested files in models."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_client.get_branches.return_value = iter(['main'])
        mock_client.get_path.return_value = ['config/app.json']
        mock_client.get_file_content.return_value = '{"app": "test"}'
        
        class AppConfig(GitHubFile):
            class Meta:
                file_name = 'app.json'
        
        class AppModel(GitHubModel):
            class Meta:
                owner = 'testowner'
                repo = 'testrepo'
                branch = 'main'
                folder_path = 'config/'
            
            app_config: AppConfig
        
        manager = AppModel.objects
        manager._github_client = mock_client
        
        results = list(AppModel.objects.all())
        assert len(results) == 1
        
        result = results[0]
        content = result.app_config.read()
        assert content == '{"app": "test"}'
        mock_client.get_file_content.assert_called()





