import pandas as pd
import subprocess
import os
import sys
import argparse
import logging
from sqlalchemy import create_engine

#Link to SDoH database using FIPS code and date. This version is conbined all year csv output in one csv file(keep the original datasets column name)
def sdoh_linkage(df, args):
    df[args.date] = pd.to_datetime(df[args.date])
    df['year'] = df[args.date].dt.year
    df['year'] = df['year'].clip(lower=2012, upper=2023)
    df = df.rename(columns={args.f: 'FIPS'})
    df['FIPS'] = df['FIPS'].apply(lambda x: str(x).split('.')[0])

    DATABASE_URL = ""
    engine = create_engine(DATABASE_URL)

    all_data_frames = []

    for year, group_df in df.groupby('year'):
        fips_list = ', '.join(f"'{fip}'" for fip in group_df['FIPS'].unique())
        fips_condition = f"geocode IN ({fips_list})"
        
        logging.debug(f"Year: {year}, FIPS condition: {fips_condition}")
        #Find the index table
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
        # Mapping for the vairable table
        for _, v_row in variables_index_df.iterrows():
            variable_table_name = v_row['variables_index_name'][:-6] + '_variables'
            variable_table_query = f"""
            SELECT *
            FROM data.\"{variable_table_name}\"
            WHERE {fips_condition}
            """
            # logging.debug(f"Variable table query: {variable_table_query}")

            variable_table_df = pd.read_sql(variable_table_query, engine)
            print(f"{variable_table_name} generated")

            if variable_table_df.empty:
                logging.warning(f"No data returned for {variable_table_name}. Skipping...")
                continue

            variable_table_df['effective_start_timestamp'] = pd.to_datetime(variable_table_df['effective_start_timestamp'])
            variable_table_df['effective_end_timestamp'] = pd.to_datetime(variable_table_df['effective_end_timestamp'])
            #Link to SDoH database using FIPS code and date column
            filtered_df = variable_table_df[(variable_table_df['geocode'].isin(group_df['FIPS'])) &
                                            (variable_table_df['effective_start_timestamp'] <= group_df[args.date].max()) &
                                            (variable_table_df['effective_end_timestamp'] >= group_df[args.date].min())]

            if not filtered_df.empty:
                group_df = pd.merge(group_df, filtered_df, left_on='FIPS', right_on='geocode', how='left')
                group_df.drop(columns=['geocode', 'effective_start_timestamp', 'effective_end_timestamp'], inplace=True)

        all_data_frames.append(group_df)

    final_df = pd.concat(all_data_frames, ignore_index=True, sort=False)
    output_file = './SDoH_linkage_full.csv'
#     final_df.rename(columns={
#         'lat': 'latitude',
#         'lon': 'longitude'}, inplace=True)
#     final_df.drop(columns=['score', 'precision', 'geocode_result'], inplace=True)
    final_df.to_csv(output_file, index=False)
    logging.info(f'{output_file} written successfully.')

    engine.dispose()

def main():
    parser = argparse.ArgumentParser(description='FIPS Geocoding')
    parser.add_argument('-i', '--input', type=str, required=True, help='Input file path')
    parser.add_argument('--debug', dest='debug', action='store_true', help='Enable debug logging')
    parser.add_argument('-d', '--date', type=str, required=True, help='Date column name')
    parser.add_argument('-f',  type=str, required=True, help='FIPS column name')
    
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    
    df = pd.read_csv(args.input)
    sdoh_linkage(df, args)
 
 

if __name__ == '__main__':
    main()
