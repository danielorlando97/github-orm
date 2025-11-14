# Propuesta de Implementación: GitHub ORM

ORM basado en GitHub inspirado en Django para mapear estructuras de
repositorios GitHub (branches, folders, files) como modelos Python.

## Arquitectura General

### Estructura de Archivos

```
github_orm/
├── __init__.py              # Exports principales
├── base.py                  # Clases base Model, Manager, Meta
├── fields.py                # Campos Name, Path con extracción regex
├── nodes/
│   ├── __init__.py
│   ├── branch.py            # Modelo Branch
│   ├── folder.py            # Modelo Folder
│   └── file/
│       ├── __init__.py
│       └── json_file.py     # Modelo JsonFile
└── tools/
    ├── __init__.py
    └── github_client.py     # Cliente de GitHub API
```

## Componentes Principales

### 1. Clase Base Model (`github_orm/base.py`)

**Responsabilidades:**
- Proporcionar funcionalidad base similar a `django.db.models.Model`
- Manejar la clase Meta para configuración (owner, repo)
- Definir el Manager con `.objects`
- Implementar `__getattribute__` para acceso dinámico a campos

**Características:**
- `Manager`: Clase para `.objects.all()` y `.objects.filter()`
- `Model`: Clase abstracta base para todos los modelos
- `Meta`: Clase interna para configuración del repositorio
- Soporte para campos con extracción automática de valores

### 2. Campos (`github_orm/fields.py`)

**Responsabilidades:**
- Extraer valores de strings usando patrones regex
- Soportar formatos tipo `r'config/mops/{tenant}'`
- Convertir patrones con variables a regex groups

**Tipos de Campos:**
- `Name`: Extrae valores del nombre (usado en Branch)
- `Path`: Extrae valores del path (usado en Folder)

**Ejemplo de uso:**
```python
tenant = Branch.Name(format=r'config/mops/{tenant}')
# Si el branch es "config/mops/tenant1", extrae: {'tenant': 'tenant1'}
```

### 3. Cliente GitHub (`github_orm/tools/github_client.py`)

**Responsabilidades:**
- Wrapper para GitHub API usando PyGithub
- Manejar autenticación con token
- Proporcionar métodos para branches, tree, y contenido de archivos

**Métodos principales:**
- `get_branches(owner, repo)`: Lista todas las branches
- `get_tree(owner, repo, branch, path)`: Obtiene contenido de directorio
- `get_file_content(owner, repo, path, branch)`: Lee contenido de archivo

**Autenticación:**
- Requiere variable de entorno `GITHUB_TOKEN`
- Implementa patrón Singleton para reutilizar conexión

### 4. Modelo Branch (`github_orm/nodes/branch.py`)

**Responsabilidades:**
- Representar branches de un repositorio GitHub
- Extraer valores de campos usando el nombre del branch
- Proporcionar contexto para modelos anidados

**Características:**
- `objects.all()`: Retorna iterator de todas las branches
- Campos con formato para extraer valores del nombre
- Pasa contexto (branch, owner, repo) a modelos hijos

**Ejemplo:**
```python
class MopsConfig(Branch):
    class Meta:
        owner = "myorg"
        repo = "myrepo"
    
    tenant = Branch.Name(format=r'config/mops/{tenant}')
```

### 5. Modelo Folder (`github_orm/nodes/folder.py`)

**Responsabilidades:**
- Representar carpetas/directorios en el repositorio
- Soportar `.all()` para listar contenido de la carpeta
- Extraer valores de campos usando el path

**Características:**
- `all()`: Retorna iterator de todas las subcarpetas/archivos
- Campos con formato para extraer valores del path
- Mantiene contexto del branch y path padre

**Ejemplo:**
```python
class PiperIntegrationConfigFolder(Folder):
    operation = Folder.Path(format=r'configs/mops/{operation}/piper_integration/')
```

### 6. Modelo JsonFile (`github_orm/nodes/file/json_file.py`)

**Responsabilidades:**
- Representar archivos JSON en el repositorio
- Leer y validar contenido JSON
- Validar contra schema opcional

**Características:**
- `read()`: Lee y retorna contenido JSON parseado
- Validación con jsonschema si se proporciona schema
- Manejo de encoding base64 de GitHub API

**Ejemplo:**
```python
class PiperConfigFile(JsonFile):
    name = "piper_config.json"
    schema = {
        "type": "object",
    }
```

## Flujo de Datos

### 1. Query de Branches

```
Usuario: MopsConfig.objects.all()
  ↓
Manager.all() → Branch._get_all_instances()
  ↓
GitHubClient.get_branches(owner, repo)
  ↓
GitHub API → Lista de branches
  ↓
Instanciar Branch para cada nombre
  ↓
Extraer valores de campos (ej: tenant) usando regex
  ↓
Retornar iterator de instancias
```

### 2. Query de Folders

```
Usuario: config.piper_integration_config.all()
  ↓
Folder.all() → GitHubClient.get_tree(owner, repo, branch, path)
  ↓
GitHub API → Contenido del directorio
  ↓
Filtrar por tipo 'dir'
  ↓
Instanciar Folder para cada directorio
  ↓
Extraer valores de campos (ej: operation) usando regex
  ↓
Retornar iterator de instancias
```

### 3. Lectura de Archivos JSON

```
Usuario: piper_config.validation_config.read()
  ↓
JsonFile.read() → GitHubClient.get_file_content(owner, repo, path, branch)
  ↓
GitHub API → Contenido base64 del archivo
  ↓
Decodificar base64 → string
  ↓
json.loads() → dict
  ↓
Validar con jsonschema (si existe schema)
  ↓
Retornar dict
```

## Relaciones entre Modelos

### Contexto Padre-Hijo

Los modelos mantienen contexto de su padre:

- **Branch → Folder**: Branch pasa su nombre y Meta a Folder
- **Folder → Folder**: Folder pasa su path completo y branch a hijos
- **Folder → JsonFile**: Folder pasa path y branch a JsonFile

**Implementación:**
```python
# En Branch.__init__
nested_instance._parent_branch = self._branch_name
nested_instance._parent_meta = self._meta

# En Folder.__init__
nested_instance._parent_branch = self._parent_branch
nested_instance._parent_path = self._full_path
```

## Extracción de Valores con Regex

### Patrón de Formato

Los formatos usan sintaxis `{variable}` que se convierte en regex:

```
Input: r'config/mops/{tenant}'
Output regex: r'^config/mops/(?P<tenant>[^/]+)$'
```

### Proceso de Conversión

1. Encontrar todas las variables `{nombre}` en el formato
2. Reemplazar cada variable con regex group `(?P<nombre>[^/]+)`
3. Escapar caracteres especiales del formato literal
4. Hacer match contra el string fuente
5. Retornar dict con valores extraídos

## Manejo de Errores

### Validaciones

- **Branch/Folder sin Meta**: Raise `ValueError` si falta owner o repo
- **Token faltante**: Raise `ValueError` si no hay `GITHUB_TOKEN`
- **JSON inválido**: Raise `ValueError` si schema no coincide
- **Archivo no encontrado**: Retornar lista vacía o raise según contexto

### Rate Limiting

- PyGithub maneja rate limiting automáticamente
- Considerar implementar retry logic si es necesario

## Dependencias

### Python Packages

```
PyGithub>=2.1.0      # Cliente oficial de GitHub API
jsonschema>=4.17.0   # Validación de JSON schemas
```

### Variables de Entorno

```
GITHUB_TOKEN         # Token de GitHub con permisos de lectura
```

## Ejemplo de Uso Completo

```python
import github_orm as gorm

class PiperConfigFile(gorm.JsonFile):
    name = "piper_config.json"
    schema = {
        "type": "object",
    }

class PiperIntegrationConfigFolder(gorm.Folder):
    operation = gorm.Folder.Path(
        format=r'configs/mops/{operation}/piper_integration/'
    )
    
    validation_config = PiperConfigFile()

class MopsConfig(gorm.Branch):
    class Meta:
        owner = "myorg"
        repo = "myrepo"
     
    tenant = gorm.Branch.Name(format=r'config/mops/{tenant}')
    piper_integration_config = PiperIntegrationConfigFolder()

# Uso
configs = MopsConfig.objects.all()
config = next(configs)
print(config.tenant)  # Extraído del nombre del branch

piper_configs = config.piper_integration_config.all()
piper_config = next(piper_configs)
print(piper_config.operation)  # Extraído del path

validation_json = piper_config.validation_config.read()
print(validation_json)  # Contenido JSON parseado
```

## Consideraciones de Implementación

### 1. Lazy Loading

- Los datos se cargan bajo demanda
- `.all()` retorna iterator, no lista completa
- `.read()` se ejecuta solo cuando se llama

### 2. Caching (Futuro)

- Considerar cachear resultados de GitHub API
- Implementar TTL para datos que cambian poco

### 3. Extensibilidad

- Fácil agregar nuevos tipos de nodos (ej: TextFile, YAMLFile)
- Campo Field es extensible para nuevos tipos
- Manager puede agregar métodos adicionales

### 4. Testing

- Mockear GitHubClient para tests unitarios
- Tests de integración con repositorio de prueba
- Tests de extracción de regex para campos

## Ventajas del Diseño

1. **Familiar para usuarios de Django**: API similar a Django ORM
2. **Type-safe**: Campos tipados y validación con schema
3. **Flexible**: Fácil agregar nuevos tipos de modelos
4. **Lazy**: Iterator-based para eficiencia de memoria
5. **Claro**: Relaciones explícitas entre modelos

## Próximos Pasos

1. Implementar código base según esta propuesta
2. Agregar tests unitarios y de integración
3. Documentación con ejemplos adicionales
4. Considerar soporte para escritura (create/update/delete)
5. Agregar soporte para paginación de GitHub API
6. Implementar sistema de cache opcional



