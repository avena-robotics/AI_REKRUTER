-- Drop tables first (in reverse order of dependencies)
DROP TABLE IF EXISTS link_groups_users CASCADE;
DROP TABLE IF EXISTS link_groups_tests CASCADE;
DROP TABLE IF EXISTS link_groups_campaigns CASCADE;
DROP TABLE IF EXISTS groups CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS candidate_answers CASCADE;
DROP TABLE IF EXISTS candidates CASCADE;
DROP TABLE IF EXISTS questions CASCADE;
DROP TABLE IF EXISTS tests CASCADE;
DROP TABLE IF EXISTS campaigns CASCADE;

-- Drop custom types
DROP TYPE IF EXISTS recruitment_status CASCADE;
DROP TYPE IF EXISTS answer_type CASCADE;
DROP TYPE IF EXISTS test_type CASCADE;

-- Create types first
create type test_type as enum ('SURVEY', 'EQ', 'IQ', 'EQ_EVALUATION');
create type answer_type as enum ('TEXT', 'BOOLEAN', 'SCALE', 'SALARY', 'DATE', 'ABCDEF', 'AH_POINTS');
create type recruitment_status as enum ('PO1', 'PO2', 'PO3', 'PO4', 'REJECTED', 'ACCEPTED');

-- Create tests table before campaigns (since campaigns references tests)
create table tests (
    id serial primary key,
    title text not null,
    test_type test_type not null,
    description text,
    passing_threshold int not null,
    time_limit_minutes int,
    created_at timestamp default now(),
    updated_at timestamp default now()
);

-- Now create campaigns table (which references tests)
create table campaigns (
    id bigserial primary key,
    code text not null unique,            -- J5A_logopeda_05_2024
    title text not null,                  -- Logopedia - Warszawa   
    workplace_location text not null,     -- Warszawa
    contract_type text not null,          -- umowa o pracę, B2B, etc.
    employment_type text not null,        -- pełny etat, część etatu, etc.
    work_start_date date not null,        -- 2024-05-01
    duties text not null,                 -- opis obowiązków
    requirements text not null,           -- opis wymagań
    employer_offerings text not null,     -- opis co oferuje pracodawca
    job_description text not null,        -- opis czego potrzebujemy
    salary_range_min integer,             -- 3000
    salary_range_max integer,             -- 5000
    is_active boolean default true,
    universal_access_token text,
    po1_test_id integer references tests(id),    -- References to tests are kept
    po2_test_id integer references tests(id),
    po3_test_id integer references tests(id),
    po1_test_weight integer,
    po2_test_weight integer,
    po3_test_weight integer,
    created_at timestamp default now(),
    updated_at timestamp default now()
);

-- Tabela pytań
create table questions (
    id serial primary key,
    test_id integer references tests(id) ON DELETE CASCADE,         -- Id testu
    question_text text not null,                                    -- Pytanie do kandydata lub sekcja (I-VII) dla testu EQ     
    answer_type answer_type not null,                               -- TEXT, BOOLEAN, SCALE(0-5), SALARY, DATE, ABCDEF, AH_POINTS
    options jsonb,                                                  -- Opcje dla testu EQ (a-h)
    points int not null default 0,                                  -- Punkty za pytanie
    order_number integer not null,                                  -- Numer pytania w testach
    is_required boolean default true,                               -- Czy pytanie jest obowiązkowe
    image text,                                                     -- Add image URL field
    correct_answer_text text,
    correct_answer_boolean boolean,
    correct_answer_salary numeric,
    correct_answer_scale int,
    correct_answer_date date,
    correct_answer_abcdef text
);

-- Tabela kandydatów
create table candidates (
    id bigserial primary key,
    campaign_id bigint references campaigns(id),    -- J5A_logopeda_05_2024    
    first_name text not null,                       -- Jan
    last_name text not null,                        -- Kowalski
    email text not null,                            -- jan.kowalski@example.com
    phone text,                                     -- +48 123 456 789
    recruitment_status recruitment_status not null, -- PO1, PO2, PO3, PO4, REJECTED, ACCEPTED
    po1_score int,                                  -- 100
    po2_score int,                                  -- 80
    po3_score int,                                  -- 70
    po4_score int,                                  -- 60
    total_score float,                                -- 310  
    po1_started_at timestamp with time zone,
    po2_started_at timestamp with time zone,
    po3_started_at timestamp with time zone,
    po1_completed_at timestamp with time zone,      -- Data zakończenia testu PO1
    po2_completed_at timestamp with time zone,      -- Data zakończenia testu PO2
    po3_completed_at timestamp with time zone,      -- Data zakończenia testu PO3
    access_token_po2 text,                          -- token do testu PO2
    access_token_po3 text,                          -- token do testu PO3
    access_token_po2_is_used boolean default false, -- Czy token PO2 został użyty
    access_token_po3_is_used boolean default false, -- Czy token PO3 został użyty
    access_token_po2_expires_at timestamp with time zone, -- Data ważności tokenu PO2
    access_token_po3_expires_at timestamp with time zone, -- Data ważności tokenu PO3
    score_ko int,
    score_re int,
    score_w int,
    score_in int,
    score_pz int,
    score_kz int,
    score_dz int,
    score_sw int,
    created_at timestamp default now(),
    updated_at timestamp default now()
);

-- Tabela odpowiedzi kandydatów
create table candidate_answers (
    id bigserial primary key,
    candidate_id bigint references candidates(id) ON DELETE CASCADE,
    question_id integer references questions(id),
    stage text not null check (stage in ('PO1', 'PO2', 'PO3', 'PO4')),
    text_answer text,                              -- Odpowiedź tekstowa    
    boolean_answer boolean,                        -- Odpowiedź typu boolean
    salary_answer numeric,                        -- Odpowiedź typu numeric
    scale_answer int,                              -- Odpowiedź typu scale
    date_answer date,                              -- Odpowiedź typu date
    abcdef_answer text,                            -- Odpowiedź typu ABCDEF
    points_per_option jsonb,                       -- Format JSON, np. {"a": 3, "b": 5, "c": 0}
    score int,                                     -- Punkty za odpowiedź
    score_ai int,                                  -- Punkty za odpowiedź AI,
    created_at timestamp default now()
);

-- Users table
create table users (
    id bigserial primary key,
    first_name text not null,
    last_name text not null,
    email text not null unique,
    phone text,
    can_edit_tests boolean default false,
    created_at timestamp default now(),
    updated_at timestamp default now()
);

-- Groups table
create table groups (
    id bigserial primary key,
    name text not null,
    created_at timestamp default now(),
    updated_at timestamp default now()
);

-- Linking table for users and groups
create table link_groups_users (
    group_id bigint references groups(id) ON DELETE CASCADE,
    user_id bigint references users(id) ON DELETE CASCADE,
    primary key (group_id, user_id)
);

-- Linking table for campaigns and groups
create table link_groups_campaigns (
    group_id bigint references groups(id) ON DELETE CASCADE,
    campaign_id bigint references campaigns(id) ON DELETE CASCADE,
    primary key (group_id, campaign_id)
);

-- Linking table for tests and groups
create table link_groups_tests (
    group_id bigint references groups(id) ON DELETE CASCADE,
    test_id integer references tests(id) ON DELETE CASCADE,
    primary key (group_id, test_id)
);

-- Add indexes for common queries and joins
CREATE INDEX idx_campaigns_is_active ON campaigns(is_active);
CREATE INDEX idx_link_groups_campaigns_campaign_id ON link_groups_campaigns(campaign_id);
CREATE INDEX idx_link_groups_users_user_id ON link_groups_users(user_id);

-- Function to get campaigns with groups in a single query
CREATE OR REPLACE FUNCTION get_campaigns_with_groups(
    p_user_group_ids bigint[],
    p_limit integer,
    p_offset integer
) RETURNS TABLE (
    id bigint,
    code text,
    title text,
    workplace_location text,
    is_active boolean,
    universal_access_token text,
    created_at timestamp,
    updated_at timestamp,
    groups jsonb,
    po1_test jsonb,
    po2_test jsonb,
    po3_test jsonb
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH campaign_groups AS (
        SELECT DISTINCT c.*, 
            jsonb_agg(
                jsonb_build_object(
                    'id', g.id,
                    'name', g.name
                )
            ) FILTER (WHERE g.id IS NOT NULL) AS groups
        FROM campaigns c
        JOIN link_groups_campaigns lgc ON c.id = lgc.campaign_id
        JOIN groups g ON lgc.group_id = g.id
        WHERE lgc.group_id = ANY(p_user_group_ids)
        GROUP BY c.id
    )
    SELECT 
        cg.id,
        cg.code,
        cg.title,
        cg.workplace_location,
        cg.is_active,
        cg.universal_access_token,
        cg.created_at,
        cg.updated_at,
        cg.groups,
        jsonb_build_object(
            'test_type', t1.test_type,
            'title', t1.title,
            'description', t1.description
        ) AS po1_test,
        jsonb_build_object(
            'test_type', t2.test_type,
            'title', t2.title,
            'description', t2.description
        ) AS po2_test,
        jsonb_build_object(
            'test_type', t3.test_type,
            'title', t3.title,
            'description', t3.description
        ) AS po3_test
    FROM campaign_groups cg
    LEFT JOIN tests t1 ON cg.po1_test_id = t1.id
    LEFT JOIN tests t2 ON cg.po2_test_id = t2.id
    LEFT JOIN tests t3 ON cg.po3_test_id = t3.id
    ORDER BY cg.created_at DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;

-- Function to get total campaign count
CREATE OR REPLACE FUNCTION get_campaigns_count(
    p_user_group_ids bigint[]
) RETURNS TABLE (count bigint) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT COUNT(DISTINCT c.id)
    FROM campaigns c
    JOIN link_groups_campaigns lgc ON c.id = lgc.campaign_id
    WHERE lgc.group_id = ANY(p_user_group_ids);
END;
$$;

-- Function to get tests for groups
CREATE OR REPLACE FUNCTION get_group_tests(
    p_group_ids bigint[]
) RETURNS TABLE (
    id integer,
    test_type text,
    title text,
    description text
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT t.id, t.test_type::text, t.title, t.description
    FROM tests t
    JOIN link_groups_tests lgt ON t.id = lgt.test_id
    WHERE lgt.group_id = ANY(p_group_ids)
    ORDER BY t.test_type;
END;
$$;

-- Function to get single campaign data with all related information
CREATE OR REPLACE FUNCTION get_single_campaign_data(
    p_campaign_id bigint
) RETURNS TABLE (
    id bigint,
    code text,
    title text,
    workplace_location text,
    contract_type text,
    employment_type text,
    work_start_date date,
    duties text,
    requirements text,
    employer_offerings text,
    job_description text,
    salary_range_min integer,
    salary_range_max integer,
    is_active boolean,
    universal_access_token text,
    po1_test_id integer,
    po2_test_id integer,
    po3_test_id integer,
    po1_test_weight integer,
    po2_test_weight integer,
    po3_test_weight integer,
    created_at timestamp,
    updated_at timestamp,
    groups jsonb,
    po1_test jsonb,
    po2_test jsonb,
    po3_test jsonb
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH campaign_groups AS (
        SELECT 
            c.*,
            jsonb_agg(
                jsonb_build_object(
                    'id', g.id,
                    'name', g.name
                )
            ) FILTER (WHERE g.id IS NOT NULL) AS groups
        FROM campaigns c
        LEFT JOIN link_groups_campaigns lgc ON c.id = lgc.campaign_id
        LEFT JOIN groups g ON lgc.group_id = g.id
        WHERE c.id = p_campaign_id
        GROUP BY c.id
    )
    SELECT 
        cg.*,
        jsonb_build_object(
            'test_type', t1.test_type,
            'title', t1.title,
            'description', t1.description
        ) AS po1_test,
        jsonb_build_object(
            'test_type', t2.test_type,
            'title', t2.title,
            'description', t2.description
        ) AS po2_test,
        jsonb_build_object(
            'test_type', t3.test_type,
            'title', t3.title,
            'description', t3.description
        ) AS po3_test
    FROM campaign_groups cg
    LEFT JOIN tests t1 ON cg.po1_test_id = t1.id
    LEFT JOIN tests t2 ON cg.po2_test_id = t2.id
    LEFT JOIN tests t3 ON cg.po3_test_id = t3.id
    WHERE cg.id = p_campaign_id;
END;
$$;

-- Function to duplicate campaign
CREATE OR REPLACE FUNCTION duplicate_campaign(
    p_campaign_id bigint,
    p_new_code text
) RETURNS TABLE (
    id bigint,
    code text
) LANGUAGE plpgsql AS $$
DECLARE
    new_campaign_id bigint;
BEGIN
    -- Insert new campaign
    INSERT INTO campaigns (
        code,
        title,
        workplace_location,
        contract_type,
        employment_type,
        work_start_date,
        duties,
        requirements,
        employer_offerings,
        job_description,
        salary_range_min,
        salary_range_max,
        is_active,
        po1_test_id,
        po2_test_id,
        po3_test_id,
        po1_test_weight,
        po2_test_weight,
        po3_test_weight,
        created_at,
        updated_at
    )
    SELECT 
        p_new_code,
        title,
        workplace_location,
        contract_type,
        employment_type,
        work_start_date,
        duties,
        requirements,
        employer_offerings,
        job_description,
        salary_range_min,
        salary_range_max,
        is_active,
        po1_test_id,
        po2_test_id,
        po3_test_id,
        po1_test_weight,
        po2_test_weight,
        po3_test_weight,
        now(),
        now()
    FROM campaigns
    WHERE id = p_campaign_id
    RETURNING id INTO new_campaign_id;
    
    -- Copy group associations
    INSERT INTO link_groups_campaigns (group_id, campaign_id)
    SELECT group_id, new_campaign_id
    FROM link_groups_campaigns
    WHERE campaign_id = p_campaign_id;
    
    RETURN QUERY
    SELECT new_campaign_id, p_new_code;
END;
$$;

-- Add after other functions
CREATE OR REPLACE FUNCTION get_candidate_with_tests(p_candidate_id bigint)
RETURNS TABLE (
    candidate_data jsonb,
    tests_data jsonb
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH candidate_info AS (
        SELECT 
            jsonb_build_object(
                'id', c.id,
                'first_name', c.first_name,
                'last_name', c.last_name,
                'email', c.email,
                'phone', c.phone,
                'recruitment_status', c.recruitment_status,
                'created_at', c.created_at,
                'updated_at', c.updated_at,
                'po1_score', c.po1_score,
                'po2_score', c.po2_score,
                'po3_score', c.po3_score,
                'po4_score', c.po4_score,
                'total_score', c.total_score,
                'po1_started_at', c.po1_started_at,
                'po2_started_at', c.po2_started_at,
                'po3_started_at', c.po3_started_at,
                'po1_completed_at', c.po1_completed_at,
                'po2_completed_at', c.po2_completed_at,
                'po3_completed_at', c.po3_completed_at,
                'score_ko', c.score_ko,
                'score_re', c.score_re,
                'score_w', c.score_w,
                'score_in', c.score_in,
                'score_pz', c.score_pz,
                'score_kz', c.score_kz,
                'score_dz', c.score_dz,
                'score_sw', c.score_sw,
                'access_token_po2', c.access_token_po2,
                'access_token_po3', c.access_token_po3,
                'access_token_po2_is_used', c.access_token_po2_is_used,
                'access_token_po3_is_used', c.access_token_po3_is_used,
                'access_token_po2_expires_at', c.access_token_po2_expires_at,
                'access_token_po3_expires_at', c.access_token_po3_expires_at,
                'campaign', jsonb_build_object(
                    'id', camp.id,
                    'code', camp.code,
                    'title', camp.title,
                    'workplace_location', camp.workplace_location,
                    'contract_type', camp.contract_type,
                    'employment_type', camp.employment_type,
                    'work_start_date', camp.work_start_date,
                    'salary_range_min', camp.salary_range_min,
                    'salary_range_max', camp.salary_range_max,
                    'po1_test_id', camp.po1_test_id,
                    'po2_test_id', camp.po2_test_id,
                    'po3_test_id', camp.po3_test_id
                )
            ) as cand_data
        FROM candidates c
        JOIN campaigns camp ON c.campaign_id = camp.id
        WHERE c.id = p_candidate_id
    ),
    questions_with_answers AS (
        SELECT 
            t.id as test_id,
            stages.stage,
            jsonb_agg(
                jsonb_build_object(
                    'id', q.id,
                    'question_text', q.question_text,
                    'answer_type', q.answer_type,
                    'options', q.options,
                    'points', q.points,
                    'order_number', q.order_number,
                    'is_required', q.is_required,
                    'image', q.image,
                    'correct_answer_text', q.correct_answer_text,
                    'correct_answer_boolean', q.correct_answer_boolean,
                    'correct_answer_salary', q.correct_answer_salary,
                    'correct_answer_scale', q.correct_answer_scale,
                    'correct_answer_date', q.correct_answer_date,
                    'correct_answer_abcdef', q.correct_answer_abcdef,
                    'answer', (
                        SELECT COALESCE(jsonb_build_object(
                            'id', ca.id,
                            'text_answer', ca.text_answer,
                            'boolean_answer', ca.boolean_answer,
                            'salary_answer', ca.salary_answer,
                            'scale_answer', ca.scale_answer,
                            'date_answer', ca.date_answer,
                            'abcdef_answer', ca.abcdef_answer,
                            'points_per_option', ca.points_per_option,
                            'score', ca.score,
                            'score_ai', ca.score_ai
                        ), NULL)
                        FROM candidate_answers ca
                        WHERE ca.question_id = q.id 
                        AND ca.candidate_id = p_candidate_id
                        AND ca.stage = stages.stage
                        LIMIT 1
                    )
                ) ORDER BY q.order_number
            ) as questions
        FROM (
            SELECT 'PO1' as stage, po1_test_id as test_id 
            FROM campaigns 
            WHERE id = (SELECT campaign_id FROM candidates WHERE id = p_candidate_id)
            UNION ALL
            SELECT 'PO2', po2_test_id 
            FROM campaigns 
            WHERE id = (SELECT campaign_id FROM candidates WHERE id = p_candidate_id)
            UNION ALL
            SELECT 'PO3', po3_test_id 
            FROM campaigns 
            WHERE id = (SELECT campaign_id FROM candidates WHERE id = p_candidate_id)
        ) stages
        JOIN tests t ON stages.test_id = t.id
        JOIN questions q ON q.test_id = t.id
        GROUP BY t.id, stages.stage
    ),
    test_data AS (
        SELECT 
            stages.stage,
            jsonb_build_object(
                'test', jsonb_build_object(
                    'id', t.id,
                    'title', t.title,
                    'test_type', t.test_type,
                    'description', t.description,
                    'passing_threshold', t.passing_threshold,
                    'time_limit_minutes', t.time_limit_minutes
                ),
                'questions', qa.questions
            ) as test_data
        FROM (
            SELECT stage, test_id FROM questions_with_answers
        ) stages
        JOIN tests t ON stages.test_id = t.id
        LEFT JOIN questions_with_answers qa ON qa.test_id = t.id AND qa.stage = stages.stage
    )
    SELECT 
        (SELECT cand_data FROM candidate_info) as candidate_data,
        jsonb_object_agg(stages.stage, test_data) as tests_data
    FROM test_data stages
    GROUP BY 1;
END;
$$;