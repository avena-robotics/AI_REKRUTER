-- 1. User Sebastian
INSERT INTO users (id, first_name, last_name, email, phone, can_edit_tests) VALUES 
(2, 'Sebastian', 'Krajna', 'sebastian.krajna@pomagier.info', null, true);

-- 2. 50 Groups
INSERT INTO groups (id, name)
SELECT 
    generate_series(1, 50),
    'Grupa Sebastian ' || generate_series(1, 50);

-- 3. Link Sebastian to all 50 groups
INSERT INTO link_groups_users (group_id, user_id)
SELECT 
    generate_series(1, 50),
    2;

-- 4. 50 Tests
WITH series AS (
    SELECT 
        id,
        CASE (id % 3)
            WHEN 0 THEN 'SURVEY'::test_type
            WHEN 1 THEN 'IQ'::test_type
            WHEN 2 THEN 'EQ'::test_type
        END as test_type
    FROM generate_series(1, 50) id
)
INSERT INTO tests (id, title, test_type, description, passing_threshold, time_limit_minutes, created_at, updated_at)
SELECT 
    id,
    'Test ' || id,
    test_type,
    'Opis testu ' || id,
    70,
    45,
    now(),
    now()
FROM series;

-- 5. 50 Questions for the first test
INSERT INTO questions (
    id, test_id, question_text, answer_type, options,
    points, order_number, is_required,
    algorithm_type,
    algorithm_params
)
SELECT 
    generate_series(1, 50),
    1,
    'Pytanie ' || generate_series(1, 50),
    'TEXT'::answer_type,
    null,
    10,
    generate_series(1, 50),
    true,
    'NO_ALGORITHM'::algorithm_type,
    jsonb_build_object('correct_answer', 'Odpowiedź na pytanie ' || generate_series(1, 50))
FROM series;

-- 6. Link all tests to Sebastian's groups
INSERT INTO link_groups_tests (group_id, test_id)
SELECT 
    g.id,
    t.id
FROM generate_series(1, 50) g(id)
CROSS JOIN generate_series(1, 50) t(id);

-- 7. 50 Campaigns
INSERT INTO campaigns (
    id, code, title, workplace_location, contract_type, employment_type,
    work_start_date, duties, requirements, employer_offerings, job_description,
    salary_range_min, salary_range_max, po1_test_id, po2_test_id, po3_test_id,
    po1_test_weight, po2_test_weight, po3_test_weight, universal_access_token,
    is_active, created_at, updated_at
)
SELECT 
    id,
    'KAM_' || id,
    'Kampania ' || id,
    'Lokalizacja ' || id,
    'Umowa o pracę',
    'Pełny etat',
    '2024-06-01'::date + (id || ' days')::interval,
    'Obowiązki ' || id,
    'Wymagania ' || id,
    'Oferujemy ' || id,
    'Opis stanowiska ' || id,
    5000,
    10000,
    id,
    id,
    id,
    30,
    30,
    40,
    'token_' || id,
    true,
    now(),
    now()
FROM generate_series(1, 50) id;

-- 8. Link campaigns to Sebastian's groups
INSERT INTO link_groups_campaigns (group_id, campaign_id)
SELECT 
    g.id,
    c.id
FROM generate_series(1, 50) g(id)
CROSS JOIN generate_series(1, 50) c(id);

-- 9. 50 Candidates
WITH candidate_data AS (
    SELECT 
        id,
        CASE (id % 6)
            WHEN 0 THEN 'PO1'::recruitment_status
            WHEN 1 THEN 'PO2'::recruitment_status
            WHEN 2 THEN 'PO3'::recruitment_status
            WHEN 3 THEN 'PO4'::recruitment_status
            WHEN 4 THEN 'REJECTED'::recruitment_status
            WHEN 5 THEN 'ACCEPTED'::recruitment_status
        END as status,
        CASE 
            WHEN id % 6 >= 1 THEN floor(random() * 100)::int
            ELSE NULL
        END as po1_score,
        CASE 
            WHEN id % 6 >= 2 THEN floor(random() * 100)::int
            ELSE NULL
        END as po2_score,
        CASE 
            WHEN id % 6 >= 3 THEN floor(random() * 100)::int
            ELSE NULL
        END as po3_score,
        CASE 
            WHEN id % 6 = 3 THEN floor(random() * 100)::int
            ELSE NULL
        END as po4_score,
        CASE 
            WHEN id % 6 >= 1 THEN now() - (floor(random() * 30) || ' days')::interval
            ELSE NULL
        END as po1_completed_at,
        CASE 
            WHEN id % 6 >= 2 THEN now() - (floor(random() * 20) || ' days')::interval
            ELSE NULL
        END as po2_completed_at,
        CASE 
            WHEN id % 6 >= 3 THEN now() - (floor(random() * 10) || ' days')::interval
            ELSE NULL
        END as po3_completed_at
    FROM generate_series(1, 50) id
)
INSERT INTO candidates (
    id,
    campaign_id,
    first_name,
    last_name,
    email,
    phone,
    recruitment_status,
    po1_score,
    po2_score,
    po3_score,
    po4_score,
    total_score,
    po1_completed_at,
    po2_completed_at,
    po3_completed_at,
    access_token_po2,
    access_token_po3,
    access_token_po2_is_used,
    access_token_po3_is_used,
    access_token_po2_expires_at,
    access_token_po3_expires_at,
    score_ko,
    score_re,
    score_w,
    score_in,
    score_pz,
    score_kz,
    score_dz,
    score_sw,
    created_at,
    updated_at
)
SELECT 
    id,
    (id % 50) + 1 as campaign_id,
    'Kandydat_' || id as first_name,
    'Nazwisko_' || id as last_name,
    'kandydat' || id || '@example.com' as email,
    '+48 ' || (500000000 + id) as phone,
    status,
    po1_score,
    po2_score,
    po3_score,
    po4_score,
    COALESCE(po1_score, 0) + COALESCE(po2_score, 0) + COALESCE(po3_score, 0) + COALESCE(po4_score, 0) as total_score,
    po1_completed_at,
    po2_completed_at,
    po3_completed_at,
    CASE WHEN status = 'PO1'::recruitment_status THEN 'token_po2_' || id ELSE NULL END,
    CASE WHEN status = 'PO2'::recruitment_status THEN 'token_po3_' || id ELSE NULL END,
    status > 'PO2'::recruitment_status,
    status > 'PO3'::recruitment_status,
    CASE WHEN status = 'PO1'::recruitment_status THEN now() + interval '7 days' ELSE NULL END,
    CASE WHEN status = 'PO2'::recruitment_status THEN now() + interval '7 days' ELSE NULL END,
    floor(random() * 10)::int,
    floor(random() * 10)::int,
    floor(random() * 10)::int,
    floor(random() * 10)::int,
    floor(random() * 10)::int,
    floor(random() * 10)::int,
    floor(random() * 10)::int,
    floor(random() * 10)::int,
    now() - (floor(random() * 60) || ' days')::interval,
    now() - (floor(random() * 60) || ' days')::interval
FROM candidate_data;

-- 10. Add some candidate answers for the first test
INSERT INTO candidate_answers (
    candidate_id,
    question_id,
    answer,
    score,
    created_at
)
SELECT 
    c.id as candidate_id,
    q.id as question_id,
    'Odpowiedź kandydata ' || c.id || ' na pytanie ' || q.id as answer,
    floor(random() * 10)::int as score,
    c.po1_completed_at
FROM candidates c
CROSS JOIN questions q
WHERE c.po1_completed_at IS NOT NULL
AND q.test_id = 1; 