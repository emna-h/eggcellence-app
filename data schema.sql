USE EggcellenceDB;
GO

DROP TABLE IF EXISTS stg_inspections;
DROP TABLE IF EXISTS inspections;
DROP TABLE IF EXISTS support_tickets;
DROP TABLE IF EXISTS grading_settings;
DROP TABLE IF EXISTS users;
GO


-- Users Table
CREATE TABLE users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('Admin', 'User')),
    department VARCHAR(10) NOT NULL CHECK (department IN ('D1', 'D2', 'D3', 'D4')),
    password_hash VARCHAR(255) NOT NULL,
    is_verified BIT NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Deactivated')),
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

-- Quality Threshold Settings Table
CREATE TABLE grading_settings (
    setting_id INT IDENTITY(1,1) PRIMARY KEY,
    cutoff_aa DECIMAL(5,2) NOT NULL DEFAULT 72.00,
    cutoff_a DECIMAL(5,2) NOT NULL DEFAULT 60.00,
    cutoff_b DECIMAL(5,2) NOT NULL DEFAULT 31.00,
    min_strength DECIMAL(5,2) NOT NULL DEFAULT 25.00,
    updated_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

-- Support Tickets Table
CREATE TABLE support_tickets (
    ticket_id INT IDENTITY(1,1) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    department VARCHAR(10) NOT NULL CHECK (department IN ('D1', 'D2', 'D3', 'D4')),
    role VARCHAR(20) NOT NULL CHECK (role IN ('Admin', 'User', 'Other')),
    category VARCHAR(100) NOT NULL,
    priority VARCHAR(10) NOT NULL DEFAULT 'Low' CHECK (priority IN ('Low', 'Medium', 'Urgent')),
    message VARCHAR(500) NOT NULL,
    attachment_path VARCHAR(255) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

-- Inspections Table
CREATE TABLE inspections (
    inspection_id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    inspection_datetime DATETIME2 NOT NULL,
    poids DECIMAL(5,2) NOT NULL CHECK (poids BETWEEN 20.00 AND 90.00),
    hauteur DECIMAL(4,2) NOT NULL CHECK (hauteur BETWEEN 2.00 AND 12.00),
    coloration DECIMAL(4,2) NOT NULL CHECK (coloration BETWEEN 7.00 AND 17.00),
    fraicheur DECIMAL(5,2) NOT NULL CHECK (fraicheur BETWEEN 20.00 AND 110.00),
    classement VARCHAR(2) NOT NULL CHECK (classement IN ('AA', 'A', 'B', 'C')),
    charge_rupture DECIMAL(4,2) NOT NULL CHECK (charge_rupture BETWEEN 10.00 AND 70.00),
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT FK_inspections_users FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
GO

CREATE TABLE stg_inspections (
    stg_id INT IDENTITY(1,1) PRIMARY KEY,
    raw_datetime VARCHAR(50) NULL,
    raw_inspector_email VARCHAR(150) NULL,
    raw_poids VARCHAR(50) NULL,
    raw_hauteur VARCHAR(50) NULL,
    raw_coloration VARCHAR(50) NULL,
    raw_fraicheur VARCHAR(50) NULL,
    raw_charge_rupture VARCHAR(50) NULL,
    raw_classement VARCHAR(10) NULL,
    imported_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    is_processed BIT NOT NULL DEFAULT 0,
    error_log VARCHAR(MAX) NULL
);
GO

-- STEP 4: Indexes for Performance Optimization
CREATE INDEX IX_inspections_user_id ON inspections(user_id);
CREATE INDEX IX_inspections_datetime ON inspections(inspection_datetime DESC);
CREATE INDEX IX_users_email ON users(email);
GO

-- STEP 5: Initial Seed Data Insertion
INSERT INTO users (full_name, email, role, department, password_hash, is_verified, status)
VALUES 
('System Admin', 'admin@eggcellence.com', 'Admin', 'D1', 'pbkdf2:sha256:600000$mockhashhere$', 1, 'Active'),
('Rayen Mahmoudi', 'R.Mahmoudi@eggcellence.com', 'User', 'D2', 'pbkdf2:sha256:600000$mockhashhere$', 1, 'Active'),
('Jihen Ben Hdid', 'J.Ben.Hdid@eggcellence.com', 'User', 'D1', 'pbkdf2:sha256:600000$mockhashhere$', 1, 'Active'),
('Anas Graja', 'A.Graja@eggcellence.com', 'User', 'D3', 'pbkdf2:sha256:600000$mockhashhere$', 1, 'Active');

INSERT INTO grading_settings (cutoff_aa, cutoff_a, cutoff_b, min_strength)
VALUES (72.00, 60.00, 31.00, 25.00);

INSERT INTO inspections (user_id, inspection_datetime, poids, hauteur, coloration, fraicheur, classement, charge_rupture)
VALUES 
(2, '2026-08-07 12:15:00', 58.20, 4.80, 10.50, 65.10, 'A', 38.00),
(4, '2026-08-06 16:40:00', 61.10, 3.90, 8.20, 55.00, 'B', 31.50),
(3, '2026-08-06 09:05:00', 54.30, 2.50, 7.10, 28.40, 'C', 18.20),
(2, '2026-08-05 11:20:00', 65.00, 6.10, 14.00, 82.10, 'AA', 48.90);
GO
