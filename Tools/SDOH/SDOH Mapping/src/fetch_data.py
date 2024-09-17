import os
import pandas as pd
import pyodbc
import logging

# Function to fetch and save data to CSV in batches
#def fetch_data_and_save(category, query):
def fetch_data_and_save(category, query_file, conn_str, base_directory, categories):
        """
            Fetches data from a SQL database in batches of 100,000 rows and saves each batch as a CSV file.
            The function executes a SQL query provided for a specific data category (e.g., Latlong, Invalid, Address),
            retrieves data in chunks, and saves it to different directories based on the category.

            Parameters:
            category (str): The category of data being fetched (e.g., 'Latlong', 'Invalid', 'Address').
            query_file (str): Path to the SQL file containing the query for the given category.
            conn_str (str): Connection string for the database.
            base_directory (str): Base directory for saving CSVs.
            categories (dict): A dictionary of categories and their corresponding subdirectories.
            
            Each batch of 100,000 rows is saved to a CSV file named as {category}_batch.csv.
            If there is any error connecting to the database or during data retrieval, it logs the error and stops the process.
        """

        filename_template = os.path.join(base_directory, categories[category], f"{category}_{{}}.csv")
        try:
            with open(query_file, 'r') as file:
                query = file.read()

            with pyodbc.connect(conn_str) as conn:
                logging.info(f"Successfully connected to the database for {category}.")
                offset = 0
                batch_number = 1
                while batch_number <= 2: #True: #testing
                    # Pagination with OFFSET and FETCH
                    batch_query = f"{query} ORDER BY person_id, visit_start_date OFFSET {offset} ROWS FETCH NEXT 100,000 ROWS ONLY"
                    df = pd.read_sql(batch_query, conn)
                    if df.empty:
                        logging.info(f"No more rows for {category} after batch {batch_number}.")
                        break
                    #save to csv
                    df.to_csv(filename_template.format(batch_number), index=False)
                    logging.info(f"Saved batch {batch_number} for {category}.")
                    offset += 100000
                    batch_number += 1
        except pyodbc.Error as conn_err:
            # Handles database connection errors
            logging.error(f"Database connection failed for {category}: {conn_err}")
        except Exception as e:
            # Handles all other possible exceptions
            logging.error(f"Error fetching data for {category}: {e}")

