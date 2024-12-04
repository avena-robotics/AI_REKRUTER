-- Clear existing data (w odwrotnej kolejności niż zależności)
TRUNCATE TABLE candidate_answers CASCADE;
TRUNCATE TABLE candidates CASCADE;
TRUNCATE TABLE link_groups_tests CASCADE;
TRUNCATE TABLE link_groups_campaigns CASCADE;
TRUNCATE TABLE link_groups_users CASCADE;
TRUNCATE TABLE questions CASCADE;
TRUNCATE TABLE campaigns CASCADE;
TRUNCATE TABLE tests CASCADE;
TRUNCATE TABLE groups CASCADE;
TRUNCATE TABLE users CASCADE;