import dash
import dash_leaflet as dl
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import requests
import pandas as pd

# URLs del servicio WMS de GeoServer para cada satélite
wms_url_terra = "http://localhost:8080/geoserver/workspace_name/wms?"  # MODIS TERRA
wms_url_aqua = "http://localhost:8080/geoserver/workspace_name/wms?"  # MODIS AQUA

# Definición de capas en el WMS según el satélite
layer_terra = "workspace_name:MODIS_TERRA"
layer_aqua = "workspace_name:MODIS_AQUA"

# URLs del servicio WFS de GeoServer para cada satélite
wfs_url_terra = "http://localhost:8080/geoserver/workspace_name/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=GIRSAR%3AMODIS_TERRA_parted&maxFeatures=50&outputFormat=application%2Fjson"
wfs_url_aqua = "http://localhost:8080/geoserver/workspace_name/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=GIRSAR%3AMODIS_AQUA_parted&maxFeatures=50&outputFormat=application%2Fjson"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Visualización de Datos MODIS Terra-Aqua"

app.layout = dbc.Container(fluid=True, children=[
    dbc.Row([
        dbc.Col(html.H1("Visualización de Datos MODIS Terra-Aqua", className="text-center my-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.Label("Seleccionar Rango de Fechas:"),
            dcc.DatePickerRange(
                id='fecha-range',
                start_date_placeholder_text="Inicio",
                end_date_placeholder_text="Fin",
                start_date=None,
                end_date=None,
                className="mb-3"
            ),
            html.Label("Seleccionar Satélite:"),
            dcc.Dropdown(
                id='satelite-dropdown',
                options=[
                    {'label': 'MODIS TERRA', 'value': 'MODIS_TERRA'},
                    {'label': 'MODIS AQUA', 'value': 'MODIS_AQUA'}
                ],
                multi=False,  # Solo permite seleccionar uno a la vez
                value='MODIS_TERRA',  # Valor por defecto
                className="mb-3"
            ),
            html.Div(id='fecha-lista')
        ], md=4),
        dbc.Col([
            dl.Map(center=[0, 0], zoom=2, children=[dl.TileLayer()], id='mapa-leaflet', style={'width': '100%', 'height': '500px'})
        ], md=8)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='grafico-barras'), md=4),
        dbc.Col(dcc.Graph(id='grafico-caja'), md=4),
        dbc.Col(dcc.Graph(id='grafico-autogenerado'), md=4),
    ], className="my-4"),
    dbc.Row([
        dbc.Col(html.Div(id='estadisticas-container'), md=12),
    ], className="my-4")
])

# Función para obtener y procesar datos de WFS según el satélite seleccionado
def obtener_y_procesar_datos_wfs(satelite_seleccionado, start_date, end_date):
    # Asignar la URL WFS según el satélite seleccionado
    if satelite_seleccionado == 'MODIS_TERRA':
        url = wfs_url_terra
    elif satelite_seleccionado == 'MODIS_AQUA':
        url = wfs_url_aqua

    response = requests.get(url)
    if response.status_code == 200:
        datos = response.json()
        df = pd.json_normalize(datos['features'])

        print(f"Datos obtenidos para {satelite_seleccionado}:")
        print(df.head())  # Imprimir los primeros registros para depuración

        # Extraer coordenadas
        df['longitude'] = df['geometry.coordinates'].apply(lambda x: x[0])  # Extrae la longitud
        df['latitude'] = df['geometry.coordinates'].apply(lambda x: x[1])  # Extrae la latitud

        print(f"Filas restantes después de filtrar: {len(df)}")
        return df if 'properties.FP_POWER' in df.columns else pd.DataFrame()
    else:
        print(f"Error en la solicitud WFS: {response.status_code}")
        return pd.DataFrame()

# Función para calcular estadísticas
def calcular_estadisticas(df):
    estadisticas = {
        "Media de FP_POWER": df["properties.FP_POWER"].mean(),
        "Max de FP_CONFIDENCE": df["properties.FP_CONFIDENCE"].max(),
    }
    return estadisticas

# Función para actualizar el mapa según el satélite seleccionado
@app.callback(
    Output('mapa-leaflet', 'children'),
    [Input('satelite-dropdown', 'value'), Input('fecha-range', 'start_date'), Input('fecha-range', 'end_date')]
)
def actualizar_mapa(satelite_seleccionado, start_date, end_date):
    mapa_children = [dl.TileLayer()]  # Agregar TileLayer base
    if satelite_seleccionado == 'MODIS_TERRA':
        # Cargar la capa WMS de MODIS TERRA
        mapa_children.append(dl.WMSTileLayer(
            url=wms_url_terra, layers=layer_terra,
            format="image/png", transparent=True, version="1.1.0",
            attribution="MODIS Terra Data"
        ))
    elif satelite_seleccionado == 'MODIS_AQUA':
        # Cargar la capa WMS de MODIS AQUA
        mapa_children.append(dl.WMSTileLayer(
            url=wms_url_aqua, layers=layer_aqua,
            format="image/png", transparent=True, version="1.1.0",
            attribution="MODIS Aqua Data"
        ))
    return mapa_children

# Función para actualizar gráficos y estadísticas
@app.callback(
    [Output('grafico-barras', 'figure'),
     Output('grafico-caja', 'figure'),
     Output('grafico-autogenerado', 'figure'),
     Output('estadisticas-container', 'children')],
    [Input('satelite-dropdown', 'value'), Input('fecha-range', 'start_date'), Input('fecha-range', 'end_date')]
)
def actualizar_graficos(satelite_seleccionado, start_date, end_date):
    if not satelite_seleccionado or not start_date or not end_date:
        return [px.bar(), px.box(), px.scatter(), "Seleccione un rango de fechas y satélite válido."]
    
    df = obtener_y_procesar_datos_wfs(satelite_seleccionado, start_date, end_date)
    if df.empty:
        return [px.bar(), px.box(), px.scatter(), "No se encontraron datos para el satélite y fechas seleccionadas."]
    
    estadisticas = calcular_estadisticas(df)

    # Asegúrate de que las columnas que usas para los gráficos existan
    fig_barras = px.bar(df, x='latitude', y='properties.FP_POWER', title='FP_POWER a lo largo del tiempo')
    fig_caja = px.box(df, y='properties.FP_POWER', title='Distribución de FP_POWER')
    fig_autogenerado = px.scatter(df, x='longitude', y='latitude', color='properties.FP_POWER', title='FP_POWER por Ubicación')

    estadisticas_html = html.Div([
        html.H4("Estadísticas Combinadas"),
        html.Ul([html.Li(f"{key}: {value}") for key, value in estadisticas.items()])
    ])

    return fig_barras, fig_caja, fig_autogenerado, estadisticas_html


if __name__ == '__main__':
    app.run_server(host="127.0.0.1", port=8050, debug=True)