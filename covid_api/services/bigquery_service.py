from google.cloud import bigquery

class BigQueryService:
    def __init__(self):
        self.client = bigquery.Client()

    def run_query(self, query: str):
        """Ejecuta una consulta SQL en BigQuery y devuelve lista de diccionarios."""
        results = self.client.query(query).to_dataframe()
        return results.to_dict('records')