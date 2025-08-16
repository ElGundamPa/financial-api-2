#!/usr/bin/env python3
"""
Script para ver exactamente qué datos está devolviendo la API
"""

import requests
import json

# Configuración
BASE_URL = "http://localhost:8000"
API_KEY = "mF9zX2q7Lr4pK8yD1sBvWj"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_detailed_data():
    """Ver datos detallados de la API"""
    print("🔍 Analizando datos detallados de la API...")
    try:
        response = requests.get(f"{BASE_URL}/api/datos", headers=HEADERS, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Datos obtenidos exitosamente")
            print("\n" + "="*60)
            print("📊 DATOS DETALLADOS DE LA API")
            print("="*60)
            
            # Mostrar cada categoría con todos sus elementos
            categories = ["forex", "acciones", "criptomonedas", "indices", "materias_primas"]
            
            for category in categories:
                print(f"\n🪙 {category.upper()}:")
                if category in data and data[category]:
                    items = data[category]
                    print(f"   Total: {len(items)} elementos")
                    for i, item in enumerate(items, 1):
                        symbol = item.get('symbol', 'N/A')
                        name = item.get('name', 'N/A')
                        change = item.get('change', 'N/A')
                        price = item.get('price', 'N/A')
                        print(f"   {i}. {symbol} - {name} - {change} - Precio: {price}")
                else:
                    print(f"   ❌ No hay datos para {category}")
            
            # Mostrar metadatos
            print(f"\n📈 Total items: {data.get('total_items', 0)}")
            print(f"⏰ Timestamp: {data.get('timestamp', 0)}")
            print(f"📝 Note: {data.get('note', 'N/A')}")
            
            # Verificar si son datos reales o de fallback
            if data.get('note') == 'Datos de fallback - error en scraping':
                print("\n⚠️  ATENCIÓN: Se están devolviendo datos de fallback")
                print("   Esto significa que el scraping no está funcionando correctamente")
            else:
                print("\n✅ Se están devolviendo datos reales del scraping")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_scraper_directly():
    """Probar el scraper directamente"""
    print("\n🔧 Probando scraper directamente...")
    try:
        # Importar y ejecutar el scraper
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from api.scraper_simple import scrape_all_data
        import asyncio
        
        print("🔄 Ejecutando scraper...")
        result = asyncio.run(scrape_all_data())
        
        print("📊 Resultado del scraper:")
        print(json.dumps(result, indent=2, default=str))
        
        return True
    except Exception as e:
        print(f"❌ Error en scraper: {e}")
        return False

if __name__ == "__main__":
    test_detailed_data()
    test_scraper_directly()
