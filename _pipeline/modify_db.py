from sqlalchemy import create_engine, Column, String, Integer, Text, ForeignKey, TIMESTAMP, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd

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
