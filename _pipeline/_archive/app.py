import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output

from app_pages import homepage, db_view_tshc, db_view_brcas, db_update, db_rollback

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


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = 'PBDA: Variant Vault'


navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="/")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("View Database", href="/database/tshc/view"),
                dbc.DropdownMenuItem("Update Database", href="/database/tshc/update"),
                dbc.DropdownMenuItem("Rollback Database", href="/database/tshc/rollback")
            ],
            nav=True,
            in_navbar=True,
            label="TSHC Database",
            style={'zIndex': 1030, 'fontFamily':'Monaco, monospace' ,'color':'white'},  # High z-index to ensure it's on top
        ),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("View Database", href="/database/brcas/view"),
                dbc.DropdownMenuItem("Update Database", href="/database/brcas/update"),
                dbc.DropdownMenuItem("Rollback Database", href="/database/brcas/rollback")
            ],
            nav=True,
            in_navbar=True,
            label="BRCA Somatic Database",
            style={'zIndex': 1030, 'fontFamily':'Monaco, monospace' ,'color':'white'},  # High z-index to ensure it's on top
        ),        
    ],
    brand_href="/",
    color="#000000",
    dark=True,
    #style={'overflow': 'visible'},  # Ensure navbar overflow is visible
)

app.layout = html.Div([
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
        navbar, # Navbar stays to the right
    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'marginBottom': '10px', 'backgroundColor': '#000000', 'overflow':'visible','fontFamily':'Monaco, monospace' ,'color':'white'}),
    
    #Page Content
    html.Div(id='page-content'),
])

@app.callback(Output('page-content', 'children'),
            [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/database/tshc/view':
        return db_view_tshc.layout
    elif pathname == '/database/brcas/view':
        return db_view_brcas.layout
    elif pathname == '/database/update':
        return db_update.layout    
    elif pathname == '/database/rollback':
        return db_rollback.layout
    else:
        return homepage.layout

# Register callbacks for each page
homepage.register_callbacks(app)
db_view_tshc.register_callbacks(app)
db_view_brcas.register_callbacks(app)
db_update.register_callbacks(app)
db_rollback.register_callbacks(app)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--host', type=str, default='192.168.101.44',
                        help='IP(v4) address of host machine where this Dashboard is hosted.')
    parser.add_argument('-p', '--port', type=str, default='9002',
                        help='Port to use')

    args = parser.parse_args()

    if args.host and args.port:
        app.run_server(host=args.host, port=args.port, debug=True)
    else:
        app.run_server(host='192.168.101.44', port='9002', debug=True)