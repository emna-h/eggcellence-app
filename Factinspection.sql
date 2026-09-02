USE EggcellenceDW;
GO

CREATE TABLE dbo.FactInspections (
    InspectionKey INT IDENTITY(1,1) PRIMARY KEY, -- Surrogate Key
    inspection_id INT NOT NULL,                  -- Natural Key
    user_id INT,                                 -- Foreign Key to DimUsers
    DateKey INT NOT NULL,                        -- Foreign Key to DimDate (YYYYMMDD)
    InspectionDate DATE,                         -- Separated Date
    InspectionTime TIME,                         -- Separated Time
    poids FLOAT,                                 -- Weight measure
    hauteur FLOAT,                               -- Height measure
    coloration VARCHAR(50),                      -- Color attribute
    fraicheur VARCHAR(50),                       -- Freshness rating
    classement VARCHAR(50),                      -- Grade classification
    charge_rupture FLOAT                         -- Breaking load measure
);
GO