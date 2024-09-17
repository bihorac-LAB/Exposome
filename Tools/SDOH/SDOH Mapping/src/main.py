import argparse
import logging
from src.omop_extraction import omop_extract_and_save_data
from src.data_processing import process_directory


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    parser = argparse.ArgumentParser(description="Export data from SQL Server to CSV files.")
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Call the function with credentials read from .env file
    omop_extract_and_save_data()
    

    # Process files in the 'invalid_lat_lon_address' directory
    process_directory('./Linkage_data/invalid_lat_lon_address')

    # Process files in the 'valid_address' directory
    process_directory('./Linkage_data/valid_address')

    # Process files in the 'valid_lat_long' directory
    process_directory('./Linkage_data/valid_lat_long')



if __name__ == "__main__":
    main()
                


