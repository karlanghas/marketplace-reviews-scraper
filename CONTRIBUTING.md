# Guía de Contribución

¡Gracias por tu interés en contribuir a Marketplace Reviews Scraper! 🎉

## Código de Conducta

Este proyecto adhiere a un código de conducta. Al participar, se espera que respetes este código.

## ¿Cómo puedo contribuir?

### Reportar Bugs

Los bugs se rastrean como [GitHub issues](https://github.com/tu-usuario/marketplace-reviews-scraper/issues).

**Antes de crear un issue:**
- Verifica que el bug no haya sido reportado ya
- Asegúrate de que estás usando la última versión
- Recopila información sobre el problema

**Al crear un issue, incluye:**
- Descripción clara del problema
- Pasos para reproducir
- Comportamiento esperado vs. comportamiento actual
- Versión del software
- Sistema operativo
- Logs relevantes

### Sugerir Mejoras

Las mejoras también se rastrean como GitHub issues.

**Al sugerir una mejora:**
- Usa un título claro y descriptivo
- Proporciona una descripción detallada
- Explica por qué sería útil
- Si es posible, incluye ejemplos o mockups

### Pull Requests

1. **Fork el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/marketplace-reviews-scraper.git
   cd marketplace-reviews-scraper
   ```

2. **Crea una rama**
   ```bash
   git checkout -b feature/nueva-caracteristica
   # o
   git checkout -b fix/correccion-bug
   ```

3. **Realiza tus cambios**
   - Escribe código limpio y bien documentado
   - Sigue las convenciones de estilo de Python (PEP 8)
   - Añade tests si es apropiado
   - Actualiza la documentación

4. **Commit tus cambios**
   ```bash
   git add .
   git commit -m "feat: añade nueva característica X"
   ```
   
   Usa [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` nueva característica
   - `fix:` corrección de bug
   - `docs:` cambios en documentación
   - `style:` formateo, punto y coma faltante, etc.
   - `refactor:` refactorización de código
   - `test:` añadir tests
   - `chore:` actualizar tareas de construcción, etc.

5. **Push a tu fork**
   ```bash
   git push origin feature/nueva-caracteristica
   ```

6. **Abre un Pull Request**
   - Usa un título descriptivo
   - Describe qué cambios realizaste y por qué
   - Referencia issues relacionados

## Guías de Estilo

### Python

- Seguir [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Usar type hints cuando sea posible
- Documentar funciones con docstrings
- Máximo 100 caracteres por línea

**Ejemplo:**
```python
def extract_reviews(product_url: str, max_reviews: int = 100) -> List[Dict[str, Any]]:
    """
    Extrae reseñas de un producto.
    
    Args:
        product_url: URL del producto
        max_reviews: Número máximo de reseñas a extraer
        
    Returns:
        Lista de diccionarios con las reseñas
    """
    # Implementación
    pass
```

### Git Commit Messages

- Usa el tiempo presente ("añade característica" no "añadida característica")
- Primera línea: resumen conciso (máx. 72 caracteres)
- Separar con línea en blanco
- Cuerpo del mensaje: explicación detallada si es necesario

**Ejemplo:**
```
feat: añade soporte para scraping de eBay

- Implementa detector de marketplace para eBay
- Añade extractor específico para reviews de eBay
- Actualiza documentación con ejemplos de eBay
- Añade tests para el nuevo scraper

Closes #123
```

## Desarrollo Local

### Configurar el entorno

1. **Clonar y crear entorno virtual**
   ```bash
   git clone https://github.com/tu-usuario/marketplace-reviews-scraper.git
   cd marketplace-reviews-scraper
   python3 -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Si existe
   ```

3. **Configurar credenciales**
   ```bash
   cp .env.example .env
   # Edita .env con tus configuraciones
   ```

### Ejecutar tests

```bash
# Tests unitarios
pytest tests/

# Tests con coverage
pytest --cov=app tests/

# Tests de integración
pytest tests/integration/
```

### Ejecutar la aplicación localmente

```bash
# Sin Docker
uvicorn app.main:app --reload

# Con Docker
docker-compose up
```

### Linting y formateo

```bash
# Formatear código
black app/

# Linting
flake8 app/

# Type checking
mypy app/
```

## Agregar un Nuevo Marketplace

Para agregar soporte para un nuevo marketplace:

1. **Crear método en `scraper.py`**
   ```python
   async def _scrape_nuevo_marketplace(self, url: str) -> List[Dict[str, Any]]:
       """
       Extrae reseñas de Nuevo Marketplace
       
       Args:
           url: URL del producto
           
       Returns:
           Lista de reseñas
       """
       # Implementación
       pass
   ```

2. **Actualizar `_detect_marketplace()`**
   ```python
   def _detect_marketplace(self, url: str) -> str:
       domain = urlparse(url).netloc.lower()
       
       if 'nuevomarketplace' in domain:
           return 'nuevo_marketplace'
       # ...
   ```

3. **Actualizar `scrape_product_reviews()`**
   ```python
   if marketplace == 'nuevo_marketplace':
       return await self._scrape_nuevo_marketplace(product_url)
   ```

4. **Añadir tests**
   ```python
   def test_scrape_nuevo_marketplace():
       # Tests
       pass
   ```

5. **Actualizar documentación**
   - Añadir en README.md
   - Actualizar CHANGELOG.md

## Preguntas

Si tienes preguntas, puedes:
- Abrir un issue con la etiqueta `question`
- Contactar a los mantenedores

## Reconocimientos

Los contribuidores serán reconocidos en el README.md

¡Gracias por contribuir! 🚀
