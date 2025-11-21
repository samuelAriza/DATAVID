from flask import Blueprint, jsonify
from services.bigquery_service import BigQueryService

bp = Blueprint('kpis', __name__, url_prefix='/kpis')
bq = BigQueryService()

@bp.route("/", methods=['GET'])
def get_kpis():
    """Consultar KPIs principales"""
    try:
        query = """
        SELECT *
        FROM `covid_analytics.dashboard_kpis`
        LIMIT 1
        """
        result = bq.run_query(query)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500