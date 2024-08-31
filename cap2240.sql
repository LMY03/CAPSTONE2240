CREATE DATABASE  IF NOT EXISTS `cap2240db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `cap2240db`;
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
) ENGINE=InnoDB AUTO_INCREMENT=117 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add request entry',1,'add_requestentry'),(2,'Can change request entry',1,'change_requestentry'),(3,'Can delete request entry',1,'delete_requestentry'),(4,'Can view request entry',1,'view_requestentry'),(5,'Can add vm templates',2,'add_vmtemplates'),(6,'Can change vm templates',2,'change_vmtemplates'),(7,'Can delete vm templates',2,'delete_vmtemplates'),(8,'Can view vm templates',2,'view_vmtemplates'),(9,'Can add user profile',3,'add_userprofile'),(10,'Can change user profile',3,'change_userprofile'),(11,'Can delete user profile',3,'delete_userprofile'),(12,'Can view user profile',3,'view_userprofile'),(13,'Can add request use case',4,'add_requestusecase'),(14,'Can change request use case',4,'change_requestusecase'),(15,'Can delete request use case',4,'delete_requestusecase'),(16,'Can view request use case',4,'view_requestusecase'),(17,'Can add request entry audit',5,'add_requestentryaudit'),(18,'Can change request entry audit',5,'change_requestentryaudit'),(19,'Can delete request entry audit',5,'delete_requestentryaudit'),(20,'Can view request entry audit',5,'view_requestentryaudit'),(21,'Can add port rules',6,'add_portrules'),(22,'Can change port rules',6,'change_portrules'),(23,'Can delete port rules',6,'delete_portrules'),(24,'Can view port rules',6,'view_portrules'),(25,'Can add comment',7,'add_comment'),(26,'Can change comment',7,'change_comment'),(27,'Can delete comment',7,'delete_comment'),(28,'Can view comment',7,'view_comment'),(29,'Can add guacamole user',8,'add_guacamoleuser'),(30,'Can change guacamole user',8,'change_guacamoleuser'),(31,'Can delete guacamole user',8,'delete_guacamoleuser'),(32,'Can view guacamole user',8,'view_guacamoleuser'),(33,'Can add guacamole connection',9,'add_guacamoleconnection'),(34,'Can change guacamole connection',9,'change_guacamoleconnection'),(35,'Can delete guacamole connection',9,'delete_guacamoleconnection'),(36,'Can view guacamole connection',9,'view_guacamoleconnection'),(37,'Can add destination ports',10,'add_destinationports'),(38,'Can change destination ports',10,'change_destinationports'),(39,'Can delete destination ports',10,'delete_destinationports'),(40,'Can view destination ports',10,'view_destinationports'),(41,'Can add nodes',11,'add_nodes'),(42,'Can change nodes',11,'change_nodes'),(43,'Can delete nodes',11,'delete_nodes'),(44,'Can view nodes',11,'view_nodes'),(45,'Can add virtual machines',12,'add_virtualmachines'),(46,'Can change virtual machines',12,'change_virtualmachines'),(47,'Can delete virtual machines',12,'delete_virtualmachines'),(48,'Can view virtual machines',12,'view_virtualmachines'),(49,'Can add log entry',13,'add_logentry'),(50,'Can change log entry',13,'change_logentry'),(51,'Can delete log entry',13,'delete_logentry'),(52,'Can view log entry',13,'view_logentry'),(53,'Can add permission',14,'add_permission'),(54,'Can change permission',14,'change_permission'),(55,'Can delete permission',14,'delete_permission'),(56,'Can view permission',14,'view_permission'),(57,'Can add group',15,'add_group'),(58,'Can change group',15,'change_group'),(59,'Can delete group',15,'delete_group'),(60,'Can view group',15,'view_group'),(61,'Can add user',16,'add_user'),(62,'Can change user',16,'change_user'),(63,'Can delete user',16,'delete_user'),(64,'Can view user',16,'view_user'),(65,'Can add content type',17,'add_contenttype'),(66,'Can change content type',17,'change_contenttype'),(67,'Can delete content type',17,'delete_contenttype'),(68,'Can view content type',17,'view_contenttype'),(69,'Can add session',18,'add_session'),(70,'Can change session',18,'change_session'),(71,'Can delete session',18,'delete_session'),(72,'Can view session',18,'view_session'),(73,'Can add association',19,'add_association'),(74,'Can change association',19,'change_association'),(75,'Can delete association',19,'delete_association'),(76,'Can view association',19,'view_association'),(77,'Can add code',20,'add_code'),(78,'Can change code',20,'change_code'),(79,'Can delete code',20,'delete_code'),(80,'Can view code',20,'view_code'),(81,'Can add nonce',21,'add_nonce'),(82,'Can change nonce',21,'change_nonce'),(83,'Can delete nonce',21,'delete_nonce'),(84,'Can view nonce',21,'view_nonce'),(85,'Can add user social auth',22,'add_usersocialauth'),(86,'Can change user social auth',22,'change_usersocialauth'),(87,'Can delete user social auth',22,'delete_usersocialauth'),(88,'Can view user social auth',22,'view_usersocialauth'),(89,'Can add partial',23,'add_partial'),(90,'Can change partial',23,'change_partial'),(91,'Can delete partial',23,'delete_partial'),(92,'Can view partial',23,'view_partial'),(93,'Can add crontab',24,'add_crontabschedule'),(94,'Can change crontab',24,'change_crontabschedule'),(95,'Can delete crontab',24,'delete_crontabschedule'),(96,'Can view crontab',24,'view_crontabschedule'),(97,'Can add interval',25,'add_intervalschedule'),(98,'Can change interval',25,'change_intervalschedule'),(99,'Can delete interval',25,'delete_intervalschedule'),(100,'Can view interval',25,'view_intervalschedule'),(101,'Can add periodic task',26,'add_periodictask'),(102,'Can change periodic task',26,'change_periodictask'),(103,'Can delete periodic task',26,'delete_periodictask'),(104,'Can view periodic task',26,'view_periodictask'),(105,'Can add periodic task track',27,'add_periodictasks'),(106,'Can change periodic task track',27,'change_periodictasks'),(107,'Can delete periodic task track',27,'delete_periodictasks'),(108,'Can view periodic task track',27,'view_periodictasks'),(109,'Can add solar event',28,'add_solarschedule'),(110,'Can change solar event',28,'change_solarschedule'),(111,'Can delete solar event',28,'delete_solarschedule'),(112,'Can view solar event',28,'view_solarschedule'),(113,'Can add clocked',29,'add_clockedschedule'),(114,'Can change clocked',29,'change_clockedschedule'),(115,'Can delete clocked',29,'delete_clockedschedule'),(116,'Can view clocked',29,'view_clockedschedule');
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
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$720000$5gL9pa3JAHZYMUbNgW3qqL$udv7QLPHZ/Fv5ijQQMvklg06MOZvEkkbGY2LJ17dIyM=',NULL,1,'admin','admin','chan','',1,1,'2024-08-31 13:22:27.000000'),(2,'pbkdf2_sha256$720000$5gL9pa3JAHZYMUbNgW3qqL$udv7QLPHZ/Fv5ijQQMvklg06MOZvEkkbGY2LJ17dIyM=',NULL,1,'john.doe','John','Doe','',1,1,'2024-08-31 13:22:27.000000'),(3,'pbkdf2_sha256$720000$5gL9pa3JAHZYMUbNgW3qqL$udv7QLPHZ/Fv5ijQQMvklg06MOZvEkkbGY2LJ17dIyM=',NULL,0,'josephine.cruz','Josephine','Cruz','',0,1,'2024-08-31 13:22:27.000000');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_celery_beat_crontabschedule`
--

LOCK TABLES `django_celery_beat_crontabschedule` WRITE;
/*!40000 ALTER TABLE `django_celery_beat_crontabschedule` DISABLE KEYS */;
INSERT INTO `django_celery_beat_crontabschedule` VALUES (1,'0','4','*','*','*','Asia/Manila');
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_celery_beat_periodictask`
--

LOCK TABLES `django_celery_beat_periodictask` WRITE;
/*!40000 ALTER TABLE `django_celery_beat_periodictask` DISABLE KEYS */;
INSERT INTO `django_celery_beat_periodictask` VALUES (1,'celery.backend_cleanup','celery.backend_cleanup','[]','{}',NULL,NULL,NULL,NULL,1,NULL,0,'2024-08-31 13:20:28.020499','',1,NULL,NULL,0,NULL,NULL,'{}',NULL,43200);
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
INSERT INTO `django_celery_beat_periodictasks` VALUES (1,'2024-08-31 13:20:28.021275');
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
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (13,'admin','logentry'),(15,'auth','group'),(14,'auth','permission'),(16,'auth','user'),(17,'contenttypes','contenttype'),(29,'django_celery_beat','clockedschedule'),(24,'django_celery_beat','crontabschedule'),(25,'django_celery_beat','intervalschedule'),(26,'django_celery_beat','periodictask'),(27,'django_celery_beat','periodictasks'),(28,'django_celery_beat','solarschedule'),(9,'guacamole','guacamoleconnection'),(8,'guacamole','guacamoleuser'),(10,'pfsense','destinationports'),(11,'proxmox','nodes'),(12,'proxmox','virtualmachines'),(18,'sessions','session'),(19,'social_django','association'),(20,'social_django','code'),(21,'social_django','nonce'),(23,'social_django','partial'),(22,'social_django','usersocialauth'),(7,'ticketing','comment'),(6,'ticketing','portrules'),(1,'ticketing','requestentry'),(5,'ticketing','requestentryaudit'),(4,'ticketing','requestusecase'),(3,'ticketing','userprofile'),(2,'ticketing','vmtemplates');
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
INSERT INTO `django_migrations` VALUES (1,'django_celery_beat','0001_initial','2024-08-31 13:20:25.612935'),(2,'django_celery_beat','0002_auto_20161118_0346','2024-08-31 13:20:25.888764'),(3,'django_celery_beat','0003_auto_20161209_0049','2024-08-31 13:20:25.970342'),(4,'django_celery_beat','0004_auto_20170221_0000','2024-08-31 13:20:25.988509'),(5,'django_celery_beat','0005_add_solarschedule_events_choices','2024-08-31 13:20:26.003677'),(6,'django_celery_beat','0006_auto_20180322_0932','2024-08-31 13:20:26.250329'),(7,'django_celery_beat','0007_auto_20180521_0826','2024-08-31 13:20:26.379576'),(8,'django_celery_beat','0008_auto_20180914_1922','2024-08-31 13:20:26.417192'),(9,'django_celery_beat','0006_auto_20180210_1226','2024-08-31 13:20:26.445689'),(10,'django_celery_beat','0006_periodictask_priority','2024-08-31 13:20:26.625031'),(11,'django_celery_beat','0009_periodictask_headers','2024-08-31 13:20:26.805868'),(12,'django_celery_beat','0010_auto_20190429_0326','2024-08-31 13:20:26.992131'),(13,'django_celery_beat','0011_auto_20190508_0153','2024-08-31 13:20:27.253460'),(14,'django_celery_beat','0012_periodictask_expire_seconds','2024-08-31 13:20:27.450873'),(15,'django_celery_beat','0013_auto_20200609_0727','2024-08-31 13:20:27.468446'),(16,'django_celery_beat','0014_remove_clockedschedule_enabled','2024-08-31 13:20:27.510773'),(17,'django_celery_beat','0015_edit_solarschedule_events_choices','2024-08-31 13:20:27.525626'),(18,'django_celery_beat','0016_alter_crontabschedule_timezone','2024-08-31 13:20:27.544741'),(19,'django_celery_beat','0017_alter_crontabschedule_month_of_year','2024-08-31 13:20:27.565932'),(20,'django_celery_beat','0018_improve_crontab_helptext','2024-08-31 13:20:27.584128'),(21,'django_celery_beat','0019_alter_periodictasks_options','2024-08-31 13:20:27.597264'),(22,'contenttypes','0001_initial','2024-08-31 13:22:10.375391'),(23,'auth','0001_initial','2024-08-31 13:22:11.863231'),(24,'admin','0001_initial','2024-08-31 13:22:12.175035'),(25,'admin','0002_logentry_remove_auto_add','2024-08-31 13:22:12.196895'),(26,'admin','0003_logentry_add_action_flag_choices','2024-08-31 13:22:12.223623'),(27,'contenttypes','0002_remove_content_type_name','2024-08-31 13:22:12.376538'),(28,'auth','0002_alter_permission_name_max_length','2024-08-31 13:22:12.516140'),(29,'auth','0003_alter_user_email_max_length','2024-08-31 13:22:12.556208'),(30,'auth','0004_alter_user_username_opts','2024-08-31 13:22:12.573377'),(31,'auth','0005_alter_user_last_login_null','2024-08-31 13:22:12.681332'),(32,'auth','0006_require_contenttypes_0002','2024-08-31 13:22:12.690143'),(33,'auth','0007_alter_validators_add_error_messages','2024-08-31 13:22:12.708043'),(34,'auth','0008_alter_user_username_max_length','2024-08-31 13:22:12.850174'),(35,'auth','0009_alter_user_last_name_max_length','2024-08-31 13:22:13.003174'),(36,'auth','0010_alter_group_name_max_length','2024-08-31 13:22:13.036968'),(37,'auth','0011_update_proxy_permissions','2024-08-31 13:22:13.061693'),(38,'auth','0012_alter_user_first_name_max_length','2024-08-31 13:22:13.196840'),(39,'ticketing','0001_initial','2024-08-31 13:22:15.145312'),(40,'proxmox','0001_initial','2024-08-31 13:22:15.541385'),(41,'guacamole','0001_initial','2024-08-31 13:22:16.106692'),(42,'pfsense','0001_initial','2024-08-31 13:22:16.418574'),(43,'sessions','0001_initial','2024-08-31 13:22:16.505399'),(44,'default','0001_initial','2024-08-31 13:22:17.048000'),(45,'social_auth','0001_initial','2024-08-31 13:22:17.056716'),(46,'default','0002_add_related_name','2024-08-31 13:22:17.083713'),(47,'social_auth','0002_add_related_name','2024-08-31 13:22:17.091458'),(48,'default','0003_alter_email_max_length','2024-08-31 13:22:17.116536'),(49,'social_auth','0003_alter_email_max_length','2024-08-31 13:22:17.124437'),(50,'default','0004_auto_20160423_0400','2024-08-31 13:22:17.149424'),(51,'social_auth','0004_auto_20160423_0400','2024-08-31 13:22:17.159546'),(52,'social_auth','0005_auto_20160727_2333','2024-08-31 13:22:17.204982'),(53,'social_django','0006_partial','2024-08-31 13:22:17.293358'),(54,'social_django','0007_code_timestamp','2024-08-31 13:22:17.387839'),(55,'social_django','0008_partial_timestamp','2024-08-31 13:22:17.482678'),(56,'social_django','0009_auto_20191118_0520','2024-08-31 13:22:17.608957'),(57,'social_django','0010_uid_db_index','2024-08-31 13:22:17.668509'),(58,'social_django','0011_alter_id_fields','2024-08-31 13:22:18.388061'),(59,'social_django','0012_usersocialauth_extra_data_new','2024-08-31 13:22:18.693581'),(60,'social_django','0013_migrate_extra_data','2024-08-31 13:22:18.733379'),(61,'social_django','0014_remove_usersocialauth_extra_data','2024-08-31 13:22:18.815911'),(62,'social_django','0015_rename_extra_data_new_usersocialauth_extra_data','2024-08-31 13:22:18.912259'),(63,'social_django','0016_alter_usersocialauth_extra_data','2024-08-31 13:22:18.932625'),(64,'social_django','0003_alter_email_max_length','2024-08-31 13:22:18.947035'),(65,'social_django','0005_auto_20160727_2333','2024-08-31 13:22:18.955641'),(66,'social_django','0002_add_related_name','2024-08-31 13:22:18.963616'),(67,'social_django','0001_initial','2024-08-31 13:22:18.970188'),(68,'social_django','0004_auto_20160423_0400','2024-08-31 13:22:18.977353');
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
  `status` varchar(20) NOT NULL,
  `node_id` bigint NOT NULL,
  `request_id` bigint NOT NULL,
  `system_password` varchar(45) DEFAULT NULL,
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
  `expiration_date` date NOT NULL,
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
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ticketing_vmtemplates`
--

LOCK TABLES `ticketing_vmtemplates` WRITE;
/*!40000 ALTER TABLE `ticketing_vmtemplates` DISABLE KEYS */;
INSERT INTO `ticketing_vmtemplates` VALUES (1,'3000','Ubuntu-Desktop-24 (GUI)',1,1024,15,'pve',0,'rdp'),(2,'3001','Ubuntu-Desktop-22 (GUI)',1,1024,15,'pve',0,'rdp'),(3,'3002','Ubuntu-Server-24 (TUI)',1,1024,15,'pve',0,'ssh'),(4,'3003','Ubuntu-Server-22 (TUI)',1,1024,15,'pve',0,'ssh'),(5,'5000','Ubuntu-LXC-23',1,1024,10,'pve',1,'ssh');
/*!40000 ALTER TABLE `ticketing_vmtemplates` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-08-31 21:23:16
