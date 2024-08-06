import dash
from dash import dcc, html, dash_table, callback
from dash.dependencies import Input, Output, State
from dash import callback_context
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
import dash_ag_grid as dag


import numpy as np
from datetime import datetime
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


from variables import vava_db_dir, database_file_tshc, database_file_brcas , variant_table, version_history_table
from excel_to_sqldb import convert_excel_to_df_vava

user = 'admin'


pgnum = 2


page_address = '/modify/upload/'

dash.register_page(__name__,path=page_address,name='PBDA: Variant Vault',title='PBDA: Variant Vault')


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
input_temp_dir = os.path.join(os.getcwd(),'input_temp_db')

print('input_temp_dir:', input_temp_dir)


#db_path = f'{vava_db_dir}/{database_file}'

# Connect to the SQLite database
#conn = sqlite3.connect(db_path)

# Create a cursor object
#cur = conn.cursor()

# Execute a query
#cur.execute("SELECT * FROM db_var")


# def read_data_from_database():
#     engine = create_engine(f'sqlite:///{vava_db_dir}/{database_file_tshc}')
#     query = f"SELECT * FROM {variant_table}"
#     df = pd.read_sql(query, engine)
#     return df

def get_main_table(df):
    columns = [
        "Rundate", "SampleID", "Variant", "Clinical_Relevance", "Disease_Name",
        "Chromosome", "dbSNP_ID", "Gene", "Start", "End", "Ref", "Alt",
        "Variant_Type", "Variant_Classification", "VAF", "Genotype",
        "alt_count", "ref_count", "DP", "P_LP_Result", "Mode_of_Inheritance", "Variant_Record"
    ]

    columnDefs = [{"field": i,"width": 50, "maxWidth": 500} for i in columns]
    # [
    #     {
    #     "field":"Rundate",
    #     "filter": "agDateColumnFilter",
    #     "checkboxSelection": True,
    #     "headerCheckboxSelection": True,
    #     "sort": "desc",  # Default sort direction to descending (newest to oldest)
    #     "width": 50, "maxWidth": 200
    #     },
    #     {"field":"SampleID","width": 50, "maxWidth": 200, "sort": "desc"},
    #     {"field":"Variant","width": 150, "maxWidth": 200},
    #     ] + 
    
    defaultColDef = {
        "flex": 1,
        #"minWidth": 10,
        #"filter": "agTextColumnFilter",
        "filter": True, 
        "sortable": True, "floatingFilter": True,
    }    
    
    main_table = dag.AgGrid(
        id=f"main-table-{pgnum}",
        rowData=df.to_dict("records"),
        columnDefs=columnDefs,
        defaultColDef=defaultColDef,
        columnSize="autoSize",
        filterModel={},
        dashGridOptions={
                "rowSelection": "multiple",
                "pagination": True,
                "paginationAutoPageSize": True,
                "animateRows": True,
                "paginationPageSize":10},
        style={"height": "600px", "width": "100%"} #-> indirectly affects the number of rows
    )

    return main_table






# Define the column names as per your SQL schema
columns = [
    "Rundate", "SampleID", "Variant", "Clinical_Relevance", "Disease_Name",
    "Chromosome", "dbSNP_ID", "Gene", "Start", "End", "Ref", "Alt",
    "Variant_Type", "Variant_Classification", "VAF", "Genotype",
    "alt_count", "ref_count", "DP", "P_LP_Result", "Mode_of_Inheritance", "Variant_Record"
]

empty_df = [
            {'Rundate':None},
            {'SampleID':None},
            {'Variant':None},
            {'Clinical_Relevance':None},
            {'Disease_Name':None},
            {'Chromosome':None},
            {'dbSNP_ID':None},
            {'Gene':None},
            {'Start':None},
            {'End':None},
            {'Ref':None},
            {'Alt':None},
            {'Variant_Type':None},
            {'Variant_Classification':None},
            {'VAF':None},
            {'Genotype':None},
            {'alt_count':None},
            {'ref_count':None},
            {'DP':None},
            {'P_LP_Result':None},
            {'Mode_of_Inheritance':None},
            {'Variant_Record':None}
            ]


df = pd.DataFrame(data=np.nan, index=range(10), columns=columns)



#df = read_data_from_database()


page_number = 1
rows_per_page = 10


# Create the filter dropdowns for the sidebar
upload_rekap_excel = html.Div([
    dcc.Upload(
        id=f'upload-rekap-excel{pgnum}',
        #children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
        style={
            'width': '99%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
            'textAlign': 'center', 'margin': '10px', 'margin-left':'10px'
        },
        # Allow multiple files to be uploaded
        multiple=False,
        disabled=True
    ),
    
])

scrollable_markdown = {
            'height': '200px',        # Set the desired height
            'overflowY': 'scroll',    # Enable vertical scrolling
            'overflowX': 'auto',      # Enable horizontal scrolling if needed
            'border': '1px solid #ccc', # Optional: add a border for better visibility
            'padding': '10px'         # Optional: add some padding for better readability
        }

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


save_changes_modal_2 = html.Div([
                        dmc.Button('Save Changes', id=f'save-changes-button-{pgnum}', disabled=True),#style=big_button_style  #{**button_style, **{"margin-left":"10px"}}
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
                    ], style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center', 'margin-top':'20px'}) #

#filterable_columns = ['Rundate', 'SampleID', 'Variant', 'Clinical_Relevance', 'Disease_Name'] #, , , '''Gene'  'Nucleotide [AAchange]', 

# dropdowns = [dcc.Dropdown(
#                 id=f'filter-dropdown-{col}',
#                 options=[{'label': i, 'value': i} for i in sorted(df[col].unique())],
#                 multi=True,
#                 placeholder=f'{col}',
#                 style={'fontSize': '12px'}
#             ) for col in filterable_columns]

# dropdown_container = html.Div([
#                     ])
# dropdown_container.children.extend(dropdowns) 

# # Create a row for the dropdowns, positioned horizontally
# dropdown_row = dbc.Row(
#     [dbc.Col(dropdown, md=True) for dropdown in dropdowns],
#     className="mb-3",  # Adds a margin bottom for spacing
# )


# unique_sorted_options = {
#     col: [{'label': i, 'value': i} for i in sorted(df[col].unique())]
#     for col in filterable_columns
# }


# # Create the filter dropdowns for the sidebar
# sidebar_filters = html.Div([
#     html.Div([
#         html.P(f"{col}", style={'font-style':'italic'}), #className="lead"
#         dcc.Dropdown(
#             id=f'filter-dropdown-{col}',
#             options=unique_sorted_options[col],
#             #options = [{'label': i, 'value': i} for i in sorted(df[col].unique())],
#             multi=True,
#             placeholder=f'Select {col}...'
#         )
#     ], style={'margin-bottom': '10px'}) for col in filterable_columns
# ], style={'padding': '10px', 'margin-left':'5px'}) #'padding': '10px', 


main_table = get_main_table(df)

# main_table = dash_table.DataTable(
#                 id=f'editable-table-{pgnum}',
#                 columns=[{"name": i, "id": i} for i in df.columns if i != "Variant_Record"],
#                 data=df.iloc[:rows_per_page].to_dict('records'),
#                 editable=True,
#                 style_table={
#                     'minWidth': '100%',
#                     'overflowX': 'auto'  # Ensures horizontal scrolling if necessary
#                 },
#                 style_data={
#                     'fontSize': '14px',
#                     'whiteSpace': 'normal',  # Allows text wrapping within cells
#                     'height': 'auto',  # Adjusts row height to content
#                     'minWidth': '100px',  # Minimum width for all data cells
#                 },
#                 style_header={
#                     'fontSize': '14px',
#                     'fontWeight': 'bold',
#                     'whiteSpace': 'normal',  # Allows text wrapping within header cells
#                     'height': 'auto',  # Adjusts header height to content
#                     'minWidth': '100px',  # Minimum width for header cells
#                 },
#                 style_cell_conditional=[
#                     # Apply custom minWidth for specific columns here if needed
#                     # Example:
#                     # {'if': {'column_id': 'Your-Column-ID'},
#                     #  'minWidth': '150px', 'width': '150px', 'maxWidth': '150px'},
#                 ],
#                 fixed_columns={'headers': True, 'data': 3},
#                 page_current=0,
#                 page_size=rows_per_page,
#                 page_action='custom',
#                 virtualization=True,
#                 cell_selectable=True
#             )


# pagination_info = html.Div(id=f'pagination-info-{pgnum}', children=f"Entry: 1 -{min(rows_per_page, len(df))} of {len(df)}", style={'fontSize':'14px','margin-left':'10px','margin-bottom':'3px'})




layout = dmc.AppShell(
    [
        #dmc.AppShellHeader("Header", px=25),
        #dmc.AppShellNavbar("Navbar"),
        #dmc.AppShellAside("Aside", withBorder=False),
        dmc.AppShellMain(children=[
                dcc.Location(id=f'page-url-{pgnum}', refresh=True),
                dcc.Store(id=f'store-change-log-{pgnum}'),


                dmc.Title('Upload Rekap', order=3),
                dmc.Space(h=10),
                dmc.Divider(variant="solid", size="sm", color="grey"),
                dmc.Space(h=20),
                
                dmc.Grid(
                    children=[
                        dcc.Store(id='store-output'),
                        dmc.GridCol(html.Div([
                            dmc.Title('1. Select Database', order=4),
                            html.P('Please select the database that you want to change.', style={'margin':0}),
                            dmc.Space(h=10),
                            dmc.SegmentedControl(
                                id=f"database-selector-{pgnum}",
                                orientation="horizontal",
                                fullWidth=False,
                                data=[
                                    {"value": "-", "label": "None"},
                                    {"value": "TSHC", "label": "TSHC"},
                                    {"value": "BRCA12_Somatic", "label": "BRCA12_Somatic"},
                                      ],
                                radius='lg',
                                color='blue'
                                ),
                            dmc.Text(id='segmented-value'),                
                            
                            dmc.Space(h=50),

                            dmc.Title('2. File Upload', order=4),
                            html.P('Please upload the Rekap_[TSHC/BRCA12_Somatic]_MAF Excel file (.xlsx) that must contain "ALL" sheet in it.', style={'margin':0}),
                            html.Div([
                                upload_rekap_excel,
                                html.Div([
                                    dmc.Button('Upload File', id=f'upload-excel-btn-{pgnum}', disabled=True),#style=big_button_style  #{**button_style, **{"margin-left":"10px"}}
                                    ], style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center', 'margin-top':'20px'}), #
                                ], style={'margin-right':'30px'}),
                            ]), span=4),

                        dmc.Divider(orientation="vertical", variant="solid", size="xs", color="grey", style={"height": 750}),

                        dmc.GridCol(html.Div([
                            dmc.Title('3. File Preview', order=4),
                            dmc.Space(h=30),
                            html.Div([
                                main_table,
                                ], style={'margin-right':'30px'}),
                            save_changes_modal_2
                            ], style={'margin-left':'30px'}), span=4),
                    ], grow=True 
                ),

            ], style={'margin-left':'30px', 'margin-right':'10px', 'margin-top':'30px'})
    ],

)


@callback(
    Output(f'upload-rekap-excel{pgnum}', 'disabled'),
    Output(f'upload-excel-btn-{pgnum}', 'disabled'),
    Output(f'main-table-{pgnum}', 'rowData'),
    [Input(f'database-selector-{pgnum}','value')],
    #allow_duplicate=True
)
def database_selection(database_selector_value):
    print('database_selector_value',database_selector_value)
    if database_selector_value == '-' or database_selector_value == None:
        return True, True, empty_df
    else:
        return False, False, empty_df

@callback(
    Output(f'upload-rekap-excel{pgnum}', 'children'),
    Output(f'upload-excel-btn-{pgnum}', 'disabled', allow_duplicate=True),
    Output(f'save-changes-button-{pgnum}', 'disabled', allow_duplicate=True),
    [Input(f'upload-rekap-excel{pgnum}', 'filename')],
    [State(f'upload-rekap-excel{pgnum}', 'contents'),
     Input(f'database-selector-{pgnum}','value')],
     prevent_initial_call=True
)
def update_rekap_excel(rekap_filename, rekap_contents, database_selector_value):
    counteract_dict = {'TSHC':'BRCA12_Somatic','BRCA12_Somatic':'TSHC'}
    if rekap_filename is not None:
        print(database_selector_value)
        #print(rekap_filename)
        extension = '.xlsx'
        if extension not in rekap_filename:
            return html.Div(['Please input XLSX file only!'], style={'backgroundColor': 'red', 'color': 'white'}), True, True
        
        if database_selector_value == '-':
            return html.Div(['Please select the appropriate database!'], style={'backgroundColor': 'red', 'color': 'white'}), True, True
        
        if database_selector_value not in rekap_filename:
            return html.Div([f'You have selected "{database_selector_value}", but you have uploaded "{counteract_dict[database_selector_value]}" excel file!'], style={'backgroundColor': 'red', 'color': 'white'}), True, True

        rekap_file_path = os.path.join(input_temp_dir, rekap_filename)
        print('rekap_file_path:', rekap_file_path)
        with open(rekap_file_path, 'wb') as f:
            f.write(base64.b64decode(rekap_contents.split(",")[1]))

        print('Upload success: {}'.format(rekap_file_path))

        # Check if the file contains a sheet named "ALL"
        try:
            xls = pd.ExcelFile(rekap_file_path, engine='openpyxl')
            if 'ALL' not in xls.sheet_names:
                return html.Div(['The Excel file must contain a sheet named "ALL".'], style={'backgroundColor': 'red', 'color': 'white'}), True, True
            xls.close()
        except Exception as e:
            print(f"Error reading the Excel file: {e}")
            return html.Div(['Error reading the Excel file. Please ensure it is a valid XLSX file.'], style={'backgroundColor': 'red', 'color': 'white'}), True, True

        # Return updated Upload components with file names and blue background
        return html.Div([rekap_filename], style={'backgroundColor': '#1c7ed6', 'color': 'white'}), False, dash.no_update

    return html.Div(['Drag and Drop or ', html.A('Select Files')]), dash.no_update, dash.no_update

@callback(
    Output(f'main-table-{pgnum}', 'rowData', allow_duplicate=True),
    Output(f'save-changes-button-{pgnum}', 'disabled'),
    Input(f'upload-excel-btn-{pgnum}','n_clicks'),
    State(f'upload-rekap-excel{pgnum}', 'filename'),
    State(f'upload-excel-btn-{pgnum}','disabled'),
    prevent_initial_call=True
)
def preview_excel_rekap(n_clicks, rekap_filename, state_upload_btn):
    if rekap_filename is not None and state_upload_btn != True:
        #print('n_clicks',n_clicks)
        #print('rekap_content',rekap_filename)
        rekap_file_path = os.path.join(input_temp_dir, rekap_filename)
        df = convert_excel_to_df_vava(rekap_file_path)
        #print(df)
        rowData=df.to_dict("records")
        print('rowData', rowData)
        return rowData, False
    else:
        print('n_clicks',n_clicks)

        print('empty_df', empty_df)
        # print('rekap_content',rekap_filename)        
        return empty_df, dash.no_update

@callback(
    Output(f'store-change-log-{pgnum}','data'),
    Input(f"save-changes-button-{pgnum}", "n_clicks"),
    State(f'upload-rekap-excel{pgnum}', 'filename'),
    prevent_initial_call=True
)
def track_changes(*args):
    change_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    rekap_filename = args[-1]

    rekap_file_path = os.path.join(input_temp_dir, rekap_filename)
    df = convert_excel_to_df_vava(rekap_file_path)

    changes_list = {
        change_time:{
        "Variant Record": df.at[row, 'Variant_Record'],
        "Changed Column": col,
        "Previous Value": "No Previous Value (value added by Upload Rekap)",
        "New Value": df.at[row, col]
        }
        for row, col in df
    }

    print(changes_list)

    return 

@callback(
    Output(f"modal-simple-{pgnum}", "opened"),
    Output(f'page-url-{pgnum}', 'href'),
    Input(f"save-changes-button-{pgnum}", "n_clicks"),
    Input(f"modal-close-button-{pgnum}", "n_clicks"),
    Input(f"modal-submit-button-{pgnum}", "n_clicks"),
    State(f"modal-simple-{pgnum}", "opened"),
    prevent_initial_call=True,
)
def modal_demo(nc1, nc2, nc3, opened):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if 'modal-submit-button' in button_id:
        print('Submit Changes Button Pressed!!!')
        print('Commiting Changes to the Database!!!')

        #process_log_entries(DB_URI, log_entries)
        #print(DB_URI, log_entries)

        #print('Reloading the Database!!!')
        #global layout
        #layout = get_layout()
        return not opened, page_address

    return not opened, dash.no_update
