-- ============================================================
--  StaySync — notifications.sql
--  System-wide and user-targeted notifications / announcements
-- ============================================================

CREATE TABLE IF NOT EXISTS notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT          NULL,          -- NULL = broadcast to all users
    title           VARCHAR(150) NOT NULL,
    message         TEXT         NOT NULL,
    type            ENUM('info','success','warning','error','announcement') DEFAULT 'info',
    is_read         TINYINT(1)   DEFAULT 0,
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    expires_at      DATETIME     NULL,          -- NULL = never expires

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Sample data
INSERT INTO notifications (user_id, title, message, type) VALUES
(NULL, 'Hostel Fee Reminder',    'Last date to pay semester fee is 15th April 2026.',          'warning'),
(NULL, 'Water Supply Shutdown',  'Water will be unavailable on 10th April from 9 AM to 1 PM.', 'info'),
(NULL, 'Mess Menu Updated',      'New mess menu effective from Monday. Check the portal.',      'announcement'),
(1,    'Booking Approved',       'Your room booking for Block A - Room 101 has been approved.', 'success'),
(2,    'Complaint Update',       'Your water leakage complaint (CMP-002) is now In Progress.',  'info'),
(3,    'Fine Issued',            'A fine of ₹200 has been issued for late fee payment.',         'error');