import dash
from dash import dcc, html, Input, Output, callback_context
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate
import numpy as np

# Función para preprocesar datos
def preprocesar_datos(df):
    # Copia para evitar modificar el original
    df_procesado = df.copy()
    
    # Asegurar tipos de datos correctos
    if 'ANIO_INSTALACION' in df_procesado.columns:
        df_procesado['ANIO_INSTALACION'] = df_procesado['ANIO_INSTALACION'].astype(int)
    
    # Creamos columna de fecha completa si no existe
    if 'FECHA_INSTALACION' not in df_procesado.columns and 'MES_INSTALACION' in df_procesado.columns:
        try:
            df_procesado['FECHA_INSTALACION'] = pd.to_datetime(
                df_procesado['ANIO_INSTALACION'].astype(str) + '-' + 
                df_procesado['MES_INSTALACION'].astype(str) + '-01',
                errors='coerce'  # Ignora errores en conversión
            )
            
            # Agregamos columna de trimestre solo si la fecha se creó correctamente
            df_procesado['TRIMESTRE'] = df_procesado['FECHA_INSTALACION'].dt.quarter
        except Exception as e:
            print(f"No se pudo crear la columna de fecha: {e}")
    elif 'FECHA_INSTALACION' in df_procesado.columns:
        # Aseguramos que FECHA_INSTALACION sea datetime
        try:
            if not pd.api.types.is_datetime64_any_dtype(df_procesado['FECHA_INSTALACION']):
                df_procesado['FECHA_INSTALACION'] = pd.to_datetime(df_procesado['FECHA_INSTALACION'], errors='coerce')
            
            # Solo creamos TRIMESTRE si FECHA_INSTALACION es realmente datetime
            if pd.api.types.is_datetime64_any_dtype(df_procesado['FECHA_INSTALACION']):
                df_procesado['TRIMESTRE'] = df_procesado['FECHA_INSTALACION'].dt.quarter
        except Exception as e:
            print(f"Error al procesar FECHA_INSTALACION: {e}")
    
    return df_procesado

# Cargar tu archivo CSV o el dataframe base antes de procesarlo
df = pd.read_csv('Database.csv')
  # Ajusta el nombre del archivo
df = preprocesar_datos(df)

# Procesamos el dataframe (asumiendo que df ya está definido)
try:
    df = preprocesar_datos(df)
except NameError:
    # Si df no está definido, mostrar un mensaje de error
    print("Error: El dataframe 'df' no está definido. Por favor, define el dataframe antes de ejecutar este código.")
    # Podemos crear un dataframe de ejemplo para propósitos de demostración
    df = pd.DataFrame({
        'DEPARTAMENTO_INSTALACION': ['Antioquia', 'Bogotá', 'Valle del Cauca'] * 10,
        'MUNICIPIO_INSTALACION': ['Medellín', 'Bogotá', 'Cali'] * 10,
        'ANIO_INSTALACION': [2020, 2021, 2022] * 10,
        'MES_INSTALACION': list(range(1, 13)) + list(range(1, 13)) + list(range(1, 5)),
        'LATITUD_MUNICIPIO': [6.2518, 4.6097, 3.4516] * 10,
        'LONGITUD_MUNICIPIO': [-75.5636, -74.0817, -76.5320] * 10
    })
    df = preprocesar_datos(df)

# Agrupamos datos para mapa
conteo_mpios = df.groupby(['DEPARTAMENTO_INSTALACION', 'MUNICIPIO_INSTALACION']).size().reset_index(name='TOTAL_CONVERSIONES')
df_mapa = df.merge(conteo_mpios, on=['DEPARTAMENTO_INSTALACION', 'MUNICIPIO_INSTALACION'], how='left')
df_mapa = df_mapa.drop_duplicates(subset=['MUNICIPIO_INSTALACION', 'DEPARTAMENTO_INSTALACION'])

# Lista de años y departamentos
anios = sorted(df['ANIO_INSTALACION'].dropna().unique().astype(int).tolist())
departamentos = sorted(df['DEPARTAMENTO_INSTALACION'].dropna().unique().tolist())

# Preparamos datos para el análisis temporal
df_tiempo = df.groupby(['ANIO_INSTALACION', 'MES_INSTALACION']).size().reset_index(name='CONVERSIONES')
try:
    df_tiempo['FECHA'] = pd.to_datetime(df_tiempo['ANIO_INSTALACION'].astype(str) + '-' + 
                                    df_tiempo['MES_INSTALACION'].astype(str) + '-01',
                                    errors='coerce')
    df_tiempo = df_tiempo.sort_values('FECHA')
except Exception as e:
    print(f"Error al crear fechas para análisis temporal: {e}")
    # Alternativa si falla la creación de fechas
    df_tiempo = df_tiempo.sort_values(['ANIO_INSTALACION', 'MES_INSTALACION'])

# Calculamos algunos KPIs
total_conversiones = len(df)
promedio_mensual = df.groupby(['ANIO_INSTALACION', 'MES_INSTALACION']).size().mean().round(0)
if len(df['MUNICIPIO_INSTALACION'].value_counts()) > 0:
    municipio_top = df['MUNICIPIO_INSTALACION'].value_counts().idxmax()
    cantidad_top = df['MUNICIPIO_INSTALACION'].value_counts().max()
else:
    municipio_top = "N/A"
    cantidad_top = 0

# Colores temáticos para la aplicación
colores = {
    'fondo': '#f9f9f9',
    'tarjeta': '#ffffff',
    'primario': '#00205B',  # Azul oscuro
    'secundario': '#82B0D9',  # Azul claro
    'resalte': '#FF5733',  # Naranja (para resaltar)
    'texto': '#333333'
}

# ========== ESTILOS ==========
estilo_tarjeta = {
    'backgroundColor': colores['tarjeta'],
    'borderRadius': '5px',
    'boxShadow': '0 2px 6px rgba(0, 0, 0, 0.15)',
    'padding': '15px',
    'margin': '10px',
}

estilo_indicador = {
    'fontSize': '2.5rem',
    'fontWeight': 'bold',
    'color': colores['primario'],
    'margin': '10px 0 5px 0',
    'textAlign': 'center'
}

estilo_subtitulo = {
    'fontSize': '1rem',
    'color': colores['texto'],
    'textAlign': 'center',
    'margin': '0 0 15px 0'
}

estilo_titulo_principal = {
    'textAlign': 'center',
    'color': colores['primario'],
    'padding': '20px 0',
    'borderBottom': f'2px solid {colores["secundario"]}',
    'margin': '0 0 20px 0'
}

# ========== INICIAR APP ==========
app = dash.Dash(
    __name__, 
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)
app.title = 'Dashboard GNCV Colombia'

# ========== LAYOUT ==========
app.layout = html.Div([
    # Encabezado
    html.Div([
        html.H1('Dashboard de Conversiones a GNCV en Colombia', style=estilo_titulo_principal),
        html.P("Análisis de datos de conversiones a Gas Natural Comprimido Vehicular", 
               style={'textAlign': 'center', 'marginBottom': '30px'}),
    ]),
    
    # Fila de KPIs
    html.Div([
        # KPI 1: Total conversiones
        html.Div([
            html.Div(f"{total_conversiones:,}", style=estilo_indicador),
            html.Div("Total Conversiones", style=estilo_subtitulo)
        ], style=estilo_tarjeta, className='four columns'),
        
        # KPI 2: Promedio mensual
        html.Div([
            html.Div(f"{int(promedio_mensual):,}", style=estilo_indicador),
            html.Div("Promedio Mensual", style=estilo_subtitulo)
        ], style=estilo_tarjeta, className='four columns'),
        
        # KPI 3: Municipio top
        html.Div([
            html.Div(f"{municipio_top}", style=estilo_indicador),
            html.Div(f"Municipio Top ({cantidad_top:,} conversiones)", style=estilo_subtitulo)
        ], style=estilo_tarjeta, className='four columns'),
    ], className='row', style={'margin': '0 15px 30px 15px'}),
    
    # Fila de filtros y gráficos principales
    html.Div([
        # Panel de filtros
        html.Div([
            html.Div([
                html.H3("Filtros", style={'color': colores['primario'], 'marginBottom': '20px'}),
                
                html.Label('Filtrar por Año'),
                dcc.Dropdown(
                    options=[{'label': str(anio), 'value': anio} for anio in anios] + [{'label': 'Todos', 'value': 'todos'}],
                    value='todos',
                    id='filtro-anio',
                    clearable=False
                ),
                
                html.Label('Filtrar por Departamento', style={'marginTop': '15px'}),
                dcc.Dropdown(
                    options=[{'label': dep, 'value': dep} for dep in departamentos] + [{'label': 'Todos', 'value': 'todos'}],
                    value='todos',
                    id='filtro-departamento',
                    clearable=False
                ),
                
                html.Div([
                    html.Button('Restablecer Filtros', id='btn-reset', 
                              style={
                                  'marginTop': '20px',
                                  'backgroundColor': colores['secundario'],
                                  'color': 'white',
                                  'border': 'none',
                                  'padding': '10px 15px',
                                  'borderRadius': '5px',
                                  'cursor': 'pointer',
                                  'width': '100%'
                              })
                ], style={'textAlign': 'center', 'marginTop': '10px'})
            ], style=estilo_tarjeta)
        ], className='three columns'),
        
        # Gráficos principales
        html.Div([
            # Gráfico de tendencia temporal
            html.Div([
                dcc.Graph(
                    id='grafico-tendencia',
                    figure=px.line(
                        df_tiempo, 
                        x='FECHA' if 'FECHA' in df_tiempo.columns else 'ANIO_INSTALACION', 
                        y='CONVERSIONES',
                        title='Tendencia de Conversiones a lo Largo del Tiempo',
                        labels={'CONVERSIONES': 'Cantidad de Conversiones', 'FECHA': 'Fecha', 'ANIO_INSTALACION': 'Año'},
                        template='plotly_white'
                    ).update_layout(
                        title_font_size=16,
                        xaxis=dict(tickangle=-45),
                        margin=dict(l=40, r=40, t=60, b=40)
                    )
                )
            ], style=estilo_tarjeta),
            
            # Fila de gráficos secundarios
            html.Div([
                # Gráfico de barras
                html.Div([
                    dcc.Graph(id='grafico-barras')
                ], className='six columns', style=estilo_tarjeta),
                
                # Gráfico de tipo de vehículo (asumiendo que existe esa columna)
                html.Div([
                    dcc.Graph(id='grafico-tipo-vehiculo')
                ], className='six columns', style=estilo_tarjeta)
            ], className='row'),
            
            # Mapa
            html.Div([
                dcc.Graph(id='mapa-conversiones')
            ], style=estilo_tarjeta)
        ], className='nine columns'),
    ], className='row', style={'margin': '0 15px'}),
    
    # Footer con información adicional
    html.Div([
        html.P('Dashboard desarrollado para análisis de conversiones GNCV en Colombia', 
               style={'textAlign': 'center', 'color': colores['texto'], 'padding': '20px 0 10px 0'})
    ], style={'marginTop': '30px', 'borderTop': f'1px solid {colores["secundario"]}'}),
    
], style={'backgroundColor': colores['fondo'], 'fontFamily': 'Arial, sans-serif'})

# ========== CALLBACKS ==========

@app.callback(
    [Output('grafico-barras', 'figure'),
     Output('mapa-conversiones', 'figure'),
     Output('grafico-tipo-vehiculo', 'figure')],
    [Input('filtro-anio', 'value'),
     Input('filtro-departamento', 'value'),
     Input('btn-reset', 'n_clicks')]
)
def actualizar_graficos(anio, departamento, n_clicks):
    try:
        # Verificar si se ha presionado el botón de reset
        ctx = callback_context
        if ctx.triggered:
            id_trigger = ctx.triggered[0]['prop_id'].split('.')[0]
            if id_trigger == 'btn-reset':
                anio = 'todos'
                departamento = 'todos'
        
        # Filtro base
        df_filtrado = df.copy()
        df_mapa_filtrado = df_mapa.copy()

        if anio and anio != 'todos':
            df_filtrado = df_filtrado[df_filtrado['ANIO_INSTALACION'] == anio]
            df_mapa_filtrado = df_mapa_filtrado[df_mapa_filtrado['ANIO_INSTALACION'] == anio]

        if departamento and departamento != 'todos':
            df_filtrado = df_filtrado[df_filtrado['DEPARTAMENTO_INSTALACION'] == departamento]
            df_mapa_filtrado = df_mapa_filtrado[df_mapa_filtrado['DEPARTAMENTO_INSTALACION'] == departamento]

        # Título dinámico basado en filtros
        titulo_filtro = 'Top 10 municipios por conversiones'
        if anio != 'todos' and departamento != 'todos':
            titulo_filtro += f' en {departamento} durante {anio}'
        elif anio != 'todos':
            titulo_filtro += f' durante {anio}'
        elif departamento != 'todos':
            titulo_filtro += f' en {departamento}'

        # Gráfico de barras
        conteo_municipios = df_filtrado['MUNICIPIO_INSTALACION'].value_counts().nlargest(10)
        fig_barras = px.bar(
            conteo_municipios,
            x=conteo_municipios.index,
            y=conteo_municipios.values,
            labels={'x': 'Municipio', 'y': 'Cantidad de conversiones'},
            title=titulo_filtro,
            color_discrete_sequence=[colores['primario']],
            template='plotly_white'
        )
        fig_barras.update_layout(
            xaxis={'categoryorder': 'total descending', 'tickangle': -45},
            margin=dict(l=40, r=20, t=50, b=80),
            title_font_size=14
        )

        # Mapa
        zoom_level = 4
        if departamento != 'todos':
            zoom_level = 6
        
        # Verificar que existan las columnas necesarias para el mapa
        if all(col in df_mapa_filtrado.columns for col in ['LATITUD_MUNICIPIO', 'LONGITUD_MUNICIPIO']):
            fig_mapa = px.scatter_mapbox(
                df_mapa_filtrado,
                lat='LATITUD_MUNICIPIO',
                lon='LONGITUD_MUNICIPIO',
                color='DEPARTAMENTO_INSTALACION',
                size='TOTAL_CONVERSIONES',
                hover_name='MUNICIPIO_INSTALACION',
                hover_data={
                    'DEPARTAMENTO_INSTALACION': True,
                    'TOTAL_CONVERSIONES': True,
                    'LATITUD_MUNICIPIO': False,
                    'LONGITUD_MUNICIPIO': False
                },
                mapbox_style='carto-positron',
                zoom=zoom_level,
                title='Distribución geográfica de conversiones GNCV',
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            fig_mapa.update_layout(
                margin=dict(l=0, r=0, t=50, b=0),
                title_font_size=14,
                mapbox=dict(center=dict(lat=4.5709, lon=-74.2973))  # Centrado en Colombia
            )
        else:
            # Crear un mapa vacío si faltan columnas
            fig_mapa = go.Figure()
            fig_mapa.add_annotation(
                text="No hay datos geográficos disponibles",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            fig_mapa.update_layout(
                title="Distribución geográfica - Datos no disponibles",
                title_font_size=14
            )

        # Gráfico por tipo de vehículo (asumiendo que existe la columna TIPO_VEHICULO)
        # Si no existe, crear un gráfico alternativo con otra información relevante
        if 'TIPO_VEHICULO' in df_filtrado.columns:
            conteo_tipo = df_filtrado['TIPO_VEHICULO'].value_counts()
            fig_tipo = px.pie(
                values=conteo_tipo.values,
                names=conteo_tipo.index,
                title='Distribución por Tipo de Vehículo',
                hole=0.4,
                template='plotly_white'
            )
        else:
            # Alternativa: Gráfico por año o mes
            conteo_tiempo = df_filtrado.groupby('ANIO_INSTALACION').size().reset_index(name='CONVERSIONES')
            fig_tipo = px.bar(
                conteo_tiempo,
                x='ANIO_INSTALACION',
                y='CONVERSIONES',
                title='Conversiones por Año',
                labels={'ANIO_INSTALACION': 'Año', 'CONVERSIONES': 'Cantidad de conversiones'},
                color_discrete_sequence=[colores['secundario']],
                template='plotly_white'
            )
        
        fig_tipo.update_layout(
            margin=dict(l=20, r=20, t=50, b=20),
            title_font_size=14
        )

        return fig_barras, fig_mapa, fig_tipo
    
    except Exception as e:
        # En caso de error, devolver gráficos vacíos con mensaje
        fig_error = go.Figure()
        fig_error.add_annotation(
            text=f"Error al generar el gráfico: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        
        return fig_error, fig_error, fig_error

# Callback para actualizar el gráfico de tendencia cuando se aplican filtros
@app.callback(
    Output('grafico-tendencia', 'figure'),
    [Input('filtro-anio', 'value'),
     Input('filtro-departamento', 'value'),
     Input('btn-reset', 'n_clicks')]
)
def actualizar_tendencia(anio, departamento, n_clicks):
    try:
        # Verificar si se ha presionado el botón de reset
        ctx = callback_context
        if ctx.triggered:
            id_trigger = ctx.triggered[0]['prop_id'].split('.')[0]
            if id_trigger == 'btn-reset':
                anio = 'todos'
                departamento = 'todos'
        
        # Filtro base
        df_filtrado = df.copy()

        if anio and anio != 'todos':
            df_filtrado = df_filtrado[df_filtrado['ANIO_INSTALACION'] == anio]

        if departamento and departamento != 'todos':
            df_filtrado = df_filtrado[df_filtrado['DEPARTAMENTO_INSTALACION'] == departamento]

        # Preparamos datos para el análisis temporal
        df_tiempo_filtrado = df_filtrado.groupby(['ANIO_INSTALACION', 'MES_INSTALACION']).size().reset_index(name='CONVERSIONES')
        
        # Intentamos crear la columna de fecha, con manejo de errores
        tiene_fecha = False
        try:
            df_tiempo_filtrado['FECHA'] = pd.to_datetime(
                df_tiempo_filtrado['ANIO_INSTALACION'].astype(str) + '-' + 
                df_tiempo_filtrado['MES_INSTALACION'].astype(str) + '-01',
                errors='coerce'
            )
            df_tiempo_filtrado = df_tiempo_filtrado.sort_values('FECHA')
            tiene_fecha = True
        except Exception:
            # Si falla, ordenamos por año y mes
            df_tiempo_filtrado = df_tiempo_filtrado.sort_values(['ANIO_INSTALACION', 'MES_INSTALACION'])
        
        # Título dinámico
        titulo_tendencia = 'Tendencia de Conversiones a lo Largo del Tiempo'
        if anio != 'todos' and departamento != 'todos':
            titulo_tendencia = f'Tendencia de Conversiones en {departamento} durante {anio}'
        elif anio != 'todos':
            titulo_tendencia = f'Tendencia de Conversiones durante {anio}'
        elif departamento != 'todos':
            titulo_tendencia = f'Tendencia de Conversiones en {departamento}'
        
        # Gráfico de tendencia usando FECHA o ANIO_INSTALACION/MES_INSTALACION
        if tiene_fecha:
            fig_tendencia = px.line(
                df_tiempo_filtrado, 
                x='FECHA', 
                y='CONVERSIONES',
                title=titulo_tendencia,
                labels={'CONVERSIONES': 'Cantidad de Conversiones', 'FECHA': 'Fecha'},
                template='plotly_white'
            )
            
            # Añadir promedio móvil si hay suficientes datos
            if len(df_tiempo_filtrado) > 3:
                df_tiempo_filtrado['PROMEDIO_MOVIL'] = df_tiempo_filtrado['CONVERSIONES'].rolling(window=3).mean()
                fig_tendencia.add_scatter(
                    x=df_tiempo_filtrado['FECHA'], 
                    y=df_tiempo_filtrado['PROMEDIO_MOVIL'],
                    mode='lines',
                    name='Promedio móvil (3 meses)',
                    line=dict(color=colores['resalte'], width=2, dash='dash')
                )
        else:
            # Alternativa sin columna de fecha
            df_tiempo_filtrado['PERIODO'] = df_tiempo_filtrado['ANIO_INSTALACION'].astype(str) + '-' + df_tiempo_filtrado['MES_INSTALACION'].astype(str)
            fig_tendencia = px.bar(
                df_tiempo_filtrado, 
                x='PERIODO', 
                y='CONVERSIONES',
                title=titulo_tendencia,
                labels={'CONVERSIONES': 'Cantidad de Conversiones', 'PERIODO': 'Año-Mes'},
                template='plotly_white',
                color_discrete_sequence=[colores['primario']]
            )
        
        fig_tendencia.update_layout(
            title_font_size=16,
            xaxis=dict(tickangle=-45),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return fig_tendencia
    
    except Exception as e:
        # En caso de error, devolver gráfico vacío con mensaje
        fig_error = go.Figure()
        fig_error.add_annotation(
            text=f"Error al generar el gráfico de tendencia: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig_error

# ========== RUN ==========
if __name__ == '__main__':
    app.run(debug=True)
