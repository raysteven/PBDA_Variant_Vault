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


dash.register_page(__name__,path='/playground/',name='PBDA: Variant Vault',title='PBDA: Variant Vault')



pgnum = 999




# Sample data
df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6],
    'C': [7, 8, 9]
})



layout = html.Div([
    dash_table.DataTable(
        id='editable-table',
        columns=[{'name': i, 'id': i} for i in df.columns],
        data=df.to_dict('records'),
        editable=True,
    ),
    dcc.Markdown(id='output')
])

@callback(
    Output('output', 'children'),
    Input('editable-table', 'data'),
    State('editable-table', 'data_previous')
)
def track_changes(data, data_previous):
    if data_previous is None:
        return "No changes yet."

    # Convert lists of dictionaries to DataFrames
    df_current = pd.DataFrame(data)
    df_previous = pd.DataFrame(data_previous)

    # Find changes
    changes = df_current.ne(df_previous) & ~df_current.isna()
    
    changed_cells = changes.stack()[changes.stack()].index.tolist()

    if not changed_cells:
        return "No changes detected."

    changes_list = [
        f"Row {row + 1}, Column '{col}': {df_previous.at[row, col]} -> {df_current.at[row, col]}"
        for row, col in changed_cells
    ]
    
    return "Changes detected:\n" + "\n".join(changes_list)
