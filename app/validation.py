#!/usr/bin/env python3
"""
Utilidades para validación de datos financieros
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
import pandas as pd
import numpy as np

class DataValidator:
    """Clase para validar datos financieros"""
    
    # Rangos de precios por categoría (en USD)
    PRICE_RANGES = {
        "forex": {"min": 0.0001, "max": 10000.0},
        "stocks": {"min": 0.01, "max": 1000000.0},
        "crypto": {"min": 0.00000001, "max": 1000000.0},
        "indices": {"min": 0.1, "max": 100000.0},
        "commodities": {"min": 0.01, "max": 100000.0}
    }
    
    # Rangos de cambio porcentual (en %)
    CHANGE_RANGES = {
        "forex": {"min": -50.0, "max": 50.0},
        "stocks": {"min": -100.0, "max": 1000.0},  # Permite cambios extremos para penny stocks
        "crypto": {"min": -99.0, "max": 10000.0},  # Crypto puede tener cambios extremos
        "indices": {"min": -30.0, "max": 30.0},
        "commodities": {"min": -50.0, "max": 100.0}
    }
    
    @staticmethod
    def validate_price(price: float, category: str = "stocks") -> bool:
        """Validar que el precio esté en un rango realista"""
        if not isinstance(price, (int, float)) or pd.isna(price):
            return False
            
        if price <= 0:
            return False
            
        price_range = DataValidator.PRICE_RANGES.get(category, DataValidator.PRICE_RANGES["stocks"])
        return price_range["min"] <= price <= price_range["max"]
    
    @staticmethod
    def validate_change_percentage(change_pct: Optional[float], category: str = "stocks") -> bool:
        """Validar que el cambio porcentual esté en un rango realista"""
        if change_pct is None:
            return True  # Permitir valores nulos
            
        if not isinstance(change_pct, (int, float)) or pd.isna(change_pct):
            return False
            
        change_range = DataValidator.CHANGE_RANGES.get(category, DataValidator.CHANGE_RANGES["stocks"])
        return change_range["min"] <= change_pct <= change_range["max"]
    
    @staticmethod
    def validate_timestamp(ts: Union[datetime, str], max_age_hours: int = 24) -> bool:
        """Validar que el timestamp sea reciente y válido"""
        try:
            if isinstance(ts, str):
                # Intentar parsear diferentes formatos de fecha
                for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"]:
                    try:
                        ts = datetime.strptime(ts, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # Si no se puede parsear, intentar con pandas
                    ts = pd.to_datetime(ts)
            
            if not isinstance(ts, datetime):
                return False
            
            # Verificar que no sea futuro
            now = datetime.now()
            if ts > now:
                return False
            
            # Verificar que no sea demasiado antiguo
            max_age = timedelta(hours=max_age_hours)
            if now - ts > max_age:
                return False
                
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def validate_symbol(symbol: str, category: str = "stocks") -> bool:
        """Validar formato del símbolo según la categoría"""
        if not isinstance(symbol, str) or not symbol.strip():
            return False
            
        symbol = symbol.strip().upper()
        
        # Patrones por categoría
        patterns = {
            "forex": r"^[A-Z]{6}=X$|^[A-Z]{3}[A-Z]{3}$",  # EURUSD=X o EURUSD
            "stocks": r"^[A-Z]{1,5}$",  # AAPL, MSFT, etc.
            "crypto": r"^[A-Z]{2,10}-USD$|^[A-Z]{2,10}USD$",  # BTC-USD, BTCUSD
            "indices": r"^\^[A-Z0-9]{1,10}$|^[A-Z0-9]{1,10}$",  # ^GSPC, GSPC
            "commodities": r"^[A-Z]{2,4}=F$|^[A-Z]{2,4}$"  # GC=F, GC
        }
        
        pattern = patterns.get(category, patterns["stocks"])
        return bool(re.match(pattern, symbol))
    
    @staticmethod
    def validate_volume(volume: Optional[Union[int, float]]) -> bool:
        """Validar volumen de trading"""
        if volume is None:
            return True  # Permitir valores nulos
            
        if not isinstance(volume, (int, float)) or pd.isna(volume):
            return False
            
        return volume >= 0  # El volumen no puede ser negativo
    
    @staticmethod
    def validate_market_cap(market_cap: Optional[Union[int, float]]) -> bool:
        """Validar capitalización de mercado"""
        if market_cap is None:
            return True  # Permitir valores nulos
            
        if not isinstance(market_cap, (int, float)) or pd.isna(market_cap):
            return False
            
        # Market cap debe ser positivo y no excesivamente grande
        return 0 < market_cap < 1e15  # Máximo 1 cuatrillón USD
    
    @staticmethod
    def sanitize_price(price_str: str) -> Optional[float]:
        """Limpiar y convertir string de precio a float"""
        if not isinstance(price_str, str):
            return None
            
        try:
            # Remover caracteres no numéricos excepto punto y coma
            cleaned = re.sub(r'[^\d.,\-+]', '', price_str.strip())
            
            # Manejar diferentes formatos de números
            if ',' in cleaned and '.' in cleaned:
                # Formato como 1,234.56
                cleaned = cleaned.replace(',', '')
            elif ',' in cleaned and cleaned.count(',') == 1 and len(cleaned.split(',')[1]) <= 2:
                # Formato europeo como 1234,56
                cleaned = cleaned.replace(',', '.')
            elif ',' in cleaned:
                # Formato como 1,234,567
                cleaned = cleaned.replace(',', '')
            
            return float(cleaned)
            
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def sanitize_percentage(pct_str: str) -> Optional[float]:
        """Limpiar y convertir string de porcentaje a float"""
        if not isinstance(pct_str, str):
            return None
            
        try:
            # Remover símbolo de porcentaje y espacios
            cleaned = pct_str.replace('%', '').strip()
            
            # Convertir a float
            pct = float(cleaned)
            
            # Si el valor es mayor a 100, probablemente ya está en formato decimal
            if abs(pct) > 100:
                pct = pct / 100
                
            return pct
            
        except (ValueError, AttributeError):
            return None

class DataCleaner:
    """Clase para limpiar y normalizar datos financieros"""
    
    @staticmethod
    def clean_instrument_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Limpiar datos de un instrumento financiero"""
        cleaned = data.copy()
        validator = DataValidator()
        
        # Limpiar precio
        if 'price' in cleaned and isinstance(cleaned['price'], str):
            cleaned['price'] = validator.sanitize_price(cleaned['price'])
        
        # Limpiar cambios porcentuales
        for field in ['change_1d_pct', 'change_24h_pct', 'change_1h_pct']:
            if field in cleaned and isinstance(cleaned[field], str):
                cleaned[field] = validator.sanitize_percentage(cleaned[field])
        
        # Limpiar símbolo
        if 'symbol' in cleaned and isinstance(cleaned['symbol'], str):
            cleaned['symbol'] = cleaned['symbol'].strip().upper()
        
        # Limpiar nombre
        if 'name' in cleaned and isinstance(cleaned['name'], str):
            cleaned['name'] = cleaned['name'].strip()
        
        # Convertir timestamp
        if 'ts' in cleaned and isinstance(cleaned['ts'], str):
            try:
                cleaned['ts'] = pd.to_datetime(cleaned['ts'])
            except:
                cleaned['ts'] = datetime.now()
        
        return cleaned
    
    @staticmethod
    def validate_instrument_data(data: Dict[str, Any], category: str = "stocks") -> bool:
        """Validar datos completos de un instrumento"""
        validator = DataValidator()
        
        # Validaciones obligatorias
        if not validator.validate_symbol(data.get('symbol', ''), category):
            return False
            
        if not validator.validate_price(data.get('price', 0), category):
            return False
        
        # Validaciones opcionales
        for field in ['change_1d_pct', 'change_24h_pct', 'change_1h_pct']:
            if field in data and not validator.validate_change_percentage(data[field], category):
                return False
        
        if 'ts' in data and not validator.validate_timestamp(data['ts']):
            return False
        
        if 'volume' in data and not validator.validate_volume(data['volume']):
            return False
        
        if 'market_cap' in data and not validator.validate_market_cap(data['market_cap']):
            return False
        
        return True

# Instancias globales
validator = DataValidator()
cleaner = DataCleaner()
