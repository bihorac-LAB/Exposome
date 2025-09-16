
# Exposome Data Linkage Tool

[Demo](https://www.loom.com/share/bc4097b0d3db4f8f9132a06a49c17e71?sid=ad9671c1-6535-4bc9-b893-7e917efbcf75)
## Background and Introduction

Exposome data refers to the collection, analysis, and integration of diverse data types to represent an individual's or population's exposure to various environmental and lifestyle factors, including social determinants of health (SDOH). The SDoH and environmental datasets are getting more and more popular for clinical research and highly needed by researchers around the world. However, because the various datasets are collected and shared by different government organizations, research institutes and so on, there is lack of a combined database for researchers to check, visualize and download data in a quick and reliable manner. 

So we started the journey and tried to provide a solution for below areas:

1. A GIS database 
2. Quick data ingestion with limited manual jobs
3. A slim web application for data catalog, visualization and even analysis
4. A local running toolkits for geocoding

## Database design 
We selected PostgreSQL database and GIS extension to fulfill our requests. Inspired by [OHDSI GIS working group](https://github.com/OHDSI/GIS), we designed our database with the most fundamental components and tables. As SDoH and environmental datasets are highly involved with geo-information, we ingested the Census Tract, ZCTA, County and States shapefiles into the database and link the variable tables with the geo-tables.

* `data_source` table is used to store significant metadata from all source datasets includes SDoH datasets, environmental data and geomentry data. 

[placeholder of a metadata table]

* For each SDoH and environmental data, there are two tables generated
  - `variable_index table`, which is applied to record the important attributes /properties of each variable 
  - `variable_value table`, which is applied to store the values of the variable for each geocoded locations

* For each geometry data, we stored them as a single table to link with variables through geoCodes such as FIPS, ZCTA, COUNTY and STATE. 
![database design](./assets/Database%20design.png)

## Toolkits

Since the most SDoH datasets have the Census Tract(FIPS) as boundary type, the toolkits are developed for investigators to geocode the source address to coordinates or FIPS codes. 

To maintain the privacy of patient's address, investigators need to execute the geocoding toolkits locally with the help of [DeGauss](https://degauss.org). 
We prepared the scripts for both file processing and fetch data directly from OMOP databases.

> If your institute already provides the geocoding service, please ignore the toolkit.

Detailed execution instructions are recorded at [here](https://github.com/bihorac-LAB/Exposome/blob/main/Tools/SDOH/doc/User%20manual.md)

## Web Application

We created a web application to provide the investigators with the access to :
- data catalog
- Exposome data linkage tool
- data visualization tool 

In the next release, we are planning to provide a basic data analyzer tool.

The web application is deployed at [HiPerGator](https://www.rc.ufl.edu/about/hipergator/) PubApps 

![workflow](./assets/External%20investigator%20workflow.png)


# Docker Run Commands for `exposome-geocoder-pipeline`

[Walkthrough video on how to run](https://www.loom.com/share/90ee845b3fd94af398e17d91e4868abc?sid=fa19691e-f185-451c-bdb8-bbf3d8ff1bb3)

## Container Name:
`omerkahveciuf/exposome-geocoder:1.0.1`

## Pre-requisite:
- **docker Desktop** - make sure it is running.
- **UF health VPN** - Make sure you are connected to UF health VPN for OMOP script.

> **Note:** For Windows systems, run the commands from WSL root  
> **Note:** Make sure your `input_folder` is in the same directory as your working directory!

---

## Run Commands

### Run `Address_to_FIPS.py`:
```bash
docker run -it --rm \
  -v "$(pwd)":/workspace \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e HOST_PWD="$(pwd)" \
  -w /workspace \
  omerkahveciuf/exposome-geocoder:1.0.1 \
  /app/code/Address_to_FIPS.py -i <input_folder>
```
Replace input_folder with the input folder storing your data.

### Run `OMOP_to_FIPS.py`:
```bash
docker run -it --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$(pwd)":/workspace \
  -e HOST_PWD="$(pwd)" \
  -w /workspace \
  omerkahveciuf/exposome-geocoder:1.0.1 \
  /app/code/OMOP_to_FIPS.py \
    --user <your_username>\
    --password <your_password> \
    --server <server_address> \
    --port <port_number> \
    --database <database_name>
```


