#!/usr/bin/env python3
"""
Script para obtener TODOS los elementos de todas las fuentes disponibles
"""
import requests
import json
import time
from datetime import datetime

def test_api_endpoint(url, timeout=120):
    """Función robusta para llamar a la API"""
    try:
        print(f"📡 Llamando a: {url}")
        start_time = time.time()
        
        response = requests.get(url, timeout=timeout)
        end_time = time.time()
        
        print(f"⏱️ Tiempo de respuesta: {end_time - start_time:.2f}s")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            return data, end_time - start_time
        else:
            print(f"❌ Error: {response.status_code}")
            return None, end_time - start_time
            
    except requests.exceptions.Timeout:
        print(f"⏰ Timeout después de {timeout}s")
        return None, timeout
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, 0

def analyze_data(data, provider_name):
    """Analizar los datos obtenidos"""
    if not data or 'data' not in data:
        print(f"❌ No hay datos para {provider_name}")
        return
    
    elements = data['data']
    print(f"✅ {provider_name}: {len(elements)} elementos")
    
    # Contar elementos con precios válidos
    valid_prices = [e for e in elements if e.get('price', 0) > 0]
    valid_changes = [e for e in elements if e.get('change_24h_pct') is not None]
    
    if len(elements) > 0:
        print(f"   💰 Con precios válidos: {len(valid_prices)}/{len(elements)} ({len(valid_prices)/len(elements)*100:.1f}%)")
        print(f"   📈 Con cambios 24h: {len(valid_changes)}/{len(elements)} ({len(valid_changes)/len(elements)*100:.1f}%)")
    else:
        print(f"   💰 Con precios válidos: 0/0 (0.0%)")
        print(f"   📈 Con cambios 24h: 0/0 (0.0%)")
    
    # Mostrar ejemplos
    if elements:
        print(f"   📋 Ejemplos:")
        for i, element in enumerate(elements[:5]):
            price = element.get('price', 0)
            change_24h = element.get('change_24h_pct')
            change_1h = element.get('change_1h_pct')
            
            price_str = f"${price:.2f}" if price > 0 else "N/A"
            change_24h_str = f"{change_24h:.2f}%" if change_24h is not None else "N/A"
            change_1h_str = f"{change_1h:.2f}%" if change_1h is not None else "N/A"
            
            print(f"      {i+1}. {element['symbol']}: {price_str} (24h: {change_24h_str}, 1h: {change_1h_str})")
    
    return len(elements), len(valid_prices), len(valid_changes)

def main():
    """Función principal"""
    print("🚀 OBTENIENDO TODOS LOS ELEMENTOS DE TODAS LAS FUENTES")
    print("=" * 80)
    
    base_url = "http://127.0.0.1:5000"
    
    # Esperar un momento para que la API esté lista
    print("⏳ Esperando que la API esté lista...")
    time.sleep(3)
    
    # Test de salud
    print("\n1️⃣ TEST DE SALUD")
    print("-" * 40)
    health_data, _ = test_api_endpoint(f"{base_url}/api/health")
    if health_data:
        print("✅ API funcionando correctamente")
    else:
        print("❌ API no responde")
        return
    
    # Configuración para obtener máximo de elementos
    providers = ["tradingview", "yahoo", "finviz"]
    categories = ["crypto", "stocks", "forex", "indices", "commodities"]
    
    total_elements = 0
    total_valid_prices = 0
    total_valid_changes = 0
    
    print(f"\n2️⃣ OBTENIENDO DATOS MÁXIMOS")
    print("-" * 40)
    
    for provider in providers:
        print(f"\n📊 PROVEEDOR: {provider.upper()}")
        print("-" * 30)
        
        for category in categories:
            print(f"\n🎯 Categoría: {category}")
            
            # Intentar con límite máximo
            url = f"{base_url}/api/scrape?providers={provider}&categories={category}&limit=1000"
            data, response_time = test_api_endpoint(url, timeout=180)
            
            if data:
                elements, valid_prices, valid_changes = analyze_data(data, f"{provider} {category}")
                if elements:
                    total_elements += elements
                    total_valid_prices += valid_prices
                    total_valid_changes += valid_changes
            else:
                print(f"   ❌ No se pudieron obtener datos de {provider} {category}")
            
            # Pausa entre requests
            time.sleep(2)
    
    # Resumen final
    print(f"\n3️⃣ RESUMEN FINAL")
    print("-" * 40)
    print(f"📊 TOTAL ELEMENTOS: {total_elements}")
    print(f"💰 ELEMENTOS CON PRECIOS VÁLIDOS: {total_valid_prices}")
    print(f"📈 ELEMENTOS CON CAMBIOS 24H: {total_valid_changes}")
    if total_elements > 0:
        print(f"✅ PORCENTAJE PRECIOS VÁLIDOS: {total_valid_prices/total_elements*100:.1f}%")
        print(f"✅ PORCENTAJE CAMBIOS VÁLIDOS: {total_valid_changes/total_elements*100:.1f}%")
    else:
        print(f"✅ PORCENTAJE PRECIOS VÁLIDOS: N/A")
        print(f"✅ PORCENTAJE CAMBIOS VÁLIDOS: N/A")
    
    # Test con todos los providers juntos
    print(f"\n4️⃣ TEST CON TODOS LOS PROVIDERS")
    print("-" * 40)
    
    for category in categories:
        print(f"\n🎯 TODOS LOS PROVIDERS - {category}")
        url = f"{base_url}/api/scrape?providers=all&categories={category}&limit=1000"
        data, response_time = test_api_endpoint(url, timeout=300)
        
        if data:
            analyze_data(data, f"ALL {category}")
        else:
            print(f"   ❌ No se pudieron obtener datos de todos los providers para {category}")
        
        time.sleep(3)
    
    print(f"\n🏁 ANÁLISIS COMPLETADO")
    print("=" * 80)

if __name__ == "__main__":
    main()
