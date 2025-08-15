#!/usr/bin/env python3
"""
Script de prueba para el endpoint simplificado /api/datos
"""

import requests
import json
import time

# Configuración
BASE_URL = "http://localhost:8000"
API_KEY = "mF9zX2q7Lr4pK8yD1sBvWj"
HEADERS = {"X-API-Key": API_KEY}

def test_api_datos():
    """Probar el endpoint simplificado /api/datos"""
    print("🚀 Probando endpoint simplificado /api/datos...")
    print("=" * 60)
    
    try:
        # Probar sin autenticación (debe fallar)
        print("🧪 Probando sin autenticación...")
        response = requests.get(f"{BASE_URL}/api/datos")
        if response.status_code == 401:
            print("✅ Correcto: Se requiere autenticación")
        else:
            print(f"❌ Error: Debería requerir autenticación, pero devolvió {response.status_code}")
        
        # Probar con autenticación
        print("\n🧪 Probando con autenticación...")
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/datos", headers=HEADERS)
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Status: 200")
            print(f"✅ Tiempo de respuesta: {end_time - start_time:.2f}s")
            print(f"✅ Total de items: {data.get('total_items', 0)}")
            print(f"✅ Timestamp: {data.get('timestamp', 'N/A')}")
            
            # Mostrar estadísticas por categoría
            print("\n📊 Estadísticas por categoría:")
            for category in ['forex', 'acciones', 'criptomonedas', 'indices', 'materias_primas']:
                items = data.get(category, [])
                print(f"   • {category.upper()}: {len(items)} items")
                if items:
                    print(f"     Ejemplo: {items[0]}")
            
            # Mostrar headers CORS
            print(f"\n🌐 Headers CORS:")
            cors_header = response.headers.get('Access-Control-Allow-Origin')
            if cors_header:
                print(f"   • Access-Control-Allow-Origin: {cors_header}")
            else:
                print("   • CORS headers no encontrados")
                
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(f"❌ Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

def test_cors():
    """Probar CORS con una petición OPTIONS"""
    print("\n🌐 Probando CORS...")
    print("=" * 60)
    
    try:
        # Simular petición preflight OPTIONS
        headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-API-Key"
        }
        
        response = requests.options(f"{BASE_URL}/api/datos", headers=headers)
        
        print(f"✅ Status OPTIONS: {response.status_code}")
        print(f"✅ Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'No encontrado')}")
        print(f"✅ Access-Control-Allow-Methods: {response.headers.get('Access-Control-Allow-Methods', 'No encontrado')}")
        print(f"✅ Access-Control-Allow-Headers: {response.headers.get('Access-Control-Allow-Headers', 'No encontrado')}")
        
    except Exception as e:
        print(f"❌ Error probando CORS: {e}")

def test_sample_data():
    """Mostrar una muestra de los datos"""
    print("\n📋 Muestra de datos...")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/datos", headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            
            for category in ['forex', 'acciones', 'criptomonedas', 'indices', 'materias_primas']:
                items = data.get(category, [])
                if items:
                    print(f"\n🔸 {category.upper()} (primeros 3 items):")
                    for i, item in enumerate(items[:3]):
                        print(f"   {i+1}. {item.get('symbol', 'N/A')} - {item.get('name', 'N/A')} - {item.get('change', 'N/A')}")
                else:
                    print(f"\n🔸 {category.upper()}: Sin datos")
                    
    except Exception as e:
        print(f"❌ Error obteniendo muestra: {e}")

if __name__ == "__main__":
    print("🎯 PRUEBAS DEL ENDPOINT SIMPLIFICADO /api/datos")
    print("=" * 60)
    
    test_api_datos()
    test_cors()
    test_sample_data()
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas")
    print("\n📝 Resumen del endpoint /api/datos:")
    print("   • URL: http://localhost:8000/api/datos")
    print("   • Método: GET")
    print("   • Autenticación: X-API-Key header")
    print("   • CORS: Habilitado")
    print("   • Formato: JSON unificado")
    print("   • Categorías: forex, acciones, criptomonedas, indices, materias_primas")
