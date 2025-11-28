"""Minimalist tests for GitHubRouter."""
import pytest
from github_orm.github_client.router import GitHubRouter
from github_orm.base.string_property import Field


class TestGitHubRouter:
    """Tests for GitHubRouter configuration."""
    
    def test_router_creation(self):
        """Test router creation with string values."""
        router = GitHubRouter(
            owner='testowner',
            repo='testrepo',
            branch='main',
            folder_path='config/',
            file_name='config.json'
        )
        assert router.owner == 'testowner'
        assert router.repo == 'testrepo'
        assert router.branch == 'main'
        assert router.folder_path == 'config/'
        assert router.file_name == 'config.json'
    
    def test_router_with_field_pattern(self):
        """Test router with Field pattern."""
        router = GitHubRouter(
            owner='testowner',
            repo='testrepo',
            branch='data/test/{client}'
        )
        assert router.owner == 'testowner'
        assert isinstance(router.branch, Field)
        assert router.branch.format == 'data/test/{client}'
    
    def test_router_addition(self):
        """Test router addition operator."""
        router1 = GitHubRouter(owner='owner1', repo='repo1')
        router2 = GitHubRouter(branch='main', folder_path='config/')
        
        result = router1 + router2
        assert result.owner == 'owner1'
        assert result.repo == 'repo1'
        assert result.branch == 'main'
        assert result.folder_path == 'config/'
    
    def test_router_addition_priority(self):
        """Test that first router takes priority."""
        router1 = GitHubRouter(owner='owner1', branch='main')
        router2 = GitHubRouter(owner='owner2', branch='develop')
        
        result = router1 + router2
        assert result.owner == 'owner1'
        assert result.branch == 'main'
    
    def test_router_addition_with_none(self):
        """Test router addition with None."""
        router1 = GitHubRouter(owner='owner1', repo='repo1')
        result = router1 + None
        assert result.owner == 'owner1'
        assert result.repo == 'repo1'
    
    def test_router_from_class(self):
        """Test router creation from class Meta."""
        class TestMeta:
            owner = 'testowner'
            repo = 'testrepo'
            branch = 'main'
            folder_path = 'config/'
            file_name = 'config.json'
        
        router = GitHubRouter.from_class(TestMeta)
        assert router.owner == 'testowner'
        assert router.repo == 'testrepo'
        assert router.branch == 'main'
        assert router.folder_path == 'config/'
        assert router.file_name == 'config.json'
    
    def test_router_from_class_none(self):
        """Test from_class with None."""
        router = GitHubRouter.from_class(None)
        assert router.owner is None
        assert router.repo is None

