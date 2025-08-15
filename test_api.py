#!/usr/bin/env python3
"""
Script de prueba para la Financial API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Probar endpoint de salud"""
    print("🧪 Probando /health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_root():
    """Probar endpoint raíz"""
    print("\n🧪 Probando /...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_sources():
    """Probar endpoint de fuentes"""
    print("\n🧪 Probando /sources...")
    try:
        response = requests.get(f"{BASE_URL}/sources", timeout=10)
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_datos_without_auth():
    """Probar endpoint de datos sin autenticación"""
    print("\n🧪 Probando /datos sin autenticación...")
    try:
        response = requests.get(f"{BASE_URL}/datos", timeout=10)
        print(f"✅ Status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Correcto: Se requiere autenticación")
            return True
        else:
            print(f"❌ Inesperado: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_datos_with_auth():
    """Probar endpoint de datos con autenticación"""
    print("\n🧪 Probando /datos con autenticación...")
    try:
        headers = {"X-API-Key": "mF9zX2q7Lr4pK8yD1sBvWj"}
        response = requests.get(f"{BASE_URL}/datos", headers=headers, timeout=30)
        print(f"✅ Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Datos obtenidos de {data.get('total_sources', 0)} fuentes")
            print(f"✅ Tiempo de scraping: {data.get('scraping_time', 0)}s")
            return True
        else:
            print(f"❌ Error: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_datos_resume():
    """Probar endpoint de resumen"""
    print("\n🧪 Probando /datos/resume...")
    try:
        headers = {"X-API-Key": "mF9zX2q7Lr4pK8yD1sBvWj"}
        response = requests.get(f"{BASE_URL}/datos/resume", headers=headers, timeout=30)
        print(f"✅ Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Resumen obtenido con {len(data.get('indices', []))} índices")
            return True
        else:
            print(f"❌ Error: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 Iniciando pruebas de la Financial API...")
    print("=" * 50)
    
    tests = [
        test_health,
        test_root,
        test_sources,
        test_datos_without_auth,
        test_datos_with_auth,
        test_datos_resume
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(1)  # Pausa entre pruebas
    
    print("\n" + "=" * 50)
    print(f"📊 Resultados: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! La API está funcionando correctamente.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa los errores arriba.")

if __name__ == "__main__":
    main()
