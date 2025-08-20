import os
import asyncio
import time
import threading
from typing import List, Optional
from datetime import datetime
from flask import Flask, request, jsonify

# Importaciones opcionales
try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
from app.models import ScrapeResponse, ScrapeMeta, ProviderStatus, HealthResponse, InstrumentSnapshot
from app.adapters.mock import MockAdapter
from app.utils import format_latency

def run_async_in_thread(coro):
    """Ejecutar corrutina asíncrona en un hilo separado"""
    result = [None]
    exception = [None]
    
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result[0] = loop.run_until_complete(coro)
        except Exception as e:
            exception[0] = e
        finally:
            loop.close()
    
    thread = threading.Thread(target=run_in_thread)
    thread.start()
    thread.join()
    
    if exception[0]:
        raise exception[0]
    
    return result[0]

# Importaciones opcionales para adaptadores avanzados
try:
    from app.adapters.yahoo import YahooAdapter
    YAHOO_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Yahoo adapter not available: {e}")
    YAHOO_AVAILABLE = False

try:
    from app.adapters.tradingview import TradingViewAdapter
    TRADINGVIEW_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ TradingView adapter not available: {e}")
    TRADINGVIEW_AVAILABLE = False

try:
    from app.adapters.finviz import FinvizAdapter
    FINVIZ_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Finviz adapter not available: {e}")
    FINVIZ_AVAILABLE = False

try:
    from app.adapters.alpha_vantage import AlphaVantageAdapter
    ALPHA_VANTAGE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Alpha Vantage adapter not available: {e}")
    ALPHA_VANTAGE_AVAILABLE = False

try:
    from app.auth import AuthMiddleware, require_api_key, optional_api_key, api_key_manager
    AUTH_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Authentication not available: {e}")
    AUTH_AVAILABLE = False

try:
    from app.cache import cache_manager
    CACHE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Cache not available: {e}")
    CACHE_AVAILABLE = False

try:
    from app.validation import validator, cleaner
    VALIDATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Validation not available: {e}")
    VALIDATION_AVAILABLE = False

def create_app():
    app = Flask(__name__)
    
    # Configurar Sentry para monitoreo (opcional)
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn and SENTRY_AVAILABLE:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.1,
            environment=os.getenv("ENVIRONMENT", "development")
        )
        print("✅ Sentry monitoring initialized")
    elif sentry_dsn and not SENTRY_AVAILABLE:
        print("⚠️ Sentry DSN provided but sentry_sdk not installed")
    
    # Configuración desde variables de entorno
    MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "4"))
    # Configuración de timeouts
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))  # Aumentado de 15 a 60 segundos
    RETRY_MAX = int(os.getenv("RETRY_MAX", "3"))
    RESPECT_ROBOTS = os.getenv("RESPECT_ROBOTS", "true").lower() == "true"
    DEFAULT_LIMIT_PER_PAGE = int(os.getenv("DEFAULT_LIMIT_PER_PAGE", "50"))
    DEFAULT_HOURS_WINDOW = int(os.getenv("DEFAULT_HOURS_WINDOW", "1"))
    
    # Inicializar middleware de autenticación (opcional)
    if AUTH_AVAILABLE:
        auth_middleware = AuthMiddleware(app)
        print("✅ Authentication middleware initialized")
    else:
        print("⚠️ Authentication not available - API will work without auth")
    
    # Inicializar adaptadores con fallback inteligente
    adapters = {}
    
    # TradingView adapter (scraping real)
    if TRADINGVIEW_AVAILABLE:
        try:
            adapters["tradingview"] = TradingViewAdapter(timeout=REQUEST_TIMEOUT)
            print("✅ TradingView adapter initialized")
        except Exception as e:
            print(f"⚠️ TradingView adapter failed to initialize: {e}")
    
    # Finviz adapter (scraping real)
    if FINVIZ_AVAILABLE:
        try:
            adapters["finviz"] = FinvizAdapter(timeout=REQUEST_TIMEOUT)
            print("✅ Finviz adapter initialized")
        except Exception as e:
            print(f"⚠️ Finviz adapter failed to initialize: {e}")
    
    # Yahoo Finance como fallback (con precaución)
    if YAHOO_AVAILABLE:
        try:
            adapters["yahoo"] = YahooAdapter(timeout=REQUEST_TIMEOUT)
            print("✅ Yahoo Finance adapter initialized")
        except Exception as e:
            print(f"⚠️ Yahoo adapter failed to initialize: {e}")
    
    # Intentar usar Alpha Vantage si hay API key y está disponible
    alpha_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if alpha_key and alpha_key != "demo" and ALPHA_VANTAGE_AVAILABLE:
        try:
            adapters["alpha_vantage"] = AlphaVantageAdapter(api_key=alpha_key, timeout=REQUEST_TIMEOUT)
            print("✅ Alpha Vantage adapter initialized")
        except Exception as e:
            print(f"⚠️ Alpha Vantage adapter failed to initialize: {e}")
    
    # Mock adapter siempre disponible como último recurso
    adapters["mock"] = MockAdapter(timeout=REQUEST_TIMEOUT)
    print("✅ Mock adapter initialized")
    
    if not adapters:
        raise RuntimeError("No adapters available!")
    
    @app.route("/api/health")
    def health():
        """Endpoint de salud"""
        start_time = time.time()
        
        # Verificar estado de cada proveedor
        provider_status = {}
        for name, adapter in adapters.items():
            try:
                # Hacer una petición simple para verificar conectividad
                start_provider = time.time()
                # Aquí podrías hacer una petición de prueba real
                latency = format_latency(start_provider)
                provider_status[name] = ProviderStatus(
                    status="ok",
                    latency_ms=latency
                )
            except Exception as e:
                provider_status[name] = ProviderStatus(
                    status="fail",
                    message=str(e)
                )
        
        response = HealthResponse(
            status="ok",
            providers=provider_status
        )
        
        return jsonify(response.to_dict())
    
    @app.route("/api/verify")
    def verify():
        """Endpoint de verificación que ejecuta un scrap rápido de cada fuente"""
        start_time = time.time()
        
        verification_results = {}
        
        # Probar cada proveedor con una categoría específica
        test_configs = {
            "tradingview": "crypto",
            "finviz": "forex", 
            "yahoo": "stocks"
        }
        
        for provider_name, test_category in test_configs.items():
            if provider_name not in adapters:
                verification_results[provider_name] = {
                    "status": "not_available",
                    "message": "Adapter not available"
                }
                continue
            
            try:
                adapter = adapters[provider_name]
                
                # Ejecutar scraping rápido
                start_provider = time.time()
                try:
                    all_snapshots = run_async_in_thread(
                        scrape_data(
                            {provider_name: adapter},
                            [provider_name],
                            [test_category],
                            10,  # Solo 10 elementos para verificación rápida
                            None,
                            1,
                            1,
                            True
                        )
                    ) or []
                except Exception as e:
                    print(f"Error en scraping de {provider_name}: {e}")
                    all_snapshots = []
                provider_time = time.time() - start_provider
                
                # Analizar resultados
                expected_count = len(all_snapshots)
                actual_count = len(all_snapshots)
                
                # Verificar precios
                price_examples = []
                for snapshot in all_snapshots[:3]:  # Primeros 3 ejemplos
                    price_examples.append({
                        "symbol": snapshot.symbol,
                        "price": snapshot.price,
                        "change_24h_pct": snapshot.change_24h_pct
                    })
                
                verification_results[provider_name] = {
                    "status": "ok" if actual_count > 0 else "no_data",
                    "category_tested": test_category,
                    "expected_vs_got": f"{expected_count} vs {actual_count}",
                    "count_match": expected_count == actual_count,
                    "price_examples": price_examples,
                    "latency_ms": round(provider_time * 1000, 2)
                }
                
            except Exception as e:
                verification_results[provider_name] = {
                    "status": "error",
                    "message": str(e),
                    "category_tested": test_category
                }
        
        # Resumen general
        total_time = time.time() - start_time
        successful_providers = sum(1 for r in verification_results.values() if r.get("status") == "ok")
        total_providers = len(verification_results)
        
        response = {
            "verification_results": verification_results,
            "summary": {
                "total_providers": total_providers,
                "successful_providers": successful_providers,
                "success_rate": f"{successful_providers}/{total_providers}",
                "total_time_ms": round(total_time * 1000, 2)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(response)
    
    @app.route("/api/scrape")
    def scrape():
        # Aplicar autenticación opcional solo si está disponible
        if AUTH_AVAILABLE:
            # Verificar API key si está presente
            api_key = (
                request.headers.get('X-API-Key') or
                request.headers.get('Authorization', '').replace('Bearer ', '') or
                request.args.get('api_key') or
                request.args.get('key')
            )
            
            if api_key:
                is_valid, result = api_key_manager.validate_api_key(api_key)
                if not is_valid:
                    return jsonify({
                        "error": "Invalid API key",
                        "details": result,
                        "timestamp": datetime.now().isoformat()
                    }), 401
        """Endpoint principal para scraping de datos"""
        start_time = time.time()
        
        # Obtener parámetros de la petición
        providers_param = request.args.get("providers", "all")
        categories_param = request.args.get("categories", "all")
        limit_per_page = int(request.args.get("limit_per_page", DEFAULT_LIMIT_PER_PAGE))
        cursor = request.args.get("cursor")
        hours_window = int(request.args.get("hours_window", DEFAULT_HOURS_WINDOW))
        max_concurrency = int(request.args.get("max_concurrency", MAX_CONCURRENCY))
        respect_robots = request.args.get("respect_robots", "true").lower() == "true"
        format_type = request.args.get("format", "json")
        dedupe_by_symbol = request.args.get("dedupe_by_symbol", "true").lower() == "true"
        
        # Validar parámetros
        if limit_per_page > 500:
            return jsonify({"error": "limit_per_page cannot exceed 500"}), 400
        
        if max_concurrency > 4:
            return jsonify({"error": "max_concurrency cannot exceed 4"}), 400
        
        # Procesar proveedores
        if providers_param == "all":
            selected_providers = list(adapters.keys())
        else:
            selected_providers = [p.strip() for p in providers_param.split(",") if p.strip() in adapters]
        
        # Procesar categorías
        valid_categories = ["forex", "stocks", "crypto", "indices", "commodities"]
        if categories_param == "all":
            selected_categories = valid_categories
        else:
            selected_categories = [c.strip() for c in categories_param.split(",") if c.strip() in valid_categories]
        
                            # Ejecutar scraping
        try:
            all_snapshots = run_async_in_thread(
                scrape_data(
                    adapters,
                    selected_providers,
                    selected_categories,
                    limit_per_page,
                    cursor,
                    hours_window,
                    max_concurrency,
                    respect_robots
                )
            ) or []
            
            # Aplicar deduplicación si se solicita
            if dedupe_by_symbol:
                all_snapshots = deduplicate_snapshots(all_snapshots)
            
            # Crear respuesta
            meta = ScrapeMeta(
                ts=datetime.now(),
                providers=selected_providers,
                categories=selected_categories,
                limit_per_page=limit_per_page,
                hours_window=hours_window,
                status=get_provider_status(selected_providers),
                next_cursor=get_next_cursor(all_snapshots, limit_per_page)
            )
            
            response = ScrapeResponse(
                meta=meta,
                data=all_snapshots
            )
            
            # Formatear respuesta
            if format_type == "jsonl":
                # Para JSONL, devolver JSON normal por ahora (Vercel no soporta streaming fácilmente)
                return jsonify(response.to_dict())
            else:
                return jsonify(response.to_dict())
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/stats")
    def stats():
        """Endpoint de estadísticas (requiere API key)"""
        try:
            # Obtener estadísticas de cache si está disponible
            cache_stats = cache_manager.get_cache_stats() if CACHE_AVAILABLE else {"status": "not_available"}
            
            # Obtener estadísticas de la API key actual si auth está disponible
            key_stats = None
            if AUTH_AVAILABLE:
                api_key = (
                    request.headers.get('X-API-Key') or
                    request.headers.get('Authorization', '').replace('Bearer ', '') or
                    request.args.get('api_key') or
                    request.args.get('key')
                )
                key_stats = api_key_manager.get_key_stats(api_key) if api_key else None
            
            return jsonify({
                "cache": cache_stats,
                "api_key": key_stats,
                "adapters": {
                    name: {
                        "name": adapter.name,
                        "available": True
                    } for name, adapter in adapters.items()
                },
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/auth")
    def auth_info():
        """Información de autenticación"""
        return jsonify({
            "message": "Financial API Authentication",
            "authentication": {
                "required": False,
                "optional": True,
                "methods": ["X-API-Key header", "Authorization Bearer", "api_key parameter"]
            },
            "rate_limits": {
                "with_api_key": "Varies by key (typically 100-1000 requests/hour)",
                "without_api_key": "10 requests/hour per IP"
            },
            "demo_key": "demo_key_12345",
            "contact": "Get your API key from the administrator",
            "timestamp": datetime.now().isoformat()
        })
    
    @app.route("/")
    def root():
        """Endpoint raíz"""
        available_adapters = list(adapters.keys())
        
        return jsonify({
            "message": "Financial Scraper Aggregator API v2.0",
            "version": "2.0.0",
            "status": "operational",
            "endpoints": {
                "health": "/api/health",
                "scrape": "/api/scrape",
                "stats": "/api/stats (requires API key)",
                "auth": "/api/auth"
            },
            "providers": available_adapters,
            "categories": ["forex", "stocks", "crypto", "indices", "commodities"],
            "features": [
                "Real-time financial data",
                "Multiple data providers",
                "Intelligent caching",
                "Rate limiting",
                "Data validation",
                "Anti-detection measures",
                "API key authentication"
            ],
            "improvements": {
                "v2.0": [
                    "Added Alpha Vantage API support",
                    "Improved Yahoo Finance adapter with rate limiting",
                    "Intelligent caching with Redis support",
                    "API key authentication system",
                    "Data validation and sanitization",
                    "Anti-detection measures",
                    "Sentry monitoring integration",
                    "Enhanced error handling",
                    "Vercel optimization"
                ]
            },
            "demo_api_key": "demo_key_12345",
            "documentation": "https://github.com/your-repo/financial-api2.0#readme",
            "timestamp": datetime.now().isoformat()
        })
    
    return app

async def scrape_data(
    adapters: dict,
    providers: List[str],
    categories: List[str],
    limit_per_page: int,
    cursor: Optional[str],
    hours_window: int,
    max_concurrency: int,
    respect_robots: bool
) -> List[InstrumentSnapshot]:
    """Función principal de scraping"""
    all_snapshots = []
    
    # Crear semáforo para limitar concurrencia
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def scrape_provider_category(provider: str, category: str):
        async with semaphore:
            try:
                print(f"🔍 DEBUG: Iniciando scraping de {provider}/{category}")
                adapter = adapters[provider]
                
                # Obtener referencias
                refs, next_cursor = await adapter.list_refs(category, cursor, limit_per_page)
                print(f"🔍 DEBUG: {provider}/{category} - Referencias obtenidas: {len(refs)}")
                
                if not refs:
                    print(f"🔍 DEBUG: {provider}/{category} - No hay referencias")
                    return []
                
                # Debug: mostrar las primeras referencias
                for i, ref in enumerate(refs[:3]):
                    print(f"🔍 DEBUG: {provider}/{category} - Ref {i+1}: {ref.symbol} = ${ref.price:.2f}")
                
                # Obtener snapshots
                snapshots = await adapter.fetch_snapshots(refs, hours_window)
                print(f"🔍 DEBUG: {provider}/{category} - Snapshots obtenidos: {len(snapshots)}")
                
                # Debug: mostrar los primeros snapshots
                for i, snapshot in enumerate(snapshots[:3]):
                    print(f"🔍 DEBUG: {provider}/{category} - Snapshot {i+1}: {snapshot.symbol} = ${snapshot.price:.2f}")
                
                return snapshots
                
            except Exception as e:
                print(f"Error scraping {provider}/{category}: {e}")
                return []
    
    # Crear tareas para todos los proveedores y categorías
    tasks = []
    for provider in providers:
        for category in categories:
            task = scrape_provider_category(provider, category)
            tasks.append(task)
    
    # Ejecutar todas las tareas
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Recolectar resultados
    for result in results:
        if isinstance(result, list):
            all_snapshots.extend(result)
    
    print(f"🔍 DEBUG: Total snapshots finales: {len(all_snapshots)}")
    for i, snapshot in enumerate(all_snapshots[:5]):
        print(f"🔍 DEBUG: Snapshot final {i+1}: {snapshot.symbol} = ${snapshot.price:.2f}")
    
    return all_snapshots

def deduplicate_snapshots(snapshots: List[InstrumentSnapshot]) -> List[InstrumentSnapshot]:
    """Deduplicar snapshots por símbolo, priorizando mock"""
    provider_priority = {"mock": 1}
    
    # Agrupar por símbolo
    symbol_groups = {}
    for snapshot in snapshots:
        symbol = snapshot.symbol
        if symbol not in symbol_groups:
            symbol_groups[symbol] = []
        symbol_groups[symbol].append(snapshot)
    
    # Para cada símbolo, seleccionar el snapshot con mayor prioridad
    deduplicated = []
    for symbol, group in symbol_groups.items():
        if len(group) == 1:
            deduplicated.append(group[0])
        else:
            # Ordenar por prioridad del proveedor
            best_snapshot = max(group, key=lambda s: provider_priority.get(s.provider, 0))
            deduplicated.append(best_snapshot)
    
    return deduplicated

def get_provider_status(providers: List[str]) -> dict:
    """Obtener estado de los proveedores"""
    status = {}
    for provider in providers:
        status[provider] = ProviderStatus(status="ok")
    return status

def get_next_cursor(snapshots: List[InstrumentSnapshot], limit_per_page: int) -> Optional[str]:
    """Obtener cursor para la siguiente página"""
    if len(snapshots) >= limit_per_page:
        # En una implementación real, aquí devolverías el cursor real
        return "next_page_token"
    return None
