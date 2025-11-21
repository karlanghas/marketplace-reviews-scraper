# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2024-11-21

### Añadido
- Implementación inicial del scraper de reseñas de marketplace
- Soporte para Mercado Libre
- Soporte para Amazon
- Scraper genérico para otros marketplaces
- API REST con FastAPI
- Integración con Google Drive y Google Sheets
- Actualización automática de columna ARCHIVOJSON
- Procesamiento en background de tareas
- Sistema de logs con loguru
- Docker y Docker Compose para Raspberry Pi 5 (ARM64)
- Healthcheck endpoints
- Script de instalación automática
- Configuración de ejemplo para n8n
- Makefile con comandos útiles
- Tests de instalación
- Documentación completa

### Características
- Extracción de reseñas con rating, título, contenido, autor y fecha
- Almacenamiento en formato JSON
- Procesamiento de múltiples productos en lote
- Rate limiting configurable
- Manejo robusto de errores
- Soporte para Selenium para sitios dinámicos
- Detección automática de marketplace

### Seguridad
- Credenciales de Google separadas del código
- Variables de entorno para configuración sensible
- .gitignore para archivos sensibles

### Documentación
- README completo con instrucciones de instalación
- Formato de planilla documentado (SPREADSHEET_FORMAT.md)
- Ejemplos de configuración para n8n
- Guía de troubleshooting

## [Unreleased]

### Planeado
- [ ] Soporte para más marketplaces (eBay, AliExpress, etc.)
- [ ] Sistema de notificaciones por email
- [ ] Dashboard web para monitoreo
- [ ] Exportación a otros formatos (CSV, Excel)
- [ ] Análisis de sentimiento de reseñas
- [ ] API para consulta de reseñas almacenadas
- [ ] Rate limiting avanzado
- [ ] Caché de reseñas
- [ ] Reintentos automáticos en caso de fallo
- [ ] Métricas y estadísticas de scraping

### En consideración
- [ ] Soporte para proxies
- [ ] Scraping distribuido
- [ ] Interfaz web de administración
- [ ] Webhooks para notificaciones
- [ ] Base de datos para histórico de reseñas
