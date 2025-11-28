# Tests para GitHub ORM

Este directorio contiene la suite completa de tests para la capa de lectura del GitHub ORM.

## Estructura de Tests

- `test_field.py`: Tests para pattern matching de Field
- `test_meta.py`: Tests para la clase Meta y resolución de metadatos
- `test_github_client.py`: Tests para GitHubClient (métodos de lectura)
- `test_github_file.py`: Tests para GitHubFile (lectura de archivos)
- `test_github_model.py`: Tests para GitHubModel
- `test_github_handler_manager.py`: Tests para GitHubHandlerManager (queries e iteración)
- `test_integration.py`: Tests de integración end-to-end

## Ejecutar Tests

### Instalar dependencias de testing

```bash
pip install pytest pytest-cov
```

### Ejecutar todos los tests

```bash
pytest tests/
```

### Ejecutar tests con cobertura

```bash
pytest tests/ --cov=github_orm --cov-report=html
```

### Ejecutar un archivo específico

```bash
pytest tests/test_field.py
```

### Ejecutar un test específico

```bash
pytest tests/test_field.py::TestField::test_match_simple_pattern
```

## Cobertura de Tests

Los tests cubren:

1. **Field Pattern Matching**
   - Creación de Fields con y sin variables
   - Matching de patrones simples y complejos
   - Construcción de paths desde datos
   - Operaciones de concatenación

2. **Meta Class**
   - Creación con strings y Fields
   - Merging de metadatos
   - Resolución desde clases Meta
   - Prioridad en operaciones de suma

3. **GitHubClient**
   - Obtención de repositorios (con paginación)
   - Obtención de branches (con paginación)
   - Obtención de paths y árboles
   - Lectura de contenido de archivos
   - Headers de autenticación

4. **GitHubFile**
   - Inicialización con Meta
   - Lectura de archivos
   - Merging de Meta de clase e instancia
   - Manejo de errores

5. **GitHubModel**
   - Inicialización con propiedades
   - Integración con GitHubFile
   - Manejo de propiedades faltantes
   - Objects manager

6. **GitHubHandlerManager**
   - Iteración con strings simples
   - Iteración con Field patterns
   - Patrones anidados (repo, branch, folder)
   - Combinaciones complejas de patrones

7. **Integración**
   - Flujos completos end-to-end
   - Ejemplos reales de uso
   - Acceso a archivos anidados

## Notas

- Todos los tests usan mocks para evitar llamadas reales a la API de GitHub
- Los tests son determinísticos y no dependen de estado externo
- Los mocks están configurados en `conftest.py` para reutilización





