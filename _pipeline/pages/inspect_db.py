from sqlalchemy import create_engine, inspect
from variables import vava_db_dir, database_file, database_file_brcas, variant_table, version_history_table

db_name = 'TSHCvar_v2.db'
# Create an engine that connects to the SQLite database
engine = create_engine(f'sqlite:///{vava_db_dir}/{db_name}')
print()
# Create an inspector
inspector = inspect(engine)

# Get a list of all tables in the database
tables = inspector.get_table_names()
print(f"Tables in the database: {tables}")

# Loop through each table and print its columns
for table_name in tables:
    print(f"\nColumns in table '{table_name}':")
    columns = inspector.get_columns(table_name)
    for column in columns:
        print(f"Name: {column['name']}, Type: {column['type']}")

# Close the connection
engine.dispose()