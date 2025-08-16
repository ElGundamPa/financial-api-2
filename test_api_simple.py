#!/usr/bin/env python3
"""
Script simple para probar la API con autenticación correcta
"""

import requests
import json
import os

# Configurar variables de entorno
os.environ["AUTH_MODE"] = "apikey"
os.environ["API_KEYS"] = "mF9zX2q7Lr4pK8yD1sBvWj"
os.environ["CACHE_TTL"] = "3000"

# Configuración
BASE_URL = "http://localhost:8000"
API_KEY = "mF9zX2q7Lr4pK8yD1sBvWj"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_api():
    """Probar la API completa"""
    print("🚀 Probando Financial API...")
    print("=" * 50)
    
    # 1. Health check
    print("🏥 1. Health Check:")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ OK - Versión: {data.get('version')}")
            print(f"   🔧 Auth Mode: {data.get('auth_mode')}")
            print(f"   ⏰ Time: {data.get('time')}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # 2. Endpoint raíz
    print("🏠 2. Endpoint Raíz:")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ OK - {data.get('message')}")
            print(f"   📊 Endpoints disponibles: {len(data.get('endpoints', {}).get('general', {}))}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # 3. API Datos (con autenticación)
    print("🎯 3. Endpoint /api/datos (con autenticación):")
    try:
        response = requests.get(f"{BASE_URL}/api/datos", headers=HEADERS, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ OK - Total items: {data.get('total_items')}")
            
            # Mostrar resumen de cada categoría
            categories = ["forex", "acciones", "criptomonedas", "indices", "materias_primas"]
            for category in categories:
                items = data.get(category, [])
                print(f"   📊 {category}: {len(items)} elementos")
                
                # Mostrar primeros elementos
                for i, item in enumerate(items[:2], 1):
                    symbol = item.get('symbol', 'N/A')
                    change = item.get('change', 'N/A')
                    print(f"      {i}. {symbol} - {change}")
                if len(items) > 2:
                    print(f"      ... y {len(items) - 2} más")
                print()
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   📝 Respuesta: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # 4. Probar sin autenticación (debe fallar)
    print("🔒 4. Probar sin autenticación (debe fallar):")
    try:
        response = requests.get(f"{BASE_URL}/api/datos", timeout=10)
        if response.status_code == 401:
            print("   ✅ Correcto - Autenticación requerida")
        else:
            print(f"   ⚠️  Inesperado: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("=" * 50)
    print("🎉 Pruebas completadas!")

if __name__ == "__main__":
    test_api()
