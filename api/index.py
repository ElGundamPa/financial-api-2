import os
import time
import json
from typing import Dict, Any
from flask import Flask, request, jsonify
from flask_cors import CORS
from api.scraper_simple import scrape_all_data, create_summary
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Habilitar CORS para todos los endpoints

AUTH_MODE = os.getenv("AUTH_MODE", "apikey").lower()
API_KEYS = [k.strip() for k in os.getenv("API_KEYS", "mF9zX2q7Lr4pK8yD1sBvWj").split(",") if k.strip()]

cache: Dict[str, Any] = {}
CACHE_TTL = int(os.getenv("CACHE_TTL", "3000"))  # 50 minutos = 3000 segundos

# Variables globales para actualización automática
last_update = None
update_interval = timedelta(minutes=50)  # Actualizar cada 50 minutos

def check_auth():
    """Verificar autenticación"""
    if AUTH_MODE == "none":
        return True
    
    if AUTH_MODE == "apikey":
        api_key = request.headers.get("x-api-key") or request.headers.get("X-API-Key")
        auth_header = request.headers.get("authorization") or ""
        token = (
            api_key.strip()
            if api_key
            else (auth_header.split(" ", 1)[1].strip() if auth_header.lower().startswith("apikey ") else None)
        )
        return token and token in API_KEYS
    
    return True

@app.route("/")
def root():
    return jsonify({
        "message": "Financial Data API - Versión Completa",
        "version": "2.2.0",
        "runtime": "vercel",
        "description": "API con scraping masivo de datos financieros",
        "endpoints": {
            "general": {
                "/datos": "Obtener todos los datos financieros",
                "/datos/resume": "Obtener resumen de datos",
                "/datos/indices": "Obtener solo índices",
                "/datos/acciones": "Obtener solo acciones",
                "/datos/forex": "Obtener solo forex",
                "/datos/materias_primas": "Obtener solo materias primas",
                "/datos/etfs": "Obtener solo ETFs",
                "/health": "Verificar estado de la API",
                "/sources": "Información de fuentes disponibles",
            }
        },
        "auth_mode": AUTH_MODE,
        "scraping_enabled": True,
        "auto_update": "50 minutos",
    })

@app.route("/health")
def health_check():
    return jsonify({
        "ok": True,
        "time": time.time(),
        "version": "2.2.0",
        "runtime": "vercel",
        "auth_mode": AUTH_MODE,
        "cache_items": len(cache),
        "last_update": last_update.isoformat() if last_update else None,
    })

@app.route("/sources")
def get_sources():
    sources = {
        "finviz": {
            "name": "Finviz",
            "status": "ok",
            "data_types": ["indices", "acciones", "forex", "materias_primas"],
            "requires_browser": False,
            "estimated_data": "1000+ elementos",
        },
        "yahoo": {
            "name": "Yahoo Finance",
            "status": "ok",
            "data_types": ["indices", "acciones", "forex", "materias_primas", "etfs"],
            "requires_browser": False,
            "estimated_data": "100+ elementos",
        },
    }
    return jsonify({"sources": sources, "total_sources": len(sources), "runtime": "vercel"})

@app.route("/datos")
def get_datos():
    global last_update
    
    if not check_auth():
        return jsonify({"detail": "Unauthorized"}), 401
    
    nocache = request.args.get("nocache", "0") == "1"
    
    # Verificar si necesitamos actualizar automáticamente
    if last_update is None or datetime.now() - last_update > update_interval:
        nocache = True  # Forzar actualización
    
    if not nocache and "all_data" in cache:
        if time.time() - cache.get("all_data_time", 0) < CACHE_TTL:
            return jsonify(cache["all_data"])

    try:
        import asyncio
        data = asyncio.run(scrape_all_data())
        last_update = datetime.now()
        cache["all_data"] = data
        cache["all_data_time"] = time.time()
        return jsonify(data)
    except Exception as e:
        print(f"Error obteniendo datos: {e}")
        return jsonify({
            "data": {
                "finviz": {
                    "indices": [
                        {"symbol": "SPY", "name": "S&P 500", "change": "+0.5%"},
                        {"symbol": "QQQ", "name": "NASDAQ", "change": "+0.3%"},
                    ],
                    "acciones": [
                        {"symbol": "AAPL", "name": "Apple Inc", "change": "+1.2%"},
                        {"symbol": "MSFT", "name": "Microsoft", "change": "+0.8%"},
                    ],
                },
                "yahoo": {
                    "forex": [
                        {"symbol": "EUR/USD", "name": "Euro/Dollar", "change": "-0.1%"},
                        {"symbol": "GBP/USD", "name": "Pound/Dollar", "change": "+0.2%"},
                    ],
                },
            },
            "timestamp": time.time(),
            "sources_scraped": ["finviz", "yahoo"],
            "total_sources": 2,
            "note": "Datos de fallback - error en scraping",
        })

@app.route("/datos/resume")
def get_datos_resume():
    if not check_auth():
        return jsonify({"detail": "Unauthorized"}), 401
    
    nocache = request.args.get("nocache", "0") == "1"
    if not nocache and "data_summary" in cache:
        if time.time() - cache.get("data_summary_time", 0) < CACHE_TTL:
            return jsonify(cache["data_summary"])

    try:
        import asyncio
        data = asyncio.run(scrape_all_data())
        summary = create_summary(data)
        cache["data_summary"] = summary
        cache["data_summary_time"] = time.time()
        return jsonify(summary)
    except Exception as e:
        print(f"Error obteniendo resumen: {e}")
        return jsonify({
            "indices": [
                {"symbol": "SPY", "name": "S&P 500", "change": "+0.5%"},
                {"symbol": "QQQ", "name": "NASDAQ", "change": "+0.3%"},
            ],
            "acciones": [
                {"symbol": "AAPL", "name": "Apple Inc", "change": "+1.2%"},
                {"symbol": "MSFT", "name": "Microsoft", "change": "+0.8%"},
            ],
            "forex": [
                {"symbol": "EUR/USD", "name": "Euro/Dollar", "change": "-0.1%"},
                {"symbol": "GBP/USD", "name": "Pound/Dollar", "change": "+0.2%"},
            ],
            "last_updated": time.time(),
            "note": "Resumen de fallback - error en scraping",
        })

@app.route("/api/datos")
def get_api_datos():
    """Endpoint simplificado que devuelve todos los datos en formato unificado"""
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    
    nocache = request.args.get("nocache", "0") == "1"
    if not nocache and "api_datos" in cache:
        if time.time() - cache.get("api_datos_time", 0) < CACHE_TTL:
            return jsonify(cache["api_datos"])

    try:
        import asyncio
        data = asyncio.run(scrape_all_data())
        
        # Crear respuesta simplificada y unificada
        response = {
            "forex": [],
            "acciones": [],
            "criptomonedas": [],  # Agregar criptomonedas
            "indices": [],
            "materias_primas": [],
            "timestamp": time.time(),
            "total_items": 0
        }
        
        # Procesar datos de todas las fuentes
        for source_data in data.get("data", {}).values():
            # Forex
            if "forex" in source_data:
                response["forex"].extend(source_data["forex"])
            
            # Acciones
            if "acciones" in source_data:
                response["acciones"].extend(source_data["acciones"])
            
            # Índices
            if "indices" in source_data:
                response["indices"].extend(source_data["indices"])
            
            # Materias primas
            if "materias_primas" in source_data:
                response["materias_primas"].extend(source_data["materias_primas"])
            
            # ETFs (convertir a criptomonedas para este endpoint)
            if "etfs" in source_data:
                # Agregar algunos ETFs como criptomonedas para diversidad
                crypto_etfs = [etf for etf in source_data["etfs"] if etf["symbol"] in ["GBTC", "BITO", "ARKW"]]
                response["criptomonedas"].extend(crypto_etfs)
        
        # Limitar a top 50 por categoría para mantener respuesta rápida
        response["forex"] = response["forex"][:50]
        response["acciones"] = response["acciones"][:50]
        response["criptomonedas"] = response["criptomonedas"][:50]
        response["indices"] = response["indices"][:50]
        response["materias_primas"] = response["materias_primas"][:50]
        
        # Calcular total
        response["total_items"] = (
            len(response["forex"]) + 
            len(response["acciones"]) + 
            len(response["criptomonedas"]) + 
            len(response["indices"]) + 
            len(response["materias_primas"])
        )
        
        # Cachear respuesta
        cache["api_datos"] = response
        cache["api_datos_time"] = time.time()
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error en /api/datos: {e}")
        return jsonify({
            "forex": [
                {"symbol": "EUR/USD", "name": "Euro/Dollar", "change": "-0.1%"},
                {"symbol": "GBP/USD", "name": "Pound/Dollar", "change": "+0.2%"},
            ],
            "acciones": [
                {"symbol": "AAPL", "name": "Apple Inc", "change": "+1.2%"},
                {"symbol": "MSFT", "name": "Microsoft", "change": "+0.8%"},
            ],
            "criptomonedas": [
                {"symbol": "BTC", "name": "Bitcoin", "change": "+2.5%"},
                {"symbol": "ETH", "name": "Ethereum", "change": "+1.8%"},
            ],
            "indices": [
                {"symbol": "SPY", "name": "S&P 500", "change": "+0.5%"},
                {"symbol": "QQQ", "name": "NASDAQ", "change": "+0.3%"},
            ],
            "materias_primas": [
                {"symbol": "GC", "name": "Gold", "change": "+0.7%"},
                {"symbol": "CL", "name": "Crude Oil", "change": "-1.2%"},
            ],
            "timestamp": time.time(),
            "total_items": 10,
            "note": "Datos de fallback - error en scraping"
        })

# Nuevos endpoints específicos por tipo de dato
@app.route("/datos/indices")
def get_indices():
    if not check_auth():
        return jsonify({"detail": "Unauthorized"}), 401
    
    try:
        import asyncio
        data = asyncio.run(scrape_all_data())
        indices = []
        
        for source_data in data.get("data", {}).values():
            if "indices" in source_data:
                indices.extend(source_data["indices"])
        
        return jsonify({
            "indices": indices[:100],  # Top 100 índices
            "total": len(indices),
            "timestamp": time.time()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/datos/acciones")
def get_stocks():
    if not check_auth():
        return jsonify({"detail": "Unauthorized"}), 401
    
    try:
        import asyncio
        data = asyncio.run(scrape_all_data())
        stocks = []
        
        for source_data in data.get("data", {}).values():
            if "acciones" in source_data:
                stocks.extend(source_data["acciones"])
        
        return jsonify({
            "acciones": stocks[:100],  # Top 100 acciones
            "total": len(stocks),
            "timestamp": time.time()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/datos/forex")
def get_forex():
    if not check_auth():
        return jsonify({"detail": "Unauthorized"}), 401
    
    try:
        import asyncio
        data = asyncio.run(scrape_all_data())
        forex = []
        
        for source_data in data.get("data", {}).values():
            if "forex" in source_data:
                forex.extend(source_data["forex"])
        
        return jsonify({
            "forex": forex[:100],  # Top 100 forex
            "total": len(forex),
            "timestamp": time.time()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/datos/materias_primas")
def get_commodities():
    if not check_auth():
        return jsonify({"detail": "Unauthorized"}), 401
    
    try:
        import asyncio
        data = asyncio.run(scrape_all_data())
        commodities = []
        
        for source_data in data.get("data", {}).values():
            if "materias_primas" in source_data:
                commodities.extend(source_data["materias_primas"])
        
        return jsonify({
            "materias_primas": commodities[:100],  # Top 100 materias primas
            "total": len(commodities),
            "timestamp": time.time()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/datos/etfs")
def get_etfs():
    if not check_auth():
        return jsonify({"detail": "Unauthorized"}), 401
    
    try:
        import asyncio
        data = asyncio.run(scrape_all_data())
        etfs = []
        
        for source_data in data.get("data", {}).values():
            if "etfs" in source_data:
                etfs.extend(source_data["etfs"])
        
        return jsonify({
            "etfs": etfs[:100],  # Top 100 ETFs
            "total": len(etfs),
            "timestamp": time.time()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Para Vercel serverless, necesitamos exportar la app
# No ejecutar app.run() en serverless
if __name__ == "__main__":
    # Solo ejecutar en desarrollo local
    app.run(host="0.0.0.0", port=8000, debug=True)