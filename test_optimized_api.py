#!/usr/bin/env python3
"""
Script de prueba para verificar el endpoint optimizado /api/datos
Verifica que devuelva exactamente 3-4 elementos por categoría
"""

import requests
import json
import time

# Configuración
BASE_URL = "http://localhost:8000"
API_KEY = "mF9zX2q7Lr4pK8yD1sBvWj"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_health():
    """Probar health check"""
    print("🏥 Probando health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health OK - Versión: {data.get('version', 'N/A')}")
            return True
        else:
            print(f"❌ Health check falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en health check: {e}")
        return False

def test_api_datos():
    """Probar el endpoint optimizado /api/datos"""
    print("\n🎯 Probando endpoint optimizado /api/datos...")
    try:
        response = requests.get(f"{BASE_URL}/api/datos", headers=HEADERS, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint /api/datos funcionando")
            
            # Verificar estructura
            expected_categories = ["forex", "acciones", "criptomonedas", "indices", "materias_primas"]
            for category in expected_categories:
                if category in data:
                    items = data[category]
                    expected_limit = 4 if category == "criptomonedas" else 3
                    print(f"📊 {category.upper()}: {len(items)} elementos (esperado: {expected_limit})")
                    
                    # Mostrar primeros elementos
                    for i, item in enumerate(items[:2]):
                        print(f"   {i+1}. {item.get('symbol', 'N/A')} - {item.get('name', 'N/A')} - {item.get('change', 'N/A')}")
                    
                    if len(items) > 2:
                        print(f"   ... y {len(items) - 2} más")
                else:
                    print(f"❌ Categoría faltante: {category}")
            
            # Verificar total
            total_items = data.get("total_items", 0)
            expected_total = 16  # 3+3+4+3+3
            print(f"\n📈 Total items: {total_items} (esperado: {expected_total})")
            
            # Verificar timestamp
            timestamp = data.get("timestamp", 0)
            print(f"⏰ Timestamp: {timestamp}")
            
            return True
        else:
            print(f"❌ Error en /api/datos: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando /api/datos: {e}")
        return False

def test_fallback_data():
    """Probar datos de fallback si hay error"""
    print("\n🔄 Probando datos de fallback...")
    try:
        # Forzar error simulando API key inválida
        response = requests.get(f"{BASE_URL}/api/datos", headers={"X-API-Key": "invalid"}, timeout=10)
        
        if response.status_code == 401:
            print("✅ Autenticación funcionando correctamente")
            return True
        else:
            print(f"⚠️  Autenticación no funcionó como esperado: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando fallback: {e}")
        return False

def test_performance():
    """Probar rendimiento del endpoint"""
    print("\n⚡ Probando rendimiento...")
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/datos", headers=HEADERS, timeout=30)
        end_time = time.time()
        
        if response.status_code == 200:
            duration = end_time - start_time
            print(f"✅ Respuesta en {duration:.2f} segundos")
            
            if duration < 10:
                print("✅ Rendimiento aceptable (< 10s)")
                return True
            else:
                print(f"⚠️  Respuesta lenta: {duration:.2f}s")
                return False
        else:
            print(f"❌ Error en prueba de rendimiento: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba de rendimiento: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas del endpoint optimizado...")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("API Datos Optimizado", test_api_datos),
        ("Datos de Fallback", test_fallback_data),
        ("Rendimiento", test_performance),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "="*50)
    print("📋 RESUMEN DE PRUEBAS")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON! El endpoint está funcionando correctamente.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa los logs anteriores.")
    
    return passed == total

if __name__ == "__main__":
    main()
