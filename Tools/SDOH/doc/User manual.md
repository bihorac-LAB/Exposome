**User Manual: Geocoding Patient Data for SDoH Linkage**

**Note:** This manual does **not** require or share any PHI (Protected Health Information).

---

### **Step 1: Preparing Input Data**
This guide outlines the steps required to prepare input data for linking Social Determinants of Health (SDOH) using geographic information. The Census Tract (FIPS 11 code) is the key geographic identifier used to connect data to the SDOH database. Step 1 is used to prepare the information for generating FIPS11 code, and step 2 is to generate FIPS code using toolkit.

You need to prepare **only ONE** of the following data elements per encounter:

#### **Option 1: Address Information**
You can input either:
- **Format A: Multi-Column Address**
  - Columns: `street`, `city`, `state`, `zip`
- Example:
   
| street | city | state | zip |
|----------|----------|----------|----------|
| 1250 W 16th St | Jacksonville | FL | 32209 |
| 2001 SW 16th St | Gainesville | FL | 32608 |

- **Format B: Single Column Address**
  - Column: `address`
- Example:
   
| address |
|----------|
| 1250 W 16Th St Jacksonville Fl 32209 |
|2001 Sw 16Th St Gainesville Fl 32608 | 

#### **Option 2: Coordinates**
- Columns: `latitude`, `longitude`
- Example:

| latitude | longitude |
|----------|----------|
| 30.353463 | -81.6749 |
| 29.634219 | -82.3433 |

#### **Option 3: Census Tract (FIPS)**
- Column: `FIPS`
- Example:

| FIPS |
|----------|
| 12011080103 |
| 12103026400 | 

> If `FIPS` is available, skip Step 2.

---

### **Step 2: Generate Census Tract (FIPS) Information**

To convert patient location data into Census Tract identifiers (FIPS11), we use a two-step geocoding process powered by [DeGAUSS](https://degauss.org), executed locally via Docker containers.

---

####  Method: DeGAUSS Toolkit (Docker-based)

DeGAUSS consists of two Docker containers:
1. **Geocoder (3.3.0)** — Converts address to latitude/longitude
2. **Census Block Group (0.6.0)** — Converts latitude/longitude to Census Tract FIPS codes

| Step | Purpose                   | Docker Image                                  |
|------|----------------------------|-----------------------------------------------|
| 1    | Address → Coordinates      | `ghcr.io/degauss-org/geocoder:3.3.0`          |
| 2    | Coordinates → FIPS         | `ghcr.io/degauss-org/census_block_group:0.6.0`|

---

### **Case 1: CSV File Input**

Input CSVs must contain a `year` column and **either**:
- `street`, `city`, `state`, `zip` (**Option 1** — Multi-column)
- `address` (**Option 2** — Single column)
- `latitude`, `longitude` (**Option 3** — Coordinates only)

**Run Script Examples:**
```bash
# Option 1: Multi-column address
python Address_to_FIPS.py -i ./your_csv_folder -o 1

# Option 2: Single-column address
python Address_to_FIPS.py -i ./your_csv_folder -o 2

# Option 3: Latitude/Longitude input
python Address_to_FIPS.py -i ./your_csv_folder -o 3
```

**DeGAUSS Docker Commands (Executed Internally):**
```bash
# Step 1: Get Coordinates from Address
docker run --rm -v "ABS_OUTPUT_FOLDER:/tmp" ghcr.io/degauss-org/geocoder:3.3.0 /tmp/<your_preprocessed_input.csv> <threshold>

# Step 2: Get FIPS from Coordinates
docker run --rm -v "ABS_OUTPUT_FOLDER:/tmp" ghcr.io/degauss-org/census_block_group:0.6.0 /tmp/<your_coordinate_output.csv> <year>
```

Replace:
- `ABS_OUTPUT_FOLDER` → absolute path to your output directory
- `<threshold>` → numeric value (e.g. `0.7`)
- `<year>` → either `2010` or `2020`

**Output Structure**

For each input file processed by the script, the following output files are generated:

- `<filename>_with_coordinates.csv` Contains latitude and longitude coordinates appended to the original data. (Generated if coordinates are applicable.)

- `<filename>_with_fips.csv` Contains FIPS codes appended to the original data.

**Packaged Output**

All generated files are compressed into two separate ZIP archives for convenience:

- `output/coordinates_from_address_<timestamp>.zip` Contains all `<filename>_with_coordinates.csv files`.

- `output/geocoded_fips_codes_<timestamp>.zip` Contains all `<filename>_with_fips.csv files.`

> Note: `<timestamp>` is a datetime string indicating when the script was executed (e.g., 20250624_150230).


**Output Columns Description**

| Column         | Description                          |
|----------------|--------------------------------------|
| `Latitude`     | Latitude from geocoder               |
| `Longitude`    | Longitude from geocoder              |
| `geocode_result` | Indicates if geocoding was successful or imprecise |
| `reason`       | Failure reason if applicable         |


**reason Column Values**

Used when geocoding fails or is imprecise. Includes: 

- `Hospital address given` – Detected from known hardcoded hospital addresses 

- `Street missing` – No street info provided 

- `Blank/Incomplete address` – Address is empty or has missing components 

- `Zip missing` – ZIP code not provided 

> Tip: You can improve detection of hospital addresses by adding more known addresses into the hardcoded list in the script. You add that to `Address_to_FIPS.py` at `Tools/SDOH/code/Address_to_FIPS.py` just after you import all the packages at the top of the file.
> Name it `HOSPITAL_ADDRESSES`

---

### **Case 2: OMOP Database Input**

This workflow pulls patient location and visit data from OMOP CDM tables and classifies the records into 3 groups before geocoding:

**Required Tables & Fields:**

| Table              | Required Columns                                      |
|--------------------|------------------------------------------------------|
| `person`           | `person_id`                                          |
| `visit_occurrence` | `visit_occurrence_id`, `visit_start_date`, `visit_end_date`, `person_id` |
| `location`         | `location_id`, `address_1`, `city`, `state`, `zip`, `latitude`, `longitude` |
| `location_history` | `entity_id`, `start_date`, `end_date`               |

 **Required Input for the Python Script**:
- `user`: username for the OMOP database
- `password`: password for the OMOP databse
- `server`: server number
- `port`: port number
- `database`: database name for OMOP

**Run Script Example:**
```bash
python OMOP_to_FIPS.py --user <USERNAME> --password <PASSWORD> --server <HOST> --port <PORT> --database <DBNAME>
```

---

### Verified Generated Output Structure

**OMOP_data/** (raw extracted records)
```
OMOP_data/
├── valid_address/               # Records with address, no lat/lon
├── invalid_lat_lon_address/     # Records missing both address and lat/lon
├── valid_lat_long/              # Records with lat/lon
```

**OMOP_FIPS_result/** (geocoded results)
```
OMOP_FIPS_result/
├── address/
│   ├── address_with_coordinates.zip   # CSVs with lat/lon from address
│   └── address_with_fips.zip          # CSVs with FIPS codes
├── latlong/
│   └── latlong_with_fips.zip          # CSVs with FIPS from coordinates
├── invalid/                           # Usually empty; no usable location data
```

---

### **Step 3: Linking with SDoH Data (Web Platform)**

1. **Register** on the web platform
2. **Upload** your `*_with_fips.zip` from Step 2
3. **Input CSV Must Contain:**
   - `person_id`
   - `visit_occurrence_id`
   - `year`
   - `FIPS`

4. **Result:**
   - A fully linked dataset enriched with SDoH variables based on census tract and year
   - Option to download the result as a CSV

---

### **Appendix: Script Highlights**

#### **`Address_to_FIPS.py` Logic**
- Reads CSV files
- Normalizes address or uses lat/lon
- Runs DeGAUSS Docker container to get:
  - Lat/lon (via `ghcr.io/degauss-org/geocoder`)
  - FIPS (via `ghcr.io/degauss-org/census_block_group`)
- Packages outputs to ZIP

#### **`OMOP_to_FIPS.py` Logic**
- Extracts data from OMOP CDM
- Categorizes into valid/invalid address or coordinates
- Executes FIPS generation like CSV method
- Outputs compressed ZIP folders

---

This completes the geocoding preparation and execution guide for linking SDoH data.
