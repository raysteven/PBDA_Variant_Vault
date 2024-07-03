# main.py
from modify_db import process_log_entries
from variables import vava_db_dir, database_file, database_file_brcas, variant_table, version_history_table

# Define the database URI
DB_URI = f'sqlite:///{vava_db_dir}/{database_file_brcas}'  # Update this to the appropriate URI

# Define the log entries
log_entries = [
    {'2024-06-07T07:19:34Z': {'Variant Record': '52015432667221984483027277928822521353460551679304275030979138556913153714514', 'Changed Column': 'Disease_Name', 'Previous Value': 'Disease_Y', 'New Value': 'Disease_Z'}},
    {'2024-06-07T07:19:34Z': {'Variant Record': '52015432667221984483027277928822521353460551679304275030979138556913153714514', 'Changed Column': 'Chromosome', 'Previous Value': 'chr13', 'New Value': 'chrX'}}
]

# Process the log entries
process_log_entries(DB_URI, log_entries)
print('Save Changes Success!')