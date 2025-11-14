# Propuesta de Implementación: GitHub ORM

## Introducción

Esta propuesta documenta la implementación completa de una biblioteca ORM (Object-Relational Mapping) para GitHub que permite a los usuarios interactuar con repositorios, ramas, carpetas y archivos de GitHub usando una interfaz orientada a objetos similar a Django ORM.

## Objetivos

- Proporcionar una interfaz intuitiva para acceder a recursos de GitHub
- Permitir matching de patrones en nombres de ramas y rutas de archivos
- Soportar navegación anidada a través de ramas → carpetas → archivos
- Mantener un diseño extensible y fácil de usar

## Arquitectura General

La biblioteca se estructura en los siguientes componentes principales:

```
github_orm/
├── __init__.py          # Exports principales
├── client.py            # Cliente singleton para GitHub API
├── base.py              # Clases base (Model, Meta, Field, Manager)
├── branch.py            # Modelo de Branch (ramas)
├── folder.py            # Modelo de Folder (carpetas)
└── file.py              # Modelo de File y JsonFile (archivos)
```

## Componentes Principales

### 1. Cliente de GitHub API (`client.py`)

El cliente gestiona todas las interacciones con la API de GitHub usando PyGithub.

**Características:**
- Patrón Singleton para mantener una única instancia
- Autenticación mediante token (variable de entorno o parámetro)
- Métodos para obtener repositorios, ramas y contenidos

**Implementación:**

```python
# github_orm/client.py
import os
from typing import Optional
from github import Github
from github.Repository import Repository
from github.Branch import Branch as GitHubBranch
from github.ContentFile import ContentFile


class GitHubClient:
    """Singleton client for GitHub API interactions."""
    
    _instance: Optional['GitHubClient'] = None
    _github: Optional[Github] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def authenticate(self, token: Optional[str] = None):
        """Authenticate with GitHub using token."""
        token = token or os.getenv('GITHUB_TOKEN')
        if not token:
            raise ValueError(
                "GitHub token required. Set GITHUB_TOKEN env var or "
                "call authenticate(token='...')"
            )
        self._github = Github(token)
    
    @property
    def github(self) -> Github:
        """Get authenticated GitHub instance."""
        if self._github is None:
            self.authenticate()
        return self._github
    
    def get_repo(self, owner: str, repo: str) -> Repository:
        """Get repository instance."""
        return self.github.get_repo(f"{owner}/{repo}")
    
    def get_branches(self, owner: str, repo: str):
        """Get all branches from repository."""
        repository = self.get_repo(owner, repo)
        return repository.get_branches()
    
    def get_contents(
        self, owner: str, repo: str, path: str, ref: str = "main"
    ):
        """Get contents at path in repository."""
        repository = self.get_repo(owner, repo)
        try:
            return repository.get_contents(path, ref=ref)
        except Exception:
            return None
    
    def get_directory_contents(
        self, owner: str, repo: str, path: str, ref: str = "main"
    ):
        """Get all contents in a directory."""
        repository = self.get_repo(owner, repo)
        try:
            contents = repository.get_contents(path, ref=ref)
            if isinstance(contents, list):
                return contents
            elif isinstance(contents, ContentFile):
                return [contents]
            return []
        except Exception:
            return []
```

### 2. Sistema Base de Modelos (`base.py`)

Define las clases fundamentales que todos los modelos heredan.

**Componentes:**

#### `Meta`
Clase para almacenar metadatos del modelo (owner, repo).

#### `Field`
Clase base para matching de patrones usando expresiones regulares. Convierte strings con formato `{variable}` a regex patterns.

#### `Manager`
Implementa el patrón Manager para queries (similar a Django). Permite `Model.objects.all()`.

#### `Model`
Clase abstracta base que todos los modelos heredan. Maneja el sistema de Meta y Managers.

**Implementación:**

```python
# github_orm/base.py
import re
from typing import Type, TypeVar, Optional, Dict, Any, Iterator
from abc import ABC, abstractmethod

T = TypeVar('T', bound='Model')


class Meta:
    """Metadata class for models."""
    def __init__(self):
        self.owner: Optional[str] = None
        self.repo: Optional[str] = None


class Field:
    """Base field class for path pattern matching."""
    def __init__(self, format: str):
        self.format = format
        self._pattern = self._compile_pattern(format)
    
    def _compile_pattern(self, format_str: str) -> re.Pattern:
        """Convert format string to regex pattern."""
        pattern = format_str.replace('/', r'\/')
        pattern = re.sub(r'\{(\w+)\}', r'(?P<\1>[^/]+)', pattern)
        return re.compile(f'^{pattern}$')
    
    def match(self, path: str) -> Optional[Dict[str, str]]:
        """Match path against pattern and extract groups."""
        match = self._pattern.match(path)
        if match:
            return match.groupdict()
        return None


class Manager:
    """Manager for querying model instances."""
    
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class
    
    def all(self) -> Iterator[T]:
        """Return all instances matching the model."""
        meta = self.model_class._meta
        if not meta or not meta.owner or not meta.repo:
            raise ValueError(
                "Model Meta must define owner and repo"
            )
        
        from .client import GitHubClient
        client = GitHubClient()
        branches = client.get_branches(meta.owner, meta.repo)
        
        for branch in branches:
            instance = self.model_class(branch.name)
            if instance.matches():
                yield instance


class Model(ABC):
    """Base model class for GitHub ORM."""
    
    _meta: Optional[Meta] = None
    objects: Manager
    
    def __init__(self):
        """Initialize model instance."""
        self._context: Dict[str, Any] = {}
    
    def __init_subclass__(cls, **kwargs):
        """Initialize subclass and create manager."""
        super().__init_subclass__(**kwargs)
        
        # Create Meta instance if defined
        if hasattr(cls, 'Meta'):
            cls._meta = cls.Meta()
        
        # Create objects manager
        cls.objects = Manager(cls)
    
    def _get_context(self) -> Dict[str, Any]:
        """Get context for path resolution."""
        return self._context
    
    @abstractmethod
    def matches(self) -> bool:
        """Check if instance matches model criteria."""
        pass
```

### 3. Modelo Branch (`branch.py`)

Representa una rama de GitHub. Puede tener campos `BranchName` para matching de patrones y atributos anidados (Folders, Files).

**Características:**
- Matching de nombres de ramas usando `BranchName` field
- Soporte para atributos anidados (folders, files)
- Contexto que se pasa a objetos hijos

**Implementación:**

```python
# github_orm/branch.py
import re
from typing import Optional, Dict, Any
from .base import Model, Field


class BranchName(Field):
    """Field for matching branch names."""
    pass


class Branch(Model):
    """Model representing a GitHub branch."""
    
    def __init__(self, name: str):
        """Initialize branch with name."""
        super().__init__()
        self.name = name
        self._context = {'branch': name}
        self._meta_resolved = False
    
    def _resolve_meta(self):
        """Resolve meta information from class."""
        if not self._meta_resolved and self._meta:
            self._context['owner'] = self._meta.owner
            self._context['repo'] = self._meta.repo
            self._meta_resolved = True
    
    def matches(self) -> bool:
        """Check if branch name matches pattern."""
        self._resolve_meta()
        
        # Find Branch.Name field in class attributes
        for attr_name in dir(self.__class__):
            if attr_name.startswith('_'):
                continue
            attr = getattr(self.__class__, attr_name)
            if isinstance(attr, BranchName):
                match = attr.match(self.name)
                if match:
                    self._context.update(match)
                    return True
        
        # If no BranchName field, match all branches
        return True
    
    def _get_context(self) -> Dict[str, Any]:
        """Get context for nested access."""
        self._resolve_meta()
        return self._context.copy()
    
    def __getattr__(self, name: str):
        """Get nested folder or file attributes."""
        # Look for attribute in class definition
        if hasattr(self.__class__, name):
            attr = getattr(self.__class__, name)
            from .folder import Folder
            from .file import File
            if isinstance(attr, (Folder, File)):
                return attr.bind(self)
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )
```

### 4. Modelo Folder (`folder.py`)

Representa una carpeta en el repositorio. Usa `Path` field para matching de patrones de rutas.

**Características:**
- Matching de rutas usando `Path` field con formato `{variable}`
- Soporte para múltiples instancias con `all()`
- Binding a contexto del padre (Branch u otro Folder)
- Atributos anidados (sub-folders, files)

**Implementación:**

```python
# github_orm/folder.py
import re
from typing import Iterator, Optional, Dict, Any, List
from .base import Model, Field
from .client import GitHubClient
from .file import File


class Path(Field):
    """Field for matching folder paths."""
    pass


class Folder:
    """Represents a folder in the repository."""
    
    def __init__(self):
        self.operation: Optional[Field] = None
    
    def __init_subclass__(cls, **kwargs):
        """Initialize folder subclass."""
        # Find Path field in class attributes
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, Path):
                cls._path_field = attr
                break
    
    def bind(self, parent) -> 'FolderInstance':
        """Bind folder to parent context."""
        if hasattr(parent, '_get_context'):
            context = parent._get_context()
        elif isinstance(parent, dict):
            context = parent
        else:
            context = {}
        return FolderInstance(self.__class__, context)


class FolderInstance:
    """Instance of a folder bound to a context."""
    
    def __init__(self, folder_class: type, parent_context: Dict[str, Any]):
        self._folder_class = folder_class
        self._parent_context = parent_context.copy()
        self._path: Optional[str] = None
        self._operation: Optional[str] = None
    
    def _get_context(self) -> Dict[str, Any]:
        """Get context including this folder's values."""
        ctx = self._parent_context.copy()
        if self._operation:
            ctx['operation'] = self._operation
        return ctx
    
    def _resolve_path(self) -> str:
        """Resolve folder path using context."""
        if hasattr(self._folder_class, '_path_field'):
            path = self._folder_class._path_field.format
            # Replace placeholders with context values
            for key, value in self._parent_context.items():
                path = path.replace(f'{{{key}}}', str(value))
            # Clean up any unmatched placeholders
            path = re.sub(r'\{[^}]+\}', '', path)
            return path.rstrip('/')
        return ""
    
    @property
    def path(self) -> str:
        """Get resolved path."""
        if self._path is None:
            self._path = self._resolve_path()
        return self._path
    
    @property
    def operation(self) -> Optional[str]:
        """Get operation name from context."""
        return self._parent_context.get('operation')
    
    def all(self) -> Iterator['FolderInstance']:
        """Get all matching folder instances."""
        context = self._parent_context
        branch_name = context.get('branch')
        owner = context.get('owner')
        repo = context.get('repo')
        
        if not owner or not repo:
            raise ValueError("Owner and repo required in context")
        
        # Get base path (parent directories)
        path_field = getattr(self._folder_class, '_path_field', None)
        if not path_field:
            return
        
        # Extract directory part before the last {placeholder}
        base_path = path_field.format
        # Find last {placeholder}
        match = re.search(r'\{(\w+)\}[^/]*$', base_path)
        if not match:
            return
        
        # Get path before the last placeholder
        base_path = base_path[:match.start()].rstrip('/')
        
        # Resolve base path with current context
        for key, value in context.items():
            base_path = base_path.replace(f'{{{key}}}', str(value))
        base_path = re.sub(r'\{[^}]+\}', '', base_path).rstrip('/')
        
        # Get directory listing
        client = GitHubClient()
        contents = client.get_directory_contents(
            owner, repo, base_path, ref=branch_name
        )
        
        # Match each directory name against pattern
        for content in contents:
            if content.type == 'dir':
                # Extract just the directory name
                dir_name = content.name
                # Full path for pattern matching
                full_path = f"{base_path}/{dir_name}"
                match_dict = path_field.match(full_path)
                if match_dict:
                    new_context = context.copy()
                    new_context.update(match_dict)
                    new_context['operation'] = dir_name
                    instance = FolderInstance(
                        self._folder_class, new_context
                    )
                    instance._operation = dir_name
                    yield instance
    
    def __getattr__(self, name: str):
        """Get nested file or folder attributes."""
        if hasattr(self._folder_class, name):
            attr = getattr(self._folder_class, name)
            # Check if it's a File or Folder
            from .file import File
            if isinstance(attr, (Folder, File)):
                return attr.bind(self)
        raise AttributeError(
            f"'{self._folder_class.__name__}' object has no attribute '{name}'"
        )
```

### 5. Modelo File y JsonFile (`file.py`)

Representa archivos en el repositorio. `JsonFile` extiende `File` para parsear automáticamente JSON.

**Características:**
- Soporte para archivos genéricos y JSON
- Lectura lazy (solo cuando se llama `read()`)
- Binding a contexto del padre (Folder o Branch)

**Implementación:**

```python
# github_orm/file.py
import json
import base64
from typing import Optional, Dict, Any
from .client import GitHubClient


class File:
    """Base class for file models."""
    
    def __init__(self):
        self.name: Optional[str] = None
        self.schema: Optional[Dict] = None
    
    def __init_subclass__(cls, **kwargs):
        """Initialize file subclass."""
        super().__init_subclass__(**kwargs)
        # Store name from class attribute if defined
        if hasattr(cls, 'name'):
            cls._file_name = cls.name
    
    def bind(self, parent) -> 'FileInstance':
        """Bind file to parent context."""
        if hasattr(parent, '_get_context'):
            context = parent._get_context()
        elif isinstance(parent, dict):
            context = parent
        else:
            context = {}
        return FileInstance(self.__class__, context, parent)


class FileInstance:
    """Instance of a file bound to a context."""
    
    def __init__(
        self, file_class: type, context: Dict[str, Any], parent
    ):
        self._file_class = file_class
        self._context = context
        self._parent = parent
        self._content: Optional[Any] = None
    
    def _get_file_path(self) -> str:
        """Get full path to file."""
        file_name = getattr(self._file_class, '_file_name', '')
        
        # If parent is FolderInstance, get its path
        if hasattr(self._parent, 'path'):
            parent_path = self._parent.path
            return f"{parent_path}/{file_name}".strip('/')
        
        # Otherwise try to construct from context
        return file_name
    
    def read(self) -> Any:
        """Read and return file contents."""
        if self._content is not None:
            return self._content
        
        file_path = self._get_file_path()
        branch = self._context.get('branch', 'main')
        owner = self._context.get('owner')
        repo = self._context.get('repo')
        
        if not owner or not repo:
            raise ValueError("Owner and repo required in context")
        
        client = GitHubClient()
        contents = client.get_contents(owner, repo, file_path, ref=branch)
        
        if not contents:
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Decode content
        content_str = contents.content
        if isinstance(content_str, str):
            # Already decoded
            pass
        else:
            # Base64 decode
            content_str = base64.b64decode(content_str).decode('utf-8')
        
        # Parse as JSON if JsonFile
        if JsonFile in self._file_class.__mro__:
            self._content = json.loads(content_str)
        else:
            self._content = content_str
        
        return self._content


class JsonFile(File):
    """Represents a JSON file."""
    pass
```

### 6. Módulo Principal (`__init__.py`)

Exporta todas las clases públicas de la biblioteca.

**Implementación:**

```python
# github_orm/__init__.py
from .base import Model, Meta, Field
from .branch import Branch, BranchName
from .folder import Folder, Path
from .file import File, JsonFile

__all__ = [
    'Model', 'Meta', 'Field',
    'Branch', 'BranchName',
    'Folder', 'Path',
    'File', 'JsonFile'
]
```

## Flujo de Ejecución

### Ejemplo de Uso

Basado en el archivo `mops_config_example.py`:

```python
import github_orm as gorm

class PiperConfigFile(gorm.JsonFile):
    name = "piper_config.json"
    schema = {
        "type": "object",
    }

class PiperIntegrationConfigFolder(gorm.Folder):
    operation = gorm.Folder.Path(format=r'configs/mops/{operation}/piper_integration/')
    
    validation_config = PiperConfigFile()
    
class MopsConfig(gorm.Branch):
    class Meta:
        owner = "myorg"
        repo = "myrepo"
     
    tenant = gorm.Branch.Name(format=r'config/mops/{tenant}')
    piper_integration_config = PiperIntegrationConfigFolder()
    

if __name__ == "__main__":
    configs = MopsConfig.objects.all()
    config = next(configs)
    print(config.tenant)
    
    piper_configs = config.piper_integration_config.all()
    piper_config = next(piper_configs)
    print(piper_config.operation)
    
    validation_json = piper_config.validation_config.read()
    print(validation_json)
```

### Paso a Paso

1. **Definición del Modelo Branch (`MopsConfig`)**:
   - Define `Meta` con `owner` y `repo`
   - Define `tenant` usando `Branch.Name` con pattern `r'config/mops/{tenant}'`
   - Define `piper_integration_config` como `Folder`

2. **Query de Ramas**:
   - `MopsConfig.objects.all()` itera sobre todas las ramas del repo
   - Para cada rama, crea una instancia `MopsConfig`
   - `matches()` verifica si el nombre de la rama coincide con el pattern
   - Si coincide, extrae `tenant` del nombre y lo guarda en el contexto

3. **Acceso a Folder**:
   - `config.piper_integration_config` crea un `FolderInstance` bound al contexto de la rama
   - `piper_integration_config.all()` lista directorios en `configs/mops/{operation}/piper_integration/`
   - Para cada directorio que coincida con el pattern, crea un `FolderInstance`

4. **Acceso a File**:
   - `piper_config.validation_config` crea un `FileInstance` bound al contexto del folder
   - `read()` descarga y parsea el contenido JSON del archivo

## Patrón de Matching

### Format Strings

Los format strings usan `{variable}` para capturar valores:

- `r'config/mops/{tenant}'` → matchea ramas como `config/mops/acme` y extrae `tenant='acme'`
- `r'configs/mops/{operation}/piper_integration/'` → matchea paths como `configs/mops/operation1/piper_integration/` y extrae `operation='operation1'`

### Conversión a Regex

```python
format: r'config/mops/{tenant}'
regex:  r'^config\/mops\/(?P<tenant>[^/]+)$'
```

## Dependencias

### Requerimientos

```txt
PyGithub>=1.59.0
```

### Instalación

```bash
pip install PyGithub
```

### Autenticación

La biblioteca requiere un token de GitHub:

```python
# Opción 1: Variable de entorno
export GITHUB_TOKEN=tu_token_aqui

# Opción 2: Programática
from github_orm.client import GitHubClient
client = GitHubClient()
client.authenticate(token="tu_token_aqui")
```

## Consideraciones de Diseño

### 1. Lazy Loading

- Los contenidos de archivos se cargan solo cuando se llama `read()`
- Los directorios se listan solo cuando se llama `all()`
- Esto optimiza el uso de la API de GitHub

### 2. Context Propagation

- El contexto se propaga de padre a hijo (Branch → Folder → File)
- Cada nivel agrega sus variables extraídas del matching
- Permite construir paths anidados automáticamente

### 3. Pattern Matching

- Los patterns son flexibles y permiten capturar múltiples variables
- El matching es case-sensitive
- Los placeholders no coincidentes se limpian automáticamente

### 4. Singleton Client

- Una sola instancia de `GitHubClient` para toda la aplicación
- Evita crear múltiples conexiones a la API
- Facilita la gestión de autenticación

## Mejoras Futuras

### 1. Caching

- Cachear resultados de API calls para reducir requests
- TTL configurable para diferentes tipos de recursos

### 2. Validación de Schema

- Implementar validación JSON usando el campo `schema` en `JsonFile`
- Soporte para JSON Schema

### 3. Escritura de Archivos

- Método `write()` para modificar archivos
- Soporte para crear/actualizar/eliminar archivos

### 4. Paginación

- Soporte para repositorios con muchas ramas
- Lazy iterators que cargan bajo demanda

### 5. Manejo de Errores

- Mejor manejo de errores de API
- Retry logic para rate limiting
- Mensajes de error más descriptivos

### 6. Testing

- Unit tests para cada componente
- Integration tests con repositorios de prueba
- Mock de GitHub API para tests

### 7. Documentación

- Docstrings completos
- Ejemplos en README
- Type hints completos

## Estructura de Archivos Final

```
github_orm/
├── __init__.py
├── client.py
├── base.py
├── branch.py
├── folder.py
└── file.py

examples/
└── mops_config_example.py

requirements.txt
README.md
```

## Conclusión

Esta propuesta proporciona una implementación completa de un ORM para GitHub que permite:

- Definir modelos de manera declarativa
- Hacer queries usando el patrón `objects.all()`
- Navegar anidadamente a través de ramas, carpetas y archivos
- Matching de patrones flexible en nombres y rutas
- Interfaz intuitiva similar a Django ORM

La arquitectura es extensible y permite agregar nuevas funcionalidades sin romper la API existente.



