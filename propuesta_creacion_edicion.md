# Propuesta de Implementación: Creación y Edición en GitHub ORM

## Objetivo

Implementar las interfaces de creación y edición del ORM, considerando:

- La implementación depende de la configuración (si el repo o el branch ya existe)
- Si no existe: la creación es a base de commits directos
- Si existe: debe ser por PRs
- Según la configuración del ORM, la PR se puede auto-merge o no

## Cambios Requeridos

### 1. Extender `GitHubClient` con métodos de escritura

Se deben agregar los siguientes métodos a `github_orm/tools/github_client.py`:

```python
from typing import Optional

def repo_exists(self, owner: str, repo: str) -> bool:
    """Check if repository exists."""
    try:
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return response.status_code == 200
    except Exception:
        return False

def branch_exists(self, owner: str, repo: str, branch: str) -> bool:
    """Check if branch exists."""
    try:
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return response.status_code == 200
    except Exception:
        return False

def get_default_branch(self, owner: str, repo: str) -> str:
    """Get default branch of repository."""
    response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers={"Authorization": f"Bearer {self.token}"}
    )
    response.raise_for_status()
    return response.json()['default_branch']

def get_sha(self, owner: str, repo: str, branch: str, path: str) -> Optional[str]:
    """Get SHA of file if it exists."""
    try:
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        if response.status_code == 200:
            return response.json()['sha']
    except Exception:
        pass
    return None

def get_branch_sha(self, owner: str, repo: str, branch: str) -> Optional[str]:
    """Get SHA of branch head."""
    try:
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        if response.status_code == 200:
            return response.json()['object']['sha']
    except Exception:
        pass
    return None

def create_branch(self, owner: str, repo: str, branch: str, 
                  from_branch: str = "main") -> bool:
    """Create a new branch from base branch."""
    base_sha = self.get_branch_sha(owner, repo, from_branch)
    if not base_sha:
        return False
    
    response = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/git/refs",
        headers={
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        },
        json={
            "ref": f"refs/heads/{branch}",
            "sha": base_sha
        }
    )
    return response.status_code == 201

def create_or_update_file(
    self, owner: str, repo: str, branch: str, path: str,
    content: str, message: str, sha: Optional[str] = None
) -> bool:
    """Create or update a file in repository."""
    content_encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    data = {
        "message": message,
        "content": content_encoded,
        "branch": branch
    }
    
    if sha:
        data["sha"] = sha
    
    response = requests.put(
        f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
        headers={
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        },
        json=data
    )
    return response.status_code in [200, 201]

def create_pull_request(
    self, owner: str, repo: str, title: str, head: str,
    base: str, body: str = ""
) -> Optional[int]:
    """Create a pull request. Returns PR number if successful."""
    response = requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        headers={
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        },
        json={
            "title": title,
            "head": head,
            "base": base,
            "body": body
        }
    )
    if response.status_code == 201:
        return response.json()['number']
    return None

def merge_pull_request(
    self, owner: str, repo: str, pr_number: int,
    merge_method: str = "merge"
) -> bool:
    """Merge a pull request."""
    response = requests.put(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/merge",
        headers={
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        },
        json={"merge_method": merge_method}
    )
    return response.status_code == 200
```

### 2. Extender la clase `Meta` para soportar configuración

Se deben agregar los siguientes parámetros a la clase `Meta` en 
`github_orm/tools/github_handler_base.py`:

```python
class Meta:
    """Metadata class for models."""
    
    def __init__(
        self, 
        owner: Optional[Union[str, Field]] = None, 
        repo: Optional[Union[str, Field]] = None, 
        branch: Optional[Union[str, Field]] = None, 
        folder_path: Optional[Union[str, Field]] = None, 
        file_name: Optional[Union[str, Field]] = None,
        base_branch: Optional[str] = None,
        auto_merge: bool = False,
        merge_method: str = "merge"
    ) -> None:
        self.owner = Field.create_field(getattr(self, 'owner', owner))
        self.repo = Field.create_field(getattr(self, 'repo', repo))
        self.branch = Field.create_field(getattr(self, 'branch', branch))
        self.folder_path = Field.create_field(
            getattr(self, 'folder_path', folder_path)
        )
        self.file_name = Field.create_field(
            getattr(self, 'file_name', file_name)
        )
        self.base_branch = base_branch or getattr(self, 'base_branch', None)
        self.auto_merge = auto_merge if hasattr(self, 'auto_merge') else (
            getattr(self, 'auto_merge', False)
        )
        self.merge_method = merge_method or getattr(
            self, 'merge_method', "merge"
        )
    
    def __add__(self, other: 'Meta') -> 'Meta':
        if other is None:
            return self
        
        return Meta(
            owner=self.owner or other.owner,
            repo=self.repo or other.repo,
            branch=self.branch or other.branch,
            folder_path=self.folder_path or other.folder_path,
            file_name=self.file_name or other.file_name,
            base_branch=self.base_branch or other.base_branch,
            auto_merge=self.auto_merge or other.auto_merge,
            merge_method=self.merge_method or other.merge_method,
        )
    
    @staticmethod
    def from_class(meta) -> 'Meta':
        if meta is None:
            return Meta()
        
        return Meta(
            owner=getattr(meta, 'owner', None),
            repo=getattr(meta, 'repo', None),
            branch=getattr(meta, 'branch', None),
            folder_path=getattr(meta, 'folder_path', None),
            file_name=getattr(meta, 'file_name', None),
            base_branch=getattr(meta, 'base_branch', None),
            auto_merge=getattr(meta, 'auto_merge', False),
            merge_method=getattr(meta, 'merge_method', 'merge'),
        )
```

### 3. Agregar métodos `save()` y `write()` a `GitHubFile`

Se deben agregar los siguientes métodos a la clase `GitHubFile`:

```python
class GitHubFile:
    _github_client: GitHubClient = GitHubClient()
    
    def __init__(self, meta: Optional[Meta]) -> None:
        self.meta = meta + Meta.from_class(getattr(self, 'Meta', None))
        self._content = None
        self._is_modified = False
    
    def read(self):
        if self._content is None:
            content = self._github_client.get_file_content(
                self.meta.owner,
                self.meta.repo,
                self.meta.branch,
                self.meta.folder_path + self.meta.file_name,
            )
            self._content = content
        return self._content
    
    def write(self, content: str) -> None:
        """Set content to be written."""
        self._content = content
        self._is_modified = True
    
    def save(self, message: str = "Update file") -> bool:
        """Save file to GitHub. Returns True if successful."""
        if not self._is_modified or self._content is None:
            return False
        
        owner = self.meta.owner
        repo = self.meta.repo
        branch = self.meta.branch
        path = self.meta.folder_path + self.meta.file_name
        
        if not all([owner, repo, branch, path]):
            raise GitHubOrmError(
                "Missing required meta: owner, repo, branch, or path"
            )
        
        base_branch = self.meta.base_branch
        if base_branch is None:
            base_branch = self._github_client.get_default_branch(owner, repo)
        
        branch_exists = self._github_client.branch_exists(owner, repo, branch)
        sha = self._github_client.get_sha(owner, repo, branch, path)
        
        if not branch_exists:
            self._github_client.create_branch(owner, repo, branch, base_branch)
        
        success = self._github_client.create_or_update_file(
            owner, repo, branch, path, self._content, message, sha
        )
        
        if success and branch_exists and branch != base_branch:
            pr_number = self._github_client.create_pull_request(
                owner, repo,
                title=f"Update {path}",
                head=branch,
                base=base_branch,
                body=message
            )
            
            if pr_number and self.meta.auto_merge:
                self._github_client.merge_pull_request(
                    owner, repo, pr_number, self.meta.merge_method
                )
        
        if success:
            self._is_modified = False
        
        return success
```

### 4. Agregar métodos `save()` y `create()` a `GitHubModel`

Se deben agregar los siguientes métodos a la clase `GitHubModel`:

```python
class GitHubModel:

    def __init__(self, **kwargs) -> None:
        _meta = kwargs.pop('meta', None)
        self._meta_dict = _meta or {}
        for property, annotation in inspect.get_annotations(
            self.__class__
        ).items():
            if issubclass(annotation, GitHubFile):
                file_meta = Meta(**_meta) if _meta else None
                setattr(self, property, annotation(file_meta))
            
            if property in kwargs:
                property_value = kwargs[property]
            else:
                try:
                    property_value = getattr(self, property)
                except AttributeError:
                    raise GitHubOrmError(
                        f"Property {property} not found in "
                        f"{self.__class__.__name__}"
                    )
            
            try:
                property_value = annotation(property_value)
            except Exception:
                pass
            
            setattr(self, property, property_value)
    
    def _resolve_meta(self) -> Meta:
        """Resolve Meta from class and instance."""
        meta = Meta.from_class(getattr(self.__class__, 'Meta', None))
        
        for key, value in self._meta_dict.items():
            if hasattr(meta, key):
                setattr(meta, key, value)
        
        return meta
    
    def save(self, message: str = "Update configuration") -> bool:
        """Save all files in the model. Returns True if successful."""
        meta = self._resolve_meta()
        owner = meta.owner
        repo = meta.repo
        branch = meta.branch
        
        if not all([owner, repo, branch]):
            raise GitHubOrmError(
                "Missing required meta: owner, repo, or branch"
            )
        
        base_branch = meta.base_branch
        if base_branch is None:
            base_branch = GitHubClient().get_default_branch(owner, repo)
        
        branch_exists = GitHubClient().branch_exists(owner, repo, branch)
        
        if not branch_exists:
            GitHubClient().create_branch(owner, repo, branch, base_branch)
        
        all_success = True
        for attr_name in dir(self):
            if attr_name.startswith('_'):
                continue
            attr = getattr(self, attr_name)
            if isinstance(attr, GitHubFile):
                if attr._is_modified:
                    all_success = attr.save(message) and all_success
        
        if all_success and branch_exists and branch != base_branch:
            pr_number = GitHubClient().create_pull_request(
                owner, repo,
                title=f"Update {branch}",
                head=branch,
                base=base_branch,
                body=message
            )
            
            if pr_number and meta.auto_merge:
                GitHubClient().merge_pull_request(
                    owner, repo, pr_number, meta.merge_method
                )
        
        return all_success
    
    @classmethod
    def create(cls, **kwargs) -> 'GitHubModel':
        """Create a new instance and save it."""
        instance = cls(**kwargs)
        instance.save()
        return instance
```

## Lógica de Implementación

### Flujo de Creación/Edición

1. **Verificar existencia del branch:**
   - Si el branch no existe: crear branch desde base_branch y hacer commit directo
   - Si el branch existe: hacer commit en el branch existente

2. **Crear/Actualizar archivos:**
   - Usar `create_or_update_file` con el SHA si el archivo existe (para update)
   - Sin SHA si es un archivo nuevo (para create)

3. **Manejo de PRs:**
   - Si el branch existe Y es diferente del base_branch: crear PR
   - Si `auto_merge` está configurado: mergear automáticamente la PR
   - Si `auto_merge` es False: dejar la PR abierta para revisión manual

### Configuración en Meta

Los modelos pueden configurar el comportamiento de creación/edición:

```python
class MopsConfig(GitHubModel):
    class Meta:
        owner = "myorg"
        repo = "myrepo"
        branch = r'config/mops/{tenant_code}'
        folder_path = r'configs/mops/{operation_code}/piper_integration/'
        base_branch = "main"  # Branch base para PRs
        auto_merge = True     # Auto-mergear PRs
        merge_method = "squash"  # Método de merge: merge, squash, rebase
    
    tenant: str
    operation: str
    piper_integration_config: PiperIntegrationConfig
```

## Ejemplo de Uso

### Crear un nuevo modelo

```python
config = MopsConfig(
    tenant="tenant1",
    operation="op1",
    meta={
        'branch': 'config/mops/tenant1',
        'folder_path': 'configs/mops/op1/piper_integration/'
    }
)

config.piper_integration_config.write('{"key": "value"}')
config.save(message="Add new tenant configuration")
```

### Editar un modelo existente

```python
for config in MopsConfig.objects.all():
    if config.tenant == "tenant1":
        content = config.piper_integration_config.read()
        # Modificar content
        config.piper_integration_config.write(modified_content)
        config.save(message="Update tenant configuration")
```

## Consideraciones

1. **SHA para updates:** Es necesario obtener el SHA del archivo existente para poder actualizarlo correctamente.

2. **Branch vs Base Branch:** Si el branch es el mismo que el base_branch, no se crea PR (commits directos).

3. **Auto-merge:** Solo funciona si el repositorio tiene configurado auto-merge en GitHub y el token tiene permisos suficientes.

4. **Métodos de merge:** GitHub soporta tres métodos:
   - `merge`: Crea un merge commit
   - `squash`: Squash todos los commits en uno
   - `rebase`: Rebase los commits

5. **Manejo de errores:** Todos los métodos deben manejar errores de API de GitHub apropiadamente.





