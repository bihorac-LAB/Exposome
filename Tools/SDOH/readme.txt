
CHoRUS
  Tools
    SDOH
      LatLong_to_FIPS_SDoH_Mapper - folder
          LatLong_to_FIPS_SDoH_Mapper.py
          requirements.txt
          Dockerfile
      FIPS_SDoH_Mapper  - folder
        FIPS_SDoH_Mapper.py
        requirements.txt
        Dockerfile
      Address_to_FIPS_SDoH_Mapper - folder
        Address_to_FIPS_SDoH_Mapper.py
        requirements.txt
        Dockerfile
      OMOP_SDOH_mapping - folder
        OMOP_SDOH_mapping.py
        requirements.txt
        Dockerfile
      README.md - file

 
Degauss_fips_sdoh.py - LatLong_to_FIPS_SDoH_Mapper.py
 
What does the script do? - Write it here, uses degauss to convert the lat long information to fips code, also links to SDOH
Input to this file is a csv file with latitude longitude and patient encounter date information
Output - what does the script return? 
Sample input file
Sample output file
instructions on how to run the script
python scriptname ip1 ip2 
create a requirements.txt file, docker file for each script
 
Link_to_SDoH.py - FIPS_SDoH_Mapper.py
what does the script do?
Input - fips and encounter date 
Output - link to SDOH
Sample input
Sample output
instructions on how to run the script
python scriptname ip1 ip2 
create a requirements.txt file, docker file for each script
 
Full_degauss_linkage.py - Address_to_FIPS_SDoH_Mapper.py
what does it do? - address - lat long- fips - sdoh linkage (using degauss)
Input - address and ecounter date
Output - link to SDOH
Sample input
sample output
instructions on how to run the script
python scriptname ip1 ip2 
create a requirements.txt file, docker file for each script
 
OMOP_SDOH_mapping.py- OMOP database to SDOH 
Input- datbaase
Output - sdoh linkage
what does it do? - write cases. case1: if addrss, case2: if lat long, ...
sample output
instructions on how to run the script
python scriptname ip1 ip2 
create a requirements.txt file, docker file for each script
has context menu
