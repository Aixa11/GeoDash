import dash 
from dash import dcc, html
import pandas as pd
import plotly.express as px
import requests
from flask_cors import CORS

# Inicializar la aplicación Dash
app = dash.Dash(__name__)
# Obtener el servidor Flask subyacente
server = app.server
# Aplicar CORS al servidor Flask
CORS(server, resources={r"/*": {"origins": "*"}})

# Función para agregar los headers de CORS (permite acceso desde otras aplicaciones)
@app.server.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

# URL del servicio WFS de GeoServer para consumir los datos de sismos
 #cambiar por su capa propia
wfs_url = 'http://geoserver.demo.opengeo.org/geoserver/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=topp:earthquakes&maxFeatures=50&outputFormat=application/json'

# Hacer la solicitud GET al servicio WFS
try:
    response = requests.get(wfs_url)
    response.raise_for_status()  # Chequear que la respuesta sea correcta
    data_json = response.json()
    # Extraer los datos de la respuesta JSON
      # Cambiar los datos segun la solicitud que necesite 
    features = data_json['features']
    df = pd.json_normalize(features)
    # Seleccionar los campos relevantes y cambiar los nombres
    df = df[['properties.datetime', 'properties.magnitude', 'properties.depth']]
    df.columns = ['datetime', 'magnitude', 'depth']
    df['datetime'] = pd.to_datetime(df['datetime'])  # Convertir la columna de fecha a datetime
except requests.exceptions.RequestException as e:
    print(f"Error al obtener los datos del WFS: {e}")
    # Usar datos ficticios si la solicitud falla
    df = pd.DataFrame({
        'datetime': pd.date_range(start='2024-01-01', periods=50, freq='D'),
        'magnitude': [5.0, 6.0, 4.5, 3.2, 5.5] * 10,
        'depth': [10, 30, 20, 50, 15] * 10
    })

# Crear el gráfico de mapa de calor con Plotly (en base a magnitude y depth)
fig = px.density_heatmap(df, x='datetime', y='magnitude', z='depth',
                         color_continuous_scale='Oranges', labels={'depth': 'Depth (km)'})

# Layout de la aplicación
app.layout = html.Div([
    html.H1("Calendario de Mapa de Calor de Sismos"),
    html.Label('Seleccione un rango de fechas:', htmlFor='date-range'),
    dcc.DatePickerRange(
        id='date-range',
        start_date='2024-01-01',
        end_date='2024-01-31',
        display_format='YYYY-MM-DD'
    ),
    dcc.Graph(id='heatmap', figure=fig)
])

# Ejecutar la aplicación en la IP local o remota y puerto 8050
if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=8050)