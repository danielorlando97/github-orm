"""Minimalist tests for GitHubQueryBuilder."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from github_orm.github_client.router import GitHubRouter
from github_orm.github_client.query_builder import GitHubQueryBuilder
from github_orm.base.string_property import Field


class MockModel:
    """Mock model for testing."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestGitHubQueryBuilder:
    """Tests for GitHubQueryBuilder."""
    
    def test_query_builder_initialization(self):
        """Test query builder initialization."""
        router = GitHubRouter(owner='testowner', repo='testrepo')
        builder = GitHubQueryBuilder(MockModel, router)
        
        assert builder.model == MockModel
        assert builder.meta == router
    
    def test_build_iterator_empty_when_no_meta(self):
        """Test iterator is empty when no meta."""
        builder = GitHubQueryBuilder(MockModel, None)
        results = list(builder._build_iterator())
        assert len(results) == 0
    
    def test_build_iterator_empty_when_no_owner_repo(self):
        """Test iterator is empty when no owner or repo."""
        router = GitHubRouter(branch='main')
        builder = GitHubQueryBuilder(MockModel, router)
        results = list(builder._build_iterator())
        assert len(results) == 0
    
    @patch('github_orm.github_client.query_builder.GitHubClient')
    def test_build_iterator_string_repo_branch(self, mock_client_module):
        """Test iterator with string repo and branch."""
        mock_client_module.get_branches = Mock(return_value=iter(['main']))
        mock_client_module.get_paths = Mock(return_value=[])
        
        router = GitHubRouter(
            owner='testowner',
            repo='testrepo',
            branch='main'
        )
        builder = GitHubQueryBuilder(MockModel, router)
        
        results = list(builder._build_iterator())
        assert len(results) == 1
        assert results[0]['repo'] == 'testrepo'
        assert results[0]['branch'] == 'main'
    
    @patch('github_orm.github_client.query_builder.GitHubClient')
    def test_build_iterator_field_branch(self, mock_client_module):
        """Test iterator with Field pattern for branch."""
        mock_client_module.get_branches = Mock(return_value=iter([
            'data/test/client_1',
            'data/test/client_2',
            'main'
        ]))
        mock_client_module.get_paths = Mock(return_value=[])
        
        router = GitHubRouter(
            owner='testowner',
            repo='testrepo',
            branch='data/test/{client}'
        )
        builder = GitHubQueryBuilder(MockModel, router)
        
        results = list(builder._build_iterator())
        assert len(results) == 2
        assert all('client' in r for r in results)
        clients = {r['client'] for r in results}
        assert 'client_1' in clients
        assert 'client_2' in clients
    
    @patch('github_orm.github_client.query_builder.GitHubClient')
    def test_build_iterator_folder_path(self, mock_client_module):
        """Test iterator with folder_path."""
        mock_client_module.get_branches = Mock(return_value=iter(['main']))
        mock_client_module.get_paths = Mock(return_value=[
            'service_1/db_config.json',
            'service_2/db_config.json',
            'other/file.txt'
        ])
        
        router = GitHubRouter(
            owner='testowner',
            repo='testrepo',
            branch='main',
            folder_path='service_1/'
        )
        builder = GitHubQueryBuilder(MockModel, router)
        
        results = list(builder._build_iterator())
        assert len(results) == 1
        assert 'service_1/db_config.json' in results[0]['folder']
    
    @patch('github_orm.github_client.query_builder.GitHubClient')
    def test_build_iterator_field_folder_path(self, mock_client_module):
        """Test iterator with Field pattern for folder_path."""
        mock_client_module.get_branches = Mock(return_value=iter(['main']))
        mock_client_module.get_paths = Mock(return_value=[
            'service_1/db_config.json',
            'service_2/db_config.json',
            'other/file.txt'
        ])
        
        router = GitHubRouter(
            owner='testowner',
            repo='testrepo',
            branch='main',
            folder_path='{service}_{version}/'
        )
        builder = GitHubQueryBuilder(MockModel, router)
        
        results = list(builder._build_iterator())
        assert len(results) == 2
        assert all('service' in r for r in results)
        services = {r['service'] for r in results}
        versions = {r['version'] for r in results}
        assert 'service' in services
        assert versions == {'1', '2'}
    
    @patch('github_orm.github_client.query_builder.GitHubClient')
    def test_all_method(self, mock_client_module):
        """Test all() method returns model instances."""
        mock_client_module.get_branches = Mock(return_value=iter(['main']))
        mock_client_module.get_paths = Mock(return_value=[])
        
        router = GitHubRouter(
            owner='testowner',
            repo='testrepo',
            branch='main'
        )
        builder = GitHubQueryBuilder(MockModel, router)
        
        results = list(builder.all())
        assert len(results) == 1
        assert isinstance(results[0], MockModel)
        assert results[0].repo == 'testrepo'
        assert results[0].branch == 'main'

