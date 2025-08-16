#!/usr/bin/env python3
"""
Script para mostrar los datos actuales y las URLs de donde se obtienen
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

def mostrar_datos_y_urls():
    """Mostrar datos actuales y URLs de fuentes"""
    print("🚀 FINANCIAL API - DATOS ACTUALES Y FUENTES")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/datos", headers=HEADERS, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print("✅ Datos obtenidos exitosamente")
            print(f"📊 Total items: {data.get('total_items', 0)}")
            print(f"⏰ Timestamp: {data.get('timestamp', 0)}")
            print()
            
            # Mostrar cada categoría con precios y URLs
            categories = {
                "forex": "FOREX (Divisas)",
                "acciones": "ACCIONES (Stocks)", 
                "criptomonedas": "CRIPTOMONEDAS",
                "indices": "ÍNDICES",
                "materias_primas": "MATERIAS PRIMAS"
            }
            
            for category, title in categories.items():
                print(f"🪙 {title}:")
                if category in data and data[category]:
                    items = data[category]
                    print(f"   Total: {len(items)} elementos")
                    for i, item in enumerate(items, 1):
                        symbol = item.get('symbol', 'N/A')
                        name = item.get('name', 'N/A')
                        price = item.get('price', 'N/A')
                        change = item.get('change', 'N/A')
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
            
            # Mostrar URLs de fuentes
            print("🌐 FUENTES DE DATOS:")
            print("=" * 40)
            print("📊 FINVIZ (Datos principales):")
            print("   • Índices: https://finviz.com/screener.ashx?v=111&s=ta_sp500")
            print("   • Acciones: https://finviz.com/screener.ashx?v=111&s=ta_mostactive")
            print("   • Forex: https://finviz.com/forex.ashx")
            print("   • Materias Primas: https://finviz.com/screener.ashx?v=111&s=ta_commodities")
            print()
            print("📈 ALPHA VANTAGE API (Datos detallados):")
            print("   • Formato: https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={SYMBOL}&apikey=demo")
            print("   • Ejemplo: https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=demo")
            print()
            print("📊 YAHOO FINANCE (Datos alternativos):")
            print("   • Formato: https://finance.yahoo.com/quote/{SYMBOL}")
            print("   • Ejemplo: https://finance.yahoo.com/quote/AAPL")
            print()
            print("🔄 SISTEMA DE FALLBACK:")
            print("   • Si las fuentes externas fallan, se generan datos simulados realistas")
            print("   • Esto garantiza que siempre haya datos disponibles")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    mostrar_datos_y_urls()
