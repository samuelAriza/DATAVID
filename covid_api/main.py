from flask import Flask, jsonify, request
from flask_cors import CORS
from routers import kpis, departamentos, temporal, regiones, consolidado, tops
import functions_framework

# Crear aplicación Flask
app = Flask(__name__)

# Deshabilitar strict slashes para que funcione con o sin trailing slash
app.url_map.strict_slashes = False

# Configurar CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Registrar blueprints (equivalente a routers de FastAPI)
app.register_blueprint(kpis.bp)
app.register_blueprint(departamentos.bp)
app.register_blueprint(temporal.bp)
app.register_blueprint(regiones.bp)
app.register_blueprint(consolidado.bp)
app.register_blueprint(tops.bp)

@app.route("/")
def root():
    return jsonify({
        "message": "COVID Analytics API - Online",
        "title": "COVID Analytics API",
        "description": "API de consulta de datos COVID procesados en BigQuery",
        "version": "1.0.0",
        "endpoints": {
            "kpis": "/kpis - KPIs nacionales",
            "departamentos": "/departamentos - Ranking y detalle de departamentos",
            "temporal": "/temporal - Evolución mensual",
            "regiones": "/regiones - Estadísticas por región",
            "consolidado": "/consolidado - Vista consolidada completa",
            "tops": {
                "letalidad": "/tops/letalidad - Top departamentos más letales",
                "meses_criticos": "/tops/meses-criticos - Meses con más casos",
                "regiones_comparativa": "/tops/regiones-comparativa - Comparativa entre regiones",
                "poblacion_afectada": "/tops/poblacion-afectada - Departamentos por % población afectada"
            }
        }
    })

# Punto de entrada para Cloud Functions (HTTP)
@functions_framework.http
def covid_api(request):
    """
    Cloud Function HTTP entry point.
    Usa Flask directamente sin middleware adicional.
    """
    # Manejar preflight CORS requests
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    
    # Procesar request con Flask
    with app.request_context(request.environ):
        response = app.full_dispatch_request()
    
    # Agregar headers CORS manualmente
    if hasattr(response, 'headers'):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    
    return response

# Punto de entrada para ejecución local
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
