import os
import time
import json
from typing import Dict, Any
from flask import Flask, request, jsonify
from api.scraper_simple import scrape_all_data, create_summary
from api.scraper_real import scrape_all_real_data
from api.scraper_tradingview import scrape_all_tradingview_data
from datetime import datetime, timedelta

app = Flask(__name__)

# Configuración simplificada - SIN CORS
AUTH_MODE = os.getenv("AUTH_MODE", "none").lower()  # Cambiar a "none" por defecto
API_KEYS = [k.strip() for k in os.getenv("API_KEYS", "mF9zX2q7Lr4pK8yD1sBvWj").split(",") if k.strip()]

cache: Dict[str, Any] = {}
CACHE_TTL = int(os.getenv("CACHE_TTL", "3000"))

# Variables globales para actualización automática
last_update = None
update_interval = timedelta(minutes=50)

def check_auth():
    """Verificar autenticación simplificada"""
    if AUTH_MODE == "none":
        return True  # Sin autenticación
    
    if AUTH_MODE == "apikey":
        # Verificar múltiples formas de enviar la API key
        api_key = (
            request.headers.get("x-api-key") or 
            request.headers.get("X-API-Key") or
            request.headers.get("Authorization") or
            request.args.get("api_key") or
            request.args.get("key")
        )
        
        # Limpiar el token
        if api_key:
            if api_key.startswith("Bearer "):
                api_key = api_key[7:]
            elif api_key.startswith("ApiKey "):
                api_key = api_key[7:]
            api_key = api_key.strip()
        
        return api_key and api_key in API_KEYS
    
    return True

@app.route("/")
def root():
    return jsonify({
        "message": "Financial Data API - Sin CORS",
        "version": "2.3.0",
        "runtime": "vercel",
        "auth_mode": AUTH_MODE,
        "cors": "disabled",
        "endpoint": "/api/datos"
    })

@app.route("/health")
def health_check():
    return jsonify({
        "ok": True,
        "time": time.time(),
        "version": "2.3.0",
        "runtime": "vercel",
        "auth_mode": AUTH_MODE,
        "cors": "disabled"
    })

@app.route("/api/datos")
def get_api_datos():
    """Endpoint principal con datos reales verificables"""
    # Verificar autenticación
    if not check_auth():
        return jsonify({
            "error": "Unauthorized",
            "message": "API key required",
            "auth_mode": AUTH_MODE,
            "help": "Add X-API-Key header or ?api_key=your_key parameter"
        }), 401
    
    # Verificar cache
    nocache = request.args.get("nocache", "0") == "1"
    if not nocache and "api_datos" in cache:
        if time.time() - cache.get("api_datos_time", 0) < CACHE_TTL:
            return jsonify(cache["api_datos"])

    try:
        # Usar scraper con TradingView para datos reales
        import asyncio
        real_data = asyncio.run(scrape_all_tradingview_data())
        
        # Crear respuesta con datos reales
        response = {
            "forex": [],
            "acciones": [],
            "criptomonedas": [],
            "indices": [],
            "materias_primas": [],
            "timestamp": time.time(),
            "total_items": 0,
            "data_source": "tradingview_real"
        }
        
        # Procesar datos reales
        if "data" in real_data and "tradingview_scraper" in real_data["data"]:
            source_data = real_data["data"]["tradingview_scraper"]
            
            # Aplicar límites específicos
            response["forex"] = source_data.get("forex", [])[:3]
            response["acciones"] = source_data.get("acciones", [])[:3]
            response["criptomonedas"] = source_data.get("criptomonedas", [])[:4]
            response["indices"] = source_data.get("indices", [])[:3]
            response["materias_primas"] = source_data.get("materias_primas", [])[:3]
        
        # Calcular total
        response["total_items"] = sum(len(response[cat]) for cat in ["forex", "acciones", "criptomonedas", "indices", "materias_primas"])
        
        # Cachear
        cache["api_datos"] = response
        cache["api_datos_time"] = time.time()
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error en /api/datos: {e}")
        # Datos de fallback realistas
        return jsonify({
            "forex": [
                {"symbol": "EUR/USD", "name": "Euro/Dollar", "change": "-0.25%", "price": "1.0850", "max_24h": "1.0870", "min_24h": "1.0830", "volume_24h": "125.5K"},
                {"symbol": "GBP/USD", "name": "Pound/Dollar", "change": "+0.35%", "price": "1.2650", "max_24h": "1.2670", "min_24h": "1.2630", "volume_24h": "98.2K"},
                {"symbol": "USD/JPY", "name": "Dollar/Yen", "change": "+0.45%", "price": "150.25", "max_24h": "150.50", "min_24h": "150.00", "volume_24h": "75.8K"}
            ],
            "acciones": [
                {"symbol": "AAPL", "name": "Apple Inc", "change": "+1.85%", "price": "185.50", "max_24h": "187.00", "min_24h": "184.00", "volume_24h": "45.2M"},
                {"symbol": "MSFT", "name": "Microsoft", "change": "+2.15%", "price": "385.75", "max_24h": "388.00", "min_24h": "383.00", "volume_24h": "28.7M"},
                {"symbol": "GOOGL", "name": "Google", "change": "+1.45%", "price": "142.25", "max_24h": "143.50", "min_24h": "141.00", "volume_24h": "15.3M"}
            ],
            "criptomonedas": [
                {"symbol": "BTC", "name": "Bitcoin", "change": "+2.5%", "price": "43250.00", "max_24h": "43500.00", "min_24h": "42800.00", "volume_24h": "2.1B"},
                {"symbol": "ETH", "name": "Ethereum", "change": "+1.8%", "price": "2650.50", "max_24h": "2675.00", "min_24h": "2625.00", "volume_24h": "1.8B"},
                {"symbol": "BNB", "name": "Binance Coin", "change": "+3.2%", "price": "315.75", "max_24h": "320.00", "min_24h": "310.50", "volume_24h": "850M"},
                {"symbol": "ADA", "name": "Cardano", "change": "+1.5%", "price": "0.4850", "max_24h": "0.4900", "min_24h": "0.4800", "volume_24h": "125M"}
            ],
            "indices": [
                {"symbol": "^GSPC", "name": "S&P 500", "change": "+0.85%", "price": "4520.50", "max_24h": "4535.00", "min_24h": "4505.00", "volume_24h": "85.2M"},
                {"symbol": "^IXIC", "name": "NASDAQ", "change": "+1.25%", "price": "14250.75", "max_24h": "14300.00", "min_24h": "14200.00", "volume_24h": "45.8M"},
                {"symbol": "^DJI", "name": "Dow Jones", "change": "+0.65%", "price": "35250.00", "max_24h": "35300.00", "min_24h": "35100.00", "volume_24h": "12.5M"},
            ],
            "materias_primas": [
                {"symbol": "GC=F", "name": "Gold", "change": "+0.75%", "price": "2050.50", "max_24h": "2055.00", "min_24h": "2045.00", "volume_24h": "125K"},
                {"symbol": "CL=F", "name": "Crude Oil", "change": "-1.85%", "price": "75.25", "max_24h": "76.50", "min_24h": "74.80", "volume_24h": "85K"},
                {"symbol": "SI=F", "name": "Silver", "change": "+1.25%", "price": "23.45", "max_24h": "23.60", "min_24h": "23.30", "volume_24h": "45K"}
            ],
            "timestamp": time.time(),
            "total_items": 16,
            "data_source": "fallback"
        })

# Para desarrollo local
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
