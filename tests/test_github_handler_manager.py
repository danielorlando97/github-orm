"""Tests for GitHubHandlerManager."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from github_orm.tools.github_handler_base import (
    GitHubHandlerManager, GitHubModel, Meta
)
from github_orm.tools.property_base import Field


class TestGitHubHandlerManager:
    """Test GitHubHandlerManager functionality."""
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        class TestModel(GitHubModel):
            class Meta:
                owner = 'testowner'
                repo = 'testrepo'
        
        manager = TestModel.objects
        assert manager.model == TestModel
        assert manager.meta is not None
        assert manager.meta.owner == 'testowner'
        assert manager.meta.repo == 'testrepo'
    
    def test_all_empty_when_no_meta(self):
        """Test all() returns empty when no meta."""
        class TestModel(GitHubModel):
            pass
        
        manager = TestModel.objects
        results = list(manager.all())
        assert len(results) == 0
    
    def test_all_empty_when_no_owner_repo(self):
        """Test all() returns empty when no owner or repo."""
        class TestModel(GitHubModel):
            class Meta:
                branch = 'main'
        
        manager = TestModel.objects
        results = list(manager.all())
        assert len(results) == 0
    
    @patch.object(GitHubHandlerManager, '_github_client')
    def test_all_with_string_repo_branch(self, mock_client):
        """Test all() with string repo and branch."""
        mock_client.get_branches = Mock(return_value=iter(['main', 'develop']))
        mock_client.get_path = Mock(return_value=[])
        
        class TestModel(GitHubModel):
            class Meta:
                owner = 'testowner'
                repo = 'testrepo'
                branch = 'main'
        
        manager = TestModel.objects
        manager._github_client = mock_client
        
        results = list(manager.all())
        assert len(results) == 1
        assert results[0].meta['branch'] == 'main'
    
    @patch.object(GitHubHandlerManager, '_github_client')
    def test_all_with_field_branch_pattern(self, mock_client):
        """Test all() with Field pattern for branch."""
        mock_client.get_branches = Mock(return_value=iter([
            'data/test/client_1',
            'data/test/client_2',
            'main',
            'develop'
        ]))
        mock_client.get_path = Mock(return_value=[])
        
        class TestModel(GitHubModel):
            class Meta:
                owner = 'testowner'
                repo = 'testrepo'
                branch = Field('data/test/{client}')
            
            client: str
        
        manager = TestModel.objects
        manager._github_client = mock_client
        
        results = list(manager.all())
        assert len(results) == 2
        assert results[0].client == 'client_1'
        assert results[1].client == 'client_2'
    
    @patch.object(GitHubHandlerManager, '_github_client')
    def test_all_with_field_repo_pattern(self, mock_client):
        """Test all() with Field pattern for repo."""
        mock_client.get_repos = Mock(return_value=iter([
            'test-repo',
            'github-orm',
            'other-repo'
        ]))
        mock_client.get_branches = Mock(return_value=iter(['main']))
        mock_client.get_path = Mock(return_value=[])
        
        class TestModel(GitHubModel):
            class Meta:
                owner = 'testowner'
                repo = Field('{name}-repo')
                branch = 'main'
            
            name: str
        
        manager = TestModel.objects
        manager._github_client = mock_client
        
        results = list(manager.all())
        assert len(results) == 1
        assert results[0].name == 'test'
        assert results[0].meta['repo'] == 'test-repo'
    
    @patch.object(GitHubHandlerManager, '_github_client')
    def test_all_with_folder_path_string(self, mock_client):
        """Test all() with string folder_path."""
        mock_client.get_branches = Mock(return_value=iter(['main']))
        mock_client.get_path = Mock(return_value=[
            'service_1/db_config.json',
            'service_2/db_config.json',
            'other/file.txt'
        ])
        
        class TestModel(GitHubModel):
            class Meta:
                owner = 'testowner'
                repo = 'testrepo'
                branch = 'main'
                folder_path = 'service_1/'
        
        manager = TestModel.objects
        manager._github_client = mock_client
        
        results = list(manager.all())
        assert len(results) == 1
        assert results[0].meta['folder_path'] == 'service_1/db_config.json'
    
    @patch.object(GitHubHandlerManager, '_github_client')
    def test_all_with_folder_path_field(self, mock_client):
        """Test all() with Field pattern for folder_path."""
        mock_client.get_branches = Mock(return_value=iter(['main']))
        mock_client.get_path = Mock(return_value=[
            'service_1/db_config.json',
            'service_2/db_config.json',
            'other/file.txt'
        ])
        
        class TestModel(GitHubModel):
            class Meta:
                owner = 'testowner'
                repo = 'testrepo'
                branch = 'main'
                folder_path = Field('{service}/')
            
            service: str
        
        manager = TestModel.objects
        manager._github_client = mock_client
        
        results = list(manager.all())
        assert len(results) == 2
        assert results[0].service == 'service_1'
        assert results[1].service == 'service_2'
    
    @patch.object(GitHubHandlerManager, '_github_client')
    def test_all_with_file_name(self, mock_client):
        """Test all() with file_name specified."""
        mock_client.get_branches = Mock(return_value=iter(['main']))
        mock_client.get_path = Mock(return_value=[
            'service_1/db_config.json',
            'service_1/other.json',
            'service_2/db_config.json'
        ])
        
        class TestModel(GitHubModel):
            class Meta:
                owner = 'testowner'
                repo = 'testrepo'
                branch = 'main'
                folder_path = Field('{service}/')
                file_name = 'db_config.json'
            
            service: str
        
        manager = TestModel.objects
        manager._github_client = mock_client
        
        results = list(manager.all())
        assert len(results) == 2
        assert all(r.service in ['service_1', 'service_2'] for r in results)
    
    @patch.object(GitHubHandlerManager, '_github_client')
    def test_all_complex_pattern(self, mock_client):
        """Test all() with complex nested patterns."""
        mock_client.get_branches = Mock(return_value=iter([
            'config/mops/tenant1',
            'config/mops/tenant2'
        ]))
        mock_client.get_path = Mock(return_value=[
            'configs/mops/op1/piper_integration/piper_config.json',
            'configs/mops/op2/piper_integration/piper_config.json',
        ])
        
        class TestModel(GitHubModel):
            class Meta:
                owner = 'testowner'
                repo = 'testrepo'
                branch = Field('config/mops/{tenant}')
                folder_path = Field('configs/mops/{operation}/piper_integration/')
                file_name = 'piper_config.json'
            
            tenant: str
            operation: str
        
        manager = TestModel.objects
        manager._github_client = mock_client
        
        results = list(manager.all())
        assert len(results) == 4  # 2 tenants * 2 operations
        tenants = {r.tenant for r in results}
        operations = {r.operation for r in results}
        assert tenants == {'tenant1', 'tenant2'}
        assert operations == {'op1', 'op2'}





