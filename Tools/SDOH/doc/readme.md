# Geocoding Patient Data for Exposome Linkage

> **Note:** This toolkit does **not** require or share any Protected Health Information (PHI).

This repository provides a reproducible workflow to geocode patient location data and generate Census Tract (FIPS 11-digit) identifiers for linking with Exposome datasets.

---

## 🚀 Quickstart

For CSV input (addresses or coordinates):

```bash
docker run -it --rm \
  -v "$(pwd)":/workspace \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e HOST_PWD="$(pwd)" \
  -w /workspace \
  prismaplab/exposome-geocoder:1.0.2 \
  /app/code/Address_to_FIPS.py -i <input_folder>
```
- Replace `<input_folder>` with the path to your CSV folder.  
- Outputs are saved in the `output/` directory.  
- Upload the `*_with_fips.zip` file to [https://exposome.rc.ufl.edu](https://exposome.rc.ufl.edu) to link with Exposme datasets.
---

## 📑 Table of Contents
- [Step 1: Preparing Input Data](#step-1-preparing-input-data)
- [Step 2: Get FIPS Code](#step-2-get-fips-code)
- [Step 3: Output Structure](#step-3-output-structure)
- [Step 4: Linking with Exposome Data (Web Platform)](#step-4-linking-with-exposome-data-web-platform)
- [Appendix](#appendix)
  - [How Does Geocoding Work?](#how-does-geocoding-work)
  - [Script Highlights](#script-highlights)

---

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
- `output/coordinates_from_address_<timestamp>.zip`
- `output/geocoded_fips_codes_<timestamp>.zip`

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

## Step 4: Linking with SDoH Data (Web Platform)

1. Register at [https://exposome.rc.ufl.edu](https://exposome.rc.ufl.edu/)  
2. Upload your `*_with_fips.zip` file  
3. Input CSV must contain:  
   - `person_id`  
   - `visit_occurrence_id`  
   - `year`  
   - `FIPS`  
4. Download linked dataset with SDoH variables

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
- Runs DeGAUSS (geocoder + census block group)
- Packages outputs into ZIP

**OMOP_to_FIPS.py**
- Extracts OMOP CDM data
- Categorizes records
- Runs FIPS generation
- Outputs compressed ZIP folders

---
