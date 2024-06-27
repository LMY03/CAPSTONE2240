-- DROP SCHEMA IF EXISTS cap2240db;

GRANT SELECT, UPDATE, INSERT, DELETE ON cap2240db.* TO 'cap-2240'@'%';

INSERT INTO cap2240db.ticketing_vmtemplates (vm_id, vm_name, cores, ram) VALUES
("3000", "Ubuntu-Desktop-22-RDP", 1, 1024),
("4000", "Ubuntu-Desktop-24-RDP", 1, 1024),
("5000", "Ubuntu-LXC-23", 1, 1024);

INSERT INTO cap2240db.proxmox_vmuser (vm_id, username, password)
SELECT id, "jin", "123456"
FROM cap2240db.proxmox_virtualmachines
WHERE ip_add IS NULL
AND status = 'SHUTDOWN';

INSERT INTO cap2240db.auth_user (password, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) VALUES
("pbkdf2_sha256$720000$5gL9pa3JAHZYMUbNgW3qqL$udv7QLPHZ/Fv5ijQQMvklg06MOZvEkkbGY2LJ17dIyM=", "1", "admin", "admin", "chan", "", "1", "1", NOW()),
("pbkdf2_sha256$720000$5gL9pa3JAHZYMUbNgW3qqL$udv7QLPHZ/Fv5ijQQMvklg06MOZvEkkbGY2LJ17dIyM=", "0", "faculty", "faculty", "chan", "", "1", "1", NOW());

INSERT INTO cap2240db.ticketing_userprofile (user_type, user_id) VALUES
("admin", 1),
("faculty", 2);