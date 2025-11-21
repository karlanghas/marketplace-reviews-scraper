# 🚀 Inicio Rápido

Guía para tener el sistema funcionando en menos de 10 minutos.

## ⚡ Setup Express

### 1. Clonar repositorio (30 segundos)

```bash
git clone https://github.com/tu-usuario/marketplace-reviews-scraper.git
cd marketplace-reviews-scraper
```

### 2. Credenciales de Google (5 minutos)

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Habilita APIs: Google Drive + Google Sheets
3. Crea cuenta de servicio y descarga JSON
4. Guarda como `credentials/google-credentials.json`

**Email de la cuenta de servicio**: Ábrelo y copia el `client_email`

### 3. Instalar (3 minutos)

```bash
# Opción A: Script automático
./install.sh

# Opción B: Manual
docker-compose build
docker-compose up -d
```

### 4. Verificar (1 minuto)

```bash
# Ver si está corriendo
curl http://localhost:8000/health

# Probar conexión Google
curl -X POST http://localhost:8000/test-connection

# O usar el script de test
python3 test_installation.py
```

## 📊 Preparar Planilla

### Crear Google Sheet

| PRODUCTO | URL | ARCHIVOJSON |
|----------|-----|-------------|
| iPhone 14 | https://articulo.mercadolibre.cl/MLC-123 | |
| Samsung S23 | https://www.amazon.com/dp/B098... | |

### Compartir con cuenta de servicio

1. Copia el `client_email` de `credentials/google-credentials.json`
2. En Google Sheet → Compartir
3. Pega el email → Permisos de "Editor"

## 🔌 Configurar n8n

### Crear Workflow

1. n8n → Add Node → HTTP Request
2. Configurar:
   - **Method**: POST
   - **URL**: `http://tu-raspberry-ip:8000/scrape`
   - **Body**:
   ```json
   {
     "spreadsheet_name": "Mi Planilla",
     "sheet_name": "Hoja1"
   }
   ```

### Probar

```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "spreadsheet_name": "Mi Planilla",
    "sheet_name": "Hoja1"
  }'
```

Respuesta esperada:
```json
{
  "status": "accepted",
  "message": "Proceso de scraping iniciado",
  "task_id": "abc-123-def"
}
```

## ✅ Checklist

- [ ] Docker y Docker Compose instalados
- [ ] Credenciales de Google en `credentials/google-credentials.json`
- [ ] Contenedor corriendo (`docker ps`)
- [ ] Health check OK (`curl http://localhost:8000/health`)
- [ ] Conexión Google OK (`make test` o script de test)
- [ ] Google Sheet compartido con cuenta de servicio
- [ ] Planilla con columnas correctas
- [ ] n8n configurado (si aplica)

## 🆘 Problemas Comunes

### "File not found: google-credentials.json"
```bash
# Verifica que existe
ls credentials/google-credentials.json

# Si no existe, descárgalo de Google Cloud Console
```

### "Permission denied" en Google Sheets
```bash
# Obtén el email de la cuenta de servicio
make credentials

# Comparte tu Sheet con ese email
```

### Contenedor no inicia
```bash
# Ver logs
docker-compose logs -f

# Reconstruir
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Puerto 8000 en uso
```bash
# Cambiar puerto en docker-compose.yml
ports:
  - "8001:8000"  # Usa 8001 en lugar de 8000
```

## 📚 Siguiente Paso

Una vez funcionando:

1. Lee [SPREADSHEET_FORMAT.md](SPREADSHEET_FORMAT.md) para formato detallado
2. Revisa [README.md](README.md) para documentación completa
3. Configura automatización en n8n
4. Monitorea logs: `docker-compose logs -f`

## 🎯 Comandos Útiles

```bash
# Ver logs
make logs

# Reiniciar
make restart

# Estado
make status

# Probar Google Drive
make test

# Ver credenciales
make credentials

# Ayuda
make help
```

## 💡 Tips

1. **Primero prueba con 2-3 productos** antes de escalar
2. **Revisa los logs** regularmente para detectar problemas
3. **Mercado Libre** y **Amazon** tienen mejor soporte
4. **Rate limiting**: Espera ~3 segundos entre productos
5. **Backup**: Guarda tus credenciales en lugar seguro

## 🎉 ¡Listo!

Si todo funciona, deberías ver:
- ✅ API respondiendo en puerto 8000
- ✅ Archivos JSON apareciendo en Google Drive
- ✅ Columna ARCHIVOJSON llenándose automáticamente

¿Problemas? Abre un [issue](https://github.com/tu-usuario/marketplace-reviews-scraper/issues)
