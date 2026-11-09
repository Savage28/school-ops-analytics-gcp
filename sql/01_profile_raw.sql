-- Profile the raw layer to measure data quality issues before cleaning
-- 1. Student ID formats: compare distinct raw IDs to the real student count
SELECT
  COUNT(*) AS total_rows,
  COUNT(DISTINCT student_id) AS distinct_raw_ids,
  COUNTIF(STARTS_WITH(student_id, 'S')) AS prefixed_ids,
  COUNTIF(student_id != TRIM(student_id)) AS ids_with_spaces,
  COUNTIF(ENDS_WITH(student_id, '.0')) AS float_ids
FROM raw.students;

-- 2. Attendance status variants: how many spellings of Present/Absent/Tardy?
SELECT status, COUNT(*) AS row_count
FROM raw.attendance
GROUP BY status
ORDER BY row_count DESC;
