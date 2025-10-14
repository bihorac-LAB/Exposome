import pandas as pd
import os
import shutil
import subprocess
import sys
import argparse
from loguru import logger
from sqlalchemy import create_engine
import concurrent
from concurrent.futures import ThreadPoolExecutor, as_completed
import zipfile
from datetime import datetime


# -------------------------------------------------------------------
# A quick-lookup set of FULL normalized hospital addresses.
# Add / update as needed.  All entries must be lower-case and trimmed.
HOSPITAL_ADDRESSES = {
    "1000 peachtree park dr ne atlanta ga 30309",
    "240 nw 25th st miami fl 33127",
    "1400 briarcliff rd ne atlanta ga 30306",
    # …extend the list …
}
# -------------------------------------------------------------------

# Set the base directory for output, parallel to the code folder
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
host_base = os.environ["HOST_PWD"] 
#base_output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), f'../output_{timestamp}'))
base_output_dir = os.path.abspath(f'output_{timestamp}')
linkage_data_dir = os.path.join(base_output_dir, 'OMOP_data')
linkage_result_dir = os.path.join(base_output_dir, 'OMOP_FIPS_result')


# Create the Linkage_result directory if it doesn't exist
os.makedirs(linkage_result_dir, exist_ok=True)

# Create a timestamped log filename
log_filename = f"OMOP_to_FIPS_{timestamp}.log"
log_file_path = os.path.join(linkage_result_dir, log_filename)
# Set up the logger to write to the log file
logger.add(log_file_path, format="{time} {level} {message}", level="INFO")
logger.info(f"Logging started. Log file created at: {log_file_path}")

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
        - './OMOP_data/valid_lat_long'
        - './OMOP_data/invalid_lat_lon_address'
        - './OMOP_data/valid_address'
    """

    # Fetch credentials from environment variables
    conn_str = f"mssql+pyodbc://{user}:{password}@{server}:{port}/{database}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes"
    print(conn_str)
    engine = create_engine(conn_str)
    # base_directory = './Linkage_data'
    categories = {
        'Latlong': 'valid_lat_long',
        'Invalid': 'invalid_lat_lon_address',
        'Address': 'valid_address'
    }

    # Create directories
    for category in categories.values():
        os.makedirs(os.path.join(linkage_data_dir, category), exist_ok=True)

    # SQL Queries for each category
    queries = {
        'Latlong': """
            WITH patient AS (
                SELECT p.person_id, v.visit_occurrence_id, v.visit_start_date, v.visit_end_date
                FROM CDM.PERSON p
                LEFT JOIN CDM.VISIT_OCCURRENCE v ON p.person_id = v.person_id),
            address AS (
                SELECT entity_id, L.location_id, L.address_1, L.address_2, L.city, L.state, L.zip, L.county, L.location_source_value, L.country_concept_id, L.country_source_value, L.latitude, L.longitude, LS.start_date, LS.end_date
                FROM CDM.LOCATION L LEFT JOIN CDM.LOCATION_HISTORY LS ON L.location_id = LS.location_id)
            SELECT person_id, visit_occurrence_id, year(visit_start_date) as year, address.location_id, address.address_1, address.address_2, address.city, address.state, address.zip, address.county, address.location_source_value, address.country_concept_id, address.country_source_value, address.latitude, address.longitude
            FROM patient p
            LEFT JOIN address ON p.person_id = address.entity_id
            WHERE p.visit_start_date BETWEEN address.start_date AND address.end_date
              AND p.visit_end_date BETWEEN address.start_date AND address.end_date
              AND visit_start_date >= '2012-01-01'
              AND NOT (LTRIM(RTRIM(ISNULL(address.latitude, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))
              AND NOT (LTRIM(RTRIM(ISNULL(address.longitude, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))""",
        
        'Invalid': """
            WITH patient AS (
                SELECT p.person_id, v.visit_occurrence_id, YEAR(v.visit_start_date) AS year
                FROM CDM.PERSON p
                LEFT JOIN CDM.VISIT_OCCURRENCE v ON p.person_id = v.person_id),
            address AS (
                SELECT entity_id, L.location_id, L.address_1, L.address_2, L.city, L.state, L.zip, L.county, L.location_source_value, L.country_concept_id, L.country_source_value, L.latitude, L.longitude, LS.start_date, LS.end_date
                FROM CDM.LOCATION L LEFT JOIN CDM.LOCATION_HISTORY LS ON L.location_id = LS.location_id)
            SELECT person_id, visit_occurrence_id, year(visit_start_date) as year, address.location_id, address.address_1, address.address_2, address.city, address.state, address.zip, address.county, address.location_source_value, address.country_concept_id, address.country_source_value, address.latitude, address.longitude
            FROM patient p
            LEFT JOIN address ON p.person_id = address.entity_id
            WHERE p.visit_start_date BETWEEN address.start_date AND address.end_date
              AND p.visit_end_date BETWEEN address.start_date AND address.end_date
              AND visit_start_date >= '2012-01-01'
              AND (LTRIM(RTRIM(ISNULL(address.latitude, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))
              AND (LTRIM(RTRIM(ISNULL(address.longitude, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))
              AND (LTRIM(RTRIM(ISNULL(address.address_1, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))""",

        'Address': """
            WITH patient AS (
                SELECT p.person_id, v.visit_occurrence_id, YEAR(v.visit_start_date) AS year
                FROM CDM.PERSON p
                LEFT JOIN CDM.VISIT_OCCURRENCE v ON p.person_id = v.person_id),
            address AS (
                SELECT entity_id, L.location_id, L.address_1, L.address_2, L.city, L.state, L.zip, L.county, L.location_source_value, L.country_concept_id, L.country_source_value, L.latitude, L.longitude, LS.start_date, LS.end_date
                FROM CDM.LOCATION L LEFT JOIN CDM.LOCATION_HISTORY LS ON L.location_id = LS.location_id)
            SELECT person_id, visit_occurrence_id, year(visit_start_date) as year, address.location_id, address.address_1, address.address_2, address.city, address.state, address.zip, address.county, address.location_source_value, address.country_concept_id, address.country_source_value, address.latitude, address.longitude
            FROM patient p
            LEFT JOIN address ON p.person_id = address.entity_id
            WHERE p.visit_start_date BETWEEN address.start_date AND address.end_date
              AND p.visit_end_date BETWEEN address.start_date AND address.end_date
              AND visit_start_date >= '2012-01-01'
              AND (LTRIM(RTRIM(ISNULL(address.latitude, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))
              AND (LTRIM(RTRIM(ISNULL(address.longitude, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))
              AND NOT (LTRIM(RTRIM(ISNULL(address.address_1, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))"""
    }

    # Function to fetch and save data
    def fetch_and_save(category, query):
        print(f"Starting data extraction for category: {category}")
        filename_template = os.path.join(linkage_data_dir, categories[category], f"{category}_{{}}.csv")
        offset = 0
        batch_number = 1
        with engine.connect() as conn:
            while batch_number <= 2: #True: #testing
                print(f"Fetching batch {batch_number} for category {category} with offset {offset}")
                batch_query = f"{query} ORDER BY person_id, visit_start_date OFFSET {offset} ROWS FETCH NEXT 100000 ROWS ONLY"
                df = pd.read_sql(batch_query, conn)
                print(f"Rows fetched: {len(df)}")
                if df.empty:
                    print(f"No more data for category {category}. Exiting loop.")
                    break
                df.to_csv(filename_template.format(batch_number), index=False)
                print(f"Saved batch {batch_number} for category {category}")
                offset += 100000
                batch_number += 1

    # Execute queries in parallel using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_and_save, category, query) for category, query in queries.items()]


def flag_geocode_results(geocoded_df, orig_df):
    try:
        # 2️⃣  bring the original address pieces back in (needed for the reason logic)
        geocoded_df = geocoded_df.rename(columns={'address_1':'street'})
        orig_df = orig_df.rename(columns={'address_1':'street'})
        print('columns in orig_df: ', orig_df.columns)
        print('columns in geocoded_df: ', geocoded_df.columns)
        merge_cols = [c for c in ("street", "city", "state", "zip") if c in orig_df.columns]
        geocoded_df = (
            geocoded_df
            .merge(orig_df[merge_cols + ["_rid"]], on="_rid", how="left")
            .sort_values("_rid")
            .reset_index(drop=True)
        )

        geocoded_df = geocoded_df.drop(columns=['city_x','state_x','zip_x','street_x'])
        geocoded_df = geocoded_df.rename(columns={'city_y':'city', 'state_y':'state', 'zip_y':'zip','street_y':'street'})

        # ── helpers ────────────────────────────────────────────────
        MISSING_SENTINELS = {"nan", "na", "n/a", "none", "null", ""}

        def _blank(x: object) -> bool:
            return pd.isna(x) or str(x).strip().lower() in MISSING_SENTINELS

        def _has_coords(row) -> bool:
            """Return True **only** if lat/lon are real numbers inside
            normal geographic limits (and not NaN)."""
            try:
                lat = float(row.get("lat", ""))
                lon = float(row.get("lon", ""))
            except (ValueError, TypeError):
                return False
            if pd.isna(lat) or pd.isna(lon):
                return False
            return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0

        def _zip_clean(z):
            z = str(z).strip().lower()
            return z[:-2] if z.endswith(".0") else z

        def _reason(row):
            # ----- Successful geocode – hospital address test -----
            if row["geocode_result"] == "Geocoded":
                if {"street", "city", "state", "zip"}.issubset(row.index):
                    full_addr = " ".join(
                        [
                            str(row.get("street", "")).strip().lower(),
                            str(row.get("city", "")).strip().lower(),
                            str(row.get("state", "")).strip().lower(),
                            _zip_clean(row.get("zip", "")),
                        ]
                    ).strip()
                else:  # single-column case
                    full_addr = (
                        str(row.get("address", ""))
                        .lower()
                        .strip()
                    )
                return "Hospital address given" if full_addr in HOSPITAL_ADDRESSES else ""

            # ----- Imprecise geocode – why? -----
            if all(_blank(row.get(c, "")) for c in ("street", "city", "state", "zip")):
                return "Blank/Incomplete address"
            if _blank(row.get("zip", "")):
                return "Zip missing"
            if _blank(row.get("street", "")):
                return "Street missing"
            return ""

        # 3️⃣  rebuild geocode_result & reason
        geocoded_df.drop(columns=["geocode_result"], errors="ignore", inplace=True)
        geocoded_df["geocode_result"] = geocoded_df.apply(
            lambda r: "Geocoded" if _has_coords(r) else "Imprecise Geocode",
            axis=1,
        )
        geocoded_df["reason"] = geocoded_df.apply(_reason, axis=1)

        # 4️⃣  tidy-up: remove auxiliary cols (_rid) but KEEP 'address'
        geocoded_df.drop(columns=[c for c in geocoded_df.columns if c.startswith("_")],
                         inplace=True, errors="ignore")
        geocoded_df.drop(columns=merge_cols, inplace=True, errors="ignore")

        # normalise year (no trailing “.0”)
        if "year" in geocoded_df.columns:
            geocoded_df["year"] = pd.to_numeric(
                geocoded_df["year"], errors="coerce"
            ).astype("Int64")
        
        logger.info("geocode_result / reason fixed, _rid removed.")

    except Exception as e:
        logger.warning(f"Could not post-process geocoder output: {e}")

    return geocoded_df

# Generate latitude and longitude from address infomation
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
    print('Generate_coordinates ........')
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

    if os.path.exists(preprocessed_file_path):
        logger.info(f"Preprocessed file created: {preprocessed_file_path}")
    else:
        logger.error(f"Failed to create preprocessed file: {preprocessed_file_path}")
        return os.path.abspath(output_file_name)  # Return early if file not created

    # Convert the folder and file paths to absolute paths for Docker
    abs_output_folder = os.path.abspath(output_folder)  # Convert to absolute path
    abs_preprocessed_file = os.path.abspath(preprocessed_file_path)  # Convert to absolute path

    container_cwd = os.getcwd()  # This will be /workspace when using -w /workspace

    # Calculate the relative path from the container's working directory
    rel_path = os.path.relpath(abs_output_folder, container_cwd)
    container_input_path = f'/workspace/{rel_path}/{os.path.basename(abs_preprocessed_file)}'
    
    # Define the Docker command
    # NOTE: Mount the host workspace to allow the geocoder container to access the input file.
    docker_command = [
        'docker', 'run', '--rm',
        '-v', f'{host_base}:/workspace',
        'ghcr.io/degauss-org/geocoder:3.3.0',
       container_input_path,
        str(threshold)
    ]
    logger.debug(f"Using container path {container_input_path} with /workspace mount for geocoder access")

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
    columns_to_drop = {'matched_street', 'matched_zip', 'matched_city', 'matched_state', 'score', 'precision', 'address_1', 'state', 'city', 'zip'}
    # Drop only the columns that exist in the DataFrame
    columns_in_df = set(df.columns)  # Get the columns that exist in the DataFrame
    columns_to_drop = columns_to_drop.intersection(columns_in_df)  # Find intersection of existing columns and columns to drop
    
    if columns_to_drop:  # Only drop if there are columns to drop
        df.drop(columns=columns_to_drop, inplace=True)
        
    df.to_csv(preprocessed_file_path, index=False)

    # Also normalize the preprocessed file path
    abs_preprocessed_file = os.path.abspath(preprocessed_file_path).replace("\\", "/")
    
    output_file = os.path.join(output_folder, f"preprocessed_2_census_block_group_0.6.0_{year}.csv")    

    container_cwd = os.getcwd()  # This will be /workspace when using -w /workspace

    # Calculate the relative path from the container's working directory
    rel_path = os.path.relpath(abs_output_folder, container_cwd)
    container_input_path = f'/workspace/{rel_path}/{os.path.basename(abs_preprocessed_file)}'
    # output_file = f"{df.replace('.csv', '')}_census_block_group_0.6.0_{year}.csv"
    # Define the Docker command
    # NOTE: Mount the host workspace to allow the census container to access the input file.
    docker_command2 = [
        "docker", "run", "--rm",
        "-v", f"{host_base}:/workspace",
        "ghcr.io/degauss-org/census_block_group:0.6.0",
        container_input_path, str(year)
    ]
    logger.debug(f"Using container path {container_input_path} with /workspace mount for census access")
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
        # Add FIPS to original df
        df['FIPS'] = all_fips_df['FIPS']
        df.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
        df.to_csv(encounter_with_fips_file, index=False)
        logger.info(f"Encounter with FIPS file generated: {encounter_with_fips_file}")
        generated_fips_files.append(encounter_with_fips_file)  # Add to list

    elif os.path.exists(fips_file_2010):
        fips_df_2010 = pd.read_csv(fips_file_2010)
        fips_df_2010.drop(columns=['year_for_fips'], inplace=True)
        fips_df_2010.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
        # Add FIPS to original df
        df['FIPS'] = fips_df_2010['FIPS']
        df.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
        df.to_csv(encounter_with_fips_file, index=False)
        logger.info(f"FIPS file generated for 2010 with {len(fips_df_2010)} rows: {encounter_with_fips_file}")
        generated_fips_files.append(encounter_with_fips_file)  # Add to list

    elif os.path.exists(fips_file_2020):
        fips_df_2020 = pd.read_csv(fips_file_2020)
        fips_df_2020.drop(columns=['year_for_fips'], inplace=True)
        fips_df_2020.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
        # Add FIPS to original df
        df['FIPS'] = fips_df_2020['FIPS']
        df.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
        df.to_csv(encounter_with_fips_file, index=False)
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

        orig_df = df.copy(deep=True)
        orig_df["_rid"] = orig_df.index
        df["_rid"]      = orig_df["_rid"]
        if "zip" in orig_df.columns:
            orig_df["zip"] = (
                orig_df["zip"]
                .fillna("")
                .astype(str)
                .str.replace(r"\.0$", "", regex=True)
                .str.strip()
            )

        geocoded_file = generate_coordinates_degauss(df, columns, threshold, csv_output_dir)
        #get the coordinates files
        latlon = pd.read_csv(geocoded_file)
        columns_to_drop = ['matched_street', 'matched_zip', 'matched_city', 'matched_state', 'score', 'precision']
        latlon.drop(columns=[col for col in columns_to_drop if col in latlon.columns], inplace=True)
        latlon.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
        output_file = os.path.join(csv_output_dir, f"{base_filename}_with_coordinates.csv")
        latlon.to_csv(output_file, index=False)
        logger.info(f"Coordinates file generated: {output_file}")
        # Add coordinate file to the final_coordinate_files list
        final_coordinate_files.append(output_file)
        
    elif process_type == 'latlong':
        df = pd.read_csv(filepath)

        orig_df = df.copy(deep=True)
        orig_df["_rid"] = orig_df.index
        df["_rid"]      = orig_df["_rid"]
        if "zip" in orig_df.columns:
            orig_df["zip"] = (
                orig_df["zip"]
                .fillna("")
                .astype(str)
                .str.replace(r"\.0$", "", regex=True)
                .str.strip()
            )
        # Assume latlong processing includes geocoding as well
        geocoded_file = filepath  # For simplicity

    # Process FIPS generation for valid data
    if geocoded_file:
        df = pd.read_csv(geocoded_file)
        # Check if 'latitude' and 'longitude' columns exist and rename them to 'lat' and 'lon'
        if 'latitude' in df.columns and 'longitude' in df.columns:
            df.rename(columns={'latitude': 'lat', 'longitude': 'lon'}, inplace=True)

        df["_rid"] = orig_df["_rid"].values
        #df = flag_geocode_results(df, orig_df)
        
        df['year_for_fips'] = df[date_column].apply(lambda x: 2010 if x < 2020 else 2020)

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
    # output_base = './Linkage_result'
    # os.makedirs(output_base, exist_ok=True)
    threshold = 0.7
    columns = ['address_1', 'city', 'state', 'zip']
    date_column = 'year'
    
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
    
    output_dir = os.path.join(linkage_result_dir, process_type)
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

def export_location_history(user, password, server, port, database):
    """
    Exports the LOCATION_HISTORY table to LOCATION_HISTORY.csv
    """
    conn_str = f"mssql+pyodbc://{user}:{password}@{server}:{port}/{database}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes"
    engine = create_engine(conn_str)
    
    query = "SELECT * FROM CDM.LOCATION_HISTORY_DEMO"
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    output_path = os.path.join(base_output_dir, 'LOCATION_HISTORY.csv')
    df.to_csv(output_path, index=False)
    logger.info(f"LOCATION_HISTORY.csv created at {output_path}")

def create_location_csv(base_output_dir):
    """
    Create a LOCATION.csv file from the processed FIPS data.
    Collect unique locations with address, lat, long, FIPS.
    """
    import glob
    
    # Find all FIPS files
    fips_pattern = os.path.join(base_output_dir, 'OMOP_FIPS_result', '**', '*_with_fips.csv')
    fips_files = glob.glob(fips_pattern, recursive=True)
    logger.info(f"Found FIPS files: {fips_files}")
    
    all_data = []
    for file in fips_files:
        df = pd.read_csv(file)
        logger.info(f"Columns in {file}: {list(df.columns)}")
        # Assume columns: person_id, visit_occurrence_id, year, location_id, address_1, address_2, city, state, zip, county, location_source_value, country_concept_id, country_source_value, latitude, longitude, FIPS
        # Keep only location-related columns
        location_cols = ['location_id', 'address_1', 'address_2', 'city', 'state', 'zip', 'county', 'location_source_value', 'country_concept_id', 'country_source_value', 'latitude', 'longitude', 'FIPS']
        if all(col in df.columns for col in location_cols):
            loc_df = df[location_cols].drop_duplicates()
            all_data.append(loc_df)
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True).drop_duplicates()
        # Reorder columns to match expected format
        columns_order = ['location_id', 'address_1', 'address_2', 'city', 'state', 'zip', 'county', 'location_source_value', 'country_concept_id', 'country_source_value', 'latitude', 'longitude', 'FIPS']
        combined_df = combined_df[columns_order]
        # Sort by location_id in ascending order
        combined_df = combined_df.sort_values('location_id')
        # Save to LOCATION.csv in the base output dir
        output_path = os.path.join(base_output_dir, 'LOCATION.csv')
        combined_df.to_csv(output_path, index=False)
        logger.info(f"LOCATION.csv created at {output_path}")
    else:
        logger.warning("No FIPS data found to create LOCATION.csv")

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
    
    # Export LOCATION_HISTORY table
    export_location_history(args.user, args.password, args.server, args.port, args.database)
    
    process_directory(os.path.join(linkage_data_dir, 'invalid_lat_lon_address'))
    process_directory(os.path.join(linkage_data_dir, 'valid_address'))
    process_directory(os.path.join(linkage_data_dir, 'valid_lat_long'))
    
    # Create LOCATION.csv from processed data
    create_location_csv(base_output_dir)

    # Move ZIP files to base output directory before deleting subdirectories
    import shutil
    fips_result_dir = os.path.join(base_output_dir, 'OMOP_FIPS_result')
    for root, dirs, files in os.walk(fips_result_dir):
        for file in files:
            if file.endswith('.zip'):
                src = os.path.join(root, file)
                dst = os.path.join(base_output_dir, file)
                shutil.move(src, dst)
                logger.info(f"Moved ZIP file: {dst}")

    # Now delete all subdirectories after creating LOCATION.csv
    for root, dirs, files in os.walk(fips_result_dir):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            shutil.rmtree(dir_path)
            logger.info(f"Deleted directory: {dir_path}")



if __name__ == "__main__":
    main()