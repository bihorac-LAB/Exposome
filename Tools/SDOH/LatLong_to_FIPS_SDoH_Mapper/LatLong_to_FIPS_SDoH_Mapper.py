import pandas as pd
import subprocess
import os
import sys
import argparse
import logging
from sqlalchemy import create_engine

# Generate the FIPS code using latitude and longitude
def generate_fips_degauss(input_file, year, lat_col, long_col):
     # Load the data
    if input_file.endswith('.csv'):
        df = pd.read_csv(input_file)
    elif input_file.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(input_file)
                           
    print('Generating FIPS...')
    
    # Rename latitude and longitude columns to 'lat' and 'lon'
    df = df.rename(columns={lat_col: 'lat', long_col: 'lon'})
    
    # Map the year to the nearest supported year
    if year < 2020:
        year = 2010
    else:
        year = 2020
        
    preprocessed_file_path = './preprocessed.csv'
    df.to_csv(preprocessed_file_path, index=False)


    output_file = f"preprocessed_census_block_group_0.6.0_{year}.csv"
    docker_command2 = ["docker", "run", "--rm", "-v", f"{os.getcwd()}:/tmp", "ghcr.io/degauss-org/census_block_group:0.6.0", '/tmp/preprocessed.csv', str(year)]
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

#Link to SDoH database using FIPS code and date. This version is conbined all year csv output in one csv file(keep the original datasets column name)
def sdoh_linkage(df, args):
    df[args.date] = pd.to_datetime(df[args.date])
    df['year'] = df[args.date].dt.year
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

     # FInd the index table 
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
            logging.debug(f"Variable table query: {variable_table_query}")

            variable_table_df = pd.read_sql(variable_table_query, engine)
            print(f"{variable_table_name} generated")

            if variable_table_df.empty:
                logging.warning(f"No data returned for {variable_table_name}. Skipping...")
                continue

            variable_table_df['effective_start_timestamp'] = pd.to_datetime(variable_table_df['effective_start_timestamp'])
            variable_table_df['effective_end_timestamp'] = pd.to_datetime(variable_table_df['effective_end_timestamp'])
            # Link to the SDoH database when data between effective_start_timestamp and effective_end_timestamp.
            filtered_df = variable_table_df[(variable_table_df['geocode'].isin(group_df['FIPS'])) &
                                            (variable_table_df['effective_start_timestamp'] <= group_df[args.date].max()) &
                                            (variable_table_df['effective_end_timestamp'] >= group_df[args.date].min())]

            if not filtered_df.empty:
                group_df = pd.merge(group_df, filtered_df, left_on='FIPS', right_on='geocode', how='left')
                group_df.drop(columns=['geocode', 'effective_start_timestamp', 'effective_end_timestamp'], inplace=True)

        all_data_frames.append(group_df)
    
       # Combine all the DataFrames from the index tables
    if all_index_data_frames:
        combined_index_df = pd.concat(all_index_data_frames, ignore_index=True, sort=False)
        # Drop duplicate rows
        combined_index_df.drop_duplicates(inplace=True)
        index_output_file = './combined_index_data.csv'
        combined_index_df.to_csv(index_output_file, index=False)
        logging.info(f'{index_output_file} written successfully.')

    final_df = pd.concat(all_data_frames, ignore_index=True, sort=False)
    output_file = './SDoH_linkage_Degauss_full.csv'
    final_df.rename(columns={
        'lat': 'latitude',
        'lon': 'longitude'}, inplace=True)
    # final_df.drop(columns=['score', 'precision', 'geocode_result'], inplace=True)
    final_df.to_csv(output_file, index=False)
    logging.info(f'{output_file} written successfully.')

    engine.dispose()

def main():
    parser = argparse.ArgumentParser(description='FIPS Geocoding')
    parser.add_argument('-i', '--input', type=str, required=True, help='Input file path')
    parser.add_argument('--debug', dest='debug', action='store_true', help='Enable debug logging')
    parser.add_argument('-d', '--date', type=str, required=True, help='Date column name')
    parser.add_argument('-lat', type=str, required=True, help='Latitude column name')
    parser.add_argument('-long', type=str, required=True, help='Longitude column name')
    
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    
    df = pd.read_csv(args.input)
    print('Read')
    df[args.date] = pd.to_datetime(df[args.date], errors='coerce')
    df['year'] = df[args.date].dt.year
    df['year'] = df['year'].clip(lower=2012, upper=2023)
    
    for year in df['year'].unique():
        geocoded_fips = generate_fips_degauss(args.input, year, args.lat, args.long)
#         if geocoded_fips:
#             print(f"Output file: {geocoded_fips}")
#             df_year = pd.read_csv(geocoded_fips)  # read the updated CSV with FIPS
#             sdoh_linkage(df_year, args)
#         else:
#             print("Error: Geocoded FIPS file was not generated.")
    fips_file_2010 = "preprocessed_census_block_group_0.6.0_2010.csv"
    fips_file_2020 = "preprocessed_census_block_group_0.6.0_2020.csv"
    
    if os.path.exists(fips_file_2010) and os.path.exists(fips_file_2020):
        fips_df_2010 = pd.read_csv(fips_file_2010)
        fips_df_2020 = pd.read_csv(fips_file_2020)

        if args.date in fips_df_2010.columns and args.date in fips_df_2020.columns:
            fips_df_2010[args.date] = pd.to_datetime(fips_df_2010[args.date], errors='coerce')
            fips_df_2020[args.date] = pd.to_datetime(fips_df_2020[args.date], errors='coerce')

            print("Years in 2010 file:", fips_df_2010[args.date].dt.year.unique())
            print("Years in 2020 file:", fips_df_2020[args.date].dt.year.unique())
            #Keep year < 2020 in fips 2010 version, keep year >= 2020 in fips 2020 version
            fips_df_2010 = fips_df_2010[fips_df_2010[args.date].dt.year < 2020]
            fips_df_2020 = fips_df_2020[fips_df_2020[args.date].dt.year >= 2020]

            print("Rows after filtering 2010:", len(fips_df_2010))
            print("Rows after filtering 2020:", len(fips_df_2020))

            all_fips_df = pd.concat([fips_df_2010, fips_df_2020], ignore_index=True)

            print("Combined rows count:", len(all_fips_df))
            sdoh_linkage(all_fips_df, args)
        else:
            print(f"Error: Date column '{args.date}' not found in FIPS files.")
    else:
        print("Error: Required FIPS files are missing.")
        

if __name__ == '__main__':
    main()



