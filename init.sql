GRANT SELECT, UPDATE, INSERT, DELETE ON cap2240db.* TO 'cap-2240'@'%';

-- Triggers
DROP TRIGGER IF EXISTS `cap2240db`.`create_guac_user`;

DELIMITER $$
USE `cap2240db`$$
CREATE DEFINER=`root`@`%` TRIGGER `create_guac_user` AFTER INSERT ON `auth_user` FOR EACH ROW BEGIN
	DECLARE guac_entity_id INT;
    SET @salt = UNHEX(SHA2(UUID(), 256));
    
    -- INSERT guacamole_user into cap2240db
    INSERT INTO cap2240db.guacamole_guacamoleuser (username, password, system_user_id, status)
    VALUES (NEW.username, NEW.password, NEW.id, 'ACTIVE');
    
    -- INSERT the new system user into guacamole_db.guacamole_entity
    INSERT INTO guacamole_db.guacamole_entity (name, type) VALUES (NEW.username, 'USER');

    -- Get the entity_id of the new system user
    SELECT entity_id INTO guac_entity_id FROM guacamole_db.guacamole_entity WHERE name = NEW.username;

    -- INSERT the new system user into guacamole_db.guacamole_user
    INSERT INTO guacamole_db.guacamole_user (entity_id, password_salt, password_hash, password_date, disabled, expired)
	VALUES (
		guac_entity_id, @salt, UNHEX(SHA2(CONCAT(NEW.password, HEX(@salt)), 256)), NOW(), 0, 0);
        
    -- TODO: Add system_admin_account to guacamole_admin_group
END$$
DELIMITER ;

-- guacamole_db
-- TODO: Create INSERT statement to create admin user group

-- cap2240db

INSERT INTO cap2240db.ticketing_vmtemplates (vm_id, vm_name, cores, ram, storage) VALUES
("3000", "Ubuntu-Desktop-22-RDP", 1, 1024, 20),
("4000", "Ubuntu-Desktop-24-RDP", 1, 1024, 20),
("5000", "Ubuntu-LXC-23", 1, 1024, 10);

INSERT INTO cap2240db.auth_user (password, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) VALUES
("pbkdf2_sha256$720000$5gL9pa3JAHZYMUbNgW3qqL$udv7QLPHZ/Fv5ijQQMvklg06MOZvEkkbGY2LJ17dIyM=", "1", "admin", "admin", "chan", "", "1", "1", NOW());

INSERT INTO cap2240db.ticketing_userprofile (user_type, user_id) VALUES
("admin", 1);