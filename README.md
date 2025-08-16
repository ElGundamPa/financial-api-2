# Financial API 2.0 - Serverless Ready

API optimizada para obtener datos financieros en tiempo real, diseñada para funcionar en Vercel y localmente.

## 🚀 Características

- **Serverless Ready**: Optimizada para Vercel
- **Scraping en tiempo real**: Datos de Finviz y Yahoo Finance
- **Cache inteligente**: Reduce llamadas a APIs externas
- **Autenticación flexible**: API Key o modo sin autenticación
- **Fallback data**: Datos de respaldo en caso de error
- **Múltiples fuentes**: Índices, acciones, forex, materias primas, ETFs
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
   ├─ __init__.py       # Paquete Python
   ├─ index.py          # API Flask principal
   └─ scraper_simple.py # Scraper optimizado
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

### Estructura de respuesta optimizada
```json
{
  "forex": [
    {"symbol": "EUR/USD", "name": "Euro/Dollar", "change": "-0.1%"},
    {"symbol": "GBP/USD", "name": "Pound/Dollar", "change": "+0.2%"},
    {"symbol": "USD/JPY", "name": "Dollar/Yen", "change": "+0.3%"}
  ],
  "acciones": [
    {"symbol": "AAPL", "name": "Apple Inc", "change": "+1.2%"},
    {"symbol": "MSFT", "name": "Microsoft", "change": "+0.8%"},
    {"symbol": "GOOGL", "name": "Google", "change": "+1.5%"}
  ],
  "criptomonedas": [
    {"symbol": "BTC", "name": "Bitcoin", "change": "+2.5%"},
    {"symbol": "ETH", "name": "Ethereum", "change": "+1.8%"},
    {"symbol": "BNB", "name": "Binance Coin", "change": "+3.2%"},
    {"symbol": "ADA", "name": "Cardano", "change": "+1.5%"}
  ],
  "indices": [
    {"symbol": "SPY", "name": "S&P 500", "change": "+0.5%"},
    {"symbol": "QQQ", "name": "NASDAQ", "change": "+0.3%"},
    {"symbol": "DIA", "name": "Dow Jones", "change": "+0.2%"}
  ],
  "materias_primas": [
    {"symbol": "GC", "name": "Gold", "change": "+0.7%"},
    {"symbol": "CL", "name": "Crude Oil", "change": "-1.2%"},
    {"symbol": "SI", "name": "Silver", "change": "+0.8%"}
  ],
  "timestamp": 1755281638.2603242,
  "total_items": 16
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
- S&P 500, NASDAQ, Dow Jones
- Datos de Finviz y Yahoo Finance

### Acciones
- AAPL, MSFT, GOOGL, AMZN, TSLA
- Acciones más activas de Finviz

### Forex
- EUR/USD, GBP/USD, USD/JPY
- Pares de divisas principales

### Materias Primas
- Oro (GC=F)
- Petróleo (CL=F)

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

- **Scraping paralelo**: Finviz y Yahoo se ejecutan simultáneamente
- **Cache en memoria**: Reduce llamadas a APIs externas
- **Fallback data**: Datos de respaldo en caso de error
- **Headers seguros**: User-Agent y headers por defecto
- **Decode tolerante**: Maneja caracteres especiales
- **Flask framework**: Estable y compatible con Python 3.13+

## 📝 Notas

- El scraper usa solo librerías estándar de Python
- Optimizado para funcionar en entorno serverless
- Datos limitados a top 5-10 por categoría para velocidad
- Compatible con Python 3.8+
- Usa Flask en lugar de FastAPI para mejor compatibilidad

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.
