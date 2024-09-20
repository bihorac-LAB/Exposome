
# SDoH and Environmental Database and Toolkits

## Background and Introduction

The SDoH (Social Determints of Health) and environmental datasets are getting more and more popular for clinical research and highly needed by researchers around the world. However, because the various datasets are collected and shared by different government organizations, research institutes and so on, there is lack of a combined database for researchers to check, visualize and download data in a quick and reliable manner. 

So we started the journey and tried to provide a solution for below areas:

1. A GIS database 
2. Quick data ingestion with limited manual jobs
3. A slim web application for data catalog, visualization and even analysis
4. A local running toolkits for geocoding

## Database design 
We seletced PostgreSQL database and GIS extension to fulfill our requests. Inspired by OHDSI GIS working group, we designed our database with the most fundmental components and tables. As SDoH and environmental datasets are highly involved with geo-information, we ingested the Census Tract, ZCTA, County and States shapefiles into the database and link the variable tables with the geo-tables.

* `data_source` table is used to store significant metadata from all source datasets includes SDoH datasets, environmental data and geomentry data. 

[placeholder of a metadata table]

* For each SDoH and environmental data, there are two tables generated
  - `variable_index table`, which is applied to record the important attributes /properties of each variable 
  - `variable_value table`, which is applied to store the values of the variable for each geocoded locations

* For each geometry data, we stored them as a single table to link with variables through geoCodes such as FIPS, ZCTA, COUNTY and STATE. 
![database design](./assets/Database%20design.png)

## Toolkits

To maintain the privacy of patient's address, investigators need to execute the geocoding toolkits locally with the help of DeGauss. 
We prepared the scripts for both file processing and fetch data directly from OMOP databases.

[more details]

## Web Application

[more details]

![workflow](./assets/External%20investigator%20workflow.png)

