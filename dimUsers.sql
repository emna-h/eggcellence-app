use EggcellenceDW
go

CREATE TABLE dbo.DimUsers (
    UserKey INT IDENTITY(1,1) PRIMARY KEY, -- Data warehouse surrogate key
    user_id INT NOT NULL,                  -- Natural key from source
    full_name VARCHAR(150),
    email VARCHAR(150),
    role VARCHAR(50),
    job_title VARCHAR(100),
    department VARCHAR(100),
    is_verified BIT,
    status VARCHAR(50),
    created_at DATETIME
);
GO