# Makefile para Sistema de Emisión de Tickets
# Comandos útiles para desarrollo, testing y despliegue

.PHONY: help install install-dev test test-unit test-integration test-advanced test-all test-coverage test-quality test-performance clean docker-build docker-up docker-down docker-logs docker-shell lint format security-check docs run migrate seed

# Variables
PYTHON = python3
PIP = pip3
MANAGE = python manage.py
PYTEST = pytest
COVERAGE = coverage

# Colores para output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Mostrar ayuda con todos los comandos disponibles
	@echo "$(GREEN)Sistema de Emisión de Tickets - Comandos Disponibles$(NC)"
	@echo "=================================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Instalar dependencias de producción
	@echo "$(GREEN)Instalando dependencias de producción...$(NC)"
	$(PIP) install -r requirements.txt

install-dev: ## Instalar dependencias de desarrollo
	@echo "$(GREEN)Instalando dependencias de desarrollo...$(NC)"
	$(PIP) install -r requirements-dev.txt

# =============================================================================
# TESTING
# =============================================================================

test: ## Ejecutar todos los tests (Django)
	@echo "$(GREEN)Ejecutando tests con Django...$(NC)"
	$(MANAGE) test

test-unit: ## Ejecutar solo tests unitarios
	@echo "$(GREEN)Ejecutando tests unitarios...$(NC)"
	$(MANAGE) test accounts.tests catalog.tests sales.tests

test-integration: ## Ejecutar tests de integración
	@echo "$(GREEN)Ejecutando tests de integración...$(NC)"
	$(MANAGE) test tests_integration

test-advanced: ## Ejecutar tests avanzados
	@echo "$(GREEN)Ejecutando tests avanzados...$(NC)"
	$(MANAGE) test sales.tests_advanced

test-all: ## Ejecutar todos los tests con script personalizado
	@echo "$(GREEN)Ejecutando suite completa de tests...$(NC)"
	$(PYTHON) scripts/run_tests.py

test-coverage: ## Ejecutar tests con cobertura
	@echo "$(GREEN)Ejecutando tests con cobertura...$(NC)"
	$(MANAGE) test --with-coverage --cover-package=accounts,catalog,sales

test-pytest: ## Ejecutar tests con pytest
	@echo "$(GREEN)Ejecutando tests con pytest...$(NC)"
	$(PYTEST)

test-pytest-cov: ## Ejecutar tests con pytest y cobertura
	@echo "$(GREEN)Ejecutando tests con pytest y cobertura...$(NC)"
	$(PYTEST) --cov=accounts --cov=catalog --cov=sales --cov-report=html --cov-report=term-missing

test-quality: ## Ejecutar verificaciones de calidad de código
	@echo "$(GREEN)Ejecutando verificaciones de calidad...$(NC)"
	$(PYTHON) scripts/run_tests.py --quality

test-performance: ## Ejecutar tests de rendimiento
	@echo "$(GREEN)Ejecutando tests de rendimiento...$(NC)"
	$(PYTEST) -m performance

test-parallel: ## Ejecutar tests en paralelo
	@echo "$(GREEN)Ejecutando tests en paralelo...$(NC)"
	$(MANAGE) test --parallel

test-verbose: ## Ejecutar tests con output detallado
	@echo "$(GREEN)Ejecutando tests con output detallado...$(NC)"
	$(PYTEST) -v

# =============================================================================
# DOCKER
# =============================================================================

docker-build: ## Construir imagen Docker
	@echo "$(GREEN)Construyendo imagen Docker...$(NC)"
	docker compose build

docker-up: ## Levantar servicios Docker
	@echo "$(GREEN)Levantando servicios Docker...$(NC)"
	docker compose up -d

docker-down: ## Detener servicios Docker
	@echo "$(GREEN)Deteniendo servicios Docker...$(NC)"
	docker compose down

docker-logs: ## Ver logs de Docker
	@echo "$(GREEN)Mostrando logs de Docker...$(NC)"
	docker compose logs -f

docker-shell: ## Acceder al shell del contenedor web
	@echo "$(GREEN)Accediendo al shell del contenedor web...$(NC)"
	docker compose exec web bash

docker-restart: ## Reiniciar servicios Docker
	@echo "$(GREEN)Reiniciando servicios Docker...$(NC)"
	docker compose restart

# =============================================================================
# DESARROLLO
# =============================================================================

run: ## Ejecutar servidor de desarrollo
	@echo "$(GREEN)Ejecutando servidor de desarrollo...$(NC)"
	$(MANAGE) runserver

migrate: ## Aplicar migraciones
	@echo "$(GREEN)Aplicando migraciones...$(NC)"
	$(MANAGE) migrate

makemigrations: ## Crear migraciones
	@echo "$(GREEN)Creando migraciones...$(NC)"
	$(MANAGE) makemigrations

seed: ## Poblar base de datos con datos iniciales
	@echo "$(GREEN)Poblando base de datos...$(NC)"
	$(MANAGE) seed_catalog
	$(MANAGE) create_default_admin

collectstatic: ## Recolectar archivos estáticos
	@echo "$(GREEN)Recolectando archivos estáticos...$(NC)"
	$(MANAGE) collectstatic --noinput

# =============================================================================
# CALIDAD DE CÓDIGO
# =============================================================================

lint: ## Ejecutar linting con flake8
	@echo "$(GREEN)Ejecutando linting...$(NC)"
	flake8 accounts catalog sales --max-line-length=79 --exclude=__pycache__,migrations

format: ## Formatear código con black
	@echo "$(GREEN)Formateando código...$(NC)"
	black accounts catalog sales

format-check: ## Verificar formato sin cambiar
	@echo "$(GREEN)Verificando formato...$(NC)"
	black --check accounts catalog sales

isort: ## Ordenar imports
	@echo "$(GREEN)Ordenando imports...$(NC)"
	isort accounts catalog sales

isort-check: ## Verificar orden de imports sin cambiar
	@echo "$(GREEN)Verificando orden de imports...$(NC)"
	isort --check-only accounts catalog sales

security-check: ## Verificar seguridad del código
	@echo "$(GREEN)Verificando seguridad...$(NC)"
	bandit -r accounts catalog sales
	safety check

# =============================================================================
# DOCUMENTACIÓN
# =============================================================================

docs: ## Generar documentación
	@echo "$(GREEN)Generando documentación...$(NC)"
	@if command -v sphinx-build >/dev/null 2>&1; then \
		sphinx-build -b html docs/source docs/build/html; \
		echo "$(GREEN)Documentación generada en docs/build/html$(NC)"; \
	else \
		echo "$(YELLOW)sphinx-build no está instalado. Instala con: pip install sphinx$(NC)"; \
	fi

docs-serve: ## Servir documentación en localhost:8001
	@echo "$(GREEN)Sirviendo documentación en http://localhost:8001$(NC)"
	@if command -v python >/dev/null 2>&1; then \
		cd docs/build/html && python -m http.server 8001; \
	else \
		echo "$(RED)Python no está disponible$(NC)"; \
	fi

# =============================================================================
# LIMPIEZA
# =============================================================================

clean: ## Limpiar archivos temporales y caché
	@echo "$(GREEN)Limpiando archivos temporales...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.pyd" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -rf test_reports/ 2>/dev/null || true
	rm -rf .coverage 2>/dev/null || true

clean-docker: ## Limpiar contenedores y volúmenes Docker
	@echo "$(GREEN)Limpiando Docker...$(NC)"
	docker compose down -v --remove-orphans
	docker system prune -f

# =============================================================================
# UTILIDADES
# =============================================================================

shell: ## Abrir shell de Django
	@echo "$(GREEN)Abriendo shell de Django...$(NC)"
	$(MANAGE) shell

dbshell: ## Abrir shell de base de datos
	@echo "$(GREEN)Abriendo shell de base de datos...$(NC)"
	$(MANAGE) dbshell

check: ## Verificar configuración del proyecto
	@echo "$(GREEN)Verificando configuración...$(NC)"
	$(MANAGE) check

status: ## Mostrar estado del sistema
	@echo "$(GREEN)Estado del sistema:$(NC)"
	@echo "Docker:"
	@docker compose ps
	@echo ""
	@echo "Base de datos:"
	@$(MANAGE) showmigrations

# =============================================================================
# DESPLIEGUE
# =============================================================================

deploy: ## Desplegar sistema completo
	@echo "$(GREEN)Desplegando sistema...$(NC)"
	@make docker-build
	@make docker-up
	@echo "$(GREEN)Sistema desplegado en http://localhost:8000$(NC)"

deploy-test: ## Desplegar y ejecutar tests
	@echo "$(GREEN)Desplegando y ejecutando tests...$(NC)"
	@make deploy
	@sleep 10
	@make test-all

# =============================================================================
# MONITOREO
# =============================================================================

logs: ## Ver logs en tiempo real
	@echo "$(GREEN)Mostrando logs...$(NC)"
	docker compose logs -f web

logs-db: ## Ver logs de base de datos
	@echo "$(GREEN)Mostrando logs de base de datos...$(NC)"
	docker compose logs -f db

monitor: ## Monitorear recursos del sistema
	@echo "$(GREEN)Monitoreando recursos...$(NC)"
	@echo "Contenedores:"
	@docker stats --no-stream
	@echo ""
	@echo "Volúmenes:"
	@docker volume ls
	@echo ""
	@echo "Redes:"
	@docker network ls

# =============================================================================
# BACKUP Y RESTAURACIÓN
# =============================================================================

backup: ## Crear backup de la base de datos
	@echo "$(GREEN)Creando backup de la base de datos...$(NC)"
	@mkdir -p backups
	docker compose exec -T db pg_dump -U tickets tickets > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql

restore: ## Restaurar backup (especificar archivo con BACKUP_FILE=archivo.sql)
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "$(RED)Especifica el archivo de backup: make restore BACKUP_FILE=archivo.sql$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Restaurando backup: $(BACKUP_FILE)$(NC)"
	docker compose exec -T db psql -U tickets tickets < backups/$(BACKUP_FILE)

# =============================================================================
# DESARROLLO RÁPIDO
# =============================================================================

dev: ## Modo desarrollo completo (instalar, migrar, ejecutar)
	@echo "$(GREEN)Configurando entorno de desarrollo...$(NC)"
	@make install-dev
	@make migrate
	@make seed
	@make run

quick-test: ## Ejecutar tests rápidos
	@echo "$(GREEN)Ejecutando tests rápidos...$(NC)"
	@make test-unit
	@make test-integration

full-test: ## Ejecutar suite completa de tests
	@echo "$(GREEN)Ejecutando suite completa...$(NC)"
	@make test-all
	@make test-quality
	@make test-performance

# =============================================================================
# AYUDA ESPECÍFICA
# =============================================================================

help-testing: ## Mostrar ayuda específica de testing
	@echo "$(GREEN)Comandos de Testing Disponibles:$(NC)"
	@echo "  test              - Ejecutar todos los tests (Django)"
	@echo "  test-unit         - Solo tests unitarios"
	@echo "  test-integration  - Tests de integración"
	@echo "  test-advanced     - Tests avanzados"
	@echo "  test-all          - Suite completa con script personalizado"
	@echo "  test-coverage     - Tests con cobertura (Django)"
	@echo "  test-pytest       - Tests con pytest"
	@echo "  test-pytest-cov   - Tests con pytest y cobertura"
	@echo "  test-quality      - Verificaciones de calidad"
	@echo "  test-performance  - Tests de rendimiento"
	@echo "  test-parallel     - Tests en paralelo"
	@echo "  test-verbose      - Tests con output detallado"

help-docker: ## Mostrar ayuda específica de Docker
	@echo "$(GREEN)Comandos de Docker Disponibles:$(NC)"
	@echo "  docker-build      - Construir imagen"
	@echo "  docker-up         - Levantar servicios"
	@echo "  docker-down       - Detener servicios"
	@echo "  docker-logs       - Ver logs"
	@echo "  docker-shell      - Acceder al shell"
	@echo "  docker-restart    - Reiniciar servicios"

help-quality: ## Mostrar ayuda específica de calidad
	@echo "$(GREEN)Comandos de Calidad Disponibles:$(NC)"
	@echo "  lint              - Linting con flake8"
	@echo "  format            - Formatear con black"
	@echo "  format-check      - Verificar formato"
	@echo "  isort             - Ordenar imports"
	@echo "  isort-check       - Verificar imports"
	@echo "  security-check    - Verificar seguridad"

# =============================================================================
# COMANDOS COMPUESTOS
# =============================================================================

setup: install install-dev migrate seed ## Configuración inicial completa
	@echo "$(GREEN)Configuración inicial completada$(NC)"

test-suite: test-quality test-all test-performance ## Ejecutar suite completa de testing
	@echo "$(GREEN)Suite de testing completada$(NC)"

quality-suite: lint format-check isort-check security-check ## Ejecutar suite de calidad
	@echo "$(GREEN)Suite de calidad completada$(NC)"

dev-reset: clean docker-down docker-build docker-up migrate seed ## Reset completo del entorno de desarrollo
	@echo "$(GREEN)Entorno de desarrollo reseteado$(NC)"

# =============================================================================
# INFORMACIÓN DEL SISTEMA
# =============================================================================

info: ## Mostrar información del sistema
	@echo "$(GREEN)Información del Sistema:$(NC)"
	@echo "Python: $(shell python --version 2>/dev/null || echo 'No disponible')"
	@echo "Django: $(shell python -c 'import django; print(django.get_version())' 2>/dev/null || echo 'No disponible')"
	@echo "Docker: $(shell docker --version 2>/dev/null || echo 'No disponible')"
	@echo "Docker Compose: $(shell docker compose version 2>/dev/null || echo 'No disponible')"
	@echo "Pytest: $(shell pytest --version 2>/dev/null || echo 'No disponible')"
	@echo "Coverage: $(shell coverage --version 2>/dev/null || echo 'No disponible')"

version: ## Mostrar versiones de dependencias
	@echo "$(GREEN)Versiones de Dependencias:$(NC)"
	@$(PIP) list | grep -E "(Django|djangorestframework|psycopg2|pytest|coverage)"

# =============================================================================
# COMANDOS DE EMERGENCIA
# =============================================================================

emergency-stop: ## Detener todo el sistema de emergencia
	@echo "$(RED)⚠️  DETENIENDO SISTEMA DE EMERGENCIA ⚠️$(NC)"
	@docker compose down --remove-orphans
	@docker system prune -f
	@echo "$(GREEN)Sistema detenido de emergencia$(NC)"

emergency-reset: ## Reset completo de emergencia
	@echo "$(RED)⚠️  RESET COMPLETO DE EMERGENCIA ⚠️$(NC)"
	@make emergency-stop
	@make clean
	@make clean-docker
	@echo "$(GREEN)Reset de emergencia completado$(NC)"

# =============================================================================
# COMANDO POR DEFECTO
# =============================================================================

.DEFAULT_GOAL := help
