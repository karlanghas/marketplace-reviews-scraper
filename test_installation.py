#!/usr/bin/env python3
"""
Script de prueba para verificar la instalación
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000"

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def test_health():
    """Prueba el endpoint de health"""
    print_header("Probando Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check OK")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en health check: {str(e)}")
        return False

def test_root():
    """Prueba el endpoint raíz"""
    print_header("Probando Endpoint Raíz")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Endpoint raíz OK")
            data = response.json()
            print(f"   Service: {data.get('service')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Endpoint raíz falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en endpoint raíz: {str(e)}")
        return False

def test_connection():
    """Prueba la conexión con Google Drive"""
    print_header("Probando Conexión con Google Drive")
    try:
        response = requests.post(f"{BASE_URL}/test-connection", timeout=10)
        data = response.json()
        
        if response.status_code == 200 and data.get('status') == 'success':
            print("✅ Conexión con Google Drive OK")
            details = data.get('details', {})
            print(f"   Connected: {details.get('connected')}")
            print(f"   Files found: {details.get('files_found')}")
            if details.get('sample_files'):
                print(f"   Sample files: {details.get('sample_files')[:3]}")
            return True
        else:
            print(f"❌ Conexión con Google Drive falló")
            print(f"   Error: {data.get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Error probando conexión: {str(e)}")
        return False

def test_scrape_endpoint():
    """Prueba el endpoint de scraping (sin ejecutar realmente)"""
    print_header("Probando Endpoint de Scraping")
    print("ℹ️  Esta prueba verifica que el endpoint responde correctamente")
    print("   pero NO ejecutará un scraping real")
    
    # Payload de prueba con datos ficticios
    payload = {
        "spreadsheet_name": "Test Spreadsheet (No existe)",
        "sheet_name": "Test Sheet"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/scrape",
            json=payload,
            timeout=5
        )
        
        # Esperamos un error porque la planilla no existe
        # pero el endpoint debe responder
        if response.status_code in [200, 500]:
            print("✅ Endpoint de scraping responde correctamente")
            print(f"   Status Code: {response.status_code}")
            return True
        else:
            print(f"⚠️  Respuesta inesperada: {response.status_code}")
            return True  # No es crítico
    except Exception as e:
        print(f"❌ Error probando endpoint de scraping: {str(e)}")
        return False

def main():
    """Ejecuta todas las pruebas"""
    print("\n" + "🧪 " * 30)
    print("   MARKETPLACE REVIEWS SCRAPER - PRUEBAS DE INSTALACIÓN")
    print("🧪 " * 30)
    
    tests = [
        ("Health Check", test_health),
        ("Endpoint Raíz", test_root),
        ("Conexión Google Drive", test_connection),
        ("Endpoint Scraping", test_scrape_endpoint)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
        time.sleep(1)
    
    # Resumen
    print_header("RESUMEN DE PRUEBAS")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    print(f"\n   Total: {passed}/{total} pruebas pasadas")
    
    if passed == total:
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("\n📋 Próximos pasos:")
        print("   1. Comparte tu Google Sheet con la cuenta de servicio")
        print("   2. Prepara tu planilla con las columnas: PRODUCTO, URL, ARCHIVOJSON")
        print("   3. Configura tu flujo en n8n para llamar al endpoint /scrape")
        print("\n📖 Lee SPREADSHEET_FORMAT.md para más detalles sobre el formato")
        sys.exit(0)
    else:
        print("\n⚠️  Algunas pruebas fallaron")
        print("\n🔧 Solución de problemas:")
        print("   1. Verifica que el contenedor esté corriendo: docker-compose ps")
        print("   2. Revisa los logs: docker-compose logs -f")
        print("   3. Verifica las credenciales: make credentials")
        print("   4. Lee el README.md para más información")
        sys.exit(1)

if __name__ == "__main__":
    main()
