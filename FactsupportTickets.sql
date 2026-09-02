USE EggcellenceDW;
GO

CREATE TABLE dbo.FactSupportTickets (
    TicketKey INT IDENTITY(1,1) PRIMARY KEY, -- Primary Key (Surrogate)
    ticket_id INT NOT NULL,                  -- Natural Key / Degenerate Dimension
    user_id INT,                             -- Foreign Key to DimUsers
    DateKey INT NOT NULL,                    -- Foreign Key to DimDate (YYYYMMDD)
    CreatedDate DATE,
    CreatedTime TIME,
    category VARCHAR(100),
    priority VARCHAR(50),
    status VARCHAR(50),
    department VARCHAR(100),
    role VARCHAR(100),
    message VARCHAR(MAX),
    attachment_path VARCHAR(255)
);
GO