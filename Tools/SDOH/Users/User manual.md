# User manual

## Step 1: Preparing Input Data

#### This guide outlines the steps required to prepare input data for Social Determinants of Health (SDOH) linkage using geographic information. Users need to prepare only one of the following data types per patient: address, coordinates, or census tract information.

### Option 1. Address information 
#### Prepare a CSV file with formatted address data using one of the following acceptable formats:
#### Format A: Single Column Address
1. Column: address
   Example:
   
| address |
|----------|
| 1250 W 16Th St Jacksonville Fl 32209 |
|2001 Sw 16Th St Gainesville Fl 32608 | 

#### Format B: Multi-Column Address
2. Column: street city state zip
   Example:
   
| Street | City | State | Zip |
|----------|----------|----------|----------|
| 1250 W 16th St | Jacksonville | FL | 32209 |
| 2001 SW 16th St | Gainesville | FL | 32608 |


Note: If you can directly collect latitude, longitude, or FIPS code information for patients, preparing address information is not required.

### Option 2: Coordinates Information 
#### Prepare a CSV file with latitude and longitude information for the patients.
Column: latitude longitude
Example:

| latitude | longitude |
|----------|----------|
| 30.353463 | -81.6749 |
| 29.634219 | -82.3433 |


### Option 3: Census Tract Information

#### Prepare a CSV file with FIPS code information for the patients.
Column: FIPS 
Example:

| FIPS |
|----------|
| 12011080103 |
| 12011080103 | 


Note: If you obtain Census tract information for patients, you can skip preparing coordinate information.

## Step 2: Using Python Scripts to Retrieve Census Tract Information
### Case 1: csv format

![image](https://github.com/user-attachments/assets/a1c5b366-dd78-4173-8ae7-33537e2a1bbc)

#### This input csv file should contain: 
1. Patient encunter id (e.g, 12345)
2. Patient encounter year (e.g, 2024)
3. Address information OR Coordinates information (Please refer to step1 for the detailed format)

### Case 2: OMOP format

![image](https://github.com/user-attachments/assets/79eacedc-e047-4e92-8b80-a67502c4b4e3)

#### Required table and column for OMOP database:

| Table_name | Required_column_name |
|----------|----------|
| person | person_id |
| visit_occurrence | visit_occurrence_id, visit_start_date, visit_end_date, person_id |
| location | location_id, address_1, city, state, zip, latitude, longitude |
| location history | location_id, entity_id, start_date, end_date |

#### Required input for the python script:

user: username for the OMOP database
password: password for the OMOP databse
server: server number
port: port number
database: database name for OMOP

## Step 3: SDOH Linkage
First, User should go to the web page for sign up.









     
