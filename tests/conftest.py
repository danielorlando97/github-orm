"""Pytest configuration and fixtures."""
import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any


@pytest.fixture
def mock_github_client():
    """Create a mock GitHubClient for testing."""
    client = Mock()
    
    # Mock get_repos
    client.get_repos = Mock(return_value=iter([
        'repo1', 'repo2', 'test-repo', 'github-orm'
    ]))
    
    # Mock get_branches
    client.get_branches = Mock(return_value=iter([
        'main', 'develop', 'data/test/client_1', 
        'data/test/client_2', 'config/mops/tenant1'
    ]))
    
    # Mock get_path
    client.get_path = Mock(return_value=[
        'service_1/db_config.json',
        'service_1/tropicalization.yaml',
        'service_2/db_config.json',
        'service_2/tropicalization.yaml',
        'configs/mops/op1/piper_integration/piper_config.json',
        'configs/mops/op2/piper_integration/piper_config.json',
    ])
    
    # Mock get_file_content
    client.get_file_content = Mock(return_value='{"key": "value"}')
    
    return client


@pytest.fixture
def sample_repos_response():
    """Sample GitHub API repos response."""
    return [
        {'name': 'repo1'},
        {'name': 'repo2'},
        {'name': 'test-repo'},
        {'name': 'github-orm'},
    ]


@pytest.fixture
def sample_branches_response():
    """Sample GitHub API branches response."""
    return [
        {'name': 'main'},
        {'name': 'develop'},
        {'name': 'data/test/client_1'},
        {'name': 'data/test/client_2'},
        {'name': 'config/mops/tenant1'},
    ]


@pytest.fixture
def sample_tree_response():
    """Sample GitHub API tree response."""
    return {
        'tree': [
            {'path': 'service_1/db_config.json', 'type': 'blob'},
            {'path': 'service_1/tropicalization.yaml', 'type': 'blob'},
            {'path': 'service_2/db_config.json', 'type': 'blob'},
            {'path': 'service_2/tropicalization.yaml', 'type': 'blob'},
            {'path': 'configs/mops/op1/piper_integration/piper_config.json', 
             'type': 'blob'},
            {'path': 'configs/mops/op2/piper_integration/piper_config.json', 
             'type': 'blob'},
        ]
    }


@pytest.fixture
def sample_file_content_response():
    """Sample GitHub API file content response."""
    import base64
    content = '{"key": "value"}'
    encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    return {
        'content': encoded,
        'encoding': 'base64',
        'sha': 'abc123',
    }





