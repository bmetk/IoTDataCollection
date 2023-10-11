import dash
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(__name__, path="/about", order=2)

layout = dbc.Container([
    html.Br(),
    html.Br(),
    html.Br(),

    dcc.Markdown(
        '''
        ### About The Project

        This is a simple [Dash](https://plotly.com/dash/) dashboard for the thesis project: *Design and development of an IoT-based data collection/data analysis system*.
        All of the source material - including code, documentation and so on - can be found [here](https://github.com/bmetk/IoTDataCollection).
        The project runs on one of the BME Industry 4.0 lab servers, the raw data comes from a lathe in the **G** facility.   
        ''' 
    ),
    html.Br(),

    dcc.Markdown(
        '''
        ##### Data Collection

        The data acquisition is done with the help of two ESP32 microcontrollers and four sensors. These collect information about the rotation speed of the main spindle,
        vibration along all three axes, the motor's temperature and current draw. These get sent via MQTT to a [Mosquitto](https://mosquitto.org/) broker to the server for further processing and storage.   
       
        ''' 
    ),
    html.Br(),

    dcc.Markdown(
        '''
        ##### Data Analytics

        After receiving a bundle of data, the rpm, current and temperature values are transfered directly to the [InfluxDB](https://www.influxdata.com/) time series database, whereas the raw vibration data
        is further processed. With the help of an analytics script - acting as a middle man between the broker and the database - further information can be retreived, such as the spectrum, 
        RMS and PSD (Power Spectral Density). For *offline* analysis a large number of records can be downloaded in a .csv format.   
         
        ''' 
    ),
    html.Br(),

    dcc.Markdown(
        '''
        ##### Real-Time Visualization

        This part is acomplished via Dash, which is a dashboard framework written in Python. It gives the user huge flexibility and provides plenty of options. The communication with the backend is done through
        WebSocket connections, the received data is the displayed with the Plotly python module.   
         
        ''' 
    ),


    html.Br(),
    html.Br(),

    html.Hr(),

    dcc.Markdown(
        '''
        Kereszty Márk, 2023
        '''
    ),

    html.Br(),
    html.Br(),

])
