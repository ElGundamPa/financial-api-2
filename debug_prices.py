#!/usr/bin/env python3
"""
Script para debuggear la extracción de precios en TradingView
"""
import requests
import json
import time

def debug_tradingview_prices():
    """Debuggear precios de TradingView específicamente"""
    print("🔍 DEBUGGEANDO PRECIOS DE TRADINGVIEW")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:5000"
    
    # Test específico de TradingView crypto con límite pequeño
    print("\n🎯 TEST TRADINGVIEW CRYPTO (10 elementos)")
    print("-" * 40)
    
    url = f"{base_url}/api/scrape?providers=tradingview&categories=crypto&limit=10"
    print(f"📡 Llamando a: {url}")
    
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            data = response.json()
            elements = data.get('data', [])
            
            print(f"✅ Obtenidos {len(elements)} elementos")
            print("\n📋 ANÁLISIS DETALLADO DE PRECIOS:")
            print("-" * 40)
            
            for i, element in enumerate(elements):
                symbol = element.get('symbol', 'N/A')
                price = element.get('price', 0)
                change_24h = element.get('change_24h_pct')
                name = element.get('name', 'N/A')
                
                print(f"{i+1:2d}. {symbol:8s} | ${price:10.2f} | {change_24h:6.2f}% | {name}")
                
                # Verificar si el precio parece correcto
                if price < 1.0 and symbol in ['BTC', 'ETH', 'BNB']:
                    print(f"    ⚠️  PRECIO SOSPECHOSO: {symbol} debería ser > $1000")
                elif price > 100000 and symbol not in ['BTC']:
                    print(f"    ⚠️  PRECIO SOSPECHOSO: {symbol} parece muy alto")
                    
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test de stocks también
    print(f"\n🎯 TEST TRADINGVIEW STOCKS (10 elementos)")
    print("-" * 40)
    
    url = f"{base_url}/api/scrape?providers=tradingview&categories=stocks&limit=10"
    print(f"📡 Llamando a: {url}")
    
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            data = response.json()
            elements = data.get('data', [])
            
            print(f"✅ Obtenidos {len(elements)} elementos")
            print("\n📋 ANÁLISIS DETALLADO DE PRECIOS:")
            print("-" * 40)
            
            for i, element in enumerate(elements):
                symbol = element.get('symbol', 'N/A')
                price = element.get('price', 0)
                change_24h = element.get('change_24h_pct')
                name = element.get('name', 'N/A')
                
                print(f"{i+1:2d}. {symbol:8s} | ${price:10.2f} | {change_24h:6.2f}% | {name}")
                
                # Verificar si el precio parece correcto para stocks
                if price < 1.0 and symbol in ['NVDA', 'MSFT', 'AAPL', 'GOOG', 'AMZN']:
                    print(f"    ⚠️  PRECIO SOSPECHOSO: {symbol} debería ser > $10")
                elif price > 10000:
                    print(f"    ⚠️  PRECIO SOSPECHOSO: {symbol} parece muy alto")
                    
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_tradingview_prices()
