-- Wprowadzanie danych w kolejności zależności
-- 1. Najpierw users (brak zależności)
INSERT INTO users (id, first_name, last_name, email, phone, can_edit_tests) VALUES 
(2, 'Sebastian', 'Krajna', 'sebastian.krajna@pomagier.info', null, true),
(3, 'Maciej', 'Szulc', 'maciej.szulc@pomagier.info', null, true);

-- 2. Grupy (brak zależności)
INSERT INTO groups (id, name) VALUES             
(2, 'Grupa Sebastian'),              
(3, 'Grupa Sebastian i Maciej'),     
(4, 'Grupa Maciej');                 

-- 3. Powiązania użytkowników z grupami
INSERT INTO link_groups_users (group_id, user_id) VALUES
(2, 2),                    
(3, 2), (3, 3),           
(4, 3);                    
