USE EggcellenceDW;
GO

CREATE TABLE dbo.DimGradingSettings (
    GradingSettingKey INT IDENTITY(1,1) PRIMARY KEY, -- Surrogate Key
    setting_id INT NOT NULL,                          -- Natural Key
    cutoff_aa FLOAT,
    cutoff_a FLOAT,
    cutoff_b FLOAT,
    min_strength FLOAT,
    updated_by INT,
    updated_at DATETIME
);
GO