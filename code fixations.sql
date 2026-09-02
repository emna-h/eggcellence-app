USE EggcellenceDW;
GO

-- ============================================================
-- FactInspections fixes
-- ============================================================

-- Fix the wrong data types (these are measurements, not text)
ALTER TABLE dbo.FactInspections ALTER COLUMN coloration FLOAT;
ALTER TABLE dbo.FactInspections ALTER COLUMN fraicheur FLOAT;
GO

-- Guard against duplicate loads
ALTER TABLE dbo.FactInspections
ADD CONSTRAINT UQ_FactInspections_inspection_id UNIQUE (inspection_id);
GO

-- Add the surrogate key column (keeps user_id too, for traceability)
ALTER TABLE dbo.FactInspections
ADD UserKey INT NULL;
GO

-- Real star-schema relationships
ALTER TABLE dbo.FactInspections
ADD CONSTRAINT FK_FactInspections_DimDate  FOREIGN KEY (DateKey) REFERENCES dbo.DimDate(DateKey);
GO
ALTER TABLE dbo.FactInspections
ADD CONSTRAINT FK_FactInspections_DimUsers FOREIGN KEY (UserKey) REFERENCES dbo.DimUsers(UserKey);
GO


-- ============================================================
-- FactSupportTickets fixes
-- ============================================================

ALTER TABLE dbo.FactSupportTickets
ADD CONSTRAINT UQ_FactSupportTickets_ticket_id UNIQUE (ticket_id);
GO

ALTER TABLE dbo.FactSupportTickets
ADD UserKey INT NULL;
GO

ALTER TABLE dbo.FactSupportTickets
ADD CONSTRAINT FK_FactSupportTickets_DimDate  FOREIGN KEY (DateKey) REFERENCES dbo.DimDate(DateKey);
GO
ALTER TABLE dbo.FactSupportTickets
ADD CONSTRAINT FK_FactSupportTickets_DimUsers FOREIGN KEY (UserKey) REFERENCES dbo.DimUsers(UserKey);
GO