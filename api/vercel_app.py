"""
Archivo específico para Vercel serverless functions
Exporta la app Flask para que Vercel pueda usarla
"""

from api.index import app

# Vercel necesita que la app esté disponible como 'app'
# Este archivo se usa cuando Vercel despliega la función serverless
