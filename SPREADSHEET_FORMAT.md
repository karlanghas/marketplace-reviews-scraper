# Ejemplo de Planilla para Marketplace Reviews Scraper

## Formato requerido

Tu planilla de Google Sheets debe tener exactamente estas columnas:

| Columna | Descripción | Requerido | Tipo |
|---------|-------------|-----------|------|
| PRODUCTO | Nombre del producto | Sí | Texto |
| URL | URL completa del producto | Sí | URL |
| ARCHIVOJSON | Nombre del archivo JSON (se llena automáticamente) | Sí | Texto |

## Ejemplo de datos

```
PRODUCTO                          | URL                                                    | ARCHIVOJSON
----------------------------------|--------------------------------------------------------|------------------
iPhone 14 Pro 256GB              | https://articulo.mercadolibre.cl/MLC-123456789        | 
Samsung Galaxy S23 Ultra         | https://www.amazon.com/dp/B0BN4EXAMPLE                | 
Laptop Dell Inspiron 15          | https://articulo.mercadolibre.com.mx/MLM-987654321    | 
PlayStation 5 Digital Edition    | https://www.mercadolibre.com.ar/MLA-456789123         | 
Nintendo Switch OLED             | https://www.amazon.com/dp/B098EXAMPLE                 | 
```

## Notas importantes

1. **PRODUCTO**: 
   - Será usado como nombre base para el archivo JSON
   - Se limpiarán caracteres especiales automáticamente
   - Ejemplo: "iPhone 14 Pro" → "iPhone_14_Pro.json"

2. **URL**:
   - Debe ser la URL completa del producto
   - Debe comenzar con http:// o https://
   - Ejemplos válidos:
     - Mercado Libre: https://articulo.mercadolibre.cl/MLC-123456789
     - Amazon: https://www.amazon.com/dp/B0BN4EXAMPLE
     - Otros marketplaces también son soportados

3. **ARCHIVOJSON**:
   - Esta columna se llena automáticamente por la aplicación
   - NO la llenes manualmente
   - Contendrá el nombre del archivo JSON creado

## Compartir la planilla

**MUY IMPORTANTE**: Debes compartir tu planilla de Google Sheets con el email de la cuenta de servicio.

Para encontrar el email:
1. Abre el archivo `credentials/google-credentials.json`
2. Busca el campo `client_email`
3. Copia ese email
4. En tu Google Sheet, click en "Compartir"
5. Pega el email y dale permisos de "Editor"

Ejemplo de email de cuenta de servicio:
```
marketplace-scraper@tu-proyecto.iam.gserviceaccount.com
```

## Consejos

- Mantén nombres de productos descriptivos pero concisos
- Verifica que las URLs sean correctas antes de ejecutar el scraping
- Puedes tener múltiples hojas en la misma planilla
- La aplicación procesará solo la hoja que especifiques en la API

## Límites recomendados

- Máximo 100 productos por ejecución (ajustable)
- Espera entre 2-5 segundos por producto
- Para grandes volúmenes, considera ejecutar en lotes

## Ejemplo de llamada a la API

```json
{
  "spreadsheet_name": "Mi Planilla de Productos",
  "sheet_name": "Hoja1"
}
```
