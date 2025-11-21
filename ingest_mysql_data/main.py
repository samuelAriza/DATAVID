import pymysql
import json
from datetime import datetime
from google.cloud import storage
import pandas as pd
import logging
from dotenv import load_dotenv
import os
from google.cloud.sql.connector import Connector

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MySQLIngester:
    def __init__(self, bucket_name, instance_connection_name, db_config):
        self.bucket_name = bucket_name
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)
        self.instance_connection_name = instance_connection_name
        self.db_config = db_config
        self.connector = Connector()
    
    def get_connection(self):
        """Obtiene una conexión usando Cloud SQL Connector"""
        conn = self.connector.connect(
            self.instance_connection_name,
            "pymysql",
            user=self.db_config['user'],
            password=self.db_config['password'],
            db=self.db_config['database']
        )
        return conn
    
    def extract_table(self, table_name):
        """Extrae datos de una tabla MySQL"""
        try:
            connection = self.get_connection()
            
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql(query, connection)
            
            connection.close()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Guardar como JSON
            blob_path = f"mysql/{table_name}/{timestamp}.json"
            blob = self.bucket.blob(blob_path)
            blob.upload_from_string(
                df.to_json(orient='records', force_ascii=False, indent=2),
                content_type='application/json'
            )
            
            logger.info(f"✓ {table_name}: {len(df)} registros extraídos a {blob_path}")
            return len(df)
            
        except Exception as e:
            logger.error(f"Error extrayendo {table_name}: {str(e)}")
            raise
    
    def run_full_extraction(self):
        """Extrae todas las tablas"""
        tables = ['departamentos', 'municipios', 'hospitales']
        results = {}
        
        logger.info("=== Iniciando extracción MySQL ===")
        for table in tables:
            results[table] = self.extract_table(table)
        
        logger.info("=== Extracción MySQL completada ===")
        return results

def main(request=None):
    """Cloud Function entry point"""
    # Configuración para Cloud SQL
    instance_connection_name = "datavid-478812:us-central1:covid-mysql-instance"
    db_config = {
        'user': os.environ.get('DB_USER', 'covid_user'),
        'password': os.environ.get('DB_PASSWORD', ''),
        'database': os.environ.get('DB_NAME', 'covid_db')
    }
    
    logger.info(f"Conectando a Cloud SQL: {instance_connection_name}")
    ingester = MySQLIngester('datavid-raw-zone', instance_connection_name, db_config)
    results = ingester.run_full_extraction()
    return {'status': 'success', 'results': results}