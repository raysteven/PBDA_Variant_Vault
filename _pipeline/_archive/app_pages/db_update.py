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
from sqlalchemy import text


from variables import vava_db_dir, database_file, variant_table, version_history_table


user = 'admin'


pgnum = 2


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




#db_path = f'{vava_db_dir}/{database_file}'

# Connect to the SQLite database
#conn = sqlite3.connect(db_path)

# Create a cursor object
#cur = conn.cursor()

# Execute a query
#cur.execute("SELECT * FROM db_var")

def read_data_from_database():
    engine = create_engine(f'sqlite:///{vava_db_dir}/{database_file}')
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


filterable_columns = ['Rundate', 'SampleID', 'Variant', 'Clinical_Relevance', 'Disease_Name'] #, , , '''Gene'  'Nucleotide [AAchange]', 

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


'''
main_table = dash_table.DataTable(
                id=f'editable-table-{pgnum}',
                columns = [{"name": i, "id": i} for i in df.columns ], #if i != "Variant_Record"
                data=df.iloc[:rows_per_page].to_dict('records'),
                editable=True,
                style_table={'minWidth': '100%'},  #'overflowX': 'scroll'  | 'minWidth': '100%'
                style_data={'fontSize':'14px'},
                style_header={'fontSize':'14px', 'font-weight':'bold'},
                fixed_columns={'headers': True, 'data': 3},
                page_current=0,
                page_size=10,
                page_action='custom'
                )
'''

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




layout = dbc.Container([
    dbc.Row([
##        dbc.Col(html.Div([
#                html.Div([
#                    html.P("Filter Panel"),
#                        ], className="lead", style={'margin-left':'10px'}),
#                sidebar_filters
#                ]), md=4),  # Sidebar on the left taking up 4 out of 12 columns
        
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
                        #html.Button('Previous', id='prev-button', n_clicks=0, style=button_style),
                        #html.Button('Next', id='next-button', n_clicks=0, style=button_style),
                        #html.Button('Submit Changes', id='submit-button', n_clicks=0)
                    ]),
                    html.Br(),
                    html.Div([
                        html.P('Upload Rekap_TSHC_MAF File' , className="lead", style={'margin-bottom':'3px'}),
                        html.P('Please upload the Excel file (.xlsx) that must contain "ALL" sheet in it.'),
                        upload_rekap_excel,
                    ]),

                ], ), #style={'margin-right':'30px'}


                #dcc.Store(id='store-original-data', data=df.to_dict('records')),
                dcc.Store(id='store-selected-cell'),
                html.Div(id='output-selected-cell'),



                html.Div([
                    html.Button('Save All Changes', id='save-changes-btn', n_clicks=0, style=big_button_style), #{**button_style, **{"margin-left":"10px"}}
                ], style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center', 'margin-top':'20px'}), #
                html.Br(),

        ]), md=12)  # Main content area taking up the remaining 8 out of 12 columns
    ],style={'margin-top':'10px'})
], fluid=True)




def register_callbacks(app):
    @app.callback(
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

        

        #displayed_data = filtered_df.iloc[start_index:end_index].to_dict('records')
        #pagination_info = f"Page {page_number}, Rows {start_index + 1}-{min(end_index, len(filtered_df))} of {len(filtered_df)}"
        pagination_info = f"Entry: {min(d_start_index, len(filtered_df))}-{min(end_index, len(filtered_df))} of {len(filtered_df)}"
        return displayed_table, pagination_info


    @app.callback(
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
    

    @app.callback(
        Output('store-selected-cell', 'data'),
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

    @app.callback(
        Output('output-selected-cell', 'children'),
        [Input('store-selected-cell', 'data')]
    )
    def display_selected_cell(data):
        if data:
            edited = "Edited" if data['original_value'] != data['selected_value'] else "No Edit"
            #return f"Column B value: {data['selected_value']}, Selected Column: {data['selected_column']}" #, Status: {data['edit_status']}
            return f"Original Value: {data['original_value']}, Selected Value: {data['selected_value']}, Column B Value: {data['selected_index']}, Selected Column: {data['selected_column']}, Edit Status: {edited}"

        return "No cell selected"



# Define callback to update the table and pagination information
#    @app.callback(
#        [Output(f'editable-table-{pgnum}', 'data',allow_duplicate=True),
#        Output(f'pagination-info-{pgnum}', 'children')],
#        [Input(f'filter-dropdown-{col}', 'value') for col in filterable_columns] +
#        [Input('prev-button', 'n_clicks'),
#        Input('next-button', 'n_clicks')],
#        [State(f'editable-table-{pgnum}', 'data')],
#        prevent_initial_call=True
#    )
#    def update_table(*args):
#        # The last three arguments are the previous and next button clicks, and the current table data
#        prev_clicks, next_clicks, data = args[-3], args[-2], args[-1]
#        filter_values = args[:-3]  # All filter values
#        
#        ctx = dash.callback_context
#        if not ctx.triggered:
#            raise PreventUpdate

#        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
#        
#       global page_number
#        if 'filter-dropdown' in button_id:
#            page_number = 1  # Reset to the first page on filter change

#        # Filter the DataFrame based on selected values for each dropdown
#        filtered_df = df
#        for filter_val, col in zip(filter_values, filterable_columns):
#            if filter_val:  # If any value is selected
#                filtered_df = filtered_df[filtered_df[col].isin(filter_val)]

#        if button_id == 'prev-button' and page_number > 1:
#            page_number -= 1
#        elif button_id == 'next-button' and page_number < (len(filtered_df) // rows_per_page) + 1:
#            page_number += 1

#        start_index = (page_number - 1) * rows_per_page
#        end_index = start_index + rows_per_page

#        displayed_data = filtered_df.iloc[start_index:end_index].to_dict('records')
#        pagination_info = f"Page {page_number}, Rows {start_index + 1}-{min(end_index, len(filtered_df))} of {len(filtered_df)}"

#        return displayed_data, pagination_info


    # Callback to save changes to the database
#    @app.callback(
#        Output(f'editable-table-{pgnum}', 'data'), #, allow_duplicate=True
#        Input('save-changes-btn', 'n_clicks'),
#        State(f'editable-table-{pgnum}', 'data'),
#        #prevent_initial_call=True,
#    )
#    def save_changes_database(n_clicks, rows):
#        global df
#        if n_clicks > 0:
#            for row in rows:
#                # Log current state to version history before update
#                #print(row)

#                row_df = pd.DataFrame(row, index=[0])
#                print("------MODIFIED-----")
#                print(row_df)
#                
#                print("------Variant_Record-----")
#                variant_record = row_df['Variant_Record']
#                print(variant_record)

#                original_df_at_this_variant_record = df[df['Variant_Record']==variant_record]
#                print("------ORIGINAL-----")
#                print(original_df_at_this_variant_record)
#                comparison_result = original_df_at_this_variant_record.equals(row_df)
#                print("Are the rows with this Variant_Record the same in both DataFrames?", comparison_result)

#                db_path = f'{vava_db_dir}/{database_file}'
#                # Connect to the SQLite database
#                conn = sqlite3.connect(db_path)
#                print('Connection Opened')
#                cursor = conn.cursor()

#                # SQL statement for creating a table
#                create_table_sql1 = f"""
#                CREATE TABLE IF NOT EXISTS {variant_table} (
#                    `Rundate` TEXT,
#                    `SampleID` TEXT,
#                    `Variant` TEXT,
#                    `Clinical_Relevance` TEXT,
#                    `Disease_Name` TEXT,
#                    `Chromosome` TEXT,
#                    `dbSNP_ID` TEXT,
#                    `Gene` TEXT,
#                    `Start` TEXT,
#                    `End` TEXT,
#                    `Ref` TEXT,
#                    `Alt` TEXT,
#                    `Variant_Type` TEXT,
#                    `Variant_Classification` TEXT,
#                    `VAF` TEXT,
#                    `Genotype` TEXT,
#                    `alt_count` TEXT,
#                    `ref_count` TEXT,
#                    `DP` TEXT,
#                    `P_LP_Result` TEXT,
#                    `Mode_of_Inheritance` TEXT,
#                    `Variant_Record` TEXT PRIMARY KEY
#                );
#                """

#                # SQL statement for creating a table
#                create_table_sql2 = f"""
#                CREATE TABLE IF NOT EXISTS {version_history_table} (
#                    `version_id` INTEGER PRIMARY KEY AUTOINCREMENT,
#                    `Rundate` TEXT,
#                    `SampleID` TEXT,
#                    `Variant` TEXT,
#                    `Clinical_Relevance` TEXT,
#                    `Disease_Name` TEXT,
#                    `Chromosome` TEXT,
#                    `dbSNP_ID` TEXT,
#                    `Gene` TEXT,
#                    `Start` TEXT,
#                    `End` TEXT,
#                    `Ref` TEXT,
#                    `Alt` TEXT,
#                    `Variant_Type` TEXT,
#                    `Variant_Classification` TEXT,
#                    `VAF` TEXT,
#                    `Genotype` TEXT,
#                    `alt_count` TEXT,
#                    `ref_count` TEXT,
#                    `DP` TEXT,
#                    `P_LP_Result` TEXT,
#                    `Mode_of_Inheritance` TEXT,
#                    `Variant_Record` TEXT,
#                    `changed_by` TEXT,
#                    `change_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                    FOREIGN KEY(`Variant_Record`) REFERENCES {variant_table} (`Variant_Record`)
#                );
#                """

#                cursor.execute(create_table_sql1)
#                cursor.execute(create_table_sql2)

#                # Insert the deduplicated data into the SQL table
#                if comparison_result == False:
#                    row_df.to_sql(version_history_table, conn, if_exists='append', index=False, method='multi', chunksize=500)

#                    # Insert or replace into variant_table
#                    placeholders = ', '.join(['?'] * len(row_df.columns))
#                    columns = ', '.join(row_df.columns)
#                    sql = f"INSERT OR REPLACE INTO {variant_table} ({columns}) VALUES ({placeholders})"
#                    cursor.execute(sql, row_df.iloc[0].values)
#                    conn.commit()

#                    print('Row inserted or replaced successfully.')

#                    #conn.close()


#               #cursor.execute(sql_query_log_to_vht2)
#                print('Command Executed')
#                #cursor.execute(sql_query_replace_new_data, {'Rundate':row['Rundate'], 'SampleID':row['SampleID'], 'Nucleotide':row['Nucleotide [AAchange]'], 'Clinical':row['Clinical Relevance'], 'Disease':row['Disease Name'], 'Chromosome':row['Chromosome'], 'dbSNP':row['dbSNP ID'], 'Gene':row['Gene'], 'Start':row['Start'], 'End':row['End'], 'Ref':row['Ref'], 'Alt':row['Alt'], 'Variant':row['Variant Type'], 'Variant_Classification':row['Variant_Classification'], 'VAF':row['VAF'], 'Genotype':row['Genotype'], 'alt_count':row['alt_count'], 'ref_count':row['ref_count'], 'DP':row['DP'], 'P':row['P/LP_Result'], 'Mode_of_Inheritance':row['Mode_of_Inheritance'], 'Variant_Record':row['Variant_Record']})
                
#                # Verify insertion by querying the first 5 rows
#                cursor.execute(f"SELECT * FROM {version_history_table} LIMIT 5;")
#                rows = cursor.fetchall()

#                # Display the first 5 rows from the database for verification
#                for row in rows:
#                    print(row)                
                    
#                conn.close()
#                print('Connection Closed')

#        df = read_data_from_database()
#        return df.to_dict('records')

