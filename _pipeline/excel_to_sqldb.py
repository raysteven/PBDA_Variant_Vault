import hashlib
import os
from PBTK import *
import pandas as pd
from sqlalchemy import create_engine, Column, String, MetaData, Table
import sqlite3
import argparse

def generate_unique_id(data):
    # Create a hash object
    hash_object = hashlib.sha256(data.encode())
    
    # Convert the hash to a hexadecimal string
    hex_dig = hash_object.hexdigest()
    
    # Convert hexadecimal to integer (you can also truncate this to fit your needs)
    unique_id = str(int(hex_dig, 16))
    
    return unique_id



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create database from excel files into a sql file.')
    parser.add_argument('--source', '-s', required=True, help='Source folder')
    parser.add_argument('--name', '-n', required=True, help='Name of the database file')
    parser.add_argument('--target', '-t', required=True, help='Target folder')


    args = parser.parse_args()

    source = args.source
    vava_db_dir = args.target
    database_file = args.name


    current_directory = os.getcwd()
    bahan_db = os.listdir(os.path.join(current_directory, source))

    bahan_db_df = pd.DataFrame()

    # Loop through the files, read each into a DataFrame, and append it to the merged_df
    for file in bahan_db:
        print(file)
        file_path = os.path.join(current_directory, source, file)
        df_temp = pd.read_excel(file_path, engine='openpyxl')
        bahan_db_df = pd.concat([bahan_db_df, df_temp], ignore_index=True)

    try:
        bahan_db_df = bahan_db_df.drop(columns='Unnamed: 0')
        bahan_db_df = bahan_db_df.drop(columns='Nucleotide [AAchange].1')
    except:
        pass
    bahan_db_df.dropna(subset=['Rundate'], inplace=True)
    bahan_db_df.fillna(' ', inplace=True)

    bahan_db_df.rename(columns={'Disease_Name': 'Disease Name'}, inplace=True)
    all_columns = bahan_db_df.columns
    desired_columns = ['Rundate','SampleID','Nucleotide [AAchange]', 'Clinical Relevance', 'Disease Name', 'Chromosome', 'dbSNP ID']
    new_column_order = [col for col in desired_columns if col in all_columns] + [col for col in all_columns if col not in desired_columns]
    bahan_db_df = bahan_db_df[new_column_order]


    # Convert the 'Date' column to datetime format using the 'dayfirst' parameter
    bahan_db_df['Rundate'] = pd.to_datetime(bahan_db_df['Rundate'], dayfirst=True, errors='coerce')

    # Convert the datetime objects back to strings in the desired format
    bahan_db_df['Rundate'] = bahan_db_df['Rundate'].dt.strftime('%Y/%m/%d')

    bahan_db_df['Variant_Record'] = bahan_db_df.apply(lambda row: generate_unique_id(row['Rundate'] + ' | ' + row['SampleID'] + ' | ' + row['Nucleotide [AAchange]']), axis=1)


    bahan_db_df.at[0,'Variant_Record']
    duplicate_rows_specific = bahan_db_df[bahan_db_df.duplicated(['Variant_Record'])]
    print(duplicate_rows_specific)

    final_column_name = {
        'Nucleotide [AAchange]':'Variant',
        'Clinical Relevance':'Clinical_Relevance',
        'Disease Name':'Disease_Name',
        'dbSNP ID':'dbSNP_ID',
        'Variant Type':'Variant_Type',
        'P/LP_Result':'P_LP_Result'
    }
    bahan_db_df.rename(columns=final_column_name, inplace=True)




    # Remove duplicates based on the 'Variant Record' column, keeping the first occurrence
    df_unique = bahan_db_df.drop_duplicates(subset=['Variant_Record'], keep='first')

    table_name1 = 'db_var'
    table_name2 = 'db_var_version_history'

    # SQL statement for creating a table
    create_table_sql1 = f"""
    CREATE TABLE IF NOT EXISTS {table_name1} (
        `Rundate` TEXT,
        `SampleID` TEXT,
        `Variant` TEXT,
        `Clinical_Relevance` TEXT,
        `Disease_Name` TEXT,
        `Chromosome` TEXT,
        `dbSNP_ID` TEXT,
        `Gene` TEXT,
        `Start` TEXT,
        `End` TEXT,
        `Ref` TEXT,
        `Alt` TEXT,
        `Variant_Type` TEXT,
        `Variant_Classification` TEXT,
        `VAF` TEXT,
        `Genotype` TEXT,
        `alt_count` TEXT,
        `ref_count` TEXT,
        `DP` TEXT,
        `P_LP_Result` TEXT,
        `Mode_of_Inheritance` TEXT,
        `Variant_Record` TEXT PRIMARY KEY
    );
    """


    # SQL statement for creating a table
    create_table_sql2 = f"""
    CREATE TABLE IF NOT EXISTS {table_name2} (
        `Version_ID` INTEGER PRIMARY KEY AUTOINCREMENT,
        `Variant_Record` TEXT,
        `Rundate` TEXT,
        `Changed_Column` TEXT,
        `Previous_Value` TEXT,
        `New_Value` TEXT,
        `Changed_By` TEXT,
        `Change_Date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(`Variant_Record`) REFERENCES {table_name1} (`Variant_Record`)
    );
    """


    # Replace 'your_database.sqlite' with the path to your SQLite file
    db_path = f'{vava_db_dir}/{database_file}'

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Execute the SQL statement to create the table
    cursor.execute(create_table_sql1)
    cursor.execute(create_table_sql2)

    # Insert the deduplicated data into the SQL table
    df_unique.to_sql(table_name1, conn, if_exists='append', index=False, method='multi', chunksize=500)

    # Verify insertion by querying the first 5 rows
    cursor.execute(f"SELECT * FROM {table_name1} LIMIT 5;")
    rows = cursor.fetchall()

    # Display the first 5 rows from the database for verification
    for row in rows:
        print(row)

    # Verify insertion by querying the first 5 rows
    cursor.execute(f"SELECT * FROM {table_name2} LIMIT 5;")
    rows = cursor.fetchall()

    # Display the first 5 rows from the database for verification
    for row in rows:
        print(row)


    # Close the connection to the database
    conn.close()