from sqlalchemy import create_engine, Column, String, Integer, Text, text, ForeignKey, TIMESTAMP, func, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd


# import pandas as pd
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy import text

# Create a base class
Base = declarative_base()

# Define the db_var table
class DbVar(Base):
    __tablename__ = 'db_var'
    Rundate = Column(Text)
    SampleID = Column(Text)
    Variant = Column(Text)
    Clinical_Relevance = Column(Text)
    Disease_Name = Column(Text)
    Chromosome = Column(Text)
    dbSNP_ID = Column(Text)
    Gene = Column(Text)
    Start = Column(Text)
    End = Column(Text)
    Ref = Column(Text)
    Alt = Column(Text)
    Variant_Type = Column(Text)
    Variant_Classification = Column(Text)
    VAF = Column(Text)
    Genotype = Column(Text)
    alt_count = Column(Text)
    ref_count = Column(Text)
    DP = Column(Text)
    P_LP_Result = Column(Text)
    Mode_of_Inheritance = Column(Text)
    Variant_Record = Column(Text, primary_key=True)

# Define the db_var_version_history table
class DbVarVersionHistory(Base):
    __tablename__ = 'db_var_version_history'
    Version_ID = Column(Integer, primary_key=True, autoincrement=True)
    Variant_Record = Column(Text, ForeignKey('db_var.Variant_Record'))
    Rundate = Column(Text)
    Changed_Column = Column(Text)
    Previous_Value = Column(Text)
    New_Value = Column(Text)
    Changed_By = Column(Text)
    Change_Date = Column(TIMESTAMP, server_default=func.current_timestamp())

# Function to initialize the database
def init_db(db_uri):
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

# Function to process log entries
def process_log_entries(db_uri, log_entries):
    session_factory = init_db(db_uri)
    session = session_factory()
    
    for entry in log_entries:
        for timestamp, change in entry.items():
            variant_record = change['Variant Record']
            changed_column = change['Changed Column']
            previous_value = change['Previous Value']
            new_value = change['New Value']

            # Update the db_var table
            record = session.query(DbVar).filter_by(Variant_Record=variant_record).first()
            if record:
                setattr(record, changed_column, new_value)
                #session.commit()

            # Log the change to db_var_version_history
            version_history_entry = DbVarVersionHistory(
                Variant_Record=variant_record,
                Rundate=record.Rundate if record else None,
                Changed_Column=changed_column,
                Previous_Value=previous_value,
                New_Value=new_value,
                Changed_By='user'  # Assuming 'user' as the user making the change
            )
            session.add(version_history_entry)
            #session.commit()
    session.commit()
    session.close()

# Function to append dataframe to the db_var table
def process_df(db_uri, df):
    session_factory = init_db(db_uri)
    session = session_factory()

    # Replace null values with empty strings
    df = df.fillna(" ")

    for index, row in df.iterrows():
        db_var_entry = DbVar(
            Rundate=row.get('Rundate', " "),
            SampleID=row.get('SampleID', " "),
            Variant=row.get('Variant', " "),
            Clinical_Relevance=row.get('Clinical_Relevance', " "),
            Disease_Name=row.get('Disease_Name', " "),
            Chromosome=row.get('Chromosome', " "),
            dbSNP_ID=row.get('dbSNP_ID', " "),
            Gene=row.get('Gene', " "),
            Start=row.get('Start', " "),
            End=row.get('End', " "),
            Ref=row.get('Ref', " "),
            Alt=row.get('Alt', " "),
            Variant_Type=row.get('Variant_Type', " "),
            Variant_Classification=row.get('Variant_Classification', " "),
            VAF=row.get('VAF', " "),
            Genotype=row.get('Genotype', " "),
            alt_count=row.get('alt_count', " "),
            ref_count=row.get('ref_count', " "),
            DP=row.get('DP', " "),
            P_LP_Result=row.get('P_LP_Result', " "),
            Mode_of_Inheritance=row.get('Mode_of_Inheritance', " "),
            Variant_Record=row.get('Variant_Record', " ")
        )
        session.add(db_var_entry)

    session.commit()
    session.close()



# def count_and_group(db_uri, table_name, count_col, group_col):
#     # Initialize the database session
#     session_factory = init_db(db_uri)
#     session = session_factory()
    
#     # Retrieve column names from the table
#     inspector = inspect(session.bind)
#     columns = [col['name'] for col in inspector.get_columns(table_name)]
    
#     # Filter out the group_col and count_col
#     selected_columns = [col for col in columns if col not in {group_col, count_col}]
    
#     # Create the SQL query string
#     sql_query = f"""
#     SELECT
#         {group_col},
#         COUNT(DISTINCT {count_col}) AS {count_col}_Count,
#         {', '.join(selected_columns)}
#     FROM {table_name}
#     GROUP BY {group_col};
#     """
    
#     # Execute the query and fetch all the results
#     result = session.execute(text(sql_query))
    
#     # Convert the result to a pandas DataFrame
#     df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
#     # Close the session
#     session.close()
    
#     return df


###################################


from sqlalchemy import create_engine, inspect, text
import pandas as pd

def count_and_group(db_uri, table_name, count_col, group_col):
    # Initialize the database session
    engine = create_engine(db_uri)
    connection = engine.connect()
    
    # Retrieve column names from the table
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    
    # Filter out the group_col and count_col
    other_columns = [col for col in columns if col not in {group_col, count_col}]
    
    # Find columns with the same value across all rows within each group
    consistent_columns = []
    for col in other_columns:
        check_query = f"""
        SELECT {group_col}, COUNT(DISTINCT {col})
        FROM {table_name}
        GROUP BY {group_col}
        HAVING COUNT(DISTINCT {col}) = 1;
        """
        result = connection.execute(text(check_query))

        print((result.rowcount))

        if result.rowcount == len(connection.execute(text(f"SELECT DISTINCT {group_col} FROM {table_name}")).fetchall()):
            consistent_columns.append(col)
    
    # Create the SQL query string
    if consistent_columns:
        sql_query = f"""
        SELECT
            {group_col},
            COUNT(DISTINCT {count_col}) AS {count_col}_Count,
            {', '.join(consistent_columns)}
        FROM {table_name}
        GROUP BY {group_col};
        """
    else:
        sql_query = f"""
        SELECT
            {group_col},
            COUNT(DISTINCT {count_col}) AS {count_col}_Count
        FROM {table_name}
        GROUP BY {group_col};
        """
    
    # Execute the query and fetch all the results
    result = connection.execute(text(sql_query))
    
    # Convert the result to a pandas DataFrame
    df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    # Close the connection
    connection.close()
    
    return df


##############################


# from sqlalchemy import create_engine, inspect, text
# import pandas as pd

# def count_and_group(db_uri, table_name, count_col, group_col):
#     # Initialize the database session
#     engine = create_engine(db_uri)
#     connection = engine.connect()
    
#     # Retrieve column names from the table
#     inspector = inspect(engine)
#     columns = [col['name'] for col in inspector.get_columns(table_name)]
    
#     # Filter out the group_col and count_col
#     other_columns = [col for col in columns if col not in {group_col, count_col}]
    
#     # Build the SQL query string
#     case_statements = []
#     for col in other_columns:
#         case_statements.append(f"""
#         GROUP_CON_CONCAT_DISTINCT({col}) AS {col}
#         """)
    
#     case_statements.append(f"""
#     COUNT(DISTINCT {count_col}) AS {count_col}_Count
#     """)
    
#     sql_query = f"""
#     WITH DistinctValues AS (
#         SELECT {group_col}, {', '.join(f'DISTINCT {col} AS {col}_distinct' for col in other_columns)}
#         FROM {table_name}
#         GROUP BY {group_col}
#     )
#     SELECT
#         {group_col},
#         {', '.join(case_statements)}
#     FROM DistinctValues
#     GROUP BY {group_col};
#     """
    
#     # Execute the query and fetch all the results
#     result = connection.execute(text(sql_query))
    
#     # Convert the result to a pandas DataFrame
#     df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
#     # Close the connection
#     connection.close()
    
#     return df