# 🎟️ Sistema de Emisión y Gestión de Tickets

Plataforma para gestionar catálogos (zonas, tipos de sorteo, horarios y límites), emisión de tickets y validaciones de negocio, con API basada en Django REST Framework.

## 📋 Índice
- Requisitos
- Instalación
- Ejecución
- Configuración
- Migraciones
- API
- Testing
- Calidad de Código
- CI/CD
- Troubleshooting
- Contribución

## ✅ Requisitos
- Python 3.12
- Docker y Docker Compose (opcional, recomendado)

## ⚙️ Instalación
1. Clona el repositorio y entra al directorio del proyecto.
2. (Opcional) Crea un entorno virtual local:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   ```
3. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

## 🚀 Ejecución
### Opción A: Docker (recomendada)
```bash
docker compose up -d --build
```
Aplicación disponible en `http://localhost:8000`.

### Opción B: Local
```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## 🛠️ Configuración
Variables de entorno comunes:
- `DJANGO_SETTINGS_MODULE=core.settings`
- `SECRET_KEY=...`
- `DEBUG=true|false`
- `DATABASE_URL=...` (si aplica)

## 🗃️ Migraciones
Generar y aplicar migraciones:
```bash
python manage.py makemigrations
python manage.py migrate
```

## 🔌 API
- API REST con Django REST Framework.
- Endpoints principales (routers):
  - `zones/`
  - `draw-types/`
  - `draw-schedules/`
  - `number-limits/`
- Autenticación JWT (SimpleJWT).
- Permisos: escritura restringida a `ADMIN`/`staff`/`superuser`.

## 🧪 Testing
Suite que valida modelos, serializers, viewsets, permisos y flujos de integración.

## ⚡ Comandos rápidos
- Iniciar app (Docker): `docker compose up -d --build`
- Migraciones: `python manage.py makemigrations && python manage.py migrate`
- Tests rápidos: `python manage.py test -v 2`
- Tests por módulo: `python manage.py test catalog.tests -v 2`
- Lint+formato: `flake8 && black . && isort .`
- Borrar caché Python: `find . -type d -name "__pycache__" -exec rm -r {} +`

### Ejecutar todos los tests
```bash
python manage.py test -v 2
```

### Ejecutar por módulo/archivo
```bash
python manage.py test accounts.tests -v 2
python manage.py test catalog.tests -v 2
python manage.py test sales.tests -v 2
python manage.py test sales.tests_advanced -v 2
python manage.py test tests_integration -v 2
python manage.py test test_simple -v 2
```

### Ejecutar por clase/test específico
```bash
python manage.py test catalog.tests.ZoneViewSetTests -v 2
python manage.py test catalog.tests.ZoneViewSetTests.test_update_zone -v 2
```

### Pytest (opcional)
```bash
pytest
# Con cobertura
pytest --cov=accounts --cov=catalog --cov=sales --cov-report=term-missing
```

## 🧹 Calidad de Código
```bash
flake8 accounts catalog sales --max-line-length=88
black accounts catalog sales
isort accounts catalog sales
bandit -r accounts catalog sales
```

## 🔄 CI/CD (ejemplo GitHub Actions)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: python manage.py test -v 2
```

## 🐛 Troubleshooting
- Usa siempre `manage.py test` para cargar `DJANGO_SETTINGS_MODULE` y evitar errores tipo:
  `ImproperlyConfigured: Requested setting REST_FRAMEWORK ...`.
- Si hay inconsistencias en la BD de tests, el runner recrea la DB automáticamente.
- Limpia caché de Python si ves comportamientos extraños:
  ```bash
  find . -type d -name "__pycache__" -exec rm -r {} +
  ```

## ❓ FAQ
- ¿Cómo evito el error de settings en tests?  
  Ejecuta siempre con `python manage.py test ...` (no ejecutes archivos de test directamente).
- ¿Por qué recibo 403 en endpoints de catálogo?  
  Acciones de escritura requieren `ADMIN`/`staff`/`superuser`. Asegúrate de enviar un JWT válido.
- ¿Cómo ejecuto un solo test?  
  `python manage.py test catalog.tests.ZoneViewSetTests.test_update_zone -v 2`
- ¿Cómo creo datos mínimos?  
  Usa los endpoints `zones/`, `draw-types/` y luego `draw-schedules/` para horarios.

## 🤝 Contribución
- Agrega tests para toda nueva funcionalidad.
- Mantén cobertura ≥80%.
- Sigue el estilo (black, isort, flake8).
- Ejecuta la suite completa antes de enviar PR.
