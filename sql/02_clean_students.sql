-- 02_clean_students.sql
-- Normalize IDs and grades, then keep one row per student.
CREATE OR REPLACE TABLE clean.students AS
WITH normalized AS (
  SELECT
    -- "S100234", " 100234 ", "100234.0" -> 100234
    SAFE_CAST(REGEXP_EXTRACT(TRIM(student_id), r'\d+') AS INT64) AS student_id,
    TRIM(first_name) AS first_name,
    TRIM(last_name) AS last_name,
    -- "Grade 6" -> 6; blank grade falls back to the homeroom ("6A" -> 6)
    COALESCE(
      SAFE_CAST(REGEXP_EXTRACT(grade, r'\d+') AS INT64),
      SAFE_CAST(LEFT(TRIM(homeroom), 1) AS INT64)
    ) AS grade,
    TRIM(homeroom) AS homeroom,
    UPPER(TRIM(ell_status)) = 'Y' AS is_ell
  FROM raw.students
)
SELECT *
FROM normalized
WHERE student_id IS NOT NULL
QUALIFY ROW_NUMBER() OVER (PARTITION BY student_id ORDER BY grade DESC) = 1;
