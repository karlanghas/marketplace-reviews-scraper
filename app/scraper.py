"""
Módulo para scraping de reseñas de marketplace (Fixed Processing Logic)
"""
import asyncio
import json
from typing import List, Dict, Optional, Any
import re
from urllib.parse import urlparse
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
        chrome_options.add_argument('--headless') 
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        return chrome_options
    
    async def scrape_from_spreadsheet(self, spreadsheet_name: str, sheet_name: str, drive_folder_id: Optional[str] = None) -> Dict[str, Any]:
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
                    await asyncio.sleep(random.uniform(3, 5))
                    
                except Exception as e:
                    logger.error(f"Error item {idx}: {e}")
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
             return await self._scrape_mercadolibre_selenium(product_url)
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
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            driver.get(url)
            time.sleep(random.uniform(2, 4))
            logger.info(f"Página cargada: {driver.title[:40]}...")

            reviews_url = None
            try:
                links = driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    h = link.get_attribute('href')
                    if h and ('/reviews/' in h or 'opiniones' in h):
                        if 'todas' in link.text.lower() or 'all' in link.text.lower():
                            reviews_url = h
                            break
                        if not reviews_url: reviews_url = h
            except: pass

            if reviews_url:
                logger.info("Navegando a página de reseñas...")
                driver.get(reviews_url)
                time.sleep(3)
                for _ in range(6):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.5)
            else:
                logger.warning("No se halló link reseñas, usando página principal.")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(2)

            # PARSEO
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Buscar contenedores de estrellas
            star_containers = soup.find_all(class_=re.compile(r'rating|stars'))
            potential_cards = []
            
            for star_box in star_containers:
                parent = star_box.find_parent('article')
                if not parent:
                    parent = star_box.find_parent('div', class_=re.compile(r'card|review|content'))
                
                if parent and parent not in potential_cards:
                    if len(parent.get_text(strip=True)) > 20: 
                        potential_cards.append(parent)

            if not potential_cards:
                logger.info("Estrategia estrellas falló, buscando etiquetas <article>...")
                potential_cards = soup.find_all('article')

            logger.info(f"Candidatos a reseña encontrados: {len(potential_cards)}")

            # --- CORRECCIÓN EN EL BUCLE DE PROCESAMIENTO ---
            success_count = 0
            for i, card in enumerate(potential_cards):
                try:
                    full_text = card.get_text(" ", strip=True)
                    if len(full_text) < 10: continue

                    # 1. Extracción de Contenido (Blindada)
                    content = self._extract_text(card, ['p'], re.compile('content|text|comment'))
                    if not content:
                        # Fallback: tomamos todo el texto pero cortamos headers comunes
                        content = full_text[:800]

                    # 2. Rating (Simplificado para evitar errores de int())
                    rating = 5.0
                    try:
                        svgs = card.find_all('svg')
                        if svgs:
                            rating = float(len(svgs))
                            if rating > 5: rating = 5.0 # Normalizar
                    except: pass # Si falla contar estrellas, dejamos 5.0 por defecto

                    # 3. Fecha
                    date = self._extract_text(card, ['time', 'span'], re.compile('date|created'))
                    
                    # 4. Título
                    title = self._extract_text(card, ['h4', 'h3'], re.compile('title'))

                    reviews.append({
                        'contenido': content,
                        'rating': rating,
                        'fecha': date,
                        'autor': "Usuario ML", 
                        'titulo': title,
                        'marketplace': 'Mercado Libre'
                    })
                    success_count += 1
                except Exception as e:
                    # Log solo del primer error para no spamear
                    if i == 0: logger.error(f"Error procesando tarjeta individual: {e}")
                    continue
            
            logger.info(f"Procesadas correctamente: {success_count}/{len(potential_cards)}")

            # Deduplicar
            unique_reviews = []
            seen_content = set()
            for r in reviews:
                # Usar los primeros 50 chars como hash simple para deduplicar
                key = r['contenido'][:50]
                if key not in seen_content:
                    seen_content.add(key)
                    unique_reviews.append(r)
            
            return unique_reviews

        except Exception as e:
            logger.error(f"Error Selenium: {e}")
            return [] # Retornar lista vacía en error fatal
        finally:
            if driver: driver.quit()

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