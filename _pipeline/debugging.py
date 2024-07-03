import os
import pandas as pd
from sqlalchemy import create_engine

# Change to the correct directory if necessary
os.chdir('/mnt/c/Users/MSI/Variant_Vault/_pipeline')

# Verify the database file path
database_path = '/mnt/c/Users/MSI/Variant_Vault/_pipeline/your_database_file.db'
engine = create_engine(f'sqlite:///{database_path}')

def read_data_from_database():
    query = "SELECT * FROM your_table_name"
    df = pd.read_sql(query, engine)
    print("Columns in the DataFrame:", df.columns)  # Print DataFrame columns
    return df

df = read_data_from_database()

# Check if 'Variant' column exists before using it
if 'Variant' in df.columns:
    options = [{'label': i, 'value': i} for i in sorted(df['Variant'].unique())]
else:
    print("Column 'Variant' does not exist in the DataFrame")
    options = []  # or handle accordingly

# Rest of your script
print(options)
