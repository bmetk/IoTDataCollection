import dash
from dash import dcc, html, callback, Output, Input
import dash_bootstrap_components as dbc
from dash_extensions import WebSocket
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import requests
import ast



dash.register_page(__name__, path="/analytics", order=1)

layout = dbc.Container([
    WebSocket(id='ws-1', url="ws://172.22.101.1:8765/realtime"),
    #WebSocket(id='ws-1', url="ws://127.0.0.1:8765/realtime"),
    WebSocket(id='ws-2', url="ws://152.66.34.82:61114/realtime"),

    html.Br(),
    html.Br(),

    dbc.Row([
         dcc.Graph(id='rpm-current-temp')
    ]),
    
    html.Br(),
    html.Br(),
    html.Hr(),
    html.Br(),
    html.Br(),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id='vibration-rms',  config={'displayModeBar': False})
        ], ),

        dbc.Col([
            dcc.Graph(id='vibration-psd',  config={'displayModeBar': False}),
        ], width=6),
    ]),


    html.Br(),
    html.Br(),
    html.Hr(),
    html.Br(),
    html.Br(),

    dbc.Row([
        dbc.Col([
            dcc.Slider(0, 30, 1,
                    value=1,
                    marks={
                        0: {'label': '0d'},
                        10: {'label': '10d'},
                        20: {'label': '20d'},
                        30: {'label': '30d'},
                    },
                    id='download-slider',
                    tooltip={"placement": "top", "always_visible": True}
            )
        ]),
        
        
        dbc.Col([
            dcc.Markdown('''
                Select the number of days (backwards) from which you want data. The records are combined into a single .csv file that can be 
                processed or analysed separately from this web application. A basic Jupyter notebook for data pre-processing can be found [here](https://github.com/bmetk/IoTDataCollection/blob/main/preprocessing/preprocessing.ipynb).
            '''),
        ]),
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Button("Download Data", id='btn-download-data', class_name='btn btn-primary'),
            dcc.Download(id='download-data'),
        ]),
        dbc.Col([
            dbc.Alert(
                "Download failed",
                id='download-fail',
                color='danger',
                is_open=False,
                duration=5000,
                dismissable=True,
            ),
        ])
    ]),

    html.Br(),
    html.Br(),
])

# callback for websocket message handling
@callback(
    Output('rpm-current-temp', 'figure'),
    Input('ws-1', 'message'),
    Input('ws-2', 'message'),
    #prevent_initial_call=True
)
def update_combined_data(msg1, msg2):
    df = pd.DataFrame()
    fig = go.Figure()
    fig.update_layout(title="Combined data overview", title_x=0.5,
                    yaxis=dict(title='Speed [rpm]'),
                    yaxis2=dict(title='Phase Cur. Sum [A], Temp. [°C]', overlaying='y', side='right'),
                    xaxis=dict(title='Time [s]', domain=[0, 0.95]),
                    font_size=13,
                    title_font=dict(size=20),
                    template='plotly_white'
                    )
    
    if msg1 is not None:
        df = pd.read_json(msg1['data'])
    elif msg2 is not None:
        df = pd.read_json(msg2['data'])
    else:
        return fig
        
    
    rpm_data = df[df['variable'] == 'rpm']
    cur_data = df[df['variable'] == 'cur']
    tempC_data = df[df['variable'] == 'tempC']

    # Access the values and timestamps for each variable
    rpm_values = rpm_data['_value'].tolist()
    rpm_timestamps = rpm_data['_time'].tolist()

    cur_values = cur_data['_value'].tolist()
    cur_sum = []
    for point in cur_values:
        ls = ast.literal_eval(point)
        cur_sum.append((ls[0]+ls[1]+ls[2]))
    cur_timestamps = cur_data['_time'].tolist()

    tempC_values = tempC_data['_value'].tolist()
    tempC_timestamps = tempC_data['_time'].tolist()

    
    


    fig.add_trace(go.Scatter(x=rpm_timestamps, y=rpm_values,
                            mode = 'lines+markers',
                            name = 'Rotation Speed [rpm]',
                            yaxis='y1'))

    fig.add_trace(go.Scatter(x=cur_timestamps, y=cur_sum,
                            mode = 'lines+markers',
                            name = 'Phase Cur. Sum [A]',
                            yaxis='y2'))
    
    fig.add_trace(go.Scatter(x=tempC_timestamps, y=tempC_values,
                            mode = 'lines+markers',
                            name = 'Temperature [°C]',
                            yaxis='y2'))

    
    #fig.update_xaxes(title="Time [s]")
    #fig.update_yaxes(title="Speed, Temperature, Current average")
    
    return fig



# callback for websocket message handling
@callback(
    Output('vibration-rms', 'figure'),
    Input('ws-1', 'message'),
    Input('ws-2', 'message'),
    #prevent_initial_call=True
)
def update_rms_data(msg1, msg2):
    fig=go.Figure()
    fig.update_layout(title='RMS value for each axes', title_x=0.5,
                    xaxis=dict(title='Time [s]'),
                    yaxis=dict(title='RMS [a]'),
                    font_size=13,
                    title_font=dict(size=20),
                    template='plotly_white'
                    )

    df = pd.DataFrame()
    if msg1 is not None:
        df = pd.read_json(msg1['data'])
    elif msg2 is not None:
        df = pd.read_json(msg2['data'])
    else:
        return fig
    #fig = go.Figure()

    x_rms_data = df[df['variable'] == 'vibX_rms']
    y_rms_data = df[df['variable'] == 'vibY_rms']
    z_rms_data = df[df['variable'] == 'vibZ_rms']

    x_rms_val = x_rms_data['_value'].astype(float).tolist()
    x_rms_time = x_rms_data['_time'].tolist()

    y_rms_val = y_rms_data['_value'].astype(float).tolist()
    y_rms_time = y_rms_data['_time'].tolist()
    
    z_rms_val = z_rms_data['_value'].astype(float).tolist()
    z_rms_time = z_rms_data['_time'].tolist()
    
    fig.add_trace(go.Scatter(x=x_rms_time, y=x_rms_val, customdata=list(zip(x_rms_data['table'].tolist(), x_rms_data['variable'].tolist(), x_rms_time)),
                            mode = 'lines+markers',
                            name = 'X Axis RMS'))
    
    fig.add_trace(go.Scatter(x=y_rms_time, y=y_rms_val, customdata=list(zip(y_rms_data['table'].tolist(), y_rms_data['variable'].tolist(), y_rms_time)),
                            mode = 'lines+markers',
                            name = 'Y Axis RMS'))
    
    fig.add_trace(go.Scatter(x=z_rms_time, y=z_rms_val, customdata=list(zip(z_rms_data['table'].tolist(), z_rms_data['variable'].tolist(), z_rms_time)),
                            mode = 'lines+markers',
                            name = 'Z Axis RMS'))
    
    return fig





# callback for interactive graph
@callback(
    Output('vibration-psd', 'figure'),
    Input('vibration-rms', 'clickData'),
    Input('ws-1', 'message'),
    Input('ws-2', 'message'),
    #prevent_initial_call=True
)
def update_psd_data(clickData, msg1, msg2):
    fig = go.Figure()
    df = pd.DataFrame()
    
    if clickData is None or (msg1 is None and msg2 is None):
        fig.update_layout(title='Select RMS value for PSD',
                    title_x=0.5,
                    font_size=13,
                    title_font=dict(size=20),
                    template='plotly_white')
        return fig
    elif msg1 is not None:
        df = pd.read_json(msg1['data'])
    elif msg2 is not None:
        df = pd.read_json(msg2['data'])
    

    selection = clickData['points'][0]

    axis = ''
    axis_short = ''

    match selection['customdata'][1]:
        case 'vibX_rms':
            axis = 'vibX_psd'
            axis_short = 'X'

        case 'vibY_rms':
            axis = 'vibY_psd'
            axis_short = 'Y'

        case 'vibZ_rms':
            axis = 'vibZ_psd'
            axis_short = 'Z'

    delta = timedelta(seconds=0.5)
    rms_time = datetime.strptime(selection['customdata'][2], "%Y-%m-%dT%H:%M:%S.%f%z")

    
    dff = df[(df['_time'] >= rms_time - delta) &
        (df['_time'] <= rms_time + delta) &
        (df['variable'] == axis)]
    
    if len(dff.index) == 0:
        fig.update_layout(title='Select RMS value for PSD',
                    title_x=0.5,
                    font_size=13,
                    title_font=dict(size=20),
                    template='plotly_white')
        return fig

    try:
        psd_raw = ast.literal_eval(dff['_value'].values[0])
    except:
        return fig
    
    string_time = selection['customdata'][2]
    timestamp = string_time[string_time.find('T')+1:string_time.find('T')+9]

    fig.add_trace(go.Scatter(x=psd_raw[0], y=psd_raw[1], mode='lines'))
    fig.update_xaxes(title="Frequency [Hz]")
    fig.update_yaxes(type="log", title="Acceleration [a^2/Hz]")

    fig.update_layout(
                    title='PSD on the <b>{}</b> axis<br>@{}'.format(axis_short, timestamp),
                    title_x=0.5, 
                    font_size=13,
                    title_font=dict(size=20),
                    template='plotly_white'
                    )


    return fig
    
    


previous_n_clicks = 0

#callback for download button
@callback(
    Output('download-data', 'data'),
    Output('download-fail', 'is_open'),
    Input('btn-download-data', 'n_clicks'),
    Input('download-slider', 'value'),
    prevent_initial_call=True
)
def download_data(n_clicks, data_range_days):
    global previous_n_clicks
    if n_clicks is None or n_clicks == previous_n_clicks:
        return None
    previous_n_clicks = n_clicks
    try:
        response = requests.get(f"http://download:5000/export-csv?data_range_days={data_range_days}")
        if response.status_code == 200:
            csv_data = response.content.decode('utf-8')
        
            # Define the download data as a dictionary
            download_data = dict(content=csv_data, filename="influxdb_data.csv")
            return download_data, False
        else:
            return None, True
    except:
        return None, True

