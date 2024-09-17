import os
import logging

def create_directories(base_directory, categories):
    """
    Creates directories for each category if they do not exist.

    Parameters:
    base_directory (str): The base directory path.
    categories (dict): A dictionary of categories and their corresponding subdirectories.
    """
    for category in categories.values():
        os.makedirs(os.path.join(base_directory, category), exist_ok=True)
    logging.info("Directories created or verified.")