# github-orm

ORM basado en GitHub para mapear estructuras de repositorios GitHub (branches, folders, files) como modelos Python.

## Estado del Proyecto

![Tests](https://github.com/danielorlando97/github-orm/workflows/Tests/badge.svg)
![Lint](https://github.com/danielorlando97/github-orm/workflows/Lint/badge.svg)

## Tests

El proyecto incluye una suite completa de tests para la capa de lectura. Los tests se ejecutan automáticamente en GitHub Actions ante cualquier actualización de las ramas principales (`main`, `master`, `develop`).

### Ejecutar tests localmente

```bash
# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Ejecutar todos los tests
pytest tests/

# Con cobertura
pytest tests/ --cov=github_orm --cov-report=html
```

Ver [tests/README.md](tests/README.md) para más información sobre los tests.