"""Tests for Meta class."""
import pytest
from github_orm.tools.github_handler_base import Meta
from github_orm.tools.property_base import Field


class TestMeta:
    """Test Meta metadata class."""
    
    def test_meta_creation_with_strings(self):
        """Test Meta creation with string values."""
        meta = Meta(
            owner='testowner',
            repo='testrepo',
            branch='main',
            folder_path='config/',
            file_name='config.json'
        )
        assert meta.owner == 'testowner'
        assert meta.repo == 'testrepo'
        assert meta.branch == 'main'
        assert meta.folder_path == 'config/'
        assert meta.file_name == 'config.json'
    
    def test_meta_creation_with_fields(self):
        """Test Meta creation with Field patterns."""
        meta = Meta(
            owner='testowner',
            repo='testrepo',
            branch=Field('data/test/{client}'),
            folder_path=Field('{service}/'),
            file_name='config.json'
        )
        assert isinstance(meta.branch, Field)
        assert isinstance(meta.folder_path, Field)
        assert meta.branch.format == 'data/test/{client}'
        assert meta.folder_path.format == '{service}/'
    
    def test_meta_creation_with_none(self):
        """Test Meta creation with None values."""
        meta = Meta()
        assert meta.owner is None
        assert meta.repo is None
        assert meta.branch is None
        assert meta.folder_path is None
        assert meta.file_name is None
    
    def test_meta_addition(self):
        """Test Meta addition operator."""
        meta1 = Meta(owner='owner1', repo='repo1')
        meta2 = Meta(branch='main', folder_path='config/')
        
        result = meta1 + meta2
        assert result.owner == 'owner1'
        assert result.repo == 'repo1'
        assert result.branch == 'main'
        assert result.folder_path == 'config/'
    
    def test_meta_addition_with_none(self):
        """Test Meta addition with None."""
        meta1 = Meta(owner='owner1', repo='repo1')
        result = meta1 + None
        assert result.owner == 'owner1'
        assert result.repo == 'repo1'
    
    def test_meta_addition_priority(self):
        """Test that first Meta takes priority in addition."""
        meta1 = Meta(owner='owner1', branch='main')
        meta2 = Meta(owner='owner2', branch='develop')
        
        result = meta1 + meta2
        assert result.owner == 'owner1'  # First takes priority
        assert result.branch == 'main'  # First takes priority
    
    def test_meta_from_class(self):
        """Test Meta creation from class Meta."""
        class TestMeta:
            owner = 'testowner'
            repo = 'testrepo'
            branch = 'main'
            folder_path = 'config/'
            file_name = 'config.json'
        
        meta = Meta.from_class(TestMeta)
        assert meta.owner == 'testowner'
        assert meta.repo == 'testrepo'
        assert meta.branch == 'main'
        assert meta.folder_path == 'config/'
        assert meta.file_name == 'config.json'
    
    def test_meta_from_class_none(self):
        """Test Meta.from_class with None."""
        meta = Meta.from_class(None)
        assert meta.owner is None
        assert meta.repo is None
    
    def test_meta_from_class_partial(self):
        """Test Meta.from_class with partial attributes."""
        class PartialMeta:
            owner = 'testowner'
            repo = 'testrepo'
        
        meta = Meta.from_class(PartialMeta)
        assert meta.owner == 'testowner'
        assert meta.repo == 'testrepo'
        assert meta.branch is None
        assert meta.folder_path is None
        assert meta.file_name is None
    
    def test_meta_field_auto_creation(self):
        """Test that Field patterns are auto-created."""
        meta = Meta(branch='data/test/{client}')
        assert isinstance(meta.branch, Field)
        assert meta.branch.format == 'data/test/{client}'
    
    def test_meta_string_not_converted_to_field(self):
        """Test that plain strings are not converted to Field."""
        meta = Meta(branch='main')
        assert meta.branch == 'main'
        assert not isinstance(meta.branch, Field)





