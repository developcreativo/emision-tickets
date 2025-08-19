# 🧪 Suite de Testing del Sistema de Emisión de Tickets

Esta documentación describe la suite completa de testing implementada para el sistema de emisión y gestión de tickets.

## 📋 Índice

- [Descripción General](#descripción-general)
- [Estructura de Tests](#estructura-de-tests)
- [Configuración](#configuración)
- [Ejecución de Tests](#ejecución-de-tests)
- [Tipos de Tests](#tipos-de-tests)
- [Reportes](#reportes)
- [Herramientas de Calidad](#herramientas-de-calidad)
- [CI/CD](#cicd)

## 🎯 Descripción General

La suite de testing está diseñada para garantizar la **robustez**, **escalabilidad** y **confiabilidad** del sistema de emisión de tickets. Incluye:

- ✅ **Tests Unitarios**: Validación de modelos, serializers y lógica de negocio
- ✅ **Tests de Integración**: Flujos completos del sistema
- ✅ **Tests de Rendimiento**: Validación de escalabilidad
- ✅ **Tests de Seguridad**: Verificación de permisos y roles
- ✅ **Cobertura de Código**: Mínimo 80% de cobertura
- ✅ **Análisis de Calidad**: Linting, formateo y seguridad

## 🏗️ Estructura de Tests

```
emision-tickets/
├── accounts/
│   ├── tests.py                 # Tests unitarios de usuarios
│   └── models.py
├── catalog/
│   ├── tests.py                 # Tests unitarios de catálogos
│   └── models.py
├── sales/
│   ├── tests.py                 # Tests básicos de ventas
│   ├── tests_advanced.py        # Tests avanzados de reglas de negocio
│   └── models.py
├── tests_integration.py         # Tests de integración del sistema
├── pytest.ini                  # Configuración de pytest
├── requirements-dev.txt         # Dependencias de desarrollo
└── scripts/
    └── run_tests.py            # Script principal de ejecución
```

## ⚙️ Configuración

### 1. Instalar Dependencias de Desarrollo

```bash
pip install -r requirements-dev.txt
```

### 2. Configuración de Base de Datos para Tests

El sistema usa automáticamente una base de datos SQLite en memoria para los tests, configurada en `core/settings.py`.

### 3. Variables de Entorno

```bash
export DJANGO_SETTINGS_MODULE=core.settings
export PYTHONPATH=/path/to/emision-tickets
```

## 🚀 Ejecución de Tests

### Opción 1: Script Principal (Recomendado)

```bash
# Ejecutar todos los tests
python scripts/run_tests.py

# Ejecutar solo tests unitarios
python scripts/run_tests.py --type unit

# Ejecutar tests de integración
python scripts/run_tests.py --type integration

# Ejecutar tests avanzados
python scripts/run_tests.py --type advanced

# Con reporte HTML y cobertura
python scripts/run_tests.py --html-report --quality

# Tests en paralelo
python scripts/run_tests.py --parallel
```

### Opción 2: Django Test Runner

```bash
# Tests básicos
python manage.py test

# Con cobertura
python manage.py test --with-coverage --cover-package=accounts,catalog,sales

# Tests específicos
python manage.py test accounts.tests
python manage.py test catalog.tests
python manage.py test sales.tests
python manage.py test sales.tests_advanced
python manage.py test tests_integration

# Tests en paralelo
python manage.py test --parallel
```

### Opción 3: Pytest

```bash
# Todos los tests
pytest

# Tests específicos por marcadores
pytest -m unit
pytest -m integration
pytest -m performance
pytest -m security

# Con cobertura
pytest --cov=accounts --cov=catalog --cov=sales --cov-report=html

# Tests en paralelo
pytest -n auto
```

## 🧩 Tipos de Tests

### 1. Tests Unitarios (`accounts/tests.py`)

**Propósito**: Validar funcionalidad individual de componentes

**Cobertura**:
- ✅ Modelos de Usuario
- ✅ Serializers
- ✅ ViewSets
- ✅ Autenticación JWT
- ✅ Permisos y Roles
- ✅ Validaciones

**Ejemplos**:
```python
class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.role, 'VENDEDOR')

class AuthenticationTests(TestCase):
    def test_token_obtain(self):
        response = self.client.post('/api/auth/token/', credentials)
        self.assertEqual(response.status_code, 200)
```

### 2. Tests de Catálogo (`catalog/tests.py`)

**Propósito**: Validar gestión de zonas, tipos de sorteo y configuraciones

**Cobertura**:
- ✅ Modelos de Catálogo
- ✅ Serializers
- ✅ ViewSets
- ✅ Restricciones de Unicidad
- ✅ Permisos de Acceso

### 3. Tests de Ventas (`sales/tests.py`, `sales/tests_advanced.py`)

**Propósito**: Validar lógica de negocio y reglas de tickets

**Cobertura**:
- ✅ Creación de Tickets
- ✅ Validación de Reglas
- ✅ Límites Acumulados
- ✅ Horarios de Cierre
- ✅ Generación de Reportes
- ✅ Exportación (CSV/Excel)
- ✅ Generación de PDF

**Tests Avanzados**:
```python
class AdvancedTicketRulesTests(TestCase):
    def test_ticket_with_multiple_numbers(self):
        # Test tickets con múltiples números
        
    def test_accumulated_limit_across_multiple_tickets(self):
        # Test límites acumulados
        
    def test_cutoff_time_exact_match(self):
        # Test horarios de cierre exactos
```

### 4. Tests de Integración (`tests_integration.py`)

**Propósito**: Validar flujos completos del sistema

**Cobertura**:
- ✅ Flujo Completo Admin
- ✅ Flujo Completo Vendedor
- ✅ Gestión de Permisos
- ✅ Reglas de Negocio Integradas
- ✅ Consistencia de Datos
- ✅ Manejo de Errores
- ✅ Escenarios de Rendimiento
- ✅ Acceso Concurrente

**Ejemplo de Flujo Completo**:
```python
def test_complete_system_workflow_admin(self):
    # 1. Gestionar catálogos
    # 2. Crear tickets como vendedor
    # 3. Generar reportes
    # 4. Exportar reportes
    # 5. Generar PDF
```

## 📊 Reportes

### 1. Cobertura de Código

```bash
# Generar reporte HTML
coverage html --directory=test_reports/coverage

# Ver en navegador
open test_reports/coverage/index.html
```

**Métricas Objetivo**:
- 📈 **Cobertura Total**: ≥80%
- 📈 **Cobertura Crítica**: ≥90%
- 📈 **Cobertura de Reglas de Negocio**: 100%

### 2. Reporte HTML de Tests

```bash
pytest --html=test_reports/report.html --self-contained-html
```

### 3. Reporte de Cobertura en Terminal

```bash
pytest --cov=accounts --cov=catalog --cov=sales --cov-report=term-missing
```

## 🔍 Herramientas de Calidad

### 1. Linting y Formateo

```bash
# Flake8 - Estilo de código
flake8 accounts catalog sales --max-line-length=79

# Black - Formateo automático
black accounts catalog sales

# Isort - Orden de imports
isort accounts catalog sales
```

### 2. Análisis de Seguridad

```bash
# Bandit - Análisis de seguridad
bandit -r accounts catalog sales

# Safety - Verificación de dependencias
safety check
```

### 3. Verificación de Tipos

```bash
# MyPy - Verificación de tipos
mypy accounts catalog sales
```

## 🚀 CI/CD

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: python scripts/run_tests.py --quality --html-report
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### GitLab CI

```yaml
test:
  stage: test
  image: python:3.12
  script:
    - pip install -r requirements.txt
    - pip install -r requirements-dev.txt
    - python scripts/run_tests.py --quality
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

## 📈 Métricas de Calidad

### Objetivos de Cobertura

| Módulo | Cobertura Objetivo | Cobertura Actual |
|--------|-------------------|------------------|
| **accounts** | ≥90% | 🔄 |
| **catalog** | ≥85% | 🔄 |
| **sales** | ≥85% | 🔄 |
| **Total** | ≥80% | 🔄 |

### Objetivos de Rendimiento

| Métrica | Objetivo | Actual |
|---------|----------|---------|
| **Tests Unitarios** | <1s | 🔄 |
| **Tests de Integración** | <5s | 🔄 |
| **Generación de Reportes** | <2s | 🔄 |
| **Creación de Tickets** | <100ms | 🔄 |

## 🐛 Troubleshooting

### Problemas Comunes

1. **Base de Datos de Tests**
   ```bash
   # Limpiar base de datos de tests
   python manage.py flush --settings=core.settings
   ```

2. **Caché de Tests**
   ```bash
   # Limpiar caché de Python
   find . -type d -name "__pycache__" -exec rm -r {} +
   ```

3. **Permisos de Archivos**
   ```bash
   # Hacer ejecutable el script
   chmod +x scripts/run_tests.py
   ```

### Logs y Debugging

```bash
# Tests con output detallado
python scripts/run_tests.py --verbose

# Tests con debugger
python -m pdb -m pytest tests_integration.py::SystemIntegrationTests::test_complete_system_workflow_admin
```

## 📚 Recursos Adicionales

- [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Django REST Framework Testing](https://www.django-rest-framework.org/api-guide/testing/)

## 🤝 Contribución

Para contribuir a la suite de tests:

1. **Escribir tests para nueva funcionalidad**
2. **Mantener cobertura ≥80%**
3. **Seguir convenciones de nomenclatura**
4. **Documentar tests complejos**
5. **Ejecutar suite completa antes de PR**

---

**🎯 Objetivo**: Garantizar un sistema robusto, escalable y confiable a través de testing exhaustivo y automatizado.
