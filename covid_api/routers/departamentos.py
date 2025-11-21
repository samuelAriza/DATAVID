from flask import Blueprint, jsonify, request
from services.bigquery_service import BigQueryService

bp = Blueprint('departamentos', __name__, url_prefix='/departamentos')
bq = BigQueryService()

@bp.route("/", methods=['GET'])
def get_departamentos():
    """
    Obtener ranking de departamentos o detalle de uno específico
    Si se proporciona el parámetro 'nombre', devuelve el detalle
    Si no, devuelve el ranking completo
    """
    try:
        nombre = request.args.get('nombre')
        
        if nombre:
            # Detalle de un departamento específico
            query = f"""
            SELECT *
            FROM `covid_analytics.geografia_departamentos`
            WHERE nombre_departamento = '{nombre}'
            """
        else:
            # Ranking de todos los departamentos
            query = """
            SELECT *
            FROM `covid_analytics.ranking_departamentos`
            ORDER BY ranking
            LIMIT 20
            """
        
        result = bq.run_query(query)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/ranking", methods=['GET'])
def get_ranking():
    """Ranking de departamentos (endpoint alternativo)"""
    try:
        query = """
        SELECT *
        FROM `covid_analytics.ranking_departamentos`
        ORDER BY ranking
        LIMIT 20
        """
        result = bq.run_query(query)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
