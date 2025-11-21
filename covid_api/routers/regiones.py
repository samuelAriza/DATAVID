from flask import Blueprint, jsonify
from services.bigquery_service import BigQueryService

bp = Blueprint('regiones', __name__, url_prefix='/regiones')
bq = BigQueryService()

@bp.route("/", methods=['GET'])
def get_regiones():
    """Consultar estadísticas por regiones"""
    try:
        query = """
        SELECT *
        FROM `covid_analytics.geografia_regiones`
        ORDER BY total_casos DESC
        """
        result = bq.run_query(query)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
