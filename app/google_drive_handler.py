"""
Módulo para interactuar con Google Drive y Google Sheets
"""
import os
import json
from typing import List, Dict, Optional, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
from loguru import logger

class GoogleDriveHandler:
    """Manejador de Google Drive y Google Sheets"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    
    def __init__(self, credentials_path: str = '/app/credentials/resenas_credentials.json'):
        self.credentials_path = credentials_path
        self.credentials = None
        self.gspread_client = None
        
        self._authenticate()
    
    def _authenticate(self):
        """Autentica con Google APIs"""
        try:
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(
                    f"Archivo de credenciales no encontrado: {self.credentials_path}"
                )
            
            self.credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            
            # Usamos gspread principalmente ya que es más fácil para manipular celdas
            self.gspread_client = gspread.authorize(self.credentials)
            
            logger.info("Autenticación con Google APIs exitosa")
            
        except Exception as e:
            logger.error(f"Error en autenticación con Google: {str(e)}")
            raise
    
    def read_spreadsheet(self, spreadsheet_name: str, sheet_name: str) -> List[Dict[str, Any]]:
        """Lee una hoja de cálculo de Google Sheets"""
        try:
            logger.info(f"Leyendo planilla: {spreadsheet_name} - Hoja: {sheet_name}")
            spreadsheet = self.gspread_client.open(spreadsheet_name)
            worksheet = spreadsheet.worksheet(sheet_name)
            records = worksheet.get_all_records()
            return records
        except Exception as e:
            logger.error(f"Error al leer planilla: {str(e)}")
            raise

    def find_column_letter(self, spreadsheet_name: str, sheet_name: str, column_name: str) -> str:
        """Encuentra la letra de columna dado el nombre del encabezado"""
        try:
            spreadsheet = self.gspread_client.open(spreadsheet_name)
            worksheet = spreadsheet.worksheet(sheet_name)
            headers = worksheet.row_values(1)
            
            if column_name in headers:
                col_index = headers.index(column_name) + 1
                return self._column_number_to_letter(col_index)
            else:
                # Si no existe, retornamos None o lanzamos error, 
                # en este caso asumimos que si no existe, usaremos la ultima disponible
                logger.warning(f"Columna {column_name} no encontrada")
                return "Z" # Fallback
                
        except Exception as e:
            logger.error(f"Error al buscar columna: {str(e)}")
            raise

    def update_cell(self, spreadsheet_name: str, sheet_name: str, row: int, column: str, value: str):
        """Actualiza una celda específica"""
        try:
            spreadsheet = self.gspread_client.open(spreadsheet_name)
            worksheet = spreadsheet.worksheet(sheet_name)
            worksheet.update(f"{column}{row}", [[value]])
        except Exception as e:
            logger.error(f"Error al actualizar celda: {str(e)}")
            raise

    def save_reviews_to_new_sheet(
        self, 
        spreadsheet_name: str, 
        new_sheet_name: str, 
        reviews: List[Dict[str, Any]]
    ) -> str:
        """
        Crea una nueva hoja (tab) para el producto y escribe las reseñas.
        Columnas: A: Reseña, B: Rating, C: Fecha, D: Usuario
        """
        try:
            spreadsheet = self.gspread_client.open(spreadsheet_name)
            
            # Intentar obtener la hoja, si no existe, crearla
            try:
                worksheet = spreadsheet.worksheet(new_sheet_name)
                logger.info(f"La hoja '{new_sheet_name}' ya existe. Limpiando contenido anterior.")
                worksheet.clear()
            except gspread.exceptions.WorksheetNotFound:
                logger.info(f"Creando nueva hoja: {new_sheet_name}")
                worksheet = spreadsheet.add_worksheet(title=new_sheet_name, rows=100, cols=10)
            
            # Preparar encabezados
            headers = ['Reseña', 'Rating', 'Fecha', 'Usuario', 'Titulo', 'Marketplace']
            
            # Preparar datos
            rows_to_write = [headers]
            
            for r in reviews:
                row = [
                    r.get('contenido', '')[:4000], # Limite de celda de excel por seguridad
                    r.get('rating', ''),
                    r.get('fecha', ''),
                    r.get('autor', ''),
                    r.get('titulo', ''),
                    r.get('marketplace', '')
                ]
                rows_to_write.append(row)
            
            # Escribir todo de una vez (Batch update)
            worksheet.update(f'A1', rows_to_write)
            
            # Dar formato simple al encabezado (Negrita)
            worksheet.format('A1:F1', {'textFormat': {'bold': True}})
            
            return new_sheet_name
            
        except Exception as e:
            logger.error(f"Error guardando reseñas en hoja nueva: {str(e)}")
            raise

    @staticmethod
    def _column_number_to_letter(n: int) -> str:
        string = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            string = chr(65 + remainder) + string
        return string