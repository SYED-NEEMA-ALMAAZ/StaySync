-- ============================================================
--  StaySync — master_setup.sql
--  Run this file to set up the ENTIRE database from scratch
--  Usage: mysql -u root -p < master_setup.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS staysync_db;
USE staysync_db;

-- ── Step 1: Core tables (run your existing files in this order) ──
-- ORDER MATTERS due to foreign key dependencies

-- 1. users         (no dependencies)
SOURCE users.sql;

-- 2. rooms         (no dependencies)
SOURCE rooms.sql;

-- 3. students      (depends on users, rooms)
SOURCE students.sql;

-- 4. complaints    (depends on students)
SOURCE complaints.sql;

-- 5. payments      (depends on students)
SOURCE payments.sql;

-- 6. fines         (depends on students)
SOURCE fines.sql;

-- 7. attendance    (depends on students)
SOURCE attendance.sql;

-- 8. leaves        (depends on students, users)
SOURCE leaves.sql;

-- 9. maintenance   (depends on students, users)
SOURCE maintenance.sql;

-- 10. routines     (no dependencies)
SOURCE routines.sql;

-- 11. reports      (no dependencies)
SOURCE reports.sql;

-- ── Step 2: New tables (run in this order) ──

-- 12. bookings     (depends on students, rooms, users)
SOURCE bookings.sql;

-- 13. notifications (depends on users)
SOURCE notifications.sql;

-- 14. visitors     (depends on students, users)
SOURCE visitors.sql;

-- ── Step 3: Enrich rooms table with extra columns ──
SOURCE rooms_enhanced.sql;

-- ── Done ──
SELECT 'StaySync database setup complete!' AS status;