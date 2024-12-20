INSERT INTO users (id, first_name, last_name, email, phone, can_edit_tests) VALUES 
(1, 'Maciej', 'Szulc', 'maciej.szulc@pomagier.info', null, true),
(2, 'Agnieszka', 'Chomicka', 'agnieszka.chomicka@avenatech.pl', null, true),
(3, 'Sebastian', 'Krajna', 'sebastian.krajna@pomagier.info', null, true),
(4, 'Agnieszka', 'Lubińska', 'agnieszka.lubinska@montessori.gda.pl', null, true),
(5, 'Piotr', 'Jordan', 'piotr.jordan@pomagier.info', null, true);

INSERT INTO groups (id, name) VALUES             
(1, 'Avena'),              
(2, 'Robotics'),     
(3, 'Liceum'),
(4, 'SPJ5A'),
(5, 'PJ5A'),
(6, 'SPKG74'),
(7, 'P74'),
(8, 'P27'),
(9, 'Munchies');

INSERT INTO link_groups_users (group_id, user_id) VALUES
-- Maciej Szulc
(1, 1),
(2, 1),
(3, 1),
(4, 1),
(5, 1),
(6, 1),
(7, 1),
(8, 1),
(9, 1),
-- Agnieszka Chomicka
(1, 2),
(2, 2),
(3, 2),
(4, 2),
(5, 2),
(6, 2),
(7, 2),
(8, 2),
(9, 2),
-- Sebastian Krajna
(1, 3),
(2, 3),
(3, 3),
(4, 3),
(5, 3),
(6, 3),
(7, 3),
(8, 3),
(9, 3), 
-- Agnieszka Lubińska
(1, 4),
(2, 4),
(3, 4),
(4, 4),
(5, 4),
(6, 4),
(7, 4),
(8, 4),
(9, 4), 
-- Piotr Jordan
(1, 5),
(2, 5),
(9, 5);