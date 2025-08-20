#!/bin/bash

# Script para mover el frontend a un repositorio separado
# Uso: ./scripts/move_frontend.sh [ruta_destino]

FRONTEND_SOURCE="./frontend"
DEFAULT_DESTINATION="../tickets-admin-frontend"

# Verificar si se proporcionó una ruta de destino
if [ $# -eq 0 ]; then
    DESTINATION=$DEFAULT_DESTINATION
else
    DESTINATION=$1
fi

echo "🚀 Moviendo frontend a repositorio separado..."
echo "📁 Origen: $FRONTEND_SOURCE"
echo "📁 Destino: $DESTINATION"

# Verificar que existe el directorio frontend
if [ ! -d "$FRONTEND_SOURCE" ]; then
    echo "❌ Error: No se encontró el directorio frontend en $FRONTEND_SOURCE"
    exit 1
fi

# Crear directorio de destino si no existe
if [ ! -d "$DESTINATION" ]; then
    echo "📂 Creando directorio de destino..."
    mkdir -p "$DESTINATION"
fi

# Copiar archivos del frontend
echo "📋 Copiando archivos..."
cp -r "$FRONTEND_SOURCE"/* "$DESTINATION/"

# Crear README.md para el frontend
cat > "$DESTINATION/README.md" << 'EOF'
# 🎟️ Tickets Admin Frontend

Dashboard de administración para el sistema de emisión de tickets construido con Vue.js 3.

## 🚀 Características

- **Vue.js 3** con Composition API
- **Tailwind CSS** para estilos
- **Pinia** para gestión de estado
- **Vue Router** para navegación
- **Chart.js** para gráficos
- **Axios** para peticiones HTTP
- **Heroicons** para iconografía

## 📋 Requisitos

- Node.js 18+
- npm o yarn

## ⚙️ Instalación

```bash
# Instalar dependencias
npm install

# Ejecutar en modo desarrollo
npm run dev

# Construir para producción
npm run build

# Vista previa de producción
npm run preview
```

## 🔧 Configuración

El frontend está configurado para conectarse al backend en `http://localhost:8000`.

### Variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
VITE_API_URL=http://localhost:8000
VITE_APP_TITLE=Tickets Admin
```

## 📁 Estructura del Proyecto

```
src/
├── components/          # Componentes reutilizables
│   └── layout/         # Componentes de layout
├── views/              # Vistas de la aplicación
├── stores/             # Stores de Pinia
├── router/             # Configuración de rutas
├── assets/             # Recursos estáticos
├── style.css           # Estilos globales
└── main.js             # Punto de entrada
```

## 🎨 Componentes Principales

- **AdminLayout**: Layout principal con sidebar y header
- **DashboardView**: Vista principal con estadísticas y gráficos
- **LoginView**: Formulario de autenticación
- **CatalogView**: Gestión de catálogos (zonas, tipos de sorteo)
- **UsersView**: Gestión de usuarios
- **ReportsView**: Reportes y análisis

## 🔐 Autenticación

El sistema usa JWT tokens para autenticación:

- Los tokens se almacenan en localStorage
- Refresh automático de tokens
- Protección de rutas con guardias

## 📱 Responsive Design

El dashboard es completamente responsive y funciona en:
- Desktop (1024px+)
- Tablet (768px - 1023px)
- Mobile (< 768px)

## 🧪 Testing

```bash
# Ejecutar tests
npm run test

# Tests con cobertura
npm run test:coverage

# Tests E2E
npm run test:e2e
```

## 🚀 Deployment

### Build para producción

```bash
npm run build
```

Los archivos se generan en `dist/` y pueden ser servidos por cualquier servidor web estático.

### Docker

```bash
# Construir imagen
docker build -t tickets-admin-frontend .

# Ejecutar contenedor
docker run -p 3000:80 tickets-admin-frontend
```

## 🔗 Integración con Backend

El frontend se conecta al backend Django a través de la API REST:

- **Autenticación**: `/api/auth/`
- **Catálogos**: `/api/catalog/`
- **Ventas**: `/api/sales/`
- **Usuarios**: `/api/auth/users/`

## 📈 Roadmap

### Fase 1 ✅
- [x] Dashboard principal
- [x] Autenticación
- [x] Layout responsive
- [x] Gráficos básicos

### Fase 2 🚧
- [ ] Gestión completa de catálogos
- [ ] Reportes avanzados
- [ ] Exportación de datos
- [ ] Notificaciones en tiempo real

### Fase 3 📋
- [ ] PWA para vendedores
- [ ] Componentes reutilizables
- [ ] Tests E2E
- [ ] Optimización de rendimiento

## 🤝 Contribución

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para más detalles.

---

Desarrollado con ❤️ para el sistema de emisión de tickets.
EOF

# Crear .gitignore para el frontend
cat > "$DESTINATION/.gitignore" << 'EOF'
# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

# Dependencies
node_modules
.pnp
.pnp.js

# Build outputs
dist
dist-ssr
*.local

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Testing
coverage
.nyc_output

# Cache
.cache
.parcel-cache

# Temporary files
*.tmp
*.temp
EOF

# Crear Dockerfile para el frontend
cat > "$DESTINATION/Dockerfile" << 'EOF'
# Build stage
FROM node:18-alpine as build-stage

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build for production
RUN npm run build

# Production stage
FROM nginx:alpine as production-stage

# Copy built files
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
EOF

# Crear nginx.conf
cat > "$DESTINATION/nginx.conf" << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;

        # Gzip compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

        # Handle Vue Router history mode
        location / {
            try_files $uri $uri/ /index.html;
        }

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
EOF

# Crear docker-compose.yml para desarrollo
cat > "$DESTINATION/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  frontend:
    build: .
    ports:
      - "3000:80"
    environment:
      - NODE_ENV=production
    depends_on:
      - backend

  backend:
    image: tickets-backend:latest
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - DATABASE_URL=postgresql://user:password@db:5432/tickets
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=tickets
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
EOF

echo "✅ Frontend movido exitosamente a $DESTINATION"
echo ""
echo "📋 Próximos pasos:"
echo "1. cd $DESTINATION"
echo "2. git init"
echo "3. git add ."
echo "4. git commit -m 'Initial commit: Dashboard de administración'"
echo "5. Crear repositorio en GitHub/GitLab"
echo "6. git remote add origin <url-del-repositorio>"
echo "7. git push -u origin main"
echo ""
echo "🔧 Para desarrollo:"
echo "cd $DESTINATION && npm install && npm run dev"
