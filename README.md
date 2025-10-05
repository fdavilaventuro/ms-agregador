# Microservicio Agregador

## 📋 Descripción

Microservicio agregador que consolida información de tres microservicios especializados (Estudiantes, Cursos e Inscripciones) proporcionando endpoints unificados para el frontend.

## 🏗️ Arquitectura

```
Frontend
    ↓
Microservicio Agregador (Puerto 5000)
    ├──→ MS Estudiantes (Puerto 8080)
    ├──→ MS Cursos (Puerto 8010)
    └──→ MS Inscripciones (Puerto 3000)
```

## 🚀 Características

- **API Gateway**: Fachada única para el frontend
- **Documentación Swagger**: UI interactiva en `/docs`
- **Resiliencia**: Manejo de errores y timeouts
- **Dockerizado**: Fácil despliegue con Docker Compose

## 📊 Endpoints Disponibles

### Dashboard
- `GET /dashboard/estadisticas` - Estadísticas generales del sistema
- `GET /dashboard/resumen-actividad` - Actividad reciente

### Estudiantes
- `GET /estudiantes/{id}/detalles-completos` - Perfil completo con cursos y progreso
- `GET /estudiantes/{id}/cursos-activos` - Cursos en progreso

### Cursos
- `GET /cursos/{id}/informacion-completa` - Detalles completos del curso con estudiantes
- `GET /cursos/populares` - Top 10 cursos más populares

### Inscripciones
- `GET /inscripciones/estadisticas-progreso` - Métricas de progreso general

### Salud del Sistema
- `GET /health` - Health check de todos los microservicios

## 🛠️ Tecnologías

- **Python 3.9**
- **Flask 2.3.3**
- **Flask-RESTX** - Documentación Swagger automática
- **Requests** - Cliente HTTP para consumir APIs
- **Docker** - Contenerización

## 📦 Estructura del Proyecto

```
ms-agregador/
├── Dockerfile
├── requirements.txt
├── app.py
└── README.md
```

## 🚀 Despliegue Rápido

### Prerrequisitos
- Docker
- Docker Compose

### Ejecutar todos los servicios

```bash
# Clonar o crear el proyecto
git clone <repository>
cd proyecto-completo

# Ejecutar todos los microservicios
docker compose up -d --build

# Verificar estado
docker compose ps

# Ver logs del agregador
docker compose logs -f agregador-app
```

### URLs de Acceso

- **Agregador API Docs**: http://localhost:5000/docs
- **MS Estudiantes**: http://localhost:8080
- **MS Cursos**: http://localhost:8010  
- **MS Inscripciones**: http://localhost:3000

## 🔧 Configuración

### Variables de Entorno

```env
MS_ESTUDIANTES=http://estudiantes-app:8080
MS_CURSOS=http://cursos-app:8010
MS_INSCRIPCIONES=http://inscripciones-app:3000
```

### Docker Compose

```yaml
agregador-app:
  build: ./ms-agregador
  ports:
    - "5000:5000"
  environment:
    - MS_INSCRIPCIONES=http://inscripciones-app:3000
    - MS_CURSOS=http://cursos-app:8010
    - MS_ESTUDIANTES=http://estudiantes-app:8080
  networks:
    - app-network
```

## 📋 Dependencias

```txt
flask==2.3.3
requests==2.31.0
flask-restx==1.1.0
werkzeug==2.3.7
```

## 🧪 Testing

### Health Check
```bash
curl http://localhost:5000/health
```

### Ejemplo de Uso
```bash
# Estadísticas del sistema
curl http://localhost:5000/dashboard/estadisticas

# Información de estudiante
curl http://localhost:5000/estudiantes/1/detalles-completos

# Cursos populares
curl http://localhost:5000/cursos/populares
```

## 🔍 Monitoreo y Logs

```bash
# Logs en tiempo real
docker compose logs -f agregador-app

# Logs específicos
docker compose logs agregador-app

# Estado de contenedores
docker compose ps
```

## 🐛 Solución de Problemas

### Error común: Dependencias incompatibles
Si hay conflictos de versiones, verificar `requirements.txt`:
```txt
werkzeug==2.3.7  # Compatible con Flask 2.3.3
```

### Error: Microservicios no disponibles
Verificar que todos los servicios estén corriendo:
```bash
docker compose ps
```

### Recargar cambios
```bash
docker compose restart agregador-app
```

## 📈 Modelos de Datos

El agregador consume y combina los siguientes modelos:

### Estudiante
```json
{
  "id": "uuid",
  "nombres": "string",
  "apellidos": "string", 
  "email": "string",
  "telefono": "string",
  "pais": "string"
}
```

### Curso
```json
{
  "id": "integer",
  "titulo": "string",
  "descripcion": "string",
  "nivel": "string",
  "instructores": "array"
}
```

### Inscripción
```json
{
  "estudianteId": "string",
  "cursoId": "integer",
  "estado": "activa|completada|cancelada",
  "progreso": {
    "porcentaje": "number",
    "leccionesCompletadas": "array[number]"
  }
}
```

## 🤝 Contribución

1. Fork del proyecto
2. Crear feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit de cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Distribuido bajo la Licencia MIT. Ver `LICENSE` para más información.

## 👥 Autores

- **Tu Nombre** - *Desarrollo inicial*

## 📞 Soporte

Si encuentras algún problema, por favor abre un issue en el repositorio del proyecto.
