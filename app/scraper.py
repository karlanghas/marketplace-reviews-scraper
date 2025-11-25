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
        self.drive_handler = drive_handler
        self.chrome_options = self._setup_chrome_options()
    
    def _setup_chrome_options(self) -> Options:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        return chrome_options
    
    async def scrape_from_spreadsheet(
        self,
        spreadsheet_name: str,
        sheet_name: str,
        drive_folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            logger.info("Leyendo planilla de Google Sheets...")
            records = self.drive_handler.read_spreadsheet(spreadsheet_name, sheet_name)
            
            if not records:
                raise ValueError("No se encontraron registros en la planilla")
            
            try:
                column_letter = self.drive_handler.find_column_letter(
                    spreadsheet_name, sheet_name, 'ARCHIVOJSON'
                )
            except:
                column_letter = "E" 
                logger.warning("No se encontró columna ARCHIVOJSON, usando columna E por defecto")

            results = []
            
            for idx, record in enumerate(records, start=2):
                try:
                    product_name = record.get('PRODUCTO', f'producto_{idx}')
                    product_url = record.get('URL', '')
                    
                    if not product_url:
                        continue
                    
                    logger.info(f">>> Procesando URL: {product_url}")
                    
                    reviews = await self.scrape_product_reviews(product_url, product_name)
                    
                    if reviews:
                        sheet_title = self._sanitize_sheet_name(product_name)
                        self.drive_handler.save_reviews_to_new_sheet(
                            spreadsheet_name,
                            sheet_title,
                            reviews
                        )
                        status_message = f"OK: Hoja '{sheet_title}' ({len(reviews)} reseñas)"
                        logger.info(status_message)
                    else:
                        status_message = "Sin reseñas encontradas (Revisar selectores o bloqueo)"
                        logger.warning(f"No se extrajeron reseñas para: {product_name}")

                    self.drive_handler.update_cell(
                        spreadsheet_name, sheet_name, idx, column_letter, status_message
                    )
                    
                    results.append({
                        'producto': product_name,
                        'reseñas_extraidas': len(reviews)
                    })
                    
                    await asyncio.sleep(3) # Pausa amigable
                    
                except Exception as e:
                    logger.error(f"Error procesando producto {product_name}: {str(e)}")
                    results.append({'producto': product_name, 'error': str(e)})
                    continue
            
            return {'status': 'success', 'resultados': results}
            
        except Exception as e:
            logger.error(f"Error en scraping desde planilla: {str(e)}")
            raise
    
    async def scrape_product_reviews(self, product_url: str, product_name: str) -> List[Dict[str, Any]]:
        marketplace = self._detect_marketplace(product_url)
        logger.info(f"Marketplace detectado: {marketplace}")
        
        if marketplace == 'mercadolibre':
            return await self._scrape_mercadolibre(product_url)
        elif marketplace == 'amazon':
            return await self._scrape_amazon(product_url)
        else:
            return await self._scrape_with_selenium(product_url)

    def _detect_marketplace(self, url: str) -> str:
        domain = urlparse(url).netloc.lower()
        if 'mercadolibre' in domain or 'mercadolivre' in domain:
            return 'mercadolibre'
        elif 'amazon' in domain:
            return 'amazon'
        else:
            return 'generic'

    # --- MERCADO LIBRE SCRAPER ---
    async def _scrape_mercadolibre(self, url: str) -> List[Dict[str, Any]]:
        reviews = []
        try:
            # 1. Intentar con requests (más rápido)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
            response = requests.get(url, headers=headers, timeout=20)
            
            # Si nos redirigen al login, fallamos
            if "login" in response.url:
                logger.warning("MercadoLibre redirigió a login. Se requiere Selenium.")
                return await self._scrape_with_selenium(url)

            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar el contenedor de opiniones. 
            # Estrategia: Buscar artículos de review o contenedores genéricos de comentarios
            review_elements = soup.find_all('article', class_=re.compile(r'ui-review|review-card'))
            
            if not review_elements:
                # Fallback: buscar divs que parezcan reviews
                review_elements = soup.select('div.ui-pdp-reviews__comments__content')
            
            logger.info(f"Elementos de reseña encontrados (Requests): {len(review_elements)}")

            for el in review_elements:
                r = self._parse_ml_element(el)
                if r['contenido']: # Solo agregar si tiene contenido
                    reviews.append(r)
            
            # Si requests falló, intentar Selenium
            if not reviews:
                logger.info("Requests no trajo reseñas, intentando Selenium para ML...")
                return await self._scrape_with_selenium(url)

        except Exception as e:
            logger.error(f"Error ML Requests: {e}")
            return await self._scrape_with_selenium(url)
            
        return reviews

    def _parse_ml_element(self, el) -> Dict[str, Any]:
        """Helper para extraer datos de un elemento HTML de ML"""
        # Selectores de contenido
        content = self._extract_text(el, ['p'], re.compile(r'content|comment|text'))
        if not content: content = el.get_text(strip=True)
        
        # Selectores de rating
        rating = 0
        rating_span = el.find('span', class_=re.compile(r'rating|star'))
        if rating_span:
            txt = rating_span.get_text()
            # Buscar números
            nums = re.findall(r'\d+', txt)
            if nums: rating = float(nums[0])
        
        # Si no encontramos rating numérico, buscar estrellas visuales (clases css)
        if not rating:
            stars = el.find_all(class_=re.compile(r'full-star|ui-review-capability-rating__icon'))
            if stars: rating = len(stars)

        return {
            'rating': rating,
            'titulo': self._extract_text(el, ['h3', 'h4'], re.compile(r'title')),
            'contenido': content,
            'autor': self._extract_text(el, ['span', 'div'], re.compile(r'author|user')),
            'fecha': self._extract_text(el, ['time', 'span'], re.compile(r'date|created')),
            'marketplace': 'Mercado Libre'
        }

    # --- AMAZON SCRAPER ---
    async def _scrape_amazon(self, url: str) -> List[Dict[str, Any]]:
        # Amazon bloquea requests casi siempre. Mejor ir directo a una estrategia mixta
        # pero intentaremos requests con headers muy completos primero.
        reviews = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'es-ES,es;q=0.9',
                'referer': 'https://www.google.com/'
            }
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code != 200:
                logger.warning(f"Amazon bloqueó requests (Status {response.status_code}). Usando Selenium.")
                return await self._scrape_with_selenium(url)
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Selectores clásicos de Amazon
            review_divs = soup.find_all('div', {'data-hook': 'review'})
            
            for div in review_divs:
                review = {
                    'titulo': self._extract_text(div, ['a'], {'data-hook': 'review-title'}),
                    'contenido': self._extract_text(div, ['span'], {'data-hook': 'review-body'}),
                    'rating': self._extract_amazon_rating(div),
                    'autor': self._extract_text(div, ['span'], 'a-profile-name'),
                    'fecha': self._extract_text(div, ['span'], {'data-hook': 'review-date'}),
                    'marketplace': 'Amazon'
                }
                if review['contenido']:
                    reviews.append(review)
            
            logger.info(f"Reseñas encontradas Amazon (Requests): {len(reviews)}")
            
            if not reviews:
                 return await self._scrape_with_selenium(url)
                 
        except Exception as e:
            logger.error(f"Error Amazon: {e}")
            return await self._scrape_with_selenium(url)
            
        return reviews

    # --- SELENIUM GENÉRICO (FALLBACK) ---
    async def _scrape_with_selenium(self, url: str) -> List[Dict[str, Any]]:
        reviews = []
        driver = None
        try:
            logger.info(f"Iniciando Selenium para: {url[:50]}...")
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.get(url)
            
            # Esperar carga inicial
            time.sleep(4)
            
            # Scroll agresivo para cargar lazy-load
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Estrategia "Escopeta": Buscar cualquier bloque de texto que parezca reseña
            # 1. Buscar contenedores específicos si sabemos el sitio
            detected_reviews = []
            
            # Selectores genéricos muy comunes
            selectors = [
                'div[data-hook="review"]',         # Amazon
                'article.ui-review',               # ML
                'div.ui-pdp-reviews__comments',    # ML Moderno
                'div[class*="review-content"]',
                'div[class*="comment-content"]',
                'div[itemprop="review"]'
            ]
            
            for sel in selectors:
                elements = soup.select(sel)
                if elements:
                    logger.info(f"Selenium encontró {len(elements)} elementos con selector '{sel}'")
                    detected_reviews = elements
                    break
            
            # Procesar lo encontrado
            for el in detected_reviews:
                text = el.get_text(" ", strip=True)
                # Limpieza básica
                if len(text) < 10: continue # Ignorar basura
                
                # Intentar parsear mejor
                r_content = self._extract_text(el, ['p', 'span'], re.compile(r'body|content|text|comment'))
                if not r_content: 
                    # Si no encuentra contenido específico, tomar el texto del bloque pero limpiar
                    r_content = text[:500] 

                r_rating = 0
                r_rating_txt = self._extract_text(el, ['span'], re.compile(r'rating|star'))
                if r_rating_txt:
                     nums = re.findall(r'(\d+)', r_rating_txt)
                     if nums: r_rating = nums[0]

                reviews.append({
                    'contenido': r_content,
                    'rating': r_rating,
                    'fecha': self._extract_text(el, ['time', 'span'], re.compile(r'date')),
                    'autor': self._extract_text(el, ['span', 'div'], re.compile(r'author|user|profile')),
                    'titulo': '',
                    'marketplace': self._detect_marketplace(url)
                })

            logger.info(f"Total reseñas extraídas con Selenium: {len(reviews)}")

        except Exception as e:
            logger.error(f"Error fatal Selenium: {str(e)}")
        finally:
            if driver:
                driver.quit()
        
        return reviews

    # --- HELPERS ---
    def _extract_text(self, element, tags: List[str], attrs=None) -> str:
        """Helper robusto para extraer texto"""
        try:
            target = None
            for tag in tags:
                if isinstance(attrs, dict):
                    target = element.find(tag, attrs)
                elif hasattr(attrs, 'search'): # es regex
                    target = element.find(tag, class_=attrs) or element.find(tag, id=attrs)
                elif isinstance(attrs, str):
                    target = element.find(tag, class_=re.compile(attrs))
                else:
                    target = element.find(tag)
                
                if target:
                    return target.get_text(strip=True)
        except:
            pass
        return ""

    def _extract_amazon_rating(self, element) -> str:
        try:
            res = element.find('i', {'data-hook': 'review-star-rating'})
            if res: return res.get_text()
            res = element.find('span', class_='a-icon-alt')
            if res: return res.get_text()
        except: pass
        return ""

    @staticmethod
    def _sanitize_sheet_name(name: str) -> str:
        name = re.sub(r'[\[\]\*\?\:\\\/]', '', str(name))
        name = name.replace('\n', ' ').replace('\r', '').replace('\t', ' ')
        if len(name) > 95: name = name[:95] + "..."
        return name.strip()