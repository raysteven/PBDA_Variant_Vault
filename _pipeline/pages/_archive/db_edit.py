import dash
from dash import dcc, html, dash_table, callback
from dash.dependencies import Input, Output, State
from dash import callback_context
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import dash_loading_spinners
import dash_mantine_components as dmc


import base64
import os
import shutil  # For file copying
import time
import threading
from datetime import datetime
import copy

from PBTK import *
import pandas as pd
from sqlalchemy import create_engine
import sqlite3
from sqlalchemy import text


import json

from variables import vava_db_dir, database_file, database_file_brcas, variant_table, version_history_table
from modify_db import process_log_entries

user = 'admin'

page_address = '/database/edit/'

dash.register_page(__name__,path=page_address,name='PBDA: Variant Vault',title='PBDA: Variant Vault')



pgnum = 9


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


big_button_style_enabled = {
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

big_button_style_disabled = {
    'background-color': '#A9A9A9', 
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


scrollable_markdown = {
            'height': '200px',        # Set the desired height
            'overflowY': 'scroll',    # Enable vertical scrolling
            'overflowX': 'auto',      # Enable horizontal scrolling if needed
            'border': '1px solid #ccc', # Optional: add a border for better visibility
            'padding': '10px'         # Optional: add some padding for better readability
        }


current_directory = os.getcwd()
# Get the parent directory
parent_directory = os.path.dirname(current_directory)
input_temp_dir = os.path.join(os.getcwd(),'input_temp')

DB_URI = f'sqlite:///{vava_db_dir}/{database_file_brcas}'

def read_data_from_database(DB_URI):
    print('Reading from Database!')
    engine = create_engine(DB_URI)
    query = f"SELECT * FROM {variant_table}"
    df = pd.read_sql(query, engine)
    #df.set_index('Variant_Record', inplace=True)
    print('Successfully reading from Database!')
    #print(df)
    return df

#df = read_data_from_database(DB_URI)

page_number = 1
rows_per_page = 10



def get_filterable_columns():
    filterable_columns = ['Rundate', 'SampleID', 'Variant', 'Clinical_Relevance','Gene','dbSNP_ID','Chromosome','Disease_Name'] #, , , '''Gene'  'Nucleotide [AAchange]', 
    return filterable_columns

def get_dropdowns(filterable_columns, df):

    dropdowns = [dcc.Dropdown(
                    id=f'filter-dropdown-{pgnum}-{col}',
                    options=[{'label': i, 'value': i} for i in sorted(df[col].unique())],
                    multi=True,
                    placeholder=f'{col}',
                    style={'fontSize': '12px'}
                ) for col in filterable_columns]
    return dropdowns

def get_dropdown_row(dropdowns):

    # Create a row for the dropdowns, positioned horizontally
    dropdown_row = dbc.Row(
        [dbc.Col(dropdown, md=True) for dropdown in dropdowns],
        className="mb-3",  # Adds a margin bottom for spacing
    )

    return dropdown_row

def get_unique_sorted_options(filterable_columns, df):
    unique_sorted_options = {
        col: [{'label': i, 'value': i} for i in sorted(df[col].unique())]
        for col in filterable_columns
    }

    return unique_sorted_options

def get_sidebar_filters(filterable_columns, unique_sorted_options):
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

    return sidebar_filters

def get_main_table(df):

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
                        'minWidth': '250px',  'maxWidth': '550px'},
                    ],
                    fixed_columns={'headers': True, 'data': 3},
                    page_current=0,
                    page_size=rows_per_page,
                    page_action='custom',
                    virtualization=True,
                    cell_selectable=True
                )
    
    return main_table

def get_pagination_info(df):
    pagination_info = html.Div(id=f'pagination-info-{pgnum}', children=f"Entry: 1 -{min(rows_per_page, len(df))} of {len(df)}", style={'fontSize':'14px','margin-left':'10px','margin-bottom':'3px'})
    return pagination_info

def get_save_changes_modal():

    save_changes_modal = html.Div([
            html.Button('Save Changes!', id=f'save-changes-button-{pgnum}',n_clicks=0),
                dmc.Modal(
                    title=dmc.Text("Saving Changes to the SQLite Database",size='lg',fw=500),
                    id=f"modal-simple-{pgnum}",
                    size='55%',
                    zIndex=10000,
                    children=[
                        dmc.Space(h=5),
                        dmc.Text("Are you sure to submit the following change(s) to the SQLite Database?"),
                        dmc.Space(h=10),
                        dcc.Markdown(id=f'confirmation-change-log-{pgnum}',style=scrollable_markdown),
                        dmc.Space(h=20),
                        dmc.Group(
                            [
                                dmc.Button("Submit", id=f"modal-submit-button-{pgnum}"),
                                dmc.Button(
                                    "Close",
                                    color="red",
                                    variant="outline",
                                    id=f"modal-close-button-{pgnum}",
                                ),
                            ],
                            justify="flex-end",
                        ),
                    ])
                ])

    return save_changes_modal


## Layout Init


##

filterable_columns = get_filterable_columns()


def get_layout():

    df = read_data_from_database(DB_URI)
    dropdowns = get_dropdowns(filterable_columns, df)
    dropdown_row = get_dropdown_row(dropdowns)
    unique_sorted_options = get_unique_sorted_options(filterable_columns, df)
    sidebar_filters = get_sidebar_filters(filterable_columns,unique_sorted_options)
    main_table = get_main_table(df)
    pagination_info = get_pagination_info(df)
    save_changes_modal = get_save_changes_modal()

    print("Initializing Layout!")


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
                                
                                dcc.Location(id=f'page-url-{pgnum}', refresh=True),  # This component will refresh the page

                                #dcc.ConfirmDialog(
                                #    id='confirm-save-database',
                                #    message='Are you sure you want to commit change(s) to the database?',
                                #),

                                html.Div([
                                html.P("Filter Panel", className="lead", style={'margin-bottom':'0px','margin-left':'10px'}),
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
                                                html.P('Variant Database' , className="lead", style={'margin-bottom':'0px','margin-left':'10px'}),
                                                pagination_info,
                                                main_table,
                                                #html.Div([
                                                #    html.Div(id=f'store-selected-cell-{pgnum}', style={'white-space': 'pre-line'}),
                                                #    dcc.Markdown(id=f'change-log-{pgnum}')
                                                #]),
                                                dcc.Store(id=f'editable-table-data-store-{pgnum}'),
                                                

                                            ]),


                                        ], ), #style={'margin-right':'30px'}

                                        dcc.Store(id=f'editable-table-page_current-{pgnum}'),
                                        dcc.Store(id=f'boolean-switch-page_current-{pgnum}'),


                                ]), md=12)  # Main content area taking up the remaining 12 out of 12 columns
                            ],style={'margin-top':'10px'}),
                            dbc.Row([
                                dbc.Col([
                                    html.P("Cell Selector", className="lead", style={'margin-bottom':'0px'}),
                                    html.Div(id=f'store-selected-cell-{pgnum}', style={'white-space': 'pre-line'})
                                    ],style={'margin-left':'10px'}),
                                dbc.Col([
                                    html.P("Change Log", className="lead", style={'margin-bottom':'0px'}),
                                    #html.Div(id=f'change-log-{pgnum}', style={'white-space': 'pre-line'}),
                                    dcc.Markdown(id=f'change-log-{pgnum}',style=scrollable_markdown),
                                    dcc.Store(id=f'store-change-log-{pgnum}'),
                                    html.Br(),
                                    save_changes_modal,
                                    ],style={'margin-right':'10px'}),
                            ])
                        ], fluid=True)
                    ]
                )
            ]
        )

    return layout


layout = get_layout()

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
    [
    Output(f'editable-table-{pgnum}', 'data'),
    Output(f'pagination-info-{pgnum}', 'children'),
    Output(f'editable-table-{pgnum}', "page_current")],
    [Input(f'filter-dropdown-{pgnum}-{col}', 'value') for col in filterable_columns] +
    [
    Input(f'editable-table-{pgnum}', "page_current"),
    Input(f'editable-table-{pgnum}', "page_size")
    ]
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
    filtered_df = read_data_from_database(DB_URI)
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


@callback(
    Output(f'store-selected-cell-{pgnum}', 'children'),
    [Input(f'editable-table-{pgnum}', 'active_cell'), Input(f'editable-table-{pgnum}', 'data')],
    #[State('store-original-data', 'data')]
)
def update_cell_selector(active_cell, current_data): #original_data
    ctx = dash.callback_context
    if not ctx.triggered:
        input_id = 'No clicks yet'
    else:
        input_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if active_cell:
        try:
            row = active_cell['row']
            column_id = active_cell['column_id']
            #selected_value = current_data[row][column_id]
            original_value = current_data[row][column_id]
            #edited = "Edited" if selected_value != original_value else "No Edit"
            return_text_active_cell = f'''Variant Record : {current_data[row]['Variant_Record']} \nSelected Column : {column_id}\nSelected Value  : {current_data[row][column_id]}\n '''
            return return_text_active_cell
        except:
            return 'No Active Cell Selected'
    else:
        return 'No Active Cell Selected'


@callback(
    Output(f'store-change-log-{pgnum}','data', allow_duplicate=True),
    Output(f'boolean-switch-page_current-{pgnum}','data', allow_duplicate=True),
    [Input(f'filter-dropdown-{pgnum}-{col}', 'value') for col in filterable_columns] +
    [
    Input(f'boolean-switch-page_current-{pgnum}','data'),
    Input(f'editable-table-{pgnum}', 'data'),
    State(f'editable-table-{pgnum}', 'data_previous'),
    State(f'store-change-log-{pgnum}','data')],
    prevent_initial_call=True,
)
def track_changes(*args):
    ctx = dash.callback_context
    #if not ctx.triggered:
    #    return "No changes yet.", None
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if 'filter-dropdown' in button_id:
        return None, False
    #elif 'editable-table' in button_id:
    #    return None
    bool_switch = args[-4]
    data = args[-3]
    data_previous = args[-2]
    change_log = args[-1]
    
    if bool_switch == True:
        #print('Turning Boolean Switch off..')
        return "No changes yet.", False

    if data_previous is None:
        return "No changes yet.", False

    # Convert lists of dictionaries to DataFrames
    df_current = pd.DataFrame(data)
    df_previous = pd.DataFrame(data_previous)

    # Find changes
    changes = df_current.ne(df_previous) & ~df_current.isna()
    
    changed_cells = changes.stack()[changes.stack()].index.tolist()
    
    if not changed_cells:
        return "No changes detected.", False

    change_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    changes_list = {
        change_time:{
        "Variant Record": df_current.at[row, 'Variant_Record'],
        "Changed Column": col,
        "Previous Value": df_previous.at[row, col],
        "New Value": df_current.at[row, col]
        }
        for row, col in changed_cells
    }
    #changes_list = [
    #    f"Variant Record: {df_current.at[row, 'Variant_Record']} \n Changed Column: '{col}' \n Previous Value: {df_previous.at[row, col]} \n New Value: {df_current.at[row, col]}"
    #    for row, col in changed_cells
    #]
    if change_log is None:
        change_log = []
    elif type(change_log) != list:
        change_log = []
        
    change_log.insert(0,changes_list)
    #print("change_log in def track_changes")
    #print(change_log)
    print(change_log)
    return change_log, False


@callback(
    Output(f'change-log-{pgnum}', 'children'),
    Output(f'store-change-log-{pgnum}','data'),
    [Input(f'filter-dropdown-{pgnum}-{col}', 'value') for col in filterable_columns] +
    [
    #Input(f'editable-table-{pgnum}', "derived_viewport_data"),
    Input(f'editable-table-{pgnum}', "page_current"),
    Input(f'store-change-log-{pgnum}','data')
    ], 
)
def display_change_log(*args):
    #print('-----')
    #print('page_current:')
    page_current = args[-2]
    #print(page_current)
    #print('-----')

    change_log = args[-1]
    #print("change_log in def display_change_log")
    #print(change_log)

    ctx = dash.callback_context
    if not ctx.triggered:
        return "No changes yet.", None
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    #print(button_id)
    if 'filter-dropdown' in button_id:
        #print(1)
        return "No changes yet.", None
    elif 'editable-table' in button_id:
        #print(2)
        return "No changes yet.", None
    elif change_log is None:
        #print(3)
        return "No changes yet.", None
    elif change_log == "No changes yet.":
        #print(4)
        return "No changes yet.", None
    else:
        #print(5)
        displayed_change_log = [
        f"""
            **{key}** 
            * Variant Record: {value['Variant Record']} 
            * Changed Column: {value['Changed Column']} 
            * Previous Value: {value['Previous Value']}
            * New Value: {value['New Value']}
        """
        for change_log_item in change_log
        for key, value in change_log_item.items()
        ]
        return '\n'.join(displayed_change_log), dash.no_update

@callback(
    Output(f'editable-table-page_current-{pgnum}','data'),
    [
    Input(f'editable-table-{pgnum}', "page_current"),
    Input(f'editable-table-{pgnum}', "page_size")
    ]
)
def capture_current_page_table(*args):
    page_current = args[-2]
    page_size = args[-1]
    return page_current

@callback(
    Output(f'boolean-switch-page_current-{pgnum}','data'),
    State(f'editable-table-page_current-{pgnum}','data'),
    Input(f'editable-table-{pgnum}', "page_current"),
)
def detect_change_page_table(previous_page, page_current):
    if previous_page != page_current:
        return True
    elif previous_page == page_current:
        return False
    pass

@callback(
    Output(f"modal-simple-{pgnum}", "opened"),
    Output(f'page-url-{pgnum}', 'href'),
    Input(f"save-changes-button-{pgnum}", "n_clicks"),
    Input(f"modal-close-button-{pgnum}", "n_clicks"),
    Input(f"modal-submit-button-{pgnum}", "n_clicks"),
    State(f"modal-simple-{pgnum}", "opened"),
    State(f'store-change-log-{pgnum}','data'),
    prevent_initial_call=True,
)
def modal_demo(nc1, nc2, nc3, opened, log_entries):
    global layout

    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if 'modal-submit-button' in button_id:
        print('Submit Changes Button Pressed!!!')
        print('Commiting Changes to the Database!!!')

        process_log_entries(DB_URI, log_entries)
        print(DB_URI, log_entries)

        print('Reloading the Database!!!')

        layout = get_layout()
        return not opened, page_address



    return not opened, dash.no_update

@callback(
    Output(f'confirmation-change-log-{pgnum}','children'),
    Input(f'change-log-{pgnum}', 'children')
)
def display_change_log_confirmation(displayed_change_log):
    return displayed_change_log

@callback(
    Output(f"save-changes-button-{pgnum}", "style"),
    Output(f"save-changes-button-{pgnum}", "disabled"),
    Input(f'change-log-{pgnum}', 'children'),
)
def toggle_save_change_button(change_log):
    if change_log == "No changes yet.":
        return big_button_style_disabled, True
    elif change_log != "No changes yet.":
        return big_button_style_enabled, False