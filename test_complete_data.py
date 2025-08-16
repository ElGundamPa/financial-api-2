#!/usr/bin/env python3
"""
Script para probar los datos completos con precio, máximo, mínimo y volumen
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

def test_complete_data():
    """Probar datos completos con todos los campos"""
    print("🔍 Probando datos completos con precio, máximo, mínimo y volumen...")
    print("=" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/api/datos", headers=HEADERS, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Datos obtenidos exitosamente")
            print(f"📊 Total items: {data.get('total_items', 0)}")
            print(f"⏰ Timestamp: {data.get('timestamp', 0)}")
            print()
            
            # Mostrar cada categoría con todos los campos
            categories = ["forex", "acciones", "criptomonedas", "indices", "materias_primas"]
            
            for category in categories:
                print(f"🪙 {category.upper()}:")
                if category in data and data[category]:
                    items = data[category]
                    print(f"   Total: {len(items)} elementos")
                    for i, item in enumerate(items, 1):
                        symbol = item.get('symbol', 'N/A')
                        name = item.get('name', 'N/A')
                        change = item.get('change', 'N/A')
                        price = item.get('price', 'N/A')
                        max_24h = item.get('max_24h', 'N/A')
                        min_24h = item.get('min_24h', 'N/A')
                        volume_24h = item.get('volume_24h', 'N/A')
                        
                        print(f"   {i}. {symbol} - {name}")
                        print(f"      💰 Precio: ${price}")
                        print(f"      📈 Cambio: {change}")
                        print(f"      🔺 Máximo 24h: ${max_24h}")
                        print(f"      🔻 Mínimo 24h: ${min_24h}")
                        print(f"      📊 Volumen 24h: {volume_24h}")
                        print()
                else:
                    print(f"   ❌ No hay datos para {category}")
                print()
            
            # Verificar si son datos reales o de fallback
            if data.get('note') == 'Datos de fallback - error en scraping':
                print("⚠️  ATENCIÓN: Se están devolviendo datos de fallback")
                print("   Esto significa que el scraping no está funcionando correctamente")
            else:
                print("✅ Se están devolviendo datos reales del scraping")
            
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
    test_complete_data()
    test_scraper_directly()
