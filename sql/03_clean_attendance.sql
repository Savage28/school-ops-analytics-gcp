-- 03_clean_attendance.sql
-- Normalize IDs, dates, and status codes; remove duplicate scans.
CREATE OR REPLACE TABLE clean.attendance AS
WITH normalized AS (
  SELECT
    SAFE_CAST(REGEXP_EXTRACT(TRIM(student_id), r'\d+') AS INT64) AS student_id,
    -- handles both "2025-09-04" and "09/04/2025"
    COALESCE(
      SAFE.PARSE_DATE('%Y-%m-%d', TRIM(date)),
      SAFE.PARSE_DATE('%m/%d/%Y', TRIM(date))
    ) AS attendance_date,
    CASE
      WHEN UPPER(TRIM(status)) IN ('PRESENT', 'P') THEN 'Present'
      WHEN UPPER(TRIM(status)) IN ('ABSENT', 'A', 'ABS') THEN 'Absent'
      WHEN UPPER(TRIM(status)) IN ('TARDY', 'T', 'LATE') THEN 'Tardy'
    END AS status
  FROM raw.attendance
)
SELECT *
FROM normalized
WHERE student_id IS NOT NULL
QUALIFY ROW_NUMBER() OVER (PARTITION BY student_id, attendance_date) = 1;
