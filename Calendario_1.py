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

# URL de la API de MapStore para consumir los datos 
#url = 'http://localhost:8082/mapstore/rest/'
url = 'http://localhost:8082/mapstore/'

# Hacer la solicitud GET a la API de MapStore (cambiar 'url' por la API real si existe)
# Aquí se debe adaptar según el formato que la API de MapStore retorne los datos
try:
    response = requests.get(url)
    response.raise_for_status()  # Chequear que la respuesta sea correcta
    data_json = response.json()
    # Supongamos que la API devuelve un JSON con campos "date" y "value"
    data = pd.DataFrame(data_json)
except requests.exceptions.RequestException as e:
    print(f"Error al obtener los datos de MapStore: {e}")
    # Usar datos ficticios para el calendario si la solicitud falla
    data = {
        'Day': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] * 3,
        'Hour': ['12 AM', '6 AM', '12 PM', '6 PM'] * 5 + ['12 AM'],  # Ajustado para que tenga 21 elementos
        'Volume': [4, 7, 2, 9, 13, 6, 10, 8, 7, 5, 10, 14, 12, 3, 9, 13, 21, 18, 20, 9, 14]
    }

df = pd.DataFrame(data)

# Crear el gráfico de mapa de calor utilizando Plotly
fig = px.density_heatmap(df, x='Hour', y='Day', z='Patient Volume', 
                         color_continuous_scale='Blues', labels={'Patient Volume': 'Volume'})

# Layout de la aplicación con un campo de entrada y su etiqueta correctamente asociados
app.layout = html.Div([
    html.H1("Calendario de Mapa de Calor"),
    html.Label('Seleccione un rango de fechas:', htmlFor='date-range'),
    dcc.DatePickerRange(
        id='date-range',
        start_date='2024-01-01',
        end_date='2024-01-31',
    ),
    dcc.Graph(id='heatmap', figure=fig)
])

# Ejecutar la aplicación en la IP local y puerto 8050
if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=8050)
