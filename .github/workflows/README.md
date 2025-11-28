# GitHub Actions Workflows

Este directorio contiene los workflows de GitHub Actions para automatizar CI/CD.

## Workflows Disponibles

### `tests.yml`

Ejecuta la suite completa de tests en múltiples sistemas operativos cuando hay cambios en las ramas principales (`main`, `master`, `develop`) o en Pull Requests hacia estas ramas.

**Características:**
- Ejecuta tests en Ubuntu, macOS y Windows
- Usa Python 3.13
- Genera reportes de cobertura
- Sube cobertura a Codecov (solo en Ubuntu)

**Triggers:**
- Push a `main`, `master`, o `develop`
- Pull Requests hacia `main`, `master`, o `develop`

### `lint.yml`

Ejecuta verificaciones de linting y formato de código.

**Características:**
- Verifica el código con `ruff`
- Verifica el formato con `black`
- Solo se ejecuta en Ubuntu con Python 3.13

**Triggers:**
- Push a `main`, `master`, o `develop`
- Pull Requests hacia `main`, `master`, o `develop`

## Configuración

Los workflows están configurados para:
- Instalar automáticamente las dependencias del proyecto
- Usar cache de pip para acelerar las instalaciones
- Ejecutar tests con cobertura
- Reportar resultados

## Ver Estado de los Workflows

Puedes ver el estado de los workflows en la pestaña "Actions" de tu repositorio en GitHub.





