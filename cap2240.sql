--
-- Licensed to the Apache Software Foundation (ASF) under one
-- or more contributor license agreements.  See the NOTICE file
-- distributed with this work for additional information
-- regarding copyright ownership.  The ASF licenses this file
-- to you under the Apache License, Version 2.0 (the
-- "License"); you may not use this file except in compliance
-- with the License.  You may obtain a copy of the License at
--
--   http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing,
-- software distributed under the License is distributed on an
-- "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
-- KIND, either express or implied.  See the License for the
-- specific language governing permissions and limitations
-- under the License.
--

--
-- Table of connection groups. Each connection group has a name.
--
CREATE DATABASE IF NOT EXISTS guacamole_db;

CREATE USER IF NOT EXISTS 'guacadmin'@'%' IDENTIFIED BY 'guacpassword';

GRANT SELECT, UPDATE, INSERT, DELETE ON guacamole_db.* TO 'guacadmin'@'%';

flush privileges;

use guacamole_db;

CREATE TABLE `guacamole_connection_group` (

  `connection_group_id`   int(11)      NOT NULL AUTO_INCREMENT,
  `parent_id`             int(11),
  `connection_group_name` varchar(128) NOT NULL,
  `type`                  enum('ORGANIZATIONAL',
                               'BALANCING') NOT NULL DEFAULT 'ORGANIZATIONAL',

  -- Concurrency limits
  `max_connections`          int(11),
  `max_connections_per_user` int(11),
  `enable_session_affinity`  boolean NOT NULL DEFAULT 0,

  PRIMARY KEY (`connection_group_id`),
  UNIQUE KEY `connection_group_name_parent` (`connection_group_name`, `parent_id`),

  CONSTRAINT `guacamole_connection_group_ibfk_1`
    FOREIGN KEY (`parent_id`)
    REFERENCES `guacamole_connection_group` (`connection_group_id`) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of connections. Each connection has a name, protocol, and
-- associated set of parameters.
-- A connection may belong to a connection group.
--

CREATE TABLE `guacamole_connection` (

  `connection_id`       int(11)      NOT NULL AUTO_INCREMENT,
  `connection_name`     varchar(128) NOT NULL,
  `parent_id`           int(11),
  `protocol`            varchar(32)  NOT NULL,
  
  -- Guacamole proxy (guacd) overrides
  `proxy_port`              integer,
  `proxy_hostname`          varchar(512),
  `proxy_encryption_method` enum('NONE', 'SSL'),

  -- Concurrency limits
  `max_connections`          int(11),
  `max_connections_per_user` int(11),
  
  -- Load-balancing behavior
  `connection_weight`        int(11),
  `failover_only`            boolean NOT NULL DEFAULT 0,

  PRIMARY KEY (`connection_id`),
  UNIQUE KEY `connection_name_parent` (`connection_name`, `parent_id`),

  CONSTRAINT `guacamole_connection_ibfk_1`
    FOREIGN KEY (`parent_id`)
    REFERENCES `guacamole_connection_group` (`connection_group_id`) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of base entities which may each be either a user or user group. Other
-- tables which represent qualities shared by both users and groups will point
-- to guacamole_entity, while tables which represent qualities specific to
-- users or groups will point to guacamole_user or guacamole_user_group.
--

CREATE TABLE `guacamole_entity` (

  `entity_id`     int(11)            NOT NULL AUTO_INCREMENT,
  `name`          varchar(128)       NOT NULL,
  `type`          enum('USER',
                       'USER_GROUP') NOT NULL,

  PRIMARY KEY (`entity_id`),
  UNIQUE KEY `guacamole_entity_name_scope` (`type`, `name`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of users. Each user has a unique username and a hashed password
-- with corresponding salt. Although the authentication system will always set
-- salted passwords, other systems may set unsalted passwords by simply not
-- providing the salt.
--

CREATE TABLE `guacamole_user` (

  `user_id`       int(11)      NOT NULL AUTO_INCREMENT,
  `entity_id`     int(11)      NOT NULL,

  -- Optionally-salted password
  `password_hash` binary(32)   NOT NULL,
  `password_salt` binary(32),
  `password_date` datetime     NOT NULL,

  -- Account disabled/expired status
  `disabled`      boolean      NOT NULL DEFAULT 0,
  `expired`       boolean      NOT NULL DEFAULT 0,

  -- Time-based access restriction
  `access_window_start`    TIME,
  `access_window_end`      TIME,

  -- Date-based access restriction
  `valid_from`  DATE,
  `valid_until` DATE,

  -- Timezone used for all date/time comparisons and interpretation
  `timezone` VARCHAR(64),

  -- Profile information
  `full_name`           VARCHAR(256),
  `email_address`       VARCHAR(256),
  `organization`        VARCHAR(256),
  `organizational_role` VARCHAR(256),

  PRIMARY KEY (`user_id`),

  UNIQUE KEY `guacamole_user_single_entity` (`entity_id`),

  CONSTRAINT `guacamole_user_entity`
    FOREIGN KEY (`entity_id`)
    REFERENCES `guacamole_entity` (`entity_id`)
    ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of user groups. Each user group may have an arbitrary set of member
-- users and member groups, with those members inheriting the permissions
-- granted to that group.
--

CREATE TABLE `guacamole_user_group` (

  `user_group_id` int(11)      NOT NULL AUTO_INCREMENT,
  `entity_id`     int(11)      NOT NULL,

  -- Group disabled status
  `disabled`      boolean      NOT NULL DEFAULT 0,

  PRIMARY KEY (`user_group_id`),

  UNIQUE KEY `guacamole_user_group_single_entity` (`entity_id`),

  CONSTRAINT `guacamole_user_group_entity`
    FOREIGN KEY (`entity_id`)
    REFERENCES `guacamole_entity` (`entity_id`)
    ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of users which are members of given user groups.
--

CREATE TABLE `guacamole_user_group_member` (

  `user_group_id`    int(11)     NOT NULL,
  `member_entity_id` int(11)     NOT NULL,

  PRIMARY KEY (`user_group_id`, `member_entity_id`),

  -- Parent must be a user group
  CONSTRAINT `guacamole_user_group_member_parent_id`
    FOREIGN KEY (`user_group_id`)
    REFERENCES `guacamole_user_group` (`user_group_id`) ON DELETE CASCADE,

  -- Member may be either a user or a user group (any entity)
  CONSTRAINT `guacamole_user_group_member_entity_id`
    FOREIGN KEY (`member_entity_id`)
    REFERENCES `guacamole_entity` (`entity_id`) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of sharing profiles. Each sharing profile has a name, associated set
-- of parameters, and a primary connection. The primary connection is the
-- connection that the sharing profile shares, and the parameters dictate the
-- restrictions/features which apply to the user joining the connection via the
-- sharing profile.
--

CREATE TABLE guacamole_sharing_profile (

  `sharing_profile_id`    int(11)      NOT NULL AUTO_INCREMENT,
  `sharing_profile_name`  varchar(128) NOT NULL,
  `primary_connection_id` int(11)      NOT NULL,

  PRIMARY KEY (`sharing_profile_id`),
  UNIQUE KEY `sharing_profile_name_primary` (sharing_profile_name, primary_connection_id),

  CONSTRAINT `guacamole_sharing_profile_ibfk_1`
    FOREIGN KEY (`primary_connection_id`)
    REFERENCES `guacamole_connection` (`connection_id`)
    ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of connection parameters. Each parameter is simply a name/value pair
-- associated with a connection.
--

CREATE TABLE `guacamole_connection_parameter` (

  `connection_id`   int(11)       NOT NULL,
  `parameter_name`  varchar(128)  NOT NULL,
  `parameter_value` varchar(4096) NOT NULL,

  PRIMARY KEY (`connection_id`,`parameter_name`),

  CONSTRAINT `guacamole_connection_parameter_ibfk_1`
    FOREIGN KEY (`connection_id`)
    REFERENCES `guacamole_connection` (`connection_id`) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of sharing profile parameters. Each parameter is simply
-- name/value pair associated with a sharing profile. These parameters dictate
-- the restrictions/features which apply to the user joining the associated
-- connection via the sharing profile.
--

CREATE TABLE guacamole_sharing_profile_parameter (

  `sharing_profile_id` integer       NOT NULL,
  `parameter_name`     varchar(128)  NOT NULL,
  `parameter_value`    varchar(4096) NOT NULL,

  PRIMARY KEY (`sharing_profile_id`, `parameter_name`),

  CONSTRAINT `guacamole_sharing_profile_parameter_ibfk_1`
    FOREIGN KEY (`sharing_profile_id`)
    REFERENCES `guacamole_sharing_profile` (`sharing_profile_id`) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of arbitrary user attributes. Each attribute is simply a name/value
-- pair associated with a user. Arbitrary attributes are defined by other
-- extensions. Attributes defined by this extension will be mapped to
-- properly-typed columns of a specific table.
--

CREATE TABLE guacamole_user_attribute (

  `user_id`         int(11)       NOT NULL,
  `attribute_name`  varchar(128)  NOT NULL,
  `attribute_value` varchar(4096) NOT NULL,

  PRIMARY KEY (user_id, attribute_name),
  KEY `user_id` (`user_id`),

  CONSTRAINT guacamole_user_attribute_ibfk_1
    FOREIGN KEY (user_id)
    REFERENCES guacamole_user (user_id) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of arbitrary user group attributes. Each attribute is simply a
-- name/value pair associated with a user group. Arbitrary attributes are
-- defined by other extensions. Attributes defined by this extension will be
-- mapped to properly-typed columns of a specific table.
--

CREATE TABLE guacamole_user_group_attribute (

  `user_group_id`   int(11)       NOT NULL,
  `attribute_name`  varchar(128)  NOT NULL,
  `attribute_value` varchar(4096) NOT NULL,

  PRIMARY KEY (`user_group_id`, `attribute_name`),
  KEY `user_group_id` (`user_group_id`),

  CONSTRAINT `guacamole_user_group_attribute_ibfk_1`
    FOREIGN KEY (`user_group_id`)
    REFERENCES `guacamole_user_group` (`user_group_id`) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of arbitrary connection attributes. Each attribute is simply a
-- name/value pair associated with a connection. Arbitrary attributes are
-- defined by other extensions. Attributes defined by this extension will be
-- mapped to properly-typed columns of a specific table.
--

CREATE TABLE guacamole_connection_attribute (

  `connection_id`   int(11)       NOT NULL,
  `attribute_name`  varchar(128)  NOT NULL,
  `attribute_value` varchar(4096) NOT NULL,

  PRIMARY KEY (connection_id, attribute_name),
  KEY `connection_id` (`connection_id`),

  CONSTRAINT guacamole_connection_attribute_ibfk_1
    FOREIGN KEY (connection_id)
    REFERENCES guacamole_connection (connection_id) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of arbitrary connection group attributes. Each attribute is simply a
-- name/value pair associated with a connection group. Arbitrary attributes are
-- defined by other extensions. Attributes defined by this extension will be
-- mapped to properly-typed columns of a specific table.
--

CREATE TABLE guacamole_connection_group_attribute (

  `connection_group_id` int(11)       NOT NULL,
  `attribute_name`      varchar(128)  NOT NULL,
  `attribute_value`     varchar(4096) NOT NULL,

  PRIMARY KEY (connection_group_id, attribute_name),
  KEY `connection_group_id` (`connection_group_id`),

  CONSTRAINT guacamole_connection_group_attribute_ibfk_1
    FOREIGN KEY (connection_group_id)
    REFERENCES guacamole_connection_group (connection_group_id) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of arbitrary sharing profile attributes. Each attribute is simply a
-- name/value pair associated with a sharing profile. Arbitrary attributes are
-- defined by other extensions. Attributes defined by this extension will be
-- mapped to properly-typed columns of a specific table.
--

CREATE TABLE guacamole_sharing_profile_attribute (

  `sharing_profile_id` int(11)       NOT NULL,
  `attribute_name`     varchar(128)  NOT NULL,
  `attribute_value`    varchar(4096) NOT NULL,

  PRIMARY KEY (sharing_profile_id, attribute_name),
  KEY `sharing_profile_id` (`sharing_profile_id`),

  CONSTRAINT guacamole_sharing_profile_attribute_ibfk_1
    FOREIGN KEY (sharing_profile_id)
    REFERENCES guacamole_sharing_profile (sharing_profile_id) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of connection permissions. Each connection permission grants a user or
-- user group specific access to a connection.
--

CREATE TABLE `guacamole_connection_permission` (

  `entity_id`     int(11) NOT NULL,
  `connection_id` int(11) NOT NULL,
  `permission`    enum('READ',
                       'UPDATE',
                       'DELETE',
                       'ADMINISTER') NOT NULL,

  PRIMARY KEY (`entity_id`,`connection_id`,`permission`),

  CONSTRAINT `guacamole_connection_permission_ibfk_1`
    FOREIGN KEY (`connection_id`)
    REFERENCES `guacamole_connection` (`connection_id`) ON DELETE CASCADE,

  CONSTRAINT `guacamole_connection_permission_entity`
    FOREIGN KEY (`entity_id`)
    REFERENCES `guacamole_entity` (`entity_id`) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of connection group permissions. Each group permission grants a user
-- or user group specific access to a connection group.
--

CREATE TABLE `guacamole_connection_group_permission` (

  `entity_id`           int(11) NOT NULL,
  `connection_group_id` int(11) NOT NULL,
  `permission`          enum('READ',
                             'UPDATE',
                             'DELETE',
                             'ADMINISTER') NOT NULL,

  PRIMARY KEY (`entity_id`,`connection_group_id`,`permission`),

  CONSTRAINT `guacamole_connection_group_permission_ibfk_1`
    FOREIGN KEY (`connection_group_id`)
    REFERENCES `guacamole_connection_group` (`connection_group_id`) ON DELETE CASCADE,

  CONSTRAINT `guacamole_connection_group_permission_entity`
    FOREIGN KEY (`entity_id`)
    REFERENCES `guacamole_entity` (`entity_id`) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of sharing profile permissions. Each sharing profile permission grants
-- a user or user group specific access to a sharing profile.
--

CREATE TABLE guacamole_sharing_profile_permission (

  `entity_id`          integer NOT NULL,
  `sharing_profile_id` integer NOT NULL,
  `permission`         enum('READ',
                            'UPDATE',
                            'DELETE',
                            'ADMINISTER') NOT NULL,

  PRIMARY KEY (`entity_id`, `sharing_profile_id`, `permission`),

  CONSTRAINT `guacamole_sharing_profile_permission_ibfk_1`
    FOREIGN KEY (`sharing_profile_id`)
    REFERENCES `guacamole_sharing_profile` (`sharing_profile_id`) ON DELETE CASCADE,

  CONSTRAINT `guacamole_sharing_profile_permission_entity`
    FOREIGN KEY (`entity_id`)
    REFERENCES `guacamole_entity` (`entity_id`) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of system permissions. Each system permission grants a user or user
-- group a system-level privilege of some kind.
--

CREATE TABLE `guacamole_system_permission` (

  `entity_id`  int(11) NOT NULL,
  `permission` enum('CREATE_CONNECTION',
                    'CREATE_CONNECTION_GROUP',
                    'CREATE_SHARING_PROFILE',
                    'CREATE_USER',
                    'CREATE_USER_GROUP',
                    'ADMINISTER') NOT NULL,

  PRIMARY KEY (`entity_id`,`permission`),

  CONSTRAINT `guacamole_system_permission_entity`
    FOREIGN KEY (`entity_id`)
    REFERENCES `guacamole_entity` (`entity_id`) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of user permissions. Each user permission grants a user or user group
-- access to another user (the "affected" user) for a specific type of
-- operation.
--

CREATE TABLE `guacamole_user_permission` (

  `entity_id`        int(11) NOT NULL,
  `affected_user_id` int(11) NOT NULL,
  `permission`       enum('READ',
                          'UPDATE',
                          'DELETE',
                          'ADMINISTER') NOT NULL,

  PRIMARY KEY (`entity_id`,`affected_user_id`,`permission`),

  CONSTRAINT `guacamole_user_permission_ibfk_1`
    FOREIGN KEY (`affected_user_id`)
    REFERENCES `guacamole_user` (`user_id`) ON DELETE CASCADE,

  CONSTRAINT `guacamole_user_permission_entity`
    FOREIGN KEY (`entity_id`)
    REFERENCES `guacamole_entity` (`entity_id`) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of user group permissions. Each user group permission grants a user
-- or user group access to a another user group (the "affected" user group) for
-- a specific type of operation.
--

CREATE TABLE `guacamole_user_group_permission` (

  `entity_id`              int(11) NOT NULL,
  `affected_user_group_id` int(11) NOT NULL,
  `permission`             enum('READ',
                                'UPDATE',
                                'DELETE',
                                'ADMINISTER') NOT NULL,

  PRIMARY KEY (`entity_id`, `affected_user_group_id`, `permission`),

  CONSTRAINT `guacamole_user_group_permission_affected_user_group`
    FOREIGN KEY (`affected_user_group_id`)
    REFERENCES `guacamole_user_group` (`user_group_id`) ON DELETE CASCADE,

  CONSTRAINT `guacamole_user_group_permission_entity`
    FOREIGN KEY (`entity_id`)
    REFERENCES `guacamole_entity` (`entity_id`) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table of connection history records. Each record defines a specific user's
-- session, including the connection used, the start time, and the end time
-- (if any).
--

CREATE TABLE `guacamole_connection_history` (

  `history_id`           int(11)      NOT NULL AUTO_INCREMENT,
  `user_id`              int(11)      DEFAULT NULL,
  `username`             varchar(128) NOT NULL,
  `remote_host`          varchar(256) DEFAULT NULL,
  `connection_id`        int(11)      DEFAULT NULL,
  `connection_name`      varchar(128) NOT NULL,
  `sharing_profile_id`   int(11)      DEFAULT NULL,
  `sharing_profile_name` varchar(128) DEFAULT NULL,
  `start_date`           datetime     NOT NULL,
  `end_date`             datetime     DEFAULT NULL,

  PRIMARY KEY (`history_id`),
  KEY `user_id` (`user_id`),
  KEY `connection_id` (`connection_id`),
  KEY `sharing_profile_id` (`sharing_profile_id`),
  KEY `start_date` (`start_date`),
  KEY `end_date` (`end_date`),
  KEY `connection_start_date` (`connection_id`, `start_date`),

  CONSTRAINT `guacamole_connection_history_ibfk_1`
    FOREIGN KEY (`user_id`)
    REFERENCES `guacamole_user` (`user_id`) ON DELETE SET NULL,

  CONSTRAINT `guacamole_connection_history_ibfk_2`
    FOREIGN KEY (`connection_id`)
    REFERENCES `guacamole_connection` (`connection_id`) ON DELETE SET NULL,

  CONSTRAINT `guacamole_connection_history_ibfk_3`
    FOREIGN KEY (`sharing_profile_id`)
    REFERENCES `guacamole_sharing_profile` (`sharing_profile_id`) ON DELETE SET NULL

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- User login/logout history
--

CREATE TABLE guacamole_user_history (

  `history_id`           int(11)      NOT NULL AUTO_INCREMENT,
  `user_id`              int(11)      DEFAULT NULL,
  `username`             varchar(128) NOT NULL,
  `remote_host`          varchar(256) DEFAULT NULL,
  `start_date`           datetime     NOT NULL,
  `end_date`             datetime     DEFAULT NULL,

  PRIMARY KEY (history_id),
  KEY `user_id` (`user_id`),
  KEY `start_date` (`start_date`),
  KEY `end_date` (`end_date`),
  KEY `user_start_date` (`user_id`, `start_date`),

  CONSTRAINT guacamole_user_history_ibfk_1
    FOREIGN KEY (user_id)
    REFERENCES guacamole_user (user_id) ON DELETE SET NULL

) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- User password history
--

CREATE TABLE guacamole_user_password_history (

  `password_history_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id`             int(11) NOT NULL,

  -- Salted password
  `password_hash` binary(32) NOT NULL,
  `password_salt` binary(32),
  `password_date` datetime   NOT NULL,

  PRIMARY KEY (`password_history_id`),
  KEY `user_id` (`user_id`),

  CONSTRAINT `guacamole_user_password_history_ibfk_1`
    FOREIGN KEY (`user_id`)
    REFERENCES `guacamole_user` (`user_id`) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8;
--
-- Licensed to the Apache Software Foundation (ASF) under one
-- or more contributor license agreements.  See the NOTICE file
-- distributed with this work for additional information
-- regarding copyright ownership.  The ASF licenses this file
-- to you under the Apache License, Version 2.0 (the
-- "License"); you may not use this file except in compliance
-- with the License.  You may obtain a copy of the License at
--
--   http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing,
-- software distributed under the License is distributed on an
-- "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
-- KIND, either express or implied.  See the License for the
-- specific language governing permissions and limitations
-- under the License.
--

-- Create default user "guacadmin" with password "guacadmin"
INSERT INTO guacamole_entity (name, type) VALUES ('guacadmin', 'USER');
INSERT INTO guacamole_user (entity_id, password_hash, password_salt, password_date)
SELECT
    entity_id,
    x'CA458A7D494E3BE824F5E1E175A1556C0F8EEF2C2D7DF3633BEC4A29C4411960',  -- 'guacadmin'
    x'FE24ADC5E11E2B25288D1704ABE67A79E342ECC26064CE69C5B3177795A82264',
    NOW()
FROM guacamole_entity WHERE name = 'guacadmin';

-- Grant this user all system permissions
INSERT INTO guacamole_system_permission (entity_id, permission)
SELECT entity_id, permission
FROM (
          SELECT 'guacadmin'  AS username, 'CREATE_CONNECTION'       AS permission
    UNION SELECT 'guacadmin'  AS username, 'CREATE_CONNECTION_GROUP' AS permission
    UNION SELECT 'guacadmin'  AS username, 'CREATE_SHARING_PROFILE'  AS permission
    UNION SELECT 'guacadmin'  AS username, 'CREATE_USER'             AS permission
    UNION SELECT 'guacadmin'  AS username, 'CREATE_USER_GROUP'       AS permission
    UNION SELECT 'guacadmin'  AS username, 'ADMINISTER'              AS permission
) permissions
JOIN guacamole_entity ON permissions.username = guacamole_entity.name AND guacamole_entity.type = 'USER';

-- Grant admin permission to read/update/administer self
INSERT INTO guacamole_user_permission (entity_id, affected_user_id, permission)
SELECT guacamole_entity.entity_id, guacamole_user.user_id, permission
FROM (
          SELECT 'guacadmin' AS username, 'guacadmin' AS affected_username, 'READ'       AS permission
    UNION SELECT 'guacadmin' AS username, 'guacadmin' AS affected_username, 'UPDATE'     AS permission
    UNION SELECT 'guacadmin' AS username, 'guacadmin' AS affected_username, 'ADMINISTER' AS permission
) permissions
JOIN guacamole_entity          ON permissions.username = guacamole_entity.name AND guacamole_entity.type = 'USER'
JOIN guacamole_entity affected ON permissions.affected_username = affected.name AND guacamole_entity.type = 'USER'
JOIN guacamole_user            ON guacamole_user.entity_id = affected.entity_id;


-- MySQL dump 10.13  Distrib 8.0.31, for Win64 (x86_64)
--
-- Host: 192.168.1.9    Database: cap2240db
-- ------------------------------------------------------
-- Server version	8.0.39

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `cap2240db`
--

CREATE DATABASE  IF NOT EXISTS `cap2240db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `cap2240db`;
-- MySQL dump 10.13  Distrib 8.0.31, for Win64 (x86_64)
--
-- Host: localhost    Database: cap2240db
-- ------------------------------------------------------
-- Server version	8.0.39

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=125 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add request entry',1,'add_requestentry'),(2,'Can change request entry',1,'change_requestentry'),(3,'Can delete request entry',1,'delete_requestentry'),(4,'Can view request entry',1,'view_requestentry'),(5,'Can add vm templates',2,'add_vmtemplates'),(6,'Can change vm templates',2,'change_vmtemplates'),(7,'Can delete vm templates',2,'delete_vmtemplates'),(8,'Can view vm templates',2,'view_vmtemplates'),(9,'Can add user profile',3,'add_userprofile'),(10,'Can change user profile',3,'change_userprofile'),(11,'Can delete user profile',3,'delete_userprofile'),(12,'Can view user profile',3,'view_userprofile'),(13,'Can add request use case',4,'add_requestusecase'),(14,'Can change request use case',4,'change_requestusecase'),(15,'Can delete request use case',4,'delete_requestusecase'),(16,'Can view request use case',4,'view_requestusecase'),(17,'Can add request entry audit',5,'add_requestentryaudit'),(18,'Can change request entry audit',5,'change_requestentryaudit'),(19,'Can delete request entry audit',5,'delete_requestentryaudit'),(20,'Can view request entry audit',5,'view_requestentryaudit'),(21,'Can add port rules',6,'add_portrules'),(22,'Can change port rules',6,'change_portrules'),(23,'Can delete port rules',6,'delete_portrules'),(24,'Can view port rules',6,'view_portrules'),(25,'Can add issue ticket',7,'add_issueticket'),(26,'Can change issue ticket',7,'change_issueticket'),(27,'Can delete issue ticket',7,'delete_issueticket'),(28,'Can view issue ticket',7,'view_issueticket'),(29,'Can add issue file',8,'add_issuefile'),(30,'Can change issue file',8,'change_issuefile'),(31,'Can delete issue file',8,'delete_issuefile'),(32,'Can view issue file',8,'view_issuefile'),(33,'Can add comment',9,'add_comment'),(34,'Can change comment',9,'change_comment'),(35,'Can delete comment',9,'delete_comment'),(36,'Can view comment',9,'view_comment'),(37,'Can add guacamole user',10,'add_guacamoleuser'),(38,'Can change guacamole user',10,'change_guacamoleuser'),(39,'Can delete guacamole user',10,'delete_guacamoleuser'),(40,'Can view guacamole user',10,'view_guacamoleuser'),(41,'Can add guacamole connection',11,'add_guacamoleconnection'),(42,'Can change guacamole connection',11,'change_guacamoleconnection'),(43,'Can delete guacamole connection',11,'delete_guacamoleconnection'),(44,'Can view guacamole connection',11,'view_guacamoleconnection'),(45,'Can add destination ports',12,'add_destinationports'),(46,'Can change destination ports',12,'change_destinationports'),(47,'Can delete destination ports',12,'delete_destinationports'),(48,'Can view destination ports',12,'view_destinationports'),(49,'Can add nodes',13,'add_nodes'),(50,'Can change nodes',13,'change_nodes'),(51,'Can delete nodes',13,'delete_nodes'),(52,'Can view nodes',13,'view_nodes'),(53,'Can add virtual machines',14,'add_virtualmachines'),(54,'Can change virtual machines',14,'change_virtualmachines'),(55,'Can delete virtual machines',14,'delete_virtualmachines'),(56,'Can view virtual machines',14,'view_virtualmachines'),(57,'Can add log entry',15,'add_logentry'),(58,'Can change log entry',15,'change_logentry'),(59,'Can delete log entry',15,'delete_logentry'),(60,'Can view log entry',15,'view_logentry'),(61,'Can add permission',16,'add_permission'),(62,'Can change permission',16,'change_permission'),(63,'Can delete permission',16,'delete_permission'),(64,'Can view permission',16,'view_permission'),(65,'Can add group',17,'add_group'),(66,'Can change group',17,'change_group'),(67,'Can delete group',17,'delete_group'),(68,'Can view group',17,'view_group'),(69,'Can add user',18,'add_user'),(70,'Can change user',18,'change_user'),(71,'Can delete user',18,'delete_user'),(72,'Can view user',18,'view_user'),(73,'Can add content type',19,'add_contenttype'),(74,'Can change content type',19,'change_contenttype'),(75,'Can delete content type',19,'delete_contenttype'),(76,'Can view content type',19,'view_contenttype'),(77,'Can add session',20,'add_session'),(78,'Can change session',20,'change_session'),(79,'Can delete session',20,'delete_session'),(80,'Can view session',20,'view_session'),(81,'Can add association',21,'add_association'),(82,'Can change association',21,'change_association'),(83,'Can delete association',21,'delete_association'),(84,'Can view association',21,'view_association'),(85,'Can add code',22,'add_code'),(86,'Can change code',22,'change_code'),(87,'Can delete code',22,'delete_code'),(88,'Can view code',22,'view_code'),(89,'Can add nonce',23,'add_nonce'),(90,'Can change nonce',23,'change_nonce'),(91,'Can delete nonce',23,'delete_nonce'),(92,'Can view nonce',23,'view_nonce'),(93,'Can add user social auth',24,'add_usersocialauth'),(94,'Can change user social auth',24,'change_usersocialauth'),(95,'Can delete user social auth',24,'delete_usersocialauth'),(96,'Can view user social auth',24,'view_usersocialauth'),(97,'Can add partial',25,'add_partial'),(98,'Can change partial',25,'change_partial'),(99,'Can delete partial',25,'delete_partial'),(100,'Can view partial',25,'view_partial'),(101,'Can add crontab',26,'add_crontabschedule'),(102,'Can change crontab',26,'change_crontabschedule'),(103,'Can delete crontab',26,'delete_crontabschedule'),(104,'Can view crontab',26,'view_crontabschedule'),(105,'Can add interval',27,'add_intervalschedule'),(106,'Can change interval',27,'change_intervalschedule'),(107,'Can delete interval',27,'delete_intervalschedule'),(108,'Can view interval',27,'view_intervalschedule'),(109,'Can add periodic task',28,'add_periodictask'),(110,'Can change periodic task',28,'change_periodictask'),(111,'Can delete periodic task',28,'delete_periodictask'),(112,'Can view periodic task',28,'view_periodictask'),(113,'Can add periodic task track',29,'add_periodictasks'),(114,'Can change periodic task track',29,'change_periodictasks'),(115,'Can delete periodic task track',29,'delete_periodictasks'),(116,'Can view periodic task track',29,'view_periodictasks'),(117,'Can add solar event',30,'add_solarschedule'),(118,'Can change solar event',30,'change_solarschedule'),(119,'Can delete solar event',30,'delete_solarschedule'),(120,'Can view solar event',30,'view_solarschedule'),(121,'Can add clocked',31,'add_clockedschedule'),(122,'Can change clocked',31,'change_clockedschedule'),(123,'Can delete clocked',31,'delete_clockedschedule'),(124,'Can view clocked',31,'view_clockedschedule');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$720000$5gL9pa3JAHZYMUbNgW3qqL$udv7QLPHZ/Fv5ijQQMvklg06MOZvEkkbGY2LJ17dIyM=',NULL,1,'admin','admin','chan','',1,1,'2024-09-14 13:54:58.000000'),(2,'pbkdf2_sha256$720000$5gL9pa3JAHZYMUbNgW3qqL$udv7QLPHZ/Fv5ijQQMvklg06MOZvEkkbGY2LJ17dIyM=',NULL,1,'john.doe','John','Doe','jonathan_lin@dlsu.edu.ph',1,1,'2024-09-14 13:54:58.000000'),(3,'pbkdf2_sha256$720000$5gL9pa3JAHZYMUbNgW3qqL$udv7QLPHZ/Fv5ijQQMvklg06MOZvEkkbGY2LJ17dIyM=',NULL,0,'josephine.cruz','Josephine','Cruz','jonathan_lin@dlsu.edu.ph',0,1,'2024-09-14 13:54:58.000000');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`%`*/ /*!50003 TRIGGER `create_guac_user` AFTER INSERT ON `auth_user` FOR EACH ROW BEGIN
	DECLARE guac_entity_id INT;
    SET @salt = UNHEX(SHA2(UUID(), 256));
    
    -- INSERT guacamole_user into cap2240db
    INSERT INTO cap2240db.guacamole_guacamoleuser (username, password, system_user_id, is_active)
    VALUES (NEW.username, NEW.password, NEW.id, 1);
    
    -- INSERT the new system user into guacamole_db.guacamole_entity
    INSERT INTO guacamole_db.guacamole_entity (name, type) VALUES (NEW.username, 'USER');

    -- Get the entity_id of the new system user
    SELECT entity_id INTO guac_entity_id FROM guacamole_db.guacamole_entity WHERE name = NEW.username;

    -- INSERT the new system user into guacamole_db.guacamole_user
    INSERT INTO guacamole_db.guacamole_user (entity_id, password_salt, password_hash, password_date, disabled, expired)
	VALUES (
		guac_entity_id, @salt, UNHEX(SHA2(CONCAT(NEW.password, HEX(@salt)), 256)), NOW(), 0, 0);
        
    -- TODO: Add system_admin_account to guacamole_admin_group
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_celery_beat_clockedschedule`
--

DROP TABLE IF EXISTS `django_celery_beat_clockedschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_celery_beat_clockedschedule` (
  `id` int NOT NULL AUTO_INCREMENT,
  `clocked_time` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_celery_beat_clockedschedule`
--

LOCK TABLES `django_celery_beat_clockedschedule` WRITE;
/*!40000 ALTER TABLE `django_celery_beat_clockedschedule` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_celery_beat_clockedschedule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_celery_beat_crontabschedule`
--

DROP TABLE IF EXISTS `django_celery_beat_crontabschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_celery_beat_crontabschedule` (
  `id` int NOT NULL AUTO_INCREMENT,
  `minute` varchar(240) NOT NULL,
  `hour` varchar(96) NOT NULL,
  `day_of_week` varchar(64) NOT NULL,
  `day_of_month` varchar(124) NOT NULL,
  `month_of_year` varchar(64) NOT NULL,
  `timezone` varchar(63) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_celery_beat_crontabschedule`
--

LOCK TABLES `django_celery_beat_crontabschedule` WRITE;
/*!40000 ALTER TABLE `django_celery_beat_crontabschedule` DISABLE KEYS */;
INSERT INTO `django_celery_beat_crontabschedule` VALUES (1,'0','4','*','*','*','Asia/Manila'),(2,'*','*','*','*','*','Asia/Manila');
/*!40000 ALTER TABLE `django_celery_beat_crontabschedule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_celery_beat_intervalschedule`
--

DROP TABLE IF EXISTS `django_celery_beat_intervalschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_celery_beat_intervalschedule` (
  `id` int NOT NULL AUTO_INCREMENT,
  `every` int NOT NULL,
  `period` varchar(24) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_celery_beat_intervalschedule`
--

LOCK TABLES `django_celery_beat_intervalschedule` WRITE;
/*!40000 ALTER TABLE `django_celery_beat_intervalschedule` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_celery_beat_intervalschedule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_celery_beat_periodictask`
--

DROP TABLE IF EXISTS `django_celery_beat_periodictask`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_celery_beat_periodictask` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `task` varchar(200) NOT NULL,
  `args` longtext NOT NULL,
  `kwargs` longtext NOT NULL,
  `queue` varchar(200) DEFAULT NULL,
  `exchange` varchar(200) DEFAULT NULL,
  `routing_key` varchar(200) DEFAULT NULL,
  `expires` datetime(6) DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `last_run_at` datetime(6) DEFAULT NULL,
  `total_run_count` int unsigned NOT NULL,
  `date_changed` datetime(6) NOT NULL,
  `description` longtext NOT NULL,
  `crontab_id` int DEFAULT NULL,
  `interval_id` int DEFAULT NULL,
  `solar_id` int DEFAULT NULL,
  `one_off` tinyint(1) NOT NULL,
  `start_time` datetime(6) DEFAULT NULL,
  `priority` int unsigned DEFAULT NULL,
  `headers` longtext NOT NULL DEFAULT (_utf8mb3'{}'),
  `clocked_id` int DEFAULT NULL,
  `expire_seconds` int unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `django_celery_beat_p_crontab_id_d3cba168_fk_django_ce` (`crontab_id`),
  KEY `django_celery_beat_p_interval_id_a8ca27da_fk_django_ce` (`interval_id`),
  KEY `django_celery_beat_p_solar_id_a87ce72c_fk_django_ce` (`solar_id`),
  KEY `django_celery_beat_p_clocked_id_47a69f82_fk_django_ce` (`clocked_id`),
  CONSTRAINT `django_celery_beat_p_clocked_id_47a69f82_fk_django_ce` FOREIGN KEY (`clocked_id`) REFERENCES `django_celery_beat_clockedschedule` (`id`),
  CONSTRAINT `django_celery_beat_p_crontab_id_d3cba168_fk_django_ce` FOREIGN KEY (`crontab_id`) REFERENCES `django_celery_beat_crontabschedule` (`id`),
  CONSTRAINT `django_celery_beat_p_interval_id_a8ca27da_fk_django_ce` FOREIGN KEY (`interval_id`) REFERENCES `django_celery_beat_intervalschedule` (`id`),
  CONSTRAINT `django_celery_beat_p_solar_id_a87ce72c_fk_django_ce` FOREIGN KEY (`solar_id`) REFERENCES `django_celery_beat_solarschedule` (`id`),
  CONSTRAINT `django_celery_beat_periodictask_chk_1` CHECK ((`total_run_count` >= 0)),
  CONSTRAINT `django_celery_beat_periodictask_chk_2` CHECK ((`priority` >= 0)),
  CONSTRAINT `django_celery_beat_periodictask_chk_3` CHECK ((`expire_seconds` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_celery_beat_periodictask`
--

LOCK TABLES `django_celery_beat_periodictask` WRITE;
/*!40000 ALTER TABLE `django_celery_beat_periodictask` DISABLE KEYS */;
INSERT INTO `django_celery_beat_periodictask` VALUES (1,'celery.backend_cleanup','celery.backend_cleanup','[]','{}',NULL,NULL,NULL,NULL,1,NULL,0,'2024-09-14 13:52:54.611598','',1,NULL,NULL,0,NULL,NULL,'{}',NULL,43200),(2,'delete-expired-requests','ticketing.tasks.delete_expired_requests','[]','{}',NULL,NULL,NULL,NULL,1,'2024-09-14 13:55:00.002856',3,'2024-09-14 13:55:59.999284','',2,NULL,NULL,0,NULL,NULL,'{}',NULL,NULL);
/*!40000 ALTER TABLE `django_celery_beat_periodictask` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_celery_beat_periodictasks`
--

DROP TABLE IF EXISTS `django_celery_beat_periodictasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_celery_beat_periodictasks` (
  `ident` smallint NOT NULL,
  `last_update` datetime(6) NOT NULL,
  PRIMARY KEY (`ident`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_celery_beat_periodictasks`
--

LOCK TABLES `django_celery_beat_periodictasks` WRITE;
/*!40000 ALTER TABLE `django_celery_beat_periodictasks` DISABLE KEYS */;
INSERT INTO `django_celery_beat_periodictasks` VALUES (1,'2024-09-14 13:52:54.659132');
/*!40000 ALTER TABLE `django_celery_beat_periodictasks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_celery_beat_solarschedule`
--

DROP TABLE IF EXISTS `django_celery_beat_solarschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_celery_beat_solarschedule` (
  `id` int NOT NULL AUTO_INCREMENT,
  `event` varchar(24) NOT NULL,
  `latitude` decimal(9,6) NOT NULL,
  `longitude` decimal(9,6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_celery_beat_solar_event_latitude_longitude_ba64999a_uniq` (`event`,`latitude`,`longitude`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_celery_beat_solarschedule`
--

LOCK TABLES `django_celery_beat_solarschedule` WRITE;
/*!40000 ALTER TABLE `django_celery_beat_solarschedule` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_celery_beat_solarschedule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (15,'admin','logentry'),(17,'auth','group'),(16,'auth','permission'),(18,'auth','user'),(19,'contenttypes','contenttype'),(31,'django_celery_beat','clockedschedule'),(26,'django_celery_beat','crontabschedule'),(27,'django_celery_beat','intervalschedule'),(28,'django_celery_beat','periodictask'),(29,'django_celery_beat','periodictasks'),(30,'django_celery_beat','solarschedule'),(11,'guacamole','guacamoleconnection'),(10,'guacamole','guacamoleuser'),(12,'pfsense','destinationports'),(13,'proxmox','nodes'),(14,'proxmox','virtualmachines'),(20,'sessions','session'),(21,'social_django','association'),(22,'social_django','code'),(23,'social_django','nonce'),(25,'social_django','partial'),(24,'social_django','usersocialauth'),(9,'ticketing','comment'),(8,'ticketing','issuefile'),(7,'ticketing','issueticket'),(6,'ticketing','portrules'),(1,'ticketing','requestentry'),(5,'ticketing','requestentryaudit'),(4,'ticketing','requestusecase'),(3,'ticketing','userprofile'),(2,'ticketing','vmtemplates');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=69 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'django_celery_beat','0001_initial','2024-09-14 13:52:51.614524'),(2,'django_celery_beat','0002_auto_20161118_0346','2024-09-14 13:52:51.844984'),(3,'django_celery_beat','0003_auto_20161209_0049','2024-09-14 13:52:51.904655'),(4,'django_celery_beat','0004_auto_20170221_0000','2024-09-14 13:52:51.920663'),(5,'django_celery_beat','0005_add_solarschedule_events_choices','2024-09-14 13:52:51.929902'),(6,'django_celery_beat','0006_auto_20180322_0932','2024-09-14 13:52:52.132737'),(7,'django_celery_beat','0007_auto_20180521_0826','2024-09-14 13:52:52.276142'),(8,'django_celery_beat','0008_auto_20180914_1922','2024-09-14 13:52:52.321430'),(9,'django_celery_beat','0006_auto_20180210_1226','2024-09-14 13:52:52.351446'),(10,'django_celery_beat','0006_periodictask_priority','2024-09-14 13:52:52.556366'),(11,'django_celery_beat','0009_periodictask_headers','2024-09-14 13:52:52.747148'),(12,'django_celery_beat','0010_auto_20190429_0326','2024-09-14 13:52:53.038120'),(13,'django_celery_beat','0011_auto_20190508_0153','2024-09-14 13:52:53.327650'),(14,'django_celery_beat','0012_periodictask_expire_seconds','2024-09-14 13:52:53.517971'),(15,'django_celery_beat','0013_auto_20200609_0727','2024-09-14 13:52:53.541901'),(16,'django_celery_beat','0014_remove_clockedschedule_enabled','2024-09-14 13:52:53.586723'),(17,'django_celery_beat','0015_edit_solarschedule_events_choices','2024-09-14 13:52:53.599573'),(18,'django_celery_beat','0016_alter_crontabschedule_timezone','2024-09-14 13:52:53.619294'),(19,'django_celery_beat','0017_alter_crontabschedule_month_of_year','2024-09-14 13:52:53.634791'),(20,'django_celery_beat','0018_improve_crontab_helptext','2024-09-14 13:52:53.652533'),(21,'django_celery_beat','0019_alter_periodictasks_options','2024-09-14 13:52:53.663081'),(22,'contenttypes','0001_initial','2024-09-14 13:53:57.236655'),(23,'auth','0001_initial','2024-09-14 13:53:58.732014'),(24,'admin','0001_initial','2024-09-14 13:53:59.106422'),(25,'admin','0002_logentry_remove_auto_add','2024-09-14 13:53:59.143279'),(26,'admin','0003_logentry_add_action_flag_choices','2024-09-14 13:53:59.174231'),(27,'contenttypes','0002_remove_content_type_name','2024-09-14 13:53:59.354890'),(28,'auth','0002_alter_permission_name_max_length','2024-09-14 13:53:59.498429'),(29,'auth','0003_alter_user_email_max_length','2024-09-14 13:53:59.541295'),(30,'auth','0004_alter_user_username_opts','2024-09-14 13:53:59.560392'),(31,'auth','0005_alter_user_last_login_null','2024-09-14 13:53:59.678580'),(32,'auth','0006_require_contenttypes_0002','2024-09-14 13:53:59.686329'),(33,'auth','0007_alter_validators_add_error_messages','2024-09-14 13:53:59.718777'),(34,'auth','0008_alter_user_username_max_length','2024-09-14 13:53:59.867422'),(35,'auth','0009_alter_user_last_name_max_length','2024-09-14 13:54:00.012159'),(36,'auth','0010_alter_group_name_max_length','2024-09-14 13:54:00.058426'),(37,'auth','0011_update_proxy_permissions','2024-09-14 13:54:00.086893'),(38,'auth','0012_alter_user_first_name_max_length','2024-09-14 13:54:00.267360'),(39,'ticketing','0001_initial','2024-09-14 13:54:02.847906'),(40,'proxmox','0001_initial','2024-09-14 13:54:03.288432'),(41,'guacamole','0001_initial','2024-09-14 13:54:03.856500'),(42,'pfsense','0001_initial','2024-09-14 13:54:04.249214'),(43,'sessions','0001_initial','2024-09-14 13:54:04.394162'),(44,'default','0001_initial','2024-09-14 13:54:04.921789'),(45,'social_auth','0001_initial','2024-09-14 13:54:04.931938'),(46,'default','0002_add_related_name','2024-09-14 13:54:04.978977'),(47,'social_auth','0002_add_related_name','2024-09-14 13:54:04.987915'),(48,'default','0003_alter_email_max_length','2024-09-14 13:54:05.018395'),(49,'social_auth','0003_alter_email_max_length','2024-09-14 13:54:05.025449'),(50,'default','0004_auto_20160423_0400','2024-09-14 13:54:05.055391'),(51,'social_auth','0004_auto_20160423_0400','2024-09-14 13:54:05.064578'),(52,'social_auth','0005_auto_20160727_2333','2024-09-14 13:54:05.116029'),(53,'social_django','0006_partial','2024-09-14 13:54:05.231557'),(54,'social_django','0007_code_timestamp','2024-09-14 13:54:05.322844'),(55,'social_django','0008_partial_timestamp','2024-09-14 13:54:05.411003'),(56,'social_django','0009_auto_20191118_0520','2024-09-14 13:54:05.550926'),(57,'social_django','0010_uid_db_index','2024-09-14 13:54:05.616806'),(58,'social_django','0011_alter_id_fields','2024-09-14 13:54:06.348657'),(59,'social_django','0012_usersocialauth_extra_data_new','2024-09-14 13:54:06.633950'),(60,'social_django','0013_migrate_extra_data','2024-09-14 13:54:06.808370'),(61,'social_django','0014_remove_usersocialauth_extra_data','2024-09-14 13:54:06.897121'),(62,'social_django','0015_rename_extra_data_new_usersocialauth_extra_data','2024-09-14 13:54:06.998995'),(63,'social_django','0016_alter_usersocialauth_extra_data','2024-09-14 13:54:07.023001'),(64,'social_django','0001_initial','2024-09-14 13:54:07.037756'),(65,'social_django','0004_auto_20160423_0400','2024-09-14 13:54:07.045671'),(66,'social_django','0005_auto_20160727_2333','2024-09-14 13:54:07.053829'),(67,'social_django','0002_add_related_name','2024-09-14 13:54:07.061132'),(68,'social_django','0003_alter_email_max_length','2024-09-14 13:54:07.069219');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `guacamole_guacamoleconnection`
--

DROP TABLE IF EXISTS `guacamole_guacamoleconnection`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `guacamole_guacamoleconnection` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `connection_id` int NOT NULL,
  `connection_group_id` int NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `user_id` bigint NOT NULL,
  `vm_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `vm_id` (`vm_id`),
  KEY `guacamole_guacamolec_user_id_b118cf32_fk_guacamole` (`user_id`),
  CONSTRAINT `guacamole_guacamolec_user_id_b118cf32_fk_guacamole` FOREIGN KEY (`user_id`) REFERENCES `guacamole_guacamoleuser` (`id`),
  CONSTRAINT `guacamole_guacamolec_vm_id_5f48e279_fk_proxmox_v` FOREIGN KEY (`vm_id`) REFERENCES `proxmox_virtualmachines` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `guacamole_guacamoleconnection`
--

LOCK TABLES `guacamole_guacamoleconnection` WRITE;
/*!40000 ALTER TABLE `guacamole_guacamoleconnection` DISABLE KEYS */;
/*!40000 ALTER TABLE `guacamole_guacamoleconnection` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `guacamole_guacamoleuser`
--

DROP TABLE IF EXISTS `guacamole_guacamoleuser`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `guacamole_guacamoleuser` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `username` varchar(150) NOT NULL,
  `password` varchar(128) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `system_user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `system_user_id` (`system_user_id`),
  CONSTRAINT `guacamole_guacamoleuser_system_user_id_8263859b_fk_auth_user_id` FOREIGN KEY (`system_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `guacamole_guacamoleuser`
--

LOCK TABLES `guacamole_guacamoleuser` WRITE;
/*!40000 ALTER TABLE `guacamole_guacamoleuser` DISABLE KEYS */;
INSERT INTO `guacamole_guacamoleuser` VALUES (1,'admin','pbkdf2_sha256$720000$5gL9pa3JAHZYMUbNgW3qqL$udv7QLPHZ/Fv5ijQQMvklg06MOZvEkkbGY2LJ17dIyM=',1,1),(2,'john.doe','pbkdf2_sha256$720000$5gL9pa3JAHZYMUbNgW3qqL$udv7QLPHZ/Fv5ijQQMvklg06MOZvEkkbGY2LJ17dIyM=',1,2),(3,'josephine.cruz','pbkdf2_sha256$720000$5gL9pa3JAHZYMUbNgW3qqL$udv7QLPHZ/Fv5ijQQMvklg06MOZvEkkbGY2LJ17dIyM=',1,3);
/*!40000 ALTER TABLE `guacamole_guacamoleuser` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pfsense_destinationports`
--

DROP TABLE IF EXISTS `pfsense_destinationports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pfsense_destinationports` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `dest_port` int NOT NULL,
  `port_rule_id` bigint NOT NULL,
  `vm_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `pfsense_destinationp_port_rule_id_53282df0_fk_ticketing` (`port_rule_id`),
  KEY `pfsense_destinationp_vm_id_b4b2370a_fk_proxmox_v` (`vm_id`),
  CONSTRAINT `pfsense_destinationp_port_rule_id_53282df0_fk_ticketing` FOREIGN KEY (`port_rule_id`) REFERENCES `ticketing_portrules` (`id`),
  CONSTRAINT `pfsense_destinationp_vm_id_b4b2370a_fk_proxmox_v` FOREIGN KEY (`vm_id`) REFERENCES `proxmox_virtualmachines` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pfsense_destinationports`
--

LOCK TABLES `pfsense_destinationports` WRITE;
/*!40000 ALTER TABLE `pfsense_destinationports` DISABLE KEYS */;
/*!40000 ALTER TABLE `pfsense_destinationports` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `proxmox_nodes`
--

DROP TABLE IF EXISTS `proxmox_nodes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `proxmox_nodes` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `proxmox_nodes`
--

LOCK TABLES `proxmox_nodes` WRITE;
/*!40000 ALTER TABLE `proxmox_nodes` DISABLE KEYS */;
INSERT INTO `proxmox_nodes` VALUES (1,'pve'),(2,'jin');
/*!40000 ALTER TABLE `proxmox_nodes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `proxmox_virtualmachines`
--

DROP TABLE IF EXISTS `proxmox_virtualmachines`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `proxmox_virtualmachines` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `vm_id` int NOT NULL,
  `vm_name` varchar(90) NOT NULL,
  `cores` int NOT NULL,
  `ram` int NOT NULL,
  `storage` decimal(5,2) NOT NULL,
  `ip_add` varchar(15) DEFAULT NULL,
  `is_lxc` tinyint(1) NOT NULL,
  `system_password` varchar(45) DEFAULT NULL,
  `status` varchar(20) NOT NULL,
  `node_id` bigint NOT NULL,
  `request_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `proxmox_virtualmachines_node_id_f4438889_fk_proxmox_nodes_id` (`node_id`),
  KEY `proxmox_virtualmachi_request_id_b2e8251c_fk_ticketing` (`request_id`),
  CONSTRAINT `proxmox_virtualmachi_request_id_b2e8251c_fk_ticketing` FOREIGN KEY (`request_id`) REFERENCES `ticketing_requestentry` (`id`),
  CONSTRAINT `proxmox_virtualmachines_node_id_f4438889_fk_proxmox_nodes_id` FOREIGN KEY (`node_id`) REFERENCES `proxmox_nodes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `proxmox_virtualmachines`
--

LOCK TABLES `proxmox_virtualmachines` WRITE;
/*!40000 ALTER TABLE `proxmox_virtualmachines` DISABLE KEYS */;
/*!40000 ALTER TABLE `proxmox_virtualmachines` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `social_auth_association`
--

DROP TABLE IF EXISTS `social_auth_association`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `social_auth_association` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `server_url` varchar(255) NOT NULL,
  `handle` varchar(255) NOT NULL,
  `secret` varchar(255) NOT NULL,
  `issued` int NOT NULL,
  `lifetime` int NOT NULL,
  `assoc_type` varchar(64) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `social_auth_association_server_url_handle_078befa2_uniq` (`server_url`,`handle`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `social_auth_association`
--

LOCK TABLES `social_auth_association` WRITE;
/*!40000 ALTER TABLE `social_auth_association` DISABLE KEYS */;
/*!40000 ALTER TABLE `social_auth_association` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `social_auth_code`
--

DROP TABLE IF EXISTS `social_auth_code`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `social_auth_code` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `email` varchar(254) NOT NULL,
  `code` varchar(32) NOT NULL,
  `verified` tinyint(1) NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `social_auth_code_email_code_801b2d02_uniq` (`email`,`code`),
  KEY `social_auth_code_code_a2393167` (`code`),
  KEY `social_auth_code_timestamp_176b341f` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `social_auth_code`
--

LOCK TABLES `social_auth_code` WRITE;
/*!40000 ALTER TABLE `social_auth_code` DISABLE KEYS */;
/*!40000 ALTER TABLE `social_auth_code` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `social_auth_nonce`
--

DROP TABLE IF EXISTS `social_auth_nonce`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `social_auth_nonce` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `server_url` varchar(255) NOT NULL,
  `timestamp` int NOT NULL,
  `salt` varchar(65) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `social_auth_nonce_server_url_timestamp_salt_f6284463_uniq` (`server_url`,`timestamp`,`salt`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `social_auth_nonce`
--

LOCK TABLES `social_auth_nonce` WRITE;
/*!40000 ALTER TABLE `social_auth_nonce` DISABLE KEYS */;
/*!40000 ALTER TABLE `social_auth_nonce` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `social_auth_partial`
--

DROP TABLE IF EXISTS `social_auth_partial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `social_auth_partial` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `token` varchar(32) NOT NULL,
  `next_step` smallint unsigned NOT NULL,
  `backend` varchar(32) NOT NULL,
  `timestamp` datetime(6) NOT NULL,
  `data` json NOT NULL DEFAULT (_utf8mb3'{}'),
  PRIMARY KEY (`id`),
  KEY `social_auth_partial_token_3017fea3` (`token`),
  KEY `social_auth_partial_timestamp_50f2119f` (`timestamp`),
  CONSTRAINT `social_auth_partial_chk_1` CHECK ((`next_step` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `social_auth_partial`
--

LOCK TABLES `social_auth_partial` WRITE;
/*!40000 ALTER TABLE `social_auth_partial` DISABLE KEYS */;
/*!40000 ALTER TABLE `social_auth_partial` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `social_auth_usersocialauth`
--

DROP TABLE IF EXISTS `social_auth_usersocialauth`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `social_auth_usersocialauth` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `provider` varchar(32) NOT NULL,
  `uid` varchar(255) NOT NULL,
  `user_id` int NOT NULL,
  `created` datetime(6) NOT NULL,
  `modified` datetime(6) NOT NULL,
  `extra_data` json NOT NULL DEFAULT (_utf8mb3'{}'),
  PRIMARY KEY (`id`),
  UNIQUE KEY `social_auth_usersocialauth_provider_uid_e6b5e668_uniq` (`provider`,`uid`),
  KEY `social_auth_usersocialauth_user_id_17d28448_fk_auth_user_id` (`user_id`),
  KEY `social_auth_usersocialauth_uid_796e51dc` (`uid`),
  CONSTRAINT `social_auth_usersocialauth_user_id_17d28448_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `social_auth_usersocialauth`
--

LOCK TABLES `social_auth_usersocialauth` WRITE;
/*!40000 ALTER TABLE `social_auth_usersocialauth` DISABLE KEYS */;
/*!40000 ALTER TABLE `social_auth_usersocialauth` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ticketing_comment`
--

DROP TABLE IF EXISTS `ticketing_comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ticketing_comment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `comment` longtext NOT NULL,
  `date_time` datetime(6) NOT NULL,
  `request_entry_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ticketing_comment_id_request_entry_id_d2fb2bd8_uniq` (`id`,`request_entry_id`),
  KEY `ticketing_comment_request_entry_id_22e7afab_fk_ticketing` (`request_entry_id`),
  KEY `ticketing_comment_user_id_67ffe313_fk_auth_user_id` (`user_id`),
  CONSTRAINT `ticketing_comment_request_entry_id_22e7afab_fk_ticketing` FOREIGN KEY (`request_entry_id`) REFERENCES `ticketing_requestentry` (`id`),
  CONSTRAINT `ticketing_comment_user_id_67ffe313_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ticketing_comment`
--

LOCK TABLES `ticketing_comment` WRITE;
/*!40000 ALTER TABLE `ticketing_comment` DISABLE KEYS */;
/*!40000 ALTER TABLE `ticketing_comment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ticketing_issuecomment`
--

DROP TABLE IF EXISTS `ticketing_issuecomment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ticketing_issuecomment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `comment` longtext NOT NULL,
  `date_time` datetime(6) NOT NULL,
  `ticket_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ticketing_issuecomme_ticket_id_582d3c44_fk_ticketing` (`ticket_id`),
  KEY `ticketing_issuecomment_user_id_05834b5d_fk_auth_user_id` (`user_id`),
  CONSTRAINT `ticketing_issuecomme_ticket_id_582d3c44_fk_ticketing` FOREIGN KEY (`ticket_id`) REFERENCES `ticketing_issueticket` (`id`),
  CONSTRAINT `ticketing_issuecomment_user_id_05834b5d_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ticketing_issuecomment`
--

LOCK TABLES `ticketing_issuecomment` WRITE;
/*!40000 ALTER TABLE `ticketing_issuecomment` DISABLE KEYS */;
/*!40000 ALTER TABLE `ticketing_issuecomment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ticketing_issuecommentfile`
--

DROP TABLE IF EXISTS `ticketing_issuecommentfile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ticketing_issuecommentfile` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `file` varchar(100) NOT NULL,
  `uploaded_date` datetime(6) NOT NULL,
  `comment_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ticketing_issuecomme_comment_id_19319833_fk_ticketing` (`comment_id`),
  CONSTRAINT `ticketing_issuecomme_comment_id_19319833_fk_ticketing` FOREIGN KEY (`comment_id`) REFERENCES `ticketing_issuecomment` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ticketing_issuecommentfile`
--

LOCK TABLES `ticketing_issuecommentfile` WRITE;
/*!40000 ALTER TABLE `ticketing_issuecommentfile` DISABLE KEYS */;
/*!40000 ALTER TABLE `ticketing_issuecommentfile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ticketing_issuefile`
--

DROP TABLE IF EXISTS `ticketing_issuefile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ticketing_issuefile` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `file` varchar(100) NOT NULL,
  `uploaded_date` datetime(6) NOT NULL,
  `ticket_id` bigint NOT NULL,
  `uploaded_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ticketing_issuefile_ticket_id_5293a3b6_fk_ticketing` (`ticket_id`),
  KEY `ticketing_issuefile_uploaded_by_id_39f13ffc_fk_auth_user_id` (`uploaded_by_id`),
  CONSTRAINT `ticketing_issuefile_ticket_id_5293a3b6_fk_ticketing` FOREIGN KEY (`ticket_id`) REFERENCES `ticketing_issueticket` (`id`),
  CONSTRAINT `ticketing_issuefile_uploaded_by_id_39f13ffc_fk_auth_user_id` FOREIGN KEY (`uploaded_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ticketing_issuefile`
--

LOCK TABLES `ticketing_issuefile` WRITE;
/*!40000 ALTER TABLE `ticketing_issuefile` DISABLE KEYS */;
/*!40000 ALTER TABLE `ticketing_issuefile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ticketing_issueticket`
--

DROP TABLE IF EXISTS `ticketing_issueticket`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ticketing_issueticket` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `subject` varchar(100) NOT NULL,
  `category` varchar(100) NOT NULL,
  `description` varchar(10000) NOT NULL,
  `date_created` datetime(6) NOT NULL,
  `resolve_date` datetime(6) DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `request_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ticketing_issueticket_created_by_id_8b65b615_fk_auth_user_id` (`created_by_id`),
  KEY `ticketing_issueticke_request_id_2f6b56ee_fk_ticketing` (`request_id`),
  CONSTRAINT `ticketing_issueticke_request_id_2f6b56ee_fk_ticketing` FOREIGN KEY (`request_id`) REFERENCES `ticketing_requestentry` (`id`),
  CONSTRAINT `ticketing_issueticket_created_by_id_8b65b615_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ticketing_issueticket`
--

LOCK TABLES `ticketing_issueticket` WRITE;
/*!40000 ALTER TABLE `ticketing_issueticket` DISABLE KEYS */;
/*!40000 ALTER TABLE `ticketing_issueticket` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ticketing_portrules`
--

DROP TABLE IF EXISTS `ticketing_portrules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ticketing_portrules` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `protocol` varchar(45) NOT NULL,
  `dest_ports` varchar(45) NOT NULL,
  `request_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ticketing_portrules_request_id_69883978_fk_ticketing` (`request_id`),
  CONSTRAINT `ticketing_portrules_request_id_69883978_fk_ticketing` FOREIGN KEY (`request_id`) REFERENCES `ticketing_requestentry` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ticketing_portrules`
--

LOCK TABLES `ticketing_portrules` WRITE;
/*!40000 ALTER TABLE `ticketing_portrules` DISABLE KEYS */;
/*!40000 ALTER TABLE `ticketing_portrules` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ticketing_requestentry`
--

DROP TABLE IF EXISTS `ticketing_requestentry`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ticketing_requestentry` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `ram` int NOT NULL,
  `has_internet` tinyint(1) NOT NULL,
  `other_config` longtext,
  `status` varchar(20) NOT NULL,
  `cores` int NOT NULL,
  `isExpired` tinyint(1) NOT NULL,
  `requestDate` datetime(6) NOT NULL,
  `date_needed` date NOT NULL,
  `expiration_date` date DEFAULT NULL,
  `is_vm_tested` tinyint(1) NOT NULL,
  `assigned_to_id` int DEFAULT NULL,
  `fulfilled_by_id` int DEFAULT NULL,
  `requester_id` int NOT NULL,
  `template_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ticketing_requestent_template_id_a12a934a_fk_ticketing` (`template_id`),
  KEY `ticketing_requestentry_assigned_to_id_506defcc_fk_auth_user_id` (`assigned_to_id`),
  KEY `ticketing_requestentry_fulfilled_by_id_d919446a_fk_auth_user_id` (`fulfilled_by_id`),
  KEY `ticketing_requestentry_requester_id_59344ce4_fk_auth_user_id` (`requester_id`),
  CONSTRAINT `ticketing_requestent_template_id_a12a934a_fk_ticketing` FOREIGN KEY (`template_id`) REFERENCES `ticketing_vmtemplates` (`id`),
  CONSTRAINT `ticketing_requestentry_assigned_to_id_506defcc_fk_auth_user_id` FOREIGN KEY (`assigned_to_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `ticketing_requestentry_fulfilled_by_id_d919446a_fk_auth_user_id` FOREIGN KEY (`fulfilled_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `ticketing_requestentry_requester_id_59344ce4_fk_auth_user_id` FOREIGN KEY (`requester_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ticketing_requestentry`
--

LOCK TABLES `ticketing_requestentry` WRITE;
/*!40000 ALTER TABLE `ticketing_requestentry` DISABLE KEYS */;
/*!40000 ALTER TABLE `ticketing_requestentry` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ticketing_requestentryaudit`
--

DROP TABLE IF EXISTS `ticketing_requestentryaudit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ticketing_requestentryaudit` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `change_date` datetime(6) NOT NULL,
  `changes` longtext NOT NULL,
  `changed_by_id` int DEFAULT NULL,
  `request_entry_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ticketing_requestent_changed_by_id_922d79a4_fk_auth_user` (`changed_by_id`),
  KEY `ticketing_requestent_request_entry_id_a321fee1_fk_ticketing` (`request_entry_id`),
  CONSTRAINT `ticketing_requestent_changed_by_id_922d79a4_fk_auth_user` FOREIGN KEY (`changed_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `ticketing_requestent_request_entry_id_a321fee1_fk_ticketing` FOREIGN KEY (`request_entry_id`) REFERENCES `ticketing_requestentry` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ticketing_requestentryaudit`
--

LOCK TABLES `ticketing_requestentryaudit` WRITE;
/*!40000 ALTER TABLE `ticketing_requestentryaudit` DISABLE KEYS */;
/*!40000 ALTER TABLE `ticketing_requestentryaudit` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ticketing_requestusecase`
--

DROP TABLE IF EXISTS `ticketing_requestusecase`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ticketing_requestusecase` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `request_use_case` varchar(45) DEFAULT NULL,
  `vm_count` int DEFAULT NULL,
  `request_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ticketing_requestuse_request_id_f2fe6137_fk_ticketing` (`request_id`),
  CONSTRAINT `ticketing_requestuse_request_id_f2fe6137_fk_ticketing` FOREIGN KEY (`request_id`) REFERENCES `ticketing_requestentry` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ticketing_requestusecase`
--

LOCK TABLES `ticketing_requestusecase` WRITE;
/*!40000 ALTER TABLE `ticketing_requestusecase` DISABLE KEYS */;
/*!40000 ALTER TABLE `ticketing_requestusecase` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ticketing_userprofile`
--

DROP TABLE IF EXISTS `ticketing_userprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ticketing_userprofile` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_type` varchar(20) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `ticketing_userprofile_user_id_e3bea9bb_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ticketing_userprofile`
--

LOCK TABLES `ticketing_userprofile` WRITE;
/*!40000 ALTER TABLE `ticketing_userprofile` DISABLE KEYS */;
INSERT INTO `ticketing_userprofile` VALUES (1,'admin',1),(2,'admin',2),(3,'faculty',3);
/*!40000 ALTER TABLE `ticketing_userprofile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ticketing_vmtemplates`
--

DROP TABLE IF EXISTS `ticketing_vmtemplates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ticketing_vmtemplates` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `vm_id` varchar(45) NOT NULL,
  `vm_name` varchar(90) NOT NULL,
  `cores` int NOT NULL,
  `ram` int NOT NULL,
  `storage` int NOT NULL,
  `node` varchar(45) NOT NULL,
  `is_lxc` tinyint(1) NOT NULL,
  `guacamole_protocol` varchar(10) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ticketing_vmtemplates`
--

LOCK TABLES `ticketing_vmtemplates` WRITE;
/*!40000 ALTER TABLE `ticketing_vmtemplates` DISABLE KEYS */;
INSERT INTO `ticketing_vmtemplates` VALUES (1,'3000','Ubuntu-Desktop-24 (GUI)',1,1024,15,'pve',0,'rdp'),(2,'3001','Ubuntu-Desktop-22 (GUI)',1,1024,15,'pve',0,'rdp'),(3,'3002','Ubuntu-Server-24 (TUI)',1,1024,15,'pve',0,'ssh'),(4,'3003','Ubuntu-Server-22 (TUI)',1,1024,15,'pve',0,'ssh'),(5,'5000','Ubuntu-LXC-23',1,1024,10,'pve',1,'ssh');
/*!40000 ALTER TABLE `ticketing_vmtemplates` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'cap2240db'
--

--
-- Dumping routines for database 'cap2240db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-09-26  9:43:01
