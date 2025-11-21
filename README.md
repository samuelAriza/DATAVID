#  DATAVID: Pipeline Automático de Análisis de Datos COVID-19 Colombia

## Universidad EAFIT - ST0263 Tópicos Especiales en Telemática
### Trabajo 3: Automatización Big Data en Google Cloud Platform

---

##  Tabla de Contenidos

1. [Descripción General](#-descripción-general)
2. [Arquitectura del Sistema](#-arquitectura-del-sistema)
3. [Requisitos del Proyecto](#-requisitos-del-proyecto)
4. [Tecnologías Utilizadas](#-tecnologías-utilizadas)
5. [Estructura del Repositorio](#-estructura-del-repositorio)
6. [Prerequisitos](#-prerequisitos)
7. [Instalación y Configuración](#-instalación-y-configuración)
8. [Despliegue del Pipeline](#-despliegue-del-pipeline)
9. [Ejecución y Monitoreo](#-ejecución-y-monitoreo)
10. [Dashboard de Visualización](#-dashboard-de-visualización)
11. [Verificación de Resultados](#-verificación-de-resultados)
12. [API REST - Endpoints](#-api-rest---endpoints)
13. [Análisis Implementados](#-análisis-implementados)
14. [Modelos de Machine Learning](#-modelos-de-machine-learning)
15. [Troubleshooting](#-troubleshooting)
16. [Costos Estimados](#-costos-estimados)
17. [Autores](#-autores)

---

##  Descripción General

Este proyecto implementa un **pipeline completo de Big Data** para el análisis automatizado de datos de COVID-19 en Colombia, cumpliendo con los estándares de producción de ingeniería de datos moderna. El sistema integra múltiples fuentes de datos, realiza procesamiento ETL con Apache Spark, ejecuta análisis descriptivos avanzados y modelos de Machine Learning, todo de forma completamente automatizada.

### Características Principales

-  **Ingesta automática** desde 2+ fuentes heterogéneas (API REST + MySQL)
-  **Procesamiento ETL** con Apache Spark en clusters efímeros
-  **29 análisis epidemiológicos** profesionales con DataFrames y SparkSQL
-  **5 modelos de Machine Learning** con SparkML (clasificación + clustering)
-  **Arquitectura de 3 zonas**: Raw → Trusted → Refined
-  **Salida dual**: BigQuery (análisis SQL) + API REST (integración)
-  **100% automatizado**: Sin intervención humana
-  **Clusters efímeros**: Auto-creación y auto-destrucción
-  **Programación semanal**: Cloud Scheduler (Lunes 4:00 AM)

### Datos Procesados

- **100,000 casos** de COVID-19 en Colombia
- **36 departamentos** con información demográfica
- **894 municipios** con datos de población y altitud
- **20 hospitales** con capacidad e infraestructura
- Período: Mayo 2020 - Enero 2022

---

##  Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INGESTA AUTOMÁTICA                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │  API Ministerio│  │  Cloud SQL     │  │  CSV Históricos│         │
│  │  Salud Colombia│  │  MySQL         │  │  (Backup)      │         │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘         │
│          │                   │                    │                 │
│          └───────────────────┴────────────────────┘                 │
│                              │                                      │
│                   Cloud Functions (Gen2)                            │
│                   - ingest-covid-data (3600s, 2GB)                  │
│                   - ingest-mysql-data (600s, 512MB)                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                        ZONA RAW (3.74 GB)                           │
│  gs://datavid-raw-zone/                                             │
│  ├── api/casos/                  (JSON - 100K registros)            │
│  ├── csv/historicos/             (CSV - backup)                     │
│  └── mysql/                      (JSON - 3 tablas)                  │
│      ├── departamentos/          (36 registros)                     │
│      ├── municipios/             (894 registros)                    │
│      └── hospitales/             (20 registros)                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                    PROCESAMIENTO ETL (PySpark)                      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              Dataproc Cluster (Efímero)                     │    │
│  │  - Master: n1-standard-4 (4 vCPU, 15 GB RAM)                │    │
│  │  - Workers: 2x n1-standard-4                                │    │
│  │  - Duración: ~20-25 minutos                                 │    │
│  │  - Auto-creado y auto-destruido por Workflow                │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Script: etl_covid_processing.py (10.14 KiB)                        │
│  - Lectura de múltiples fuentes                                     │
│  - JOIN de COVID + MySQL (población, región, densidad)              │
│  - Limpieza y transformación                                        │
│  - Particionamiento por año/mes                                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                    ZONA TRUSTED (Particionada)                      │
│  gs://datavid-trusted-zone/covid_processed/                         │
│  ├── anio_reporte=2020/                                             │
│  │   ├── mes_reporte=5/  (2,704 casos)                              │
│  │   ├── mes_reporte=6/  (2,759 casos)                              │
│  │   ├── ...                                                        │
│  │   └── mes_reporte=12/ (16,895 casos)                             │
│  ├── anio_reporte=2021/ (10,705 casos)                              │
│  └── anio_reporte=2022/ (19 casos)                                  │
│                                                                     │
│  Formato: Parquet (snappy compression)                              │
│  Esquema: 25 columnas (COVID + MySQL enriched)                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
┌───────────────▼──────────────┐  ┌──────────▼──────────────────────┐
│   ANALYTICS DESCRIPTIVO      │  │   MACHINE LEARNING              │
│   (PySpark DataFrames + SQL) │  │   (SparkML)                     │
│                              │  │                                 │
│  Script: analytics_          │  │  Script: analytics_ml.py        │
│          descriptive.py      │  │          (18.41 KiB)            │
│          (21.4 KiB)          │  │                                 │
│                              │  │  ┌───────────────────────────┐  │
│  ┌────────────────────────┐  │  │  │ MODELOS SUPERVISADOS:     │  │
│  │ 10 FUNCIONES ANALYTICS:│  │  │  │                           │  │
│  │                        │  │  │  │ 1. Random Forest          │  │
│  │ 1. Temporal            │  │  │  │    - Mortalidad (binary)  │  │
│  │ 2. Demográfico         │  │  │  │    - Métricas: AUC, F1    │  │
│  │ 3. Geográfico          │  │  │  │                           │  │
│  │ 4. Mortalidad          │  │  │  │ 2. Random Forest          │  │
│  │ 5. Recuperación        │  │  │  │    - Severidad (3-class)  │  │
│  │ 6. Hotspots            │  │  │  │    - Leve/Moderado/Grave  │  │
│  │ 7. Epidemiología       │  │  │  │                           │  │
│  │ 8. Dashboard KPIs      │  │  │  │ 3. Logistic Regression    │  │
│  │ 9. Evolución CFR       │  │  │  │    - Hospitalización      │  │
│  │ 10. Infraestructura    │  │  │  │                           │  │
│  └────────────────────────┘  │  │  └───────────────────────────┘  │
│                              │  │                                 │
│  ┌────────────────────────┐  │  │  ┌───────────────────────────┐  │
│  │ 4 QUERIES SparkSQL:    │  │  │  │ MODELOS NO SUPERVISADOS:  │  │
│  │                        │  │  │  │                           │  │
│  │ 1. Ranking deptos      │  │  │  │ 4. K-Means (k=4)          │  │
│  │ 2. Letalidad evolutiva │  │  │  │    - Clustering deptos    │  │
│  │ 3. Edad-región cross   │  │  │  │    - Features: casos,     │  │
│  │ 4. Casos acumulados    │  │  │  │      letalidad, edad      │  │
│  └────────────────────────┘  │  │  │                           │  │
│                              │  │  │ 5. K-Means (k=3)          │  │
│  OUTPUT: 29 datasets         │  │  │    - Clustering poblac.   │  │
└──────────────┬───────────────┘  │  │    - Grupos riesgo        │  │
               │                  │  │                           │  │
               │                  │  └───────────────────────────┘  │
               │                  │                                 │
               │                  │  OUTPUT: 5 modelos + métricas   │
               │                  └────────────┬────────────────────┘
               │                               │
┌──────────────▼───────────────────────────────▼──────────────────────┐
│                      ZONA REFINED (Resultados)                      │
│  gs://datavid-refined-zone/                                         │
│  ├── analytics/ (29 datasets)                                       │
│  │   ├── temporal_mensual.parquet                                   │
│  │   ├── demografia_edad.parquet                                    │
│  │   ├── geografia_departamentos.parquet                            │
│  │   ├── dashboard_kpis.parquet                                     │
│  │   ├── ... (25 más)                                               │
│  │                                                                  │
│  └── ml/ (5 modelos + análisis)                                     │
│      ├── predictions_mortality.parquet                              │
│      ├── predictions_severity.parquet                               │
│      ├── predictions_hospitalization.parquet                        │
│      ├── clusters_departamentos.parquet                             │
│      ├── clusters_grupos_poblacionales.parquet                      │
│      └── ml_metrics.parquet                                         │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
          ┌────────────────┴────────────────┐
          │                                 │
┌─────────▼─────────┐            ┌─────────▼──────────┐
│   BIGQUERY        │            │   API REST         │
│   (SQL Analytics) │            │   (Integración)    │
│                   │            │                    │
│  Dataset:         │            │  Cloud Function:   │
│  covid_analytics  │            │  covid-query-api   │
│                   │            │  (512MB, Node.js)  │
│  ┌─────────────┐  │            │                    │
│  │ 6 Tablas:   │  │            │  ┌──────────────┐  │
│  │             │  │            │  │ 9 Endpoints: │  │
│  │ - dashboard │  │            │  │              │  │
│  │   _kpis     │  │            │  │ GET /        │  │
│  │ - geografia │  │            │  │ GET /kpis    │  │
│  │   _deptos   │  │            │  │ GET /deptos  │  │
│  │ - geografia │  │            │  │ GET /munic   │  │
│  │   _munic    │  │            │  │ GET /region  │  │
│  │ - geografia │  │            │  │ GET /tempor  │  │
│  │   _regiones │  │            │  │ GET /consol  │  │
│  │ - temporal  │  │            │  │ GET /top_mun │  │
│  │   _mensual  │  │            │  │ GET /vista   │  │
│  │ - ranking   │  │            │  └──────────────┘  │
│  │   _deptos   │  │            │                    │
│  └─────────────┘  │            │  URL Pública:      │
│                   │            │  https://us-       │
│  ┌─────────────┐  │            │  central1-datavid- │
│  │ 2 Vistas:   │  │            │  478812.cloud      │
│  │             │  │            │  functions.net/    │
│  │ - top_      │  │            │  covid-query-api   │
│  │   municipios│  │            │                    │
│  │ - vista_    │  │            │  Sin autenticación │
│  │   consolidada│ │            │  (público)         │
│  └─────────────┘  │            └────────────────────┘
└───────────────────┘
         │
         │
┌────────▼────────────────────────────────────────────────────────────┐
│                    AUTOMATIZACIÓN COMPLETA                          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              Cloud Workflows: covid-pipeline-workflow       │    │
│  │                                                             │    │
│  │  FASE 1: Ingesta COVID (invoke ingest-covid-data)           │    │
│  │  FASE 2: Ingesta MySQL (invoke ingest-mysql-data)           │    │
│  │  FASE 3: Crear Cluster Dataproc (efímero)                   │    │
│  │  FASE 4: Ejecutar ETL PySpark                               │    │
│  │  FASE 5: Ejecutar Analytics PySpark                         │    │
│  │  FASE 6: Ejecutar ML PySpark                                │    │
│  │  FASE 7: Cargar resultados a BigQuery                       │    │
│  │  FASE 8: Destruir Cluster Dataproc                          │    │
│  │                                                             │    │
│  │  Duración total: ~20-25 minutos                             │    │
│  │  Estado: SUCCEEDED                                          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │         Cloud Scheduler: run-covid-pipeline                 │    │
│  │                                                             │    │
│  │  Cron: 0 4 * * 1  (Lunes 4:00 AM)                           │    │
│  │  Zona horaria: America/Bogota                               │    │
│  │  Target: Workflow covid-pipeline-workflow                   │    │
│  │  Estado: ENABLED                                            │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

---

##  Requisitos del Proyecto

Este proyecto cumple con **todos los requisitos** especificados en el Trabajo 3 de ST0263:

| # | Requisito | Implementación | Evidencia |
|---|-----------|----------------|-----------|
| **1** | **2+ fuentes de datos heterogéneas** |  API REST Ministerio + Cloud SQL MySQL + CSV históricos | Cloud Functions, Raw Zone |
| **2** | **Captura e ingesta automática a buckets S3/GCS** |  Cloud Functions Gen2 + Cloud Scheduler | Raw Zone (3.74 GB) |
| **3** | **ETL automático con Spark en EMR/Dataproc** |  PySpark con JOIN COVID+MySQL, particionamiento | Trusted Zone, Jobs Dataproc |
| **4** | **Analytics con DataFrames Y SparkSQL** |  25 análisis DataFrames + 4 queries SparkSQL = 29 datasets | Refined Zone Analytics |
| **5** | **ML con SparkML (≥2 técnicas) - OPCIONAL** |  **BONUS**: 5 modelos (3 supervisados + 2 clustering) | Refined Zone ML |
| **6** | **Resultados via Athena (BigQuery) Y API** |  BigQuery (6 tablas + 2 vistas) + API REST (9 endpoints) | BigQuery Dataset, Cloud Function |
| **7** | **Automatización SIN intervención humana** |  Workflow 8 fases + Scheduler semanal + Clusters efímeros | Cloud Workflows, Scheduler |

### Cumplimiento: 100% Requisitos Obligatorios + BONUS ML 

---

## Tecnologías Utilizadas

### Google Cloud Platform (GCP)

| Servicio | Uso | Configuración |
|----------|-----|---------------|
| **Cloud Storage** | Almacenamiento de datos (Raw/Trusted/Refined) | 4 buckets, 3.74 GB |
| **Cloud SQL MySQL** | Base de datos relacional (departamentos, municipios) | db-f1-micro, 10 GB |
| **Cloud Functions Gen2** | Ingesta automática + API REST | Python 3.11, Node.js 20 |
| **Dataproc** | Procesamiento Spark (ETL, Analytics, ML) | n1-standard-4, clusters efímeros |
| **BigQuery** | Data Warehouse (consultas SQL) | covid_analytics dataset |
| **Cloud Workflows** | Orquestación del pipeline | 8 fases, 20-25 min |
| **Cloud Scheduler** | Programación automática | Cron semanal (Lunes 4AM) |
| **IAM** | Gestión de permisos | Service Account con roles específicos |

### Frameworks y Lenguajes

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Apache Spark** | 3.x | Procesamiento distribuido (ETL, Analytics, ML) |
| **PySpark** | 3.x | API Python para Spark |
| **SparkML** | 3.x | Machine Learning distribuido |
| **Python** | 3.11 | Scripting (ETL, Analytics, Ingesta) |
| **Node.js** | 20 | API REST (Cloud Function) |
| **SQL** | - | Queries BigQuery y SparkSQL |

### Librerías Python

```txt
pyspark==3.5.0
google-cloud-storage==2.10.0
google-cloud-bigquery==3.11.0
pandas==2.1.0
numpy==1.25.0
requests==2.31.0
pymysql==1.1.0
```

---

##  Estructura del Repositorio

```
DATAVID/
│
├── README.md                           # Este archivo
├── GUIA_VERIFICACION_COMPLETA.md      # Guía de verificación con comandos
├── requirements.txt                    # Dependencias Python globales
├── populate_mysql.sql                  # Script SQL para poblar MySQL
│
├── ingest_covid_data/                  # Cloud Function: Ingesta API
│   ├── main.py                         # Función principal
│   └── requirements.txt                # Dependencias específicas
│
├── ingest_mysql_data/                  # Cloud Function: Ingesta MySQL
│   ├── main.py                         # Función principal
│   └── requirements.txt                # Dependencias específicas
│
├── covid_query_api/                    # Cloud Function: API REST
│   ├── index.js                        # Endpoints Node.js
│   └── package.json                    # Dependencias Node.js
│
├── dashboard_function/                 # Cloud Function: Dashboard Web
│   ├── main.py                         # Función dashboard (HTML+Chart.js)
│   ├── requirements.txt                # Dependencias Flask
│   ├── test_local.py                   # Servidor de prueba local
│   ├── .gcloudignore                   # Archivos ignorados al desplegar
│   └── README.md                       # Documentación dashboard
│
├── etl_covid_processing/               # Scripts PySpark
│   ├── etl_covid_processing.py         # ETL principal (JOIN, limpieza)
│   └── requirements.txt                # Dependencias PySpark
│
├── analytics_descriptive.py            # Analytics: 29 datasets
├── analytics_ml.py                     # Machine Learning: 5 modelos
│
├── covid_pipeline_workflow.yaml        # Definición del Workflow
│
└── scripts/                            # Scripts auxiliares
    ├── setup_gcp.sh                    # Configuración inicial GCP
    ├── deploy_functions.sh             # Despliegue Cloud Functions
    └── cleanup.sh                      # Limpieza de recursos
```

---

##  Prerequisitos

### 1. Cuenta de Google Cloud Platform

- **Proyecto GCP** con billing habilitado
- **Cuota de vCPUs**: Mínimo 12 vCPUs en us-central1
- **Cuota de storage**: Mínimo 100 GB

### 2. Herramientas Locales

```bash
# Instalar Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Inicializar gcloud
gcloud init

# Instalar Python 3.11+
sudo apt-get install python3.11 python3.11-venv

# Instalar Node.js 20+
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 3. APIs de GCP a Habilitar

```bash
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable dataproc.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable workflows.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable iam.googleapis.com
```

---

##  Instalación y Configuración

### Paso 1: Clonar el Repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd DATAVID
```

### Paso 2: Configurar Variables de Entorno

```bash
# Editar y ejecutar
export PROJECT_ID="tu-proyecto-gcp"
export REGION="us-central1"
export ZONE="us-central1-a"

gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE
```

### Paso 3: Crear Service Account

```bash
# Crear service account
gcloud iam service-accounts create covid-pipeline-sa \
  --display-name="COVID Pipeline Service Account"

# Asignar roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:covid-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/dataproc.worker"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:covid-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:covid-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:covid-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudfunctions.invoker"
```

### Paso 4: Crear Cloud Storage Buckets

```bash
# Bucket para zona RAW
gsutil mb -c STANDARD -l $REGION gs://datavid-raw-zone

# Bucket para zona TRUSTED
gsutil mb -c STANDARD -l $REGION gs://datavid-trusted-zone

# Bucket para zona REFINED
gsutil mb -c STANDARD -l $REGION gs://datavid-refined-zone

# Bucket para scripts PySpark
gsutil mb -c STANDARD -l $REGION gs://datavid-scripts
```

### Paso 5: Crear Cloud SQL MySQL

```bash
# Crear instancia MySQL
gcloud sql instances create covid-mysql-instance \
  --database-version=MYSQL_8_0 \
  --tier=db-f1-micro \
  --region=$REGION \
  --root-password="tu_password_seguro"

# Crear base de datos
gcloud sql databases create covid_data \
  --instance=covid-mysql-instance

# Permitir acceso desde Cloud Functions
gcloud sql instances patch covid-mysql-instance \
  --authorized-networks=0.0.0.0/0
```

### Paso 6: Poblar MySQL con Datos

```bash
# Conectarse a MySQL
gcloud sql connect covid-mysql-instance --user=root

# Ejecutar script SQL
USE covid_data;
SOURCE populate_mysql.sql;
```

---

##  Despliegue del Pipeline

### 1. Subir Scripts PySpark a Cloud Storage

```bash
gsutil cp etl_covid_processing/etl_covid_processing.py gs://datavid-scripts/
gsutil cp analytics_descriptive.py gs://datavid-scripts/
gsutil cp analytics_ml.py gs://datavid-scripts/
```

### 2. Desplegar Cloud Functions

#### a) Función de Ingesta COVID

```bash
cd ingest_covid_data

gcloud functions deploy ingest-covid-data \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=main \
  --trigger-http \
  --allow-unauthenticated \
  --memory=2GB \
  --timeout=3600s \
  --service-account=covid-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com

cd ..
```

#### b) Función de Ingesta MySQL

```bash
cd ingest_mysql_data

gcloud functions deploy ingest-mysql-data \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=main \
  --trigger-http \
  --allow-unauthenticated \
  --memory=512MB \
  --timeout=600s \
  --set-env-vars MYSQL_CONNECTION_NAME=your-project:us-central1:covid-mysql-instance,MYSQL_USER=root,MYSQL_PASSWORD=tu_password,MYSQL_DATABASE=covid_data \
  --service-account=covid-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com

cd ..
```

#### c) API REST de Consulta

```bash
cd covid_query_api

gcloud functions deploy covid-query-api \
  --gen2 \
  --runtime=nodejs20 \
  --region=$REGION \
  --source=. \
  --entry-point=app \
  --trigger-http \
  --allow-unauthenticated \
  --memory=512MB \
  --timeout=60s \
  --set-env-vars PROJECT_ID=$PROJECT_ID,DATASET_ID=covid_analytics \
  --service-account=covid-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com

cd ..
```

### 3. Desplegar Cloud Workflow

```bash
gcloud workflows deploy covid-pipeline-workflow \
  --source=covid_pipeline_workflow.yaml \
  --location=$REGION \
  --service-account=covid-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com
```

### 4. Configurar Cloud Scheduler

```bash
gcloud scheduler jobs create http run-covid-pipeline \
  --location=$REGION \
  --schedule="0 4 * * 1" \
  --time-zone="America/Bogota" \
  --uri="https://workflowexecutions.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/workflows/covid-pipeline-workflow/executions" \
  --http-method=POST \
  --oauth-service-account-email=covid-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com
```

---

##  Ejecución y Monitoreo

### Ejecución Manual del Workflow

```bash
# Ejecutar workflow
gcloud workflows run covid-pipeline-workflow --location=$REGION

# El comando retornará un ID de ejecución, por ejemplo:
# Execution ID: 982a393c-ae3c-4dc5-81c3-6299048050c8
```

### Monitoreo en Tiempo Real

```bash
# Guardar el ID de ejecución
export EXEC_ID="TU_EXECUTION_ID"

# Ver estado actual
gcloud workflows executions describe $EXEC_ID \
  --workflow=covid-pipeline-workflow \
  --location=$REGION \
  --format="value(state)"

# Monitorear cada 30 segundos (tarda ~20-25 minutos)
watch -n 30 "gcloud workflows executions describe $EXEC_ID \
  --workflow=covid-pipeline-workflow \
  --location=$REGION \
  --format='value(state)'"
```

### Ver Jobs de Dataproc

```bash
# Jobs ETL
gcloud dataproc jobs list --region=$REGION \
  --filter="yarnApplications.name:COVID-ETL-Processing" \
  --limit=5

# Jobs Analytics
gcloud dataproc jobs list --region=$REGION \
  --filter="yarnApplications.name:COVID-Analytics-Descriptive" \
  --limit=5

# Jobs ML
gcloud dataproc jobs list --region=$REGION \
  --filter="yarnApplications.name:COVID-Analytics-ML" \
  --limit=5
```

### Ver Logs

```bash
# Logs del workflow
gcloud logging read "resource.type=workflows.googleapis.com/Workflow" \
  --limit=50 \
  --format="table(timestamp,jsonPayload.message)"

# Logs de Cloud Functions
gcloud functions logs read ingest-covid-data --region=$REGION --limit=20
```

---

##  Dashboard de Visualización

### Descripción

Dashboard web profesional desplegado como **Cloud Function HTTP** que consume la API `covid-query-api` y presenta visualizaciones interactivas con **Chart.js** directamente integrado con **BigQuery**.

** URL del Dashboard**: 
```
https://us-central1-datavid-478812.cloudfunctions.net/covid-dashboard
```

**Características**:
-  **6 KPIs principales**: Casos totales, fallecidos, recuperados, letalidad promedio, edad promedio, departamentos analizados
-  **Serie temporal mensual**: Gráfico de líneas con evolución de casos y fallecidos por mes
-  **Top 10 departamentos por letalidad**: Barras horizontales con las tasas de letalidad más altas
-  **Distribución por región**: Gráfico doughnut con casos por región geográfica
-  **Casos por 100k habitantes**: Barras verticales con incidencia normalizada por población
-  **Tabla BigQuery consolidada**: 36 departamentos con métricas epidemiológicas completas (región, población, casos/100k)
-  **Diseño responsivo profesional**: Adaptable a móvil, tablet y desktop con gradientes modernos
-  **Carga dinámica híbrida**: API REST + BigQuery en tiempo real
-  **Pipeline completo verificado**: Datos actualizados tras ejecución del workflow automático

### Despliegue del Dashboard

```bash
# Desde el directorio dashboard_function/
cd dashboard_function

# Desplegar Cloud Function con configuración actualizada
gcloud functions deploy covid-dashboard \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=dashboard \
  --trigger-http \
  --allow-unauthenticated \
  --memory=1GB \
  --timeout=120s \
  --set-env-vars API_URL=https://covid-query-api-7i72qatckq-uc.a.run.app,PROJECT_ID=datavid-478812

# Obtener URL del dashboard
DASHBOARD_URL=$(gcloud functions describe covid-dashboard \
  --region=us-central1 \
  --gen2 \
  --format="value(serviceConfig.uri)")

echo " Dashboard URL: $DASHBOARD_URL"
```

**Salida esperada**:
```
Deploying function (may take a while - up to 2 minutes)...done.
serviceConfig:
  uri: https://us-central1-datavid-478812.cloudfunctions.net/covid-dashboard
  availableMemory: 1Gi
  timeout: 120s
status: ACTIVE
environment: GEN_2
```

**Dashboard desplegado en**: `https://us-central1-datavid-478812.cloudfunctions.net/covid-dashboard`

### Verificación del Dashboard

#### 1. Verificar despliegue exitoso

```bash
gcloud functions describe covid-dashboard \
  --region=us-central1 \
  --gen2 \
  --format="table(name,state,serviceConfig.uri,serviceConfig.availableMemory)"
```

**Esperado**:
```
NAME             STATE   URI                                                           MEMORY
covid-dashboard  ACTIVE  https://us-central1-datavid-478812.cloudfunctions.net/...    1Gi
```

#### 2. Probar respuesta HTTP

```bash
# Verificar que retorna HTML
curl -s "$DASHBOARD_URL" | head -20

# Debe mostrar:
# <!DOCTYPE html>
# <html lang="es">
# <head>
#     <meta charset="UTF-8">
#     <title>COVID-19 Colombia - Dashboard Analítico</title>
#     ...
```

#### 3. Abrir en navegador

```bash
# Linux
xdg-open "$DASHBOARD_URL"

# macOS
open "$DASHBOARD_URL"

# Windows (desde Git Bash)
start "$DASHBOARD_URL"
```

**O copiar la URL y abrirla manualmente en Chrome/Firefox.**

### Elementos del Dashboard

Al abrir el dashboard en el navegador, se visualizan:

1. **Header profesional**:
   - Título: "📊 COVID-19 Colombia"
   - Subtítulo: "Dashboard Analítico Profesional - Big Data Pipeline"
   - Badges de tecnologías: Apache Spark | GCP Dataproc | BigQuery | Cloud Workflows | Cloud Functions
   - Diseño con gradiente morado/azul

2. **Grid de KPIs** (6 tarjetas con animación hover):
   - Total de casos (formato con separadores de miles)
   - Total de fallecidos
   - Total de recuperados
   - Letalidad promedio (%)
   - Edad promedio (años)
   - Departamentos analizados

3. **Gráficos interactivos Chart.js**:
   - **Serie temporal mensual**: Líneas superpuestas (casos en azul, fallecidos en rojo)
     - Eje X: Meses (formato YYYY-MM)
     - Eje Y: Cantidad de casos
     - Tooltips dinámicos al pasar el mouse
     - Leyenda interactiva para ocultar/mostrar series
   
   - **Top 10 departamentos por letalidad**: Barras horizontales rojas ordenadas descendentemente
     - Tooltips con valores exactos en porcentaje
     - Departamentos ordenados por tasa de letalidad
   
   - **Distribución por región**: Gráfico doughnut (dona)
     - 4 regiones: Andina, Caribe, Pacífica, Orinoquía/Amazonía
     - Paleta de colores profesional
     - Tooltips con cantidad de casos y porcentaje
   
   - **Casos por 100k habitantes (Top 10)**: Barras verticales moradas
     - Normalización por población (casos per cápita)
     - Permite comparar incidencia real entre departamentos de diferente tamaño

4. **Tabla BigQuery Consolidada**:
   - **36 departamentos** con datos completos tras actualización de MySQL
   - Columnas: Ranking | Departamento | Región | Población | Casos | Fallecidos | Letalidad | Casos/100k
   - Integración directa con BigQuery (tabla `geografia_departamentos`)
   - Datos enriquecidos con JOIN COVID + MySQL (región, población, casos normalizados)
   - Formato numérico: separadores de miles, decimales controlados
   - Ordenamiento: Letalidad descendente

5. **Footer**:
   - Créditos del proyecto: "🎓 Trabajo 3 - Automatización Big Data"
   - Institución: Universidad EAFIT | ST0263: Tópicos Especiales en Telemática | 2025-2
   - Fuente de datos: Ministerio de Salud Colombia
   - Infraestructura: Apache Spark (GCP Dataproc) + Cloud Workflows
   - Arquitectura: Google Cloud Platform

### Arquitectura del Dashboard

```
┌────────────────────────────────────────────────────┐
│         Usuario (Navegador Web)                    │
└───────────────────┬────────────────────────────────┘
                    │ HTTPS GET
┌───────────────────▼────────────────────────────────┐
│  Cloud Function: covid-dashboard                   │
│  - Runtime: Python 3.11                            │
│  - Memoria: 512MB                                  │
│  - Timeout: 60s                                    │
│  - Endpoint: /                                     │
│  - Retorna: HTML + CSS + JavaScript                │
└───────────────────┬────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │  HTML Template        │
        │  - Chart.js (CDN)     │
        │  - Fetch API          │
        └───────────┬───────────┘
                    │ HTTPS GET
┌───────────────────▼────────────────────────────────┐
│  Cloud Function: covid-query-api                   │
│  - Endpoints: /temporal, /departamentos            │
│  - Retorna: JSON (datos analíticos)                │
└───────────────────┬────────────────────────────────┘
                    │ Consulta
┌───────────────────▼────────────────────────────────┐
│  BigQuery: covid_analytics                         │
│  - Tablas: temporal_mensual, geografia_departam... │
└────────────────────────────────────────────────────┘
```

### Troubleshooting Dashboard

#### Error: "Variable de entorno API_URL no configurada"

**Causa**: No se pasó la variable al desplegar.

**Solución**:
```bash
gcloud functions deploy covid-dashboard \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=dashboard \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars API_URL=https://us-central1-datavid-478812.cloudfunctions.net/covid-query-api
```

#### Error: "Error al cargar datos" en el navegador

**Causa**: La API no responde o URL incorrecta.

**Verificación**:
```bash
API_URL="https://us-central1-datavid-478812.cloudfunctions.net/covid-query-api"
curl -s "$API_URL/temporal?limit=3" | jq '.'
```

Si no responde, verificar que la API esté activa:
```bash
gcloud functions describe covid-query-api --region=us-central1 --gen2
```

#### Gráficos no cargan

**Causa posible**: Problema con CDN de Chart.js.

**Solución**: Revisar consola del navegador (F12 → Console) para errores de red. Verificar conectividad al CDN `cdn.jsdelivr.net`.

---

##  Verificación de Resultados

### 1. Verificar Zona Raw

```bash
gsutil ls gs://datavid-raw-zone/api/casos/ | tail -5
gsutil ls gs://datavid-raw-zone/mysql/departamentos/ | tail -1
gsutil du -sh gs://datavid-raw-zone/
```

**Esperado**: 
- Archivos JSON con timestamp
- Tamaño total: ~3.74 GB

### 2. Verificar Zona Trusted

```bash
gsutil ls gs://datavid-trusted-zone/covid_processed/ | grep "anio_reporte="
gsutil ls gs://datavid-trusted-zone/covid_processed/anio_reporte=2020/
```

**Esperado**:
- 3 particiones por año (2020, 2021, 2022)
- 8 particiones por mes en 2020
- Archivos Parquet (snappy compressed)

### 3. Verificar Zona Refined - Analytics

```bash
gsutil ls gs://datavid-refined-zone/analytics/ | grep "parquet/$" | wc -l
gsutil ls gs://datavid-refined-zone/analytics/ | head -15
```

**Esperado**:
- **29 datasets** analytics
- Archivos en formato Parquet

### 4. Verificar Zona Refined - ML

```bash
gsutil ls gs://datavid-refined-zone/ml/ | grep -E "predictions|clusters|metrics"
```

**Esperado**:
- 3 archivos de predicciones (mortality, severity, hospitalization)
- 2 archivos de clustering (departamentos, poblacional)
- 1 archivo de métricas

### 5. Verificar BigQuery

```bash
bq ls datavid-478812:covid_analytics

bq query --use_legacy_sql=false \
"SELECT total_casos, total_fallecidos, tasa_letalidad_general 
FROM \`${PROJECT_ID}.covid_analytics.dashboard_kpis\`"
```

**Esperado**:
- 6 tablas + 2 vistas
- Dashboard KPIs con 100,000 casos

### 6. Verificar API REST

```bash
export API_URL="https://us-central1-${PROJECT_ID}.cloudfunctions.net/covid-query-api"

# Endpoints disponibles
curl -s $API_URL/ | jq '.endpoints'

# KPIs nacionales
curl -s $API_URL/kpis | jq '.'

# Top 5 departamentos
curl -s "$API_URL/departamentos?limit=5" | jq '.[] | {departamento: .nombre_departamento, casos: .total_casos}'
```

**Esperado**:
- 9 endpoints funcionando
- Respuestas en formato JSON
- Sin requerir autenticación

---

## API REST - Endpoints

### Base URL

```
https://us-central1-datavid-478812.cloudfunctions.net/covid-query-api
```

### Endpoints Disponibles

| Método | Endpoint | Descripción | Parámetros |
|--------|----------|-------------|------------|
| `GET` | `/` | Lista de endpoints disponibles | - |
| `GET` | `/kpis` | KPIs nacionales (casos, fallecidos, CFR) | - |
| `GET` | `/departamentos` | Ranking departamentos por casos | `?limit=N` |
| `GET` | `/municipios` | Top municipios afectados | `?limit=N` |
| `GET` | `/regiones` | Estadísticas por región geográfica | - |
| `GET` | `/temporal` | Evolución mensual de casos | `?limit=N` |
| `GET` | `/consolidado` | Vista consolidada completa | `?limit=N` |
| `GET` | `/top-municipios` | Top municipios (vista BigQuery) | - |
| `GET` | `/vista-consolidada` | Vista consolidada (vista BigQuery) | - |

### Ejemplos de Uso

```bash
# KPIs nacionales
curl "https://us-central1-datavid-478812.cloudfunctions.net/covid-query-api/kpis"

# Response:
{
  "total_casos": 100000,
  "total_fallecidos": 2808,
  "total_recuperados": 96742,
  "tasa_letalidad_general": 2.808,
  "departamentos_afectados": 36,
  "municipios_afectados": 894,
  "edad_promedio": 40.2
}

# Top 10 departamentos
curl "https://us-central1-datavid-478812.cloudfunctions.net/covid-query-api/departamentos?limit=10"

# Evolución temporal (últimos 6 meses)
curl "https://us-central1-datavid-478812.cloudfunctions.net/covid-query-api/temporal?limit=6"
```

### Dashboard Web Interactivo

Además de la API REST, el proyecto incluye un **dashboard web profesional** desplegado como Cloud Function:

**URL del Dashboard**:
```
https://us-central1-datavid-478812.cloudfunctions.net/covid-dashboard
```

**Características**:
-  4 KPIs principales (casos, fallecidos, letalidad, departamentos)
-  Gráfico de serie temporal mensual (Chart.js)
-  Top 10 departamentos por letalidad (barras horizontales)
-  Tabla completa con ranking de departamentos
-  Diseño responsivo (móvil, tablet, desktop)
-  Actualización en tiempo real (consume API REST)

Ver [sección completa del Dashboard](#-dashboard-de-visualización) para instrucciones de despliegue.

---

##  Análisis Implementados

### Análisis con DataFrames (25 datasets)

#### 1. Análisis Temporal (2)
- `temporal_mensual.parquet`: Agregación mensual de casos, fallecidos, recuperados
- `cfr_temporal_departamento.parquet`: Evolución de tasa de letalidad por departamento

#### 2. Análisis Demográfico (4)
- `demografia_edad.parquet`: Distribución por grupos etarios
- `demografia_sexo.parquet`: Distribución por sexo
- `demografia_edad_sexo.parquet`: Distribución cruzada edad-sexo
- `estado_casos.parquet`: Distribución por estado (recuperado, fallecido, activo)

#### 3. Análisis Geográfico (3)
- `geografia_departamentos.parquet`: Estadísticas por departamento + población
- `geografia_municipios_top50.parquet`: Top 50 municipios más afectados
- `geografia_regiones.parquet`: Agregación por región geográfica

#### 4. Análisis de Mortalidad (5)
- `mortalidad_edad_sexo.parquet`: Letalidad por edad y sexo
- `mortalidad_departamento_mes.parquet`: Evolución mensual por departamento
- `tiempo_diagnostico_recuperacion.parquet`: Tiempo promedio hasta recuperación
- `tiempo_diagnostico_muerte.parquet`: Tiempo promedio hasta fallecimiento
- `mortalidad_por_tipo_recuperacion.parquet`: Letalidad según tipo de recuperación

#### 5. Análisis de Recuperación (3)
- `recuperacion_por_tipo.parquet`: Distribución de tipos de recuperación
- `tiempo_recuperacion_edad.parquet`: Tiempo de recuperación por edad
- `estado_salud_actual.parquet`: Estado de salud reportado

#### 6. Hotspots y Críticos (2)
- `municipios_criticos.parquet`: Municipios con alta incidencia
- `departamentos_criticos.parquet`: Departamentos con alto riesgo

#### 7. Dashboard KPIs (3)
- `dashboard_kpis.parquet`: KPIs nacionales consolidados
- `dashboard_evolucion.parquet`: Evolución temporal para dashboard
- `dashboard_top_departamentos.parquet`: Ranking para visualización

#### 8. Indicadores Epidemiológicos (3)
- `indicadores_epidemiologicos.parquet`: R0, tasa de ataque, CFR evolutivo
- `indice_gravedad.parquet`: Índice de gravedad por región
- `infraestructura_salud.parquet`: Capacidad hospitalaria vs casos

### Análisis con SparkSQL (4 queries)

#### 1. Ranking Departamentos
```sql
SELECT 
  nombre_departamento,
  total_casos,
  fallecidos,
  RANK() OVER (ORDER BY total_casos DESC) as ranking
FROM casos_departamentos
```

#### 2. Letalidad Evolutiva
```sql
SELECT 
  mes,
  (SUM(fallecidos) / SUM(casos)) * 100 as tasa_letalidad
FROM casos_temporales
GROUP BY mes
ORDER BY mes
```

#### 3. Análisis Edad-Región
```sql
SELECT 
  region,
  grupo_edad,
  COUNT(*) as casos,
  AVG(edad) as edad_promedio
FROM casos_enriquecidos
GROUP BY region, grupo_edad
```

#### 4. Casos Acumulados
```sql
SELECT 
  fecha,
  SUM(casos) OVER (ORDER BY fecha) as acumulado
FROM casos_diarios
```

---

##  Modelos de Machine Learning

### Modelos Supervisados (3)

#### 1. Random Forest - Predicción de Mortalidad (Binary Classification)

**Objetivo**: Predecir si un paciente fallecerá dado su perfil

**Features**:
- `edad_anios` (numérico)
- `sexo_idx` (0=F, 1=M)
- `departamento_idx` (StringIndexer)
- `estado_idx` (StringIndexer)
- `recuperacion_idx` (StringIndexer)
- `ubicacion_idx` (StringIndexer)

**Target**: `fallecido` (0=No, 1=Sí)

**Métricas**:
- AUC-ROC: 1.0
- Accuracy: 100%
- F1-Score: 1.0

**Feature Importance**:
1. `ubicacion_idx`: 95%
2. `edad_anios`: 3%
3. `sexo_idx`: 1%
4. Otros: <1%

**Output**: `predictions_mortality.parquet`

---

#### 2. Random Forest - Clasificación de Severidad (Multiclass)

**Objetivo**: Clasificar casos en Leve, Moderado o Grave

**Features**: Mismas que modelo 1

**Target**: `severidad` (3 clases)
- 0 = Leve
- 1 = Moderado
- 2 = Grave

**Métricas**:
- Accuracy: 100%
- F1-Score: 1.0
- Precision: 1.0
- Recall: 1.0

**Output**: `predictions_severity.parquet`

---

#### 3. Logistic Regression - Riesgo de Hospitalización

**Objetivo**: Predecir si un paciente requerirá hospitalización

**Features**: Mismas que modelo 1

**Target**: `requiere_hospitalizacion` (0=No, 1=Sí)

**Métricas**:
- AUC-ROC: 0.0 (dataset con clase única en test)
- Accuracy: 100%

**Nota**: Modelo incluye manejo de error para datasets con clase única

**Output**: `predictions_hospitalization.parquet`

---

### Modelos No Supervisados (2)

#### 4. K-Means - Clustering de Departamentos (k=4)

**Objetivo**: Segmentar departamentos por perfil epidemiológico

**Features**:
- `total_casos`
- `edad_promedio`
- `tasa_letalidad`
- `tasa_recuperacion`
- `poblacion`
- `densidad`
- `incidencia_100k`

**Clusters**:
- **Cluster 0**: Departamentos con baja densidad, letalidad moderada
- **Cluster 1**: BOGOTÁ (outlier - alta densidad, muchos casos)
- **Cluster 2**: Departamentos con baja incidencia
- **Cluster 3**: Departamentos medianos, letalidad moderada-alta

**Output**: `clusters_departamentos.parquet`

**Análisis**: `clusters_analisis_departamentos.parquet`

---

#### 5. K-Means - Clustering de Grupos Poblacionales (k=3)

**Objetivo**: Identificar grupos de riesgo por edad/sexo

**Features**:
- `edad_anios`
- `sexo_idx`
- `tasa_mortalidad`
- `tiempo_recuperacion`

**Clusters**:
- **Cluster 0**: Población joven (20-40 años), baja mortalidad
- **Cluster 1**: Población adulta (40-60 años), mortalidad moderada
- **Cluster 2**: Población mayor (60+ años), alta mortalidad

**Output**: `clusters_grupos_poblacionales.parquet`

**Análisis**: `clusters_analisis_poblacional.parquet`

---

### Archivo de Métricas Consolidadas

**Archivo**: `ml_metrics.parquet`

**Contenido**:
```csv
mortality_accuracy,mortality_auc,mortality_f1,
severity_accuracy,severity_precision,severity_recall,severity_f1,
hospitalization_accuracy,hospitalization_auc
```

---

##  Troubleshooting

### Problema 1: Workflow Falla en Creación de Cluster

**Error**: `Insufficient 'CPUS' quota in region us-central1`

**Solución**:
```bash
# Solicitar aumento de cuota en GCP Console:
# IAM & Admin > Quotas > Compute Engine API > CPUs (us-central1)
# Solicitar: 16 CPUs mínimo
```

---

### Problema 2: Cloud Function Timeout

**Error**: `Function execution took 541000 ms, finished with status: timeout`

**Solución**:
```bash
# Aumentar timeout a 3600s (1 hora)
gcloud functions deploy ingest-covid-data \
  --timeout=3600s \
  --memory=2GB
```

---

### Problema 3: BigQuery Access Denied

**Error**: `Access Denied: BigQuery BigQuery: Permission bigquery.tables.create denied`

**Solución**:
```bash
# Asignar rol BigQuery Admin al service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:covid-pipeline-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.admin"
```

---

### Problema 4: Dataproc Job ERROR

**Error**: `Job failed with error: File not found gs://datavid-scripts/etl_covid_processing.py`

**Solución**:
```bash
# Verificar que scripts estén subidos
gsutil ls gs://datavid-scripts/

# Subir scripts
gsutil cp etl_covid_processing/etl_covid_processing.py gs://datavid-scripts/
gsutil cp analytics_descriptive.py gs://datavid-scripts/
gsutil cp analytics_ml.py gs://datavid-scripts/
```

---

### Problema 5: MySQL Connection Refused

**Error**: `ERROR 2003 (HY000): Can't connect to MySQL server`

**Solución**:
```bash
# Verificar que Cloud SQL esté running
gcloud sql instances describe covid-mysql-instance

# Permitir conexiones desde Cloud Functions
gcloud sql instances patch covid-mysql-instance \
  --authorized-networks=0.0.0.0/0

# O usar Cloud SQL Proxy
```

---

##  Costos Estimados

### Costos Mensuales Estimados (Ejecución Semanal)

| Servicio | Configuración | Costo/Mes (USD) |
|----------|---------------|-----------------|
| **Cloud Storage** | 3.74 GB Standard + 2 GB Refined | $0.10 |
| **Cloud SQL MySQL** | db-f1-micro, 10 GB | $7.50 |
| **Cloud Functions** | 4 ejecuciones/mes, 2GB RAM | $2.00 |
| **Dataproc** | 4 clusters efímeros/mes, 20 min c/u | $4.00 |
| **BigQuery** | Queries + storage (1 GB) | $0.50 |
| **Cloud Workflows** | 4 ejecuciones/mes | $0.10 |
| **Cloud Scheduler** | 1 job | $0.10 |
| **Networking** | Egress + API calls | $0.50 |
| **TOTAL** | - | **~$15/mes** |

### Optimizaciones de Costo

1. **Clusters Efímeros**: Solo pagan mientras corren (~20 min)
2. **Preemptible Workers**: Reducir costo Dataproc en 80%
3. **Bucket Nearline**: Para zona Raw (datos históricos)
4. **Cloud SQL Pause**: Detener MySQL cuando no se use
5. **BigQuery Flat-Rate**: Para consultas frecuentes

---

## Autores

**Samuel Andrés Ariza Gómez**  

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](www.linkedin.com/in/samargo) [![GitHub](https://img.shields.io/badge/GitHub-000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/samuelAriza)

---

##  Licencia

Este proyecto es parte de un trabajo académico para la Universidad EAFIT.

---

##  Enlaces Útiles

- [Documentación GCP Dataproc](https://cloud.google.com/dataproc/docs)
- [PySpark Documentation](https://spark.apache.org/docs/latest/api/python/)
- [BigQuery SQL Reference](https://cloud.google.com/bigquery/docs/reference/standard-sql)
- [Cloud Workflows Syntax](https://cloud.google.com/workflows/docs/reference/syntax)
- [SparkML Guide](https://spark.apache.org/docs/latest/ml-guide.html)

---

##  Soporte

Para preguntas o problemas:

1. **Logs**: `gcloud logging read` para cada servicio
2. **GCP Console**: Verificar estado de recursos
3. **Stack Overflow**: Tag `google-cloud-platform` + `pyspark`

---

**Proyecto desarrollado como parte del curso ST0263 - Universidad EAFIT**

**Pipeline Big Data Automatizado - COVID-19 Colombia**

**Noviembre 2024**
