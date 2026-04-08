-- ============================================================
--  StaySync — rooms_enhanced.sql
--  DROP and recreate rooms with all columns the frontend uses
--  Run this ONLY if your existing rooms.sql is missing columns
-- ============================================================

-- If rooms table already exists, add missing columns safely:
ALTER TABLE rooms
  ADD COLUMN IF NOT EXISTS type        VARCHAR(50)  DEFAULT 'Single',   -- Single / Double / Triple
  ADD COLUMN IF NOT EXISTS floor       INT          DEFAULT 1,
  ADD COLUMN IF NOT EXISTS amenities   TEXT         NULL,               -- JSON array string e.g. '["WiFi","AC"]'
  ADD COLUMN IF NOT EXISTS description TEXT         NULL,
  ADD COLUMN IF NOT EXISTS image_url   VARCHAR(500) NULL;

-- Sample enriched room data
INSERT INTO rooms (block, capacity, occupied, price, status, type, floor, amenities, description) VALUES
('A', 1, 0, 8000,  'Available',   'Single', 1, '["WiFi","AC","Attached Bathroom","Study Table"]',   'Spacious single-occupancy room in Block A with AC and attached bathroom.'),
('A', 2, 1, 6000,  'Available',   'Double', 1, '["WiFi","Fan","Common Bathroom","Study Table"]',    'Comfortable double-sharing room on the ground floor.'),
('A', 3, 3, 4500,  'Occupied',    'Triple', 2, '["WiFi","Fan","Common Bathroom"]',                  'Triple sharing room, fully occupied.'),
('B', 1, 0, 8500,  'Available',   'Single', 2, '["WiFi","AC","Attached Bathroom","Balcony"]',       'Premium single room with balcony view.'),
('B', 2, 2, 6000,  'Occupied',    'Double', 1, '["WiFi","Fan","Common Bathroom"]',                  'Double sharing room, currently full.'),
('B', 1, 0, 9000,  'Available',   'Single', 3, '["WiFi","AC","Attached Bathroom","Study Table","Balcony"]', 'Top-floor premium room with city view.'),
('C', 3, 1, 4500,  'Available',   'Triple', 1, '["WiFi","Fan","Common Bathroom"]',                  'Triple sharing room with two beds available.'),
('C', 2, 0, 6500,  'Available',   'Double', 2, '["WiFi","AC","Common Bathroom","Study Table"]',     'AC double room on second floor.'),
('C', 1, 0, 0,     'Maintenance', 'Single', 1, '[]',                                                'Under maintenance — plumbing repair in progress.'),
('D', 2, 1, 5500,  'Available',   'Double', 1, '["WiFi","Fan","Common Bathroom"]',                  'One bed available in this double room.');