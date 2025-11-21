# 🛒 Marketplace Reviews Scraper

Aplicación para extraer automáticamente reseñas de productos de marketplace (Mercado Libre, Amazon, etc.) y almacenarlas en Google Drive como archivos JSON.

## 📋 Características

- ✅ Extracción de reseñas de múltiples marketplaces
- ✅ Integración con Google Sheets y Google Drive
- ✅ API REST para automatización con n8n
- ✅ Procesamiento en background
- ✅ Optimizado para Raspberry Pi 5 (ARM64)
- ✅ Gestión con Docker y Portainer
- ✅ Actualización automática de planilla con nombres de archivos

## 🏗️ Arquitectura

```
marketplace-reviews-scraper/
├── app/
│   ├── main.py                    # API FastAPI principal
│   ├── scraper.py                 # Lógica de scraping
│   ├── google_drive_handler.py   # Manejo de Google Drive/Sheets
│   └── __init__.py
├── config/                        # Archivos de configuración
├── credentials/                   # Credenciales de Google (no versionado)
├── logs/                         # Logs de la aplicación
├── Dockerfile                    # Imagen Docker ARM64
├── docker-compose.yml           # Orquestación Docker
├── requirements.txt             # Dependencias Python
└── README.md                    # Este archivo
```

## 🚀 Instalación

### Prerequisitos

1. **Raspberry Pi 5** con Raspberry Pi OS (64-bit)
2. **Docker** y **Docker Compose** instalados
3. **Portainer** (opcional, para gestión visual)
4. **Cuenta de servicio de Google Cloud** con acceso a:
   - Google Drive API
   - Google Sheets API

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/marketplace-reviews-scraper.git
cd marketplace-reviews-scraper
```

### Paso 2: Configurar credenciales de Google

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita las APIs:
   - Google Drive API
   - Google Sheets API
4. Crea una cuenta de servicio:
   - Ve a "IAM y administración" → "Cuentas de servicio"
   - Crea una nueva cuenta de servicio
   - Descarga el archivo JSON de credenciales
5. Coloca el archivo JSON en la carpeta `credentials/`:
   ```bash
   mkdir -p credentials
   cp ~/Downloads/tu-archivo-credenciales.json credentials/google-credentials.json
   ```

6. **Importante**: Comparte tu Google Sheet con el email de la cuenta de servicio
   - Abre el archivo JSON de credenciales
   - Busca el campo `client_email`
   - Comparte tu Google Sheet con ese email (con permisos de edición)

### Paso 3: Configurar variables de entorno

```bash
cp .env.example .env
# Edita .env si necesitas cambiar configuraciones
```

### Paso 4: Construir e iniciar el contenedor

```bash
# Construir la imagen
docker-compose build

# Iniciar el servicio
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### Paso 5: Verificar instalación

```bash
# Verificar que el contenedor está corriendo
docker ps

# Probar la API
curl http://localhost:8000/health

# Probar conexión con Google Drive
curl -X POST http://localhost:8000/test-connection
```

## 📊 Formato de la Planilla de Google Sheets

Tu planilla debe tener las siguientes columnas (los nombres deben ser exactos):

| PRODUCTO | URL | ARCHIVOJSON |
|----------|-----|-------------|
| Producto 1 | https://... | *(se llenará automáticamente)* |
| Producto 2 | https://... | *(se llenará automáticamente)* |
| ... | ... | ... |

**Campos requeridos:**
- `PRODUCTO`: Nombre del producto (se usará para el nombre del archivo JSON)
- `URL`: URL completa del producto en el marketplace
- `ARCHIVOJSON`: Columna que se llenará automáticamente con el nombre del archivo JSON creado

## 🔧 Uso con n8n

### Configuración del webhook en n8n

1. Crea un nuevo workflow en n8n
2. Agrega un nodo **HTTP Request** con la siguiente configuración:

```json
{
  "method": "POST",
  "url": "http://tu-raspberry-ip:8000/scrape",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "spreadsheet_name": "Nombre de tu planilla",
    "sheet_name": "Hoja1"
  }
}
```

### Ejemplo de payload

```json
{
  "spreadsheet_name": "Productos Marketplace 2024",
  "sheet_name": "Hoja1",
  "drive_folder_id": "opcional-id-de-carpeta"
}
```

### Respuesta de la API

```json
{
  "status": "accepted",
  "message": "Proceso de scraping iniciado",
  "task_id": "uuid-de-la-tarea"
}
```

### Verificar estado de la tarea

```bash
curl http://localhost:8000/task/{task_id}
```

## 📡 Endpoints de la API

### `GET /`
Health check básico

**Respuesta:**
```json
{
  "service": "Marketplace Reviews Scraper",
  "version": "1.0.0",
  "status": "running"
}
```

### `GET /health`
Verificación de salud del servicio

**Respuesta:**
```json
{
  "status": "healthy"
}
```

### `POST /scrape`
Inicia el proceso de scraping

**Body:**
```json
{
  "spreadsheet_name": "string",
  "sheet_name": "string",
  "drive_folder_id": "string (opcional)"
}
```

**Respuesta:**
```json
{
  "status": "accepted",
  "message": "Proceso de scraping iniciado",
  "task_id": "string"
}
```

### `GET /task/{task_id}`
Obtiene el estado de una tarea

**Respuesta:**
```json
{
  "status": "completed|processing|failed",
  "progress": 100,
  "result": {
    "productos_procesados": 10,
    "resultados": [...]
  }
}
```

### `POST /test-connection`
Prueba la conexión con Google Drive

**Respuesta:**
```json
{
  "status": "success",
  "message": "Conexión exitosa con Google Drive",
  "details": {
    "connected": true,
    "files_found": 5
  }
}
```

## 🔍 Marketplaces Soportados

- ✅ **Mercado Libre** (Argentina, Chile, México, etc.)
- ✅ **Amazon**
- ✅ **Genérico** (intenta extraer reseñas de cualquier sitio)

## 📦 Formato de salida JSON

Cada archivo JSON generado tendrá la siguiente estructura:

```json
{
  "producto": "Nombre del producto",
  "url": "https://...",
  "fecha_extraccion": "2024-01-15T10:30:00",
  "total_reseñas": 25,
  "reseñas": [
    {
      "rating": 5.0,
      "titulo": "Excelente producto",
      "contenido": "Muy buena calidad...",
      "autor": "Usuario123",
      "fecha": "15/01/2024",
      "marketplace": "Mercado Libre"
    }
  ]
}
```

## 🐛 Troubleshooting

### El contenedor no inicia

```bash
# Ver logs detallados
docker-compose logs

# Reconstruir imagen
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Error de credenciales de Google

1. Verifica que el archivo `credentials/google-credentials.json` existe
2. Asegúrate de que la cuenta de servicio tiene permisos en Google Drive
3. Comparte tu planilla con el email de la cuenta de servicio

### No se extraen reseñas

- Verifica que la URL del producto es correcta
- Algunos sitios pueden tener protección anti-scraping
- Revisa los logs: `docker-compose logs -f`

### Problemas de memoria en Raspberry Pi

```bash
# Ajustar workers en .env
MAX_WORKERS=2

# Reiniciar contenedor
docker-compose restart
```

## 🔄 Actualización

```bash
# Detener contenedor
docker-compose down

# Actualizar código
git pull origin main

# Reconstruir e iniciar
docker-compose build
docker-compose up -d
```

## 📝 Logs

Los logs se almacenan en:
- `/app/logs/app.log` dentro del contenedor
- `./logs/app.log` en tu host

Ver logs en tiempo real:
```bash
docker-compose logs -f
```

## 🛡️ Seguridad

- ✅ No subas `credentials/` al repositorio
- ✅ Mantén `.env` privado
- ✅ Usa HTTPS en producción
- ✅ Implementa rate limiting si es necesario
- ✅ Restringe acceso a la API con firewall

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

## 📧 Contacto

Para soporte o consultas, abre un issue en GitHub.

---

Hecho con ❤️ para automatización de e-commerce
