"""Tests for Field pattern matching."""
import pytest
from github_orm.tools.property_base import Field


class TestField:
    """Test Field pattern matching functionality."""
    
    def test_create_field_with_variables(self):
        """Test Field creation with variable pattern."""
        field = Field.create_field('config/mops/{tenant}')
        assert isinstance(field, Field)
        assert field.format == 'config/mops/{tenant}'
    
    def test_create_field_without_variables(self):
        """Test Field creation without variables returns string."""
        field = Field.create_field('config/mops/tenant1')
        assert field == 'config/mops/tenant1'
        assert not isinstance(field, Field)
    
    def test_create_field_none(self):
        """Test Field creation with None."""
        field = Field.create_field(None)
        assert field is None
    
    def test_match_simple_pattern(self):
        """Test matching simple pattern."""
        field = Field('config/mops/{tenant}')
        result = field.match('config/mops/tenant1')
        assert result == {'tenant': 'tenant1'}
    
    def test_match_pattern_with_path(self):
        """Test matching pattern with additional path."""
        field = Field('config/mops/{tenant}')
        result = field.match('config/mops/tenant1/images/image1.png')
        assert result == {'tenant': 'tenant1'}
    
    def test_match_pattern_no_match(self):
        """Test pattern that doesn't match."""
        field = Field('config/mops/{tenant}')
        result = field.match('config/other/tenant1')
        assert result is None
    
    def test_match_multiple_variables(self):
        """Test matching pattern with multiple variables."""
        field = Field('data/test/{client}/{service}')
        result = field.match('data/test/client_1/service_1')
        assert result == {'client': 'client_1', 'service': 'service_1'}
    
    def test_match_with_slashes(self):
        """Test matching pattern with slashes."""
        field = Field('configs/mops/{operation}/piper_integration/')
        result = field.match('configs/mops/op1/piper_integration/piper_config.json')
        assert result == {'operation': 'op1'}
    
    def test_build_path(self):
        """Test building path from data."""
        field = Field('config/mops/{tenant}')
        path = field.build_path({'tenant': 'tenant1'})
        assert path == 'config/mops/tenant1'
    
    def test_build_path_multiple_variables(self):
        """Test building path with multiple variables."""
        field = Field('data/test/{client}/{service}')
        path = field.build_path({'client': 'client_1', 'service': 'service_1'})
        assert path == 'data/test/client_1/service_1'
    
    def test_field_addition_string(self):
        """Test Field addition with string."""
        field1 = Field('config/mops/')
        field2 = field1 + '{tenant}'
        assert isinstance(field2, Field)
        assert field2.format == 'config/mops/{tenant}'
    
    def test_field_addition_field(self):
        """Test Field addition with another Field."""
        field1 = Field('config/mops/')
        field2 = Field('{tenant}')
        field3 = field1 + field2
        assert isinstance(field3, Field)
        assert field3.format == 'config/mops/{tenant}'
    
    def test_field_repr(self):
        """Test Field string representation."""
        field = Field('config/mops/{tenant}')
        repr_str = repr(field)
        assert 'Field' in repr_str
        assert 'config/mops/{tenant}' in repr_str
    
    def test_match_complex_pattern(self):
        """Test matching complex nested pattern."""
        field = Field('configs/mops/{operation}/piper_integration/{file}')
        result = field.match('configs/mops/op1/piper_integration/config.json')
        assert result == {'operation': 'op1', 'file': 'config.json'}
    
    def test_match_edge_cases(self):
        """Test edge cases in pattern matching."""
        field = Field('{name}')
        result = field.match('test')
        assert result == {'name': 'test'}
        
        result = field.match('test/path')
        assert result == {'name': 'test'}





