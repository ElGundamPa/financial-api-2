#!/usr/bin/env python3
"""
Script de prueba para el nuevo scraper con TradingView
"""
import asyncio
import json
import time
from api.scraper_tradingview import scrape_all_tradingview_data

async def test_tradingview_scraper():
    """Probar el scraper con TradingView"""
    print("🧪 Probando scraper con TradingView...")
    print("=" * 50)
    
    try:
        # Ejecutar scraper
        start_time = time.time()
        result = await scrape_all_tradingview_data()
        end_time = time.time()
        
        print(f"\n✅ Scraping completado en {result['duration']:.2f}s")
        print(f"📊 Total de datos obtenidos: {result['real_data_count']}")
        print(f"⏰ Timestamp: {result['timestamp']}")
        
        # Mostrar resultados detallados
        if "data" in result and "tradingview_scraper" in result["data"]:
            data = result["data"]["tradingview_scraper"]
            
            print("\n📈 RESULTADOS DETALLADOS:")
            print("=" * 50)
            
            # Criptomonedas
            print(f"\n🪙 CRIPTOMONEDAS ({len(data.get('criptomonedas', []))}):")
            for crypto in data.get('criptomonedas', []):
                print(f"  {crypto['symbol']}: ${crypto['price']} ({crypto['change']}) - Vol: {crypto['volume_24h']}")
            
            # Acciones
            print(f"\n📈 ACCIONES ({len(data.get('acciones', []))}):")
            for stock in data.get('acciones', []):
                print(f"  {stock['symbol']}: ${stock['price']} ({stock['change']}) - Vol: {stock['volume_24h']}")
            
            # Forex
            print(f"\n💱 FOREX ({len(data.get('forex', []))}):")
            for forex in data.get('forex', []):
                print(f"  {forex['symbol']}: {forex['price']} ({forex['change']}) - Vol: {forex['volume_24h']}")
            
            # Índices
            print(f"\n📊 ÍNDICES ({len(data.get('indices', []))}):")
            for index in data.get('indices', []):
                print(f"  {index['symbol']}: {index['price']} ({index['change']}) - Vol: {index['volume_24h']}")
            
            # Materias primas
            print(f"\n🛢️ MATERIAS PRIMAS ({len(data.get('materias_primas', []))}):")
            for commodity in data.get('materias_primas', []):
                print(f"  {commodity['symbol']}: ${commodity['price']} ({commodity['change']}) - Vol: {commodity['volume_24h']}")
            
            # Verificar que los datos son reales
            print(f"\n🔍 VERIFICACIÓN DE DATOS REALES:")
            print("=" * 50)
            
            total_real = 0
            total_fake = 0
            
            for category in ['criptomonedas', 'acciones', 'forex', 'indices', 'materias_primas']:
                for item in data.get(category, []):
                    # Verificar que el precio no es 0 o muy bajo
                    try:
                        price = float(item['price'])
                        if price > 0:
                            total_real += 1
                            print(f"  ✅ {item['symbol']}: ${price:.2f} (REAL)")
                        else:
                            total_fake += 1
                            print(f"  ❌ {item['symbol']}: ${price:.2f} (FAKE)")
                    except:
                        total_fake += 1
                        print(f"  ❌ {item['symbol']}: {item['price']} (ERROR)")
            
            print(f"\n📊 RESUMEN:")
            print(f"  Datos reales: {total_real}")
            print(f"  Datos falsos/error: {total_fake}")
            print(f"  Porcentaje real: {(total_real/(total_real+total_fake)*100):.1f}%")
            
            if total_real > total_fake:
                print("  🎉 ¡EXCELENTE! La mayoría de datos son reales")
            else:
                print("  ⚠️ ADVERTENCIA: Muchos datos parecen ser falsos")
        
        else:
            print("❌ No se encontraron datos en el resultado")
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

def test_api_endpoint():
    """Probar el endpoint de la API"""
    print("\n🌐 Probando endpoint de la API...")
    print("=" * 50)
    
    try:
        import requests
        
        # URL local
        url = "http://localhost:8000/api/datos"
        headers = {
            "X-API-Key": "mF9zX2q7Lr4pK8yD1sBvWj",
            "Content-Type": "application/json"
        }
        
        print(f"🔗 Haciendo request a: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API respondió correctamente")
            print(f"📊 Data source: {data.get('data_source', 'unknown')}")
            print(f"📈 Total items: {data.get('total_items', 0)}")
            print(f"⏰ Timestamp: {data.get('timestamp', 0)}")
            
            # Mostrar algunos datos de ejemplo
            if data.get('criptomonedas'):
                print(f"\n🪙 Ejemplo crypto: {data['criptomonedas'][0]}")
            if data.get('acciones'):
                print(f"📈 Ejemplo acción: {data['acciones'][0]}")
            if data.get('forex'):
                print(f"💱 Ejemplo forex: {data['forex'][0]}")
                
        else:
            print(f"❌ API respondió con error: {response.status_code}")
            print(f"📄 Respuesta: {response.text}")
            
    except Exception as e:
        print(f"❌ Error probando API: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS DEL SCRAPER CON TRADINGVIEW")
    print("=" * 60)
    
    # Probar scraper directamente
    asyncio.run(test_tradingview_scraper())
    
    # Probar endpoint de la API (si está corriendo)
    test_api_endpoint()
    
    print("\n🎯 PRUEBAS COMPLETADAS")
    print("=" * 60)
