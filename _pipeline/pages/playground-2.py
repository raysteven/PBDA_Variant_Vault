import dash
from dash import dcc, html, dash_table, callback
from dash.dependencies import Input, Output, State
from dash import callback_context
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import dash_loading_spinners


import base64
import os
import shutil  # For file copying
import time
import threading
import datetime
import copy

from PBTK import *
import pandas as pd
from sqlalchemy import create_engine
import sqlite3
from sqlalchemy import text


from variables import vava_db_dir, database_file_tshc, database_file_brcas, variant_table, version_history_table


user = 'admin'


dash.register_page(__name__,path='/playground/2',name='PBDA: Variant Vault',title='PBDA: Variant Vault')



pgnum = 998





layout = html.Div([
    html.Button(id='button', children='Button'),
    html.Br(),
    dcc.Dropdown(id='dropdown',
                 options=[{'value': True, 'label': 'True'},
                          {'value': False, 'label': 'False'}])
])

@callback(Output('button', 'disabled'),
             [Input('dropdown', 'value')])
def set_button_enabled_state(on_off):
    return on_off

