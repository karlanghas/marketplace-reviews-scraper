#!/bin/bash

# Healthcheck script para Docker
# Este script verifica que la aplicación esté funcionando correctamente

set -e

# URL del health endpoint
HEALTH_URL="http://localhost:8000/health"

# Realizar request
response=$(curl -sf "$HEALTH_URL" || echo "failed")

# Verificar respuesta
if [ "$response" = "failed" ]; then
    echo "Health check failed: No response from API"
    exit 1
fi

# Verificar que el JSON contiene "status": "healthy"
if echo "$response" | grep -q '"status":"healthy"'; then
    exit 0
else
    echo "Health check failed: Unexpected response: $response"
    exit 1
fi
