import dash
from dash import dcc, html, callback, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash_extensions import WebSocket
import ast


current_val = [0, 0]
previous_val = [0, 0]


dash.register_page(__name__, path="/")


layout = dbc.Container([
    WebSocket(id="ws", url="ws://127.0.0.1:8765/realtime"),
    #dcc.Interval(id='ws-source-timer', interval=1000),

    html.Br(),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id='rpm-indicator'),
        ]),
        dbc.Col([
            dcc.Graph(id='temp-indicator'),
        ]),
        dbc.Col([
            dcc.Graph(id='current-indicator'),
        ]),
    ]),
    

    dbc.Row([
        dbc.Col([
            dbc.Card(
                dbc.CardBody(
                    [
                        dbc.Tabs([
                            dbc.Tab(label='X axis', tab_id='tab-1-vibX-graph'),
                            dbc.Tab(label='Y axis', tab_id='tab-2-vibY-graph'),
                            dbc.Tab(label='Z axis', tab_id='tab-3-vibZ-graph')
                        ], 
                        id="tabs-vibration-graph",
                        active_tab='tab-1-vibX-graph',
                        ),
                        
                        html.Div(id='tabs-content-vib-graph')
                    ]
                )
            )
        ],
        align = "center",
        )
    ]),

    html.Br(),
    html.Br(),
])
"""prev_url = 'ws://localhost:8765/realtim'

@callback(
        Output('ws', 'url'),
        Input('ws-source-timer', 'n_interval')
)
def update_source(num):
    global prev_url
    try:
        url = ''
        with open('source.txt', 'r') as file:
            url = file.readline()
        if prev_url != url:
            prev_url = url
            return url
    except:
        return prev_url"""
        

@callback(
        Output('tabs-content-vib-graph', 'children'),
        Input('tabs-vibration-graph', 'active_tab'),
        Input('ws', 'message'),
        #prevent_initial_call=True
    )
def get_spectrum_grph(tab, msg):
    var_name = "vibX_fft"
    axis=''
    x_axis = [0,1,2]
    y_axis = [0,0,0]

    match tab:
        case 'tab-1-vibX-graph':
            var_name="vibX_fft"
            axis='X'
        case 'tab-2-vibY-graph':
            var_name="vibY_fft"
            axis='Y'
        case 'tab-3-vibZ-graph':
            var_name="vibZ_fft"
            axis='Z'
    
    df = pd.DataFrame()
    try:
        df = pd.read_json(msg['data'], orient="list")
        data = ast.literal_eval(df.loc[df['variable'] == var_name, '_value'].values[0])
        x_axis=list(i for i in range(len(data)))
        y_axis=data
    except:
        pass

    fig = go.Figure()
    fig.add_trace(go.Bar(
            x=x_axis, 
            y=y_axis,
            marker_color='darkblue'
        )),
    fig.update_layout(
        title_text=f"Vibration spectrum for the {axis} axis",
        title_x=0.5,
        font_size=13,
        title_font=dict(size=21, color='#6e6e6e'),
        template='plotly_white'
        #title_font_color='#6e6e6e',
    )
    fig.update_xaxes(title="Frequency [Hz]", )
    fig.update_yaxes(title="Amplitude [dB]", type='log')

    return html.Div([
        #html.H3('Z axis vibrations'),
        dcc.Graph(figure=fig)
    ])







@callback(
        Output("rpm-indicator", "figure"),
        Output("temp-indicator", "figure"),
        Output("current-indicator", "figure"),
        Input("ws", "message"),
        #prevent_initial_call=True
)
def update_graphs(msg):
    df=pd.DataFrame()

    if msg is not None:
        df = pd.read_json(msg['data'], orient="list")
        global current_val, previous_val
        previous_val=current_val
        current_val=[df.loc[df['variable'] == "rpm",'_value'].values[0], df.loc[df['variable'] == "tempC",'_value'].values[0]]


    fig_rpm = go.Figure()
    fig_rpm.add_trace(go.Indicator(
        mode = "gauge+number+delta",
        value = current_val[0],
        delta = {'reference': previous_val[0]},
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'axis': {'range': [0, 3000]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 2500], 'color': "lightgray"},
                {'range': [2500, 3000], 'color': "red"}
            ]
        },
        #title = {'text': "Speed [rpm]"}
        ))
    fig_rpm.update_layout(title="Speed [rpm]", title_x=0.5, font=dict(size=16))
    

    fig_temp = go.Figure()
    fig_temp.add_trace(go.Indicator(
        mode = "gauge+number+delta",
        value = current_val[1],
        delta = {'reference': previous_val[1]},
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 75], 'color': "lightgray"},
                {'range': [75, 100], 'color': "red"}
            ]
        },
        #title = {'text': "Temperature [C°]"}
        ))
    fig_temp.update_layout(title="Temperature [°C]", title_x=0.5, font=dict(size=16)) 

    fig_current = go.Figure()
    y=[0,0,0]
    try:
        y=ast.literal_eval(df.loc[df['variable'] == "cur", '_value'].values[0])
    except:
        pass

    fig_current.add_trace(go.Bar(
        x=[1, 2, 3], 
        y=y if msg is not None else [0,0,0],
        marker_color='darkblue'
    ))

    fig_current.update_layout(
        title_text="Phase Currents [A]",
        title_x=0.5,
        font=dict(size=16),
        template='plotly_white'
    )

    

    return fig_rpm, fig_temp, fig_current
