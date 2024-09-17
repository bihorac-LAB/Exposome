import pandas as pd
import os
import concurrent.futures
import logging
from create_directories import create_directories
from fetch_data import fetch_data_and_save
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

#extract required info from OMOP database
def omop_extract_and_save_data(user, password, server, port, database):
    """
    Executes three SQL queries in parallel to categorize data based on the validity of latitude, longitude, and address_1.
    The results of each query are saved in separate directories in batches of 100,000 rows per CSV.

        user (str): Database username
        password (str): Database password
        server (str): Database server address
        port (int): Port number for the database
        database (str): Database name
    
    Directories will be created:
        - './Linkage_data/valid_lat_long'
        - './Linkage_data/invalid_lat_lon_address'
        - './Linkage_data/valid_address'
    """

    # Fetch credentials from environment variables
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    server = os.getenv('DB_SERVER')
    port = os.getenv('DB_PORT')
    database = os.getenv('DB_DATABASE')

    # Connection string for the database
    conn_str = (
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={server},{port};'
        f'DATABASE={database};'
        f'UID={user};'
        f'PWD={password}'
    )

    # Base directory for saving CSVs
    base_directory = './Linkage_data'

    #Categories and corresponding directories divided into three parts
    categories = {
        'Latlong': 'valid_lat_long',
        'Invalid': 'invalid_lat_lon_address',
        'Address': 'valid_address'
    }

    # SQL Queries for each category
    query_files = {
        'Latlong': 'sql/fetch_latlong.sql',
        'Invalid': 'sql/fetch_invalid.sql',
        'Address': 'sql/fetch_address.sql'
    }

    create_directories(base_directory, categories)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(fetch_data_and_save, category, query_files[category], conn_str, base_directory, categories): category
            for category in categories.keys()
        }
        for future in concurrent.futures.as_completed(futures):
            category = futures[future]
            try:
                future.result()
                logging.info(f"Data extraction completed for {category}.")
            except Exception as exc:
                logging.error(f"Data extraction failed for {category}: {exc}")
