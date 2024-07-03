import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output
import dash_loading_spinners
import dash_mantine_components as dmc

### MANDATORY FOR DMC ###
dash._dash_renderer._set_react_version('18.2.0')


import base64
import os
import shutil  # For file copying
import time
import threading
import argparse


from PBTK import *

current_directory = os.getcwd()
# Get the parent directory
parent_directory = os.path.dirname(current_directory)
input_temp_dir = os.path.join(os.getcwd(),'input_temp')


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True, use_pages=True)
app.title = 'PBDA: Variant Vault'



navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="/")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("TSHC Database", href="/view/tshc/"),
                dbc.DropdownMenuItem("BRCA_S Database", href="/view/brcas/"),
            ],
            nav=True,
            in_navbar=True,
            label="View Database",
            style={'zIndex': 1030, 'fontFamily':'Monaco, monospace' ,'color':'white'},  # High z-index to ensure it's on top
        ),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Upload Rekap", href="/database/upload/"),
                dbc.DropdownMenuItem("Edit Database", href="/database/edit/"),
                dbc.DropdownMenuItem("Rollback Database", href="/database/rollback/")
            ],
            nav=True,
            in_navbar=True,
            label="Edit Database",
            style={'zIndex': 1030, 'fontFamily':'Monaco, monospace' ,'color':'white','margin-right':'30px'},  # High z-index to ensure it's on top
        ),        
    ],
    brand_href="/",
    color="#000000",
    dark=True,
    #style={'overflow': 'visible'},  # Ensure navbar overflow is visible
)

app.layout = dmc.MantineProvider([html.Div([
    dcc.Location(id='url', refresh=False),

    # Header
    html.Div([
        # New div wrapping the image and text, with flex-grow style
        html.Div([
            html.Img(src='/assets/prodia-sulur.png', style={'height': '75px', 'marginRight': '15px'}),
            html.Div([
                html.H4('Variant Vault', style={'display': 'inline-block', 'verticalAlign': 'middle', 'margin':'0', 'font-weight':'bold'}),
                html.P('Prodia Bioinformatics Dashboard Application (PBDA)', style={'margin':'0', 'font-weight':'bold'})
            ], style={'display': 'inline-block', 'verticalAlign': 'middle'}),
        ], style={'display': 'flex', 'alignItems': 'center', 'flexGrow': '1'}), # This div will grow to take up available space
        navbar,
    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'marginBottom': '10px', 'backgroundColor': '#000000', 'overflow':'visible','fontFamily':'Monaco, monospace' ,'color':'white'}),
    
    #Page Content
    dash.page_container,
    dash_loading_spinners.Pacman(
    id='loading-transition', show_initially=True,
    fullscreen=True, 
    ),
    html.Div(id='page-content'),
])
])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--host', type=str,
                        help='IP(v4) address of host machine where this Dashboard is hosted.')
    parser.add_argument('-p', '--port', type=str,
                        help='Port to use')

    args = parser.parse_args()

    if args.host and args.port:
        app.run_server(host=args.host, port=args.port, debug=True)
    else:
        app.run_server(debug=True)