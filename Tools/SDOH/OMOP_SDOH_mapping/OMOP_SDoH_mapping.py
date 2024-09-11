import pyodbc
import pandas as pd
import os
import subprocess
import sys
import argparse
import logging
from sqlalchemy import create_engine

def omop_extraction(user, password, server, port, database):
    # Connection string
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server},{port};DATABASE={database};UID={user};PWD={password}'

    # Connect to the database
    try:
        conn = pyodbc.connect(conn_str)
        print("Connection established successfully!")
    except Exception as e:
        print("Error:", e)
        return

    # Directory for CSV files
    csv_directory = './Linkage_data'

    # Create the directory if it doesn't exist
    if not os.path.exists(csv_directory):
        os.makedirs(csv_directory)

    # Define the SQL query with pagination
    sql_query_template = """
    WITH patient AS (
        SELECT p.person_id, v.visit_occurrence_id, v.visit_start_date, v.visit_end_date
        FROM IC3_INPATIENT_PIPELINE_2024.CDM.PERSON p
        LEFT JOIN IC3_INPATIENT_PIPELINE_2024.CDM.VISIT_OCCURRENCE v ON p.person_id=v.person_id),

    address AS (
    SELECT entity_id, L.location_id, L.address_1, L.city, L.state, L.zip, L.county, L.latitude, L.longitude, L.FIPS, LS.start_date, LS.end_date
    FROM LOCATION L LEFT JOIN LOCATION_HISTORY LS ON L.location_id = LS.location_id)

    select person_id, visit_occurrence_id, visit_start_date, visit_end_date, address_1, city, state, zip, county, latitude, longitude
    from patient p left join address a on p.person_id = a.entity_id
    where p.visit_start_date between a.start_date and a.end_date
    and p.visit_end_date between a.start_date and a.end_date
    and visit_start_date >= '2012-01-01'
    order by person_id, visit_start_date
    OFFSET {offset} ROWS FETCH NEXT {fetch} ROWS ONLY;
    """

    # Number of rows to fetch per batch
    fetch_size = 100000
    # Initialize offset
    offset = 0
    # Counter for CSV files
    file_counter = 1

    # Loop through the data in batches and export to CSV
    while True:
        # Execute the SQL query for the current batch
        sql_query = sql_query_template.format(offset=offset, fetch=fetch_size)
        df = pd.read_sql(sql_query, conn)

        # Check if the DataFrame is empty (no more data to fetch)
        if df.empty:
            break

        # Define filename for CSV
        filename = os.path.join(csv_directory, f'data_{file_counter}.csv')

        # Export DataFrame to CSV
        df.to_csv(filename, index=False)

        print(f"Batch {file_counter} exported to CSV: {filename}")
        
        # Stop after exporting the first file
        if file_counter == 1:
            break

        # Increment file counter
        file_counter += 1

        # Update offset for the next batch
        offset += fetch_size

    # Close the connection
    conn.close()
    print("Connection closed.")

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
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(output_file_name)

    # Save the DataFrame back to CSV if needed
    df.to_csv(output_file_name, index=False)
    return output_file_name

def generate_fips_degauss(df, year):
    print('Generating FIPS...')
    # Map the year to the nearest supported year
#     if year < 2020:
#         year = 2010
#     else:
#         year = 2020
    

#     # Define a function to check for missing or invalid values
#     def is_invalid(value):
#         # Example of identifying multiple "missing" values
#         missing_values = [pd.NA, None, 'NA', 'null', 'Null', '', ' ']
#         return pd.isna(value) or str(value).strip() in missing_values

#     # Update 'lat' and 'lon' based on 'latitude' and 'longitude'
#     df['lat'] = df.apply(lambda row: row['latitude'] if is_invalid(row['lat']) else row['lat'], axis=1)
#     df['lon'] = df.apply(lambda row: row['longitude'] if is_invalid(row['lon']) else row['lon'], axis=1)
       # You can use 'fillna' to fill 'lat' and 'lon' from 'latitude' and 'longitude'
#     df['lat'] = df['lat'].fillna(df['latitude'])
#     df['lon'] = df['lon'].fillna(df['longitude'])

# #     Optionally drop the 'latitude' and 'longitude' columns if they are no longer needed
#     df.drop(['latitude', 'longitude'], axis=1, inplace=True)
    
    
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
def sdoh_linkage(df, date_column):
    df[date_column] = pd.to_datetime(df[date_column])
    df['year'] = df[date_column].dt.year
    df['year'] = df['year'].clip(lower=2012, upper=2023)
    df['FIPS'] = df['FIPS'].apply(lambda x: str(x).split('.')[0])

    DATABASE_URL = ""
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
    output_file = './Linkage_result/SDoH_linkage_Degauss_full.csv'
    
    final_df.rename(columns={
        'lat': 'latitude',
        'lon': 'longitude'}, inplace=True)
    
    final_df.to_csv(output_file, index=False)
    print(f'{output_file} written successfully.')

    engine.dispose()
    

def process_directory(directory):
    # Files are processed here
    filepath = './Linkage_data'
    threshold = 0.7
    columns = ['address_1', 'city', 'state', 'zip']
    date_column = 'visit_start_date'
    

    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            filepath = os.path.join(directory, filename)
            print(f"Processing file: {filepath}")
            
            df = pd.read_csv(filepath)
            
            geocoded_lat_lon = generate_coordinates_degauss(df, columns, threshold)
            if geocoded_lat_lon:
                df = pd.read_csv(geocoded_lat_lon)
                df['lat'] = df['lat'].fillna(df['latitude'])
                df['lon'] = df['lon'].fillna(df['longitude'])
                df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
               # Map year based on date_column and clip to either 2010 or 2020
                df['year'] = df[date_column].dt.year.apply(lambda x: 2010 if x < 2020 else 2020)
                df.drop(columns=['address', 'latitude', 'longitude', 'matched_street', 'matched_zip', 'matched_city', 'matched_state', 'score', 'precision', 'geocode_result'], inplace=True)
        
        # Now, process only for the two distinct mapped years
        for year in [2010, 2020]:
#             year_df = combined_df[combined_df[date_column].dt.year <= year]
            generate_fips_degauss(df, year)
                
            # Load both FIPS files if available
        fips_file_2010 = "preprocessed_2_census_block_group_0.6.0_2010.csv"
        fips_file_2020 = "preprocessed_2_census_block_group_0.6.0_2020.csv"
    
        if os.path.exists(fips_file_2010) and os.path.exists(fips_file_2020):
            fips_df_2010 = pd.read_csv(fips_file_2010)
            fips_df_2020 = pd.read_csv(fips_file_2020)
                   
            fips_df_2010[date_column] = pd.to_datetime(fips_df_2010[date_column], errors='coerce')
            fips_df_2020[date_column] = pd.to_datetime(fips_df_2020[date_column], errors='coerce')

            print("Years in 2010 file:", fips_df_2010[date_column].dt.year.unique())
            print("Years in 2020 file:", fips_df_2020[date_column].dt.year.unique())

            fips_df_2010 = fips_df_2010[fips_df_2010[date_column].dt.year < 2020]
            fips_df_2020 = fips_df_2020[fips_df_2020[date_column].dt.year >= 2020]

            print("Rows after filtering 2010:", len(fips_df_2010))
            print("Rows after filtering 2020:", len(fips_df_2020))

            all_fips_df = pd.concat([fips_df_2010, fips_df_2020], ignore_index=True)
            print("Combined rows count:", len(all_fips_df))
            sdoh_linkage(all_fips_df, date_column)
        else:
            print("Error: Required FIPS files are missing.")
    


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
    
    # Now process the directory with the CSV files
    process_directory('./Linkage_data')

if __name__ == "__main__":
    main()

