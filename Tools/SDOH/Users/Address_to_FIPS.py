import pandas as pd
import os
import subprocess
import sys
import argparse
from loguru import logger
from sqlalchemy import create_engine
import concurrent.futures
import zipfile


logger.add(sys.stderr, format="{time} {level} {message}", filter="my_module", level="INFO")

#Generate latitude and longitude from address infomation
def generate_coordinates_degauss(df, columns, threshold, output_folder):
    
    logger.info("Generating coordinates...")
    
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

    # Reorder columns to ensure 'address' is the first column
    cols = ['address'] + [col for col in df.columns if col != 'address']
    df = df[cols]
    
    # Drop original address columns if they are no longer needed
    if len(columns) > 1:
        df.drop(columns=columns, inplace=True)
    
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
        result = subprocess.run(' '.join(docker_command), shell=True, check=True, capture_output=True, text=True)
        logger.info("Docker command executed successfully.")
        logger.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing Docker command: {e}")
        logger.error(e.stderr)

    # Define the output file name
    output_file_name = os.path.join(output_folder, f"preprocessed_1_geocoder_3.3.0_score_threshold_{threshold}.csv")
    return os.path.abspath(output_file_name)

#Generate the FIPS code from latitude and longitude
def generate_fips_degauss(df, year, output_folder):
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

# Function to process each individual CSV file
def process_csv_file(file, input_folder, args):
    file_path = os.path.join(input_folder, file)
        
    # Create a new folder for each CSV file
    output_folder = os.path.join(input_folder, file.replace('.csv', ''))
    os.makedirs(output_folder, exist_ok=True)
    
    logger.info(f"Processing file: {file_path}")

    # Step 1: Check if latitude and longitude are provided (skip geocode if present)
    if args.lat and args.long:
        logger.info("Using provided latitude and longitude columns, skipping geocoding.")
        df = pd.read_csv(file_path)
        df.rename(columns={args.lat: 'lat', args.long: 'lon'}, inplace=True)
        df['year_for_fips'] = df[args.year].apply(lambda x: 2010 if x < 2020 else 2020)

    # Step 2: If latitude and longitude are not provided, check for address columns
    elif args.columns:
        logger.info("Latitude and longitude not provided. Using address columns for geocoding.")
        threshold = 0.7
        df = pd.read_csv(file_path)
        geocoded_file = generate_coordinates_degauss(df, args.columns, threshold, output_folder)
        logger.info(f"Geocoded file created: {geocoded_file}")

        # Load geocoded file after processing
        df = pd.read_csv(geocoded_file)
        df['year_for_fips'] = df[args.year].apply(lambda x: 2010 if x < 2020 else 2020)

    else:
        logger.error("You must provide either address columns (for geocoding) or latitude and longitude.")
        return None

    # Step 3: Process FIPS generation for 2010 and 2020
    has_2010 = (df['year_for_fips'] == 2010).any()
    has_2020 = (df['year_for_fips'] == 2020).any()

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

    # Final output CSV file
    base_filename = os.path.splitext(file)[0]
    encounter_with_fips_file = os.path.join(output_folder, f"{base_filename}_with_fips.csv")

    fips_file_2010 = os.path.join(output_folder, "preprocessed_2_census_block_group_0.6.0_2010.csv")
    fips_file_2020 = os.path.join(output_folder, "preprocessed_2_census_block_group_0.6.0_2020.csv")

    if os.path.exists(fips_file_2010) and os.path.exists(fips_file_2020):
        fips_df_2010 = pd.read_csv(fips_file_2010)
        fips_df_2020 = pd.read_csv(fips_file_2020)
        all_fips_df = pd.concat([fips_df_2010, fips_df_2020], ignore_index=True)
        all_fips_df.drop(columns=['year_for_fips'], inplace=True)
        all_fips_df.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
        all_fips_df.to_csv(encounter_with_fips_file, index=False)
        logger.info(f"Encounter with FIPS file generated: {encounter_with_fips_file}")

    elif os.path.exists(fips_file_2010):
        fips_df_2010 = pd.read_csv(fips_file_2010)
        fips_df_2010.drop(columns=['year_for_fips'], inplace=True)
        fips_df_2010.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
        fips_df_2010.to_csv(encounter_with_fips_file, index=False)
        logger.info(f"FIPS file generated for 2010 with {len(fips_df_2010)} rows: {encounter_with_fips_file}")

    elif os.path.exists(fips_file_2020):
        fips_df_2020 = pd.read_csv(fips_file_2020)
        fips_df_2020.drop(columns=['year_for_fips'], inplace=True)
        fips_df_2020.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
        fips_df_2020.to_csv(encounter_with_fips_file, index=False)
        logger.info(f"FIPS file generated for 2020 with {len(fips_df_2020)} rows: {encounter_with_fips_file}")

    else:
        logger.error("Error: Neither FIPS file exists.")

    return encounter_with_fips_file
        
def main():
    parser = argparse.ArgumentParser(description='FIPS Geocoding')
    parser.add_argument('-i', '--input', type=str, required=True, help='Input folder path containing CSV files')
    parser.add_argument('--debug', dest='debug', action='store_true', help='Enable debug logging')
    parser.add_argument('-d', '--year', type=str, required=True, help='Year column name')
    #(if you have separate columns for address please input in this order: street, city, state, zip. If you just have one column fro address, just input the address column name, eg:address)
    parser.add_argument('--columns', nargs='+', help='Column names for address(if you have separate columns for address please input in this order: street, city, state, zip. If you just have one column fro address, just input the address column name, eg:address)')
    parser.add_argument('-lat', type=str, help='Latitude column name')
    parser.add_argument('-long', type=str, help='Longitude column name')
    
    args = parser.parse_args()

    input_folder = args.input
    csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]

    final_output_files = []  # Collect all final output files for zipping

   # Step 1: Use ThreadPoolExecutor to process up to 10 files concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(process_csv_file, file, input_folder, args): file for file in csv_files}

        for future in concurrent.futures.as_completed(futures):
            file = futures[future]
            try:
                result = future.result()
                if result:
                    final_output_files.append(result)
            except Exception as e:
                logger.error(f"Error processing file {file}: {e}")

    # Step 2: Package all final output files into a zip
    zip_filename = os.path.join(input_folder, "final_output_files.zip")
    
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for final_file in final_output_files:
            if os.path.exists(final_file):  # Only include files that exist
                zipf.write(final_file, os.path.basename(final_file))  # Add the file to the zip archive
            else:
                logger.error(f"Skipping missing file: {final_file}")

    logger.info(f"All output files zipped into: {zip_filename}")


if __name__ == "__main__":
    main()
                
    
    