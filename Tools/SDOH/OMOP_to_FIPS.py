import pyodbc
import pandas as pd
import os
import shutil
import subprocess
import sys
import argparse
from loguru import logger
from sqlalchemy import create_engine
from concurrent.futures import ThreadPoolExecutor, as_completed
import zipfile

logger.add(sys.stderr, format="{time} {level} {message}", filter="my_module", level="INFO")

#extract required info from OMOP database
def omop_extraction(user, password, server, port, database):
    """
    Executes three SQL queries in parallel to categorize data based on the validity of latitude, longitude, and address_1.
    Each query's results are saved in different directories in batches of 100000 rows per CSV.
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
                SELECT entity_id, L.location_id, L.address_1, L.city, L.state, L.zip, L.latitude, L.longitude, L.FIPS, LS.start_date, LS.end_date
                FROM LOCATION L LEFT JOIN LOCATION_HISTORY LS ON L.location_id = LS.location_id)
            SELECT person_id, visit_occurrence_id, visit_start_date, visit_end_date, address_1, city, state, zip, latitude, longitude
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
                SELECT entity_id, L.location_id, L.address_1, L.city, L.state, L.zip, L.latitude, L.longitude, L.FIPS, LS.start_date, LS.end_date
                FROM LOCATION L LEFT JOIN LOCATION_HISTORY LS ON L.location_id = LS.location_id)
            SELECT person_id, visit_occurrence_id, visit_start_date, visit_end_date, address_1, city, state, zip, latitude, longitude
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
                SELECT entity_id, L.location_id, L.address_1, L.city, L.state, L.zip, L.latitude, L.longitude, L.FIPS, LS.start_date, LS.end_date
                FROM LOCATION L LEFT JOIN LOCATION_HISTORY LS ON L.location_id = LS.location_id)
            SELECT person_id, visit_occurrence_id, visit_start_date, visit_end_date, address_1, city, state, zip, latitude, longitude
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

#Generate latitude and longitude from address infomation

def generate_coordinates_degauss(df, columns, threshold, output_folder):
    """
    Preprocess address data, execute a Docker-based geocoding tool, and retrieve geolocation data using Degauss.
    
    Parameters:
    df (pandas.DataFrame): DataFrame containing address data
    columns (list of str): List of column names representing address information
    threshold (float): Threshold for the geocoder's score (accuracy)
    save_intermediate (bool): Whether to save the intermediate preprocessed CSV before geocoding (default is False)
    
    Returns:
    str: Name of the geocoded CSV file generated by the Docker container
    """
    
     # Convert columns to string type
    for col in columns:
        df[col] = df[col].astype(str)
    for col in columns:
         # If this is the Zip column, ensure no '.0' remains
        if col.lower() == 'zip':
            df[col] = df[col].apply(lambda x: x.split('.')[0] if '.' in x else x)
    
    # Handle single column or concatenate multiple columns
    if len(columns) == 1:
        df['address'] = df[columns[0]].str.title().replace(r'[^a-zA-Z0-9 ]', ' ', regex=True)
    else:
        df['address'] = df.apply(lambda row: ' '.join(row[columns]).lower(), axis=1)
        df['address'] = df['address'].str.title()
        df['address'] = df['address'].replace(r'[^a-zA-Z0-9 ]', ' ', regex=True)
    
    # Drop original address columns if they are no longer needed
    if len(columns) > 1:
        df.drop(columns=columns, inplace=True)

    columns_to_drop = {'latitude', 'longitude'}
    df.drop(columns=columns_to_drop, inplace=True)
    
    # Save the preprocessed DataFrame to CSV
    preprocessed_file_path = os.path.join(output_folder, 'preprocessed_1.csv')
    df.to_csv(preprocessed_file_path, index=False)

    # Convert the folder and file paths to absolute paths for Docker
    abs_output_folder = os.path.abspath(output_folder)  # Convert to absolute path
    abs_preprocessed_file = os.path.abspath(preprocessed_file_path)  # Convert to absolute path

    # Quote the paths to handle spaces
    quoted_output_folder = f'"{abs_output_folder}"'
    quoted_preprocessed_file = f'"{abs_preprocessed_file}"'
    
   # Define the Docker command
    docker_command = [
        'docker', 'run', '--rm',
        '-v', f'{quoted_output_folder}:/tmp',
        'ghcr.io/degauss-org/geocoder:3.3.0',
       f'/tmp/{os.path.basename(abs_preprocessed_file)}',
        str(threshold)
    ]
    
    try:
        # Execute Docker command to run the geocoder
        result = subprocess.run(' '.join(docker_command), shell=True, check=True, capture_output=True, text=True)
        print("Docker command executed successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing Docker command: {e}")
        print(e.stderr)

    # Define the output file name from the geocoder
    output_file_name = os.path.join(output_folder, f"preprocessed_1_geocoder_3.3.0_score_threshold_{threshold}.csv")
    return os.path.abspath(output_file_name)

#Generate the FIPS code from latitude and longitude
def generate_fips_degauss(df, year, output_folder):
    """
    Generates FIPS codes from latitude and longitude using a Docker-based geocoding service.

    This function saves the provided DataFrame to a CSV file, runs a Docker container to process this file
    and generate FIPS codes, and then updates the DataFrame with the FIPS codes before saving the final output.

    Parameters:
    df (pd.DataFrame): The input DataFrame containing latitude and longitude data.
    year (int): The year to be used for different FIPS code version.

    Returns:
    str or None: The path to the output file if successful, None otherwise.
    """
    
    logger.info("Generating FIPS...")

     # Convert the folder and file paths to absolute paths
    abs_output_folder = os.path.abspath(output_folder)  # Convert to absolute path
    
    # Normalize the paths to Unix-style for Docker (replace backslashes with forward slashes)
    abs_output_folder = abs_output_folder.replace("\\", "/")
    
    preprocessed_file_path = os.path.join(output_folder, 'preprocessed_2.csv')
    # Columns that may exist and need to be dropped
    columns_to_drop = {'matched_street', 'matched_zip', 'matched_city', 'matched_state', 'score', 'precision', 'geocode_result'}
    # Drop only the columns that exist in the DataFrame
    columns_in_df = set(df.columns)  # Get the columns that exist in the DataFrame
    columns_to_drop = columns_to_drop.intersection(columns_in_df)  # Find intersection of existing columns and columns to drop
    
    if columns_to_drop:  # Only drop if there are columns to drop
        df.drop(columns=columns_to_drop, inplace=True)
        
    df.to_csv(preprocessed_file_path, index=False)

    # Also normalize the preprocessed file path
    abs_preprocessed_file = os.path.abspath(preprocessed_file_path).replace("\\", "/")
    
    output_file = os.path.join(output_folder, f"preprocessed_2_census_block_group_0.6.0_{year}.csv")    
#     output_file = f"{df.replace('.csv', '')}_census_block_group_0.6.0_{year}.csv"
    docker_command2 = ["docker", "run", "--rm", "-v", f'{abs_output_folder}:/tmp', "ghcr.io/degauss-org/census_block_group:0.6.0", f'/tmp/{os.path.basename(abs_preprocessed_file)}', str(year)]
    try:
        result = subprocess.run(docker_command2, check=True, capture_output=True, text=True)
        logger.info("Docker command executed successfully.")
        logger.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing Docker command 2: {e}")
        logger.error(e.stderr)
        return None

    # Define the output file name
    output_file = os.path.join(output_folder, f"preprocessed_2_census_block_group_0.6.0_{year}.csv")
    output_file = os.path.abspath(output_file).replace("\\", "/")

    if os.path.exists(output_file):
        logger.info(f"Output file generated: {output_file}")
        df = pd.read_csv(output_file)
        df['FIPS'] = df[f'census_tract_id_{year}']
        df.drop(columns=[f'census_block_group_id_{year}', f'census_tract_id_{year}'], inplace=True)
        df.to_csv(output_file, index=False)
        return output_file
    else:
        logger.error(f"Expected output file not found: {output_file}")
        return None

#This fuction deal with different year of FIPS 
def process_fips_generation(df, output_folder, base_filename):
    # Process FIPS generation for 2010 and 2020
    has_2010 = (df['year_for_fips'] == 2010).any()
    has_2020 = (df['year_for_fips'] == 2020).any()

    generated_fips_files = []  # List to store the paths of generated FIPS files

    # Generate FIPS codes based on available years
    if has_2010 and has_2020:
        for Year in [2010, 2020]:
            year_df = df[df['year_for_fips'] == Year]
            generate_fips_degauss(year_df, Year, output_folder)

    elif has_2010:
        year_df_2010 = df[df['year_for_fips'] == 2010]
        generate_fips_degauss(year_df_2010, 2010, output_folder)

    elif has_2020:
        year_df_2020 = df[df['year_for_fips'] == 2020]
        generate_fips_degauss(year_df_2020, 2020, output_folder)

    else:
        logger.warning("No data available for 2010 or 2020.")

    encounter_with_fips_file = os.path.join(output_folder, f"{base_filename}_with_fips.csv")
    # Final output CSV file
    fips_file_2010 = os.path.join(output_folder, "preprocessed_2_census_block_group_0.6.0_2010.csv")
    fips_file_2020 = os.path.join(output_folder, "preprocessed_2_census_block_group_0.6.0_2020.csv")
    # base_filename = os.path.splitext(df['file'][0])[0]  # Assuming df has the file column containing filename


    if os.path.exists(fips_file_2010) and os.path.exists(fips_file_2020):
        fips_df_2010 = pd.read_csv(fips_file_2010)
        fips_df_2020 = pd.read_csv(fips_file_2020)
        all_fips_df = pd.concat([fips_df_2010, fips_df_2020], ignore_index=True)
        all_fips_df.drop(columns=['year_for_fips'], inplace=True)
        all_fips_df.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
        all_fips_df.to_csv(encounter_with_fips_file, index=False)
        logger.info(f"Encounter with FIPS file generated: {encounter_with_fips_file}")
        generated_fips_files.append(encounter_with_fips_file)  # Add to list

    elif os.path.exists(fips_file_2010):
        fips_df_2010 = pd.read_csv(fips_file_2010)
        fips_df_2010.drop(columns=['year_for_fips'], inplace=True)
        fips_df_2010.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
        fips_df_2010.to_csv(encounter_with_fips_file, index=False)
        logger.info(f"FIPS file generated for 2010 with {len(fips_df_2010)} rows: {encounter_with_fips_file}")
        generated_fips_files.append(encounter_with_fips_file)  # Add to list

    elif os.path.exists(fips_file_2020):
        fips_df_2020 = pd.read_csv(fips_file_2020)
        fips_df_2020.drop(columns=['year_for_fips'], inplace=True)
        fips_df_2020.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
        fips_df_2020.to_csv(encounter_with_fips_file, index=False)
        logger.info(f"FIPS file generated for 2020 with {len(fips_df_2020)} rows: {encounter_with_fips_file}")
        generated_fips_files.append(encounter_with_fips_file)  # Add to list

    else:
        logger.error("Error: Neither FIPS file exists.")
    # Return the generated FIPS file paths   
    return generated_fips_files

#This function run three parts of category 
def process_single_file(filepath, process_type, columns, threshold, date_column, output_dir, final_coordinate_files, final_fips_files):
    base_filename = os.path.splitext(os.path.basename(filepath))[0]
    logger.info(f"Processing file: {filepath}")

    if process_type == 'invalid':
        # Simply copy files to the new directory
        final_output = os.path.join(output_dir, f'{base_filename}_invalid.csv')
        shutil.copy(filepath, final_output)
        
        logger.info(f"Invalid file copied to {final_output}")
        logger.info("Due to the missing address and latitude and longitude, Files in invalid folder cannot link with SDoH database")
        return None

    # Create a unique folder for each CSV file based on its name
    csv_output_dir = os.path.join(output_dir, base_filename)
    os.makedirs(csv_output_dir, exist_ok=True)

    geocoded_file = None

    if process_type == 'address':
        df = pd.read_csv(filepath)
        geocoded_file = generate_coordinates_degauss(df, columns, threshold, csv_output_dir)
        
        #get the coordinates files
        latlon = pd.read_csv(geocoded_file)
        columns_to_drop = ['matched_street', 'matched_zip', 'matched_city', 'matched_state', 'score', 'precision', 'geocode_result']
        latlon.drop(columns=[col for col in columns_to_drop if col in latlon.columns], inplace=True)
        latlon.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
        
        output_file = os.path.join(csv_output_dir, f"{base_filename}_with_coordinates.csv")
        latlon.to_csv(output_file, index=False)
        logger.info(f"Coordinates file generated: {output_file}")
        # Add coordinate file to the final_coordinate_files list
        final_coordinate_files.append(output_file)
        
    elif process_type == 'latlong':
        df = pd.read_csv(filepath)
        # Assume latlong processing includes geocoding as well
        geocoded_file = filepath  # For simplicity

    # Process FIPS generation for valid data
    if geocoded_file:
        df = pd.read_csv(geocoded_file)
        # Check if 'latitude' and 'longitude' columns exist and rename them to 'lat' and 'lon'
        if 'latitude' in df.columns and 'longitude' in df.columns:
            df.rename(columns={'latitude': 'lat', 'longitude': 'lon'}, inplace=True)
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        df['year_for_fips'] = df[date_column].dt.year.apply(lambda x: 2010 if x < 2020 else 2020)
        
        # Process FIPS generation and save the FIPS file
        fips_files = process_fips_generation(df, csv_output_dir, base_filename)
        
         # Ensure FIPS files are correctly added to the list
        if fips_files:
            final_fips_files.extend(fips_files)
            logger.info(f"FIPS files generated for {base_filename}: {fips_files}")
        else:
            logger.warning(f"No FIPS files generated for {base_filename}")

#This function deal with the file in parallel and compress into a ZIP files
def process_directory(directory):
    # Set base configurations
    output_base = './Linkage_result'
    os.makedirs(output_base, exist_ok=True)
    threshold = 0.7
    columns = ['address_1', 'city', 'state', 'zip']
    date_column = 'visit_start_date'
    
    # Determine the type of processing based on the directory name
    if 'valid_address' in directory:
        process_type = 'address'
    elif 'valid_lat_long' in directory:
        process_type = 'latlong'
    elif 'invalid_lat_lon_address' in directory:
        process_type = 'invalid'
    else:
        logger.info("Unknown directory type. Please check the directory path.")
        return
    
    output_dir = os.path.join(output_base, process_type)
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Starting processing for {process_type}")

    # Get list of files in the directory
    files = sorted(os.listdir(directory))
    final_coordinate_files = []
    final_fips_files = []

    # Set the maximum number of files to process concurrently
    max_workers = 2

    # Parallel processing using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for filename in files:
            filepath = os.path.join(directory, filename)
            futures.append(executor.submit(process_single_file, filepath, process_type, columns, threshold, date_column, output_dir, final_coordinate_files, final_fips_files))
        
        # Process results as they are completed
        for future in as_completed(futures):
            try:
                future.result()  # Get the resulting coordinate file
            except Exception as e:
                logger.error(f"Error processing file: {e}")

    # After processing all files, create the zip archive for the address/latlong coordinates
    if final_coordinate_files:
        zip_file_path = os.path.join(output_dir, f'{process_type}_with_coordinates.zip')
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            for file in final_coordinate_files:
                zipf.write(file, arcname=os.path.basename(file))  # Add file to zip
        logger.info(f"Coordinates zip file created: {zip_file_path}")

    # After processing all files, create the zip archive for the address/latlong FIPS files
    if final_fips_files:
        zip_file_path_fips = os.path.join(output_dir, f'{process_type}_with_fips.zip')
        with zipfile.ZipFile(zip_file_path_fips, 'w') as zipf:
            for file in final_fips_files:
                zipf.write(file, arcname=os.path.basename(file))  # Add file to zip
        logger.info(f"FIPS zip file created: {zip_file_path_fips}")

    logger.info(f"Completed processing for {process_type}")

    # Now delete all the subdirectories and files except for the zip files
    for root, dirs, files in os.walk(output_dir):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            shutil.rmtree(dir_path)
            logger.info(f"Deleted directory: {dir_path}")
          
        
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
