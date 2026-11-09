-- 04_validate_clean.sql
SELECT 'students' AS check_name, COUNT(*) AS actual, 500 AS expected FROM clean.students
UNION ALL
SELECT 'attendance rows', COUNT(*), 500 * 195 FROM clean.attendance
UNION ALL
SELECT 'unmapped statuses', COUNTIF(status IS NULL), 0 FROM clean.attendance
UNION ALL
SELECT 'unparsed dates', COUNTIF(attendance_date IS NULL), 0 FROM clean.attendance
UNION ALL
SELECT 'missing grades', COUNTIF(grade IS NULL), 0 FROM clean.students;
