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


from PBTK import *
import pandas as pd
from sqlalchemy import create_engine
import sqlite3
from sqlalchemy import text


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
                id=f'filter-dropdown-{col}',
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
            id=f'filter-dropdown-{col}',
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
                editable=False,
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
                    # {'if': {'column_id': 'Your-Column-ID'},
                    #  'minWidth': '150px', 'width': '150px', 'maxWidth': '150px'},
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

                                        ]),


                                    ], ), #style={'margin-right':'30px'}

                                    dcc.Store(id=f'store-selected-cell-{pgnum}'),
                                    html.Div(id=f'output-selected-cell-{pgnum}'),

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
            print("remove loading spinner!")
            return None
        print("spinner already gone!")
        raise PreventUpdate

@callback(
    #Output(f'editable-table-{pgnum}', 'data'),
    [Output(f'editable-table-{pgnum}', 'data'),
    Output(f'pagination-info-{pgnum}', 'children')],
    [Input(f'filter-dropdown-{col}', 'value') for col in filterable_columns] +
    [Input(f'editable-table-{pgnum}', "page_current"),
    Input(f'editable-table-{pgnum}', "page_size")])
def update_table(*args):
    global page_current

    filter_values = args[:-3]
    page_current = args[-2]
    page_size = args[-1]
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    #global page_number
    if 'filter-dropdown' in button_id:
        page_current = 0  # Reset to the first page on filter change

    # Filter the DataFrame based on selected values for each dropdown
    filtered_df = df
    for filter_val, col in zip(filter_values, filterable_columns):
        if filter_val:  # If any value is selected
            filtered_df = filtered_df[filtered_df[col].isin(filter_val)]
    displayed_data_df = filtered_df.iloc[page_current*page_size:(page_current+ 1)*page_size]
    displayed_table = displayed_data_df.to_dict('records')


    #_page_current = min(len(filtered_df), ((page_current+1) * page_size))
    
    start_index = (page_current+1) * page_size
    if start_index <= len(filtered_df):
        start_index = (page_current) * page_size
        d_start_index = start_index+1
        end_index = start_index + page_size
    elif start_index > len(filtered_df):
        start_index = (page_current) * page_size
        d_start_index = start_index+1
        end_index =  len(filtered_df)
    else:
        start_index = 0 

    pagination_info = f"Entry: {min(d_start_index, len(filtered_df))}-{min(end_index, len(filtered_df))} of {len(filtered_df)}"
    return displayed_table, pagination_info


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
    Output(f'store-selected-cell-{pgnum}', 'data'),
    [Input(f'editable-table-{pgnum}', 'active_cell'), Input(f'editable-table-{pgnum}', 'data')],
    #[State('store-original-data', 'data')]
)
def update_store(active_cell, current_data, ): #original_data
    ctx = dash.callback_context
    if not ctx.triggered:
        input_id = 'No clicks yet'
    else:
        input_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if active_cell:
        row = active_cell['row']
        column_id = active_cell['column_id']
        #selected_value = current_data[row][column_id]
        original_value = current_data[row][column_id]
        #edited = "Edited" if selected_value != original_value else "No Edit"
        return {
            'selected_index': current_data[row]['Variant_Record'],
            'selected_column': column_id,
            'original_value': original_value,
            'selected_value': current_data[row][column_id]
            #'edit_status': edited
        }
    return {}

@callback(
    Output(f'output-selected-cell-{pgnum}', 'children'),
    [Input(f'store-selected-cell-{pgnum}', 'data')]
)
def display_selected_cell(data):
    if data:
        edited = "Edited" if data['original_value'] != data['selected_value'] else "No Edit"
        #return f"Column B value: {data['selected_value']}, Selected Column: {data['selected_column']}" #, Status: {data['edit_status']}
        return f"Original Value: {data['original_value']}, Selected Value: {data['selected_value']}, Column B Value: {data['selected_index']}, Selected Column: {data['selected_column']}, Edit Status: {edited}"

    return "No cell selected"

