"""
Módulo para scraping de reseñas de marketplace
"""
import asyncio
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from loguru import logger
import time

from app.google_drive_handler import GoogleDriveHandler


class ReviewScraper:
    """Clase para scraping de reseñas de productos"""
    
    def __init__(self, drive_handler: GoogleDriveHandler):
        """
        Inicializa el scraper
        
        Args:
            drive_handler: Handler de Google Drive
        """
        self.drive_handler = drive_handler
        self.chrome_options = self._setup_chrome_options()
    
    def _setup_chrome_options(self) -> Options:
        """
        Configura opciones de Chrome para Raspberry Pi
        
        Returns:
            Opciones de Chrome
        """
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36')
        
        return chrome_options
    
    async def scrape_from_spreadsheet(
        self,
        spreadsheet_name: str,
        sheet_name: str,
        drive_folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa scraping desde una planilla de Google Sheets
        
        Args:
            spreadsheet_name: Nombre de la planilla
            sheet_name: Nombre de la hoja
            drive_folder_id: ID de carpeta de destino (opcional)
            
        Returns:
            Resultado del proceso
        """
        try:
            # Leer planilla
            logger.info("Leyendo planilla de Google Sheets...")
            records = self.drive_handler.read_spreadsheet(spreadsheet_name, sheet_name)
            
            if not records:
                raise ValueError("No se encontraron registros en la planilla")
            
            # Si no se especificó carpeta, usar la misma de la planilla
            if not drive_folder_id:
                drive_folder_id = self.drive_handler.get_folder_id_from_spreadsheet(spreadsheet_name)
                logger.info(f"Usando carpeta de la planilla: {drive_folder_id}")
            
            # Buscar columna ARCHIVOJSON
            column_letter = self.drive_handler.find_column_letter(
                spreadsheet_name,
                sheet_name,
                'ARCHIVOJSON'
            )
            
            results = []
            
            # Procesar cada producto
            for idx, record in enumerate(records, start=2):  # Start at 2 because row 1 is headers
                try:
                    # Extraer información del producto
                    product_name = record.get('PRODUCTO', f'producto_{idx}')
                    product_url = record.get('URL', '')
                    
                    if not product_url:
                        logger.warning(f"URL vacía para producto: {product_name}")
                        continue
                    
                    logger.info(f"Procesando: {product_name}")
                    
                    # Extraer reseñas
                    reviews = await self.scrape_product_reviews(product_url, product_name)
                    
                    # Crear estructura JSON
                    json_data = {
                        'producto': product_name,
                        'url': product_url,
                        'fecha_extraccion': datetime.now().isoformat(),
                        'total_reseñas': len(reviews),
                        'reseñas': reviews
                    }
                    
                    # Generar nombre de archivo
                    safe_name = self._sanitize_filename(product_name)
                    file_name = f"{safe_name}.json"
                    
                    # Subir a Google Drive
                    logger.info(f"Subiendo archivo: {file_name}")
                    file_id = self.drive_handler.upload_json_file(
                        json_data,
                        file_name,
                        drive_folder_id
                    )
                    
                    # Actualizar columna ARCHIVOJSON
                    self.drive_handler.update_cell(
                        spreadsheet_name,
                        sheet_name,
                        idx,
                        column_letter,
                        file_name
                    )
                    
                    results.append({
                        'producto': product_name,
                        'archivo': file_name,
                        'reseñas_extraidas': len(reviews),
                        'file_id': file_id
                    })
                    
                    logger.info(f"✓ Completado: {product_name} - {len(reviews)} reseñas")
                    
                    # Pausa para evitar rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error procesando producto {product_name}: {str(e)}")
                    results.append({
                        'producto': product_name,
                        'error': str(e)
                    })
                    continue
            
            return {
                'status': 'success',
                'productos_procesados': len(results),
                'resultados': results
            }
            
        except Exception as e:
            logger.error(f"Error en scraping desde planilla: {str(e)}")
            raise
    
    async def scrape_product_reviews(
        self,
        product_url: str,
        product_name: str
    ) -> List[Dict[str, Any]]:
        """
        Extrae reseñas de un producto
        
        Args:
            product_url: URL del producto
            product_name: Nombre del producto
            
        Returns:
            Lista de reseñas
        """
        try:
            # Detectar marketplace
            marketplace = self._detect_marketplace(product_url)
            logger.info(f"Marketplace detectado: {marketplace}")
            
            if marketplace == 'mercadolibre':
                return await self._scrape_mercadolibre(product_url)
            elif marketplace == 'amazon':
                return await self._scrape_amazon(product_url)
            else:
                return await self._scrape_generic(product_url)
                
        except Exception as e:
            logger.error(f"Error extrayendo reseñas de {product_name}: {str(e)}")
            return []
    
    def _detect_marketplace(self, url: str) -> str:
        """
        Detecta el marketplace según la URL
        
        Args:
            url: URL del producto
            
        Returns:
            Nombre del marketplace
        """
        domain = urlparse(url).netloc.lower()
        
        if 'mercadolibre' in domain or 'mercadolivre' in domain:
            return 'mercadolibre'
        elif 'amazon' in domain:
            return 'amazon'
        else:
            return 'generic'
    
    async def _scrape_mercadolibre(self, url: str) -> List[Dict[str, Any]]:
        """
        Extrae reseñas de Mercado Libre
        
        Args:
            url: URL del producto
            
        Returns:
            Lista de reseñas
        """
        reviews = []
        
        try:
            # Usar requests para obtener la página
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar sección de opiniones/reseñas
            # Nota: Los selectores pueden variar según el país de Mercado Libre
            review_elements = soup.find_all('article', class_=re.compile('ui-review'))
            
            if not review_elements:
                # Intentar selectores alternativos
                review_elements = soup.find_all('div', class_=re.compile('review'))
            
            for review_el in review_elements:
                try:
                    # Extraer datos de la reseña
                    rating = self._extract_rating(review_el)
                    title = self._extract_text(review_el, ['h3', 'h4'], 'review-title')
                    content = self._extract_text(review_el, ['p', 'div'], 'review-content')
                    author = self._extract_text(review_el, ['span', 'div'], 'review-author')
                    date = self._extract_text(review_el, ['time', 'span'], 'review-date')
                    
                    review = {
                        'rating': rating,
                        'titulo': title,
                        'contenido': content,
                        'autor': author,
                        'fecha': date,
                        'marketplace': 'Mercado Libre'
                    }
                    
                    reviews.append(review)
                    
                except Exception as e:
                    logger.debug(f"Error extrayendo reseña individual: {str(e)}")
                    continue
            
            # Si no se encontraron reseñas con el método anterior, intentar con Selenium
            if not reviews:
                logger.info("No se encontraron reseñas con requests, intentando con Selenium...")
                reviews = await self._scrape_with_selenium(url)
            
            logger.info(f"Extraídas {len(reviews)} reseñas de Mercado Libre")
            
        except Exception as e:
            logger.error(f"Error en scraping de Mercado Libre: {str(e)}")
        
        return reviews
    
    async def _scrape_amazon(self, url: str) -> List[Dict[str, Any]]:
        """
        Extrae reseñas de Amazon
        
        Args:
            url: URL del producto
            
        Returns:
            Lista de reseñas
        """
        reviews = []
        
        try:
            # Amazon requiere más cuidado para evitar detección
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36',
                'Accept-Language': 'es-ES,es;q=0.9'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar reseñas en Amazon
            review_elements = soup.find_all('div', {'data-hook': 'review'})
            
            for review_el in review_elements:
                try:
                    rating_el = review_el.find('i', {'data-hook': 'review-star-rating'})
                    rating = self._extract_amazon_rating(rating_el)
                    
                    title = self._extract_text(review_el, ['a'], {'data-hook': 'review-title'})
                    content = self._extract_text(review_el, ['span'], {'data-hook': 'review-body'})
                    author = self._extract_text(review_el, ['span'], {'class': 'a-profile-name'})
                    date = self._extract_text(review_el, ['span'], {'data-hook': 'review-date'})
                    
                    review = {
                        'rating': rating,
                        'titulo': title,
                        'contenido': content,
                        'autor': author,
                        'fecha': date,
                        'marketplace': 'Amazon'
                    }
                    
                    reviews.append(review)
                    
                except Exception as e:
                    logger.debug(f"Error extrayendo reseña de Amazon: {str(e)}")
                    continue
            
            logger.info(f"Extraídas {len(reviews)} reseñas de Amazon")
            
        except Exception as e:
            logger.error(f"Error en scraping de Amazon: {str(e)}")
        
        return reviews
    
    async def _scrape_generic(self, url: str) -> List[Dict[str, Any]]:
        """
        Scraper genérico para otros sitios
        
        Args:
            url: URL del producto
            
        Returns:
            Lista de reseñas
        """
        return await self._scrape_with_selenium(url)
    
    async def _scrape_with_selenium(self, url: str) -> List[Dict[str, Any]]:
        """
        Scraping usando Selenium para sitios dinámicos
        
        Args:
            url: URL del producto
            
        Returns:
            Lista de reseñas
        """
        reviews = []
        driver = None
        
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.get(url)
            
            # Esperar a que cargue
            time.sleep(3)
            
            # Scroll para cargar contenido dinámico
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Obtener HTML
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Buscar reseñas con selectores comunes
            review_selectors = [
                'div[class*="review"]',
                'article[class*="review"]',
                'div[class*="opinion"]',
                'div[class*="comentario"]'
            ]
            
            for selector in review_selectors:
                elements = soup.select(selector)
                if elements:
                    logger.info(f"Encontrados {len(elements)} elementos con selector: {selector}")
                    break
            
            # Procesar elementos encontrados
            for el in elements[:50]:  # Limitar a 50 reseñas
                try:
                    text = el.get_text(strip=True)
                    if len(text) > 20:  # Filtrar elementos muy cortos
                        review = {
                            'contenido': text[:500],  # Limitar longitud
                            'rating': None,
                            'titulo': '',
                            'autor': '',
                            'fecha': '',
                            'marketplace': 'Generic'
                        }
                        reviews.append(review)
                except:
                    continue
            
        except Exception as e:
            logger.error(f"Error en Selenium scraping: {str(e)}")
        
        finally:
            if driver:
                driver.quit()
        
        return reviews
    
    def _extract_rating(self, element) -> Optional[float]:
        """Extrae rating de un elemento"""
        try:
            rating_el = element.find('span', class_=re.compile('star|rating'))
            if rating_el:
                rating_text = rating_el.get_text()
                rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
                if rating_match:
                    return float(rating_match.group(1))
        except:
            pass
        return None
    
    def _extract_amazon_rating(self, element) -> Optional[float]:
        """Extrae rating de Amazon"""
        try:
            if element:
                text = element.get_text()
                match = re.search(r'(\d+(?:\.\d+)?)', text)
                if match:
                    return float(match.group(1))
        except:
            pass
        return None
    
    def _extract_text(self, element, tags: List[str], attrs=None) -> str:
        """Extrae texto de un elemento con varios tags posibles"""
        try:
            for tag in tags:
                if isinstance(attrs, str):
                    el = element.find(tag, class_=re.compile(attrs))
                elif isinstance(attrs, dict):
                    el = element.find(tag, attrs)
                else:
                    el = element.find(tag)
                
                if el:
                    return el.get_text(strip=True)
        except:
            pass
        return ''
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        Limpia nombre de archivo para que sea válido
        
        Args:
            filename: Nombre original
            
        Returns:
            Nombre sanitizado
        """
        # Remover caracteres no válidos
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Reemplazar espacios
        filename = filename.replace(' ', '_')
        # Limitar longitud
        filename = filename[:100]
        return filename
