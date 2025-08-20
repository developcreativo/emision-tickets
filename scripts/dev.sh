#!/bin/bash

# Script para desarrollo con frontend y backend juntos
# Uso: ./scripts/dev.sh [opción]

set -e

FRONTEND_DIR="../tickets-admin-frontend"
BACKEND_PORT=8000
FRONTEND_PORT=3000

echo "🚀 Iniciando desarrollo fullstack..."

# Función para mostrar ayuda
show_help() {
    echo "Uso: ./scripts/dev.sh [opción]"
    echo ""
    echo "Opciones:"
    echo "  backend     - Solo backend Django"
    echo "  frontend    - Solo frontend Vue.js"
    echo "  fullstack   - Backend + Frontend (por defecto)"
    echo "  install     - Instalar dependencias de ambos"
    echo "  build       - Construir frontend para producción"
    echo "  test        - Ejecutar tests de backend"
    echo "  help        - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  ./scripts/dev.sh              # Iniciar fullstack"
    echo "  ./scripts/dev.sh backend      # Solo backend"
    echo "  ./scripts/dev.sh frontend     # Solo frontend"
    echo "  ./scripts/dev.sh install      # Instalar dependencias"
}

# Función para verificar si el frontend existe
check_frontend() {
    if [ ! -d "$FRONTEND_DIR" ]; then
        echo "❌ Error: No se encontró el directorio frontend en $FRONTEND_DIR"
        echo "💡 Ejecuta primero: ./scripts/move_frontend.sh"
        exit 1
    fi
}

# Función para instalar dependencias
install_dependencies() {
    echo "📦 Instalando dependencias..."
    
    # Backend
    echo "🐍 Instalando dependencias de Python..."
    pip install -r requirements-dev.txt
    
    # Frontend
    echo "📱 Instalando dependencias de Node.js..."
    check_frontend
    cd "$FRONTEND_DIR"
    npm install
    cd - > /dev/null
    
    echo "✅ Dependencias instaladas correctamente"
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
    echo "🚀 Iniciando desarrollo fullstack..."
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
    
    # Ejecutar frontend
    echo "📱 Iniciando frontend..."
    check_frontend
    cd "$FRONTEND_DIR"
    npm run dev -- --host 0.0.0.0 --port $FRONTEND_PORT &
    FRONTEND_PID=$!
    cd - > /dev/null
    
    echo "✅ Servicios iniciados (PIDs: Backend=$BACKEND_PID, Frontend=$FRONTEND_PID)"
    echo "💡 Presiona Ctrl+C para detener ambos servicios"
    
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
        install_dependencies
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
