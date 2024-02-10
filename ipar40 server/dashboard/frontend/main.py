import dash
from dash import html, Input, Output
import dash_bootstrap_components as dbc
from dash_extensions import WebSocket
import base64


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], use_pages=True)
logo = "images/logo.png"
logo_base64 = base64.b64encode(open(logo, 'rb').read()).decode('ascii')

#------------------------------------------------------------------
# components

navbar = dbc.Navbar(
    dbc.Container([
        html.A(
            dbc.Row([
                dbc.Col(html.Img(src='data:image/png;base64,{}'.format(logo_base64), height="40px", style={'border-radius':'20%'})),
                dbc.Col(dbc.NavbarBrand("OpenDAQ", class_name="ms-2", id="home-page")),
                dbc.Col(
                    dbc.Nav([
                        dbc.NavItem(dbc.NavLink("Home", active=True, href="/", class_name='nav-link'), class_name='nav-item'),
                        dbc.NavItem(dbc.NavLink("Analytics", active=True, href="/analytics", class_name='nav-link'), class_name='nav-item'),
                        dbc.NavItem(dbc.NavLink("About", active=True, href="/about", class_name='nav-link'), class_name='nav-item')
                    ]),
                )
            ],
            align = "center",
            class_name ="g-0"
            ),
            
        href = "/", 
        style = {"textDecoration": "none"}
        ),
        dbc.Switch(id='toggle-generated-data', label='Generate Data', value=False, style={'color':'white'}),

        
    ], fluid=True),
    class_name="navbar navbar-expand-lg bg-primary", 
    color = "primary",
    dark = True,
    
)


#------------------------------------------------------------------
# layout

app.layout = dbc.Container(html.Div([
    navbar, 
    WebSocket(id='ws-toggler-1', url="ws://172.22.101.1:8765/realtime"),
    #WebSocket(id='ws-toggler-1', url="ws://127.0.0.1:8765/realtime"),
    WebSocket(id='ws-toggler-2', url="ws://152.66.34.82:61114/realtime"),
    dash.page_container,
]), fluid=True)

@app.callback(
    Output('ws-toggler-1', 'send'),
    Output('ws-toggler-2', 'send'),
    Input('toggle-generated-data', 'value'),
    #prevent_initial_call=True
)
def toggle_data_source(value):
    if value:
        return 'generated', 'generated'
    else:
        return 'realtime', 'realtime'


if __name__ == "__main__":
    
    app.run(debug=True, host='0.0.0.0', port=8050) #linux: 0.0.0.0
