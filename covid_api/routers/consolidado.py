from flask import Blueprint, jsonify, request
from services.bigquery_service import BigQueryService

bp = Blueprint('consolidado', __name__, url_prefix='/consolidado')
bq = BigQueryService()

@bp.route("/", methods=['GET'])
def get_consolidado():
    """
    Vista consolidada con información de departamentos, regiones y KPIs nacionales
    Parámetros opcionales:
    - region: Filtrar por región específica
    - limit: Límite de resultados (default: 20)
    """
    try:
        region = request.args.get('region')
        limit = request.args.get('limit', '20')
        
        # Construir query con filtros opcionales
        base_query = "SELECT * FROM `covid_analytics.vista_consolidada`"
        
        where_clauses = []
        if region:
            where_clauses.append(f"region = '{region}'")
        
        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)
        
        base_query += f" ORDER BY total_casos DESC LIMIT {limit}"
        
        result = bq.run_query(base_query)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
