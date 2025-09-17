# Exposome Data Linkage Tool

## Background and Introduction

Exposome data refers to the collection, analysis, and integration of diverse data types representing an individual's or population's exposure to environmental and lifestyle factors, including social determinants of health (SDoH). SDoH and environmental datasets are increasingly important for clinical research worldwide. However, since these datasets are collected and shared by different government organizations, research institutes, and other entities, there is no unified database for researchers to quickly access, visualize, and download data in a reliable manner.

This project aims to provide solutions for the following areas:

1. A GIS-enabled database  
2. Rapid data ingestion with minimal manual effort  
3. A lightweight web application for data cataloging, visualization, and analysis  
4. Local toolkits for geocoding addresses to coordinates or FIPS codes  

---

## Database Design

We selected **PostgreSQL** with the **PostGIS** extension to meet our requirements. Inspired by the [OHDSI GIS Working Group](https://github.com/OHDSI/GIS), we designed the database with fundamental components and tables. Since SDoH and environmental datasets are heavily geospatial, we ingested Census Tract, ZCTA, County, and State shapefiles into the database and linked variable tables to these geo-tables.

* **`data_source` table:** Stores metadata from all source datasets, including SDoH datasets, environmental data, and geometry data.  
* For each SDoH and environmental dataset, two tables are created:
  - **`variable_index` table:** Records key attributes and properties of each variable  
  - **`variable_value` table:** Stores the values of each variable for geocoded locations  
* Geometry data is stored in dedicated tables, linked to variables via geoCodes such as FIPS, ZCTA, COUNTY, and STATE  

![Database Design](./assets/Database%20design.png)

---

## Toolkits

Since most SDoH datasets use Census Tract (FIPS) as the geographic boundary, we developed **toolkits** to help investigators geocode addresses to coordinates or FIPS codes.

To protect patient privacy, geocoding must be executed **locally** using [DeGAUSS](https://degauss.org). Scripts are provided for both CSV file processing and direct extraction from OMOP CDM databases.

> If your institution already provides geocoding services, you may skip these toolkits.

Detailed execution instructions are available [here](https://github.com/bihorac-LAB/Exposome/blob/main/Tools/SDOH/doc/UserManual.md).

### Demo Videos
- [FIPS Generation](#)  
- [Exposome Linkage to Other Datasets](https://www.loom.com/share/bc4097b0d3db4f8f9132a06a49c17e71?sid=ad9671c1-6535-4bc9-b893-7e917efbcf75)

---

## Web Application

We created a [web application](https://exposome.rc.ufl.edu/) that provides investigators access to:

- Data catalog  
- Exposome data linkage tool  
- Data visualization tool  

In the next release, a basic data analysis tool will also be available.

The web application is deployed on [HiPerGator](https://www.rc.ufl.edu/about/hipergator/) PubApps.  

![External Investigator Workflow](./assets/External%20investigator%20workflow.png)
