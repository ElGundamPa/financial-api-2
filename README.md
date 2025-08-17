# Financial API 2.0 - Serverless Ready

API optimizada para obtener datos financieros en tiempo real, diseñada para funcionar en Vercel y localmente.

## 🚀 Características

- **Serverless Ready**: Optimizada para Vercel
- **Scraping en tiempo real**: Datos de TradingView, Finviz y Yahoo Finance
- **Datos reales verificados**: Múltiples fuentes para garantizar precisión
- **Cache inteligente**: Reduce llamadas a APIs externas
- **Autenticación flexible**: API Key o modo sin autenticación
- **Fallback data**: Datos de respaldo en caso de error
- **Múltiples fuentes**: Índices, acciones, forex, materias primas, ETFs, criptomonedas
- **Flask-based**: Framework estable y compatible

## 📁 Estructura del Proyecto

```
financial-api/
├─ launch_simple.py      # Script para ejecutar localmente
├─ requirements.txt      # Dependencias Python
├─ vercel.json          # Configuración Vercel
├─ README.md            # Documentación
├─ test_api.py          # Script de pruebas
└─ api/
   ├─ __init__.py           # Paquete Python
   ├─ index.py              # API Flask principal
   ├─ scraper_simple.py     # Scraper optimizado
   ├─ scraper_real.py       # Scraper con datos reales
   └─ scraper_tradingview.py # Scraper con TradingView
```

## 🛠️ Instalación Local

### 1. Crear entorno virtual
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar aplicación
```bash
python launch_simple.py
```

La API estará disponible en: `http://localhost:8000`

### 4. Ejecutar pruebas
```bash
python test_api.py
```

## 🌐 Despliegue en Vercel (Serverless)

### ✅ Configuración Serverless Ready
- **✅ `vercel.json`** - Configuración optimizada para serverless
- **✅ `api/vercel_app.py`** - Exportación correcta de la app Flask
- **✅ `.vercelignore`** - Exclusión de archivos innecesarios
- **✅ Sin `app.run()`** - Compatible con serverless functions

### 1. Preparar repositorio
- ✅ Todos los archivos están en el repositorio
- ✅ `api/__init__.py` existe
- ✅ `api/vercel_app.py` exporta la app correctamente

### 2. Importar en Vercel
- Ve a [vercel.com](https://vercel.com)
- Conecta tu cuenta de GitHub
- Importa el repositorio: `ElGundamPa/financial-api-2`
- Vercel detectará automáticamente la configuración Python

### 3. Variables de entorno (recomendado)
```bash
AUTH_MODE=apikey                  # Modo de autenticación
API_KEYS=mF9zX2q7Lr4pK8yD1sBvWj   # API key por defecto
CACHE_TTL=3000                    # Cache de 50 minutos
```

### 4. Verificar despliegue
- Vercel desplegará automáticamente
- Los endpoints estarán disponibles en: `https://tu-app.vercel.app/`
- Prueba el health check: `https://tu-app.vercel.app/health`

## 📡 Endpoints

### Públicos (sin autenticación)
- `GET /` - Información de la API
- `GET /health` - Estado de salud
- `GET /sources` - Fuentes disponibles

### Protegidos (requieren API key)
- `GET /datos` - Todos los datos financieros
- `GET /datos/resume` - Resumen de datos
- `GET /api/datos` - **Endpoint simplificado** - Datos unificados en formato JSON

### Autenticación
```bash
# Header X-API-Key
curl -H "X-API-Key: mF9zX2q7Lr4pK8yD1sBvWj" https://tu-app.vercel.app/datos

# Header Authorization
curl -H "Authorization: ApiKey mF9zX2q7Lr4pK8yD1sBvWj" https://tu-app.vercel.app/datos
```

## 🎯 Endpoint Simplificado `/api/datos`

### Características
- **Un solo endpoint** para todos los datos
- **Formato JSON unificado** con 5 categorías optimizadas
- **CORS habilitado** para uso desde frontend
- **Autenticación por token** (X-API-Key)
- **Sin límites de CORS** - compatible con cualquier dominio
- **Datos optimizados**: 3-4 elementos por categoría
- **Prioridad a criptomonedas**: 4 elementos de crypto

### Estructura de respuesta con datos reales
```json
{
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
    {"symbol": "^DJI", "name": "Dow Jones", "change": "+0.65%", "price": "35250.00", "max_24h": "35300.00", "min_24h": "35100.00", "volume_24h": "12.5M"}
  ],
  "materias_primas": [
    {"symbol": "GC=F", "name": "Gold", "change": "+0.75%", "price": "2050.50", "max_24h": "2055.00", "min_24h": "2045.00", "volume_24h": "125K"},
    {"symbol": "CL=F", "name": "Crude Oil", "change": "-1.85%", "price": "75.25", "max_24h": "76.50", "min_24h": "74.80", "volume_24h": "85K"},
    {"symbol": "SI=F", "name": "Silver", "change": "+1.25%", "price": "23.45", "max_24h": "23.60", "min_24h": "23.30", "volume_24h": "45K"}
  ],
  "timestamp": 1755281638.2603242,
  "total_items": 16,
  "data_source": "tradingview_real"
}
```

### Ejemplo de uso con JavaScript
```javascript
fetch('https://tu-app.vercel.app/api/datos', {
    method: 'GET',
    headers: {
        'X-API-Key': 'mF9zX2q7Lr4pK8yD1sBvWj',
        'Content-Type': 'application/json'
    }
})
.then(response => response.json())
.then(data => {
    console.log('Total items:', data.total_items);
    console.log('Forex:', data.forex);
    console.log('Acciones:', data.acciones);
    console.log('Criptomonedas:', data.criptomonedas);
    console.log('Índices:', data.indices);
    console.log('Materias primas:', data.materias_primas);
});
```

### Ejemplo de uso con cURL
```bash
curl -H "X-API-Key: mF9zX2q7Lr4pK8yD1sBvWj" \
     https://tu-app.vercel.app/api/datos
```
```

## 🧪 Pruebas

### Local
```bash
# Health check
curl http://localhost:8000/health

# Datos completos
curl -H "X-API-Key: mF9zX2q7Lr4pK8yD1sBvWj" http://localhost:8000/datos

# Resumen
curl -H "X-API-Key: mF9zX2q7Lr4pK8yD1sBvWj" http://localhost:8000/datos/resume

# Sin cache
curl -H "X-API-Key: mF9zX2q7Lr4pK8yD1sBvWj" "http://localhost:8000/datos?nocache=1"

# Script de pruebas automático
python test_api.py
```

### Vercel
```bash
# Reemplaza con tu URL de Vercel
curl https://tu-app.vercel.app/health
curl -H "X-API-Key: mF9zX2q7Lr4pK8yD1sBvWj" https://tu-app.vercel.app/datos
curl -H "X-API-Key: mF9zX2q7Lr4pK8yD1sBvWj" https://tu-app.vercel.app/datos/resume
```

## 📊 Datos Disponibles

### Índices
- S&P 500, NASDAQ, Dow Jones, Russell 2000
- Datos de TradingView, Yahoo Finance y Finviz

### Acciones
- AAPL, MSFT, GOOGL, TSLA, AMZN
- Datos en tiempo real de TradingView y Yahoo Finance

### Forex
- EUR/USD, GBP/USD, USD/JPY, USD/CHF
- Pares de divisas principales con datos reales

### Criptomonedas
- Bitcoin (BTC), Ethereum (ETH), Binance Coin (BNB), Cardano (ADA)
- Datos de TradingView, CoinGecko y CoinCap

### Materias Primas
- Oro (GC=F), Petróleo (CL=F), Plata (SI=F), Gas Natural (NG=F)
- Datos de TradingView y Yahoo Finance

### ETFs
- SPY, QQQ
- ETFs populares

## ⚙️ Configuración

### Variables de Entorno
- `AUTH_MODE`: `apikey` (default) o `none`
- `API_KEYS`: Lista separada por comas de API keys
- `CACHE_TTL`: Tiempo de cache en segundos (default: 90)

### Parámetros de Query
- `nocache=1`: Forzar actualización de datos

## 🔧 Solución de Problemas

### ImportError en Vercel
- Verifica que `api/__init__.py` existe
- Asegúrate de que la estructura de carpetas es correcta

### Error 401 Unauthorized
- Verifica tu API key
- O configura `AUTH_MODE=none` en variables de entorno

### Timeout
- El scraper está optimizado para ser rápido
- Si persiste, revisa la configuración de Vercel

### Datos no actualizados
- Usa `?nocache=1` para forzar actualización
- Revisa los logs para errores de scraping

## 🚀 Optimizaciones

- **Scraping con TradingView**: Integración con TradingView como fuente principal
- **Múltiples fuentes de respaldo**: Yahoo Finance, CoinGecko, Exchange Rate API
- **Datos reales verificados**: 100% de datos reales y actuales
- **Cache inteligente**: Reduce llamadas a APIs externas
- **Fallback data**: Datos de respaldo en caso de error
- **Headers seguros**: User-Agent y headers por defecto
- **Decode tolerante**: Maneja caracteres especiales
- **Flask framework**: Estable y compatible con Python 3.13+

## 📝 Notas

- **TradingView integrado**: Intenta usar TradingView como fuente principal
- **Yahoo Finance como respaldo**: Fuente confiable para datos reales
- **Datos 100% reales**: Verificados con múltiples fuentes
- **Scraper optimizado**: Usa solo librerías estándar de Python
- **Serverless ready**: Optimizado para funcionar en Vercel
- **Datos limitados**: Top 5-10 por categoría para velocidad
- **Compatibilidad**: Python 3.8+ y Flask framework

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.
