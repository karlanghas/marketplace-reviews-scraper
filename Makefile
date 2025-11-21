.PHONY: help build up down restart logs clean test install

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Ejecuta el script de instalación
	@chmod +x install.sh
	@./install.sh

build: ## Construye la imagen Docker
	@echo "🔨 Construyendo imagen Docker..."
	docker-compose build

up: ## Inicia los servicios
	@echo "🚀 Iniciando servicios..."
	docker-compose up -d
	@echo "✅ Servicios iniciados"
	@make status

down: ## Detiene y elimina los contenedores
	@echo "🛑 Deteniendo servicios..."
	docker-compose down
	@echo "✅ Servicios detenidos"

restart: ## Reinicia los servicios
	@echo "🔄 Reiniciando servicios..."
	docker-compose restart
	@echo "✅ Servicios reiniciados"

logs: ## Muestra los logs en tiempo real
	docker-compose logs -f

status: ## Muestra el estado de los servicios
	@echo "📊 Estado de los servicios:"
	@docker-compose ps
	@echo ""
	@echo "🏥 Health check:"
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ Servicio no responde"

test: ## Prueba la conexión con Google Drive
	@echo "🧪 Probando conexión con Google Drive..."
	@curl -s -X POST http://localhost:8000/test-connection | python3 -m json.tool

clean: ## Limpia logs y cache
	@echo "🧹 Limpiando archivos temporales..."
	@rm -rf logs/*.log
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Limpieza completada"

rebuild: ## Reconstruye la imagen desde cero
	@echo "🔨 Reconstruyendo imagen desde cero..."
	docker-compose build --no-cache
	@echo "✅ Imagen reconstruida"

update: ## Actualiza el código y reinicia
	@echo "🔄 Actualizando código..."
	git pull origin main
	@make rebuild
	@make restart
	@echo "✅ Actualización completada"

credentials: ## Verifica las credenciales de Google
	@echo "🔑 Verificando credenciales..."
	@if [ -f credentials/google-credentials.json ]; then \
		echo "✅ Archivo de credenciales encontrado"; \
		echo ""; \
		echo "📧 Email de la cuenta de servicio:"; \
		cat credentials/google-credentials.json | python3 -c "import sys, json; print(json.load(sys.stdin)['client_email'])"; \
	else \
		echo "❌ Archivo de credenciales no encontrado"; \
		echo "Coloca el archivo en: credentials/google-credentials.json"; \
	fi

backup: ## Crea backup de la configuración
	@echo "💾 Creando backup..."
	@mkdir -p backups
	@tar -czf backups/backup-$(shell date +%Y%m%d-%H%M%S).tar.gz \
		docker-compose.yml \
		.env \
		app/ \
		config/ \
		README.md
	@echo "✅ Backup creado en backups/"

shell: ## Abre una shell en el contenedor
	docker-compose exec marketplace-reviews /bin/bash

python-shell: ## Abre Python shell en el contenedor
	docker-compose exec marketplace-reviews python3

docs: ## Abre la documentación de la API
	@echo "📖 Abriendo documentación..."
	@xdg-open http://localhost:8000/docs 2>/dev/null || open http://localhost:8000/docs 2>/dev/null || echo "Abre: http://localhost:8000/docs"
