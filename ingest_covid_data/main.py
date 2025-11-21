import requests
import json
from datetime import datetime
from google.cloud import storage
import logging
import tempfile
import os

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CovidDataIngester:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)

        # URLs oficiales del Ministerio de Salud / Datos Abiertos
        self.urls = {
            'casos': 'https://www.datos.gov.co/resource/gt2j-8ykr.json',
            'fallecidos_csv': 'https://www.datos.gov.co/api/views/jp5m-e7yr/rows.csv?accessType=DOWNLOAD',
            'casos_csv': 'https://www.datos.gov.co/api/views/gt2j-8ykr/rows.csv?accessType=DOWNLOAD'
        }

    def ingest_from_api(self, dataset_name, limit=100000):
        """Ingesta datos desde API JSON (solo para 'casos')"""
        try:
            url = f"{self.urls[dataset_name]}?$limit={limit}"
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; CovidDataIngester/1.0; +https://datos.gov.co)",
                "Accept": "application/json"
            }

            logger.info(f"Descargando {dataset_name} desde API: {url}")
            response = requests.get(url, timeout=300, headers=headers)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                logger.warning(f"Formato inesperado en {dataset_name}, se forzará a lista")
                data = [data]

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            blob_path = f"api/{dataset_name}/{timestamp}.json"
            blob = self.bucket.blob(blob_path)
            blob.upload_from_string(
                json.dumps(data, ensure_ascii=False, indent=2),
                content_type='application/json'
            )

            logger.info(f"✓ {dataset_name}: {len(data)} registros guardados en {blob_path}")
            return len(data)

        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP al descargar {dataset_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error ingiriendo {dataset_name}: {str(e)}")
            raise

    def ingest_from_csv(self, dataset_name):
        """Ingesta datos desde archivo CSV (casos y fallecidos) usando streaming con archivo temporal"""
        temp_file = None
        try:
            url = self.urls[f'{dataset_name}_csv']
            logger.info(f"Descargando {dataset_name} CSV desde {url}")

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            blob_path = f"csv/{dataset_name}/{timestamp}.csv"
            blob = self.bucket.blob(blob_path)

            # Usar archivo temporal para evitar carga en memoria
            response = requests.get(url, timeout=300, stream=True)
            response.raise_for_status()

            # Crear archivo temporal
            temp_file = tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.csv')
            
            line_count = 0
            chunk_size = 1024 * 1024  # 1MB chunks
            
            # Escribir en archivo temporal mientras contamos líneas
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    line_count += chunk.count(b'\n')
                    temp_file.write(chunk)
            
            temp_file.close()
            
            # Subir desde el archivo temporal
            blob.upload_from_filename(temp_file.name, content_type='text/csv')
            
            # Eliminar archivo temporal
            os.unlink(temp_file.name)
            temp_file = None
            
            # -1 para excluir el header
            record_count = max(0, line_count - 1)
            
            logger.info(f"✓ {dataset_name} CSV: ~{record_count} registros guardados en {blob_path}")
            return record_count

        except Exception as e:
            logger.error(f"Error ingiriendo CSV {dataset_name}: {str(e)}")
            # Limpiar archivo temporal si existe
            if temp_file and os.path.exists(temp_file.name):
                try:
                    temp_file.close()
                    os.unlink(temp_file.name)
                except:
                    pass
            raise

    def run_full_ingestion(self):
        """Ejecuta la ingesta completa de todos los datasets"""
        logger.info("=== Iniciando ingesta completa ===")
        results = {}

        # Ingesta desde API (solo casos)
        results['api_casos'] = self.ingest_from_api('casos')

        # Ingesta desde CSV (casos + fallecidos)
        for dataset in ['casos', 'fallecidos']:
            results[f'csv_{dataset}'] = self.ingest_from_csv(dataset)

        logger.info("=== Ingesta completada ===")
        logger.info(f"Resultados: {results}")
        return results


def main(request=None):
    """Cloud Function entry point"""
    logger.info(">>> Iniciando función Cloud Function ingest-covid-data <<<")
    try:
        ingester = CovidDataIngester('datavid-raw-zone')
        results = ingester.run_full_ingestion()
        logger.info(">>> Ingesta finalizada con éxito <<<")
        return {'status': 'success', 'results': results}
    except Exception as e:
        logger.error(f"Fallo general en la función: {str(e)}")
        return {'status': 'error', 'message': str(e)}
