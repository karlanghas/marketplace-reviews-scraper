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
        """
        Inicializa el handler de Google Drive
        
        Args:
            credentials_path: Ruta al archivo de credenciales de Google
        """
        self.credentials_path = credentials_path
        self.credentials = None
        self.gspread_client = None
        
        self._authenticate()
    
    def _authenticate(self):
        """Autentica con Google APIs"""
        try:
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(
                    f"Archivo de credenciales no encontrado: {self.credentials_path}\n"
                    "Por favor, coloca el archivo resenas-credentials.json en la carpeta credentials/"
                )
            
            # Cargar credenciales
            self.credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            
            # Inicializar servicios (Usamos gspread para manejo fácil de celdas)
            self.gspread_client = gspread.authorize(self.credentials)
            
            logger.info("Autenticación con Google APIs exitosa")
            
        except Exception as e:
            logger.error(f"Error en autenticación con Google: {str(e)}")
            raise
    
    def read_spreadsheet(
        self,
        spreadsheet_name: str,
        sheet_name: str
    ) -> List[Dict[str, Any]]:
        """
        Lee una hoja de cálculo de Google Sheets
        """
        try:
            logger.info(f"Leyendo planilla: {spreadsheet_name} - Hoja: {sheet_name}")
            
            spreadsheet = self.gspread_client.open(spreadsheet_name)
            worksheet = spreadsheet.worksheet(sheet_name)
            
            records = worksheet.get_all_records()
            logger.info(f"Se leyeron {len(records)} registros")
            
            return records
            
        except gspread.exceptions.SpreadsheetNotFound:
            logger.error(f"Planilla no encontrada: {spreadsheet_name}")
            raise ValueError(f"Planilla '{spreadsheet_name}' no encontrada.")
            
        except gspread.exceptions.WorksheetNotFound:
            logger.error(f"Hoja no encontrada: {sheet_name}")
            raise ValueError(f"Hoja '{sheet_name}' no encontrada en la planilla '{spreadsheet_name}'")
            
        except Exception as e:
            logger.error(f"Error al leer planilla: {str(e)}")
            raise
    
    def update_cell(
        self,
        spreadsheet_name: str,
        sheet_name: str,
        row: int,
        column: str,
        value: str
    ):
        """
        Actualiza una celda específica en Google Sheets
        """
        try:
            spreadsheet = self.gspread_client.open(spreadsheet_name)
            worksheet = spreadsheet.worksheet(sheet_name)
            
            cell = f"{column}{row}"
            # Uso de update compatible con versiones recientes
            worksheet.update(range_name=cell, values=[[value]])
            
        except Exception as e:
            logger.error(f"Error al actualizar celda: {str(e)}")
            raise
    
    def find_column_letter(
        self,
        spreadsheet_name: str,
        sheet_name: str,
        column_name: str
    ) -> str:
        """
        Encuentra la letra de columna dado el nombre del encabezado
        """
        try:
            spreadsheet = self.gspread_client.open(spreadsheet_name)
            worksheet = spreadsheet.worksheet(sheet_name)
            
            headers = worksheet.row_values(1)
            
            if column_name in headers:
                col_index = headers.index(column_name) + 1
                return self._column_number_to_letter(col_index)
            else:
                # Si no encuentra la columna, usamos una por defecto lejana (E) para no romper el flujo
                logger.warning(f"Columna '{column_name}' no encontrada, usando columna E por defecto")
                return "E"
                
        except Exception as e:
            logger.error(f"Error al buscar columna: {str(e)}")
            raise

    def save_reviews_to_new_sheet(
        self, 
        spreadsheet_name: str, 
        new_sheet_name: str, 
        reviews: List[Dict[str, Any]]
    ) -> str:
        """
        Crea una nueva hoja para el producto y escribe las reseñas.
        Columnas: A: Reseña, B: Rating, C: Fecha, D: Usuario, E: Titulo, F: Marketplace
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
                # Creamos hoja con suficientes filas
                worksheet = spreadsheet.add_worksheet(title=new_sheet_name, rows=len(reviews)+20, cols=7)
            
            # 2. Preparar los datos
            headers = ['Reseña', 'Rating', 'Fecha', 'Usuario', 'Titulo', 'Marketplace']
            rows_to_write = [headers]
            
            for r in reviews:
                row = [
                    str(r.get('contenido', ''))[:4000], 
                    str(r.get('rating', '') or ''),
                    str(r.get('fecha', '') or ''),
                    str(r.get('autor', '') or ''),
                    str(r.get('titulo', '') or ''),
                    str(r.get('marketplace', '') or '')
                ]
                rows_to_write.append(row)
            
            logger.info(f"Escribiendo {len(rows_to_write)} filas en la hoja '{new_sheet_name}'...")

            # 3. Escribir datos usando Argumentos con Nombre
            # IMPORTANTE: Usamos range_name y values para evitar errores de versión en gspread
            worksheet.update(range_name='A1', values=rows_to_write)
            
            # 4. Formato visual básico
            try:
                worksheet.format('A1:F1', {'textFormat': {'bold': True}})
            except Exception:
                pass # Ignorar errores de formato si ocurren

            return new_sheet_name
            
        except Exception as e:
            logger.error(f"Error guardando reseñas en hoja nueva: {str(e)}")
            raise
    
    @staticmethod
    def _column_number_to_letter(n: int) -> str:
        """
        Convierte número de columna a letra (1 = A, 2 = B, etc.)
        """
        string = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            string = chr(65 + remainder) + string
        return string