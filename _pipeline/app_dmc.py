import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import dash_loading_spinners
import dash_mantine_components as dmc
from dash_iconify import DashIconify

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

app = dash.Dash(__name__, suppress_callback_exceptions=True, use_pages=True)
app.title = 'PBDA: Variant Vault'

navbar = dmc.Group(
    children=[
        dmc.Anchor(dmc.Text("Home", fw=500, c="white"), href="/"),
        dmc.Menu(
            [
                dmc.MenuTarget(dmc.Button("View Database", variant="light", color="white")),
                dmc.MenuDropdown(
                    [
                        dmc.MenuLabel("View Database"),
                        dmc.MenuItem("TSHC Database", href="/view/tshc/"),
                        dmc.MenuItem("BRCA_S Database", href="/view/brcas/"),
                    ]
                ),
            ],
            trigger="hover",
        ),
        dmc.Menu(
            [
                dmc.MenuTarget(dmc.Button("Edit Database", variant="light", color="white")),
                dmc.MenuDropdown(
                    [
                        dmc.MenuLabel("Edit Database"),
                        dmc.MenuItem("Upload Rekap", href="/database/upload/"),
                        dmc.MenuItem("Edit Database", href="/database/edit/"),
                        dmc.MenuItem("Rollback Database", href="/database/rollback/"),
                    ]
                ),
            ],
            trigger="hover",
        ),
    ],
    align="center",
    gap="xs",
    style={'zIndex': 0, 'fontFamily':'Monaco, monospace', 'color':'white'},
)

app.layout = dmc.MantineProvider([
    html.Div([
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

        # Page Content
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
