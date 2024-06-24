DROP SCHEMA IF EXISTS cap2240db;

INSERT INTO cap2240db.ticketing_vmtemplates (vm_id, vm_name, storage) VALUES
("3000", "Ubuntu-Desktop-22-RDP", 20),
("4000", "Ubuntu-Desktop-24-RDP", 20),
("5000", "Ubuntu-LXC-23", 10);

INSERT INTO cap2240db.auth_user (password, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) VALUES
("pbkdf2_sha256$720000$5gL9pa3JAHZYMUbNgW3qqL$udv7QLPHZ/Fv5ijQQMvklg06MOZvEkkbGY2LJ17dIyM=", "1", "admin", "", "", "", "1", "1", NOW()),
("pbkdf2_sha256$720000$5gL9pa3JAHZYMUbNgW3qqL$udv7QLPHZ/Fv5ijQQMvklg06MOZvEkkbGY2LJ17dIyM=", "1", "faculty", "", "", "", "1", "1", NOW());

INSERT INTO cap2240.ticketing_userprofile (user_type, user_id) VALUES
("admin", 1),
("faculty", 2);