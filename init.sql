-- DROP SCHEMA IF EXISTS cap2240db;

GRANT SELECT, UPDATE, INSERT, DELETE ON cap2240db.* TO 'cap-2240'@'%';

DROP TRIGGER IF EXISTS `cap2240db`.`auth_user_AFTER_INSERT`;

DELIMITER $$
USE `cap2240db`$$
CREATE DEFINER = CURRENT_USER TRIGGER `cap2240db`.`auth_user_AFTER_INSERT` AFTER INSERT ON `auth_user` FOR EACH ROW
BEGIN
	DECLARE guac_entity_id INT;
    
    -- Insert the new user into guacamole_entity
    INSERT INTO guacamole_db.guacamole_entity (name, type) VALUES (NEW.username, 'USER');

    -- Get the entity_id of the new user
    SELECT entity_id INTO guac_entity_id FROM guacamole_db.guacamole_entity WHERE name = NEW.username;

    -- Insert the new user into guacamole_user
    INSERT INTO guacamole_db.guacamole_user (entity_id, password_hash, password_salt, password_date, disabled, expired)
    VALUES (guac_entity_id, SHA2(NEW.password, 256), UNHEX(SHA2(UUID(), 256)), NOW(), 0, 0);

    -- Optionally, grant default permissions to the new user
    -- INSERT INTO guacamole_system_permission (entity_id, permission)
    -- VALUES (guac_entity_id, 'CREATE_CONNECTION');
    -- INSERT INTO guacamole_system_permission (entity_id, permission)
    -- VALUES (guac_entity_id, 'CREATE_USER');
END$$
DELIMITER ;


INSERT INTO cap2240db.ticketing_vmtemplates (vm_id, vm_name, cores, ram, storage) VALUES
("3000", "Ubuntu-Desktop-22-RDP", 1, 1024, 20),
("4000", "Ubuntu-Desktop-24-RDP", 1, 1024, 20),
("5000", "Ubuntu-LXC-23", 1, 1024, 10);

INSERT INTO cap2240db.auth_user (password, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) VALUES
("pbkdf2_sha256$720000$5gL9pa3JAHZYMUbNgW3qqL$udv7QLPHZ/Fv5ijQQMvklg06MOZvEkkbGY2LJ17dIyM=", "1", "admin", "admin", "chan", "", "1", "1", NOW()),
("pbkdf2_sha256$720000$5gL9pa3JAHZYMUbNgW3qqL$udv7QLPHZ/Fv5ijQQMvklg06MOZvEkkbGY2LJ17dIyM=", "0", "faculty", "faculty", "chan", "", "1", "1", NOW());

INSERT INTO cap2240db.ticketing_userprofile (user_type, user_id) VALUES
("admin", 1),
("faculty", 2);

INSERT INTO guacamole_entity (name, type) VALUES ('jin', 'USER');

INSERT INTO guacamole_db.guacamole_user (entity_id,password_hash, password_salt, password_date, disabled, expired)
VALUES (
	2,
    UNHEX(SHA2(CONCAT('123456', 'SALT'), 256)),
    'SALT',
    NOW(),
    0,
    0
);