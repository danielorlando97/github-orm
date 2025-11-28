#!/bin/bash
# Script para ejecutar todos los tests

echo "Ejecutando tests de GitHub ORM..."
echo ""

# Verificar que pytest esté instalado
if ! command -v pytest &> /dev/null; then
    echo "pytest no está instalado. Instalando..."
    pip install pytest pytest-cov
fi

# Ejecutar tests con cobertura
echo "Ejecutando tests con cobertura..."
pytest tests/ -v --cov=github_orm --cov-report=term-missing

echo ""
echo "Tests completados!"





