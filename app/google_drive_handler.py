"""
Módulo para interactuar con Google Drive y Google Sheets
"""
import os
import json
from typing import List, Dict, Optional, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import gspread
from loguru import logger
import io
from googleapiclient.http import MediaIoBaseUpload

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
        self.drive_service = None
        self.sheets_service = None
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
            
            # Inicializar servicios
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
            self.gspread_client = gspread.authorize(self.credentials)
            
            logger.info("Autenticación con Google APIs exitosa")
            
        except Exception as e:
            logger.error(f"Error en autenticación con Google: {str(e)}")
            raise
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Prueba la conexión con Google Drive
        
        Returns:
            Dict con información de la conexión
        """
        try:
            results = self.drive_service.files().list(
                pageSize=5,
                fields="files(id, name)"
            ).execute()
            
            files = results.get('files', [])
            
            return {
                "connected": True,
                "files_found": len(files),
                "sample_files": [f['name'] for f in files]
            }
            
        except Exception as e:
            logger.error(f"Error al probar conexión: {str(e)}")
            return {
                "connected": False,
                "error": str(e)
            }
    
    def read_spreadsheet(
        self,
        spreadsheet_name: str,
        sheet_name: str
    ) -> List[Dict[str, Any]]:
        """
        Lee una hoja de cálculo de Google Sheets
        
        Args:
            spreadsheet_name: Nombre de la planilla
            sheet_name: Nombre de la hoja
            
        Returns:
            Lista de diccionarios con los datos
        """
        try:
            logger.info(f"Leyendo planilla: {spreadsheet_name} - Hoja: {sheet_name}")
            
            # Abrir planilla
            spreadsheet = self.gspread_client.open(spreadsheet_name)
            worksheet = spreadsheet.worksheet(sheet_name)
            
            # Obtener todos los registros
            records = worksheet.get_all_records()
            
            logger.info(f"Se leyeron {len(records)} registros")
            
            return records
            
        except gspread.exceptions.SpreadsheetNotFound:
            logger.error(f"Planilla no encontrada: {spreadsheet_name}")
            raise ValueError(f"Planilla '{spreadsheet_name}' no encontrada. Verifica que la cuenta de servicio tenga acceso.")
            
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
        
        Args:
            spreadsheet_name: Nombre de la planilla
            sheet_name: Nombre de la hoja
            row: Número de fila (1-indexed)
            column: Letra de columna (ej: 'A', 'B', 'C')
            value: Valor a escribir
        """
        try:
            spreadsheet = self.gspread_client.open(spreadsheet_name)
            worksheet = spreadsheet.worksheet(sheet_name)
            
            # Actualizar celda
            cell = f"{column}{row}"
            worksheet.update(cell, value)
            
            logger.debug(f"Celda {cell} actualizada con: {value}")
            
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
        
        Args:
            spreadsheet_name: Nombre de la planilla
            sheet_name: Nombre de la hoja
            column_name: Nombre de la columna
            
        Returns:
            Letra de la columna
        """
        try:
            spreadsheet = self.gspread_client.open(spreadsheet_name)
            worksheet = spreadsheet.worksheet(sheet_name)
            
            # Obtener primera fila (encabezados)
            headers = worksheet.row_values(1)
            
            # Buscar columna
            if column_name in headers:
                col_index = headers.index(column_name) + 1
                # Convertir índice a letra
                return self._column_number_to_letter(col_index)
            else:
                raise ValueError(f"Columna '{column_name}' no encontrada")
                
        except Exception as e:
            logger.error(f"Error al buscar columna: {str(e)}")
            raise
    
    @staticmethod
    def _column_number_to_letter(n: int) -> str:
        """
        Convierte número de columna a letra (1 = A, 2 = B, etc.)
        
        Args:
            n: Número de columna
            
        Returns:
            Letra de columna
        """
        string = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            string = chr(65 + remainder) + string
        return string
    
    def upload_json_file(
        self,
        json_data: Dict[str, Any],
        file_name: str,
        folder_id: Optional[str] = None
    ) -> str:
        """
        Sube un archivo JSON a Google Drive
        
        Args:
            json_data: Datos en formato JSON
            file_name: Nombre del archivo
            folder_id: ID de la carpeta de destino (opcional)
            
        Returns:
            ID del archivo creado
        """
        try:
            # Convertir JSON a string
            json_string = json.dumps(json_data, indent=2, ensure_ascii=False)
            
            # Crear archivo en memoria
            file_metadata = {'name': file_name}
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Crear MediaIoBaseUpload
            fh = io.BytesIO(json_string.encode('utf-8'))
            media = MediaIoBaseUpload(
                fh,
                mimetype='application/json',
                resumable=True
            )
            
            # Subir archivo
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            logger.info(f"Archivo JSON subido: {file.get('name')} (ID: {file.get('id')})")
            
            return file.get('id')
            
        except Exception as e:
            logger.error(f"Error al subir archivo JSON: {str(e)}")
            raise
    
    def get_folder_id_from_spreadsheet(
        self,
        spreadsheet_name: str
    ) -> Optional[str]:
        """
        Obtiene el ID de la carpeta donde está ubicada la planilla
        
        Args:
            spreadsheet_name: Nombre de la planilla
            
        Returns:
            ID de la carpeta o None
        """
        try:
            # Buscar archivo
            query = f"name='{spreadsheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"
            results = self.drive_service.files().list(
                q=query,
                fields='files(id, parents)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                parents = files[0].get('parents', [])
                if parents:
                    return parents[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error al obtener carpeta: {str(e)}")
            return None
