IF OBJECT_ID('session_service.students', 'U') IS NULL
BEGIN
    CREATE TABLE session_service.students (
        student_id UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        full_name NVARCHAR(200) NOT NULL,
        email NVARCHAR(255) NOT NULL UNIQUE,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END;
GO

IF OBJECT_ID('tutor_service.tutors', 'U') IS NULL
BEGIN
    CREATE TABLE tutor_service.tutors (
        tutor_id UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        full_name NVARCHAR(200) NOT NULL,
        email NVARCHAR(255) NOT NULL UNIQUE,
        bio NVARCHAR(1000) NULL,
        rating_avg DECIMAL(3, 2) NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
END;
GO

IF OBJECT_ID('tutor_service.subjects', 'U') IS NULL
BEGIN
    CREATE TABLE tutor_service.subjects (
        subject_id UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        name NVARCHAR(150) NOT NULL UNIQUE,
        category NVARCHAR(100) NOT NULL
    );
END;
GO

IF OBJECT_ID('tutor_service.tutor_subjects', 'U') IS NULL
BEGIN
    CREATE TABLE tutor_service.tutor_subjects (
        tutor_id UNIQUEIDENTIFIER NOT NULL,
        subject_id UNIQUEIDENTIFIER NOT NULL,
        hourly_rate DECIMAL(10, 2) NOT NULL,
        CONSTRAINT PK_tutor_subjects PRIMARY KEY (tutor_id, subject_id),
        CONSTRAINT FK_tutor_subjects_tutor FOREIGN KEY (tutor_id)
            REFERENCES tutor_service.tutors (tutor_id),
        CONSTRAINT FK_tutor_subjects_subject FOREIGN KEY (subject_id)
            REFERENCES tutor_service.subjects (subject_id)
    );
END;
GO

IF OBJECT_ID('tutor_service.tutor_availability', 'U') IS NULL
BEGIN
    CREATE TABLE tutor_service.tutor_availability (
        availability_id UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        tutor_id UNIQUEIDENTIFIER NOT NULL,
        available_from DATETIME2 NOT NULL,
        available_to DATETIME2 NOT NULL,
        is_booked BIT NOT NULL DEFAULT 0,
        CONSTRAINT FK_tutor_availability_tutor FOREIGN KEY (tutor_id)
            REFERENCES tutor_service.tutors (tutor_id)
    );
END;
GO

IF OBJECT_ID('session_service.sessions', 'U') IS NULL
BEGIN
    CREATE TABLE session_service.sessions (
        session_id UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        student_id UNIQUEIDENTIFIER NOT NULL,
        tutor_id UNIQUEIDENTIFIER NOT NULL,
        subject_id UNIQUEIDENTIFIER NOT NULL,
        scheduled_start DATETIME2 NOT NULL,
        scheduled_end DATETIME2 NOT NULL,
        status NVARCHAR(30) NOT NULL,
        notes NVARCHAR(1000) NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_sessions_student FOREIGN KEY (student_id)
            REFERENCES session_service.students (student_id),
        CONSTRAINT FK_sessions_tutor FOREIGN KEY (tutor_id)
            REFERENCES tutor_service.tutors (tutor_id),
        CONSTRAINT FK_sessions_subject FOREIGN KEY (subject_id)
            REFERENCES tutor_service.subjects (subject_id),
        CONSTRAINT CHK_sessions_status CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled'))
    );
END;
GO

IF OBJECT_ID('feedback_service.feedback', 'U') IS NOT NULL
AND (
    COL_LENGTH('feedback_service.feedback', 'session_id') IS NULL
    OR COL_LENGTH('feedback_service.feedback', 'student_id') IS NULL
    OR COL_LENGTH('feedback_service.feedback', 'tutor_id') IS NULL
    OR COL_LENGTH('feedback_service.feedback', 'comment') IS NULL
    OR COL_LENGTH('feedback_service.feedback', 'created_at') IS NULL
)
BEGIN
    DROP TABLE feedback_service.feedback;
END;
GO

IF OBJECT_ID('feedback_service.feedback', 'U') IS NULL
BEGIN
    CREATE TABLE feedback_service.feedback (
        feedback_id UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        session_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
        student_id UNIQUEIDENTIFIER NOT NULL,
        tutor_id UNIQUEIDENTIFIER NOT NULL,
        rating INT NOT NULL,
        comment NVARCHAR(2000) NULL,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_feedback_session FOREIGN KEY (session_id)
            REFERENCES session_service.sessions (session_id),
        CONSTRAINT FK_feedback_student FOREIGN KEY (student_id)
            REFERENCES session_service.students (student_id),
        CONSTRAINT FK_feedback_tutor FOREIGN KEY (tutor_id)
            REFERENCES tutor_service.tutors (tutor_id),
        CONSTRAINT CHK_feedback_rating CHECK (rating BETWEEN 1 AND 5)
    );
END;
GO

IF OBJECT_ID('feedback_service.feedback_event_log', 'U') IS NULL
BEGIN
    CREATE TABLE feedback_service.feedback_event_log (
        event_id UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        session_id UNIQUEIDENTIFIER NOT NULL,
        received_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        processing_status NVARCHAR(30) NOT NULL,
        error_message NVARCHAR(2000) NULL,
        CONSTRAINT CHK_feedback_event_status CHECK (processing_status IN ('received', 'processed', 'failed', 'sent_to_dlq'))
    );
END;
GO

IF OBJECT_ID('feedback_service.processed_session_feedback', 'U') IS NULL
BEGIN
    CREATE TABLE feedback_service.processed_session_feedback (
        session_id UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        processed_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        source_event_id UNIQUEIDENTIFIER NOT NULL
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_sessions_status' AND object_id = OBJECT_ID('session_service.sessions'))
    CREATE INDEX IX_sessions_status ON session_service.sessions (status);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_sessions_tutor_id' AND object_id = OBJECT_ID('session_service.sessions'))
    CREATE INDEX IX_sessions_tutor_id ON session_service.sessions (tutor_id);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_sessions_student_id' AND object_id = OBJECT_ID('session_service.sessions'))
    CREATE INDEX IX_sessions_student_id ON session_service.sessions (student_id);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_sessions_scheduled_start' AND object_id = OBJECT_ID('session_service.sessions'))
    CREATE INDEX IX_sessions_scheduled_start ON session_service.sessions (scheduled_start);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_tutor_availability_tutor_id' AND object_id = OBJECT_ID('tutor_service.tutor_availability'))
    CREATE INDEX IX_tutor_availability_tutor_id ON tutor_service.tutor_availability (tutor_id);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_feedback_tutor_id' AND object_id = OBJECT_ID('feedback_service.feedback'))
    CREATE INDEX IX_feedback_tutor_id ON feedback_service.feedback (tutor_id);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_feedback_session_id' AND object_id = OBJECT_ID('feedback_service.feedback'))
    CREATE INDEX IX_feedback_session_id ON feedback_service.feedback (session_id);
GO
