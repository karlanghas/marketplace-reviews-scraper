"""
Módulo para scraping de reseñas de marketplace (Fixed for Raspberry Pi 5 + Docker)
"""
import asyncio
import json
from typing import List, Dict, Optional, Any
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service # Necesario para indicar la ruta del driver
from selenium.webdriver.common.by import By
from loguru import logger
import time

from app.google_drive_handler import GoogleDriveHandler

class ReviewScraper:
    
    def __init__(self, drive_handler: GoogleDriveHandler):
        self.drive_handler = drive_handler
        # Configuración explícita para Docker en Raspberry Pi
        self.chrome_service = Service("/usr/bin/chromedriver")
        self.chrome_options = self._setup_chrome_options()
    
    def _setup_chrome_options(self) -> Options:
        chrome_options = Options()
        
        # IMPORTANTE: Decirle dónde está el binario del navegador
        chrome_options.binary_location = "/usr/bin/chromium"
        
        # Argumentos críticos para Docker
        chrome_options.add_argument('--headless') # Ejecutar sin interfaz gráfica
        chrome_options.add_argument('--no-sandbox') # Necesario para root en Docker
        chrome_options.add_argument('--disable-dev-shm-usage') # Evita errores de memoria compartida
        chrome_options.add_argument('--disable-gpu')
        
        # User Agent para parecer un navegador real y no un bot
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36')
        
        return chrome_options
    
    async def scrape_from_spreadsheet(self, spreadsheet_name: str, sheet_name: str, drive_folder_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            logger.info("Leyendo planilla de Google Sheets...")
            records = self.drive_handler.read_spreadsheet(spreadsheet_name, sheet_name)
            
            try:
                column_letter = self.drive_handler.find_column_letter(spreadsheet_name, sheet_name, 'ARCHIVOJSON')
            except:
                column_letter = "E"
            
            results = []
            
            for idx, record in enumerate(records, start=2):
                try:
                    product_name = record.get('PRODUCTO', f'producto_{idx}')
                    product_url = record.get('URL', '')
                    
                    if not product_url: continue
                    
                    logger.info(f">>> Procesando: {product_name}")
                    
                    # Llamada al scraping
                    reviews = await self.scrape_product_reviews(product_url, product_name)
                    
                    if reviews:
                        sheet_title = self._sanitize_sheet_name(product_name)
                        # Guardar en nueva hoja
                        self.drive_handler.save_reviews_to_new_sheet(spreadsheet_name, sheet_title, reviews)
                        msg = f"OK: {sheet_title} ({len(reviews)} reseñas)"
                        logger.info(msg)
                    else:
                        msg = "Sin reseñas (Check log)"
                        logger.warning(f"No se obtuvieron reseñas para {product_name}")
                        
                    # Actualizar estado en planilla principal
                    self.drive_handler.update_cell(spreadsheet_name, sheet_name, idx, column_letter, msg)
                    results.append({'producto': product_name, 'count': len(reviews)})
                    
                    # Pausa respetuosa
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error procesando item {idx}: {e}")
                    continue
                    
            return {'status': 'success', 'results': results}
        except Exception as e:
            logger.error(f"Error general scraping: {e}")
            raise

    async def scrape_product_reviews(self, product_url: str, product_name: str) -> List[Dict[str, Any]]:
        marketplace = self._detect_marketplace(product_url)
        
        if marketplace == 'mercadolibre':
            return await self._scrape_mercadolibre_selenium(product_url)
        elif marketplace == 'amazon':
            # Implementar lógica similar si se requiere
            return await self._scrape_mercadolibre_selenium(product_url) 
        else:
            return []

    def _detect_marketplace(self, url: str) -> str:
        domain = urlparse(url).netloc.lower()
        if 'mercadolibre' in domain or 'mercadolivre' in domain: return 'mercadolibre'
        elif 'amazon' in domain: return 'amazon'
        return 'generic'

    async def _scrape_mercadolibre_selenium(self, url: str) -> List[Dict[str, Any]]:
        reviews = []
        driver = None
        try:
            logger.info("Iniciando Selenium con driver local...")
            
            # INICIALIZACIÓN CORRECTA PARA RASPBERRY/DOCKER
            driver = webdriver.Chrome(service=self.chrome_service, options=self.chrome_options)
            
            driver.get(url)
            time.sleep(3) # Esperar carga inicial

            # 1. BUSCAR ENLACE A "VER TODAS"
            reviews_url = None
            try:
                # Buscar enlaces que contengan palabras clave
                links = driver.find_elements(By.CSS_SELECTOR, "a")
                for link in links:
                    href = link.get_attribute('href')
                    if href and ('/reviews/' in href or 'opiniones' in href):
                        text = link.text.lower()
                        if 'todas' in text or 'all' in text or 'ver' in text:
                            reviews_url = href
                            break
                
                if not reviews_url:
                    # Intento específico botón ML moderno
                    try:
                        btn = driver.find_element(By.CSS_SELECTOR, "a.ui-pdp-reviews__see-more")
                        reviews_url = btn.get_attribute('href')
                    except: pass
            except Exception as e:
                logger.warning(f"No se encontró enlace de reseñas: {e}")

            # 2. NAVEGAR Y SCROLL
            if reviews_url:
                logger.info(f"Navegando a reseñas completas: {reviews_url}")
                driver.get(reviews_url)
                time.sleep(3)
                
                # Scroll loop
                last_height = driver.execute_script("return document.body.scrollHeight")
                for i in range(10): # Scroll 10 veces máximo
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.5)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        # Intentar botón "Cargar más" si existe
                        try:
                            btn_more = driver.find_element(By.CSS_SELECTOR, "button.ui-review-view__more-options-button")
                            btn_more.click()
                            time.sleep(1.5)
                        except:
                            break 
                    last_height = new_height
            else:
                logger.info("Extrayendo solo reseñas de la página principal (no se halló 'ver todas')")

            # 3. EXTRAER DATOS (Usando BeautifulSoup sobre el HTML renderizado)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Selectores variados para encontrar tarjetas
            cards = soup.select('article.ui-review-card')
            if not cards: cards = soup.select('div.ui-review-card')
            if not cards: cards = soup.select('div.ui-pdp-reviews__comments__content') # Página producto
            
            logger.info(f"Tarjetas encontradas: {len(cards)}")

            for card in cards:
                try:
                    # Contenido
                    content = self._extract_text(card, ['p'], re.compile('content|text|comment'))
                    if not content: 
                        content = card.get_text(strip=True)
                        if len(content) > 500: content = content[:500]

                    # Rating (Estrellas SVG)
                    rating = 0
                    stars_div = card.select_one('div.ui-review-capability__rating')
                    if not stars_div: stars_div = card.select_one('span.ui-review-capability__rating')
                    
                    if stars_div:
                        # Contar iconos SVG
                        svgs = stars_div.find_all('svg')
                        if svgs: rating = float(len(svgs))
                    
                    # Título
                    title = self._extract_text(card, ['h4', 'h3'], re.compile('title'))
                    
                    # Fecha
                    date = self._extract_text(card, ['time', 'span'], re.compile('date|created'))

                    # Autor (a veces no existe)
                    author = "Usuario ML" # Default

                    if content:
                        reviews.append({
                            'contenido': content,
                            'rating': rating if rating > 0 else "",
                            'fecha': date,
                            'autor': author,
                            'titulo': title,
                            'marketplace': 'Mercado Libre'
                        })
                except Exception:
                    continue

        except Exception as e:
            logger.error(f"Error Selenium: {e}")
        finally:
            if driver:
                driver.quit()
        
        return reviews

    def _extract_text(self, element, tags, attrs=None) -> str:
        try:
            for tag in tags:
                el = element.find(tag, class_=attrs)
                if el: return el.get_text(strip=True)
        except: pass
        return ""

    @staticmethod
    def _sanitize_sheet_name(name: str) -> str:
        name = re.sub(r'[\[\]\*\?\:\\\/]', '', str(name))
        name = name.replace('\n', ' ').replace('\r', '').replace('\t', ' ')
        return name[:95].strip()