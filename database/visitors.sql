-- ============================================================
--  StaySync — visitors.sql
--  Visitor check-in / check-out log for hostel gate management
-- ============================================================

CREATE TABLE IF NOT EXISTS visitors (
    visitor_id      INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT          NOT NULL,       -- which student is being visited
    visitor_name    VARCHAR(100) NOT NULL,
    relation        VARCHAR(50)  NULL,            -- e.g. Parent, Sibling, Friend
    phone           VARCHAR(15)  NULL,
    id_proof_type   VARCHAR(50)  NULL,            -- Aadhaar, PAN, Passport, etc.
    id_proof_number VARCHAR(50)  NULL,
    purpose         VARCHAR(255) NULL,
    checked_in_at   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    checked_out_at  DATETIME     NULL,
    approved_by     INT          NULL,            -- user_id of warden who approved
    status          ENUM('Checked In','Checked Out','Denied') DEFAULT 'Checked In',

    FOREIGN KEY (student_id)  REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES users(user_id)       ON DELETE SET NULL
);

-- Sample data
INSERT INTO visitors (student_id, visitor_name, relation, phone, id_proof_type, purpose, status) VALUES
(1, 'Suma Devi',    'Parent',  '9876543210', 'Aadhaar', 'Dropping monthly supplies', 'Checked In'),
(2, 'Ravi Kumar',   'Sibling', '9123456780', 'Aadhaar', 'Personal visit',            'Checked Out'),
(3, 'Anita Sharma', 'Parent',  '9988776655', 'PAN',     'Fee discussion with warden','Checked Out');

-- Set checkout time for checked-out visitors
UPDATE visitors SET checked_out_at = DATE_ADD(checked_in_at, INTERVAL 2 HOUR) WHERE status = 'Checked Out';