# 🎯 INSTRUCCIONES DE INSTALACIÓN - MARKETPLACE REVIEWS SCRAPER

## ✅ Proyecto Creado Exitosamente

Has recibido todos los archivos necesarios para ejecutar el scraper de reseñas de marketplace en tu Raspberry Pi 5.

## 📦 Estructura del Proyecto

```
marketplace-reviews-scraper/
├── app/                          # Código de la aplicación
│   ├── __init__.py              # Inicialización del paquete
│   ├── main.py                  # API principal con FastAPI
│   ├── scraper.py               # Lógica de scraping
│   └── google_drive_handler.py  # Integración con Google Drive
├── config/                       # Configuraciones
│   └── n8n-workflow-example.json # Ejemplo de workflow n8n
├── credentials/                  # Credenciales (colocar tu archivo aquí)
│   └── README.md                # Instrucciones de credenciales
├── .github/workflows/           # CI/CD con GitHub Actions
│   └── ci.yml                   # Pipeline de integración continua
├── Dockerfile                   # Imagen Docker optimizada para ARM64
├── docker-compose.yml           # Orquestación con Docker Compose
├── portainer-stack.yml          # Configuración para Portainer
├── requirements.txt             # Dependencias de Python
├── Makefile                     # Comandos útiles
├── install.sh                   # Script de instalación automática
├── test_installation.py         # Script de pruebas
├── healthcheck.sh              # Healthcheck para Docker
├── example-spreadsheet.csv     # Plantilla de ejemplo
├── .gitignore                  # Archivos ignorados por Git
├── .dockerignore               # Archivos ignorados por Docker
├── .env.example                # Variables de entorno de ejemplo
├── README.md                   # Documentación principal
├── QUICKSTART.md               # Guía de inicio rápido
├── SPREADSHEET_FORMAT.md       # Formato de planilla
├── CHANGELOG.md                # Historial de cambios
├── CONTRIBUTING.md             # Guía de contribución
└── LICENSE                     # Licencia MIT
```

## 🚀 PASOS PARA INSTALAR EN TU RASPBERRY PI

### 1. Subir a GitHub (RECOMENDADO)

```bash
# En tu computadora local
cd ruta/a/marketplace-reviews-scraper
git init
git add .
git commit -m "Initial commit: Marketplace reviews scraper"
git branch -M main
git remote add origin https://github.com/tu-usuario/marketplace-reviews-scraper.git
git push -u origin main
```

### 2. Clonar en Raspberry Pi

```bash
# En tu Raspberry Pi 5
ssh pi@tu-raspberry-ip
cd ~
git clone https://github.com/tu-usuario/marketplace-reviews-scraper.git
cd marketplace-reviews-scraper
```

### 3. Obtener Credenciales de Google

**IMPORTANTE**: Sin este paso, la aplicación NO funcionará.

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto nuevo o usa uno existente
3. Habilita estas APIs:
   - Google Drive API
   - Google Sheets API
4. Crea una cuenta de servicio:
   - IAM y administración → Cuentas de servicio
   - Crear cuenta de servicio
   - Descargar clave JSON
5. Copia el archivo a tu Raspberry Pi:
   ```bash
   # Desde tu computadora
   scp google-credentials.json pi@tu-raspberry-ip:~/marketplace-reviews-scraper/credentials/
   ```

### 4. Ejecutar Instalación

```bash
# En tu Raspberry Pi
cd marketplace-reviews-scraper
chmod +x install.sh
./install.sh
```

El script instalará automáticamente:
- Dependencias necesarias
- Docker y Docker Compose (si no están instalados)
- Construirá la imagen
- Iniciará los servicios

### 5. Verificar Instalación

```bash
# Opción 1: Script de prueba
python3 test_installation.py

# Opción 2: Comandos manuales
docker ps                                      # Ver contenedor corriendo
curl http://localhost:8000/health              # Health check
curl -X POST http://localhost:8000/test-connection  # Probar Google Drive
```

### 6. Preparar Google Sheet

1. Crea una planilla en Google Sheets con estas columnas:
   ```
   PRODUCTO | URL | ARCHIVOJSON
   ```
   
2. **MUY IMPORTANTE**: Comparte la planilla con el email de tu cuenta de servicio
   - Abre `credentials/google-credentials.json`
   - Copia el valor de `client_email`
   - En Google Sheet → Compartir
   - Pega el email
   - Permisos: "Editor"

3. Llena las columnas PRODUCTO y URL (ARCHIVOJSON se llenará automáticamente)

### 7. Configurar n8n

1. En n8n, crea un nuevo workflow
2. Agrega nodo HTTP Request:
   - **Method**: POST
   - **URL**: `http://tu-raspberry-ip:8000/scrape`
   - **Body**:
   ```json
   {
     "spreadsheet_name": "Nombre de tu planilla",
     "sheet_name": "Hoja1"
   }
   ```

3. Prueba el workflow

## 📱 ACCESO A LA APLICACIÓN

Una vez instalado:

- **API**: `http://tu-raspberry-ip:8000`
- **Docs**: `http://tu-raspberry-ip:8000/docs`
- **Health**: `http://tu-raspberry-ip:8000/health`

## 🔧 COMANDOS ÚTILES

```bash
# Ver todos los comandos disponibles
make help

# Ver logs en tiempo real
make logs

# Reiniciar servicios
make restart

# Ver estado
make status

# Probar conexión Google Drive
make test

# Ver email de cuenta de servicio
make credentials
```

## 📊 GESTIÓN CON PORTAINER

Si usas Portainer:

1. Ve a Stacks → Add Stack
2. Nombra el stack: "marketplace-reviews"
3. Selecciona "Repository" o "Web editor"
4. Si usas Web editor, copia el contenido de `portainer-stack.yml`
5. Ajusta las rutas de los volúmenes
6. Deploy the stack

## 🐛 SOLUCIÓN DE PROBLEMAS

### Contenedor no inicia
```bash
docker-compose logs -f
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Error de credenciales
```bash
# Verifica que existe el archivo
ls credentials/google-credentials.json

# Verifica el email de la cuenta de servicio
cat credentials/google-credentials.json | grep client_email

# Asegúrate de compartir tu Sheet con ese email
```

### Puerto 8000 ocupado
Edita `docker-compose.yml` y cambia:
```yaml
ports:
  - "8001:8000"  # Cambia 8000 por otro puerto
```

## 📚 DOCUMENTACIÓN ADICIONAL

- **Guía rápida**: Lee `QUICKSTART.md`
- **Formato de planilla**: Lee `SPREADSHEET_FORMAT.md`
- **Documentación completa**: Lee `README.md`
- **Contribuir**: Lee `CONTRIBUTING.md`

## 🎯 CHECKLIST DE INSTALACIÓN

- [ ] Código subido a GitHub
- [ ] Código clonado en Raspberry Pi
- [ ] Docker instalado
- [ ] Credenciales de Google en `credentials/google-credentials.json`
- [ ] Script `install.sh` ejecutado exitosamente
- [ ] Contenedor corriendo (`docker ps`)
- [ ] Health check OK
- [ ] Conexión con Google Drive OK
- [ ] Google Sheet creado con columnas correctas
- [ ] Google Sheet compartido con cuenta de servicio
- [ ] n8n configurado (si aplica)
- [ ] Primera prueba exitosa

## 💡 CONSEJOS IMPORTANTES

1. **Primero prueba con 2-3 productos** para verificar que todo funciona
2. **Guarda backup de tus credenciales** en un lugar seguro
3. **No subas credenciales a Git** (ya está en .gitignore)
4. **Monitorea los logs** regularmente
5. **Rate limiting**: El scraper espera 2-3 segundos entre productos
6. **Mercado Libre y Amazon** tienen mejor soporte que otros marketplaces

## 🆘 SOPORTE

Si tienes problemas:
1. Revisa los logs: `make logs`
2. Ejecuta el test: `python3 test_installation.py`
3. Lee el README.md completo
4. Abre un issue en GitHub

## 🎉 ¡LISTO!

Si todo funciona correctamente, deberías ver:
- ✅ Contenedor corriendo en Docker
- ✅ API respondiendo en puerto 8000
- ✅ Conexión exitosa con Google Drive
- ✅ Archivos JSON creándose automáticamente
- ✅ Columna ARCHIVOJSON actualizándose

---

**Creado por:** Claude AI Assistant
**Fecha:** 2024-11-21
**Versión:** 1.0.0
**Optimizado para:** Raspberry Pi 5 (ARM64)

¡Disfruta automatizando tu recopilación de reseñas! 🚀
