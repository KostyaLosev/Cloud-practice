IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'session_service')
    EXEC('CREATE SCHEMA session_service');
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'tutor_service')
    EXEC('CREATE SCHEMA tutor_service');
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'feedback_service')
    EXEC('CREATE SCHEMA feedback_service');
GO
