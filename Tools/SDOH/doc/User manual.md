# User Manual
*Note: Please do not share any PHI information*

## Step 1: Preparing Input Data

This guide outlines the steps required to prepare input data for linking Social Determinants of Health (SDOH) using geographic information. The Census Tract (FIPS 11 code) is the key geographic identifier used to connect data to the SDOH database. Step 1 is used to prepare the information for generating FIPS11 code, and step 2 is to generate FIPS code using toolkit. Users need to prepare only **ONE** of the following data elements for each encounter: address, coordinates, or census tract information.

### Option 1. Address information 
#### Prepare a folder to save some CSV files with formatted address data using one of the following acceptable formats:
#### Format A: Multi-Column Address
- **Columns**: `street`, `city`, `state`, `zip`
- **Example**:
   
| street | city | state | zip |
|----------|----------|----------|----------|
| 1250 W 16th St | Jacksonville | FL | 32209 |
| 2001 SW 16th St | Gainesville | FL | 32608 |

#### Format B: Single Column Address
- **Column**: `address`
- **Example**:
   
| address |
|----------|
| 1250 W 16Th St Jacksonville Fl 32209 |
|2001 Sw 16Th St Gainesville Fl 32608 | 

**Note**: If you can directly collect latitude, longitude, or FIPS code information for patients, preparing address information is not required.

### Option 2: Coordinates Information 
#### Prepare a folder to save some CSV files with latitude and longitude information for the patients.
- **Columns**: `latitude`, `longitude`
- **Example**:

| latitude | longitude |
|----------|----------|
| 30.353463 | -81.6749 |
| 29.634219 | -82.3433 |


### Option 3: Census Tract Information

####  Prepare a folder to save some CSV files with FIPS code information for the patients.
- **Column**: `FIPS`
- **Example**:

| FIPS |
|----------|
| 12011080103 |
| 12103026400 | 


**Note**:  If you already have Census tract information for encounters, you can skip preparing coordinate information and skip step 2.

## Step 2: Get Census Tract Information

We provide two methods to retrieve FIPS codes from coordinate data:

- DeGAUSS Toolkit (Local Execution): Run the DeGAUSS Python toolkit locally for efficient FIPS code extraction.
- Spatial Join (Web-based Tool): Perform spatial joins via our web page, leveraging a backend database to process and return FIPS codes. Users can download the resulting FIPS file upon completion.

| Method | Advantage | Disadvantage |
|----------|----------|----------|
| DeGAUSS | Faster and more efficient processing. | Limited to 2010 year and 2020 year FIPS codes; accuracy may be lower for other years. |
| Spatial  Join | Provides year-specific FIPS codes, delivering higher accuracy with precise data for multiple years. | Requires longer processing times due to the complexity of spatial calculations.|

For year-specific accuracy, we recommend using the Spatial Join method.

### DeGAUSS Method
The DeGAUSS method offers two distinct approaches based on the data source. One method is tailored for CSV file inputs (Case 1), while the other is optimized for OMOP database integration (Case 2).

#### Case 1: csv format

![image](https://github.com/user-attachments/assets/a1c5b366-dd78-4173-8ae7-33537e2a1bbc)

 **Input CSV File Should Contain**:
- Patient encounter ID (e.g., 12345)
- Patient encounter year, the column name should called **year** (e.g., 2024)
- Address or coordinates information (refer to Step 1 for details)

**Python scripts input:**

- -i：Input folder path *(required)*

- -o: options for three different types of input, choices=[1, 2, 3]
      1 = street, city, state, zip; 2 = address; 3 = latitude, longitude'  *(required)*
  
**Usage example:**

*option 1:* 
If your prepared data in option 1 format A in step 1, you can input below:

python Address_to_FIPS.py -i ./folder -o 1

![image](https://github.com/user-attachments/assets/7758e7ef-9e30-417a-aefc-2e8703d519a2)

*option 2:*
If your prepared data in option 1 format B in step 1, you can input below:

python Address_to_FIPS.py -i ./folder -o 2

![image](https://github.com/user-attachments/assets/4f5c94dd-bc64-499c-b10b-9c8875298169)

*option 3:*
If your prepared data in option 2 in step 1, you can input below:

python Address_to_FIPS.py -i ./folder -o 3

![image](https://github.com/user-attachments/assets/6d83742a-efee-427a-969c-ca73afa1ab36)

**Output example:**

Three options input have same output format.

![image](https://github.com/user-attachments/assets/489d8cf4-cc02-4864-a7ff-fefb26167a86)

#### Case 2: OMOP format

![image](https://github.com/user-attachments/assets/79eacedc-e047-4e92-8b80-a67502c4b4e3)

The scripts extract the required infomation form OMOP database to Linkage data and then convert the address or latitude, longitude to FIPS code.

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

**Usage example:**

python OMOP_to_FIPS.py --user xxx --password xxx --server xxx --port xxx --database xxx

**Output example:**
```plaintext
├── Linkage_data/
│   ├── valid_address/        # Saved all patient encounter information with address
│   ├── invalid_lat_lon_address/        #  Saved all patient encounter information without address or latitude, longitude
│   └── valid_lat_long/     # Saved all patient encounter information with latitude and longitude

├── Linkage_result/
│   ├── address/        # Saved the output result from valid_address folder
|   |   ├──address_with_coordinates.zip   # Addresses with geographic coordinates
│   │   └── address_with_fips.zip         # Addresses with FIPS codes
│   ├── invalid/        #  Empty fodler (files in invalid_lat_lon_address do not meet the requirments for converting the FIPS code)
│   └── latlong/        # Saved the output result from valid_lat_long folder
|       └──latlong_with_fips.zip   # Latlong with valid_lat_long

```

![image](https://github.com/user-attachments/assets/525ecf22-c50e-4c1a-97b7-adde416b18d3)


### Spatial Join Method (updating)

#### Uploading Files for FIPS Code Generation
Users can upload their final_coordinates_files.zip on our web page, and we will generate files containing the most accurate FIPS codes based on the chosen method.



## Step 3: SDOH Linkage Process

### Getting Started
1. **Sign Up**: Begin by navigating to the [registration page](https://sdoh.rc.ufl.edu/)(#) to create an account. Follow the on-screen instructions to complete the sign-up process.

2. **Upload Your CSV File**: Once registered, you can upload the result zip file(e.g. output_with_fips.zip) if you follow the step 1&2. If you already have your fips file by yourself

### Required CSV File Format
Prepare your CSV file to include the following columns:
- `person_id`
- `visit_occurrence_id`
- `year`
- `FIPS`

**Input example**:

![image](https://github.com/user-attachments/assets/95b15319-fec2-459c-a079-3ea41813fe96)



**Output example:**

![image](https://github.com/user-attachments/assets/ca76eedd-e5ce-4506-9093-aba1f69dbf75)



### Processing and Results
- **Processing**: After uploading your CSV file, our system will automatically execute the necessary Python script in the backend to perform SDOH linkage.
  
- **Downloading Results**: Once processing is complete, you will be able to download the final results directly from the web page.









     
