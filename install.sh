#!/bin/bash

# Script de instalación para Marketplace Reviews Scraper
# Para Raspberry Pi 5

set -e

echo "🚀 Instalando Marketplace Reviews Scraper..."
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar si está en Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo -e "${YELLOW}⚠️  Advertencia: No se detectó Raspberry Pi${NC}"
fi

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado${NC}"
    echo "Instala Docker primero: https://docs.docker.com/engine/install/"
    exit 1
fi

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose no está instalado${NC}"
    echo "Instalando Docker Compose..."
    sudo apt-get update
    sudo apt-get install -y docker-compose
fi

echo -e "${GREEN}✓ Docker y Docker Compose están instalados${NC}"
echo ""

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p credentials
mkdir -p logs
mkdir -p config

echo -e "${GREEN}✓ Directorios creados${NC}"
echo ""

# Verificar credenciales de Google
if [ ! -f "credentials/google-credentials.json" ]; then
    echo -e "${YELLOW}⚠️  No se encontró credentials/google-credentials.json${NC}"
    echo ""
    echo "Para continuar, necesitas:"
    echo "1. Crear una cuenta de servicio en Google Cloud Console"
    echo "2. Habilitar Google Drive API y Google Sheets API"
    echo "3. Descargar el archivo JSON de credenciales"
    echo "4. Guardarlo como: credentials/google-credentials.json"
    echo ""
    read -p "¿Ya tienes el archivo? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Ruta del archivo de credenciales: " CRED_PATH
        if [ -f "$CRED_PATH" ]; then
            cp "$CRED_PATH" credentials/google-credentials.json
            echo -e "${GREEN}✓ Credenciales copiadas${NC}"
        else
            echo -e "${RED}❌ Archivo no encontrado${NC}"
            exit 1
        fi
    else
        echo ""
        echo "Instrucciones detalladas en README.md"
        echo "Ejecuta este script nuevamente cuando tengas las credenciales"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Credenciales de Google encontradas${NC}"
echo ""

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    echo "📝 Creando archivo .env..."
    cp .env.example .env
    echo -e "${GREEN}✓ Archivo .env creado${NC}"
else
    echo -e "${GREEN}✓ Archivo .env ya existe${NC}"
fi
echo ""

# Construir imagen Docker
echo "🔨 Construyendo imagen Docker..."
echo "Esto puede tomar varios minutos en Raspberry Pi..."
docker-compose build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Imagen Docker construida exitosamente${NC}"
else
    echo -e "${RED}❌ Error al construir la imagen${NC}"
    exit 1
fi
echo ""

# Iniciar servicios
echo "🚀 Iniciando servicios..."
docker-compose up -d

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Servicios iniciados${NC}"
else
    echo -e "${RED}❌ Error al iniciar servicios${NC}"
    exit 1
fi
echo ""

# Esperar a que el servicio esté listo
echo "⏳ Esperando a que el servicio esté listo..."
sleep 10

# Verificar salud
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

if [ "$HEALTH_CHECK" == "200" ]; then
    echo -e "${GREEN}✓ Servicio funcionando correctamente${NC}"
else
    echo -e "${YELLOW}⚠️  El servicio puede estar iniciándose todavía${NC}"
    echo "Verifica con: docker-compose logs -f"
fi
echo ""

# Mostrar información
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Instalación completada${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 API disponible en: http://localhost:8000"
echo "📖 Documentación: http://localhost:8000/docs"
echo ""
echo "Comandos útiles:"
echo "  docker-compose logs -f    # Ver logs"
echo "  docker-compose restart    # Reiniciar"
echo "  docker-compose stop       # Detener"
echo "  docker-compose down       # Detener y remover"
echo ""
echo "📋 Próximos pasos:"
echo "1. Comparte tu Google Sheet con el email de la cuenta de servicio"
echo "   (Busca 'client_email' en credentials/google-credentials.json)"
echo "2. Prepara tu planilla con las columnas: PRODUCTO, URL, ARCHIVOJSON"
echo "3. Configura tu flujo en n8n para llamar a: http://tu-ip:8000/scrape"
echo ""
echo "Para más información, lee el README.md"
echo ""
