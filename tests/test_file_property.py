"""Minimalist tests for GitHubFileProperty."""
import pytest
from unittest.mock import patch, Mock
from github_orm.base.file_property import GitHubFileProperty
from github_orm.github_client.router import GitHubRouter


class TestGitHubFileProperty:
    """Tests for GitHubFileProperty."""
    
    def test_file_property_initialization(self):
        """Test file property initialization."""
        router = GitHubRouter(
            owner='testowner',
            repo='testrepo',
            branch='main',
            folder_path='config/',
            file_name='config.json'
        )
        file_prop = GitHubFileProperty(router)
        
        assert file_prop.meta.owner == 'testowner'
        assert file_prop.meta.repo == 'testrepo'
        assert file_prop.meta.branch == 'main'
        assert file_prop.meta.folder_path == 'config/'
        assert file_prop.meta.file_name == 'config.json'
    
    def test_file_property_with_class_meta(self):
        """Test file property with class Meta."""
        class TestFile(GitHubFileProperty):
            class Meta:
                file_name = 'test.json'
        
        router = GitHubRouter(
            owner='testowner',
            repo='testrepo',
            branch='main',
            folder_path='config/'
        )
        file_prop = TestFile(router)
        
        assert file_prop.meta.file_name == 'test.json'
        assert file_prop.meta.owner == 'testowner'
    
    def test_file_property_meta_merging(self):
        """Test that instance and class Meta are merged."""
        class TestFile(GitHubFileProperty):
            class Meta:
                file_name = 'default.json'
        
        router = GitHubRouter(
            owner='testowner',
            repo='testrepo',
            branch='main',
            folder_path='config/',
            file_name='override.json'
        )
        file_prop = TestFile(router)
        
        assert file_prop.meta.file_name == 'override.json'
        assert file_prop.meta.owner == 'testowner'
    
    def test_file_property_with_none_meta(self):
        """Test file property with None meta."""
        class TestFile(GitHubFileProperty):
            class Meta:
                file_name = 'test.json'
                owner = 'testowner'
                repo = 'testrepo'
                branch = 'main'
                folder_path = 'config/'
        
        file_prop = TestFile(None)
        assert file_prop.meta.file_name == 'test.json'
        assert file_prop.meta.owner == 'testowner'
    
    @patch('github_orm.base.file_property.GitHubClient')
    def test_read_file(self, mock_client):
        """Test reading file content."""
        mock_client.get_file_content = Mock(
            return_value='{"key": "value"}'
        )
        
        router = GitHubRouter(
            owner='testowner',
            repo='testrepo',
            branch='main',
            folder_path='config/',
            file_name='config.json'
        )
        file_prop = GitHubFileProperty(router)
        
        content = file_prop.read()
        
        assert content == '{"key": "value"}'
        mock_client.get_file_content.assert_called_once_with(
            'testowner',
            'testrepo',
            'main',
            'config/config.json'
        )
    
    @patch('github_orm.base.file_property.GitHubClient')
    def test_read_file_with_class_meta(self, mock_client):
        """Test reading file with class Meta."""
        mock_client.get_file_content = Mock(return_value='content')
        
        class TestFile(GitHubFileProperty):
            class Meta:
                file_name = 'test.json'
        
        router = GitHubRouter(
            owner='testowner',
            repo='testrepo',
            branch='main',
            folder_path='config/'
        )
        file_prop = TestFile(router)
        
        content = file_prop.read()
        
        assert content == 'content'
        mock_client.get_file_content.assert_called_once_with(
            'testowner',
            'testrepo',
            'main',
            'config/test.json'
        )

