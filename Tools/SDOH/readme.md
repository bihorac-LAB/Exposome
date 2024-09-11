
# SDoH Repository Documentation
Welcome to the SDoH Repository, which contains scripts designed to map and link geographic data to Social Determinants of Health (SDoH) using various data inputs. Below, you will find detailed documentation for each script, including usage instructions and expected inputs and outputs.

## Scripts Overview

### 1. Address_to_FIPS_SDoH_Mapper.py

#### Description:

This script Processes a CSV file with patient addresses and encounter dates, uses DeGAUSS to geocode addresses to coordinates and FIPS codes, and links encounter data to SDOH database using FIPS codes.

![image](https://github.com/user-attachments/assets/d41ed4a7-da02-4553-b601-174ab13eb717)

#### Required input:
-i：Input file path

-d：Patient encounter start date column name

--columns: Column names for address(if you have separate columns for address please input in this order: street, city, state, zip. If you just have one column for address, input the address column name, eg:address)

#### Example usage:
python Address_to_FIPS_SDoH_Mapper.py -i "./Demo_address.csv" -d visit_start_date --columns street city state zip

python Address_to_FIPS_SDoH_Mapper.py -i "./Demo_address.csv" -d visit_start_date --columns address

#### Sample input file
![image](https://github.com/user-attachments/assets/7f4ebe78-2d75-4c98-a947-0b9bfad27a4e)
![image](https://github.com/user-attachments/assets/0dbfbae9-5be0-4009-b9c7-4389d951fede)
#### Sample output file
![image](https://github.com/user-attachments/assets/404cfe58-c210-44d5-aef2-1a2d1f48a4b0)



### 2. LatLong_to_FIPS_SDoH_Mapper.py 

#### Description:

This script uses DeGAUSS to convert latitude and longitude coordinates from a CSV file into FIPS codes, and links encounter data to SDOH database using FIPS codes.

![image](https://github.com/user-attachments/assets/b620783e-7c62-4c8b-aabf-100552e7b192)

#### Required input：
-i：Input file path

-d：Patient encounter start date column name

-lat: Latitude column name

-long: Longitude column name
#### Example usage:
python LatLong_to_FIPS_SDoH_Mapper.py  -i "./Demo_address_lat.csv"  -d visit_start_date -lat Latitude -long Longitude

#### Sample input file
![image](https://github.com/user-attachments/assets/c38aa3c6-5544-4059-8c7e-eb62f40cb4c9)
#### Sample output file
![image](https://github.com/user-attachments/assets/eb886f75-b751-4d40-b7a0-0625f5cb8dc7)



### 3. FIPS_SDoH_Mapper.py

#### Description:

Inputs a CSV file containing FIPS codes and patient encounter information with date, and links encounter data to SDOH database using FIPS codes.

![image](https://github.com/user-attachments/assets/a881476a-cc69-4984-8616-94acac911210)

#### Required input:
-i：Input file path

-d：Patient encounter start date column name

-f:  FIPS column name
#### Example usage:
python FIPS_SDoH_Mapper.py -i "./Demo_address_fips.csv" -d visit_start_date -f FIPS 
#### Sample input file
![image](https://github.com/user-attachments/assets/3c2e54c6-e377-43cb-ba5a-54bdb9cc0713)
#### Sample output file
![image](https://github.com/user-attachments/assets/67cc429f-8c0d-4518-8277-2b6fb8bf2018)

 


### 4. OMOP_SDOH_mapping.py
#### Description:
This script establishes a connection to an OMOP database using specified credentials and links patient encounters to SDOH data.

![image](https://github.com/user-attachments/assets/0d79814b-4300-4222-b7b0-bd861a200a4c)

#### Required input:
--user: Database username

--password: Database password

--server: Database server

--port: Database port

--database: Database name

#### Example usage:
python OMOP_SDOH_mapping.py --user xxx --password xxx --server xxx --port xxx --database xxx

