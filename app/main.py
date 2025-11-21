"""
Aplicación principal para scraping de reseñas de marketplace
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import logging
from loguru import logger
import sys

from app.scraper import ReviewScraper
from app.google_drive_handler import GoogleDriveHandler

# Configurar logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "/app/logs/app.log",
    rotation="500 MB",
    retention="10 days",
    level="DEBUG"
)

app = FastAPI(
    title="Marketplace Reviews Scraper API",
    description="API para extraer reseñas de productos de marketplace y guardarlas en Google Drive",
    version="1.0.0"
)

class ScrapingRequest(BaseModel):
    """Modelo de datos para la solicitud de scraping"""
    spreadsheet_name: str
    sheet_name: str
    drive_folder_id: Optional[str] = None

class ScrapingResponse(BaseModel):
    """Modelo de respuesta del scraping"""
    status: str
    message: str
    task_id: Optional[str] = None
    products_processed: Optional[int] = None
    files_created: Optional[list] = None

# Almacenamiento temporal de tareas
tasks_status = {}

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "Marketplace Reviews Scraper",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/scrape", response_model=ScrapingResponse)
async def scrape_reviews(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks
):
    """
    Endpoint principal para iniciar el scraping de reseñas
    
    Args:
        request: ScrapingRequest con el nombre de la planilla y la hoja
        background_tasks: Gestor de tareas en background
        
    Returns:
        ScrapingResponse con el estado del proceso
    """
    try:
        logger.info(f"Recibida solicitud de scraping para: {request.spreadsheet_name} - {request.sheet_name}")
        
        # Inicializar handlers
        drive_handler = GoogleDriveHandler()
        scraper = ReviewScraper(drive_handler)
        
        # Generar task_id
        import uuid
        task_id = str(uuid.uuid4())
        tasks_status[task_id] = {"status": "processing", "progress": 0}
        
        # Agregar tarea en background
        background_tasks.add_task(
            process_scraping,
            task_id=task_id,
            spreadsheet_name=request.spreadsheet_name,
            sheet_name=request.sheet_name,
            drive_folder_id=request.drive_folder_id,
            scraper=scraper,
            drive_handler=drive_handler
        )
        
        return ScrapingResponse(
            status="accepted",
            message="Proceso de scraping iniciado",
            task_id=task_id
        )
        
    except Exception as e:
        logger.error(f"Error al iniciar scraping: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_scraping(
    task_id: str,
    spreadsheet_name: str,
    sheet_name: str,
    drive_folder_id: Optional[str],
    scraper: ReviewScraper,
    drive_handler: GoogleDriveHandler
):
    """
    Procesa el scraping en background
    """
    try:
        logger.info(f"Iniciando proceso de scraping [Task ID: {task_id}]")
        
        # Ejecutar scraping
        result = await scraper.scrape_from_spreadsheet(
            spreadsheet_name=spreadsheet_name,
            sheet_name=sheet_name,
            drive_folder_id=drive_folder_id
        )
        
        # Actualizar estado
        tasks_status[task_id] = {
            "status": "completed",
            "progress": 100,
            "result": result
        }
        
        logger.info(f"Scraping completado exitosamente [Task ID: {task_id}]")
        
    except Exception as e:
        logger.error(f"Error en proceso de scraping [Task ID: {task_id}]: {str(e)}")
        tasks_status[task_id] = {
            "status": "failed",
            "error": str(e)
        }

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Obtiene el estado de una tarea de scraping
    
    Args:
        task_id: ID de la tarea
        
    Returns:
        Estado de la tarea
    """
    if task_id not in tasks_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return tasks_status[task_id]

@app.post("/test-connection")
async def test_connection():
    """
    Prueba la conexión con Google Drive
    """
    try:
        drive_handler = GoogleDriveHandler()
        result = drive_handler.test_connection()
        return {"status": "success", "message": "Conexión exitosa con Google Drive", "details": result}
    except Exception as e:
        logger.error(f"Error al probar conexión: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5050)
