#!/bin/bash

# Script para desarrollo dentro del contenedor Docker
# Este script se ejecuta DENTRO del contenedor del backend

set -e

FRONTEND_DIR="/frontend"
BACKEND_PORT=8000
FRONTEND_PORT=3000

echo "🐳 Desarrollo dentro del contenedor Docker..."

# Función para mostrar ayuda
show_help() {
    echo "Uso: ./scripts/dev-container.sh [opción]"
    echo ""
    echo "Este script se ejecuta DENTRO del contenedor Docker"
    echo ""
    echo "Opciones:"
    echo "  backend     - Solo backend Django"
    echo "  frontend    - Solo frontend Vue.js (si está montado)"
    echo "  fullstack   - Backend + Frontend (por defecto)"
    echo "  install     - Instalar dependencias del frontend"
    echo "  build       - Construir frontend para producción"
    echo "  test        - Ejecutar tests de backend"
    echo "  help        - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  ./scripts/dev-container.sh              # Iniciar fullstack"
    echo "  ./scripts/dev-container.sh backend      # Solo backend"
    echo "  ./scripts/dev-container.sh frontend     # Solo frontend"
    echo "  ./scripts/dev-container.sh install      # Instalar dependencias"
}

# Función para verificar si el frontend está montado
check_frontend() {
    if [ ! -d "$FRONTEND_DIR" ]; then
        echo "❌ Error: No se encontró el directorio frontend en $FRONTEND_DIR"
        echo "💡 Asegúrate de que el volumen esté montado en docker-compose"
        echo "   Ejemplo: - ../tickets-admin-frontend:/frontend"
        exit 1
    fi
}

# Función para instalar dependencias del frontend
install_frontend() {
    echo "📦 Instalando dependencias del frontend..."
    check_frontend
    cd "$FRONTEND_DIR"
    npm install
    cd - > /dev/null
    echo "✅ Dependencias del frontend instaladas"
}

# Función para ejecutar solo backend
run_backend() {
    echo "🐍 Iniciando backend Django en puerto $BACKEND_PORT..."
    python manage.py migrate
    python manage.py runserver 0.0.0.0:$BACKEND_PORT
}

# Función para ejecutar solo frontend
run_frontend() {
    echo "📱 Iniciando frontend Vue.js en puerto $FRONTEND_PORT..."
    check_frontend
    cd "$FRONTEND_DIR"
    npm run dev -- --host 0.0.0.0 --port $FRONTEND_PORT
}

# Función para ejecutar fullstack
run_fullstack() {
    echo "🚀 Iniciando desarrollo fullstack dentro del contenedor..."
    echo "   Backend:  http://localhost:$BACKEND_PORT"
    echo "   Frontend: http://localhost:$FRONTEND_PORT"
    echo "   API Docs: http://localhost:$BACKEND_PORT/api/docs/"
    echo ""
    
    # Ejecutar backend en background
    echo "🐍 Iniciando backend..."
    python manage.py migrate
    python manage.py runserver 0.0.0.0:$BACKEND_PORT &
    BACKEND_PID=$!
    
    # Esperar un poco para que el backend inicie
    sleep 3
    
    # Verificar si el frontend está disponible
    if [ -d "$FRONTEND_DIR" ]; then
        echo "📱 Iniciando frontend..."
        cd "$FRONTEND_DIR"
        npm run dev -- --host 0.0.0.0 --port $FRONTEND_PORT &
        FRONTEND_PID=$!
        cd - > /dev/null
        echo "✅ Servicios iniciados (PIDs: Backend=$BACKEND_PID, Frontend=$FRONTEND_PID)"
    else
        echo "⚠️  Frontend no disponible (no montado en /frontend)"
        echo "✅ Solo backend iniciado (PID: $BACKEND_PID)"
    fi
    
    echo "💡 Presiona Ctrl+C para detener los servicios"
    
    # Esperar a que se detengan
    wait
}

# Función para construir frontend
build_frontend() {
    echo "🔨 Construyendo frontend para producción..."
    check_frontend
    cd "$FRONTEND_DIR"
    npm run build
    cd - > /dev/null
    echo "✅ Frontend construido en $FRONTEND_DIR/dist/"
}

# Función para ejecutar tests
run_tests() {
    echo "🧪 Ejecutando tests del backend..."
    python manage.py test -v 2
}

# Procesar argumentos
case "${1:-fullstack}" in
    "backend")
        run_backend
        ;;
    "frontend")
        run_frontend
        ;;
    "fullstack")
        run_fullstack
        ;;
    "install")
        install_frontend
        ;;
    "build")
        build_frontend
        ;;
    "test")
        run_tests
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "❌ Opción desconocida: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
