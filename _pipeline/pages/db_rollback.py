import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
from dash import callback_context
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

import base64
import os
import shutil  # For file copying
import time
import threading


from PBTK import *
import pandas as pd
from sqlalchemy import create_engine
import sqlite3


from variables import vava_db_dir, database_file_tshc, variant_table

page_address = '/modify/rollback/'

dash.register_page(__name__,path=page_address,name='PBDA: Variant Vault',title='PBDA: Variant Vault')

pgnum = 3


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


engine = create_engine(f'sqlite:///{vava_db_dir}/{database_file_tshc}')




#db_path = f'{vava_db_dir}/{database_file}'

# Connect to the SQLite database
#conn = sqlite3.connect(db_path)

# Create a cursor object
#cur = conn.cursor()

# Execute a query
#cur.execute("SELECT * FROM db_var")



query = f"SELECT * FROM {variant_table}"
df = pd.read_sql(query, engine)


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


filterable_columns = ['Rundate', 'SampleID', 'Variant','Clinical_Relevance', 'Disease_Name'] #, , , '''Gene'  'Nucleotide [AAchange]', 

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

# Create the filter dropdowns for the sidebar
sidebar_filters = html.Div([
    html.Div([
        html.P(f"{col}", style={'font-style':'italic'}), #className="lead"
        dcc.Dropdown(
            id=f'filter-dropdown-{col}',
            options = [{'label': i, 'value': i} for i in sorted(df[col].unique())],
            multi=True,
            placeholder=f'Select {col}...'
        )
    ], style={'margin-bottom': '10px'}) for col in filterable_columns
], style={'padding': '10px', 'margin-left':'5px'}) #'padding': '10px', 




layout = dbc.Container([
    dbc.Row([
#        dbc.Col(html.Div([
#                html.Div([
#                    html.P("Filter Panel"),
#                        ], className="lead", style={'margin-left':'10px'}),
#                sidebar_filters
#                ]), md=4),  # Sidebar on the left taking up 4 out of 12 columns
        html.P("Filter Panel", className="lead"), #, style={'margin-left':'10px'}
        dropdown_row,
        dbc.Col(
            html.Div([
                html.Div([
                    html.Div([
                        html.P('Variant Database' , className="lead"),
                        dash_table.DataTable(
                            id=f'editable-table-{pgnum}',
                            columns = [{"name": i, "id": i} for i in df.columns if i != "Variant_Record"],
                            data=df.iloc[:rows_per_page].to_dict('records'),
                            editable=True,
                            style_table={'minWidth': '100%'},  #'overflowX': 'scroll'
                            style_data={'fontSize':'14px'},
                            style_header={'fontSize':'14px', 'font-weight':'bold'},
                            fixed_columns={'headers': True, 'data': 3},
                        ),
                        html.Div(id=f'pagination-info-{pgnum}', children=f"Page {page_number}, Rows 1-{min(rows_per_page, len(df))} of {len(df)}"),
                        html.Button('Previous', id='prev-button', n_clicks=0, style=button_style),
                        html.Button('Next', id='next-button', n_clicks=0, style=button_style),
                        #html.Button('Submit Changes', id='submit-button', n_clicks=0)
                    ]),
                    html.Br(),
                    html.Div([
                        html.P('Upload Rekap_TSHC_MAF File' , className="lead", style={'margin-bottom':'3px'}),
                        html.P('Please upload the Excel file (.xlsx) that must contain "ALL" sheet in it.'),
                        upload_rekap_excel,

                    ]),

                ], ), #style={'margin-right':'30px'}
                
                html.Div([
                    html.Button('Save All Changes', id='save-changes-btn', n_clicks=0, style=big_button_style), #{**button_style, **{"margin-left":"10px"}}
                ], style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center', 'margin-top':'20px'}), #
                html.Br(),

        ]), md=12)  # Main content area taking up the remaining 8 out of 12 columns
    ],style={'margin-top':'10px'})
], fluid=True)




def register_callbacks(app):
    #@app.callback(
    #Output('editable-table', 'data'),
    #Input('submit-button', 'n_clicks'),
    #State('editable-table', 'data'),
    #prevent_initial_call=True,
    #allow_duplicate=True
    #)
    #def update_database(n_clicks, rows):
    #    if n_clicks > 0:
    #        new_df = pd.DataFrame(rows)
    #        new_df.to_sql(f'{variant_table}', engine, if_exists='replace', index=False)
    #    return rows

    @app.callback(
        Output(f'upload-rekap-excel{pgnum}', 'children', allow_duplicate=True),
        [Input(f'upload-rekap-excel{pgnum}', 'filename')],
        [State(f'upload-rekap-excel{pgnum}', 'contents')],
        prevent_initial_call=True
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


# Define callback to update the table and pagination information
    @app.callback(
        [Output(f'editable-table-{pgnum}', 'data', allow_duplicate=True),
        Output(f'pagination-info-{pgnum}', 'children', allow_duplicate=True)],
        [Input(f'filter-dropdown-{col}', 'value') for col in filterable_columns] +
        [Input('prev-button', 'n_clicks'),
        Input('next-button', 'n_clicks')],
        [State(f'editable-table-{pgnum}', 'data')],
        prevent_initial_call=True
    )
    def update_table(*args):
        # The last three arguments are the previous and next button clicks, and the current table data
        prev_clicks, next_clicks, data = args[-3], args[-2], args[-1]
        filter_values = args[:-3]  # All filter values
        
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        global page_number
        if 'filter-dropdown' in button_id:
            page_number = 1  # Reset to the first page on filter change

        # Filter the DataFrame based on selected values for each dropdown
        filtered_df = df
        for filter_val, col in zip(filter_values, filterable_columns):
            if filter_val:  # If any value is selected
                filtered_df = filtered_df[filtered_df[col].isin(filter_val)]

        if button_id == 'prev-button' and page_number > 1:
            page_number -= 1
        elif button_id == 'next-button' and page_number < (len(filtered_df) // rows_per_page) + 1:
            page_number += 1

        start_index = (page_number - 1) * rows_per_page
        end_index = start_index + rows_per_page

        displayed_data = filtered_df.iloc[start_index:end_index].to_dict('records')
        pagination_info = f"Page {page_number}, Rows {start_index + 1}-{min(end_index, len(filtered_df))} of {len(filtered_df)}"

        return displayed_data, pagination_info
    
