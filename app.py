import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd

df = px.data.gapminder().query("year == 2007")

app = dash.Dash(__name__)
server = app.server  


app.layout = html.Div([
    html.H1("Población por Continente (2007)", style={'textAlign': 'center'}),
    
    
    dcc.Dropdown(
        id='dropdown-continent',
        options=[{'label': cont, 'value': cont} for cont in df['continent'].unique()],
        value='Asia',
        clearable=False
    ),
    
    
    dcc.Graph(id='grafico-poblacion')
])


@app.callback(
    dash.dependencies.Output('grafico-poblacion', 'figure'),
    [dash.dependencies.Input('dropdown-continent', 'value')]
)
def actualizar_grafico(continente):
    filtro = df[df['continent'] == continente]
    fig = px.bar(filtro, x='country', y='pop', title=f'Población en {continente}')
    return fig


if __name__ == '__main__':
    app.run(debug=True)
