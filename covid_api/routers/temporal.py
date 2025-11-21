from flask import Blueprint, jsonify
from services.bigquery_service import BigQueryService

bp = Blueprint('temporal', __name__, url_prefix='/temporal')
bq = BigQueryService()

@bp.route("/", methods=['GET'])
def get_temporal():
    """Consultar evolución temporal"""
    try:
        query = """
        SELECT *
        FROM `covid_analytics.temporal_mensual`
        ORDER BY anio_reporte, mes_reporte
        """
        result = bq.run_query(query)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
