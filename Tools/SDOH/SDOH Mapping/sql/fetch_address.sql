 WITH patient AS (
                SELECT p.person_id, v.visit_occurrence_id, v.visit_start_date, v.visit_end_date
                FROM IC3_INPATIENT_PIPELINE_2024.CDM.PERSON p
                LEFT JOIN IC3_INPATIENT_PIPELINE_2024.CDM.VISIT_OCCURRENCE v ON p.person_id = v.person_id),
            address AS (
                SELECT entity_id, L.location_id, L.address_1, L.city, L.state, L.zip, L.county, L.latitude, L.longitude, L.FIPS, LS.start_date, LS.end_date
                FROM LOCATION L LEFT JOIN LOCATION_HISTORY LS ON L.location_id = LS.location_id)
            SELECT person_id, visit_occurrence_id, visit_start_date, visit_end_date, address_1, city, state, zip, county, latitude, longitude
            FROM patient p
            LEFT JOIN address a ON p.person_id = a.entity_id
            WHERE p.visit_start_date BETWEEN a.start_date AND a.end_date
              AND p.visit_end_date BETWEEN a.start_date AND a.end_date
              AND visit_start_date >= '2012-01-01'
              AND (LTRIM(RTRIM(ISNULL(a.latitude, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))
              AND (LTRIM(RTRIM(ISNULL(a.longitude, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))
              AND NOT (LTRIM(RTRIM(ISNULL(a.address_1, ''))) IN ('', 'na', 'null', 'none', 'nan', '0', 'n/a', ' '))