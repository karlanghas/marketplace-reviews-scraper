# Credenciales de Google

Esta carpeta debe contener el archivo de credenciales de Google Cloud.

## Instrucciones

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita las siguientes APIs:
   - Google Drive API
   - Google Sheets API

4. Crea una cuenta de servicio:
   - Ve a "IAM y administración" → "Cuentas de servicio"
   - Click en "Crear cuenta de servicio"
   - Nombre: `marketplace-reviews-scraper`
   - Descripción: "Cuenta de servicio para scraper de reseñas"
   - Click en "Crear y continuar"
   - Rol: "Editor" (o permisos específicos de Drive y Sheets)
   - Click en "Continuar" → "Listo"

5. Crear y descargar clave:
   - Click en la cuenta de servicio creada
   - Pestaña "Claves"
   - "Agregar clave" → "Crear clave nueva"
   - Tipo: JSON
   - Click en "Crear"

6. Guarda el archivo descargado como:
   ```
   credentials/google-credentials.json
   ```

## Compartir acceso

**MUY IMPORTANTE**: Debes compartir tus archivos de Google con la cuenta de servicio.

Para encontrar el email de la cuenta de servicio:
1. Abre el archivo `google-credentials.json`
2. Busca el campo `client_email`
3. Copia ese email (ejemplo: `marketplace-scraper@tu-proyecto.iam.gserviceaccount.com`)
4. En Google Drive o Google Sheets:
   - Abre el archivo/carpeta que quieres compartir
   - Click en "Compartir"
   - Pega el email de la cuenta de servicio
   - Selecciona "Editor" como rol
   - Click en "Enviar"

## Seguridad

⚠️ **NUNCA subas este archivo a Git o lo compartas públicamente**

El archivo `google-credentials.json` está incluido en `.gitignore` para protegerlo.

## Verificar instalación

Ejecuta el siguiente comando para verificar que las credenciales están correctamente configuradas:

```bash
make credentials
# o
python3 -c "import json; print(json.load(open('credentials/google-credentials.json'))['client_email'])"
```

## Troubleshooting

### Error: "File not found"
- Verifica que el archivo se llama exactamente `google-credentials.json`
- Verifica que está en la carpeta `credentials/`

### Error: "Permission denied"
- Verifica que compartiste tu Google Sheet con el email de la cuenta de servicio
- Verifica que diste permisos de "Editor"

### Error: "Invalid credentials"
- Verifica que descargaste el archivo JSON correcto
- Verifica que las APIs están habilitadas en Google Cloud Console
- Intenta crear una nueva clave
