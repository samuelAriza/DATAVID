from flask import Blueprint, jsonify, request
from services.bigquery_service import BigQueryService

bp = Blueprint('tops', __name__, url_prefix='/tops')
bq = BigQueryService()

@bp.route("/letalidad", methods=['GET'])
def get_top_letalidad():
    """
    Top 20 departamentos con mayor tasa de letalidad
    Muestra los departamentos más peligrosos (con más muertes relativas)
    """
    try:
        query = """
        SELECT *
        FROM `covid_analytics.top_departamentos_letalidad`
        """
        result = bq.run_query(query)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/meses-criticos", methods=['GET'])
def get_meses_criticos():
    """
    Top 20 meses más críticos de la pandemia
    Ordenados por número de casos reportados
    """
    try:
        query = """
        SELECT *
        FROM `covid_analytics.top_meses_criticos`
        """
        result = bq.run_query(query)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/regiones-comparativa", methods=['GET'])
def get_comparativa_regiones():
    """
    Comparativa detallada entre regiones
    Incluye métricas promedio por departamento y letalidad regional
    """
    try:
        query = """
        SELECT *
        FROM `covid_analytics.comparativa_regiones`
        """
        result = bq.run_query(query)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/poblacion-afectada", methods=['GET'])
def get_poblacion_afectada():
    """
    Departamentos ordenados por porcentaje de población afectada
    Muestra qué departamentos tuvieron mayor impacto relativo a su población
    """
    try:
        limit = request.args.get('limit', '20')
        query = f"""
        SELECT *
        FROM `covid_analytics.departamentos_poblacion`
        LIMIT {limit}
        """
        result = bq.run_query(query)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
