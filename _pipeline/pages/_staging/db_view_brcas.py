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


import json

from variables import vava_db_dir, database_file, database_file_brcas, variant_table, version_history_table


user = 'admin'


dash.register_page(__name__,path='/view/brcas/',name='PBDA: Variant Vault',title='PBDA: Variant Vault')



pgnum = 4


button_style = {
    'background-color': '#FFFCFC', 
    'color': 'black',  # Text color
    'border':'solid',
    'border-width': '1px',
    'border-color': '#A9A9A9',
    'padding': '3px 10px',  # Padding to adjust button size
    'text-align': 'center',
    'text-decoration': 'none',
    'display': 'inline-block',
    'font-size': '14px',  # Decreased font size
    'margin-right':'10px',
    'margin-top':'7px'
}


big_button_style = {
    'background-color': '#2d82b5', 
    'color': 'white',  # Text color
    'border':'solid',
    'border-width': '1px',
    'border-color': '#A9A9A9',
    'padding': '6px 20px',  # Padding to adjust button size
    'text-align': 'center',
    'text-decoration': 'none',
    'display': 'inline-block',
    'font-size': '14px',  # Decreased font size
    #'margin-left':'10px',
    #'margin-top':'7px',
}



current_directory = os.getcwd()
# Get the parent directory
parent_directory = os.path.dirname(current_directory)
input_temp_dir = os.path.join(os.getcwd(),'input_temp')


def read_data_from_database():
    engine = create_engine(f'sqlite:///{vava_db_dir}/{database_file_brcas}')
    query = f"SELECT * FROM {variant_table}"
    df = pd.read_sql(query, engine)
    return df

df = read_data_from_database()
initial_df = copy.deepcopy(df)


page_number = 1
rows_per_page = 10


# Create the filter dropdowns for the sidebar
upload_rekap_excel = html.Div([
    dcc.Upload(
        id=f'upload-rekap-excel{pgnum}',
        children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
        style={
            'width': '100%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
            'textAlign': 'center', 'margin': '10px',
        },
        # Allow multiple files to be uploaded
        multiple=False
    ),
    
])


filterable_columns = ['Rundate', 'SampleID', 'Variant', 'Clinical_Relevance','Gene','dbSNP_ID','Chromosome','Disease_Name'] #, , , '''Gene'  'Nucleotide [AAchange]', 

dropdowns = [dcc.Dropdown(
                id=f'filter-dropdown-{pgnum}-{col}',
                options=[{'label': i, 'value': i} for i in sorted(df[col].unique())],
                multi=True,
                placeholder=f'{col}',
                style={'fontSize': '12px'}
            ) for col in filterable_columns]

dropdown_container = html.Div([
                    ])
dropdown_container.children.extend(dropdowns) 

# Create a row for the dropdowns, positioned horizontally
dropdown_row = dbc.Row(
    [dbc.Col(dropdown, md=True) for dropdown in dropdowns],
    className="mb-3",  # Adds a margin bottom for spacing
)


unique_sorted_options = {
    col: [{'label': i, 'value': i} for i in sorted(df[col].unique())]
    for col in filterable_columns
}


# Create the filter dropdowns for the sidebar
sidebar_filters = html.Div([
    html.Div([
        html.P(f"{col}", style={'font-style':'italic'}), #className="lead"
        dcc.Dropdown(
            id=f'filter-dropdown-{pgnum}-{col}',
            options=unique_sorted_options[col],
            #options = [{'label': i, 'value': i} for i in sorted(df[col].unique())],
            multi=True,
            placeholder=f'Select {col}...'
        )
    ], style={'margin-bottom': '10px'}) for col in filterable_columns
], style={'padding': '10px', 'margin-left':'5px'}) #'padding': '10px', 



main_table = dash_table.DataTable(
                id=f'editable-table-{pgnum}',
                columns=[{"name": i, "id": i} for i in df.columns if i != "Variant_Record"],
                data=df.iloc[:rows_per_page].to_dict('records'),
                editable=True,
                style_table={
                    'minWidth': '100%',
                    'overflowX': 'auto'  # Ensures horizontal scrolling if necessary
                },
                style_data={
                    'fontSize': '14px',
                    'whiteSpace': 'normal',  # Allows text wrapping within cells
                    'height': 'auto',  # Adjusts row height to content
                    'minWidth': '100px',  # Minimum width for all data cells
                },
                style_header={
                    'fontSize': '14px',
                    'fontWeight': 'bold',
                    'whiteSpace': 'normal',  # Allows text wrapping within header cells
                    'height': 'auto',  # Adjusts header height to content
                    'minWidth': '100px',  # Minimum width for header cells
                },
                style_cell_conditional=[
                    # Apply custom minWidth for specific columns here if needed
                    # Example:
                     {'if': {'column_id': 'Variant'},
                      'minWidth': '150px', 'width': '150px', 'maxWidth': '250px'},
                ],
                fixed_columns={'headers': True, 'data': 3},
                page_current=0,
                page_size=rows_per_page,
                page_action='custom',
                virtualization=True,
                cell_selectable=True
            )


pagination_info = html.Div(id=f'pagination-info-{pgnum}', children=f"Entry: 1 -{min(rows_per_page, len(df))} of {len(df)}", style={'fontSize':'14px','margin-left':'10px','margin-bottom':'3px'})


layout = html.Div(
     children=[
             html.Div(
                 id=f"div-loading-{pgnum}",
                 children=[
                     dash_loading_spinners.Pacman(
                         fullscreen=True, 
                         id="loading-whole-app"
                     )
                 ]
             ),
             html.Div(
                 className="div-app",
                 id=f"div-app-{pgnum}",
                 children = [ #  app layout here
                    dbc.Container([
                        dbc.Row([
                            
                            dcc.ConfirmDialog(
                                id='confirm-save-database',
                                message='Are you sure you want to commit change(s) to the database?',
                            ),
                            html.Div([
                            html.P("Filter Panel", className="lead", style={'margin-bottom':'0px'}),
                            html.Details([
                            html.Summary(''), #, 
                            dropdown_row,
                            ],style={'margin-left':'10px'}),
                            ]),
                            #html.Hr(style={'border': '1px solid black','margin-top':'10px'}),
                            dbc.Col(
                                html.Div([
                                    html.Div([
                                        html.Div([
                                            html.P('Variant Database' , className="lead", style={'margin-bottom':'0px'}),
                                            pagination_info,
                                            main_table,
                                            dcc.Store(id=f'editable-table-data-store-{pgnum}'),

                                        ]),


                                    ], ), #style={'margin-right':'30px'}

                                    dcc.Store(id=f'previous-cell-coordinate-{pgnum}'),
                                    html.Div(id=f'output-selected-cell-{pgnum}'),
                                    html.Div(id=f'display-previous-cell-coordinate-{pgnum}'),

                            ]), md=12)  # Main content area taking up the remaining 8 out of 12 columns
                        ],style={'margin-top':'10px'})
                    ], fluid=True)
                ]
             )
         ]
     )



@callback(
        Output(f"div-loading-{pgnum}", "children"),
        [
            Input(f"div-app-{pgnum}", "loading_state")
        ],
        [
            State(f"div-loading-{pgnum}", "children"),
        ]
    )
def hide_loading_after_startup(
        loading_state, 
        children
        ):
        if children:
            return None
        raise PreventUpdate

@callback(
    [Output(f'filter-dropdown-{pgnum}-{col}', 'options') for col in filterable_columns] +
    [Output(f'editable-table-{pgnum}', 'data'),
     Output(f'pagination-info-{pgnum}', 'children'),
     Output(f'editable-table-{pgnum}', "page_current")],
    [Input(f'filter-dropdown-{pgnum}-{col}', 'value') for col in filterable_columns] +
    [Input(f'editable-table-{pgnum}', "page_current"),
     Input(f'editable-table-{pgnum}', "page_size")]
)
def update_table_and_filters(*args):
    global page_current

    filter_values = args[:len(filterable_columns)]
    page_current = args[-2]
    page_size = args[-1]

    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if 'filter-dropdown' in button_id:
        page_current = 0  # Reset to the first page on filter change

    # Filter the DataFrame based on selected values for each dropdown
    filtered_df = df
    for filter_val, col in zip(filter_values, filterable_columns):
        if filter_val:  # If any value is selected
            filtered_df = filtered_df[filtered_df[col].isin(filter_val)]
    
    # Update options for each dropdown based on the filtered DataFrame
    updated_options = [
        [{'label': i, 'value': i} for i in sorted(filtered_df[col].unique())]
        for col in filterable_columns
    ]

    # Update the table data
    displayed_data_df = filtered_df.iloc[page_current * page_size:(page_current + 1) * page_size]
    displayed_table = displayed_data_df.to_dict('records')

    start_index = (page_current * page_size) + 1
    end_index = min((page_current + 1) * page_size, len(filtered_df))
    pagination_info = f"Entry: {start_index}-{end_index} of {len(filtered_df)}"

    return updated_options + [displayed_table, pagination_info, page_current]


@callback(
    Output(f'upload-rekap-excel{pgnum}', 'children'),
    [Input(f'upload-rekap-excel{pgnum}', 'filename')],
    [State(f'upload-rekap-excel{pgnum}', 'contents')],
    allow_duplicate=True
)
def update_rekap_excel(excel_input_filename, excel_input_contents):
    if excel_input_filename is not None:
        print(excel_input_filename)
        extension = '.xlsx'
        if extension not in excel_input_filename:
            return html.Div(['Please input XLSX file only!'], style={'backgroundColor': 'red', 'color': 'white'})
        excel_input_file_path = os.path.join('input_temp', excel_input_filename)
        with open(excel_input_file_path, 'wb') as f:
            f.write(base64.b64decode(excel_input_contents.split(",")[1]))
        print('Upload success: {}'.format(excel_input_file_path))
        # Return updated Upload components with file names and blue background
        return html.Div([excel_input_filename], style={'backgroundColor': '#2d82b5', 'color': 'white'})
    return html.Div(['Drag and Drop or ', html.A('Select Files')])



@callback(
    Output(f'editable-table-data-store-{pgnum}', 'data'),
    Input(f'editable-table-{pgnum}', 'data_timestamp'),
    State(f'editable-table-{pgnum}', 'data'),
    State(f'editable-table-data-store-{pgnum}', 'data')
)
def store_table_edits(timestamp, table_data, stored_data):
    if timestamp is None:
        raise PreventUpdate
    if stored_data is None:
        stored_data = []
    stored_data = table_data
    return stored_data






'''

@callback(
    Output(f'output-selected-cell-{pgnum}', 'children'),
    [Input(f'editable-table-{pgnum}', 'active_cell')],
    [State(f'editable-table-{pgnum}', 'data'), State(f'editable-table-{pgnum}', 'data_previous')]
)
def track_changes(active_cell, current_data, previous_data):
    print('=====CALLBACK CHECK=====')
    #print('timestamp', timestamp)
    print('cell_coordinate', active_cell)

    if active_cell:
        row = active_cell['row']
        column_id = active_cell['column_id']
        current_uid = current_data[row]['Variant_Record']
        original_cell_value = initial_df[initial_df['Variant_Record'] == current_uid][f'{column_id}'].values[0]
        current_cell_value = current_data[row][column_id]
        if original_cell_value == current_cell_value:
            edit_status = 'No Edit'
        else:
            edit_status = 'Edited'
        selected_data = {
            'selected_index': current_uid,
            'selected_column': column_id,   
            'selected_value': current_cell_value,
            'original_cell_value':original_cell_value,
            'edit_status':edit_status,
            'full_data':current_data[row]
        }
        print(selected_data['selected_column'])
        return json.dumps(selected_data, indent=2)

    return 'No Cell Selected'

'''