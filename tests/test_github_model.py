"""Tests for GitHubModel."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from github_orm.tools.github_handler_base import (
    GitHubModel, GitHubFile, Meta, GitHubOrmError
)


class TestGitHubModel:
    """Test GitHubModel functionality."""
    
    def test_model_initialization(self):
        """Test GitHubModel initialization."""
        class TestModel(GitHubModel):
            class Meta:
                owner = 'testowner'
                repo = 'testrepo'
                branch = 'main'
            
            name: str
        
        model = TestModel(name='test', meta={'branch': 'main'})
        assert model.name == 'test'
    
    def test_model_with_github_file(self):
        """Test GitHubModel with GitHubFile properties."""
        class TestFile(GitHubFile):
            class Meta:
                file_name = 'config.json'
        
        class TestModel(GitHubModel):
            class Meta:
                owner = 'testowner'
                repo = 'testrepo'
                branch = 'main'
                folder_path = 'config/'
            
            config: TestFile
        
        model = TestModel(meta={'branch': 'main', 'folder_path': 'config/'})
        assert isinstance(model.config, TestFile)
        assert model.config.meta.file_name == 'config.json'
    
    def test_model_missing_property(self):
        """Test error when required property is missing."""
        class TestModel(GitHubModel):
            class Meta:
                owner = 'testowner'
                repo = 'testrepo'
            
            name: str
        
        with pytest.raises(GitHubOrmError):
            TestModel()  # Missing 'name' property
    
    def test_model_objects_property(self):
        """Test that objects property returns GitHubHandlerManager."""
        class TestModel(GitHubModel):
            class Meta:
                owner = 'testowner'
                repo = 'testrepo'
        
        manager = TestModel.objects
        assert manager is not None
        assert manager.model == TestModel
        assert manager.meta is not None
    
    def test_model_objects_without_meta(self):
        """Test objects property without Meta class."""
        class TestModel(GitHubModel):
            pass
        
        manager = TestModel.objects
        assert manager.meta is None
    
    def test_model_property_annotation(self):
        """Test that properties are correctly annotated."""
        class TestModel(GitHubModel):
            class Meta:
                owner = 'testowner'
                repo = 'testrepo'
            
            name: str
            value: int
        
        model = TestModel(name='test', value=42)
        assert model.name == 'test'
        assert model.value == 42

