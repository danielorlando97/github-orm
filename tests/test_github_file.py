"""Tests for GitHubFile."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from github_orm.tools.github_handler_base import GitHubFile, Meta
from github_orm.tools.github_client import GitHubClient


class TestGitHubFile:
    """Test GitHubFile functionality."""
    
    def test_github_file_initialization(self):
        """Test GitHubFile initialization."""
        meta = Meta(
            owner='testowner',
            repo='testrepo',
            branch='main',
            folder_path='config/',
            file_name='config.json'
        )
        file = GitHubFile(meta)
        assert file.meta.owner == 'testowner'
        assert file.meta.repo == 'testrepo'
        assert file.meta.branch == 'main'
    
    def test_github_file_with_class_meta(self):
        """Test GitHubFile with class Meta."""
        class TestFile(GitHubFile):
            class Meta:
                file_name = 'test.json'
        
        meta = Meta(owner='testowner', repo='testrepo', branch='main')
        file = TestFile(meta)
        assert file.meta.file_name == 'test.json'
        assert file.meta.owner == 'testowner'
    
    def test_github_file_meta_merging(self):
        """Test that instance and class Meta are merged."""
        class TestFile(GitHubFile):
            class Meta:
                file_name = 'default.json'
        
        meta = Meta(
            owner='testowner',
            repo='testrepo',
            branch='main',
            folder_path='config/',
            file_name='override.json'
        )
        file = TestFile(meta)
        assert file.meta.file_name == 'override.json'
        assert file.meta.owner == 'testowner'
    
    @patch.object(GitHubClient, 'get_file_content')
    def test_read_file(self, mock_get_content):
        """Test reading file content."""
        mock_get_content.return_value = '{"key": "value"}'
        
        meta = Meta(
            owner='testowner',
            repo='testrepo',
            branch='main',
            folder_path='config/',
            file_name='config.json'
        )
        file = GitHubFile(meta)
        
        content = file.read()
        assert content == '{"key": "value"}'
        mock_get_content.assert_called_once_with(
            'testowner',
            'testrepo',
            'main',
            'config/config.json'
        )
    
    @patch.object(GitHubClient, 'get_file_content')
    def test_read_file_with_field_patterns(self, mock_get_content):
        """Test reading file with Field patterns in meta."""
        from github_orm.tools.property_base import Field
        
        mock_get_content.return_value = '{"key": "value"}'
        
        meta = Meta(
            owner='testowner',
            repo='testrepo',
            branch=Field('data/test/{client}'),
            folder_path=Field('{service}/'),
            file_name='config.json'
        )
        file = GitHubFile(meta)
        
        # This would need resolved values in real usage
        # For now, test that it doesn't crash
        assert file.meta.branch is not None
        assert file.meta.folder_path is not None
    
    @patch.object(GitHubClient, 'get_file_content')
    def test_read_file_error_handling(self, mock_get_content):
        """Test error handling when reading file."""
        mock_get_content.side_effect = Exception("API Error")
        
        meta = Meta(
            owner='testowner',
            repo='testrepo',
            branch='main',
            folder_path='config/',
            file_name='config.json'
        )
        file = GitHubFile(meta)
        
        with pytest.raises(Exception):
            file.read()
    
    def test_github_file_meta_none(self):
        """Test GitHubFile with None meta."""
        file = GitHubFile(None)
        assert file.meta is not None
        assert file.meta.owner is None





