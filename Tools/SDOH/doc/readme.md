# Geocoding Patient Data for SDoH Linkage

> **Note:** This toolkit does **not** require or share any Protected Health Information (PHI).

This repository provides a reproducible workflow to geocode patient location data and generate Census Tract (FIPS 11-digit) identifiers for linking with Social Determinants of Health (SDoH) datasets.

---

## 📑 Table of Contents
- [Step 1: Preparing Input Data](#step-1-preparing-input-data)
- [Step 2: Get FIPS Code](#step-2-get-fips-code)
- [Step 3: Output Structure](#step-3-output-structure)
- [Step 4: Linking with SDoH Data (Web Platform)](#step-4-linking-with-sdoh-data-web-platform)
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
