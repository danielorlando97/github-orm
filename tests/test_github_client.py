"""Tests for GitHubClient."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import base64
import requests
from github_orm.tools.github_client import GitHubClient


class TestGitHubClient:
    """Test GitHubClient functionality."""
    
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
    def test_client_initialization(self):
        """Test GitHubClient initialization."""
        client = GitHubClient()
        assert client.token == 'test_token'
    
    @patch('requests.get')
    def test_get_repos(self, mock_get):
        """Test getting repositories."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {'name': 'repo1'},
            {'name': 'repo2'},
            {'name': 'repo3'},
        ]
        mock_get.return_value = mock_response
        
        client = GitHubClient()
        client.token = 'test_token'
        
        repos = list(client.get_repos('testowner'))
        assert len(repos) == 3
        assert 'repo1' in repos
        assert 'repo2' in repos
        assert 'repo3' in repos
    
    @patch('requests.get')
    def test_get_repos_pagination(self, mock_get):
        """Test getting repositories with pagination."""
        mock_response_page1 = Mock()
        mock_response_page1.json.return_value = [
            {'name': f'repo{i}'} for i in range(30)
        ]
        
        mock_response_page2 = Mock()
        mock_response_page2.json.return_value = [
            {'name': 'repo30'},
        ]
        
        mock_get.side_effect = [mock_response_page1, mock_response_page2]
        
        client = GitHubClient()
        client.token = 'test_token'
        
        repos = list(client.get_repos('testowner'))
        assert len(repos) == 31
        assert mock_get.call_count == 2
    
    @patch('requests.get')
    def test_get_branches(self, mock_get):
        """Test getting branches."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {'name': 'main'},
            {'name': 'develop'},
            {'name': 'feature/test'},
        ]
        mock_get.return_value = mock_response
        
        client = GitHubClient()
        client.token = 'test_token'
        
        branches = list(client.get_branches('testowner', 'testrepo'))
        assert len(branches) == 3
        assert 'main' in branches
        assert 'develop' in branches
        assert 'feature/test' in branches
    
    @patch('requests.get')
    def test_get_path(self, mock_get):
        """Test getting paths from repository."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'tree': [
                {'path': 'file1.txt', 'type': 'blob'},
                {'path': 'file2.txt', 'type': 'blob'},
                {'path': 'dir1', 'type': 'tree'},
                {'path': 'dir2/file3.txt', 'type': 'blob'},
            ]
        }
        mock_get.return_value = mock_response
        
        client = GitHubClient()
        client.token = 'test_token'
        
        paths = client.get_path('testowner', 'testrepo', 'main')
        assert len(paths) == 3  # Only blobs
        assert 'file1.txt' in paths
        assert 'file2.txt' in paths
        assert 'dir2/file3.txt' in paths
        assert 'dir1' not in paths  # Not a blob
    
    @patch('requests.get')
    def test_get_file_content(self, mock_get):
        """Test getting file content."""
        content = '{"key": "value"}'
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'content': encoded_content,
            'encoding': 'base64',
        }
        mock_get.return_value = mock_response
        
        client = GitHubClient()
        client.token = 'test_token'
        
        file_content = client.get_file_content(
            'testowner', 'testrepo', 'main', 'config.json'
        )
        assert file_content == content
    
    @patch('requests.get')
    def test_get_file_content_headers(self, mock_get):
        """Test that Authorization header is set correctly."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'content': base64.b64encode(b'test').decode('utf-8'),
            'encoding': 'base64',
        }
        mock_get.return_value = mock_response
        
        client = GitHubClient()
        client.token = 'test_token'
        
        client.get_file_content('testowner', 'testrepo', 'main', 'file.txt')
        
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert 'Authorization' in call_args[1]['headers']
        assert call_args[1]['headers']['Authorization'] == 'Bearer test_token'
    
    @patch('requests.get')
    def test_get_branches_pagination(self, mock_get):
        """Test getting branches with pagination."""
        mock_response_page1 = Mock()
        mock_response_page1.json.return_value = [
            {'name': f'branch{i}'} for i in range(30)
        ]
        
        mock_response_page2 = Mock()
        mock_response_page2.json.return_value = [
            {'name': 'branch30'},
        ]
        
        mock_get.side_effect = [mock_response_page1, mock_response_page2]
        
        client = GitHubClient()
        client.token = 'test_token'
        
        branches = list(client.get_branches('testowner', 'testrepo'))
        assert len(branches) == 31
        assert mock_get.call_count == 2





