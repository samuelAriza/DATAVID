# analytics_descriptive.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window
import sys

def create_spark_session():
    return SparkSession.builder \
        .appName("COVID-Analytics-Descriptive") \
        .config("spark.sql.adaptive.enabled", "true") \
        .getOrCreate()

def load_processed_data(spark, bucket):
    """Cargar datos procesados"""
    path = f"gs://{bucket}/covid_processed/"
    return spark.read.parquet(path)

def analyze_temporal_trends(df):
    """Análisis de tendencias temporales"""
    print("\n=== Análisis Temporal ===")

    # Casos por mes
    casos_mes = df.groupBy("anio_reporte", "mes_reporte").agg(
        count("*").alias("total_casos"),
        sum("fallecido").alias("total_fallecidos"),
        sum("recuperado_flag").alias("total_recuperados"),
        (sum("fallecido") / count("*") * 100).alias("tasa_letalidad")
    ).orderBy("anio_reporte", "mes_reporte")

    # Tendencia semanal
    casos_semana = df.groupBy("anio_reporte", "semana_reporte").agg(
        count("*").alias("casos"),
        avg("edad_anios").alias("edad_promedio")
    ).orderBy("anio_reporte", "semana_reporte")

    return casos_mes, casos_semana

def analyze_demographics(df):
    """Análisis demográfico"""
    print("\n=== Análisis Demográfico ===")

    # Por grupo de edad
    edad_stats = df.groupBy("grupo_edad").agg(
        count("*").alias("total_casos"),
        sum("fallecido").alias("fallecidos"),
        (sum("fallecido") / count("*") * 100).alias("tasa_letalidad")
    ).orderBy("grupo_edad")

    # Por sexo
    sexo_stats = df.groupBy("sexo").agg(
        count("*").alias("total_casos"),
        sum("fallecido").alias("fallecidos"),
        avg("edad_anios").alias("edad_promedio")
    )

    # Cruce edad-sexo
    edad_sexo = df.groupBy("grupo_edad", "sexo").agg(
        count("*").alias("casos")
    ).orderBy("grupo_edad", "sexo")

    return edad_stats, sexo_stats, edad_sexo

def analyze_geography(df, spark):
    """Análisis geográfico"""
    print("\n=== Análisis Geográfico ===")

    # Verificar qué columnas existen
    available_cols = df.columns
    has_mysql_data = "region" in available_cols and "poblacion_departamento" in available_cols
    
    if has_mysql_data:
        # Análisis completo con datos de MySQL
        depto_stats = df.groupBy("nombre_departamento", "region", "poblacion_departamento").agg(
            count("*").alias("total_casos"),
            sum("fallecido").alias("fallecidos"),
            (count("*") / first("poblacion_departamento") * 100000).alias("casos_por_100k"),
            (sum("fallecido") / count("*") * 100).alias("tasa_letalidad")
        ).orderBy(desc("total_casos"))

        region_stats = df.groupBy("region").agg(
            count("*").alias("total_casos"),
            sum("fallecido").alias("fallecidos"),
            countDistinct("nombre_departamento").alias("num_departamentos"),
            avg("densidad_poblacional").alias("densidad_promedio")
        ).orderBy(desc("total_casos"))

        municipio_stats = df.groupBy(
            "nombre_municipio",
            "nombre_departamento",
            "poblacion_municipio"
        ).agg(
            count("*").alias("total_casos"),
            sum("fallecido").alias("fallecidos"),
            (count("*") / first("poblacion_municipio") * 100000).alias("incidencia_por_100k")
        ).orderBy(desc("total_casos")).limit(50)
    else:
        # Análisis básico sin datos de MySQL
        print("⚠ Análisis sin datos demográficos complementarios")
        depto_stats = df.groupBy("nombre_departamento").agg(
            count("*").alias("total_casos"),
            sum("fallecido").alias("fallecidos"),
            (sum("fallecido") / count("*") * 100).alias("tasa_letalidad")
        ).orderBy(desc("total_casos"))

        # Region stats no disponible sin MySQL
        region_stats = spark.createDataFrame([], "region: string, total_casos: long, fallecidos: long")

        municipio_stats = df.groupBy(
            "nombre_municipio",
            "nombre_departamento"
        ).agg(
            count("*").alias("total_casos"),
            sum("fallecido").alias("fallecidos")
        ).orderBy(desc("total_casos")).limit(50)

    return depto_stats, region_stats, municipio_stats

def analyze_health_infrastructure(df):
    """Análisis de infraestructura de salud"""
    print("\n=== Análisis Infraestructura ===")

    # Verificar si tenemos datos de infraestructura
    if "num_hospitales" not in df.columns:
        print("⚠ Datos de infraestructura no disponibles (requiere datos de MySQL)")
        return None

    # Relación casos vs capacidad hospitalaria
    infra_stats = df.filter(col("num_hospitales").isNotNull()).groupBy(
        "nombre_departamento"
    ).agg(
        count("*").alias("total_casos"),
        sum("fallecido").alias("fallecidos"),
        first("num_hospitales").alias("hospitales"),
        first("total_camas_uci").alias("camas_uci"),
        first("total_camas_general").alias("camas_general")
    ).withColumn(
        "casos_por_cama_uci",
        col("total_casos") / col("camas_uci")
    ).orderBy(desc("casos_por_cama_uci"))

    return infra_stats

def analyze_type_location(df):
    """Análisis por tipo de contagio y ubicación"""
    print("\n=== Análisis Tipo Contagio y Ubicación ===")

    # Por tipo de contagio
    tipo_stats = df.groupBy("tipo_contagio").agg(
        count("*").alias("total_casos"),
        sum("fallecido").alias("fallecidos"),
        (sum("fallecido") / count("*") * 100).alias("tasa_letalidad")
    ).orderBy(desc("total_casos"))

    # Por ubicación (casa, hospital, etc)
    ubicacion_stats = df.groupBy("ubicacion").agg(
        count("*").alias("total_casos"),
        sum("fallecido").alias("fallecidos"),
        avg("edad_anios").alias("edad_promedio")
    ).orderBy(desc("total_casos"))

    # Estado actual
    estado_stats = df.groupBy("estado").agg(
        count("*").alias("total_casos"),
        avg("edad_anios").alias("edad_promedio")
    )

    return tipo_stats, ubicacion_stats, estado_stats

def create_summary_dashboard(df):
    """Crear resumen ejecutivo"""
    print("\n=== Dashboard Resumen ===")

    # KPIs principales
    kpis = df.agg(
        count("*").alias("total_casos"),
        sum("fallecido").alias("total_fallecidos"),
        sum("recuperado_flag").alias("total_recuperados"),
        countDistinct("nombre_departamento").alias("departamentos_afectados"),
        countDistinct("nombre_municipio").alias("municipios_afectados"),
        avg("edad_anios").alias("edad_promedio"),
        (sum("fallecido") / count("*") * 100).alias("tasa_letalidad_general")
    )

    # Evolución temporal agregada
    evolucion = df.groupBy("anio_reporte", "mes_reporte").agg(
        count("*").alias("casos_nuevos"),
        sum("fallecido").alias("fallecidos"),
        sum("recuperado_flag").alias("recuperados")
    ).withColumn(
        "casos_activos_estimados",
        col("casos_nuevos") - col("fallecidos") - col("recuperados")
    ).orderBy("anio_reporte", "mes_reporte")

    # Top 10 departamentos
    top_deptos = df.groupBy("nombre_departamento").agg(
        count("*").alias("casos")
    ).orderBy(desc("casos")).limit(10)

    return kpis, evolucion, top_deptos

def analyze_mortality_patterns(df):
    """Análisis avanzado de patrones de mortalidad"""
    print("\n=== Análisis Avanzado de Mortalidad ===")
    
    # Mortalidad por grupo de edad y sexo
    mortality_age_sex = df.groupBy("grupo_edad", "sexo").agg(
        count("*").alias("total_casos"),
        sum("fallecido").alias("fallecidos"),
        (sum("fallecido") / count("*") * 100).alias("tasa_mortalidad"),
        avg("edad_anios").alias("edad_promedio")
    ).orderBy("grupo_edad", "sexo")
    
    # Tiempo entre síntomas y diagnóstico
    time_to_diagnosis = df.filter(
        col("fecha_inicio_sintomas").isNotNull() & 
        col("fecha_diagnostico").isNotNull()
    ).withColumn(
        "dias_sintomas_diagnostico",
        datediff(col("fecha_diagnostico"), col("fecha_inicio_sintomas"))
    ).groupBy("estado").agg(
        avg("dias_sintomas_diagnostico").alias("dias_promedio"),
        min("dias_sintomas_diagnostico").alias("dias_minimo"),
        max("dias_sintomas_diagnostico").alias("dias_maximo"),
        count("*").alias("casos")
    )
    
    # CFR (Case Fatality Rate) por mes y departamento
    cfr_temporal = df.groupBy("anio_reporte", "mes_reporte", "nombre_departamento").agg(
        count("*").alias("casos"),
        sum("fallecido").alias("fallecidos"),
        (sum("fallecido") / count("*") * 100).alias("cfr")
    ).filter(col("casos") > 50).orderBy("anio_reporte", "mes_reporte", desc("cfr"))
    
    return mortality_age_sex, time_to_diagnosis, cfr_temporal

def analyze_recovery_patterns(df):
    """Análisis de patrones de recuperación"""
    print("\n=== Análisis de Recuperación ===")
    
    # Tiempo de recuperación por grupo de edad
    recovery_time = df.filter(
        (col("recuperado_flag") == 1) & 
        col("fecha_diagnostico").isNotNull() & 
        col("fecha_recuperacion").isNotNull()
    ).withColumn(
        "dias_recuperacion",
        datediff(col("fecha_recuperacion"), col("fecha_diagnostico"))
    ).groupBy("grupo_edad", "estado").agg(
        avg("dias_recuperacion").alias("dias_promedio_recuperacion"),
        stddev("dias_recuperacion").alias("desviacion_std"),
        count("*").alias("casos_recuperados")
    ).filter(col("casos_recuperados") > 10)
    
    # Tasa de recuperación por tipo de contagio
    recovery_by_source = df.groupBy("tipo_contagio", "ubicacion").agg(
        count("*").alias("total_casos"),
        sum("recuperado_flag").alias("recuperados"),
        sum("fallecido").alias("fallecidos"),
        (sum("recuperado_flag") / count("*") * 100).alias("tasa_recuperacion"),
        (sum("fallecido") / count("*") * 100).alias("tasa_mortalidad")
    ).orderBy(desc("total_casos"))
    
    return recovery_time, recovery_by_source

def analyze_geographic_hotspots(df):
    """Identificar focos geográficos y patrones espaciales"""
    print("\n=== Análisis de Focos Geográficos ===")
    
    # Municipios críticos (alta incidencia y mortalidad)
    if "poblacion_municipio" in df.columns:
        critical_municipalities = df.groupBy("nombre_municipio", "nombre_departamento", "poblacion_municipio").agg(
            count("*").alias("total_casos"),
            sum("fallecido").alias("fallecidos"),
            (count("*") / first("poblacion_municipio") * 100000).alias("incidencia_100k"),
            (sum("fallecido") / count("*") * 100).alias("letalidad")
        ).filter(
            (col("total_casos") > 100) & 
            (col("incidencia_100k") > 500)
        ).orderBy(desc("incidencia_100k"))
        
        # Clustering espacial por letalidad
        dept_severity = df.groupBy("nombre_departamento").agg(
            count("*").alias("casos"),
            sum("fallecido").alias("fallecidos"),
            (sum("fallecido") / count("*") * 100).alias("letalidad")
        ).withColumn(
            "categoria_severidad",
            when(col("letalidad") > 5, "ALTA")
            .when(col("letalidad") > 3, "MEDIA")
            .otherwise("BAJA")
        ).orderBy(desc("letalidad"))
    else:
        critical_municipalities = None
        dept_severity = df.groupBy("nombre_departamento").agg(
            count("*").alias("casos"),
            sum("fallecido").alias("fallecidos"),
            (sum("fallecido") / count("*") * 100).alias("letalidad")
        ).withColumn(
            "categoria_severidad",
            when(col("letalidad") > 5, "ALTA")
            .when(col("letalidad") > 3, "MEDIA")
            .otherwise("BAJA")
        ).orderBy(desc("letalidad"))
    
    return critical_municipalities, dept_severity

def calculate_epidemiological_indicators(df):
    """Calcular indicadores epidemiológicos profesionales"""
    print("\n=== Indicadores Epidemiológicos ===")
    
    # Tasa de ataque por grupo poblacional
    if "poblacion_departamento" in df.columns:
        attack_rate = df.groupBy("nombre_departamento", "grupo_edad").agg(
            count("*").alias("casos"),
            first("poblacion_departamento").alias("poblacion")
        ).withColumn(
            "tasa_ataque",
            (col("casos") / col("poblacion")) * 100000
        ).orderBy(desc("tasa_ataque"))
    else:
        attack_rate = None
    
    # Razón de casos por sexo y edad
    sex_ratio = df.groupBy("grupo_edad").pivot("sexo").agg(
        count("*").alias("casos")
    ).na.fill(0)
    
    # Indicador de gravedad combinado
    severity_index = df.groupBy("nombre_departamento").agg(
        count("*").alias("total_casos"),
        sum("fallecido").alias("fallecidos"),
        (sum(when(col("estado") == "Grave", 1).otherwise(0)) / count("*") * 100).alias("porcentaje_graves"),
        (sum(when(col("ubicacion").isin(["Hospital", "UCI"]), 1).otherwise(0)) / count("*") * 100).alias("porcentaje_hospitalizados"),
        (sum("fallecido") / count("*") * 100).alias("tasa_letalidad")
    ).withColumn(
        "indice_gravedad",
        (col("porcentaje_graves") * 0.4 + 
         col("porcentaje_hospitalizados") * 0.3 + 
         col("tasa_letalidad") * 0.3)
    ).orderBy(desc("indice_gravedad"))
    
    return attack_rate, sex_ratio, severity_index

def save_results(df, bucket, name):
    """Guardar resultados en formato parquet y CSV"""
    base_path = f"gs://{bucket}/analytics/{name}"

    # Guardar Parquet
    df.write.mode("overwrite").parquet(f"{base_path}.parquet")

    # Guardar CSV (para visualización fácil)
    df.coalesce(1).write.mode("overwrite") \
        .option("header", "true") \
        .csv(f"{base_path}.csv")

    print(f"✓ Guardado: {name}")

def main():
    if len(sys.argv) < 3:
        print("Uso: spark-submit analytics_descriptive.py <trusted_bucket> <refined_bucket>")
        sys.exit(1)

    trusted_bucket = sys.argv[1]
    refined_bucket = sys.argv[2]

    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    print("=== Iniciando Análisis Descriptivo ===")

    # Cargar datos
    print("Cargando datos procesados...")
    df = load_processed_data(spark, trusted_bucket)
    print(f"Total registros: {df.count()}")

    # Registrar vista temporal para SparkSQL
    df.createOrReplaceTempView("covid_data")

    # === ANÁLISIS CON DATAFRAMES ===

    # 1. Análisis temporal
    casos_mes, casos_semana = analyze_temporal_trends(df)
    save_results(casos_mes, refined_bucket, "temporal_mensual")
    save_results(casos_semana, refined_bucket, "temporal_semanal")

    # 2. Análisis demográfico
    edad_stats, sexo_stats, edad_sexo = analyze_demographics(df)
    save_results(edad_stats, refined_bucket, "demografia_edad")
    save_results(sexo_stats, refined_bucket, "demografia_sexo")
    save_results(edad_sexo, refined_bucket, "demografia_edad_sexo")

    # 3. Análisis geográfico
    depto_stats, region_stats, municipio_stats = analyze_geography(df, spark)
    save_results(depto_stats, refined_bucket, "geografia_departamentos")
    if region_stats.count() > 0:
        save_results(region_stats, refined_bucket, "geografia_regiones")
    save_results(municipio_stats, refined_bucket, "geografia_municipios_top50")

    # 4. Infraestructura
    infra_stats = analyze_health_infrastructure(df)
    if infra_stats is not None:
        save_results(infra_stats, refined_bucket, "infraestructura_salud")

    # 5. Tipo y ubicación
    tipo_stats, ubicacion_stats, estado_stats = analyze_type_location(df)
    save_results(tipo_stats, refined_bucket, "tipo_contagio")
    save_results(ubicacion_stats, refined_bucket, "ubicacion_casos")
    save_results(estado_stats, refined_bucket, "estado_casos")

    # 6. Dashboard resumen
    kpis, evolucion, top_deptos = create_summary_dashboard(df)
    save_results(kpis, refined_bucket, "dashboard_kpis")
    save_results(evolucion, refined_bucket, "dashboard_evolucion")
    save_results(top_deptos, refined_bucket, "dashboard_top_departamentos")

    # 7. Análisis avanzado de mortalidad
    mortality_age_sex, time_to_diagnosis, cfr_temporal = analyze_mortality_patterns(df)
    save_results(mortality_age_sex, refined_bucket, "mortalidad_edad_sexo")
    save_results(time_to_diagnosis, refined_bucket, "tiempo_diagnostico")
    save_results(cfr_temporal, refined_bucket, "cfr_temporal_departamento")

    # 8. Análisis de recuperación
    recovery_time, recovery_by_source = analyze_recovery_patterns(df)
    save_results(recovery_time, refined_bucket, "tiempo_recuperacion")
    save_results(recovery_by_source, refined_bucket, "recuperacion_por_tipo")

    # 9. Focos geográficos
    critical_municipalities, dept_severity = analyze_geographic_hotspots(df)
    if critical_municipalities is not None:
        save_results(critical_municipalities, refined_bucket, "municipios_criticos")
    save_results(dept_severity, refined_bucket, "severidad_departamentos")

    # 10. Indicadores epidemiológicos
    attack_rate, sex_ratio, severity_index = calculate_epidemiological_indicators(df)
    if attack_rate is not None:
        save_results(attack_rate, refined_bucket, "tasa_ataque")
    save_results(sex_ratio, refined_bucket, "ratio_sexo_edad")
    save_results(severity_index, refined_bucket, "indice_gravedad")

    # === ANÁLISIS CON SPARKSQL ===
    print("\n=== Ejecutando análisis con SparkSQL ===")

    # Verificar columnas disponibles
    has_region = "region" in df.columns

    # Query 1: Casos por departamento con ranking
    if has_region:
        sql_query1 = """
        SELECT 
            nombre_departamento,
            region,
            COUNT(*) as total_casos,
            SUM(fallecido) as fallecidos,
            ROUND(SUM(fallecido) * 100.0 / COUNT(*), 2) as tasa_letalidad,
            RANK() OVER (ORDER BY COUNT(*) DESC) as ranking
        FROM covid_data
        WHERE nombre_departamento IS NOT NULL
        GROUP BY nombre_departamento, region
        ORDER BY total_casos DESC
        """
    else:
        sql_query1 = """
        SELECT 
            nombre_departamento,
            COUNT(*) as total_casos,
            SUM(fallecido) as fallecidos,
            ROUND(SUM(fallecido) * 100.0 / COUNT(*), 2) as tasa_letalidad,
            RANK() OVER (ORDER BY COUNT(*) DESC) as ranking
        FROM covid_data
        WHERE nombre_departamento IS NOT NULL
        GROUP BY nombre_departamento
        ORDER BY total_casos DESC
        """
    result1 = spark.sql(sql_query1)
    save_results(result1, refined_bucket, "sql_ranking_departamentos")

    # Query 2: Evolución de letalidad por mes
    sql_query2 = """
    SELECT 
        anio_reporte,
        mes_reporte,
        COUNT(*) as casos,
        SUM(fallecido) as fallecidos,
        ROUND(SUM(fallecido) * 100.0 / COUNT(*), 2) as tasa_letalidad,
        AVG(edad_anios) as edad_promedio
    FROM covid_data
    GROUP BY anio_reporte, mes_reporte
    ORDER BY anio_reporte, mes_reporte
    """
    result2 = spark.sql(sql_query2)
    save_results(result2, refined_bucket, "sql_evolucion_letalidad")

    # Query 3: Análisis por grupo de edad y región (solo si existe región)
    if has_region:
        sql_query3 = """
        SELECT 
            region,
            grupo_edad,
            COUNT(*) as casos,
            SUM(fallecido) as fallecidos,
            ROUND(AVG(edad_anios), 1) as edad_promedio,
            ROUND(SUM(fallecido) * 100.0 / COUNT(*), 2) as tasa_letalidad
        FROM covid_data
        WHERE region IS NOT NULL AND grupo_edad IS NOT NULL
        GROUP BY region, grupo_edad
        ORDER BY region, grupo_edad
        """
        result3 = spark.sql(sql_query3)
        save_results(result3, refined_bucket, "sql_edad_region")
    else:
        # Alternativa sin región: análisis por grupo de edad y departamento (top 10)
        sql_query3 = """
        SELECT 
            nombre_departamento,
            grupo_edad,
            COUNT(*) as casos,
            SUM(fallecido) as fallecidos,
            ROUND(AVG(edad_anios), 1) as edad_promedio,
            ROUND(SUM(fallecido) * 100.0 / COUNT(*), 2) as tasa_letalidad
        FROM covid_data
        WHERE nombre_departamento IN (
            SELECT nombre_departamento 
            FROM covid_data 
            GROUP BY nombre_departamento 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        ) AND grupo_edad IS NOT NULL
        GROUP BY nombre_departamento, grupo_edad
        ORDER BY nombre_departamento, grupo_edad
        """
        result3 = spark.sql(sql_query3)
        save_results(result3, refined_bucket, "sql_edad_departamento")

    # Query 4: Análisis con window functions
    sql_query4 = """
    SELECT 
        nombre_departamento,
        anio_reporte,
        mes_reporte,
        COUNT(*) as casos_mes,
        SUM(COUNT(*)) OVER (
            PARTITION BY nombre_departamento 
            ORDER BY anio_reporte, mes_reporte
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) as casos_acumulados
    FROM covid_data
    WHERE nombre_departamento IN (
        SELECT nombre_departamento 
        FROM covid_data 
        GROUP BY nombre_departamento 
        ORDER BY COUNT(*) DESC 
        LIMIT 10
    )
    GROUP BY nombre_departamento, anio_reporte, mes_reporte
    ORDER BY nombre_departamento, anio_reporte, mes_reporte
    """
    result4 = spark.sql(sql_query4)
    save_results(result4, refined_bucket, "sql_casos_acumulados")

    print("\n=== Análisis Descriptivo Completado ===")
    print(f"Resultados guardados en gs://{refined_bucket}/analytics/")

    # Mostrar muestra de KPIs
    print("\n=== KPIs Principales ===")
    kpis.show(truncate=False)

    spark.stop()

if __name__ == "__main__":
    main()