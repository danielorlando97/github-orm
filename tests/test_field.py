"""Minimalist tests for Field pattern matching."""
import pytest
from github_orm.base.string_property import Field


class TestField:
    """Tests for Field pattern matching."""
    
    def test_create_field_with_pattern(self):
        """Test Field creation with variable pattern."""
        field = Field.create_field('data/test/{client}')
        assert isinstance(field, Field)
        assert field.format == 'data/test/{client}'
    
    def test_create_field_without_pattern(self):
        """Test Field creation without pattern returns string."""
        field = Field.create_field('data/test/client_1')
        assert field == 'data/test/client_1'
        assert not isinstance(field, Field)
    
    def test_create_field_none(self):
        """Test Field creation with None."""
        field = Field.create_field(None)
        assert field is None
    
    def test_match_simple_pattern(self):
        """Test matching simple pattern."""
        field = Field('data/test/{client}')
        result = field.match('data/test/client_1')
        assert result == {'client': 'client_1'}
    
    def test_match_pattern_with_path(self):
        """Test matching pattern with additional path."""
        field = Field('data/test/{client}')
        result = field.match('data/test/client_1/service_1/file.json')
        assert result == {'client': 'client_1'}
    
    def test_match_no_match(self):
        """Test pattern that doesn't match."""
        field = Field('data/test/{client}')
        result = field.match('data/other/client_1')
        assert result is None
    
    def test_match_multiple_variables(self):
        """Test matching pattern with multiple variables."""
        field = Field('{service}/config/{file}')
        result = field.match('service_1/config/db.json')
        assert result == {'service': 'service_1', 'file': 'db.json'}
    
    def test_build_path(self):
        """Test building path from data."""
        field = Field('data/test/{client}')
        path = field.build_path({'client': 'client_1'})
        assert path == 'data/test/client_1'
    
    def test_field_addition_string(self):
        """Test Field addition with string."""
        field1 = Field('service_1/')
        field2 = field1 + 'db_config.json'
        assert isinstance(field2, Field)
        assert field2.format == 'service_1/db_config.json'
    
    def test_field_addition_field(self):
        """Test Field addition with another Field."""
        field1 = Field('service_1/')
        field2 = Field('db_config.json')
        field3 = field1 + field2
        assert isinstance(field3, Field)
        assert field3.format == 'service_1/db_config.json'

