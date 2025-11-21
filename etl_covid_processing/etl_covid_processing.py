from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import sys

def create_spark_session():
    """Crear sesión Spark"""
    return SparkSession.builder \
        .appName("COVID-ETL-Processing") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .getOrCreate()

def read_latest_file(spark, bucket, path_pattern):
    """Leer el archivo más reciente de un patrón"""
    from google.cloud import storage
    
    client = storage.Client()
    bucket_obj = client.bucket(bucket)
    blobs = list(bucket_obj.list_blobs(prefix=path_pattern))
    
    if not blobs:
        raise ValueError(f"No se encontraron archivos en {path_pattern}")
    
    # Encontrar el blob más reciente usando sorted
    sorted_blobs = sorted(blobs, key=lambda b: b.time_created, reverse=True)
    latest_blob = sorted_blobs[0]
    full_path = f"gs://{bucket}/{latest_blob.name}"
    
    print(f"Leyendo: {full_path}")
    
    if latest_blob.name.endswith('.json'):
        # JSON de la API viene como array, necesita multiLine=True
        return spark.read.option("multiLine", "true").json(full_path)
    elif latest_blob.name.endswith('.csv'):
        return spark.read.option("header", "true").option("inferSchema", "true").csv(full_path)
    else:
        raise ValueError(f"Formato no soportado: {latest_blob.name}")

def clean_covid_data(df):
    """Limpiar y preparar datos COVID - Maneja formato JSON y CSV"""
    
    # Detectar formato basado en nombres de columnas
    is_csv_format = "fecha reporte web" in df.columns or "Fecha reporte web" in df.columns
    
    if is_csv_format:
        # Formato CSV con espacios - normalizar nombres de columnas primero
        print("  Detectado formato CSV con espacios")
        for col_name in df.columns:
            # Reemplazar espacios por guiones bajos y convertir a minúsculas
            new_name = col_name.strip().lower() \
                .replace(" ", "_") \
                .replace("ó", "o") \
                .replace("í", "i") \
                .replace("á", "a") \
                .replace("é", "e") \
                .replace("ú", "u")
            df = df.withColumnRenamed(col_name, new_name)
    
    # Ahora seleccionar columnas con nombres normalizados
    # Manejar diferentes variantes de nombres de columnas
    def get_col(df, *variants):
        """Obtener columna usando variantes de nombres"""
        for variant in variants:
            if variant in df.columns:
                return col(variant)
        # Si no se encuentra, retornar null
        return lit(None).cast("string")
    
    df_clean = df.select(
        get_col(df, "fecha_reporte_web", "fecha_de_reporte_web").alias("fecha_reporte"),
        get_col(df, "id_de_caso", "id_caso").alias("id_caso"),
        get_col(df, "fecha_de_notificacion", "fecha_de_notificaci_n").alias("fecha_notificacion"),
        get_col(df, "codigo_divipola_departamento", "departamento").alias("codigo_departamento"),
        get_col(df, "nombre_departamento", "departamento_nom").alias("nombre_departamento"),
        get_col(df, "codigo_divipola_municipio", "ciudad_municipio").alias("codigo_municipio"),
        get_col(df, "nombre_municipio", "ciudad_municipio_nom").alias("nombre_municipio"),
        get_col(df, "edad").alias("edad"),
        get_col(df, "unidad_de_medida_de_edad", "unidad_medida").alias("unidad_edad"),
        get_col(df, "sexo").alias("sexo"),
        get_col(df, "tipo_de_contagio", "fuente_tipo_contagio").alias("tipo_contagio"),
        get_col(df, "ubicacion_del_caso", "ubicacion").alias("ubicacion"),
        get_col(df, "estado").alias("estado"),
        get_col(df, "recuperado").alias("recuperado"),
        get_col(df, "fecha_de_diagnostico", "fecha_diagnostico").alias("fecha_diagnostico"),
        get_col(df, "fecha_de_recuperacion", "fecha_recuperado").alias("fecha_recuperacion"),
        get_col(df, "fecha_de_inicio_de_sintomas", "fecha_inicio_sintomas").alias("fecha_inicio_sintomas"),
        get_col(df, "fecha_de_muerte", "fecha_muerte").alias("fecha_muerte")
    )
    
    # Convertir fechas - manejar múltiples formatos
    # Formato JSON: 'yyyy-MM-dd HH:mm:ss'
    # Formato CSV: puede variar
    for fecha_col in ["fecha_reporte", "fecha_notificacion", "fecha_diagnostico", 
                      "fecha_recuperacion", "fecha_inicio_sintomas", "fecha_muerte"]:
        if fecha_col in df_clean.columns:
            df_clean = df_clean.withColumn(
                fecha_col,
                coalesce(
                    to_timestamp(col(fecha_col), "yyyy-MM-dd HH:mm:ss"),
                    to_timestamp(col(fecha_col), "yyyy-MM-dd"),
                    to_timestamp(col(fecha_col), "dd/MM/yyyy")
                ).cast("date")
            )
    
    # Normalizar edad a años
    df_clean = df_clean.withColumn(
        "edad_anios",
        when(col("unidad_edad") == "1", col("edad").cast("double"))  # Años
        .when(col("unidad_edad") == "2", col("edad").cast("double") / 12)  # Meses
        .when(col("unidad_edad") == "3", col("edad").cast("double") / 365)  # Días
        .otherwise(None)
    )
    
    # Limpiar valores nulos y duplicados
    df_clean = df_clean.dropDuplicates(["id_caso"]) \
        .filter(col("codigo_departamento").isNotNull())
    
    return df_clean

def join_with_complementary_data(spark, covid_df, bucket):
    """Unir datos COVID con datos complementarios (opcional)"""
    try:
        # Intentar leer datos de MySQL
        departamentos_df = read_latest_file(spark, bucket, "mysql/departamentos/")
        municipios_df = read_latest_file(spark, bucket, "mysql/municipios/")
        hospitales_df = read_latest_file(spark, bucket, "mysql/hospitales/")
        
        print(f"   Departamentos MySQL leídos: {departamentos_df.count()}")
        print(f"   Municipios MySQL leídos: {municipios_df.count()}")
        
        # Normalizar código_departamento a 2 dígitos con ceros a la izquierda
        covid_df = covid_df.withColumn(
            "codigo_departamento_norm",
            lpad(col("codigo_departamento").cast("string"), 2, "0")
        )
        
        # Normalizar nombres de departamentos para mejorar el match
        # Aplicar correcciones comunes de nombres
        covid_df = covid_df.withColumn(
            "nombre_departamento_norm",
            when(upper(trim(col("nombre_departamento"))).isin("BOGOTA", "BOGOTÁ", "BOGOTA D.E."), "BOGOTA D.C.")
            .when(upper(trim(col("nombre_departamento"))) == "BARRANQUILLA", "ATLANTICO")
            .when(upper(trim(col("nombre_departamento"))) == "CARTAGENA", "BOLIVAR")
            .when(upper(trim(col("nombre_departamento"))).isin("STA MARTA D.E.", "SANTA MARTA"), "MAGDALENA")
            .when(upper(trim(col("nombre_departamento"))).isin("N SANTANDER", "NORTE SANTANDER"), "NORTE DE SANTANDER")
            .when(upper(trim(col("nombre_departamento"))).contains("SAN ANDRES"), "SAN ANDRES")
            .when(upper(trim(col("nombre_departamento"))).isin("LA GUAJIRA", "GUAJIRA"), "GUAJIRA")
            .otherwise(upper(trim(col("nombre_departamento"))))
        )
        
        # Join con departamentos usando código normalizado Y nombre como fallback
        df_enriched = covid_df.join(
            departamentos_df.select(
                col("codigo_dane").alias("cod_depto"),
                upper(trim(col("nombre_departamento"))).alias("nombre_depto_mysql"),
                col("poblacion_2020").alias("poblacion_departamento"),
                col("densidad_poblacional"),
                col("region")
            ),
            (covid_df.codigo_departamento_norm == col("cod_depto")) | 
            (covid_df.nombre_departamento_norm == col("nombre_depto_mysql")),
            "left"
        ).drop("cod_depto", "nombre_depto_mysql", "codigo_departamento_norm", "nombre_departamento_norm")
        
        # Normalizar código_municipio a 5 dígitos
        df_enriched = df_enriched.withColumn(
            "codigo_municipio_norm",
            lpad(col("codigo_municipio").cast("string"), 5, "0")
        )
        
        # Join con municipios
        df_enriched = df_enriched.join(
            municipios_df.select(
                col("codigo_dane").alias("cod_mun"),
                col("poblacion_2020").alias("poblacion_municipio"),
                col("altitud_msnm"),
                col("categoria").alias("categoria_municipio")
            ),
            df_enriched.codigo_municipio_norm == col("cod_mun"),
            "left"
        ).drop("cod_mun", "codigo_municipio_norm")
        
        # Agregar información de hospitales por municipio
        hospitales_agg = hospitales_df.groupBy("id_municipio").agg(
            count("*").alias("num_hospitales"),
            sum("camas_uci").alias("total_camas_uci"),
            sum("camas_general").alias("total_camas_general")
        )
        
        df_enriched = df_enriched.join(
            hospitales_agg,
            df_enriched.codigo_municipio == hospitales_agg.id_municipio,
            "left"
        ).drop("id_municipio")
        
        # Verificar cuántos registros tienen datos enriquecidos
        enriched_count = df_enriched.filter(col("poblacion_departamento").isNotNull()).count()
        total_count = df_enriched.count()
        print(f"✓ Datos enriquecidos con información complementaria")
        print(f"   {enriched_count}/{total_count} registros enriquecidos con datos de MySQL")
        
        return df_enriched
        
    except ValueError as e:
        print(f"⚠ Advertencia: No se encontraron datos complementarios de MySQL: {e}")
        print("⚠ Continuando sin enriquecimiento de datos...")
        return covid_df
    except Exception as e:
        print(f"⚠ Error al enriquecer datos: {e}")
        print("⚠ Continuando sin enriquecimiento de datos...")
        return covid_df

def calculate_metrics(df):
    """Calcular métricas adicionales"""
    df_metrics = df.withColumn(
        "grupo_edad",
        when(col("edad_anios") < 18, "0-17")
        .when(col("edad_anios") < 30, "18-29")
        .when(col("edad_anios") < 50, "30-49")
        .when(col("edad_anios") < 65, "50-64")
        .otherwise("65+")
    )
    
    df_metrics = df_metrics.withColumn(
        "anio_reporte",
        year(col("fecha_reporte"))
    ).withColumn(
        "mes_reporte",
        month(col("fecha_reporte"))
    ).withColumn(
        "semana_reporte",
        weekofyear(col("fecha_reporte"))
    )
    
    # Indicadores
    df_metrics = df_metrics.withColumn(
        "fallecido",
        when(col("estado") == "Fallecido", 1).otherwise(0)
    ).withColumn(
        "recuperado_flag",
        when(col("recuperado") == "Recuperado", 1).otherwise(0)
    )
    
    return df_metrics

def main():
    """Función principal ETL"""
    if len(sys.argv) < 3:
        print("Uso: spark-submit etl_covid_processing.py <raw_bucket> <trusted_bucket>")
        sys.exit(1)
    
    raw_bucket = sys.argv[1]
    trusted_bucket = sys.argv[2]
    
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    
    print("=== Iniciando ETL COVID ===")
    
    # 1. Leer datos crudos COVID
    print("1. Leyendo datos COVID...")
    covid_df = read_latest_file(spark, raw_bucket, "api/casos/")
    print(f"   Registros leídos: {covid_df.count()}")
    
    # 2. Limpiar datos
    print("2. Limpiando datos...")
    covid_clean = clean_covid_data(covid_df)
    print(f"   Registros después de limpieza: {covid_clean.count()}")
    
    # 3. Enriquecer con datos complementarios
    print("3. Enriqueciendo con datos complementarios...")
    covid_enriched = join_with_complementary_data(spark, covid_clean, raw_bucket)
    
    # 4. Calcular métricas
    print("4. Calculando métricas...")
    covid_final = calculate_metrics(covid_enriched)
    
    # 5. Guardar en zona Trusted
    print("5. Guardando en zona Trusted...")
    output_path = f"gs://{trusted_bucket}/covid_processed/"
    
    covid_final.write \
        .mode("overwrite") \
        .partitionBy("anio_reporte", "mes_reporte") \
        .parquet(output_path)
    
    print(f" ETL completado. Datos guardados en {output_path}")
    print(f"   Total registros procesados: {covid_final.count()}")
    
    # Mostrar muestra
    print("\n=== Muestra de datos procesados ===")
    # Mostrar solo columnas que existen (puede no tener datos de MySQL)
    display_cols = ["fecha_reporte", "nombre_departamento", "nombre_municipio",
                    "edad_anios", "sexo", "estado", "grupo_edad", "fallecido", "recuperado_flag"]
    covid_final.select(*display_cols).show(10, truncate=False)
    
    spark.stop()

if __name__ == "__main__":
    main()