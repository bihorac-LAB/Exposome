# User manual

## Step 1: Collect geo information

#### Users should prepare a csv file as input with formatted geocode information. Only need to prepare for ONE of the following three (address, coordinates, and census tract).

### 1. Address information 
#### You should prepare a csv file as input with formatted address columns. We have two format for teh address, both are accptable. You can choose any one of them.

1. Column: address
   Example:
   
| address |
|----------|
| 1250 W 16Th St Jacksonville Fl 32209 |
|2001 Sw 16Th St Gainesville Fl 32608 | 


2. Column: street city state zip
   Example:
   
| Street | City | State | Zip |
|----------|----------|----------|----------|
| 1250 W 16th St | Jacksonville | FL | 32209 |
| 2001 SW 16th St | Gainesville | FL | 32608 |


Note: If you can collect latitude and longitude OR FIPS code information for patients directly, you don't need to prepare the address information.

### 2. Coordinates information 
#### Prepare a csv file with latitude and longitude inofrmation for the patients
Column: latitude longitude
Example:

| latitude | longitude |
|----------|----------|
| 30.353463 | -81.6749 |
| 29.634219 | -82.3433 |


### 3. Census tract information 

#### Prepare a csv file with fips code inofrmation for the patients
Column: FIPS 
Example:

| FIPS |
|----------|
| 12011080103 |
| 12011080103 | 


Note: If you can get the Census tract information for patients, you can skip the step 2.

## Step 2: Using python scripts to get Census tract information for patients
### Case 1: csv format

![image](https://github.com/user-attachments/assets/a1c5b366-dd78-4173-8ae7-33537e2a1bbc)

This input csv file should contain: 
1. Patient encunter id (e.g, 12345)
2. Patient encounter year (e.g, 2024)
3. Address information OR Coordinates information (Please refer to step1 for the detailed format)

### Case 2: OMOP format

![image](https://github.com/user-attachments/assets/79eacedc-e047-4e92-8b80-a67502c4b4e3)

Required table and column for OMOP database:

| Table_name | Required_column_name |
|----------|----------|
| person | person_id |
| visit_occurrence | visit_occurrence_id, visit_start_date, visit_end_date, person_id |
| location | location_id, address_1, city, state, zip, latitude, longitude |
| location history | location_id, entity_id, start_date, end_date |

Required input for the python script:

user: username for the OMOP database
password: password for the OMOP databse
server: server number
port: port number
database: database name for OMOP

## Step 3: SDOH Linkage










     
