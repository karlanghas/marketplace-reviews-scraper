"""
Módulo para scraping de reseñas de marketplace (Versión Anti-Bot / Stealth)
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
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from loguru import logger
import time
import random

from app.google_drive_handler import GoogleDriveHandler

class ReviewScraper:
    
    def __init__(self, drive_handler: GoogleDriveHandler):
        self.drive_handler = drive_handler
        self.chrome_service = Service("/usr/bin/chromedriver")
        self.chrome_options = self._setup_chrome_options()
    
    def _setup_chrome_options(self) -> Options:
        chrome_options = Options()
        chrome_options.binary_location = "/usr/bin/chromium"
        
        # --- CONFIGURACIÓN ANTI-DETECCIÓN ---
        chrome_options.add_argument('--headless') 
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        # 1. Ocultar que es Selenium
        chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 2. Tamaño de ventana realista
        chrome_options.add_argument('--window-size=1920,1080')
        
        # 3. User Agent de PC real (Windows)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        return chrome_options
    
    async def scrape_from_spreadsheet(self, spreadsheet_name: str, sheet_name: str, drive_folder_id: Optional[str] = None) -> Dict[str, Any]:
        # (Lógica idéntica a versiones anteriores)
        try:
            logger.info("--- INICIANDO CICLO DE SCRAPING ---")
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
                    
                    logger.info(f"Procesando: {product_name}")
                    reviews = await self.scrape_product_reviews(product_url, product_name)
                    
                    if reviews:
                        sheet_title = self._sanitize_sheet_name(product_name)
                        self.drive_handler.save_reviews_to_new_sheet(spreadsheet_name, sheet_title, reviews)
                        msg = f"OK: {sheet_title} ({len(reviews)} reseñas)"
                    else:
                        msg = "Falló: 0 reseñas (Posible bloqueo o selector)"
                        
                    logger.info(f"Resultado: {msg}")
                    self.drive_handler.update_cell(spreadsheet_name, sheet_name, idx, column_letter, msg)
                    results.append({'producto': product_name, 'count': len(reviews)})
                    
                    # Pausa aleatoria para parecer humano
                    await asyncio.sleep(random.uniform(3, 6))
                    
                except Exception as e:
                    logger.error(f"Error item: {e}")
                    continue
            return {'status': 'success', 'results': results}
        except Exception as e:
            logger.error(f"Error general: {e}")
            raise

    async def scrape_product_reviews(self, product_url: str, product_name: str) -> List[Dict[str, Any]]:
        marketplace = self._detect_marketplace(product_url)
        if marketplace == 'mercadolibre':
            return await self._scrape_mercadolibre_selenium(product_url)
        elif marketplace == 'amazon':
             return await self._scrape_mercadolibre_selenium(product_url) # Reusa lógica ML por ahora
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
            logger.info("Lanzando navegador...")
            driver = webdriver.Chrome(service=self.chrome_service, options=self.chrome_options)
            
            # Script para evadir detección de webdriver
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info(f"Navegando a: {url[:60]}...")
            driver.get(url)
            time.sleep(random.uniform(3, 5))
            
            # DEBUG: Ver título para saber si cargó bien
            logger.info(f"Título de página: {driver.title}")

            # 1. INTENTAR IR A "VER TODAS"
            reviews_url = None
            try:
                # Buscar en el DOM enlaces relevantes
                # ML suele usar 'ui-pdp-reviews__see-more'
                links = driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    h = link.get_attribute('href')
                    if h and ('/reviews/' in h or 'opiniones' in h):
                        reviews_url = h
                        break
            except: pass

            if reviews_url:
                logger.info("Enlace 'Ver todas' encontrado. Navegando...")
                driver.get(reviews_url)
                time.sleep(3)
                
                # Scroll para cargar
                for _ in range(5):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.5)
            else:
                logger.warning("No se halló enlace 'Ver todas'. Usando página principal.")
                # Si estamos en la página principal, debemos bajar hasta las opiniones para que carguen
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 1000);")
                time.sleep(2)

            # 2. EXTRACCIÓN CON SELECTORES AMPLIOS
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Lista de selectores de ML (viejos y nuevos)
            selectors = [
                'article.ui-review-card',             # ML Página reseñas
                'div.ui-review-card',                 # Variación
                'div.ui-pdp-reviews__comments__content', # ML Página producto
                'div.ui-pdp-reviews__comments',       # ML Contenedor general
                'div[class*="review-card"]',          # Genérico
            ]
            
            cards = []
            for sel in selectors:
                found = soup.select(sel)
                if found:
                    logger.info(f"Selector exitoso: '{sel}' - Encontrados: {len(found)}")
                    cards = found
                    break
            
            if not cards:
                logger.error("DEBUG: HTML Dump (Primeros 500 chars):")
                logger.error(soup.prettify()[:500])

            for card in cards:
                try:
                    # Contenido
                    content = self._extract_text(card, ['p'], re.compile('content|text|comment'))
                    if not content: content = card.get_text(" ", strip=True)[:500]
                    
                    # Evitar tarjetas vacías o de carga
                    if len(content) < 5: continue

                    # Rating
                    rating = 5.0
                    stars = card.select('svg.ui-review-capability__rating__icon')
                    if stars: rating = float(len(stars))
                    
                    # Fecha
                    date = self._extract_text(card, ['time', 'span'], re.compile('date|created'))
                    
                    reviews.append({
                        'contenido': content,
                        'rating': rating,
                        'fecha': date,
                        'autor': "Usuario ML",
                        'titulo': self._extract_text(card, ['h4'], re.compile('title')),
                        'marketplace': 'Mercado Libre'
                    })
                except: continue

        except Exception as e:
            logger.error(f"Error Selenium: {e}")
        finally:
            if driver: driver.quit()
        
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
        return name[:95].strip()