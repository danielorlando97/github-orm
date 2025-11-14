# Propuesta de Implementación - GitHub ORM v3

## Estructura de archivos

```
github_orm/
├── __init__.py
├── branch.py           # Branch con Name descriptor y Manager
├── folder.py          # Folder con Path descriptor
├── file/
│   └── json.py        # JsonFile
├── fields.py          # Path, Name descriptors
└── tools/
    ├── __init__.py
    ├── base.py
    ├── context.py
    ├── exceptions.py
    └── manager.py     # Manager para .objects.all()
```

## Implementación

### `github_orm/tools/base.py`

```python
import os
from typing import Optional
from github_orm.tools.context import ExecutionContext
from github_orm.tools.exceptions import GitHubORMConfigError


class GitHubORMBase:
    """Base class for all ORM components"""
    
    def __init__(self, context: Optional[ExecutionContext] = None):
        if context:
            self._context = context
        else:
            self._context = ExecutionContext()
            self._load_meta()
            self._load_token()
    
    def _load_meta(self) -> None:
        """Loads configuration from Meta class"""
        meta = getattr(self.__class__, "Meta", None)
        
        if meta:
            self._context.owner = getattr(meta, "owner", None)
            self._context.repo = getattr(meta, "repo", None)
            self._context.branch = getattr(meta, "branch", None)
        
        if not self._context.owner or not self._context.repo:
            raise GitHubORMConfigError(
                f"{self.__class__.__name__} must define a Meta class "
                "with 'owner' and 'repo'"
            )
    
    def _load_token(self) -> None:
        """Loads token from environment variable"""
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise GitHubORMConfigError(
                "GITHUB_TOKEN environment variable not set"
            )
        self._context.token = token
```

### `github_orm/tools/context.py`

```python
from typing import Optional
from dataclasses import dataclass


@dataclass
class ExecutionContext:
    """Execution context"""
    owner: Optional[str] = None
    repo: Optional[str] = None
    token: Optional[str] = None
    branch: Optional[str] = None
    folder_path: str = ""
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    resolved_variables: dict = None
    
    def __post_init__(self):
        if self.resolved_variables is None:
            self.resolved_variables = {}
    
    def copy(self) -> "ExecutionContext":
        """Creates a copy of the context"""
        return ExecutionContext(
            owner=self.owner,
            repo=self.repo,
            token=self.token,
            branch=self.branch,
            folder_path=self.folder_path,
            file_name=self.file_name,
            file_type=self.file_type,
            resolved_variables=self.resolved_variables.copy() if self.resolved_variables else {},
        )
    
    def validate_for_read(self) -> None:
        """Validates context has all info needed for reading"""
        required = ["owner", "repo", "token", "file_name"]
        missing = [
            attr for attr in required 
            if not getattr(self, attr)
        ]
        
        if missing:
            from github_orm.tools.exceptions import GitHubORMConfigError
            raise GitHubORMConfigError(
                f"Missing required context: {', '.join(missing)}"
            )
    
    def get_file_path(self) -> str:
        """Gets the complete file path"""
        if self.folder_path:
            return f"{self.folder_path}/{self.file_name}"
        return self.file_name or ""
```

### `github_orm/tools/exceptions.py`

```python
class GitHubORMError(Exception):
    """Base exception"""
    pass


class GitHubORMConfigError(GitHubORMError):
    """Configuration error"""
    pass


class GitHubORMConnectionError(GitHubORMError):
    """Connection error"""
    pass


class GitHubORMValidationError(GitHubORMError):
    """Validation error"""
    pass
```

### `github_orm/fields.py` - Descriptores Path y Name

```python
import re
from typing import Optional


class Path:
    """Descriptor for dynamic folder paths"""
    
    def __init__(self, format: str):
        self.format = format
        self.variable_name = None
        self.pattern = None
        self._parse_format()
    
    def _parse_format(self) -> None:
        """Extracts variable name and creates pattern"""
        matches = re.findall(r'\{(\w+)\}', self.format)
        if matches:
            self.variable_name = matches[0]
            # Create regex pattern from format
            pattern = re.escape(self.format)
            pattern = pattern.replace(r'\{' + self.variable_name + r'\}', r'([^/]+)')
            self.pattern = re.compile(f'^{pattern}$')
    
    def __set_name__(self, owner, name):
        self.variable_name = name if not self.variable_name else self.variable_name
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, f'_{self.variable_name}', None)
    
    def __set__(self, obj, value):
        setattr(obj, f'_{self.variable_name}', value)
    
    def resolve(self, **kwargs) -> str:
        """Resolves path with given variables"""
        return self.format.format(**kwargs)
    
    def match_and_extract(self, path: str) -> Optional[dict]:
        """Matches path against pattern and extracts variable"""
        if not self.pattern:
            return None
        match = self.pattern.match(path)
        if match:
            return {self.variable_name: match.group(1)}
        return None


class Name:
    """Descriptor for dynamic branch names"""
    
    def __init__(self, format: str):
        self.format = format
        self.variable_name = None
        self.pattern = None
        self._parse_format()
    
    def _parse_format(self) -> None:
        """Extracts variable name and creates pattern"""
        matches = re.findall(r'\{(\w+)\}', self.format)
        if matches:
            self.variable_name = matches[0]
            pattern = re.escape(self.format)
            pattern = pattern.replace(r'\{' + self.variable_name + r'\}', r'(.+)')
            self.pattern = re.compile(f'^{pattern}$')
    
    def __set_name__(self, owner, name):
        self.variable_name = name if not self.variable_name else self.variable_name
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, f'_{self.variable_name}', None)
    
    def __set__(self, obj, value):
        setattr(obj, f'_{self.variable_name}', value)
    
    def resolve(self, **kwargs) -> str:
        """Resolves name with given variables"""
        return self.format.format(**kwargs)
    
    def match_and_extract(self, name: str) -> Optional[dict]:
        """Matches name against pattern and extracts variable"""
        if not self.pattern:
            return None
        match = self.pattern.match(name)
        if match:
            return {self.variable_name: match.group(1)}
        return None
```

### `github_orm/tools/manager.py` - Manager para .objects.all()

```python
import requests
from typing import Iterator, Optional
from github_orm.tools.context import ExecutionContext
from github_orm.tools.exceptions import GitHubORMConnectionError, GitHubORMConfigError


class Manager:
    """Manager for querying instances"""
    
    def __init__(self, model_class):
        self.model_class = model_class
    
    def all(self) -> Iterator:
        """Returns iterator over all instances matching the pattern"""
        meta = getattr(self.model_class, "Meta", None)
        if not meta:
            return iter([])
        
        owner = getattr(meta, "owner", None)
        repo = getattr(meta, "repo", None)
        branch = getattr(meta, "branch", "main")
        token = self._get_token()
        
        if not owner or not repo:
            return iter([])
        
        # Get name pattern if Branch has Name field
        name_field = None
        for attr_name in dir(self.model_class):
            if attr_name.startswith("_"):
                continue
            attr = getattr(self.model_class, attr_name)
            if hasattr(attr, 'pattern'):  # Is a Name descriptor
                name_field = (attr_name, attr)
                break
        
        if name_field:
            # Query branches or folders based on pattern
            field_name, field_descriptor = name_field
            base_path = field_descriptor.format.split('{')[0].rstrip('/')
            
            # List branches or folders
            instances = self._list_matching_items(
                owner, repo, branch, token, base_path, field_descriptor
            )
            
            for instance_data in instances:
                context = ExecutionContext(
                    owner=owner,
                    repo=repo,
                    token=token,
                    branch=branch,
                )
                # Resolve variables from path/name
                vars_dict = field_descriptor.match_and_extract(
                    instance_data['name']
                )
                if vars_dict:
                    context.resolved_variables = vars_dict
                    instance = self.model_class(context=context)
                    # Set the resolved variable
                    setattr(instance, field_name, vars_dict[field_descriptor.variable_name])
                    yield instance
        else:
            # No pattern, return single instance
            context = ExecutionContext(
                owner=owner,
                repo=repo,
                token=token,
                branch=branch,
            )
            yield self.model_class(context=context)
    
    def _get_token(self) -> str:
        """Gets token from environment"""
        import os
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise GitHubORMConfigError("GITHUB_TOKEN not set")
        return token
    
    def _list_matching_items(
        self, owner: str, repo: str, branch: str, 
        token: str, base_path: str, field_descriptor
    ) -> list:
        """Lists items matching the pattern"""
        # Determine if we're looking for branches or folders
        # For now, assume folders (can be extended)
        url = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/contents/{base_path}"
        )
        
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        params = {"ref": branch}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 404:
            return []
        
        if not response.ok:
            raise GitHubORMConnectionError(
                f"Error listing {base_path}: {response.status_code}"
            )
        
        items = response.json()
        if not isinstance(items, list):
            return []
        
        # Filter items matching the pattern
        matching = []
        for item in items:
            if item.get("type") == "dir":
                full_name = item.get("path", "")
                if field_descriptor.match_and_extract(full_name):
                    matching.append(item)
        
        return matching
```

### `github_orm/branch.py` - Branch con Name y Manager

```python
from typing import Optional
from github_orm.tools.base import GitHubORMBase
from github_orm.tools.manager import Manager
from github_orm.fields import Name
from github_orm.tools.context import ExecutionContext


class Branch(GitHubORMBase):
    """Branch model with dynamic naming"""
    
    objects = None  # Will be set as class attribute
    
    def __init__(self, context: Optional[ExecutionContext] = None):
        super().__init__(context)
        self._resolve_name()
    
    def _resolve_name(self) -> None:
        """Resolves branch name from Name field if context has variables"""
        if not self._context.resolved_variables:
            return
        
        for attr_name in dir(self.__class__):
            if attr_name.startswith("_"):
                continue
            attr = getattr(self.__class__, attr_name)
            if isinstance(attr, Name):
                if attr.variable_name in self._context.resolved_variables:
                    resolved_name = attr.resolve(
                        **{attr.variable_name: self._context.resolved_variables[attr.variable_name]}
                    )
                    setattr(self, attr_name, self._context.resolved_variables[attr.variable_name])
                    # Update context with resolved branch name if needed
                    if not self._context.branch:
                        self._context.branch = resolved_name
    
    @classmethod
    def _setup_objects(cls):
        """Sets up the objects manager"""
        if cls.objects is None:
            cls.objects = Manager(cls)
```

### `github_orm/folder.py` - Folder con Path y método .all()

```python
import requests
from typing import Iterator, Optional
from github_orm.tools.base import GitHubORMBase
from github_orm.fields import Path
from github_orm.tools.context import ExecutionContext
from github_orm.tools.exceptions import GitHubORMConnectionError


class Folder(GitHubORMBase):
    """Folder model with dynamic paths"""
    
    def __init__(self, context: Optional[ExecutionContext] = None):
        super().__init__(context)
        self._resolve_path()
        self._process_children()
    
    def _resolve_path(self) -> None:
        """Resolves folder path from Path field if context has variables"""
        if not self._context.resolved_variables:
            return
        
        for attr_name in dir(self.__class__):
            if attr_name.startswith("_"):
                continue
            attr = getattr(self.__class__, attr_name)
            if isinstance(attr, Path):
                if attr.variable_name in self._context.resolved_variables:
                    resolved_path = attr.resolve(
                        **{attr.variable_name: self._context.resolved_variables[attr.variable_name]}
                    )
                    self._context.folder_path = resolved_path
                    setattr(self, attr_name, self._context.resolved_variables[attr.variable_name])
    
    def _process_children(self) -> None:
        """Processes children files defined in class"""
        from github_orm.file.json import JsonFile
        
        for attr_name in dir(self.__class__):
            if attr_name.startswith("_") or attr_name in ["Meta"]:
                continue
            
            attr = getattr(self.__class__, attr_name)
            
            if isinstance(attr, JsonFile):
                context = self._context.copy()
                file_path = context.folder_path or ""
                
                file_instance = JsonFile(
                    context=context,
                    name=attr.name,
                    path=file_path,
                    required=getattr(attr, 'required', False),
                    schema=getattr(attr, 'schema', None),
                )
                file_instance._context.file_name = attr.name
                setattr(self, attr_name, file_instance)
    
    def all(self) -> Iterator["Folder"]:
        """Returns iterator over all folders matching the pattern"""
        # Find Path field
        path_field = None
        for attr_name in dir(self.__class__):
            if attr_name.startswith("_"):
                continue
            attr = getattr(self.__class__, attr_name)
            if isinstance(attr, Path):
                path_field = (attr_name, attr)
                break
        
        if not path_field:
            yield self
            return
        
        field_name, field_descriptor = path_field
        base_path = field_descriptor.format.split('{')[0].rstrip('/')
        
        # List folders matching pattern
        items = self._list_matching_folders(base_path, field_descriptor)
        
        for item in items:
            vars_dict = field_descriptor.match_and_extract(item['path'])
            if vars_dict:
                context = self._context.copy()
                context.resolved_variables = vars_dict
                context.folder_path = item['path']
                instance = self.__class__(context=context)
                setattr(instance, field_name, vars_dict[field_descriptor.variable_name])
                yield instance
    
    def _list_matching_folders(self, base_path: str, field_descriptor) -> list:
        """Lists folders matching the pattern"""
        url = (
            f"https://api.github.com/repos/"
            f"{self._context.owner}/{self._context.repo}/contents/{base_path}"
        )
        
        headers = {
            "Authorization": f"token {self._context.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        params = {"ref": self._context.branch or "main"}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 404:
            return []
        
        if not response.ok:
            raise GitHubORMConnectionError(
                f"Error listing {base_path}: {response.status_code}"
            )
        
        items = response.json()
        if not isinstance(items, list):
            return []
        
        matching = []
        for item in items:
            if item.get("type") == "dir":
                full_path = item.get("path", "")
                if field_descriptor.match_and_extract(full_path):
                    matching.append(item)
        
        return matching
```

### `github_orm/file/json.py` - JsonFile

```python
import json
import base64
import requests
from typing import Optional, Dict, Any
from github_orm.tools.base import GitHubORMBase
from github_orm.tools.context import ExecutionContext
from github_orm.tools.exceptions import (
    GitHubORMConnectionError,
    GitHubORMValidationError
)


class JsonFile(GitHubORMBase):
    """JSON file"""
    
    def __init__(
        self,
        context: Optional[ExecutionContext] = None,
        name: Optional[str] = None,
        path: Optional[str] = None,
        required: bool = False,
        schema: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(context)
        
        self.name = name
        self.required = required
        self.schema = schema
        
        if name:
            self._context.file_name = name
            self._context.file_type = "json"
        
        if path:
            self._context.folder_path = path.strip("/")
    
    def read(self) -> Dict[str, Any]:
        """Reads file and parses as JSON"""
        self._context.validate_for_read()
        
        file_path = self._context.get_file_path()
        branch = self._context.branch or "main"
        
        url = (
            f"https://api.github.com/repos/"
            f"{self._context.owner}/{self._context.repo}/contents/{file_path}"
        )
        
        headers = {
            "Authorization": f"token {self._context.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        params = {"ref": branch}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 404:
            if self.required:
                raise GitHubORMConnectionError(
                    f"Required file {file_path} not found in branch {branch}"
                )
            return {}
        
        if not response.ok:
            raise GitHubORMConnectionError(
                f"GitHub API error {response.status_code}: {response.text}"
            )
        
        data = response.json()
        
        if data.get("type") != "file":
            raise GitHubORMValidationError(
                f"{file_path} is not a file"
            )
        
        content_base64 = data.get("content", "")
        content_bytes = base64.b64decode(content_base64)
        content_str = content_bytes.decode("utf-8").rstrip()
        
        try:
            json_data = json.loads(content_str)
        except json.JSONDecodeError as e:
            raise GitHubORMValidationError(
                f"Invalid JSON in {file_path}: {e}"
            )
        
        if self.schema:
            self._validate_schema(json_data)
        
        return json_data
    
    def _validate_schema(self, data: Dict[str, Any]) -> None:
        """Validates content against defined schema"""
        if self.schema.get("type") == "object":
            if not isinstance(data, dict):
                raise GitHubORMValidationError(
                    f"Expected object in {self._context.get_file_path()}"
                )
```

### `github_orm/__init__.py`

```python
from github_orm.branch import Branch
from github_orm.folder import Folder
from github_orm.file.json import JsonFile
from github_orm.fields import Path, Name

# Alias for convenience
Branch.Name = Name
Folder.Path = Path

__all__ = [
    "Branch",
    "Folder", 
    "JsonFile",
    "Path",
    "Name",
]
```

## Características principales

1. **Descriptores dinámicos**: `Path` y `Name` que resuelven variables desde paths/nombres reales usando regex patterns
2. **Manager pattern**: `.objects.all()` similar a Django para iterar sobre instancias que cumplen un patrón
3. **Método `.all()` en Folder**: Busca todas las carpetas que cumplen el patrón definido en `Path`
4. **Resolución automática de variables**: Extrae variables de paths/nombres reales y las asigna como atributos del objeto
5. **Contexto con variables resueltas**: El `ExecutionContext` mantiene las variables resueltas para uso posterior

## Flujo de ejecución

### Para Branch con `.objects.all()`:
1. Busca el descriptor `Name` en la clase
2. Extrae el path base del formato
3. Lista carpetas/directorios en ese path
4. Para cada item, intenta hacer match con el patrón
5. Si hay match, extrae la variable y crea una instancia con esa variable resuelta

### Para Folder con `.all()`:
1. Busca el descriptor `Path` en la clase
2. Extrae el path base del formato
3. Lista carpetas en ese path base
4. Para cada carpeta, intenta hacer match con el patrón
5. Si hay match, crea una instancia con la variable resuelta del path

### Para acceso a archivos:
1. El `Folder` procesa sus hijos `JsonFile` durante `__init__`
2. Cada `JsonFile` usa el contexto del `Folder` padre
3. `read()` construye el path completo y hace la petición a GitHub API


