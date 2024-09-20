# User Manual
*Note: Please do not share any PHI information*

## Step 1: Preparing Input Data

This guide outlines the steps required to prepare input data for linking Social Determinants of Health (SDOH) using geographic information. The Census Tract (FIPS 11 code) is the key geographic identifier used to connect data to the SDOH database. Step 1 is used to prepare the information for generating FIPS11 code, and step 2 is to generate FIPS code using toolkit. Users need to prepare only **ONE** of the following data types for each encounter: address, coordinates, or census tract information.

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
- **Columns**: `street`, `city`, `state`, `zip`
- **Example**:
   
| street | city | state | zip |
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
| 12103026400 | 


**Note**:  If you already have Census tract information for patients, you can skip preparing coordinate information.

## Step 2: Using Toolkit to Retrieve Census Tract Information
### Case 1: csv format

![image](https://github.com/user-attachments/assets/a1c5b366-dd78-4173-8ae7-33537e2a1bbc)

 **Input CSV File Should Contain**:
- Patient encounter ID (e.g., 12345)
- Patient encounter year (e.g., 2024)
- Address or coordinates information (refer to Step 1 for details)

**Python scripts input:**

- -i：Input file path *(required)*

- -y：Patient encounter year  *(required)*

- --columns: Column names for address(if you have separate columns for address please input in this order: street, city, state, zip. If you just have one column for address, input the address column name, eg:address)  *(optional)*

- -lat: Latitude column name *(optional)*

- -long: Longitude column name *(optional)*

**Example usage:**

*option 1:*

python Address_to_FIPS.py -i "./Demo_address.csv" -d year --columns street city state zip

![image](https://github.com/user-attachments/assets/882367f2-5f6b-4f0d-91de-c8c5a232d7f9)


*option 2:*

python Address_to_FIPS.py -i "./Demo_address.csv" -d year --columns address

![image](https://github.com/user-attachments/assets/3c0129da-7ce2-411d-9b6a-ea5d67532fac)


*option 3:*

python Address_to_FIPS.py -i "./Demo_address.csv" -d year -lat latitude -long longitude

![image](https://github.com/user-attachments/assets/345fc88a-5eac-4a49-88ee-d067a700b97c)


**Sample output:**

*option 1:*

![image](https://github.com/user-attachments/assets/58a055d5-d634-4d99-bac1-b3a6dd1db140)


*option 2:*

![image](https://github.com/user-attachments/assets/caea7ea3-bf40-46f2-8565-3689bcc24620)


*option 3:*

![image](https://github.com/user-attachments/assets/bbd9e960-ffdb-4c19-aa1e-fe929e8a3221)


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

**Example usage:**

python OMOP_to_FIPS.py --user xxx --password xxx --server xxx --port xxx --database xxx

**Sample output:**

![image](https://github.com/user-attachments/assets/17d6285d-0491-418b-9e81-03bd19eccfc1)

## Special case


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

**Example input**:

![image](https://github.com/user-attachments/assets/9e56aa19-7406-400a-9064-51852be48f37)


**Example output**:

![image](https://github.com/user-attachments/assets/39c02650-151b-4577-aa8f-38f8800bb223)




### Processing and Results
- **Processing**: After uploading your CSV file, our system will automatically execute the necessary Python script in the backend to perform SDOH linkage.
  
- **Downloading Results**: Once processing is complete, you will be able to download the final results directly from the web page.

### Additional Guidance
For further assistance or troubleshooting, refer to our [help section](#) or contact support.








     
