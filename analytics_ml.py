from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.ml.feature import VectorAssembler, StringIndexer, StandardScaler
from pyspark.ml.classification import LogisticRegression, RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
from pyspark.ml.clustering import KMeans
from pyspark.ml import Pipeline
import sys

def create_spark_session():
    return SparkSession.builder \
        .appName("COVID-Analytics-ML") \
        .config("spark.sql.adaptive.enabled", "true") \
        .getOrCreate()

def prepare_ml_data(df):
    """Preparar datos para ML"""
    print("\n=== Preparando datos para ML ===")
    
    # Filtrar datos completos
    df_ml = df.filter(
        col("edad_anios").isNotNull() & 
        col("sexo").isNotNull() &
        col("nombre_departamento").isNotNull() &
        col("tipo_contagio").isNotNull()
    )
    
    # Crear features adicionales
    df_ml = df_ml.withColumn(
        "dias_notificacion_diagnostico",
        datediff(col("fecha_notificacion"), col("fecha_diagnostico"))
    )
    
    return df_ml

def predict_mortality_risk(df):
    """Modelo de predicción de riesgo de mortalidad"""
    print("\n=== Modelo: Predicción de Mortalidad ===")
    
    # Preparar features
    df_model = df.withColumn("label", col("fallecido").cast("double"))
    
    # Check available columns
    has_region = "region" in df.columns
    has_density = "densidad_poblacional" in df.columns
    
    print(f"Columnas disponibles - region: {has_region}, densidad: {has_density}")
    
    # Indexar variables categóricas (solo las disponibles)
    indexers = [
        StringIndexer(inputCol="sexo", outputCol="sexo_idx", handleInvalid="keep"),
        StringIndexer(inputCol="tipo_contagio", outputCol="tipo_contagio_idx", handleInvalid="keep"),
        StringIndexer(inputCol="ubicacion", outputCol="ubicacion_idx", handleInvalid="keep")
    ]
    
    if has_region:
        indexers.append(StringIndexer(inputCol="region", outputCol="region_idx", handleInvalid="keep"))
    
    # Assembler de features (solo columnas disponibles)
    feature_cols = [
        "edad_anios", 
        "sexo_idx", 
        "tipo_contagio_idx",
        "ubicacion_idx"
    ]
    
    if has_region:
        feature_cols.append("region_idx")
    if has_density:
        feature_cols.append("densidad_poblacional")
    
    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features_raw",
        handleInvalid="skip"
    )
    
    # Escalador
    scaler = StandardScaler(
        inputCol="features_raw",
        outputCol="features",
        withStd=True,
        withMean=True
    )
    
    # Modelo: Random Forest
    rf = RandomForestClassifier(
        labelCol="label",
        featuresCol="features",
        numTrees=100,
        maxDepth=10,
        seed=42
    )
    
    # Pipeline
    pipeline = Pipeline(stages=indexers + [assembler, scaler, rf])
    
    # Split train/test
    train_df, test_df = df_model.randomSplit([0.8, 0.2], seed=42)
    
    print(f"Entrenamiento: {train_df.count()} registros")
    print(f"Prueba: {test_df.count()} registros")
    
    # Entrenar
    print("Entrenando modelo...")
    model = pipeline.fit(train_df)
    
    # Predicciones
    predictions = model.transform(test_df)
    
    # Evaluación
    evaluator_auc = BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC")
    evaluator_acc = MulticlassClassificationEvaluator(labelCol="label", metricName="accuracy")
    evaluator_f1 = MulticlassClassificationEvaluator(labelCol="label", metricName="f1")
    
    auc = evaluator_auc.evaluate(predictions)
    accuracy = evaluator_acc.evaluate(predictions)
    f1 = evaluator_f1.evaluate(predictions)
    
    print(f"\n--- Métricas del Modelo ---")
    print(f"AUC-ROC: {auc:.4f}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"F1-Score: {f1:.4f}")
    
    # Importancia de features
    rf_model = model.stages[-1]
    feature_importance = list(zip(feature_cols, rf_model.featureImportances.toArray()))
    feature_importance.sort(key=lambda x: x[1], reverse=True)
    
    print("\n--- Importancia de Features ---")
    for feat, imp in feature_importance:
        print(f"{feat}: {imp:.4f}")
    
    # Resultados (sin columnas complejas para CSV)
    results = predictions.select(
        "id_caso",
        "edad_anios",
        "sexo",
        "nombre_departamento",
        "label",
        "prediction"
        # Removemos "probability" porque es un tipo struct que no se puede guardar en CSV
    )
    
    return results, {
        "auc": auc,
        "accuracy": accuracy,
        "f1": f1,
        "feature_importance": feature_importance
    }

def cluster_departments(df):
    """Clustering de departamentos por características COVID"""
    print("\n=== Modelo: Clustering de Departamentos ===")
    
    # Check if we have the required columns
    has_poblacion = "poblacion_departamento" in df.columns
    has_densidad = "densidad_poblacional" in df.columns
    
    if not has_poblacion or not has_densidad:
        print("⚠️ Saltando clustering: requiere datos demográficos de MySQL (poblacion_departamento, densidad_poblacional)")
        return None, None
    
    # Agregación por departamento
    dept_features = df.groupBy("nombre_departamento").agg(
        count("*").alias("total_casos"),
        avg("edad_anios").alias("edad_promedio"),
        (sum("fallecido") / count("*") * 100).alias("tasa_letalidad"),
        (sum("recuperado_flag") / count("*") * 100).alias("tasa_recuperacion"),
        first("poblacion_departamento").alias("poblacion"),
        first("densidad_poblacional").alias("densidad"),
        (count("*") / first("poblacion_departamento") * 100000).alias("incidencia_100k")
    ).filter(col("total_casos") > 100)  # Filtrar departamentos con casos mínimos
    
    # Assembler
    feature_cols = [
        "edad_promedio",
        "tasa_letalidad",
        "tasa_recuperacion",
        "densidad",
        "incidencia_100k"
    ]
    
    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features_raw",
        handleInvalid="skip"
    )
    
    scaler = StandardScaler(
        inputCol="features_raw",
        outputCol="features",
        withStd=True,
        withMean=True
    )
    
    # K-Means
    kmeans = KMeans(
        k=4,
        featuresCol="features",
        predictionCol="cluster",
        seed=42
    )
    
    # Pipeline y entrenamiento
    pipeline = Pipeline(stages=[assembler, scaler, kmeans])
    model = pipeline.fit(dept_features)
    
    # Predicciones
    clustered = model.transform(dept_features)
    
    # Análisis de clusters
    cluster_analysis = clustered.groupBy("cluster").agg(
        count("*").alias("num_departamentos"),
        avg("total_casos").alias("casos_promedio"),
        avg("tasa_letalidad").alias("letalidad_promedio"),
        avg("incidencia_100k").alias("incidencia_promedio")
    ).orderBy("cluster")
    
    print("\n--- Análisis de Clusters ---")
    cluster_analysis.show(truncate=False)
    
    # Departamentos por cluster
    print("\n--- Departamentos por Cluster ---")
    for i in range(4):
        print(f"\nCluster {i}:")
        clustered.filter(col("cluster") == i) \
            .select("nombre_departamento", "total_casos", "tasa_letalidad") \
            .show(truncate=False)
    
    return clustered, cluster_analysis

def save_ml_results(df, bucket, name):
    """Guardar resultados ML"""
    path = f"gs://{bucket}/ml/{name}"
    
    # Guardar Parquet (soporta todos los tipos)
    df.write.mode("overwrite").parquet(f"{path}.parquet")
    
    # Para CSV, excluir columnas complejas (features, rawPrediction, probability)
    cols_to_save = [c for c in df.columns if c not in ['features', 'features_raw', 'rawPrediction', 'probability']]
    df.select(*cols_to_save).coalesce(1).write.mode("overwrite").option("header", "true").csv(f"{path}.csv")
    
    print(f"✓ ML guardado: {name}")

def predict_severity_classification(df):
    """Clasificación multiclase de severidad de casos"""
    print("\n=== Modelo: Clasificación de Severidad ===")
    
    # Preparar labels (Leve, Moderado, Grave)
    df_model = df.withColumn(
        "label",
        when(col("estado") == "Grave", 2.0)
        .when(col("estado") == "Moderado", 1.0)
        .otherwise(0.0)  # Leve o Asintomático
    )
    
    # Features
    indexers = [
        StringIndexer(inputCol="sexo", outputCol="sexo_idx", handleInvalid="keep"),
        StringIndexer(inputCol="tipo_contagio", outputCol="tipo_contagio_idx", handleInvalid="keep"),
        StringIndexer(inputCol="grupo_edad", outputCol="grupo_edad_idx", handleInvalid="keep")
    ]
    
    feature_cols = ["edad_anios", "sexo_idx", "tipo_contagio_idx", "grupo_edad_idx"]
    
    if "densidad_poblacional" in df.columns:
        feature_cols.append("densidad_poblacional")
    
    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features",
        handleInvalid="skip"
    )
    
    # Modelo: Random Forest Multiclass
    rf = RandomForestClassifier(
        labelCol="label",
        featuresCol="features",
        numTrees=100,
        maxDepth=8,
        seed=42
    )
    
    pipeline = Pipeline(stages=indexers + [assembler, rf])
    
    # Split
    train_df, test_df = df_model.randomSplit([0.8, 0.2], seed=42)
    
    print(f"Entrenamiento: {train_df.count()}, Prueba: {test_df.count()}")
    
    # Entrenar
    model = pipeline.fit(train_df)
    predictions = model.transform(test_df)
    
    # Evaluación
    evaluator_acc = MulticlassClassificationEvaluator(labelCol="label", metricName="accuracy")
    evaluator_f1 = MulticlassClassificationEvaluator(labelCol="label", metricName="f1")
    evaluator_precision = MulticlassClassificationEvaluator(labelCol="label", metricName="weightedPrecision")
    evaluator_recall = MulticlassClassificationEvaluator(labelCol="label", metricName="weightedRecall")
    
    accuracy = evaluator_acc.evaluate(predictions)
    f1 = evaluator_f1.evaluate(predictions)
    precision = evaluator_precision.evaluate(predictions)
    recall = evaluator_recall.evaluate(predictions)
    
    print(f"\n--- Métricas Clasificación Severidad ---")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"F1-Score: {f1:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    
    results = predictions.select(
        "id_caso",
        "edad_anios",
        "sexo",
        "estado",
        "label",
        "prediction"
    )
    
    return results, {
        "accuracy": accuracy,
        "f1": f1,
        "precision": precision,
        "recall": recall
    }

def predict_hospitalization_risk(df):
    """Predicción de riesgo de hospitalización"""
    print("\n=== Modelo: Riesgo de Hospitalización ===")
    
    # Label: si está en Hospital o UCI = 1, Casa = 0
    df_model = df.withColumn(
        "label",
        when(col("ubicacion").isin(["Hospital", "UCI", "Hospital UCI"]), 1.0).otherwise(0.0)
    ).filter(col("ubicacion").isNotNull())
    
    # Verificar si hay al menos 2 clases
    label_counts = df_model.groupBy("label").count().collect()
    unique_labels = len(label_counts)
    
    print(f"Clases encontradas: {unique_labels}")
    for row in label_counts:
        print(f"  Label {int(row['label'])}: {row['count']} casos")
    
    # Si solo hay una clase, retornar resultados básicos sin entrenar
    if unique_labels < 2:
        print("⚠️  Solo una clase presente, no se puede entrenar modelo de clasificación binaria")
        # Retornar datos básicos sin predicción
        results = df_model.select(
            "id_caso",
            "edad_anios",
            "ubicacion",
            "label"
        ).limit(100)
        return results, {
            "auc": 0.0,
            "accuracy": 1.0 if unique_labels == 1 else 0.0,
            "warning": "Single class - model not trained"
        }
    
    # Features
    indexers = [
        StringIndexer(inputCol="sexo", outputCol="sexo_idx", handleInvalid="keep"),
        StringIndexer(inputCol="tipo_contagio", outputCol="tipo_contagio_idx", handleInvalid="keep")
    ]
    
    feature_cols = ["edad_anios", "sexo_idx", "tipo_contagio_idx"]
    
    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features",
        handleInvalid="skip"
    )
    
    # Logistic Regression (más interpretable)
    lr = LogisticRegression(
        labelCol="label",
        featuresCol="features",
        maxIter=100
    )
    
    pipeline = Pipeline(stages=indexers + [assembler, lr])
    
    train_df, test_df = df_model.randomSplit([0.8, 0.2], seed=42)
    
    print(f"Entrenamiento: {train_df.count()}, Prueba: {test_df.count()}")
    
    model = pipeline.fit(train_df)
    predictions = model.transform(test_df)
    
    # Evaluación con manejo de error
    try:
        evaluator_auc = BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC")
        auc = evaluator_auc.evaluate(predictions)
    except Exception as e:
        print(f"⚠️  No se pudo calcular AUC: {str(e)}")
        auc = 0.0
    
    evaluator_acc = MulticlassClassificationEvaluator(labelCol="label", metricName="accuracy")
    accuracy = evaluator_acc.evaluate(predictions)
    
    print(f"\n--- Métricas Hospitalización ---")
    print(f"AUC-ROC: {auc:.4f}")
    print(f"Accuracy: {accuracy:.4f}")
    
    results = predictions.select(
        "id_caso",
        "edad_anios",
        "ubicacion",
        "label",
        "prediction"
    )
    
    return results, {"auc": auc, "accuracy": accuracy}

def cluster_age_groups(df):
    """Clustering de grupos poblacionales por comportamiento COVID"""
    print("\n=== Modelo: Clustering Grupos Poblacionales ===")
    
    # Agregación por grupo de edad y sexo
    group_features = df.groupBy("grupo_edad", "sexo").agg(
        count("*").alias("total_casos"),
        avg("edad_anios").alias("edad_promedio"),
        (sum("fallecido") / count("*") * 100).alias("tasa_mortalidad"),
        (sum("recuperado_flag") / count("*") * 100).alias("tasa_recuperacion"),
        (sum(when(col("ubicacion").isin(["Hospital", "UCI"]), 1).otherwise(0)) / count("*") * 100).alias("tasa_hospitalizacion")
    ).filter(col("total_casos") > 100)
    
    feature_cols = [
        "edad_promedio",
        "tasa_mortalidad",
        "tasa_recuperacion",
        "tasa_hospitalizacion"
    ]
    
    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features_raw",
        handleInvalid="skip"
    )
    
    scaler = StandardScaler(
        inputCol="features_raw",
        outputCol="features",
        withStd=True,
        withMean=True
    )
    
    kmeans = KMeans(k=3, featuresCol="features", predictionCol="cluster", seed=42)
    
    pipeline = Pipeline(stages=[assembler, scaler, kmeans])
    model = pipeline.fit(group_features)
    clustered = model.transform(group_features)
    
    # Análisis
    cluster_analysis = clustered.groupBy("cluster").agg(
        count("*").alias("num_grupos"),
        avg("tasa_mortalidad").alias("mortalidad_promedio"),
        avg("tasa_hospitalizacion").alias("hospitalizacion_promedio")
    ).orderBy("cluster")
    
    print("\n--- Análisis Clusters Poblacionales ---")
    cluster_analysis.show(truncate=False)
    
    return clustered, cluster_analysis

def main():
    if len(sys.argv) < 3:
        print("Uso: spark-submit analytics_ml.py <trusted_bucket> <refined_bucket>")
        sys.exit(1)
    
    trusted_bucket = sys.argv[1]
    refined_bucket = sys.argv[2]
    
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    
    print("=== Iniciando Análisis con Machine Learning ===")
    
    # Cargar datos
    path = f"gs://{trusted_bucket}/covid_processed/"
    df = spark.read.parquet(path)
    print(f"Total registros: {df.count()}")
    
    # Preparar datos
    df_ml = prepare_ml_data(df)
    print(f"Registros para ML: {df_ml.count()}")
    
    # Modelo 1: Predicción de mortalidad
    mortality_predictions, mortality_metrics = predict_mortality_risk(df_ml)
    save_ml_results(mortality_predictions, refined_bucket, "predictions_mortality")
    
    # Modelo 2: Clasificación de severidad
    severity_predictions, severity_metrics = predict_severity_classification(df_ml)
    save_ml_results(severity_predictions, refined_bucket, "predictions_severity")
    
    # Modelo 3: Riesgo de hospitalización
    hospitalization_predictions, hospitalization_metrics = predict_hospitalization_risk(df_ml)
    save_ml_results(hospitalization_predictions, refined_bucket, "predictions_hospitalization")
    
    # Modelo 4: Clustering de departamentos
    dept_clusters, dept_cluster_analysis = cluster_departments(df_ml)
    if dept_clusters is not None:
        save_ml_results(dept_clusters, refined_bucket, "clusters_departamentos")
        save_ml_results(dept_cluster_analysis, refined_bucket, "clusters_analisis_departamentos")
    
    # Modelo 5: Clustering de grupos poblacionales
    age_clusters, age_cluster_analysis = cluster_age_groups(df_ml)
    save_ml_results(age_clusters, refined_bucket, "clusters_grupos_poblacionales")
    save_ml_results(age_cluster_analysis, refined_bucket, "clusters_analisis_poblacional")
    
    # Guardar todas las métricas
    metrics_data = {
        "mortality_auc": float(mortality_metrics["auc"]),
        "mortality_accuracy": float(mortality_metrics["accuracy"]),
        "mortality_f1": float(mortality_metrics["f1"]),
        "severity_accuracy": float(severity_metrics["accuracy"]),
        "severity_f1": float(severity_metrics["f1"]),
        "severity_precision": float(severity_metrics["precision"]),
        "severity_recall": float(severity_metrics["recall"]),
        "hospitalization_auc": float(hospitalization_metrics["auc"]),
        "hospitalization_accuracy": float(hospitalization_metrics["accuracy"])
    }
    metrics_df = spark.createDataFrame([metrics_data])
    save_ml_results(metrics_df, refined_bucket, "ml_metrics_completas")
    
    print("\n=== Análisis ML Completado ===")
    print(f"Resultados guardados en gs://{refined_bucket}/ml/")
    print("\n--- Resumen de Modelos ---")
    print(f"1. Mortalidad: AUC={mortality_metrics['auc']:.4f}, F1={mortality_metrics['f1']:.4f}")
    print(f"2. Severidad: Acc={severity_metrics['accuracy']:.4f}, F1={severity_metrics['f1']:.4f}")
    print(f"3. Hospitalización: AUC={hospitalization_metrics['auc']:.4f}")
    print(f"4. Clusters Departamentos: {'OK' if dept_clusters is not None else 'SKIP'}")
    print(f"5. Clusters Poblacionales: OK")
    
    spark.stop()

if __name__ == "__main__":
    main()