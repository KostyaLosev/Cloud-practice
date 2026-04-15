IF NOT EXISTS (SELECT 1 FROM session_service.students WHERE student_id = '11111111-1111-1111-1111-111111111111')
BEGIN
    INSERT INTO session_service.students (student_id, full_name, email)
    VALUES
    ('11111111-1111-1111-1111-111111111111', 'Alice Newton', 'alice.newton@example.com'),
    ('22222222-2222-2222-2222-222222222222', 'Bob Curie', 'bob.curie@example.com');
END;
GO

IF NOT EXISTS (SELECT 1 FROM tutor_service.tutors WHERE tutor_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')
BEGIN
    INSERT INTO tutor_service.tutors (tutor_id, full_name, email, bio, rating_avg)
    VALUES
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Dr. Emily Carter', 'emily.carter@example.com', 'Physics tutor with 8 years of experience.', 4.80),
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Prof. John Maxwell', 'john.maxwell@example.com', 'Mathematics and Computer Science specialist.', 4.60);
END;
GO

IF NOT EXISTS (SELECT 1 FROM tutor_service.subjects WHERE subject_id = '10101010-1010-1010-1010-101010101010')
BEGIN
    INSERT INTO tutor_service.subjects (subject_id, name, category)
    VALUES
    ('10101010-1010-1010-1010-101010101010', 'Physics', 'Science'),
    ('20202020-2020-2020-2020-202020202020', 'Mathematics', 'Science'),
    ('30303030-3030-3030-3030-303030303030', 'Computer Science', 'Technology');
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM tutor_service.tutor_subjects
    WHERE tutor_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa' AND subject_id = '10101010-1010-1010-1010-101010101010'
)
BEGIN
    INSERT INTO tutor_service.tutor_subjects (tutor_id, subject_id, hourly_rate)
    VALUES
    ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '10101010-1010-1010-1010-101010101010', 45.00),
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '20202020-2020-2020-2020-202020202020', 40.00),
    ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '30303030-3030-3030-3030-303030303030', 50.00);
END;
GO

IF NOT EXISTS (SELECT 1 FROM tutor_service.tutor_availability WHERE availability_id = '99999999-9999-9999-9999-999999999999')
BEGIN
    INSERT INTO tutor_service.tutor_availability (availability_id, tutor_id, available_from, available_to, is_booked)
    VALUES
    ('99999999-9999-9999-9999-999999999999', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '2026-04-20T10:00:00', '2026-04-20T11:00:00', 0),
    ('88888888-8888-8888-8888-888888888888', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '2026-04-21T12:00:00', '2026-04-21T13:30:00', 0);
END;
GO

IF NOT EXISTS (SELECT 1 FROM session_service.sessions WHERE session_id = '55555555-5555-5555-5555-555555555555')
BEGIN
    INSERT INTO session_service.sessions (
        session_id,
        student_id,
        tutor_id,
        subject_id,
        scheduled_start,
        scheduled_end,
        status,
        notes
    )
    VALUES
    (
        '55555555-5555-5555-5555-555555555555',
        '11111111-1111-1111-1111-111111111111',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        '10101010-1010-1010-1010-101010101010',
        '2026-04-20T10:00:00',
        '2026-04-20T11:00:00',
        'completed',
        'Focused on Newtonian mechanics.'
    ),
    (
        '66666666-6666-6666-6666-666666666666',
        '22222222-2222-2222-2222-222222222222',
        'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
        '20202020-2020-2020-2020-202020202020',
        '2026-04-21T12:00:00',
        '2026-04-21T13:30:00',
        'scheduled',
        'Prepare for algebra exam.'
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM feedback_service.feedback WHERE feedback_id = '77777777-7777-7777-7777-777777777777')
BEGIN
    INSERT INTO feedback_service.feedback (feedback_id, session_id, student_id, tutor_id, rating, comment)
    VALUES
    (
        '77777777-7777-7777-7777-777777777777',
        '55555555-5555-5555-5555-555555555555',
        '11111111-1111-1111-1111-111111111111',
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        5,
        'Excellent explanation and very clear examples.'
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM feedback_service.feedback_event_log WHERE event_id = '12121212-1212-1212-1212-121212121212')
BEGIN
    INSERT INTO feedback_service.feedback_event_log (event_id, session_id, processing_status, error_message)
    VALUES
    ('12121212-1212-1212-1212-121212121212', '55555555-5555-5555-5555-555555555555', 'processed', NULL),
    ('34343434-3434-3434-3434-343434343434', '66666666-6666-6666-6666-666666666666', 'received', NULL);
END;
GO

IF NOT EXISTS (SELECT 1 FROM feedback_service.processed_session_feedback WHERE session_id = '55555555-5555-5555-5555-555555555555')
BEGIN
    INSERT INTO feedback_service.processed_session_feedback (session_id, source_event_id)
    VALUES
    ('55555555-5555-5555-5555-555555555555', '12121212-1212-1212-1212-121212121212');
END;
GO
