# User Manual

## Step 1: Preparing Input Data

This guide outlines the steps required to prepare input data for Social Determinants of Health (SDOH) linkage using geographic information. Users need to prepare only **ONE** of the following data types encounter: address, coordinates, or census tract information.

### Option 1. Address information 
#### Prepare a CSV file with formatted address data using one of the following acceptable formats:
#### Format A: Single Column Address
- **Column**: `address`
- **Example**:
   
| address |
|----------|
| 1250 W 16Th St Jacksonville Fl 32209 |
|2001 Sw 16Th St Gainesville Fl 32608 | 

#### Format B: Multi-Column Address
- **Columns**: `Street`, `City`, `State`, `Zip`
- **Example**:
   
| Street | City | State | Zip |
|----------|----------|----------|----------|
| 1250 W 16th St | Jacksonville | FL | 32209 |
| 2001 SW 16th St | Gainesville | FL | 32608 |

**Note**: If you can directly collect latitude, longitude, or FIPS code information for patients, preparing address information is not required.

### Option 2: Coordinates Information 
#### Prepare a CSV file with latitude and longitude information for the patients.
- **Columns**: `latitude`, `longitude`
- **Example**:

| latitude | longitude |
|----------|----------|
| 30.353463 | -81.6749 |
| 29.634219 | -82.3433 |


### Option 3: Census Tract Information

#### Prepare a CSV file with FIPS code information for the patients.
- **Column**: `FIPS`
- **Example**:

| FIPS |
|----------|
| 12011080103 |
| 12011080103 | 


**Note**:  If you obtain Census tract information for patients, you can skip preparing coordinate information.

## Step 2: Using Python Scripts to Retrieve Census Tract Information
### Case 1: csv format

![image](https://github.com/user-attachments/assets/a1c5b366-dd78-4173-8ae7-33537e2a1bbc)

 **Input CSV File Should Contain**:
- Patient encounter ID (e.g., 12345)
- Patient encounter year (e.g., 2024)
- Address or coordinates information (refer to Step 1 for details)


### Case 2: OMOP format

![image](https://github.com/user-attachments/assets/79eacedc-e047-4e92-8b80-a67502c4b4e3)

 **Required Tables and Columns for OMOP Database**:

| Table_name | Required_column_name |
|----------|----------|
| person | person_id |
| visit_occurrence | visit_occurrence_id, visit_start_date, visit_end_date, person_id |
| location | location_id, address_1, city, state, zip, latitude, longitude |
| location history | location_id, entity_id, start_date, end_date |

 **Required Input for the Python Script**:
- `user`: username for the OMOP database
- `password`: password for the OMOP databse
- `server`: server number
- `port`: port number
- `database`: database name for OMOP

## Step 3: SDOH Linkage Process

### Getting Started
1. **Sign Up**: Begin by navigating to the [registration page](#) to create an account. Follow the on-screen instructions to complete the sign-up process.

2. **Upload Your CSV File**: Once registered, you can upload your prepared CSV file. Ensure that your file adheres to the required format listed below.

### Required CSV File Format
Prepare your CSV file to include the following columns:
- `person_id`
- `visit_occurrence_id`
- `year`
- `FIPS`

**Example**:

| person_id | visit_occurrence_id | year | FIPS        |
|-----------|---------------------|------|-------------|
| 1         | 11                  | 2012 | 12011080103 |
| 2         | 22                  | 2022 | 12103026400 |

### Processing and Results
- **Processing**: After uploading your CSV file, our system will automatically execute the necessary Python script in the backend to perform SDOH linkage.
  
- **Downloading Results**: Once processing is complete, you will be able to download the final results directly from the web page.

### Additional Guidance
For further assistance or troubleshooting, refer to our [help section](#) or contact support.








     
