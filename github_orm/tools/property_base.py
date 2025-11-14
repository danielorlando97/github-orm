import re
from typing import Optional, Dict, Any
from functools import lru_cache

class Field:
    """Base field class for path pattern matching."""
    def __init__(self, format: str):
        self.format = format
        self._pattern = self._compile_pattern(format)
    
    @lru_cache(maxsize=1000)    
    @staticmethod
    def create_field(field: str) -> bool:
        if field is None or re.search(r'\{(\w+)\}', field) is None:
            return field
        
        return Field(field)
    
    def _compile_pattern(self, format_str: str) -> re.Pattern:
        """Convert format string to regex pattern."""
        pattern = format_str.replace('/', r'\/')
        pattern = re.sub(r'\{(\w+)\}', r'(?P<\1>[^/]+)', pattern)
        return re.compile(f'^{pattern}.*$')
    
    @lru_cache(maxsize=1000)
    def match(self, path: str) -> Optional[Dict[str, str]]:
        """Match path against pattern and extract groups."""
        match = self._pattern.match(path)
        if match:
            return match.groupdict()
        return None

    def build_path(self, data: Dict[str, str]) -> str:
        return self.format.format(**data)
    
    def _get_data_value(self, github_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement this method")

    def __add__(self, other: 'Field') -> 'Field':
        if isinstance(other, str):
            return Field(self.format + other)
        return Field(self.format + other.format)
    
if __name__ == "__main__":
    text = "config/mops/{tenant}"
    field = Field.create_field(text)
    text = "config/mops/tenant1/images/image1.png"
    print(field.match(text))
    
    field = field + "/images"
    field = field + Field.create_field("/{image}")
    
    text = "config/mops/tenant1/images/image1.png"
    print(field.match(text))

    text = "config/mops2/tenant1/images/image1.png"
    print(field.match(text))