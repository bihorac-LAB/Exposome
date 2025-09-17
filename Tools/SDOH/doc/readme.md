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
  - [Step 4: Link with Exposome Web Platform](#step-4-link-with-exposome-web-platform)  
- [Appendix](#appendix)  
  - [Geocoding Workflow](#geocoding-workflow)  
  - [Script Highlights](#script-highlights)  
  - [Known Hospital Addresses](#known-hospital-addresses)  
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

You need to prepare **only ONE** of the following data elements per encounter.  

### Option 1: Address
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

### Option 3: OMOP CDM

| Table              | Required Columns |
|--------------------|------------------------------------------------------|
| person             | person_id                                            |
| visit_occurrence   | visit_occurrence_id, visit_start_date, visit_end_date, person_id |
| location           | location_id, address_1, city, state, zip, latitude, longitude |
| location_history   | entity_id, start_date, end_date                      |

---
## 🚀 Usage
## Step 1: Prepare Input Data
You need to prepare **only ONE** of the data elements as indicated under the [Input Options](#input-options) per encounter.  
Place your input CSVs or ensure DB access for OMOP.

## Step 2: Generate FIPS Codes
> Container: `prismaplab/exposome-geocoder:1.0.2`  
> Ensure Docker Desktop is running.  
> On Windows, run commands from WSL root.

### CSV Input (Option 1 & 2)

```bash
docker run -it --rm \
  -v "$(pwd)":/workspace \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e HOST_PWD="$(pwd)" \
  -w /workspace \
  prismaplab/exposome-geocoder:1.0.2 \
  /app/code/Address_to_FIPS.py -i <input_folder>
```

### OMOP Input (Option 3)

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

### CSV Input (Option 1 & 2)
Generated per file:
  - `<filename>_with_coordinates.csv` — input + latitude/longitude  
  - `<filename>_with_fips.csv` — input + FIPS codes  

Zipped outputs:
> All generated files are compressed into two separate ZIP archives for convenience:
  - `output/coordinates_from_address_<timestamp>.zip`
  - `output/geocoded_fips_codes_<timestamp>.zip`
> Note: <timestamp> is a datetime string indicating when the script was executed (e.g., 20250624_150230).

**Output Columns Description**

| Column           | Description                                                                 |
|------------------|-----------------------------------------------------------------------------|
| `Latitude`       | Latitude returned from the geocoder                                         |
| `Longitude`      | Longitude returned from the geocoder                                        |
| `geocode_result` | Outcome of geocoding — `geocoded` for successful matches, `Imprecise Geocode` if not precise |
| `reason`         | Failure reason if applicable (see [Reason Column Values](#reason-column-values)) |

#### Reason Column Values
Used when geocoding fails or is imprecise. Possible values include:

- **Hospital address given** – Detected from known hardcoded hospital addresses.  
- **Street missing** – No street info provided.  
- **Blank/Incomplete address** – Address is empty or has missing components.  
- **Zip missing** – ZIP code not provided.  

#### **Tip: Improving Hospital Address Detection**
> Define them under the variable HOSPITAL_ADDRESSES:
>    Add them in `Address_to_FIPS.py` located at `Tools/SDOH/code/Address_to_FIPS.py`, just after importing all packages.

## Note on `HOSPITAL_ADDRESSES` Format

When adding hospital addresses to the `HOSPITAL_ADDRESSES` set in `Address_to_FIPS.py`, ensure each address:

- Is written as a full, single-line string.  
- Uses only lowercase letters and numbers.  
- Has no commas or special characters.  
- Fields are separated by single spaces.  
---
### OMOP Input (Option 3)

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

## Step 4: Link with Exposome Web Platform

1. Register at [https://exposome.rc.ufl.edu](https://exposome.rc.ufl.edu/)  
2. Upload `*_with_fips.zip` file obtained from Step 3 
3. Input CSV must contain:  
   - `person_id`  
   - `visit_occurrence_id`  
   - `year`  
   - `FIPS`
4. Select the dataset you want to link it to
6. Download enriched dataset with SDoH variables
---

## Appendix

### Geocoding Workflow
This guide outlines the scripts, workflows, and Docker-based DeGAUSS toolkit used for generating Census Tract (FIPS) information from patient data.
To convert patient location data into Census Tract identifiers (**FIPS11**), we use a two-step geocoding process powered by [DeGAUSS](https://degauss.org), executed locally via Docker containers.

#### Method: DeGAUSS Toolkit (Docker-based)

DeGAUSS consists of two Docker containers:

1. **Geocoder (3.3.0)** — Converts address to latitude/longitude  
2. **Census Block Group (0.6.0)** — Converts latitude/longitude to Census Tract FIPS codes  

| Step | Purpose                  | Docker Image                                     |
|------|--------------------------|--------------------------------------------------|
| 1    | Address → Coordinates    | `ghcr.io/degauss-org/geocoder:3.3.0`             |
| 2    | Coordinates → FIPS       | `ghcr.io/degauss-org/census_block_group:0.6.0`   |

---

#### DeGAUSS Docker Commands (Executed Internally)

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

#### Script Highlights

##### Address_to_FIPS.py Logic
This script handles CSV-based input:
- Reads CSV files
- Normalizes address or uses lat/lon
- Runs DeGAUSS Docker container to generate:
     - Latitude/Longitude (via `ghcr.io/degauss-org/geocoder`)
     - FIPS codes(via `ghcr.io/degauss-org/census_block_group`)
- Packages outputs into ZIP

##### OMOP_to_FIPS.py Logic
This script integrates directly with **OMOP CDM**: 
- Extracts OMOP CDM data
- Categorizes into valid/invalid address or coordinates
- Executes FIPS generation (same as CSV workflow) 
- Packages outputs into ZIP
---
