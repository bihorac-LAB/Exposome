# Geocoding Patient Data for Exposome Linkage

> **Note:** This toolkit does **not** require or share any Protected Health Information (PHI).

This repository provides a reproducible workflow to geocode patient location data and generate Census Tract (FIPS 11-digit) identifiers for linking with Exposome datasets.

---
## 📑 Table of Contents
- [Overview](#overview)  
- [Input Options](#input-options)  
  - [Option 1: Address](#option-1-address)  
  - [Option 2: Coordinates](#option-2-coordinates)  
  - [Option 3: OMOP CDM](#option-3-omop-cdm)  
- [Usage](#usage)  
  - [Step 1: Prepare Input Data](#step-1-prepare-input-data)  
  - [Step 2: Generate FIPS Codes](#step-2-generate-fips-codes)  
  - [Step 3: Output Structure](#step-3-output-structure)  
  - [Step 4: Link with SDoH Web Platform](#step-4-link-with-sdoh-web-platform)  
- [Appendix](#appendix)  
  - [Geocoding Workflow](#geocoding-workflow)  
  - [Script Highlights](#script-highlights)  
  - [Known Hospital Addresses](#known-hospital-addresses)  

## 📑 Table of Contents
- [Step 1: Preparing Input Data](#step-1-preparing-input-data)
- [Step 2: Get FIPS Code](#step-2-get-fips-code)
- [Step 3: Output Structure](#step-3-output-structure)
- [Step 4: Linking with Exposome Data (Web Platform)](#step-4-linking-with-exposome-data-web-platform)
- [Appendix](#appendix)
  - [How Does Geocoding Work?](#how-does-geocoding-work)
  - [Script Highlights](#script-highlights)

---

## 📌 Overview
This toolkit links patient data to SDoH databases via Census Tract (FIPS-11) codes.  

It supports:  
- Address-based geocoding  
- Latitude/Longitude geocoding  
- Extraction from OMOP CDM databases  

The backend uses [DeGAUSS](https://degauss.org) Docker containers for geocoding.

---

## Input Options
## Step 1: Preparing Input Data

You need to prepare **only ONE** of the following data elements per encounter.  
The key geographic identifier is the **Census Tract (FIPS 11 code)**.

### Option 1: Address Information
- **Format A: Multi-Column Address**

| street       | city        | state | zip   |
|--------------|------------|-------|-------|
| 1250 W 16th St | Jacksonville | FL    | 32209 |
| 2001 SW 16th St | Gainesville  | FL    | 32608 |

- **Format B: Single Column Address**

| address |
|---------|
| 1250 W 16th St Jacksonville FL 32209 |
| 2001 SW 16th St Gainesville FL 32608 |

> **Tip:** Street **and** ZIP are required. Missing fields may result in imprecise geocoding.

### Option 2: Coordinates

| latitude   | longitude |
|------------|-----------|
| 30.353463  | -81.6749  |
| 29.634219  | -82.3433  |

### Option 3: OMOP CDM Tables

| Table              | Required Columns |
|--------------------|------------------------------------------------------|
| person             | person_id                                            |
| visit_occurrence   | visit_occurrence_id, visit_start_date, visit_end_date, person_id |
| location           | location_id, address_1, city, state, zip, latitude, longitude |
| location_history   | entity_id, start_date, end_date                      |

---

## Step 2: Get FIPS Code

> Container: `prismaplab/exposome-geocoder:1.0.2`  
> Ensure Docker Desktop is running.  
> On Windows, run commands from WSL root.

### For CSV Files (Option 1 & Option 2)

```bash
docker run -it --rm \
  -v "$(pwd)":/workspace \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e HOST_PWD="$(pwd)" \
  -w /workspace \
  prismaplab/exposome-geocoder:1.0.2 \
  /app/code/Address_to_FIPS.py -i <input_folder>
```

### For OMOP Database (Option 3)

```bash
docker run -it --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$(pwd)":/workspace \
  -e HOST_PWD="$(pwd)" \
  -w /workspace \
  prismaplab/exposome-geocoder:1.0.2 \
  /app/code/OMOP_to_FIPS.py \
    --user <your_username> \
    --password <your_password> \
    --server <server_address> \
    --port <port_number> \
    --database <database_name>
```

---

## Step 3: Output Structure

### For CSV Input (Option 1 & 2)
- `<filename>_with_coordinates.csv` — input + latitude/longitude  
- `<filename>_with_fips.csv` — input + FIPS codes  

Packaged outputs:
> All generated files are compressed into two separate ZIP archives for convenience:
- `output/coordinates_from_address_<timestamp>.zip`
- `output/geocoded_fips_codes_<timestamp>.zip`
> Note: <timestamp> is a datetime string indicating when the script was executed (e.g., 20250624_150230).

**Output Columns**

| Column        | Description                                  |
|---------------|----------------------------------------------|
| Latitude      | Latitude from geocoder                       |
| Longitude     | Longitude from geocoder                      |
| geocode_result| Status: `geocoded` or `Imprecise Geocode`    |
| reason        | Failure reason (e.g., missing street/ZIP)    |

### For OMOP Input (Option 3)

```
OMOP_data/
├── valid_address/               # Records with address, no lat/lon
├── invalid_lat_lon_address/     # Records missing both address and lat/lon
├── valid_lat_long/              # Records with lat/lon

OMOP_FIPS_result/
├── address/
│   ├── address_with_coordinates.zip   # CSVs with lat/lon from address
│   └── address_with_fips.zip          # CSVs with FIPS codes
├── latlong/
│   └── latlong_with_fips.zip          # CSVs with FIPS from coordinates
├── invalid/                           # Usually empty; no usable location data
```
---

## Step 4: Linking with Exposome Data (Web Platform)

1. Register at [https://exposome.rc.ufl.edu](https://exposome.rc.ufl.edu/)  
2. Upload your `*_with_fips.zip` file  
3. Input CSV must contain:  
   - `person_id`  
   - `visit_occurrence_id`  
   - `year`  
   - `FIPS`
4. Select the dataset you want to link it to
6. Download linked dataset with SDoH variables

---

## Appendix

### How Does Geocoding Work?

The toolkit uses [DeGAUSS](https://degauss.org) with two Docker containers:

| Step | Purpose                 | Docker Image                                  |
|------|-------------------------|-----------------------------------------------|
| 1    | Address → Coordinates   | `ghcr.io/degauss-org/geocoder:3.3.0`          |
| 2    | Coordinates → FIPS      | `ghcr.io/degauss-org/census_block_group:0.6.0`|

Example commands:

```bash
# Step 1: Get Coordinates
docker run --rm -v "ABS_OUTPUT_FOLDER:/tmp" ghcr.io/degauss-org/geocoder:3.3.0 /tmp/<your_input.csv> <threshold>

# Step 2: Get FIPS
docker run --rm -v "ABS_OUTPUT_FOLDER:/tmp" ghcr.io/degauss-org/census_block_group:0.6.0 /tmp/<your_coordinate_output.csv> <year>
```

- `ABS_OUTPUT_FOLDER` → absolute path to output directory  
- `<threshold>` → match threshold (e.g., 0.7)  
- `<year>` → 2010 or 2020  

### Script Highlights

**Address_to_FIPS.py**
- Reads CSV
- Normalizes address or uses lat/lon
- Runs DeGAUSS Docker container to get:
     - Lat/lon (via ghcr.io/degauss-org/geocoder)
     - FIPS (via ghcr.io/degauss-org/census_block_group)
- Packages outputs into ZIP

**OMOP_to_FIPS.py**
- Extracts OMOP CDM data
- Categorizes into valid/invalid address or coordinates
- Runs FIPS generation
- Outputs compressed ZIP folders

---

# Geocoding Preparation and Execution Guide

This guide outlines the scripts, workflows, and Docker-based DeGAUSS toolkit used for generating Census Tract (FIPS) information from patient data.

---

## Generate Census Tract (FIPS) Information

To convert patient location data into Census Tract identifiers (**FIPS11**), we use a two-step geocoding process powered by [DeGAUSS](https://degauss.org), executed locally via Docker containers.

### Method: DeGAUSS Toolkit (Docker-based)

DeGAUSS consists of two Docker containers:

1. **Geocoder (3.3.0)** — Converts address to latitude/longitude  
2. **Census Block Group (0.6.0)** — Converts latitude/longitude to Census Tract FIPS codes  

| Step | Purpose                  | Docker Image                                     |
|------|--------------------------|--------------------------------------------------|
| 1    | Address → Coordinates    | `ghcr.io/degauss-org/geocoder:3.3.0`             |
| 2    | Coordinates → FIPS       | `ghcr.io/degauss-org/census_block_group:0.6.0`   |

---

### DeGAUSS Docker Commands (Executed Internally)

```bash
# Step 1: Get Coordinates from Address
docker run --rm -v "ABS_OUTPUT_FOLDER:/tmp" \
  ghcr.io/degauss-org/geocoder:3.3.0 \
  /tmp/<your_preprocessed_input.csv> <threshold>

# Step 2: Get FIPS from Coordinates
docker run --rm -v "ABS_OUTPUT_FOLDER:/tmp" \
  ghcr.io/degauss-org/census_block_group:0.6.0 \
  /tmp/<your_coordinate_output.csv> <year>
```

**Replace values:**
- `ABS_OUTPUT_FOLDER` → absolute path to your output directory  
- `<threshold>` → numeric value (e.g., `0.7`)  
- `<year>` → either `2010` or `2020`  

---

## Appendix: Script Highlights

### Address_to_FIPS.py Logic
This script handles CSV-based input:  
- Reads CSV files  
- Normalizes addresses or uses lat/lon  
- Runs DeGAUSS Docker containers to generate:  
  - Latitude/Longitude (via `ghcr.io/degauss-org/geocoder`)  
  - FIPS codes (via `ghcr.io/degauss-org/census_block_group`)  
- Packages outputs into a compressed ZIP  

---

### OMOP_to_FIPS.py Logic
This script integrates directly with **OMOP CDM**:  
- Extracts data from OMOP CDM  
- Categorizes into valid/invalid address or coordinates  
- Executes FIPS generation (same as CSV workflow)  
- Outputs compressed ZIP folders  

---

✅ This completes the geocoding preparation and execution guide for linking SDoH data.
