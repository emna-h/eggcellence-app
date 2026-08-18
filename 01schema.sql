IF DB_ID('EggcellenceDB') IS NULL
    CREATE DATABASE EggcellenceDB;
GO

USE EggcellenceDB;
GO

-- ---------------------------------------------------------------------
-- Drop in reverse dependency order
-- ---------------------------------------------------------------------
DROP VIEW  IF EXISTS vw_inspection_report;
DROP TABLE IF EXISTS stg_inspections;
DROP TABLE IF EXISTS inspections;
DROP TABLE IF EXISTS support_tickets;
DROP TABLE IF EXISTS grading_settings;
DROP TABLE IF EXISTS access_keys;
DROP TABLE IF EXISTS users;
GO

-- ---------------------------------------------------------------------
-- users
-- added job_title — admin.html's "Add Inspector" modal has its
-- own Role dropdown ('Quality Inspector' / 'Lead Inspector').
-- ---------------------------------------------------------------------
CREATE TABLE users (
    user_id         INT IDENTITY(1,1) PRIMARY KEY,
    full_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    role            VARCHAR(20)  NOT NULL CHECK (role IN ('Admin', 'User')),
    job_title       VARCHAR(30)  NULL CHECK (job_title IN ('Quality Inspector', 'Lead Inspector', 'System Admin')),
    department      VARCHAR(10)  NOT NULL CHECK (department IN ('D1', 'D2', 'D3', 'D4')),
    password_hash   VARCHAR(255) NOT NULL,
    is_verified     BIT          NOT NULL DEFAULT 0,
    status          VARCHAR(20)  NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Deactivated')),
    created_at      DATETIME2    NOT NULL DEFAULT SYSDATETIME()
);
GO

-- ---------------------------------------------------------------------
-- access_keys  — NEW TABLE
-- ---------------------------------------------------------------------
CREATE TABLE access_keys (
    key_id      INT IDENTITY(1,1) PRIMARY KEY,
    role        VARCHAR(20)  NOT NULL CHECK (role IN ('Admin', 'User')),
    key_hash    VARCHAR(255) NOT NULL,
    created_at  DATETIME2    NOT NULL DEFAULT SYSDATETIME()
);
GO

-- ---------------------------------------------------------------------
-- grading_settings
-- added updated_by so admin.html's Settings save has an audit
-- trail of who changed thresholds and when 
-- ---------------------------------------------------------------------
CREATE TABLE grading_settings (
    setting_id      INT IDENTITY(1,1) PRIMARY KEY,
    cutoff_aa       DECIMAL(5,2) NOT NULL DEFAULT 72.00,
    cutoff_a        DECIMAL(5,2) NOT NULL DEFAULT 60.00,
    cutoff_b        DECIMAL(5,2) NOT NULL DEFAULT 31.00,
    min_strength    DECIMAL(5,2) NOT NULL DEFAULT 25.00,
    updated_by      INT NULL,
    updated_at      DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT FK_settings_users FOREIGN KEY (updated_by) REFERENCES users(user_id) ON DELETE SET NULL
);
GO

-- ---------------------------------------------------------------------
-- support_tickets
-- ---------------------------------------------------------------------
CREATE TABLE support_tickets (
    ticket_id       INT IDENTITY(1,1) PRIMARY KEY,
    full_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(150) NOT NULL,
    department      VARCHAR(10)  NOT NULL CHECK (department IN ('D1', 'D2', 'D3', 'D4')),
    role            VARCHAR(20)  NOT NULL CHECK (role IN ('Admin', 'User', 'Other')),
    category        VARCHAR(100) NOT NULL,
    priority        VARCHAR(10)  NOT NULL DEFAULT 'Low' CHECK (priority IN ('Low', 'Medium', 'Urgent')),
    message         VARCHAR(500) NOT NULL,
    attachment_path VARCHAR(255) NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT 'Open' CHECK (status IN ('Open', 'In Progress', 'Resolved')),
    created_at      DATETIME2    NOT NULL DEFAULT SYSDATETIME()
);
GO

-- ---------------------------------------------------------------------
-- inspections — unchanged from your version, it was correct
-- ---------------------------------------------------------------------
CREATE TABLE inspections (
    inspection_id       INT IDENTITY(1,1) PRIMARY KEY,
    user_id              INT NOT NULL,
    inspection_datetime  DATETIME2 NOT NULL,
    poids                DECIMAL(5,2) NOT NULL CHECK (poids BETWEEN 20.00 AND 90.00),
    hauteur              DECIMAL(4,2) NOT NULL CHECK (hauteur BETWEEN 2.00 AND 12.00),
    coloration           DECIMAL(4,2) NOT NULL CHECK (coloration BETWEEN 7.00 AND 17.00),
    fraicheur            DECIMAL(5,2) NOT NULL CHECK (fraicheur BETWEEN 20.00 AND 110.00),
    classement           VARCHAR(2)   NOT NULL CHECK (classement IN ('AA', 'A', 'B', 'C')),
    charge_rupture       DECIMAL(4,2) NOT NULL CHECK (charge_rupture BETWEEN 10.00 AND 70.00),
    created_at           DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT FK_inspections_users FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
GO

-- ---------------------------------------------------------------------
-- stg_inspections — your staging table, unchanged, it was correct and
-- is exactly the right shape for an SSIS landing zone (see SSIS
-- section in the report below for how it gets used).
-- ---------------------------------------------------------------------
CREATE TABLE stg_inspections (
    stg_id                INT IDENTITY(1,1) PRIMARY KEY,
    raw_datetime          VARCHAR(50)  NULL,
    raw_inspector_email   VARCHAR(150) NULL,
    raw_poids             VARCHAR(50)  NULL,
    raw_hauteur           VARCHAR(50)  NULL,
    raw_coloration        VARCHAR(50)  NULL,
    raw_fraicheur         VARCHAR(50)  NULL,
    raw_charge_rupture    VARCHAR(50)  NULL,
    raw_classement        VARCHAR(10)  NULL,
    imported_at           DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    is_processed          BIT NOT NULL DEFAULT 0,
    error_log             VARCHAR(MAX) NULL
);
GO

-- ---------------------------------------------------------------------
-- Indexes — unchanged from your version, they were correct
-- ---------------------------------------------------------------------
CREATE INDEX IX_inspections_user_id  ON inspections(user_id);
CREATE INDEX IX_inspections_datetime ON inspections(inspection_datetime DESC);
CREATE INDEX IX_users_email          ON users(email);
GO

-- ---------------------------------------------------------------------
-- Reporting view — NEW. Power BI and the SSIS load step both read
-- from this, not the raw tables.
-- ---------------------------------------------------------------------
CREATE OR ALTER VIEW vw_inspection_report AS
SELECT
    i.inspection_id,
    i.inspection_datetime,
    u.full_name        AS inspector_name,
    u.department,
    i.poids, i.hauteur, i.coloration, i.fraicheur, i.charge_rupture, i.classement,
    CASE WHEN i.classement IN ('AA','A') THEN 1 ELSE 0 END AS is_pass,
    CASE WHEN i.classement = 'C' THEN 1 ELSE 0 END          AS is_reject
FROM inspections i
JOIN users u ON u.user_id = i.user_id;
GO
