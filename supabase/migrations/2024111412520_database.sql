-- Tabela kampanii
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
    created_at timestamp default now(),
    updated_at timestamp default now()
);

-- Typ testu enum
create type test_type as enum ('SURVEY', 'EQ', 'IQ');

-- Etap testu enum
create type test_stage as enum ('PO1', 'PO2', 'PO3');

-- Tabela testów
create table tests (
    id serial primary key,
    campaign_id bigint references campaigns(id) ON DELETE CASCADE,    -- Dodane ON DELETE CASCADE
    test_type test_type not null,    -- SURVEY, EQ, IQ
    stage test_stage not null,       -- PO1, PO2, PO3
    description text,                -- Czas wykonania testu to.. lub inne informacje?
    passing_threshold int not null,  -- Minimum score to pass this stage
    time_limit_minutes int,          -- Time limit in minutes
    weight int                       -- Waga testu
);

-- Typ odpowiedzi enum
create type answer_type as enum ('TEXT', 'BOOLEAN', 'SCALE', 'SALARY', 'DATE', 'ABCD');

-- Tabela pytań
create table questions (
    id serial primary key,
    test_id integer references tests(id),           -- Id testu
    question_text text not null,                    -- Pytanie do kandydata     
    answer_type answer_type not null,               -- TEXT, BOOLEAN, SCALE(0-5), SALARY, DATE, ABCD
    answer_a text,
    answer_b text,
    answer_c text,
    answer_d text,
    points int not null default 0,                  -- Punkty za pytanie
    order_number integer not null,                  -- Numer pytania w testach
    is_required boolean default true,               -- Czy pytanie jest obowiązkowe
    image text,                                     -- Add image URL field
    correct_answer_text text,
    correct_answer_boolean boolean,
    correct_answer_numeric numeric,
    correct_answer_scale int,
    correct_answer_date date,
    correct_answer_abcd text
);

-- Status rekrutacji enum
create type recruitment_status as enum ('PO1', 'PO2', 'PO3', 'PO4', 'REJECTED', 'ACCEPTED');

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
    po1_completed_at timestamp with time zone,           -- Data zakończenia testu PO1
    po2_completed_at timestamp with time zone,          -- Data zakończenia testu PO2
    po3_completed_at timestamp with time zone,          -- Data zakończenia testu PO3
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
    candidate_id bigint references candidates(id),
    question_id integer references questions(id),
    text_answer text,                              -- Odpowiedź tekstowa    
    boolean_answer boolean,                        -- Odpowiedź typu boolean
    numeric_answer numeric,                        -- Odpowiedź typu numeric
    scale_answer int,                              -- Odpowiedź typu scale
    date_answer date,                              -- Odpowiedź typu date
    abcd_answer text,                              -- Odpowiedź typu ABCD
    score int,                                     -- Punkty za odpowiedź
    score_ai int,                                  -- Punkty za odpowiedź AI
    created_at timestamp default now()
);
