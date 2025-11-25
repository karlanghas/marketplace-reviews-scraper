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
        Crea una nueva hoja para el producto y escribe las reseñas.
        Columnas: A: Reseña, B: Rating, C: Fecha, D: Usuario
        """
        try:
            spreadsheet = self.gspread_client.open(spreadsheet_name)
            
            # 1. Gestionar la hoja (Crear o Limpiar)
            try:
                worksheet = spreadsheet.worksheet(new_sheet_name)
                logger.info(f"La hoja '{new_sheet_name}' ya existe. Limpiando contenido anterior.")
                worksheet.clear()
            except gspread.exceptions.WorksheetNotFound:
                logger.info(f"Creando nueva hoja: {new_sheet_name}")
                # Creamos hoja con suficientes filas para las reseñas
                worksheet = spreadsheet.add_worksheet(title=new_sheet_name, rows=len(reviews)+20, cols=6)
            
            # 2. Preparar los datos (Matriz de filas y columnas)
            headers = ['Reseña', 'Rating', 'Fecha', 'Usuario', 'Titulo', 'Marketplace']
            rows_to_write = [headers]
            
            for r in reviews:
                # Nos aseguramos de manejar valores None convirtiéndolos a string vacío
                row = [
                    str(r.get('contenido', ''))[:4000], # Col A
                    str(r.get('rating', '') or ''),     # Col B
                    str(r.get('fecha', '') or ''),      # Col C
                    str(r.get('autor', '') or ''),      # Col D
                    str(r.get('titulo', '') or ''),     # Col E
                    str(r.get('marketplace', '') or '') # Col F
                ]
                rows_to_write.append(row)
            
            logger.info(f"Escribiendo {len(rows_to_write)} filas en la hoja '{new_sheet_name}'...")

            # 3. Escribir datos usando Argumentos con Nombre (Compatible con v5 y v6 de gspread)
            # Esto evita el error de orden de parámetros
            worksheet.update(range_name='A1', values=rows_to_write)
            
            # 4. Formato visual (Opcional: Negrita encabezados y ancho columna A)
            try:
                worksheet.format('A1:F1', {'textFormat': {'bold': True}})
                worksheet.set_column_width(0, 400) # Columna A más ancha para leer reseñas
            except Exception as e:
                logger.warning(f"No se pudo aplicar formato visual (no crítico): {e}")

            return new_sheet_name
            
        except Exception as e:
            logger.error(f"Error CRÍTICO guardando reseñas en hoja nueva: {str(e)}")
            raise
            
    @staticmethod
    def _column_number_to_letter(n: int) -> str:
        string = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            string = chr(65 + remainder) + string
        return string