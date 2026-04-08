-- ============================================================
--  StaySync — bookings.sql
--  Tracks room booking requests and warden approval workflow
-- ============================================================

CREATE TABLE IF NOT EXISTS bookings (
    booking_id      INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT          NOT NULL,
    room_id         INT          NOT NULL,
    requested_on    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    approved_on     DATETIME     NULL,
    approved_by     INT          NULL,          -- user_id of warden/admin who approved
    status          ENUM('Pending','Approved','Rejected','Cancelled') DEFAULT 'Pending',
    rejection_reason VARCHAR(255) NULL,
    notes           TEXT         NULL,          -- student's optional note at request time

    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (room_id)    REFERENCES rooms(room_id)       ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES users(user_id)      ON DELETE SET NULL
);

-- Sample data
INSERT INTO bookings (student_id, room_id, status, notes) VALUES
(1, 1, 'Approved', 'Requesting ground floor due to health reasons'),
(2, 2, 'Pending',  'Prefer Block A if possible'),
(3, 3, 'Rejected', NULL),
(4, 4, 'Pending',  NULL);

-- Update rejection reason for the rejected booking
UPDATE bookings SET rejection_reason = 'Room already full' WHERE booking_id = 3;