USE EggcellenceDW;
SELECT COUNT(*) AS UserCount FROM DimUsers;
SELECT COUNT(*) AS InspectionCount FROM FactInspections;
SELECT COUNT(*) AS TicketCount FROM FactSupportTickets;
SELECT COUNT(*) AS SettingsCount FROM DimGradingSettings;
SELECT TOP 5 * FROM FactInspections;  -- eyeball that UserKey, coloration, fraicheur look like real numbers now