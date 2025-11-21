"""
Cloud Function HTTP: Dashboard COVID-19 Colombia (Frontend SPA Profesional)
Sirve un HTML con Chart.js que consume la API existente y BigQuery directamente.
Variables de entorno requeridas: API_URL, PROJECT_ID
"""
import os
import json
import functions_framework
from flask import Response
from google.cloud import bigquery


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>COVID-19 Colombia - Dashboard Analítico Profesional</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
            min-height: 100vh;
        }
        
        .container { max-width: 1600px; margin: 0 auto; }
        
        header {
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.15);
            margin-bottom: 30px;
            text-align: center;
        }
        
        h1 {
            color: #667eea;
            font-size: 3em;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .subtitle {
            color: #666;
            font-size: 1.2em;
            margin-bottom: 10px;
        }
        
        .tech-badge {
            display: inline-block;
            background: #f0f0f0;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            margin: 5px;
            color: #667eea;
            font-weight: 600;
        }
        
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmin(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .kpi-card {
            background: white;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        
        .kpi-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 12px 24px rgba(0,0,0,0.2);
        }
        
        .kpi-value {
            font-size: 2.8em;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }
        
        .kpi-label {
            color: #666;
            font-size: 0.95em;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-weight: 600;
        }
        
        .kpi-sublabel {
            color: #999;
            font-size: 0.85em;
            margin-top: 5px;
        }
        
        .section-title {
            color: white;
            font-size: 1.8em;
            margin: 40px 0 20px 0;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(550px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
        
        .chart-card {
            background: white;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .chart-title {
            font-size: 1.5em;
            color: #333;
            margin-bottom: 20px;
            font-weight: 700;
            border-left: 4px solid #667eea;
            padding-left: 15px;
        }
        
        .table-card {
            background: white;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }
        
        tr:hover {
            background-color: #f8f9ff;
        }
        
        .loading {
            text-align: center;
            padding: 60px;
            font-size: 1.4em;
            color: white;
            font-weight: 600;
        }
        
        .spinner {
            border: 4px solid rgba(255,255,255,0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error {
            background: #fee;
            border-left: 4px solid #c00;
            color: #c00;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            font-weight: 600;
        }
        
        footer {
            text-align: center;
            color: white;
            margin-top: 60px;
            padding: 30px;
            font-size: 0.95em;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }
        
        .badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 700;
        }
        
        .badge-high { background-color: #ff4444; color: white; }
        .badge-medium { background-color: #ffaa00; color: white; }
        .badge-low { background-color: #00cc66; color: white; }
        
        .ml-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .ml-metric-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }
        
        .ml-metric-value {
            font-size: 2em;
            font-weight: 700;
            color: #667eea;
        }
        
        .ml-metric-label {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
            font-weight: 600;
        }
        
        .region-chip {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            margin: 2px;
            background-color: #e3f2fd;
            color: #1976d2;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 COVID-19 Colombia</h1>
            <p class="subtitle">Dashboard Analítico Profesional - Big Data Pipeline</p>
            <div>
                <span class="tech-badge">Apache Spark</span>
                <span class="tech-badge">GCP Dataproc</span>
                <span class="tech-badge">BigQuery</span>
                <span class="tech-badge">Cloud Workflows</span>
                <span class="tech-badge">Cloud Functions</span>
            </div>
        </header>

        <div id="loading" class="loading">
            <div class="spinner"></div>
            Cargando datos analíticos desde BigQuery y API REST...
        </div>

        <div id="error" class="error" style="display:none;"></div>

        <!-- KPIs Principales -->
        <div id="kpis" class="kpi-grid" style="display:none;"></div>

        <!-- Gráficos Principales -->
        <h2 class="section-title">📈 Análisis Epidemiológico</h2>
        <div id="charts" class="charts-grid" style="display:none;">
            <div class="chart-card">
                <h3 class="chart-title">Serie Temporal Mensual</h3>
                <canvas id="timeSeriesChart"></canvas>
            </div>
            <div class="chart-card">
                <h3 class="chart-title">Tasa de Letalidad por Departamento (Top 10)</h3>
                <canvas id="departmentsChart"></canvas>
            </div>
            <div class="chart-card">
                <h3 class="chart-title">Distribución por Región</h3>
                <canvas id="regionsChart"></canvas>
            </div>
            <div class="chart-card">
                <h3 class="chart-title">Casos por 100k Habitantes (Top 10)</h3>
                <canvas id="casesPerCapitaChart"></canvas>
            </div>
        </div>

        <!-- Tabla de Departamentos -->
        <h2 class="section-title">🗂️ Ranking Detallado de Departamentos</h2>
        <div id="table" class="table-card" style="display:none;">
            <h3 class="chart-title">Datos Consolidados desde BigQuery</h3>
            <table id="deptTable">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Departamento</th>
                        <th>Región</th>
                        <th>Casos Totales</th>
                        <th>Fallecidos</th>
                        <th>Letalidad (%)</th>
                        <th>Casos/100k</th>
                        <th>Casos Región</th>
                        <th>Letalidad Región (%)</th>
                    </tr>
                </thead>
                <tbody id="deptTableBody"></tbody>
            </table>
        </div>

        <footer>
            <p><strong>🎓 Trabajo 3 - Automatización Big Data</strong></p>
            <p>Universidad EAFIT | ST0263: Tópicos Especiales en Telemática | 2025-2</p>
            <p>📊 Fuente: Ministerio de Salud Colombia | Procesado con Apache Spark en GCP Dataproc</p>
            <p>☁️ Infraestructura: Google Cloud Platform | Pipeline Orquestado con Cloud Workflows</p>
        </footer>
    </div>

    <script>
        const API_URL = '{{ API_URL }}';
        const BQ_DATA = {{ BQ_DATA }};

        // Helper para limpiar valores NaN/Infinity del JSON
        function sanitizeJSON(text) {
            return text.replace(/:\s*NaN\s*([,\}])/g, ': 0$1')
                       .replace(/:\s*Infinity\s*([,\}])/g, ': 0$1')
                       .replace(/:\s*-Infinity\s*([,\}])/g, ': 0$1');
        }

        async function fetchData() {
            try {
                // Fetch temporal data
                const temporalResp = await fetch(`${API_URL}/temporal?limit=100`);
                if (!temporalResp.ok) throw new Error(`Temporal API: ${temporalResp.status}`);
                const temporalText = await temporalResp.text();
                const temporalData = JSON.parse(sanitizeJSON(temporalText));

                // Fetch regions data
                const regionsResp = await fetch(`${API_URL}/regiones`);
                if (!regionsResp.ok) throw new Error(`Regiones API: ${regionsResp.status}`);
                const regionsText = await regionsResp.text();
                const regionsData = JSON.parse(sanitizeJSON(regionsText));

                // Fetch KPIs
                const kpisResp = await fetch(`${API_URL}/kpis`);
                if (!kpisResp.ok) throw new Error(`KPIs API: ${kpisResp.status}`);
                const kpisText = await kpisResp.text();
                const kpisData = JSON.parse(sanitizeJSON(kpisText));

                return { temporalData, regionsData, kpisData };
            } catch (error) {
                throw new Error(`Error al cargar datos: ${error.message}`);
            }
        }

        function renderKPIs(kpisData) {
            // La API devuelve un array, tomar el primer elemento
            const kpis = Array.isArray(kpisData) ? kpisData[0] : kpisData;
            
            const kpisHTML = `
                <div class="kpi-card">
                    <div class="kpi-value">${(kpis.total_casos || 0).toLocaleString()}</div>
                    <div class="kpi-label">Casos Confirmados</div>
                    <div class="kpi-sublabel">Total Nacional</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">${(kpis.total_fallecidos || 0).toLocaleString()}</div>
                    <div class="kpi-label">Fallecidos</div>
                    <div class="kpi-sublabel">Total Nacional</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">${(kpis.total_recuperados || 0).toLocaleString()}</div>
                    <div class="kpi-label">Recuperados</div>
                    <div class="kpi-sublabel">Total Nacional</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">${parseFloat(kpis.tasa_letalidad_general || 0).toFixed(2)}%</div>
                    <div class="kpi-label">Tasa de Letalidad</div>
                    <div class="kpi-sublabel">CFR Nacional</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">${(kpis.departamentos_afectados || 0)}</div>
                    <div class="kpi-label">Departamentos</div>
                    <div class="kpi-sublabel">Afectados</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">${parseFloat(kpis.edad_promedio || 0).toFixed(1)}</div>
                    <div class="kpi-label">Edad Promedio</div>
                    <div class="kpi-sublabel">Años</div>
                </div>
            `;

            document.getElementById('kpis').innerHTML = kpisHTML;
            document.getElementById('kpis').style.display = 'grid';
        }

        function renderTimeSeriesChart(temporalData) {
            const sorted = temporalData.sort((a, b) => {
                const aYear = parseInt(a.anio_reporte || a.año_reporte || 0);
                const bYear = parseInt(b.anio_reporte || b.año_reporte || 0);
                const aMonth = parseInt(a.mes_reporte || a.mes || 0);
                const bMonth = parseInt(b.mes_reporte || b.mes || 0);
                if (aYear !== bYear) return aYear - bYear;
                return aMonth - bMonth;
            });

            const labels = sorted.map(item => {
                const year = item.anio_reporte || item.año_reporte || '';
                const month = String(item.mes_reporte || item.mes || '').padStart(2, '0');
                return `${year}-${month}`;
            });
            const casos = sorted.map(item => parseInt(item.total_casos || 0));
            const fallecidos = sorted.map(item => parseInt(item.total_fallecidos || 0));

            const ctx = document.getElementById('timeSeriesChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Casos',
                            data: casos,
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            tension: 0.4,
                            fill: true,
                            borderWidth: 3
                        },
                        {
                            label: 'Fallecidos',
                            data: fallecidos,
                            borderColor: '#dc3545',
                            backgroundColor: 'rgba(220, 53, 69, 0.1)',
                            tension: 0.4,
                            fill: true,
                            borderWidth: 3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { position: 'top', labels: { font: { size: 14, weight: 'bold' } } },
                        tooltip: { mode: 'index', intersect: false }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { callback: function(value) { return value.toLocaleString(); } }
                        }
                    }
                }
            });
        }

        function renderDepartmentsChart() {
            if (!BQ_DATA || BQ_DATA.length === 0) return;

            const sorted = [...BQ_DATA].sort((a, b) => parseFloat(b.tasa_letalidad || 0) - parseFloat(a.tasa_letalidad || 0)).slice(0, 10);
            const labels = sorted.map(item => item.nombre_departamento);
            const letalidad = sorted.map(item => parseFloat(item.tasa_letalidad || 0));

            const ctx = document.getElementById('departmentsChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Tasa de Letalidad (%)',
                        data: letalidad,
                        backgroundColor: 'rgba(220, 53, 69, 0.8)',
                        borderColor: '#dc3545',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) { return `${context.parsed.x.toFixed(2)}%`; }
                            }
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            ticks: { callback: function(value) { return value + '%'; } }
                        }
                    }
                }
            });
        }

        function renderRegionsChart(regionsData) {
            if (!regionsData || regionsData.length === 0) return;

            // Filtrar regiones con nombre válido (no null)
            const validRegions = regionsData.filter(item => item.region && item.region !== 'null');
            if (validRegions.length === 0) return;

            const labels = validRegions.map(item => item.region);
            const casos = validRegions.map(item => parseInt(item.total_casos || 0));

            const ctx = document.getElementById('regionsChart').getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Casos por Región',
                        data: casos,
                        backgroundColor: [
                            'rgba(102, 126, 234, 0.8)',
                            'rgba(220, 53, 69, 0.8)',
                            'rgba(255, 193, 7, 0.8)',
                            'rgba(40, 167, 69, 0.8)',
                            'rgba(255, 87, 34, 0.8)',
                            'rgba(156, 39, 176, 0.8)'
                        ],
                        borderWidth: 2,
                        borderColor: 'white'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'right', labels: { font: { size: 12 } } },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.label}: ${context.parsed.toLocaleString()} casos`;
                                }
                            }
                        }
                    }
                }
            });
        }

        function renderCasesPerCapitaChart() {
            if (!BQ_DATA || BQ_DATA.length === 0) return;

            const sorted = [...BQ_DATA].sort((a, b) => parseFloat(b.casos_por_100k || 0) - parseFloat(a.casos_por_100k || 0)).slice(0, 10);
            const labels = sorted.map(item => item.nombre_departamento);
            const casosPer100k = sorted.map(item => parseFloat(item.casos_por_100k || 0));

            const ctx = document.getElementById('casesPerCapitaChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Casos por 100k habitantes',
                        data: casosPer100k,
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderColor: '#667eea',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) { return `${context.parsed.y.toLocaleString()} casos/100k`; }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { callback: function(value) { return value.toLocaleString(); } }
                        }
                    }
                }
            });
        }

        function renderTable() {
            if (!BQ_DATA || BQ_DATA.length === 0) return;

            const tbody = document.getElementById('deptTableBody');
            tbody.innerHTML = BQ_DATA.map((dept, idx) => {
                const letalidad = parseFloat(dept.tasa_letalidad || 0);
                const badgeClass = letalidad > 3 ? 'badge-high' : letalidad > 2 ? 'badge-medium' : 'badge-low';
                return `
                    <tr>
                        <td><strong>${idx + 1}</strong></td>
                        <td><strong>${dept.nombre_departamento || 'N/A'}</strong></td>
                        <td><span class="region-chip">${dept.region || 'N/A'}</span></td>
                        <td>${parseInt(dept.total_casos || 0).toLocaleString()}</td>
                        <td>${parseInt(dept.fallecidos || 0).toLocaleString()}</td>
                        <td><span class="badge ${badgeClass}">${letalidad.toFixed(2)}%</span></td>
                        <td>${parseFloat(dept.casos_por_100k || 0).toLocaleString()}</td>
                        <td>${parseInt(dept.casos_region || 0).toLocaleString()}</td>
                        <td>${parseFloat(dept.letalidad_region || 0).toFixed(2)}%</td>
                    </tr>
                `;
            }).join('');

            document.getElementById('table').style.display = 'block';
        }

        async function init() {
            try {
                document.getElementById('loading').style.display = 'block';
                
                const { temporalData, regionsData, kpisData } = await fetchData();

                document.getElementById('loading').style.display = 'none';

                renderKPIs(kpisData);
                renderTimeSeriesChart(temporalData);
                renderDepartmentsChart();
                renderRegionsChart(regionsData);
                renderCasesPerCapitaChart();
                renderTable();

                document.getElementById('charts').style.display = 'grid';

            } catch (error) {
                document.getElementById('loading').style.display = 'none';
                const errorDiv = document.getElementById('error');
                errorDiv.textContent = error.message;
                errorDiv.style.display = 'block';
                console.error('Error:', error);
            }
        }

        // Initialize dashboard on load
        init();
    </script>
</body>
</html>
"""


def get_bigquery_data():
    """Obtiene datos adicionales de BigQuery"""
    try:
        client = bigquery.Client()
        project_id = os.environ.get('PROJECT_ID', 'datavid-478812')
        
        # Query para obtener datos consolidados
        query = f"""
        SELECT 
            d.nombre_departamento,
            d.region,
            d.total_casos,
            d.fallecidos,
            d.tasa_letalidad,
            d.casos_por_100k,
            r.total_casos as casos_region,
            r.fallecidos as fallecidos_region,
            SAFE_DIVIDE(r.fallecidos * 100.0, r.total_casos) as letalidad_region
        FROM `{project_id}.covid_analytics.geografia_departamentos` d
        LEFT JOIN `{project_id}.covid_analytics.geografia_regiones` r
        ON d.region = r.region
        ORDER BY d.tasa_letalidad DESC
        LIMIT 50
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        data = []
        for row in results:
            # Función helper para convertir valores None/NaN a 0
            def safe_int(val):
                if val is None or (isinstance(val, float) and (val != val)):  # NaN check
                    return 0
                return int(val)
            
            def safe_float(val):
                if val is None or (isinstance(val, float) and (val != val)):  # NaN check
                    return 0.0
                return float(val)
            
            data.append({
                'nombre_departamento': row.nombre_departamento or 'N/A',
                'region': row.region or 'Sin región',
                'total_casos': safe_int(row.total_casos),
                'fallecidos': safe_int(row.fallecidos),
                'tasa_letalidad': safe_float(row.tasa_letalidad),
                'casos_por_100k': safe_float(row.casos_por_100k),
                'casos_region': safe_int(row.casos_region),
                'letalidad_region': safe_float(row.letalidad_region)
            })
        return data
    except Exception as e:
        print(f"Error querying BigQuery: {e}")
        return []


@functions_framework.http
def dashboard(request):
    """
    HTTP Cloud Function que sirve un dashboard HTML con visualizaciones.
    """
    # CORS headers para permitir acceso desde navegador
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    # Obtener configuración
    api_url = os.environ.get('API_URL', '')
    
    if not api_url:
        return Response(
            '<html><body><h1>Error de Configuración</h1>'
            '<p>Variable de entorno API_URL no configurada.</p>'
            '</body></html>',
            status=500,
            mimetype='text/html'
        )

    # Obtener datos de BigQuery
    bq_data = get_bigquery_data()

    # Renderizar template con datos (allow_nan=False evita NaN en JSON)
    html_content = HTML_TEMPLATE.replace('{{ API_URL }}', api_url)
    html_content = html_content.replace('{{ BQ_DATA }}', json.dumps(bq_data, allow_nan=False))

    headers = {
        'Content-Type': 'text/html; charset=utf-8',
        'Access-Control-Allow-Origin': '*'
    }

    return Response(html_content, status=200, headers=headers)
