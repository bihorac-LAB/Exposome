import pyodbc
import pandas as pd
import os
import shutil
import subprocess
import sys
import argparse
import logging
from sqlalchemy import create_engine
import concurrent.futures

def omop_extraction(user, password, server, port, database):
    """
    Executes three SQL queries in parallel to categorize data based on the validity of latitude, longitude, and address_1.
    Each query's results are saved in different directories in batches of 100000 rows per CSV.
    """
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server},{port};DATABASE={database};UID={user};PWD={password}'
    base_directory = './Linkage_data'
    categories = {
        'Latlong': 'valid_lat_long',
        'Invalid': 'invalid_lat_lon_address',
        'Address': 'valid_address'
    }

    # Create directories
    for category in categories.values():
        os.makedirs(os.path.join(base_directory, category), exist_ok=True)

    # SQL Queries for each category
    queries = {
        'Latlong': """
            WITH patient AS (
                SELECT p.person_id, v.visit_occurrence_id, v.visit_start_date, v.visit_end_date
                FROM IC3_INPATIENT_PIPELINE_2024.CDM.PERSON p
                LEFT JOIN IC3_INPATIENT_PIPELINE_2024.CDM.VISIT_OCCURRENCE v ON p.person_id = v.person_id),
            address AS (
                SELECT entity_id, L.location_id, L.address_1, L.city, L.state, L.zip, L.county, L.latitude, L.longitude, L.FIPS, LS.start_date, LS.end_date
                FROM LOCATION L LEFT JOIN LOCATION_HISTORY LS ON L.location_id = LS.location_id)
            SELECT person_id, visit_occurrence_id, visit_start_date, visit_end_date, address_1, city, state, zip, county, latitude, longitude
            FROM patient p
            LEFT JOIN address a ON p.person_id = a.entity_id
            WHERE p.visit_start_date BETWEEN a.start_date AND a.end_date
              AND p.visit_end_date BETWEEN a.start_date AND a.end_date
              AND visit_start_date >= '2012-01-01'
              AND NOT (LTRIM(RTRIM(ISNULL(a.latitude, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))
              AND NOT (LTRIM(RTRIM(ISNULL(a.longitude, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))""",
        
        'Invalid': """
            WITH patient AS (
                SELECT p.person_id, v.visit_occurrence_id, v.visit_start_date, v.visit_end_date
                FROM IC3_INPATIENT_PIPELINE_2024.CDM.PERSON p
                LEFT JOIN IC3_INPATIENT_PIPELINE_2024.CDM.VISIT_OCCURRENCE v ON p.person_id = v.person_id),
            address AS (
                SELECT entity_id, L.location_id, L.address_1, L.city, L.state, L.zip, L.county, L.latitude, L.longitude, L.FIPS, LS.start_date, LS.end_date
                FROM LOCATION L LEFT JOIN LOCATION_HISTORY LS ON L.location_id = LS.location_id)
            SELECT person_id, visit_occurrence_id, visit_start_date, visit_end_date, address_1, city, state, zip, county, latitude, longitude
            FROM patient p
            LEFT JOIN address a ON p.person_id = a.entity_id
            WHERE p.visit_start_date BETWEEN a.start_date AND a.end_date
              AND p.visit_end_date BETWEEN a.start_date AND a.end_date
              AND visit_start_date >= '2012-01-01'
              AND (LTRIM(RTRIM(ISNULL(a.latitude, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))
              AND (LTRIM(RTRIM(ISNULL(a.longitude, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))
              AND (LTRIM(RTRIM(ISNULL(a.address_1, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))""",

        'Address': """
            WITH patient AS (
                SELECT p.person_id, v.visit_occurrence_id, v.visit_start_date, v.visit_end_date
                FROM IC3_INPATIENT_PIPELINE_2024.CDM.PERSON p
                LEFT JOIN IC3_INPATIENT_PIPELINE_2024.CDM.VISIT_OCCURRENCE v ON p.person_id = v.person_id),
            address AS (
                SELECT entity_id, L.location_id, L.address_1, L.city, L.state, L.zip, L.county, L.latitude, L.longitude, L.FIPS, LS.start_date, LS.end_date
                FROM LOCATION L LEFT JOIN LOCATION_HISTORY LS ON L.location_id = LS.location_id)
            SELECT person_id, visit_occurrence_id, visit_start_date, visit_end_date, address_1, city, state, zip, county, latitude, longitude
            FROM patient p
            LEFT JOIN address a ON p.person_id = a.entity_id
            WHERE p.visit_start_date BETWEEN a.start_date AND a.end_date
              AND p.visit_end_date BETWEEN a.start_date AND a.end_date
              AND visit_start_date >= '2012-01-01'
              AND (LTRIM(RTRIM(ISNULL(a.latitude, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))
              AND (LTRIM(RTRIM(ISNULL(a.longitude, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))
              AND NOT (LTRIM(RTRIM(ISNULL(a.address_1, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))"""
    }

    # Function to fetch and save data
    def fetch_and_save(category, query):
        filename_template = os.path.join(base_directory, categories[category], f"{category}_{{}}.csv")
        with pyodbc.connect(conn_str) as conn:
            offset = 0
            batch_number = 1
            while batch_number <= 2: #True: #testing
                batch_query = f"{query} ORDER BY person_id, visit_start_date OFFSET {offset} ROWS FETCH NEXT 100000 ROWS ONLY"
                df = pd.read_sql(batch_query, conn)
                if df.empty:
                    break
                df.to_csv(filename_template.format(batch_number), index=False)
                offset += 100000
                batch_number += 1

    # Execute queries in parallel using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_and_save, category, query) for category, query in queries.items()]
        concurrent.futures.wait(futures)  # Wait for all tasks to complete

def generate_coordinates_degauss(df, columns, threshold):
#     # Load the data
#     if inputdata.endswith('.csv'):
#         df = pd.read_csv(inputdata)
#     elif inputdata.endswith(('.xlsx', '.xls')):
#         df = pd.read_excel(inputdata)

    # Convert columns to string type
    for col in columns:
        df[col] = df[col].astype(str)
    
    # Handle single column or concatenate multiple columns
    if len(columns) == 1:
        df['address'] = df[columns[0]].str.title().replace(r'[^a-zA-Z0-9 ]', ' ', regex=True)
    else:
        df['address'] = df.apply(lambda row: ' '.join(row[columns]).lower(), axis=1)
        df['address'] = df['address'].str.title()
        df['address'] = df['address'].replace(r'[^a-zA-Z0-9 ]', ' ', regex=True)

    # Reorder columns to ensure 'address' is the first column
    cols = ['address'] + [col for col in df.columns if col != 'address']
    df = df[cols]
    
    # Drop original address columns if they are no longer needed
    if len(columns) > 1:
        df.drop(columns=columns, inplace=True)
    
    # Save the preprocessed DataFrame to CSV
    preprocessed_file_path = './preprocessed_1.csv'
    df.to_csv(preprocessed_file_path, index=False)
    
    # Define the Docker command
    docker_command = [
        'docker', 'run', '--rm',
        '-v', f'"{os.getcwd()}:/tmp"',
        'ghcr.io/degauss-org/geocoder:3.3.0',
        '/tmp/preprocessed_1.csv',
        str(threshold)
    ]
    
    try:
        result = subprocess.run(' '.join(docker_command), shell=True, check=True, capture_output=True, text=True)
        print("Docker command executed successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing Docker command: {e}")
        print(e.stderr)

    # Define the output file name
    output_file_name = f"preprocessed_1_geocoder_3.3.0_score_threshold_{threshold}.csv"
#     # Read the CSV file into a pandas DataFrame
#     df = pd.read_csv(output_file_name)

    # Save the DataFrame back to CSV if needed
#     df.to_csv(output_file_name, index=False)
    return output_file_name

def generate_fips_degauss(df, year):
    print('Generating FIPS...')

    preprocessed_file_path = './preprocessed_2.csv'
#     df.drop(columns={'matched_street','matched_zip','matched_city', 'matched_state', 'address', 'score', 'precision', 'geocode_result'}, inplace=True)
    df.to_csv(preprocessed_file_path, index=False)
    
    output_file = f"preprocessed_2_census_block_group_0.6.0_{year}.csv"    
#     output_file = f"{df.replace('.csv', '')}_census_block_group_0.6.0_{year}.csv"
    docker_command2 = ["docker", "run", "--rm", "-v", f"{os.getcwd()}:/tmp", "ghcr.io/degauss-org/census_block_group:0.6.0", '/tmp/preprocessed_2.csv', str(year)]
    try:
        result = subprocess.run(docker_command2, check=True, capture_output=True, text=True)
        print("Docker command executed successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing Docker command 2: {e}")
        print(e.stderr)
        return None

    if os.path.exists(output_file):
        print(f"Output file generated: {output_file}")
        df = pd.read_csv(output_file)
        df['FIPS'] = df[f'census_tract_id_{year}']
        df.drop(columns=[f'census_block_group_id_{year}', f'census_tract_id_{year}'], inplace=True)
        df.to_csv(output_file, index=False)
        return output_file
    else:
        print(f"Expected output file not found: {output_file}")
        return None

#this version is conbined all year csv output in one csv file(keep the original datasets column name)
def sdoh_linkage(df, date_column, output_file_path):
    df[date_column] = pd.to_datetime(df[date_column])
    df['year'] = df[date_column].dt.year
    df['year'] = df['year'].clip(lower=2012, upper=2023)
    df['FIPS'] = df['FIPS'].apply(lambda x: str(x).split('.')[0])

    DATABASE_URL = "postgresql:"
    engine = create_engine(DATABASE_URL)

    all_data_frames = []
    all_index_data_frames = []  # List to store data from all index tables

    for year, group_df in df.groupby('year'):
        fips_list = ', '.join(f"'{fip}'" for fip in group_df['FIPS'].unique())
        fips_condition = f"geocode IN ({fips_list})"
        
        logging.debug(f"Year: {year}, FIPS condition: {fips_condition}")

        data_source_query = f"""
        SELECT variables_index_name
        FROM data.data_source 
        WHERE EXTRACT(YEAR FROM effective_start_timestamp) <= {year}
          AND EXTRACT(YEAR FROM effective_end_timestamp) >= {year}
          AND boundary_type='Census tract'
          AND geometry_y_n='0';
        """
        logging.debug(f"Data source query: {data_source_query}")

        variables_index_df = pd.read_sql(data_source_query, engine)
        
        if variables_index_df.empty:
            logging.warning(f"No data found in data source for year {year}. Exiting function.")
            continue
        
        # Get all the index information for variables
        for _, v_row in variables_index_df.iterrows():
            index_table_name = v_row['variables_index_name']
            index_table_query = f"""
            SELECT *
            FROM data.\"{index_table_name}\"
            """
            logging.debug(f"Variable table query: {index_table_query}")

            index_table_df = pd.read_sql(index_table_query, engine)
            logging.info(f"Data from {index_table_name} retrieved")

            if index_table_df.empty:
                logging.warning(f"No data returned for {index_table_name}. Skipping...")
                continue

            # Add a column to identify the source table
            index_table_df['source_table'] = index_table_name

            # Append the data to the list of DataFrames
            all_index_data_frames.append(index_table_df)
            logging.info(f"Data from {index_table_name} appended successfully")

        for _, v_row in variables_index_df.iterrows():
            variable_table_name = v_row['variables_index_name'][:-6] + '_variables'
            variable_table_query = f"""
            SELECT *
            FROM data.\"{variable_table_name}\"
            WHERE {fips_condition}
            """
            # logging.debug(f"Variable table query: {variable_table_query}")

            variable_table_df = pd.read_sql(variable_table_query, engine)
            

            if variable_table_df.empty:
                logging.warning(f"No data returned for {variable_table_name}. Skipping...")
                continue

            variable_table_df['effective_start_timestamp'] = pd.to_datetime(variable_table_df['effective_start_timestamp'])
            variable_table_df['effective_end_timestamp'] = pd.to_datetime(variable_table_df['effective_end_timestamp'])

            filtered_df = variable_table_df[(variable_table_df['geocode'].isin(group_df['FIPS'])) &
                                            (variable_table_df['effective_start_timestamp'] <= group_df[date_column].max()) &
                                            (variable_table_df['effective_end_timestamp'] >= group_df[date_column].min())]

            if not filtered_df.empty:
                group_df = pd.merge(group_df, filtered_df, left_on='FIPS', right_on='geocode', how='left')
                group_df.drop(columns=['geocode', 'effective_start_timestamp', 'effective_end_timestamp'], inplace=True)

        all_data_frames.append(group_df)
    
    # Combine all the DataFrames from the index tables
    if all_index_data_frames:
        combined_index_df = pd.concat(all_index_data_frames, ignore_index=True, sort=False)
        # Drop duplicate rows
        combined_index_df.drop_duplicates(inplace=True)
        # Ensure directory exists and save the CSV
        os.makedirs('./Linkage_result', exist_ok=True)
        Index_file = './Linkage_result/Index_data.csv'
        combined_index_df.to_csv(Index_file, index=False)
        print(f'{Index_file} written successfully.')

    final_df = pd.concat(all_data_frames, ignore_index=True, sort=False)
#     output_file = './Linkage_result/SDoH_linkage_Degauss_full.csv'
    
    final_df.rename(columns={
        'lat': 'latitude',
        'lon': 'longitude'}, inplace=True)
    final_df.to_csv(output_file_path, index=False)
    print(f'Output file saved successfully: {output_file_path}')

    engine.dispose()
    

    
def process_directory(directory):
    # Set base configurations
    output_base = './Linkage_result'
    os.makedirs(output_base, exist_ok=True)
    threshold = 0.7
    columns = ['address_1', 'city', 'state', 'zip']
    date_column = 'visit_start_date'
    default_index_file = './Linkage_result/Index_data.csv'
    
    # Determine the type of processing based on the directory name
    if 'valid_address' in directory:
        process_type = 'address'
    elif 'valid_lat_long' in directory:
        process_type = 'latlong'
    elif 'invalid_lat_lon_address' in directory:
        process_type = 'invalid'
    else:
        print("Unknown directory type. Please check the directory path.")
        return
    
    output_dir = os.path.join(output_base, process_type)
    os.makedirs(output_dir, exist_ok=True)
    print(process_type)
    # Set base configurations
    for idx, filename in enumerate(sorted(os.listdir(directory))):
        filepath = os.path.join(directory, filename)
        print(f"Processing file: {filepath}")
#         df = pd.read_csv(filepath)
#             output_dir = os.path.join(output_base, process_type)
#             os.makedirs(output_dir, exist_ok=True)

        if process_type == 'invalid':
                # Simply copy files to the new directory
            final_output = os.path.join(output_dir, f'{process_type}_no_linkage_{idx+1}.csv')
            shutil.copy(filepath, final_output)
            print(f"Invalid file to {final_output}")
#             continue
            
            
        if process_type == 'address':
            final_output = os.path.join(output_dir, f'{process_type}_linkaged_SDoH_{idx+1}.csv')
            # Process starting from geocoding
            df = pd.read_csv(filepath)
                
             # Generate coordinates and process geocoded data
            geocoded_file = generate_coordinates_degauss(df, columns, 0.7)
                
            if geocoded_file:
                df = pd.read_csv(geocoded_file)
                df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
                   # Map year based on date_column and clip to either 2010 or 2020
                df['year'] = df[date_column].dt.year.apply(lambda x: 2010 if x < 2020 else 2020)
                df.drop(columns=['address', 'latitude', 'longitude', 'matched_street', 'matched_zip', 'matched_city', 'matched_state', 'score', 'precision', 'geocode_result'], inplace=True)
                
                # Now, process only for the two distinct mapped years
            for year in [2010, 2020]:
                generate_fips_degauss(df, year)
                
#                     # Load both FIPS files if available
            fips_file_2010 = "preprocessed_2_census_block_group_0.6.0_2010.csv"
            fips_file_2020 = "preprocessed_2_census_block_group_0.6.0_2020.csv"
    
            if os.path.exists(fips_file_2010) and os.path.exists(fips_file_2020):
                fips_df_2010 = pd.read_csv(fips_file_2010)
                fips_df_2020 = pd.read_csv(fips_file_2020)
                    
                fips_df_2010[date_column] = pd.to_datetime(fips_df_2010[date_column], errors='coerce')
                fips_df_2020[date_column] = pd.to_datetime(fips_df_2020[date_column], errors='coerce')
                    
                fips_df_2010 = fips_df_2010[fips_df_2010[date_column].dt.year < 2020]
                fips_df_2020 = fips_df_2020[fips_df_2020[date_column].dt.year >= 2020]

                print("Rows after filtering 2010:", len(fips_df_2010))
                print("Rows after filtering 2020:", len(fips_df_2020))

                all_fips_df = pd.concat([fips_df_2010, fips_df_2020], ignore_index=True)
                print("Combined rows count:", len(all_fips_df))
                final_output = os.path.join(output_dir, f'Address_linkaged_SDoH_{idx+1}.csv')
                sdoh_linkage(all_fips_df, date_column, final_output)
                new_index_file = os.path.join(output_dir, f'index_data_{os.path.basename(directory)}_{idx+1}.csv')
                if os.path.exists(default_index_file):
                    os.rename(default_index_file, new_index_file)
                    print(f"Index file renamed to {new_index_file}")
            print("Address processing to be implemented.")
                
                
                
        elif process_type == 'latlong':
                # Process starting from FIPS generation
             final_output = os.path.join(output_dir, f'{process_type}_linkaged_SDoH_{idx+1}.csv')
             df = pd.read_csv(filepath)
                
             df.rename(columns={'latitude': 'lat', 'longitude': 'lon'}, inplace=True)
             df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
               # Map year based on date_column and clip to either 2010 or 2020
             df['year'] = df[date_column].dt.year.apply(lambda x: 2010 if x < 2020 else 2020)
             for year in [2010, 2020]:
                 fips_file = generate_fips_degauss(df, year)
                    
#                  # Load both FIPS files if available
             fips_file_2010 = "preprocessed_2_census_block_group_0.6.0_2010.csv"
             fips_file_2020 = "preprocessed_2_census_block_group_0.6.0_2020.csv"
    
             if os.path.exists(fips_file_2010) and os.path.exists(fips_file_2020):
                 fips_df_2010 = pd.read_csv(fips_file_2010)
                 fips_df_2020 = pd.read_csv(fips_file_2020)
                    
                 fips_df_2010[date_column] = pd.to_datetime(fips_df_2010[date_column], errors='coerce')
                 fips_df_2020[date_column] = pd.to_datetime(fips_df_2020[date_column], errors='coerce')
                    
                 fips_df_2010 = fips_df_2010[fips_df_2010[date_column].dt.year < 2020]
                 fips_df_2020 = fips_df_2020[fips_df_2020[date_column].dt.year >= 2020]

                 print("Rows after filtering 2010:", len(fips_df_2010))
                 print("Rows after filtering 2020:", len(fips_df_2020))

                 all_fips_df = pd.concat([fips_df_2010, fips_df_2020], ignore_index=True)
                 print("Combined rows count:", len(all_fips_df))
                 final_output = os.path.join(output_dir, f'Latlong_linkaged_SDoH_{idx+1}.csv')
                 sdoh_linkage(all_fips_df, date_column, final_output)
                 new_index_file = os.path.join(output_dir, f'index_data_{os.path.basename(directory)}_{idx+1}.csv')
                 if os.path.exists(default_index_file):
                     os.rename(default_index_file, new_index_file)
                     print(f"Index file renamed to {new_index_file}")
               

            
        
def main():
    parser = argparse.ArgumentParser(description="Export data from SQL Server to CSV files.")
    parser.add_argument('--user', required=True, help='Database username')
    parser.add_argument('--password', required=True, help='Database password')
    parser.add_argument('--server', required=True, help='Database server')
    parser.add_argument('--port', required=True, help='Database port')
    parser.add_argument('--database', required=True, help='Database name')
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Call the function with parsed arguments
    omop_extraction(args.user, args.password, args.server, args.port, args.database)
    
    process_directory('./Linkage_data/invalid_lat_lon_address')
    process_directory('./Linkage_data/valid_address')
    process_directory('./Linkage_data/valid_lat_long')



if __name__ == "__main__":
    main()
                











