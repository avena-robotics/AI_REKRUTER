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
create type test_type as enum ('SURVEY', 'EQ', 'IQ');
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
    section text,                                                   -- Dla testów EQ sekcje I-VII  
    question_text text not null,                                    -- Pytanie do kandydata     
    answer_type answer_type not null,                               -- TEXT, BOOLEAN, SCALE(0-5), SALARY, DATE, ABCDEF, AH_POINTS
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
    total_score int,                                -- 310  
    po1_completed_at timestamp with time zone,      -- Data zakończenia testu PO1
    po2_completed_at timestamp with time zone,      -- Data zakończenia testu PO2
    po3_completed_at timestamp with time zone,      -- Data zakończenia testu PO3
    access_token_po2 text,                          -- token do testu PO2
    access_token_po3 text,                          -- token do testu PO3
    access_token_po2_is_used boolean default false, -- Czy token PO2 został użyty
    access_token_po3_is_used boolean default false, -- Czy token PO3 został użyty
    access_token_po2_expires_at timestamp with time zone, -- Data ważności tokenu PO2
    access_token_po3_expires_at timestamp with time zone, -- Data ważności tokenu PO3
    created_at timestamp default now(),
    updated_at timestamp default now()
);

-- Tabela odpowiedzi kandydatów
create table candidate_answers (
    id bigserial primary key,
    candidate_id bigint references candidates(id) ON DELETE CASCADE,
    question_id integer references questions(id),
    text_answer text,                              -- Odpowiedź tekstowa    
    boolean_answer boolean,                        -- Odpowiedź typu boolean
    numeric_answer numeric,                        -- Odpowiedź typu numeric
    scale_answer int,                              -- Odpowiedź typu scale
    date_answer date,                              -- Odpowiedź typu date
    abcdef_answer text,                            -- Odpowiedź typu ABCDEF
    ah_points jsonb,                               -- Format JSON, np. {"a": 3, "b": 5, "c": 0}
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
