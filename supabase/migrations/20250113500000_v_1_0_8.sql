-- Dodanie kolumn do tabeli users
ALTER TABLE users 
ADD COLUMN password text,
ADD COLUMN auth_source text CHECK (auth_source IN ('email', 'ldap')) NOT NULL DEFAULT 'ldap',
ADD COLUMN is_active boolean NOT NULL DEFAULT true;

-- Dodanie indeksu dla szybszego wyszukiwania
CREATE INDEX idx_users_email_auth ON users(email, auth_source);

-- Dodanie unikalnego constraintu dla email w ramach auth_source
ALTER TABLE users 
ADD CONSTRAINT unique_email_per_auth_source UNIQUE (email, auth_source); 