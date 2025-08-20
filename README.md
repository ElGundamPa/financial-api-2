# 📈 Financial API 2.0

Una API moderna de datos financieros que extrae información en tiempo real de múltiples fuentes como TradingView, Yahoo Finance y Finviz.

## 🚀 Características

- ✅ **Múltiples Fuentes**: TradingView, Yahoo Finance, Finviz
- ✅ **Datos en Tiempo Real**: Precios y cambios porcentuales actualizados
- ✅ **Múltiples Categorías**: Crypto, Stocks, Forex, Indices, Commodities
- ✅ **API RESTful**: Endpoints JSON bien estructurados
- ✅ **Scraping Inteligente**: Extracción robusta con manejo de errores
- ✅ **Deploy en Vercel**: Listo para producción

## 📊 Datos Extraídos

Cada instrumento financiero incluye:
- `symbol`: Símbolo del instrumento
- `name`: Nombre completo (si está disponible)
- `price`: Precio actual
- `change_24h_pct`: Cambio porcentual en 24 horas
- `change_1h_pct`: Cambio porcentual en 1 hora (cuando esté disponible)
- `currency`: Moneda
- `category`: Categoría (crypto, stocks, forex, indices, commodities)
- `provider`: Fuente de datos

## 🛠️ Instalación

1. **Clonar el repositorio**:
```bash
git clone <repo-url>
cd financial-api2.0
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Ejecutar la API**:
```bash
python -m flask --app app.main run --host=0.0.0.0 --port=5000
```

## 📡 Endpoints

### Health Check
```http
GET /api/health
```
Verifica el estado de la API y todos los providers.

### Verificación
```http
GET /api/verify
```
Ejecuta una verificación rápida de todos los scrapers.

### Scraping Principal
```http
GET /api/scrape?providers=<providers>&categories=<categories>&limit=<limit>
```

**Parámetros**:
- `providers`: `tradingview`, `yahoo`, `finviz`, o `all`
- `categories`: `crypto`, `stocks`, `forex`, `indices`, `commodities`, o `all`
- `limit`: Número máximo de elementos a devolver

**Ejemplos**:
```http
# Crypto de TradingView
GET /api/scrape?providers=tradingview&categories=crypto&limit=50

# Stocks de múltiples providers
GET /api/scrape?providers=tradingview,yahoo&categories=stocks&limit=100

# Todo disponible
GET /api/scrape?providers=all&categories=all&limit=200
```

## 🏗️ Estructura del Proyecto

```
financial-api2.0/
├── app/                          # Código principal de la aplicación
│   ├── adapters/                 # Adapters para cada proveedor
│   │   ├── base.py              # Interfaces base
│   │   ├── tradingview.py       # Adapter para TradingView
│   │   ├── yahoo.py             # Adapter para Yahoo Finance
│   │   ├── finviz.py            # Adapter para Finviz
│   │   ├── mock.py              # Adapter de prueba
│   │   └── alpha_vantage.py     # Adapter para Alpha Vantage
│   ├── main.py                   # Aplicación Flask principal
│   ├── models.py                 # Modelos de datos
│   ├── utils.py                  # Utilidades
│   ├── auth.py                   # Autenticación
│   ├── cache.py                  # Sistema de caché
│   └── validation.py             # Validación de datos
├── tests/                        # Tests unitarios
├── test_api_comprehensive.py     # Test integral de la API
├── test_api_final.py            # Test final de funcionalidad
├── requirements.txt              # Dependencias Python
├── vercel.json                   # Configuración para Vercel
└── README.md                     # Este archivo
```

## 🧪 Testing

### Test Integral
```bash
python test_api_comprehensive.py
```

### Test Final
```bash
python test_api_final.py
```

## 📈 Ejemplo de Respuesta

```json
{
  "meta": {
    "ts": "2025-08-20T00:30:00.000000",
    "providers": ["tradingview"],
    "categories": ["crypto"],
    "limit_per_page": 50
  },
  "data": [
    {
      "provider": "tradingview",
      "category": "crypto",
      "symbol": "BTC",
      "name": "Bitcoin",
      "price": 113617.26,
      "change_24h_pct": -1.35,
      "change_1h_pct": null,
      "currency": "USD",
      "ts": "2025-08-20T00:30:00.000000"
    }
  ]
}
```

## 🚀 Deploy en Vercel

El proyecto está configurado para deploy automático en Vercel:

1. **Conectar repositorio** a Vercel
2. **Variables de entorno** (opcionales):
   - `ALPHA_VANTAGE_API_KEY`: Para Alpha Vantage
   - `SENTRY_DSN`: Para monitoreo
3. **Deploy automático** en cada push

## 🔧 Configuración Avanzada

### Variables de Entorno
- `MAX_CONCURRENCY`: Máximo de requests concurrentes (default: 4)
- `REQUEST_TIMEOUT`: Timeout de requests en segundos (default: 60)
- `DEFAULT_LIMIT_PER_PAGE`: Límite por defecto (default: 50)

### Providers Disponibles

- **TradingView**: ✅ Crypto, Stocks, Forex, Indices, Commodities
- **Yahoo Finance**: ✅ Crypto, Stocks, Forex, Indices
- **Finviz**: ⚠️ Limitado (requiere JavaScript)
- **Alpha Vantage**: 🔑 Requiere API key
- **Mock**: 🧪 Para testing

## 📊 Estado Actual

- **TradingView**: 100% funcional, extrae cambios 24h correctamente
- **Yahoo Finance**: 100% funcional, buenos cambios 24h
- **Finviz**: Limitado por contenido dinámico
- **API**: Completamente operativa

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🆘 Soporte

Si tienes problemas o preguntas:
1. Revisa la documentación
2. Ejecuta los tests para verificar el estado
3. Abre un issue en GitHub

---

⚡ **¡API lista para producción!** ⚡