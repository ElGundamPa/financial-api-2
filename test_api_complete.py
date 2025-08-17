#!/usr/bin/env python3
"""
Script para probar la API completa con el nuevo scraper de TradingView
"""
import urllib.request
import urllib.parse
import json
import time

def make_request(url: str, headers: dict = None) -> str:
    """Hacer petición HTTP usando urllib"""
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error en request a {url}: {e}")
        return ""

def test_api_endpoint():
    """Probar el endpoint de la API"""
    print("🌐 Probando endpoint de la API...")
    print("=" * 50)
    
    try:
        # URL local
        url = "http://localhost:8000/api/datos"
        headers = {
            "X-API-Key": "mF9zX2q7Lr4pK8yD1sBvWj",
            "Content-Type": "application/json"
        }
        
        print(f"🔗 Haciendo request a: {url}")
        response_text = make_request(url, headers)
        
        if response_text:
            data = json.loads(response_text)
            print(f"✅ API respondió correctamente")
            print(f"📊 Data source: {data.get('data_source', 'unknown')}")
            print(f"📈 Total items: {data.get('total_items', 0)}")
            print(f"⏰ Timestamp: {data.get('timestamp', 0)}")
            
            # Mostrar datos detallados
            print(f"\n📈 DATOS OBTENIDOS:")
            print("=" * 50)
            
            # Criptomonedas
            if data.get('criptomonedas'):
                print(f"\n🪙 CRIPTOMONEDAS ({len(data['criptomonedas'])}):")
                for crypto in data['criptomonedas']:
                    print(f"  {crypto['symbol']}: ${crypto['price']} ({crypto['change']}) - Vol: {crypto['volume_24h']}")
            
            # Acciones
            if data.get('acciones'):
                print(f"\n📈 ACCIONES ({len(data['acciones'])}):")
                for stock in data['acciones']:
                    print(f"  {stock['symbol']}: ${stock['price']} ({stock['change']}) - Vol: {stock['volume_24h']}")
            
            # Forex
            if data.get('forex'):
                print(f"\n💱 FOREX ({len(data['forex'])}):")
                for forex in data['forex']:
                    print(f"  {forex['symbol']}: {forex['price']} ({forex['change']}) - Vol: {forex['volume_24h']}")
            
            # Índices
            if data.get('indices'):
                print(f"\n📊 ÍNDICES ({len(data['indices'])}):")
                for index in data['indices']:
                    print(f"  {index['symbol']}: {index['price']} ({index['change']}) - Vol: {index['volume_24h']}")
            
            # Materias primas
            if data.get('materias_primas'):
                print(f"\n🛢️ MATERIAS PRIMAS ({len(data['materias_primas'])}):")
                for commodity in data['materias_primas']:
                    print(f"  {commodity['symbol']}: ${commodity['price']} ({commodity['change']}) - Vol: {commodity['volume_24h']}")
            
            # Verificar que los datos son reales
            print(f"\n🔍 VERIFICACIÓN DE DATOS REALES:")
            print("=" * 50)
            
            total_real = 0
            total_fake = 0
            
            for category in ['criptomonedas', 'acciones', 'forex', 'indices', 'materias_primas']:
                for item in data.get(category, []):
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
            if total_real + total_fake > 0:
                print(f"  Porcentaje real: {(total_real/(total_real+total_fake)*100):.1f}%")
            
            if total_real > total_fake:
                print("  🎉 ¡EXCELENTE! La mayoría de datos son reales")
            else:
                print("  ⚠️ ADVERTENCIA: Muchos datos parecen ser falsos")
                
        else:
            print(f"❌ API no respondió")
            
    except Exception as e:
        print(f"❌ Error probando API: {e}")

def test_health_endpoint():
    """Probar el endpoint de health check"""
    print("\n🏥 Probando health check...")
    print("=" * 50)
    
    try:
        url = "http://localhost:8000/health"
        response_text = make_request(url)
        
        if response_text:
            data = json.loads(response_text)
            print(f"✅ Health check exitoso")
            print(f"📊 Status: {data.get('status', 'unknown')}")
            print(f"🕒 Timestamp: {data.get('timestamp', 0)}")
            print(f"📋 Version: {data.get('version', 'unknown')}")
        else:
            print(f"❌ Health check falló")
            
    except Exception as e:
        print(f"❌ Error en health check: {e}")

def test_without_cache():
    """Probar la API sin cache"""
    print("\n🔄 Probando sin cache...")
    print("=" * 50)
    
    try:
        url = "http://localhost:8000/api/datos?nocache=1"
        headers = {
            "X-API-Key": "mF9zX2q7Lr4pK8yD1sBvWj",
            "Content-Type": "application/json"
        }
        
        print(f"🔗 Haciendo request a: {url}")
        start_time = time.time()
        response_text = make_request(url, headers)
        end_time = time.time()
        
        if response_text:
            data = json.loads(response_text)
            print(f"✅ API respondió en {end_time - start_time:.2f}s")
            print(f"📊 Data source: {data.get('data_source', 'unknown')}")
            print(f"📈 Total items: {data.get('total_items', 0)}")
        else:
            print(f"❌ API no respondió")
            
    except Exception as e:
        print(f"❌ Error probando sin cache: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS COMPLETAS DE LA API")
    print("=" * 60)
    
    # Probar health check
    test_health_endpoint()
    
    # Probar endpoint principal
    test_api_endpoint()
    
    # Probar sin cache
    test_without_cache()
    
    print("\n🎯 PRUEBAS COMPLETADAS")
    print("=" * 60)
