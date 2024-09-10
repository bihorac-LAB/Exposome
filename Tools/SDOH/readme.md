
# CHoRUS

## LatLong_to_FIPS_SDoH_Mapper.py
### What does the script do? - 
Input a csv file with latitude longitude and patient encounter date information. Uses degauss to convert the lat long information to fips code, also links to SDOH.
### instructions on how to run the script
#### required input
-i：Input file path
-d：Patient encounter start date column name
-lat: Latitude column name
-long: Longitude column name
#### Example:
python LatLong_to_FIPS_SDoH_Mapper.py -i -i "C:/Users/j.yu1/Desktop/SDOH/Demo_address_lat.csv"  -d visit_start_date -lat Latitude -long Longitude
### Output - what does the script return? 
Sample input file
Sample output file

## FIPS_SDoH_Mapper.py
### what does the script do?
Input a csv file with FIPS and patient encounter date information and Link to SDOH database.
### instructions on how to run the script
#### required input
-i：Input file path
-d：Patient encounter start date column name
-f: FIPS column name
#### Example:
python FIPS_SDoH_Mapper.py -i "C:/Users/j.yu1/Desktop/SDOH/Demo_address_fips.csv" -d visit_start_date -f FIPS 
### Output - what does the script return? 
Sample input file
Sample output file

 
## Address_to_FIPS_SDoH_Mapper.py
### what does the script do?
Input a csv file with patients' street assdree and patient encounter date information. Uses degauss to convert the address to coordinates and fips code, also links to SDOH database.
### instructions on how to run the script
#### required input
-i：Input file path
-d：Patient encounter start date column name
--columns: Column names for address(if you have separate columns for address please input in this order: street, city, state, zip. If you just have one column fro address, just input the address column name, eg:address)')
#### Example:
python Address_to_FIPS_SDoH_Mapper.py -i "C:/Users/j.yu1/Desktop/work/SDOH/phase2/Mapping/python code/Demo_address.csv" -d visit_start_date --columns street city state zip
python Address_to_FIPS_SDoH_Mapper.py -i "C:/Users/j.yu1/Desktop/work/SDOH/phase2/Mapping/python code/Demo_address.csv" -d visit_start_date --columns address
### Output - what does the script return? 
Sample input file
Sample output file
 
## OMOP_SDOH_mapping.py
### what does the script do?
Input the login information to the OMOP databse and Link patient encounter to SDOH database.
### instructions on how to run the script
#### required input
--user: Database username
--password: Database password
--server: Database server
--port: Database port
--database: Database name
#### Example:
python OMOP_SDOH_mapping.py --user jyu --password xxx --server xxx --port xxx --database IC3_INPATIENT_PIPELINE_2024
### Output - what does the script return? 
Sample input file
Sample output file
