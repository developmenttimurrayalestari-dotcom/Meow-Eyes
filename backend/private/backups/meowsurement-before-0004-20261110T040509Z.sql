-- MariaDB dump 10.17  Distrib 10.4.8-MariaDB, for Win64 (AMD64)
--
-- Host: 192.168.44.16    Database: db_meoweyes
-- ------------------------------------------------------
-- Server version	5.7.24-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `addresses`
--

DROP TABLE IF EXISTS `addresses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `addresses` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `label` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `recipient` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `street` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `subdistrict` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `district` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `city` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `province` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `postal_code` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `country_code` varchar(2) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ID',
  `everpro_destination_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_default` tinyint(1) NOT NULL DEFAULT '0',
  `default_for_user` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin GENERATED ALWAYS AS ((case when (`is_default` = 1) then `user_id` else NULL end)) STORED,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_addresses_id_user_id` (`id`,`user_id`),
  UNIQUE KEY `uq_addresses_default_for_user` (`default_for_user`),
  KEY `ix_addresses_user_id` (`user_id`),
  CONSTRAINT `fk_addresses_user_id_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `addresses`
--

LOCK TABLES `addresses` WRITE;
/*!40000 ALTER TABLE `addresses` DISABLE KEYS */;
/*!40000 ALTER TABLE `addresses` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('20261109_0003');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `article_categories`
--

DROP TABLE IF EXISTS `article_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `article_categories` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `slug` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `sort_order` int(11) NOT NULL DEFAULT '0',
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_article_categories_slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `article_categories`
--

LOCK TABLES `article_categories` WRITE;
/*!40000 ALTER TABLE `article_categories` DISABLE KEYS */;
INSERT INTO `article_categories` VALUES ('acat_009c491770594be0','Tips Kacamata','tips-kacamata',NULL,1,0,'2026-10-23 08:02:34.122919'),('acat_602dcfc180cb4af3','Fashion Eyewear','fashion-eyewear',NULL,1,1,'2026-10-23 08:02:34.151182'),('acat_a3920640b41e4715','Panduan Belanja','panduan-belanja',NULL,1,4,'2026-10-23 08:02:34.228877'),('acat_b4b83e879b5641f4','Promo & Event','promo-event',NULL,1,3,'2026-10-23 08:02:34.208013'),('acat_fcb176f9b99a4779','Kesehatan Mata','kesehatan-mata',NULL,1,2,'2026-10-23 08:02:34.177913');
/*!40000 ALTER TABLE `article_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `article_tags`
--

DROP TABLE IF EXISTS `article_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `article_tags` (
  `article_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `tag` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sort_order` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`article_id`,`tag`),
  CONSTRAINT `fk_article_tags_article_id_articles_id` FOREIGN KEY (`article_id`) REFERENCES `articles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `article_tags`
--

LOCK TABLES `article_tags` WRITE;
/*!40000 ALTER TABLE `article_tags` DISABLE KEYS */;
/*!40000 ALTER TABLE `article_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `articles`
--

DROP TABLE IF EXISTS `articles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `articles` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `category_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `author_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `author_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Admin Meow',
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `slug` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `excerpt` text COLLATE utf8mb4_unicode_ci,
  `content` mediumtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `thumbnail` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'draft',
  `view_count` bigint(20) NOT NULL DEFAULT '0',
  `seo_title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `seo_description` text COLLATE utf8mb4_unicode_ci,
  `published_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_articles_slug` (`slug`),
  KEY `fk_articles_author_id_users_user_id` (`author_id`),
  KEY `ix_articles_category` (`category_id`,`status`,`published_at`,`id`),
  KEY `ix_articles_public` (`status`,`published_at`,`id`),
  CONSTRAINT `fk_articles_author_id_users_user_id` FOREIGN KEY (`author_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `fk_articles_category_id_article_categories_id` FOREIGN KEY (`category_id`) REFERENCES `article_categories` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `articles`
--

LOCK TABLES `articles` WRITE;
/*!40000 ALTER TABLE `articles` DISABLE KEYS */;
INSERT INTO `articles` VALUES ('art_238afa86a038481e','acat_a3920640b41e4715',NULL,'Tim Meow Eyes','Panduan Memilih Frame Sesuai Bentuk Wajah','panduan-frame-bentuk-wajah','Cocok kah frame Cat Eye untuk wajah bulat? Yuk cari tahu tips memilih bentuk frame berdasarkan bentuk wajahmu.','<p>Setiap bentuk wajah punya karakter unik, dan frame yang tepat bisa mempertajam fitur wajahmu. Berikut panduan singkat dari Meow Eyes:</p>\n<h3>1. Wajah Oval</h3>\n<p>Kabar baik! Hampir semua bentuk frame cocok. Coba <strong>Square</strong> atau <strong>Rectangle</strong> untuk kesan formal, atau <strong>Round</strong> untuk vibe vintage.</p>\n<h3>2. Wajah Bulat</h3>\n<p>Pilih frame <strong>Square</strong>, <strong>Rectangular</strong>, atau <strong>Cat Eye</strong> untuk memberi kesan lebih tirus dan tegas.</p>\n<h3>3. Wajah Persegi</h3>\n<p>Frame <strong>Round</strong> atau <strong>Oval</strong> menyeimbangkan garis rahang yang kuat. Hindari frame boxy.</p>\n<h3>4. Wajah Hati/Segitiga</h3>\n<p><strong>Aviator</strong>, <strong>Rimless</strong>, atau <strong>Cat Eye</strong> yang lembut adalah pilihan ideal.</p>\n<p>Masih bingung? Coba fitur <em>filter bentuk frame</em> di halaman Shop Now Meow Eyes.</p>','https://images.unsplash.com/photo-1633621641966-23836fcafd7b?crop=entropy&cs=srgb&fm=jpg&w=1200','published',1,NULL,NULL,'2026-10-23 08:02:34.300183','2026-11-10 01:28:21.443347','2026-10-23 08:02:34.300371'),('art_73495cf070d543e9','acat_fcb176f9b99a4779',NULL,'Tim Meow Eyes','Lensa Anti Radiasi Blue Cut: Perlu atau Tidak?','lensa-blue-cut-perlu-atau-tidak','Buat kamu yang seharian di depan layar, blue cut bukan sekadar tren — ini investasi kesehatan mata.','<p>Screen time rata-rata orang Indonesia kini melebihi 8 jam sehari. Paparan cahaya biru dari layar bisa menyebabkan mata lelah, sakit kepala, dan gangguan tidur.</p>\n<p><strong>Lensa Blue Cut</strong> di Meow Eyes memfilter cahaya biru berbahaya dan tersedia dari <em>index 1.56</em> hingga <em>1.74</em>. Untuk kamu yang bekerja dari rumah, blue cut wajib banget.</p>\n<h3>Manfaat</h3>\n<ul>\n<li>Mengurangi kelelahan mata</li>\n<li>Mencegah sakit kepala</li>\n<li>Membantu kualitas tidur lebih baik</li>\n</ul>','https://images.unsplash.com/photo-1508296695146-257a814070b4?crop=entropy&cs=srgb&fm=jpg&w=1200','published',1,NULL,NULL,'2026-10-22 08:02:34.331032','2026-11-10 01:26:20.453481','2026-10-23 08:02:34.331137'),('art_a0c9893ace164ee2','acat_602dcfc180cb4af3',NULL,'Tim Meow Eyes','Trend Frame 2026: Cat Eye, Aviator, dan Rimless','trend-frame-2026','Tiga siluet ini akan mendominasi fashion eyewear di 2026. Yuk cek koleksi Meow Eyes.','<p>Tahun 2026 akan penuh dengan pernyataan berani. Berikut tiga frame trend yang wajib kamu punya:</p>\n<h3>1. Cat Eye Bold</h3>\n<p>Cat eye kembali dengan warna-warna berani seperti coral dan honey.</p>\n<h3>2. Aviator Reimagined</h3>\n<p>Aviator klasik dengan sentuhan metal titanium yang ringan.</p>\n<h3>3. Rimless Minimalist</h3>\n<p>Untuk kamu yang suka simple tapi berkelas.</p>','https://images.unsplash.com/photo-1591076482161-42ce6da69f67?crop=entropy&cs=srgb&fm=jpg&w=1200','published',0,NULL,NULL,'2026-10-21 08:02:34.354949','2026-11-10 01:39:08.908844','2026-10-23 08:02:34.355027'),('art_e8f24839239a4b0c','acat_b4b83e879b5641f4',NULL,'Tim Meow Eyes','Kupon MEOWWELCOME 15%: Yuk Belanja Pertama Kamu','kupon-meowwelcome-15-persen','Baru gabung Meow Eyes? Dapat diskon 15% untuk pembelian pertama kamu.','<p>Pakai kupon <strong>MEOWWELCOME</strong> di checkout dan dapatkan potongan 15% (maks Rp 100.000) untuk pembelian minimal Rp 250.000.</p>\n<p>Kupon berlaku 30 hari sejak kamu registrasi. Jangan lupa cek voucher lain di halaman <a href=\"/vouchers\">Voucher</a>!</p>','https://images.unsplash.com/photo-1670739368045-7f09844fc862?crop=entropy&cs=srgb&fm=jpg&w=1200','published',1,NULL,NULL,'2026-10-20 08:02:34.377381','2026-11-10 01:39:28.637907','2026-10-23 08:02:34.377451');
/*!40000 ALTER TABLE `articles` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_articles_mysql57_guard` BEFORE INSERT ON `articles`
FOR EACH ROW
BEGIN
  IF (NEW.`status` IN ('draft','published','unpublished','archived')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_articles_status failed';
  END IF;
  IF (NEW.`view_count` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_articles_views failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_articles_mysql57_guard` BEFORE UPDATE ON `articles`
FOR EACH ROW
BEGIN
  IF (NEW.`status` IN ('draft','published','unpublished','archived')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_articles_status failed';
  END IF;
  IF (NEW.`view_count` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_articles_views failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `banners`
--

DROP TABLE IF EXISTS `banners`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `banners` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `image_desktop` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `image_mobile` text COLLATE utf8mb4_unicode_ci,
  `link_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'internal',
  `link_url` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `link_product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `link_category_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `link_article_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `link_flash_sale_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `position` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'hero',
  `target_device` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'all',
  `alt_text` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sort_order` int(11) NOT NULL DEFAULT '0',
  `start_at` datetime(6) DEFAULT NULL,
  `end_at` datetime(6) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `fk_banners_link_article_id_articles_id` (`link_article_id`),
  KEY `fk_banners_link_category_id_categories_id` (`link_category_id`),
  KEY `fk_banners_link_flash_sale_id_flash_sales_id` (`link_flash_sale_id`),
  KEY `fk_banners_link_product_id_products_id` (`link_product_id`),
  KEY `ix_banners_display` (`position`,`is_active`,`sort_order`,`id`),
  CONSTRAINT `fk_banners_link_article_id_articles_id` FOREIGN KEY (`link_article_id`) REFERENCES `articles` (`id`),
  CONSTRAINT `fk_banners_link_category_id_categories_id` FOREIGN KEY (`link_category_id`) REFERENCES `categories` (`id`),
  CONSTRAINT `fk_banners_link_flash_sale_id_flash_sales_id` FOREIGN KEY (`link_flash_sale_id`) REFERENCES `flash_sales` (`id`),
  CONSTRAINT `fk_banners_link_product_id_products_id` FOREIGN KEY (`link_product_id`) REFERENCES `products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `banners`
--

LOCK TABLES `banners` WRITE;
/*!40000 ALTER TABLE `banners` DISABLE KEYS */;
INSERT INTO `banners` VALUES ('ban_30728dfde93641cb','Koleksi Leinz Pria Terbaru','https://images.unsplash.com/photo-1525786210598-d527194d3e9a?crop=entropy&cs=srgb&fm=jpg&w=1600','https://images.unsplash.com/photo-1525786210598-d527194d3e9a?crop=entropy&cs=srgb&fm=jpg&w=1600','external','/shop-now?brand=leinz',NULL,NULL,NULL,NULL,'hero','all',NULL,2,'2026-11-10 01:31:00.000000','2026-11-10 03:31:00.000000',1,'2026-10-23 08:02:35.844404'),('ban_e1bcc7dc188a4a58','Upin Ipin Leinz Kids Sale','/api/uploads-files/2026-11/b00dd2a1231440c79cf0f853bfbf5c03.jpg','/api/uploads-files/2026-11/bcdbe02d956c4acbaefc84844a643b79.jpg','category','/category/kids-frame-anak-anak',NULL,NULL,NULL,NULL,'hero','all','Upin Ipin Leinz Kids Sale',1,'2026-11-10 01:34:00.000000','2026-11-10 04:34:00.000000',1,'2026-11-10 01:35:14.674763'),('ban_fb632f4b46964abf','Diskon Hingga 50% — Cat Eye Edition','https://images.unsplash.com/photo-1670739368045-7f09844fc862?crop=entropy&cs=srgb&fm=jpg&w=1600','https://images.unsplash.com/photo-1670739368045-7f09844fc862?crop=entropy&cs=srgb&fm=jpg&w=1600','external','/shop-now?badge=flashsale',NULL,NULL,NULL,NULL,'hero','all',NULL,1,'2026-11-10 01:31:00.000000','2026-11-10 04:31:00.000000',1,'2026-10-23 08:02:35.815148');
/*!40000 ALTER TABLE `banners` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_banners_mysql57_guard` BEFORE INSERT ON `banners`
FOR EACH ROW
BEGIN
  IF (NEW.`link_type` IN ('internal','product','category','shop_now','flash_sale','article','external','none')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_banners_link_type failed';
  END IF;
  IF (NEW.`target_device` IN ('desktop','mobile','all')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_banners_target_device failed';
  END IF;
  IF (NEW.`start_at` IS NULL OR NEW.`end_at` IS NULL OR NEW.`end_at` > NEW.`start_at`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_banners_window failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_banners_mysql57_guard` BEFORE UPDATE ON `banners`
FOR EACH ROW
BEGIN
  IF (NEW.`link_type` IN ('internal','product','category','shop_now','flash_sale','article','external','none')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_banners_link_type failed';
  END IF;
  IF (NEW.`target_device` IN ('desktop','mobile','all')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_banners_target_device failed';
  END IF;
  IF (NEW.`start_at` IS NULL OR NEW.`end_at` IS NULL OR NEW.`end_at` > NEW.`start_at`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_banners_window failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `brands`
--

DROP TABLE IF EXISTS `brands`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `brands` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `slug` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `logo` text COLLATE utf8mb4_unicode_ci,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_brands_slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `brands`
--

LOCK TABLES `brands` WRITE;
/*!40000 ALTER TABLE `brands` DISABLE KEYS */;
INSERT INTO `brands` VALUES ('brd_5d2a87b6de0a421d','MeowOptik','meowoptik',NULL,'Premium brand MeowOptik',1,'2026-10-23 07:58:18.397067'),('brd_8d5d28e0ab264d8e','EssenseEye','essenseeye',NULL,'Premium brand EssenseEye',1,'2026-10-23 07:58:18.867613'),('brd_9054aabe325441da','Kittycraft','kittycraft',NULL,'Premium brand Kittycraft',1,'2026-10-23 07:58:18.803447'),('brd_a1a43360a32847d6','PurrLens','purrlens',NULL,'Premium brand PurrLens',1,'2026-10-23 07:58:18.629166'),('brd_b1845bf573734de8','Leinz','leinz',NULL,'Premium brand Leinz',1,'2026-10-23 07:58:18.141850'),('brd_e78d6cf8db334a0b','Catlux','catlux',NULL,'Premium brand Catlux',1,'2026-10-23 07:58:18.741113');
/*!40000 ALTER TABLE `brands` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cart_items`
--

DROP TABLE IF EXISTS `cart_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cart_items` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `variant_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `quantity` int(11) NOT NULL DEFAULT '1',
  `lens_product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `lens_variant_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `lens_index_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `prescription_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `fk_cart_items_lens_index_id_lens_indexes_id` (`lens_index_id`),
  KEY `fk_cart_items_lens_product_id_lens_variant_id__c4ad8059d234` (`lens_product_id`,`lens_variant_id`),
  KEY `fk_cart_items_prescription_id_user_id_prescrip_2529d3d7b52d` (`prescription_id`,`user_id`),
  KEY `fk_cart_items_product_id_variant_id_product_va_65f2cb01a646` (`product_id`,`variant_id`),
  KEY `ix_cart_items_user_created` (`user_id`,`created_at`,`id`),
  CONSTRAINT `fk_cart_items_lens_index_id_lens_indexes_id` FOREIGN KEY (`lens_index_id`) REFERENCES `lens_indexes` (`id`),
  CONSTRAINT `fk_cart_items_lens_product_id_lens_variant_id__c4ad8059d234` FOREIGN KEY (`lens_product_id`, `lens_variant_id`) REFERENCES `product_variants` (`product_id`, `id`),
  CONSTRAINT `fk_cart_items_lens_product_id_products_id` FOREIGN KEY (`lens_product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `fk_cart_items_prescription_id_user_id_prescrip_2529d3d7b52d` FOREIGN KEY (`prescription_id`, `user_id`) REFERENCES `prescriptions` (`id`, `user_id`),
  CONSTRAINT `fk_cart_items_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `fk_cart_items_product_id_variant_id_product_va_65f2cb01a646` FOREIGN KEY (`product_id`, `variant_id`) REFERENCES `product_variants` (`product_id`, `id`),
  CONSTRAINT `fk_cart_items_user_id_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cart_items`
--

LOCK TABLES `cart_items` WRITE;
/*!40000 ALTER TABLE `cart_items` DISABLE KEYS */;
INSERT INTO `cart_items` VALUES ('cit_24f57f4257a24254','usr_c4b3d45ff0b94ffd','prd_898f994b888240ab','var_efda2ee981f14664',1,'prd_0f674d6c51e34ae1','var_17821973adfb4662','lens_ce077e4b7116476e',NULL,'2026-11-09 23:28:52.646292','2026-11-09 23:28:52.646329');
/*!40000 ALTER TABLE `cart_items` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_cart_items_mysql57_guard` BEFORE INSERT ON `cart_items`
FOR EACH ROW
BEGIN
  IF (NEW.`lens_variant_id` IS NULL OR NEW.`lens_product_id` IS NOT NULL) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cart_items_lens_variant_owner failed';
  END IF;
  IF (NEW.`quantity` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cart_items_quantity failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_cart_items_mysql57_guard` BEFORE UPDATE ON `cart_items`
FOR EACH ROW
BEGIN
  IF (NEW.`lens_variant_id` IS NULL OR NEW.`lens_product_id` IS NOT NULL) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cart_items_lens_variant_owner failed';
  END IF;
  IF (NEW.`quantity` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cart_items_quantity failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `categories` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `parent_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `slug` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `category_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'product',
  `icon` text COLLATE utf8mb4_unicode_ci,
  `banner_image` text COLLATE utf8mb4_unicode_ci,
  `level` int(11) NOT NULL DEFAULT '0',
  `sort_order` int(11) NOT NULL DEFAULT '0',
  `is_featured` tinyint(1) NOT NULL DEFAULT '0',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `seo_title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `seo_description` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_categories_slug` (`slug`),
  KEY `ix_categories_parent_sort` (`parent_id`,`sort_order`,`id`),
  CONSTRAINT `fk_categories_parent_id_categories_id` FOREIGN KEY (`parent_id`) REFERENCES `categories` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES ('cat_021c207590d34a14','cat_ca9d440a48d64e4b','Anak-anak','kids-frame-anak-anak',NULL,'product',NULL,NULL,2,2,0,1,NULL,NULL,'2026-10-23 07:58:16.927281'),('cat_080745e860734087','cat_2278c39968f74d39','Unisex','full-rim-unisex',NULL,'product',NULL,NULL,2,3,0,1,NULL,NULL,'2026-10-23 07:58:16.016571'),('cat_0882be6403ac4ec8','cat_1e21dafc7f3c4850','Progresif','progresif',NULL,'lens',NULL,NULL,1,2,0,1,NULL,NULL,'2026-10-23 07:58:17.280102'),('cat_189e70b2854142af','cat_7c376dc73fc34a3f','Unisex','round-unisex',NULL,'product',NULL,NULL,2,3,0,1,NULL,NULL,'2026-10-23 07:58:13.318889'),('cat_1e21dafc7f3c4850',NULL,'Lensa','lensa',NULL,'lens',NULL,NULL,0,2,1,1,NULL,NULL,'2026-10-23 07:58:11.877529'),('cat_2278c39968f74d39','cat_f9a1ff0356e24b14','Full Rim','full-rim',NULL,'frame',NULL,NULL,1,7,0,1,NULL,NULL,'2026-10-23 07:58:15.551252'),('cat_22a34c693a8842d3','cat_b3f1b68fb5a64695','Pria','oversized-pria',NULL,'product',NULL,NULL,2,0,0,1,NULL,NULL,'2026-10-23 07:58:14.150219'),('cat_263c673054d14d28','cat_64cac2c66f40435e','Pria','sport-frame-pria',NULL,'product',NULL,NULL,2,0,0,1,NULL,NULL,'2026-10-23 07:58:16.196973'),('cat_2770f9ae4fb747c5','cat_f9a1ff0356e24b14','Square','square',NULL,'frame',NULL,NULL,1,3,1,1,NULL,NULL,'2026-10-23 07:58:13.405878'),('cat_2a242467e0f54243','cat_4ab3c4baea774537','Wanita','rimless-wanita',NULL,'product',NULL,NULL,2,1,0,1,NULL,NULL,'2026-10-23 07:58:14.772481'),('cat_2b4c108059d64203','cat_b3f1b68fb5a64695','Anak-anak','oversized-anak-anak',NULL,'product',NULL,NULL,2,2,0,1,NULL,NULL,'2026-10-23 07:58:14.391289'),('cat_2b537e48483a4811','cat_6a0f0bacaa6c4ee8','Anak-anak','half-rim-anak-anak',NULL,'product',NULL,NULL,2,2,0,1,NULL,NULL,'2026-10-23 07:58:15.407052'),('cat_3502c02ad4ac4d8d','cat_8e2e391496d84aba','Paket Anak','paket-anak',NULL,'package',NULL,NULL,1,2,0,1,NULL,NULL,'2026-10-23 07:58:18.028809'),('cat_3bf714e989974562','cat_2770f9ae4fb747c5','Pria','square-pria',NULL,'product',NULL,NULL,2,0,0,1,NULL,NULL,'2026-10-23 07:58:13.507468'),('cat_40be3187b63b4230','cat_7c376dc73fc34a3f','Pria','round-pria',NULL,'product',NULL,NULL,2,0,0,1,NULL,NULL,'2026-10-23 07:58:13.043168'),('cat_4ab3c4baea774537','cat_f9a1ff0356e24b14','Rimless','rimless',NULL,'frame',NULL,NULL,1,5,0,1,NULL,NULL,'2026-10-23 07:58:14.575644'),('cat_4bb0610322c04fae','cat_67fb4e6c624a4ce0','Pria','leinz-pria',NULL,'product',NULL,NULL,2,0,0,1,NULL,NULL,'2026-10-23 07:58:12.097895'),('cat_57160db9e3b14d10','cat_2278c39968f74d39','Pria','full-rim-pria',NULL,'product',NULL,NULL,2,0,0,1,NULL,NULL,'2026-10-23 07:58:15.634221'),('cat_5812461f3eca431b','cat_deabeef8b42b4551','Unisex','cat-eye-unisex',NULL,'product',NULL,NULL,2,3,0,1,NULL,NULL,'2026-10-23 07:58:12.842494'),('cat_5895ef68d51c4d2e','cat_67fb4e6c624a4ce0','Unisex','leinz-unisex',NULL,'product',NULL,NULL,2,3,0,1,NULL,NULL,'2026-10-23 07:58:12.431007'),('cat_60c7baaf72ae4567','cat_6a0f0bacaa6c4ee8','Pria','half-rim-pria',NULL,'product',NULL,NULL,2,0,0,1,NULL,NULL,'2026-10-23 07:58:15.162240'),('cat_64cac2c66f40435e','cat_f9a1ff0356e24b14','Sport Frame','sport-frame',NULL,'frame',NULL,NULL,1,8,0,1,NULL,NULL,'2026-10-23 07:58:16.097274'),('cat_67fb4e6c624a4ce0','cat_f9a1ff0356e24b14','Leinz','leinz',NULL,'frame',NULL,NULL,1,0,1,1,NULL,NULL,'2026-10-23 07:58:12.011257'),('cat_6a0f0bacaa6c4ee8','cat_f9a1ff0356e24b14','Half Rim','half-rim',NULL,'frame',NULL,NULL,1,6,0,1,NULL,NULL,'2026-10-23 07:58:15.073547'),('cat_6e7e4df78fbf4fff','cat_b3f1b68fb5a64695','Unisex','oversized-unisex',NULL,'product',NULL,NULL,2,3,0,1,NULL,NULL,'2026-10-23 07:58:14.501732'),('cat_71b46a9ac639436a','cat_8e2e391496d84aba','Paket Hemat','paket-hemat',NULL,'package',NULL,NULL,1,0,0,1,NULL,NULL,'2026-10-23 07:58:17.683258'),('cat_7af8d1b347834588','cat_1e21dafc7f3c4850','Single Vision','single-vision',NULL,'lens',NULL,NULL,1,0,0,1,NULL,NULL,'2026-10-23 07:58:17.098675'),('cat_7b0baaab7c314bdf','cat_ca9d440a48d64e4b','Wanita','kids-frame-wanita',NULL,'product',NULL,NULL,2,1,0,1,NULL,NULL,'2026-10-23 07:58:16.833198'),('cat_7c376dc73fc34a3f','cat_f9a1ff0356e24b14','Round','round',NULL,'frame',NULL,NULL,1,2,1,1,NULL,NULL,'2026-10-23 07:58:12.911788'),('cat_7dbdc3b4be924c27','cat_2770f9ae4fb747c5','Wanita','square-wanita',NULL,'product',NULL,NULL,2,1,0,1,NULL,NULL,'2026-10-23 07:58:13.584781'),('cat_86849a3a92084a57','cat_1e21dafc7f3c4850','Anti Radiasi (Blue Cut)','anti-radiasi-blue-cut',NULL,'lens',NULL,NULL,1,3,0,1,NULL,NULL,'2026-10-23 07:58:17.355647'),('cat_8a7fd6fddc5341fa','cat_deabeef8b42b4551','Anak-anak','cat-eye-anak-anak',NULL,'product',NULL,NULL,2,2,0,1,NULL,NULL,'2026-10-23 07:58:12.763840'),('cat_8e2e391496d84aba',NULL,'Paket Frame + Lensa','paket-frame-lensa',NULL,'package',NULL,NULL,0,3,1,1,NULL,NULL,'2026-10-23 07:58:11.926076'),('cat_90943cf30dee4098','cat_2770f9ae4fb747c5','Unisex','square-unisex',NULL,'product',NULL,NULL,2,3,0,1,NULL,NULL,'2026-10-23 07:58:13.873089'),('cat_a15c84a7ca154e17','cat_4ab3c4baea774537','Anak-anak','rimless-anak-anak',NULL,'product',NULL,NULL,2,2,0,1,NULL,NULL,'2026-10-23 07:58:14.906655'),('cat_a57421c7ee3b4826','cat_1e21dafc7f3c4850','Photochromic','photochromic',NULL,'lens',NULL,NULL,1,4,0,1,NULL,NULL,'2026-10-23 07:58:17.432839'),('cat_aa49c313f65e4610','cat_64cac2c66f40435e','Wanita','sport-frame-wanita',NULL,'product',NULL,NULL,2,1,0,1,NULL,NULL,'2026-10-23 07:58:16.305550'),('cat_ab44ff7d3aec41d7','cat_b3f1b68fb5a64695','Wanita','oversized-wanita',NULL,'product',NULL,NULL,2,1,0,1,NULL,NULL,'2026-10-23 07:58:14.267155'),('cat_af51edff4e9841ff','cat_1e21dafc7f3c4850','Bifokal','bifokal',NULL,'lens',NULL,NULL,1,1,0,1,NULL,NULL,'2026-10-23 07:58:17.200777'),('cat_b3f1b68fb5a64695','cat_f9a1ff0356e24b14','Oversized','oversized',NULL,'frame',NULL,NULL,1,4,0,1,NULL,NULL,'2026-10-23 07:58:13.973034'),('cat_b869fc45e3484158','cat_2278c39968f74d39','Wanita','full-rim-wanita',NULL,'product',NULL,NULL,2,1,0,1,NULL,NULL,'2026-10-23 07:58:15.749410'),('cat_b9c108beb0fd4d03','cat_64cac2c66f40435e','Unisex','sport-frame-unisex',NULL,'product',NULL,NULL,2,3,0,1,NULL,NULL,'2026-10-23 07:58:16.512081'),('cat_bbe67449c51b4ecd','cat_7c376dc73fc34a3f','Anak-anak','round-anak-anak',NULL,'product',NULL,NULL,2,2,0,1,NULL,NULL,'2026-10-23 07:58:13.234192'),('cat_c67d33f78ebb4d52','cat_4ab3c4baea774537','Pria','rimless-pria',NULL,'product',NULL,NULL,2,0,0,1,NULL,NULL,'2026-10-23 07:58:14.648478'),('cat_c7c70e7520d7451c','cat_6a0f0bacaa6c4ee8','Wanita','half-rim-wanita',NULL,'product',NULL,NULL,2,1,0,1,NULL,NULL,'2026-10-23 07:58:15.256117'),('cat_c8db483f74e047f0','cat_67fb4e6c624a4ce0','Wanita','leinz-wanita',NULL,'product',NULL,NULL,2,1,0,1,NULL,NULL,'2026-10-23 07:58:12.182049'),('cat_ca9d440a48d64e4b','cat_f9a1ff0356e24b14','Kids Frame','kids-frame',NULL,'frame',NULL,NULL,1,9,0,1,NULL,NULL,'2026-10-23 07:58:16.603568'),('cat_d1cf64ed5dbe41af','cat_8e2e391496d84aba','Paket Premium','paket-premium',NULL,'package',NULL,NULL,1,1,0,1,NULL,NULL,'2026-10-23 07:58:17.944415'),('cat_d64afabb5cd74370','cat_2278c39968f74d39','Anak-anak','full-rim-anak-anak',NULL,'product',NULL,NULL,2,2,0,1,NULL,NULL,'2026-10-23 07:58:15.947495'),('cat_da3988e651d349bb','cat_2770f9ae4fb747c5','Anak-anak','square-anak-anak',NULL,'product',NULL,NULL,2,2,0,1,NULL,NULL,'2026-10-23 07:58:13.678387'),('cat_deabeef8b42b4551','cat_f9a1ff0356e24b14','Cat Eye','cat-eye',NULL,'frame',NULL,NULL,1,1,1,1,NULL,NULL,'2026-10-23 07:58:12.525867'),('cat_e0992e7915e44e55','cat_deabeef8b42b4551','Pria','cat-eye-pria',NULL,'product',NULL,NULL,2,0,0,1,NULL,NULL,'2026-10-23 07:58:12.605745'),('cat_e1997c95480c4340','cat_ca9d440a48d64e4b','Pria','kids-frame-pria',NULL,'product',NULL,NULL,2,0,0,1,NULL,NULL,'2026-10-23 07:58:16.704413'),('cat_e286907b48cb4e53','cat_64cac2c66f40435e','Anak-anak','sport-frame-anak-anak',NULL,'product',NULL,NULL,2,2,0,1,NULL,NULL,'2026-10-23 07:58:16.399051'),('cat_ed2ac43616284c5e','cat_6a0f0bacaa6c4ee8','Unisex','half-rim-unisex',NULL,'product',NULL,NULL,2,3,0,1,NULL,NULL,'2026-10-23 07:58:15.481800'),('cat_ee34eb85616b40e4','cat_7c376dc73fc34a3f','Wanita','round-wanita',NULL,'product',NULL,NULL,2,1,0,1,NULL,NULL,'2026-10-23 07:58:13.142883'),('cat_f4e07e43d00145b7','cat_67fb4e6c624a4ce0','Anak-anak','leinz-anak-anak',NULL,'product',NULL,NULL,2,2,0,1,NULL,NULL,'2026-10-23 07:58:12.349651'),('cat_f7ac52c8052b4254','cat_4ab3c4baea774537','Unisex','rimless-unisex',NULL,'product',NULL,NULL,2,3,0,1,NULL,NULL,'2026-10-23 07:58:14.979615'),('cat_f9a1ff0356e24b14',NULL,'Frame','frame',NULL,'frame',NULL,NULL,0,1,1,1,NULL,NULL,'2026-10-23 07:58:11.818064'),('cat_faefff9a71944a61','cat_1e21dafc7f3c4850','Polarized','polarized',NULL,'lens',NULL,NULL,1,5,0,1,NULL,NULL,'2026-10-23 07:58:17.544945'),('cat_fc53a5d7fa854ec3','cat_deabeef8b42b4551','Wanita','cat-eye-wanita',NULL,'product',NULL,NULL,2,1,0,1,NULL,NULL,'2026-10-23 07:58:12.678678'),('cat_ff7394b7bb934c85','cat_ca9d440a48d64e4b','Unisex','kids-frame-unisex',NULL,'product',NULL,NULL,2,3,0,1,NULL,NULL,'2026-10-23 07:58:17.008826');
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_categories_mysql57_guard` BEFORE INSERT ON `categories`
FOR EACH ROW
BEGIN
  IF (NEW.`level` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_categories_level_nonnegative failed';
  END IF;
  IF (NEW.`parent_id` IS NULL OR NEW.`parent_id` <> NEW.`id`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_categories_not_own_parent failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_categories_mysql57_guard` BEFORE UPDATE ON `categories`
FOR EACH ROW
BEGIN
  IF (NEW.`level` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_categories_level_nonnegative failed';
  END IF;
  IF (NEW.`parent_id` IS NULL OR NEW.`parent_id` <> NEW.`id`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_categories_not_own_parent failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `cms_pages`
--

DROP TABLE IF EXISTS `cms_pages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cms_pages` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `page_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'custom',
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `slug` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` mediumtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'draft',
  `version` int(11) NOT NULL DEFAULT '1',
  `seo_title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `seo_description` text COLLATE utf8mb4_unicode_ci,
  `published_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_cms_pages_slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cms_pages`
--

LOCK TABLES `cms_pages` WRITE;
/*!40000 ALTER TABLE `cms_pages` DISABLE KEYS */;
INSERT INTO `cms_pages` VALUES ('pg_556d58cad6cb4055','about','Tentang Meow Eyes','tentang-meow-eyes','<h2>Tentang Meow Eyes 🐱👓</h2><p>Meow Eyes adalah marketplace kacamata online yang dibangun dengan kecintaan pada fashion, teknologi, dan tentu saja... kucing! Kami menyediakan frame berkualitas premium dari Leinz, Catlux, MeowOptik, PurrLens, dan brand pilihan lainnya.</p><p>Misi kami: bikin setiap orang bisa lihat dunia dengan tatapan meow yang stylish.</p><img src=\"/api/uploads-files/2026-11/d5419dd7180c47c8be57f421ea96ab5e.jpg\" alt=\"\" width=\"61.2%\" style=\"width: 61.2%;\" data-align=\"center\"><p></p>','published',2,NULL,NULL,'2026-10-23 08:02:35.696807','2026-11-10 02:37:17.638299','2026-10-23 08:02:35.696866'),('pg_58293e119d024a8e','privacy_policy','Kebijakan Privasi','kebijakan-privasi','<h2>Kebijakan Privasi Meow Eyes</h2>\n<p>Kami menjaga kerahasiaan data pribadi Anda seperti kami menjaga kucing kesayangan sendiri. 🐱</p>\n<h3>Data yang Kami Kumpulkan</h3>\n<ul>\n<li>Nama, email, nomor telepon (saat registrasi)</li>\n<li>Alamat pengiriman</li>\n<li>Riwayat pembelian & pembayaran</li>\n</ul>\n<h3>Penggunaan Data</h3>\n<p>Data digunakan untuk memproses pesanan, mengirim update pesanan, kampanye pemasaran (opt-in), serta rekomendasi produk.</p>\n<h3>Keamanan</h3>\n<p>Semua data dienkripsi (bcrypt untuk password/PIN), dan pembayaran diproses oleh DOKU dengan standar PCI-DSS.</p>','published',1,NULL,NULL,'2026-10-23 08:02:35.589948','2026-10-23 08:02:35.590014','2026-10-23 08:02:35.590009'),('pg_633c6cadf6f94a99','refund_policy','Kebijakan Refund','kebijakan-refund','<h2>Kebijakan Refund</h2>\n<p>Refund berlaku dalam kondisi:</p>\n<ul>\n<li>Produk cacat produksi & masih dalam masa garansi</li>\n<li>Ada kesalahan pengiriman dari sisi kami</li>\n<li>Order dibatalkan sebelum diproses</li>\n</ul>\n<p>Refund akan diproses 3-7 hari kerja ke rekening asal pembayaran.</p>','published',1,NULL,NULL,'2026-10-23 08:02:35.639678','2026-10-23 08:02:35.639760','2026-10-23 08:02:35.639755'),('pg_88defba273fe49ec','terms_conditions','Syarat & Ketentuan','syarat-ketentuan','<h2>Syarat & Ketentuan</h2>\n<p>Dengan menggunakan Meow Eyes, Anda setuju dengan syarat berikut:</p>\n<ol>\n<li>Semua transaksi final setelah pembayaran berhasil.</li>\n<li>Voucher tidak dapat digabung kecuali disebutkan.</li>\n<li>Reward roulette berlaku sesuai masa berlaku, tidak dapat ditukar uang.</li>\n<li>Meow Eyes berhak mengubah harga, promo, dan ketersediaan produk sewaktu-waktu.</li>\n</ol>','published',1,NULL,NULL,'2026-10-23 08:02:35.615983','2026-10-23 08:02:35.616050','2026-10-23 08:02:35.616044'),('pg_f94f79e60bce4d25','shipping_policy','Kebijakan Pengiriman','kebijakan-pengiriman','<h2>Kebijakan Pengiriman</h2>\n<p>Meow Eyes bekerjasama dengan aggregator EVERPRO (JNE, J&T, SiCepat, AnterAja, GoSend).</p>\n<ul>\n<li>Order dikirim maksimal 1 hari kerja setelah pembayaran</li>\n<li>Estimasi tiba tergantung kurir & tujuan</li>\n<li>Tracking otomatis di halaman detail pesanan</li>\n</ul>','published',1,NULL,NULL,'2026-10-23 08:02:35.662828','2026-10-23 08:02:35.662893','2026-10-23 08:02:35.662887');
/*!40000 ALTER TABLE `cms_pages` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_cms_pages_mysql57_guard` BEFORE INSERT ON `cms_pages`
FOR EACH ROW
BEGIN
  IF (NEW.`page_type` IN ('about','privacy_policy','terms_conditions','refund_policy','shipping_policy','custom')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cms_pages_page_type failed';
  END IF;
  IF (NEW.`status` IN ('draft','published','unpublished','archived')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cms_pages_status failed';
  END IF;
  IF (NEW.`version` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cms_pages_version failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_cms_pages_mysql57_guard` BEFORE UPDATE ON `cms_pages`
FOR EACH ROW
BEGIN
  IF (NEW.`page_type` IN ('about','privacy_policy','terms_conditions','refund_policy','shipping_policy','custom')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cms_pages_page_type failed';
  END IF;
  IF (NEW.`status` IN ('draft','published','unpublished','archived')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cms_pages_status failed';
  END IF;
  IF (NEW.`version` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_cms_pages_version failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `contact_messages`
--

DROP TABLE IF EXISTS `contact_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `contact_messages` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `subject` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `message` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'new',
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `ix_contact_messages_inbox` (`status`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contact_messages`
--

LOCK TABLES `contact_messages` WRITE;
/*!40000 ALTER TABLE `contact_messages` DISABLE KEYS */;
/*!40000 ALTER TABLE `contact_messages` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_contact_messages_mysql57_guard` BEFORE INSERT ON `contact_messages`
FOR EACH ROW
BEGIN
  IF (NEW.`status` IN ('new','read','replied')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_contact_messages_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_contact_messages_mysql57_guard` BEFORE UPDATE ON `contact_messages`
FOR EACH ROW
BEGIN
  IF (NEW.`status` IN ('new','read','replied')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_contact_messages_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `contact_settings`
--

DROP TABLE IF EXISTS `contact_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `contact_settings` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `singleton_key` smallint(6) NOT NULL DEFAULT '1',
  `store_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Meow Eyes',
  `address` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `operational_hours` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `instagram` text COLLATE utf8mb4_unicode_ci,
  `facebook` text COLLATE utf8mb4_unicode_ci,
  `tiktok` text COLLATE utf8mb4_unicode_ci,
  `tokopedia` text COLLATE utf8mb4_unicode_ci,
  `shopee` text COLLATE utf8mb4_unicode_ci,
  `google_maps_embed` text COLLATE utf8mb4_unicode_ci,
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_contact_settings_singleton_key` (`singleton_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contact_settings`
--

LOCK TABLES `contact_settings` WRITE;
/*!40000 ALTER TABLE `contact_settings` DISABLE KEYS */;
INSERT INTO `contact_settings` VALUES ('cs_ad4b09c4b3c94ed1',1,'Meow Eyes','Jl. Cat Eye Square No. 9, Kebayoran Baru, Jakarta Selatan 12130','hello@meoweyes.id','021-1234-5678','Senin - Sabtu, 09:00 - 20:00 WIB','https://instagram.com/meoweyes.id','https://facebook.com/meoweyes.id','https://tiktok.com/@meoweyes.id','https://tokopedia.com/meoweyes','https://shopee.co.id/meoweyes',NULL,'2026-10-23 08:02:35.750284');
/*!40000 ALTER TABLE `contact_settings` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_contact_settings_mysql57_guard` BEFORE INSERT ON `contact_settings`
FOR EACH ROW
BEGIN
  IF (NEW.`singleton_key` = 1) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_contact_settings_singleton failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_contact_settings_mysql57_guard` BEFORE UPDATE ON `contact_settings`
FOR EACH ROW
BEGIN
  IF (NEW.`singleton_key` = 1) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_contact_settings_singleton failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `customer_profiles`
--

DROP TABLE IF EXISTS `customer_profiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `customer_profiles` (
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `phone` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `birth_date` date DEFAULT NULL,
  `gender` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` text COLLATE utf8mb4_unicode_ci,
  `active_prescription_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `prescription_date` date DEFAULT NULL,
  `version` int(11) NOT NULL DEFAULT '1',
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`user_id`),
  KEY `fk_customer_profiles_active_prescription_id_us_fb9a7da0b44d` (`active_prescription_id`,`user_id`),
  CONSTRAINT `fk_customer_profiles_active_prescription_id_us_fb9a7da0b44d` FOREIGN KEY (`active_prescription_id`, `user_id`) REFERENCES `prescriptions` (`id`, `user_id`),
  CONSTRAINT `fk_customer_profiles_user_id_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customer_profiles`
--

LOCK TABLES `customer_profiles` WRITE;
/*!40000 ALTER TABLE `customer_profiles` DISABLE KEYS */;
INSERT INTO `customer_profiles` VALUES ('usr_c4b3d45ff0b94ffd','0192389823','2026-02-12',NULL,NULL,'rx_8a7793124f314342','2026-11-09',1,'2026-11-09 08:42:43.687137','2026-11-09 08:42:43.568452');
/*!40000 ALTER TABLE `customer_profiles` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_customer_profiles_bi` BEFORE INSERT ON `customer_profiles`
FOR EACH ROW
BEGIN
  IF (NEW.`gender` IS NULL OR NEW.`gender` IN ('male','female','unspecified')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_customer_profiles_gender failed'; END IF;
  IF (NEW.`version` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_customer_profiles_version failed'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_customer_profiles_bu` BEFORE UPDATE ON `customer_profiles`
FOR EACH ROW
BEGIN
  IF (NEW.`gender` IS NULL OR NEW.`gender` IN ('male','female','unspecified')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_customer_profiles_gender failed'; END IF;
  IF (NEW.`version` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_customer_profiles_version failed'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `faq_categories`
--

DROP TABLE IF EXISTS `faq_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `faq_categories` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `slug` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `sort_order` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_faq_categories_slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `faq_categories`
--

LOCK TABLES `faq_categories` WRITE;
/*!40000 ALTER TABLE `faq_categories` DISABLE KEYS */;
INSERT INTO `faq_categories` VALUES ('fqc_02dbe523cec2494f','Garansi & Retur','garansi-retur',NULL,1,3),('fqc_3eb115998c8f4323','Pengiriman','pengiriman',NULL,1,2),('fqc_47ce480bad944c1b','Pembayaran','pembayaran',NULL,1,1),('fqc_b887263bb8694cf7','Pemesanan','pemesanan',NULL,1,0);
/*!40000 ALTER TABLE `faq_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `faqs`
--

DROP TABLE IF EXISTS `faqs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `faqs` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `category_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `question` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `answer` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `sort_order` int(11) NOT NULL DEFAULT '0',
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `ix_faqs_public` (`category_id`,`is_active`,`sort_order`),
  CONSTRAINT `fk_faqs_category_id_faq_categories_id` FOREIGN KEY (`category_id`) REFERENCES `faq_categories` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `faqs`
--

LOCK TABLES `faqs` WRITE;
/*!40000 ALTER TABLE `faqs` DISABLE KEYS */;
INSERT INTO `faqs` VALUES ('faq_5a6dafe71ec44ca1','fqc_3eb115998c8f4323','Berapa lama pengiriman?','Tergantung kurir yang kamu pilih. JNE REG 2-3 hari, JNE YES 1 hari, GoSend Instant hari yang sama.',1,3,'2026-10-23 08:02:35.495837'),('faq_781f5b95fd1d42db','fqc_02dbe523cec2494f','Apakah ada garansi?','Ya, semua frame & lensa mendapat garansi 12 bulan untuk cacat produksi.',1,4,'2026-10-23 08:02:35.523286'),('faq_ac0e639d34234d37','fqc_b887263bb8694cf7','Bisa pilih frame + lensa sekaligus?','Bisa! Di halaman detail frame, ada opsi \'Tambahkan Lensa\'. Kamu bisa pilih jenis lensa, index, dan input resep kalau perlu.',1,1,'2026-10-23 08:02:35.427416'),('faq_e225050130d847b5','fqc_47ce480bad944c1b','Apa saja metode pembayaran yang tersedia?','Saat ini kami mendukung DOKU Virtual Account (BCA, Mandiri, BNI, BRI) dengan validitas 1 jam.',1,2,'2026-10-23 08:02:35.464017'),('faq_ea500b2727fa4989','fqc_02dbe523cec2494f','Bisa retur / tukar barang?','Bisa dalam 7 hari sejak diterima jika produk masih segel dan tidak ada kerusakan pemakaian.',1,5,'2026-10-23 08:02:35.547999'),('faq_f9110a6950094f96','fqc_b887263bb8694cf7','Bagaimana cara memesan di Meow Eyes?','Pilih produk > tambahkan ke cart > checkout > masukkan PIN 6 digit > bayar via DOKU.',1,0,'2026-10-23 08:02:35.364241');
/*!40000 ALTER TABLE `faqs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `flash_sale_categories`
--

DROP TABLE IF EXISTS `flash_sale_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `flash_sale_categories` (
  `flash_sale_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `category_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `include_descendants` tinyint(1) NOT NULL DEFAULT '1',
  `discount_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `discount_value` decimal(18,2) NOT NULL,
  `quota_per_product` int(11) NOT NULL,
  PRIMARY KEY (`flash_sale_id`,`category_id`),
  KEY `fk_flash_sale_categories_category_id_categories_id` (`category_id`),
  CONSTRAINT `fk_flash_sale_categories_category_id_categories_id` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`),
  CONSTRAINT `fk_flash_sale_categories_flash_sale_id_flash_sales_id` FOREIGN KEY (`flash_sale_id`) REFERENCES `flash_sales` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `flash_sale_categories`
--

LOCK TABLES `flash_sale_categories` WRITE;
/*!40000 ALTER TABLE `flash_sale_categories` DISABLE KEYS */;
INSERT INTO `flash_sale_categories` VALUES ('fls_41310c1d4b6140fb','cat_ca9d440a48d64e4b',1,'percent',75.00,10),('fls_c97b6d85d7d244b1','cat_ca9d440a48d64e4b',1,'percent',60.00,10);
/*!40000 ALTER TABLE `flash_sale_categories` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_flash_sale_categories_mysql57_guard` BEFORE INSERT ON `flash_sale_categories`
FOR EACH ROW
BEGIN
  IF (NEW.`discount_value` >= 0 AND NEW.`quota_per_product` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_categories_amounts failed';
  END IF;
  IF (NEW.`discount_type` <> 'percent' OR NEW.`discount_value` <= 100) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_categories_percentage failed';
  END IF;
  IF (NEW.`discount_type` IN ('percent','nominal','fixed_price')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_categories_type failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_flash_sale_categories_mysql57_guard` BEFORE UPDATE ON `flash_sale_categories`
FOR EACH ROW
BEGIN
  IF (NEW.`discount_value` >= 0 AND NEW.`quota_per_product` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_categories_amounts failed';
  END IF;
  IF (NEW.`discount_type` <> 'percent' OR NEW.`discount_value` <= 100) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_categories_percentage failed';
  END IF;
  IF (NEW.`discount_type` IN ('percent','nominal','fixed_price')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_categories_type failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `flash_sale_items`
--

DROP TABLE IF EXISTS `flash_sale_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `flash_sale_items` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `flash_sale_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `source_category_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `flash_price` decimal(18,2) NOT NULL,
  `quota` int(11) NOT NULL,
  `sold` int(11) NOT NULL DEFAULT '0',
  `reserved` int(11) NOT NULL DEFAULT '0',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_flash_sale_items_flash_sale_id_product_id` (`flash_sale_id`,`product_id`),
  UNIQUE KEY `uq_flash_sale_items_id_product_id` (`id`,`product_id`),
  KEY `fk_flash_sale_items_flash_sale_id_source_categ_0c2c06d567df` (`flash_sale_id`,`source_category_id`),
  KEY `ix_flash_sale_items_product` (`product_id`,`flash_sale_id`),
  CONSTRAINT `fk_flash_sale_items_flash_sale_id_flash_sales_id` FOREIGN KEY (`flash_sale_id`) REFERENCES `flash_sales` (`id`),
  CONSTRAINT `fk_flash_sale_items_flash_sale_id_source_categ_0c2c06d567df` FOREIGN KEY (`flash_sale_id`, `source_category_id`) REFERENCES `flash_sale_categories` (`flash_sale_id`, `category_id`),
  CONSTRAINT `fk_flash_sale_items_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `flash_sale_items`
--

LOCK TABLES `flash_sale_items` WRITE;
/*!40000 ALTER TABLE `flash_sale_items` DISABLE KEYS */;
INSERT INTO `flash_sale_items` VALUES ('9ca18cbc00474184b361eebe6a497fe8','fls_41310c1d4b6140fb','prd_898f994b888240ab','cat_ca9d440a48d64e4b',105000.00,10,0,0,0),('d1c3bd3e173b489b876d2ee4f365f400','fls_c97b6d85d7d244b1','prd_898f994b888240ab','cat_ca9d440a48d64e4b',168000.00,10,0,0,1),('imp_4411584530a85faf8fbd3370609b914f','fls_9d6274e94df94512','prd_401170d2b1564810',NULL,780000.00,20,0,0,1),('imp_e8be9a0dfc0b55bf8ce685ba803a5b66','fls_d245f914ad8a4c17','prd_75466e5b7e5c4775',NULL,10.00,10,0,0,1);
/*!40000 ALTER TABLE `flash_sale_items` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_flash_sale_items_mysql57_guard` BEFORE INSERT ON `flash_sale_items`
FOR EACH ROW
BEGIN
  IF (NEW.`flash_price` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_items_price failed';
  END IF;
  IF (NEW.`quota` >= 0 AND NEW.`sold` >= 0 AND NEW.`reserved` >= 0 AND NEW.`sold` + NEW.`reserved` <= NEW.`quota`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_items_quota failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_flash_sale_items_mysql57_guard` BEFORE UPDATE ON `flash_sale_items`
FOR EACH ROW
BEGIN
  IF (NEW.`flash_price` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_items_price failed';
  END IF;
  IF (NEW.`quota` >= 0 AND NEW.`sold` >= 0 AND NEW.`reserved` >= 0 AND NEW.`sold` + NEW.`reserved` <= NEW.`quota`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_items_quota failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `flash_sale_reservations`
--

DROP TABLE IF EXISTS `flash_sale_reservations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `flash_sale_reservations` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_item_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `flash_sale_item_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `quantity` int(11) NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active',
  `expires_at` datetime(6) NOT NULL,
  `resolved_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_flash_sale_reservations_order_item_id_flash_sale_item_id` (`order_item_id`,`flash_sale_item_id`),
  KEY `fk_flash_sale_reservations_flash_sale_item_id__6bebf7ad5666` (`flash_sale_item_id`,`product_id`),
  KEY `fk_flash_sale_reservations_order_item_id_produ_7cde6df012c5` (`order_item_id`,`product_id`),
  KEY `ix_flash_sale_reservations_expiry` (`status`,`expires_at`),
  CONSTRAINT `fk_flash_sale_reservations_flash_sale_item_id__6bebf7ad5666` FOREIGN KEY (`flash_sale_item_id`, `product_id`) REFERENCES `flash_sale_items` (`id`, `product_id`),
  CONSTRAINT `fk_flash_sale_reservations_order_item_id_produ_7cde6df012c5` FOREIGN KEY (`order_item_id`, `product_id`) REFERENCES `order_items` (`id`, `product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `flash_sale_reservations`
--

LOCK TABLES `flash_sale_reservations` WRITE;
/*!40000 ALTER TABLE `flash_sale_reservations` DISABLE KEYS */;
/*!40000 ALTER TABLE `flash_sale_reservations` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_flash_sale_reservations_mysql57_guard` BEFORE INSERT ON `flash_sale_reservations`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_reservations_quantity failed';
  END IF;
  IF (NEW.`status` IN ('active','confirmed','expired','cancelled')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_reservations_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_flash_sale_reservations_mysql57_guard` BEFORE UPDATE ON `flash_sale_reservations`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_reservations_quantity failed';
  END IF;
  IF (NEW.`status` IN ('active','confirmed','expired','cancelled')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sale_reservations_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `flash_sales`
--

DROP TABLE IF EXISTS `flash_sales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `flash_sales` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `start_at` datetime(6) NOT NULL,
  `end_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `activated_at` datetime(6) DEFAULT NULL,
  `ended_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `ix_flash_sales_window` (`is_active`,`start_at`,`end_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `flash_sales`
--

LOCK TABLES `flash_sales` WRITE;
/*!40000 ALTER TABLE `flash_sales` DISABLE KEYS */;
INSERT INTO `flash_sales` VALUES ('fls_41310c1d4b6140fb','PROMO ANAK ANAK','2026-11-09 08:58:08.739000','2026-11-10 08:58:08.739000',0,'2026-11-09 09:00:17.438538',NULL,'2026-11-09 08:59:20.336613'),('fls_9d6274e94df94512','Catlux Flash Sale','2026-10-23 06:58:20.536577','2026-10-24 06:58:20.536577',0,NULL,'2026-10-24 06:58:43.032972','2026-10-23 07:58:20.782153'),('fls_c97b6d85d7d244b1','promo anak','2026-11-09 09:03:07.443000','2026-11-10 09:03:07.443000',0,'2026-11-09 09:04:17.440642',NULL,'2026-11-09 09:03:52.786685'),('fls_d245f914ad8a4c17','11.11','2026-10-28 08:48:13.980000','2026-10-29 08:48:13.980000',0,NULL,'2026-10-29 08:48:46.600717','2026-10-28 08:48:50.551956');
/*!40000 ALTER TABLE `flash_sales` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_flash_sales_mysql57_guard` BEFORE INSERT ON `flash_sales`
FOR EACH ROW
BEGIN
  IF (NEW.`end_at` > NEW.`start_at`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sales_window failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_flash_sales_mysql57_guard` BEFORE UPDATE ON `flash_sales`
FOR EACH ROW
BEGIN
  IF (NEW.`end_at` > NEW.`start_at`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_flash_sales_window failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `game_scores`
--

DROP TABLE IF EXISTS `game_scores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `game_scores` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `game` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `score` int(11) NOT NULL,
  `points_awarded` int(11) NOT NULL DEFAULT '0',
  `played_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `ix_game_scores_daily` (`user_id`,`game`,`played_at`),
  KEY `ix_game_scores_leaderboard` (`game`,`score`,`user_id`),
  CONSTRAINT `fk_game_scores_game_games_key` FOREIGN KEY (`game`) REFERENCES `games` (`key`),
  CONSTRAINT `fk_game_scores_user_id_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `game_scores`
--

LOCK TABLES `game_scores` WRITE;
/*!40000 ALTER TABLE `game_scores` DISABLE KEYS */;
INSERT INTO `game_scores` VALUES ('gms_33af796e87a74861','usr_c4b3d45ff0b94ffd','matching',450,45,'2026-11-10 02:22:00.474462'),('gms_9e0552fb0b3e495b','usr_c4b3d45ff0b94ffd','puzzle',280,28,'2026-11-10 02:21:15.836781');
/*!40000 ALTER TABLE `game_scores` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_game_scores_mysql57_guard` BEFORE INSERT ON `game_scores`
FOR EACH ROW
BEGIN
  IF (NEW.`score` >= 0 AND NEW.`points_awarded` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_game_scores_scores failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_game_scores_mysql57_guard` BEFORE UPDATE ON `game_scores`
FOR EACH ROW
BEGIN
  IF (NEW.`score` >= 0 AND NEW.`points_awarded` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_game_scores_scores failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `games`
--

DROP TABLE IF EXISTS `games`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `games` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `key` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `image` text COLLATE utf8mb4_unicode_ci,
  `max_points` int(11) NOT NULL DEFAULT '50',
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_games_key` (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `games`
--

LOCK TABLES `games` WRITE;
/*!40000 ALTER TABLE `games` DISABLE KEYS */;
INSERT INTO `games` VALUES ('gm_2ec577929cdc49e7','matching','Match Meow Pairs','Cocokkan pasangan kartu kacamata kucing!',1,'https://images.unsplash.com/photo-1565127803051-49aaf3d36e29?crop=entropy&cs=srgb&fm=jpg&w=800',50,'2026-10-23 07:58:21.161624'),('gm_8eeb47ecdcb340c3','tetris','Glasses Tetris','Susun bingkai kacamata jatuh ala Tetris',1,'https://images.unsplash.com/photo-1574258495973-f010dfbb5371?crop=entropy&cs=srgb&fm=jpg&w=800',50,'2026-10-23 07:58:21.161713'),('gm_9ba1aba0bb5743a1','puzzle','Meow Puzzle','Susun puzzle kacamata cute Meow Eyes',1,'https://images.unsplash.com/photo-1533738363-b7f9aef128ce?crop=entropy&cs=srgb&fm=jpg&w=800',50,'2026-10-23 07:58:21.161684');
/*!40000 ALTER TABLE `games` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_games_mysql57_guard` BEFORE INSERT ON `games`
FOR EACH ROW
BEGIN
  IF (NEW.`max_points` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_games_max_points failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_games_mysql57_guard` BEFORE UPDATE ON `games`
FOR EACH ROW
BEGIN
  IF (NEW.`max_points` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_games_max_points failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `integration_webhook_events`
--

DROP TABLE IF EXISTS `integration_webhook_events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `integration_webhook_events` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `provider` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `event_key` varchar(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `payload_hash` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `event_type` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `signature_verified` tinyint(1) NOT NULL DEFAULT '0',
  `payload` json NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'received',
  `attempts` int(11) NOT NULL DEFAULT '0',
  `error_code` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `received_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `processed_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_integration_webhook_events_provider_event_key` (`provider`,`event_key`),
  KEY `fk_integration_webhook_events_order_id_orders_id` (`order_id`),
  KEY `ix_webhook_events_retry` (`status`,`received_at`),
  CONSTRAINT `fk_integration_webhook_events_order_id_orders_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `integration_webhook_events`
--

LOCK TABLES `integration_webhook_events` WRITE;
/*!40000 ALTER TABLE `integration_webhook_events` DISABLE KEYS */;
/*!40000 ALTER TABLE `integration_webhook_events` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_integration_webhook_events_mysql57_guard` BEFORE INSERT ON `integration_webhook_events`
FOR EACH ROW
BEGIN
  IF (NEW.`attempts` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_integration_webhook_events_attempts failed';
  END IF;
  IF (NEW.`status` IN ('received','processed','failed','ignored')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_integration_webhook_events_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_integration_webhook_events_mysql57_guard` BEFORE UPDATE ON `integration_webhook_events`
FOR EACH ROW
BEGIN
  IF (NEW.`attempts` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_integration_webhook_events_attempts failed';
  END IF;
  IF (NEW.`status` IN ('received','processed','failed','ignored')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_integration_webhook_events_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `lens_indexes`
--

DROP TABLE IF EXISTS `lens_indexes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `lens_indexes` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `index_value` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `thickness_level` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'medium',
  `recommended_power_range` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `additional_price` decimal(18,2) NOT NULL DEFAULT '0.00',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `sort_order` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `ix_lens_indexes_index_value` (`index_value`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lens_indexes`
--

LOCK TABLES `lens_indexes` WRITE;
/*!40000 ALTER TABLE `lens_indexes` DISABLE KEYS */;
INSERT INTO `lens_indexes` VALUES ('lens_0463b1e229e744c7','1.67 Super Thin','1.67','Super tipis untuk minus/plus di atas 5.00','thinner','-7.00 s/d +7.00',350000.00,1,3),('lens_0d3867c1d33941bc','1.56 Blue Cut','1.56','Anti radiasi biru layar, ringan','medium','-4.00 s/d +4.00',75000.00,1,1),('lens_3eabca2c19484e2f','1.74 Extra Thin','1.74','Paling tipis di kelasnya','thinnest','>-7.00 atau >+7.00',650000.00,1,4),('lens_754bff09833941d3','1.50 Standard','1.50','Standard, cocok untuk minus/plus di bawah 2.00','thick','-2.00 s/d +2.00',0.00,1,0),('lens_ce077e4b7116476e','1.60 Ultra Thin','1.60','Ultra tipis, ringan, cocok minus tinggi','thin','-5.00 s/d +5.00',175000.00,1,2);
/*!40000 ALTER TABLE `lens_indexes` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_lens_indexes_mysql57_guard` BEFORE INSERT ON `lens_indexes`
FOR EACH ROW
BEGIN
  IF (NEW.`additional_price` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_lens_indexes_price failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_lens_indexes_mysql57_guard` BEFORE UPDATE ON `lens_indexes`
FOR EACH ROW
BEGIN
  IF (NEW.`additional_price` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_lens_indexes_price failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `meowsurement_audit_events`
--

DROP TABLE IF EXISTS `meowsurement_audit_events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `meowsurement_audit_events` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `session_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `revision_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `actor_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `action` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `details` json DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `fk_meowsurement_audit_events_session_id_user_i_19b9300e0f0e` (`session_id`,`user_id`),
  KEY `fk_meowsurement_audit_events_revision_id_sessi_09038f20c82f` (`revision_id`,`session_id`,`user_id`),
  KEY `fk_meowsurement_audit_events_actor_id_users_user_id` (`actor_id`),
  KEY `ix_meowsurement_audit_owner` (`user_id`,`created_at`,`id`),
  CONSTRAINT `fk_meowsurement_audit_events_actor_id_users_user_id` FOREIGN KEY (`actor_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `fk_meowsurement_audit_events_revision_id_sessi_09038f20c82f` FOREIGN KEY (`revision_id`, `session_id`, `user_id`) REFERENCES `meowsurement_revisions` (`id`, `session_id`, `user_id`),
  CONSTRAINT `fk_meowsurement_audit_events_session_id_user_i_19b9300e0f0e` FOREIGN KEY (`session_id`, `user_id`) REFERENCES `meowsurement_sessions` (`id`, `user_id`),
  CONSTRAINT `fk_meowsurement_audit_events_user_id_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `meowsurement_audit_events`
--

LOCK TABLES `meowsurement_audit_events` WRITE;
/*!40000 ALTER TABLE `meowsurement_audit_events` DISABLE KEYS */;
INSERT INTO `meowsurement_audit_events` VALUES ('ma_0df19170c2f246aa9a4b424ef5a4715f','usr_c4b3d45ff0b94ffd','ms_f590b06bc5d34192bee59f0371955abe','mr_29190347df2a4429ba3ac8a1c80f8393','usr_c4b3d45ff0b94ffd','photo.uploaded','{\"photo_id\": \"mp_084dd33987c24014bebdc753dff3420a\", \"retention_days\": 30, \"explicit_consent\": true}','2026-11-10 02:56:47.593950'),('ma_281e311f45124c258e78d0b548735add','usr_c4b3d45ff0b94ffd','ms_8c2a17db7e0c4b2b8a57029c89623953','mr_cf4815a4e7f346cda3a7202278e238cd','usr_c4b3d45ff0b94ffd','photo.uploaded','{\"photo_id\": \"mp_4c362829cebe4a9882a8c86f05bc0413\", \"retention_days\": 30, \"explicit_consent\": true}','2026-11-10 02:30:36.394650'),('ma_306b4c5d4bc7449db08f1358d3563b3f','usr_c4b3d45ff0b94ffd','ms_28dd1244f2934db28dd0ae7c8996d442','mr_ac99c69597704000a52067ebe7cb1c94','usr_c4b3d45ff0b94ffd','session.created','{\"spec_version\": 1, \"profile_version\": 1}','2026-11-09 08:47:37.888613'),('ma_655879a62ac0449f883ba267a37a3ac8','usr_c4b3d45ff0b94ffd','ms_8c2a17db7e0c4b2b8a57029c89623953','mr_cf4815a4e7f346cda3a7202278e238cd','usr_c4b3d45ff0b94ffd','revision.created','{\"revision_number\": 2}','2026-11-10 02:29:10.610597'),('ma_75ffe41b68a54f5eae566b8469b8b3d3','usr_c4b3d45ff0b94ffd','ms_f590b06bc5d34192bee59f0371955abe','mr_29190347df2a4429ba3ac8a1c80f8393','usr_c4b3d45ff0b94ffd','photo.uploaded','{\"photo_id\": \"mp_0caa65dba9494776837d81d5b9d50b4e\", \"retention_days\": 30, \"explicit_consent\": true}','2026-11-10 02:56:47.396701'),('ma_825a043aa08c4b4aa0cea92ee27a2216','usr_c4b3d45ff0b94ffd','ms_28dd1244f2934db28dd0ae7c8996d442','mr_90517ef3d84d40c7be49090f64ccdbe5','usr_c4b3d45ff0b94ffd','revision.created','{\"revision_number\": 2}','2026-11-09 08:48:00.706414'),('ma_8d9350ad60864c109b718b500849200d','usr_c4b3d45ff0b94ffd','ms_f590b06bc5d34192bee59f0371955abe','mr_2df7aa062c6541369dc3ea6a9eed0771','usr_c4b3d45ff0b94ffd','revision.created','{\"revision_number\": 3}','2026-11-10 02:56:47.767136'),('ma_90412650e8414a81a1312c72c8dca04a','usr_c4b3d45ff0b94ffd','ms_b37caba30ed24aafb66185945883f5f1','mr_ba31e276320441b0986f7a0b5d41ebbc','usr_c4b3d45ff0b94ffd','session.created','{\"spec_version\": 1, \"profile_version\": 1}','2026-11-10 02:33:26.692311'),('ma_a0e2ce70036347908e00e172dc22a0ae','usr_c4b3d45ff0b94ffd','ms_f590b06bc5d34192bee59f0371955abe','mr_29190347df2a4429ba3ac8a1c80f8393','usr_c4b3d45ff0b94ffd','revision.created','{\"revision_number\": 2}','2026-11-10 02:55:06.732470'),('ma_a43d638bb158470b94e59e81203739f6','usr_c4b3d45ff0b94ffd','ms_f590b06bc5d34192bee59f0371955abe','mr_29190347df2a4429ba3ac8a1c80f8393','usr_c4b3d45ff0b94ffd','photo.uploaded','{\"photo_id\": \"mp_3e506397bd034da497ccf9027a599fee\", \"retention_days\": 30, \"explicit_consent\": true}','2026-11-10 02:56:47.240317'),('ma_a89bdcf250eb4ebcbda503a03b2c0d5b','usr_c4b3d45ff0b94ffd','ms_f590b06bc5d34192bee59f0371955abe','mr_d25fd2e55e644c618d7b561075d2ec5f','usr_c4b3d45ff0b94ffd','session.created','{\"spec_version\": 1, \"profile_version\": 1}','2026-11-10 02:51:22.033424'),('ma_ab18af55f6f84ccebe22784ac6b75a9e','usr_c4b3d45ff0b94ffd','ms_8c2a17db7e0c4b2b8a57029c89623953','mr_71f19a7b82764acc8ecdc4e262aa73cb','usr_c4b3d45ff0b94ffd','revision.created','{\"revision_number\": 3}','2026-11-10 02:30:36.912715'),('ma_afc3bf56811e40e48aac2155f5f2e537','usr_c4b3d45ff0b94ffd','ms_8c2a17db7e0c4b2b8a57029c89623953','mr_cf4815a4e7f346cda3a7202278e238cd','usr_c4b3d45ff0b94ffd','photo.uploaded','{\"photo_id\": \"mp_f83fadbccf7241e4a397dd665b9f2476\", \"retention_days\": 30, \"explicit_consent\": true}','2026-11-10 02:30:36.564760'),('ma_d05d594f9b1841a9b11cbbb778c5ce55','usr_c4b3d45ff0b94ffd',NULL,NULL,'usr_c4b3d45ff0b94ffd','catalog.frame_specification.updated','{\"version\": 1, \"product_id\": \"prd_898f994b888240ab\"}','2026-11-09 08:46:40.589459'),('ma_d75d7ddc66484adfa055a1ebdc9f91f8','usr_c4b3d45ff0b94ffd','ms_8c2a17db7e0c4b2b8a57029c89623953','mr_cf4815a4e7f346cda3a7202278e238cd','usr_c4b3d45ff0b94ffd','photo.uploaded','{\"photo_id\": \"mp_9db577367ca04a9fa2d5aa6e9fc182fd\", \"retention_days\": 30, \"explicit_consent\": true}','2026-11-10 02:30:36.753023'),('ma_e89e157024994157bafd559004f12ec1','usr_c4b3d45ff0b94ffd','ms_8c2a17db7e0c4b2b8a57029c89623953','mr_92b7c45678234937adc1aa1be5a14943','usr_c4b3d45ff0b94ffd','session.created','{\"spec_version\": 1, \"profile_version\": 1}','2026-11-10 02:28:50.538299'),('ma_fd322b7b66524e7090e3d624331c122a','usr_c4b3d45ff0b94ffd',NULL,NULL,'usr_c4b3d45ff0b94ffd','profile.updated','{\"version\": 1}','2026-11-09 08:42:43.722017');
/*!40000 ALTER TABLE `meowsurement_audit_events` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_audit_events_bi` BEFORE INSERT ON `meowsurement_audit_events`
FOR EACH ROW
BEGIN
  IF (NEW.`revision_id` IS NULL OR NEW.`session_id` IS NOT NULL) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_audit_events_revision_owner failed'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_audit_events_bu` BEFORE UPDATE ON `meowsurement_audit_events`
FOR EACH ROW
BEGIN
  IF (NEW.`revision_id` IS NULL OR NEW.`session_id` IS NOT NULL) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_audit_events_revision_owner failed'; END IF;
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_audit_events_bd` BEFORE DELETE ON `meowsurement_audit_events`
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `meowsurement_captures`
--

DROP TABLE IF EXISTS `meowsurement_captures`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `meowsurement_captures` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `revision_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `session_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `capture_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `view` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `photo_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `photo_hash` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `width` int(11) NOT NULL,
  `height` int(11) NOT NULL,
  `captured_at` datetime(6) DEFAULT NULL,
  `calibration` json DEFAULT NULL,
  `landmarks` json DEFAULT NULL,
  `quality` json DEFAULT NULL,
  `data` json NOT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_meowsurement_captures_revision_id_capture_id` (`revision_id`,`capture_id`),
  UNIQUE KEY `uq_meowsurement_captures_revision_id_id` (`revision_id`,`id`),
  KEY `fk_meowsurement_captures_revision_id_session_i_57d34702e9be` (`revision_id`,`session_id`,`user_id`),
  KEY `fk_meowsurement_captures_session_id_user_id_ph_3ff910ad9b57` (`session_id`,`user_id`,`photo_id`),
  CONSTRAINT `fk_meowsurement_captures_revision_id_session_i_57d34702e9be` FOREIGN KEY (`revision_id`, `session_id`, `user_id`) REFERENCES `meowsurement_revisions` (`id`, `session_id`, `user_id`),
  CONSTRAINT `fk_meowsurement_captures_session_id_user_id_ph_3ff910ad9b57` FOREIGN KEY (`session_id`, `user_id`, `photo_id`) REFERENCES `meowsurement_photos` (`session_id`, `user_id`, `id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `meowsurement_captures`
--

LOCK TABLES `meowsurement_captures` WRITE;
/*!40000 ALTER TABLE `meowsurement_captures` DISABLE KEYS */;
INSERT INTO `meowsurement_captures` VALUES ('mc_1124decd7f14486990cdb5776dc885e0','mr_71f19a7b82764acc8ecdc4e262aa73cb','ms_8c2a17db7e0c4b2b8a57029c89623953','usr_c4b3d45ff0b94ffd','d0a97e7e-050f-4398-8234-8c5ebd9e84f9','frontal','mp_9db577367ca04a9fa2d5aa6e9fc182fd','aedf009c4618cc4c16889d924d1e02b2ba8cf798ed7721f56202c224508e6d4f',960,1280,'2026-11-10 02:30:34.772000','null','{}','{\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 216, 233, 121, 110, 111, 106, 101, 107, 118, 219, 244, 217, 205, 255, 255, 253, 187, 233, 199, 178, 168, 164, 143, 119, 101, 106, 210, 227, 255, 255, 255, 195, 253, 217, 190, 180, 170, 168, 159, 154, 162, 171, 94, 255, 255, 255, 255, 172, 255, 181, 149, 166, 173, 167, 156, 102, 105, 125, 78, 255, 253, 255, 255, 222, 242, 166, 143, 141, 107, 100, 120, 116, 119, 150, 104, 140, 255, 255, 255, 255, 247, 184, 181, 180, 157, 150, 137, 141, 135, 147, 120, 221, 254, 212, 255, 254, 218, 181, 153, 179, 152, 141, 138, 127, 137, 146, 164, 253, 253, 166, 254, 255, 205, 179, 176, 198, 128, 119, 104, 121, 131, 138, 255, 251, 235, 167, 254, 255, 80, 181, 165, 165, 130, 122, 110, 123, 120, 131, 252, 254, 208, 176, 142, 70, 117, 64, 161, 166, 146, 126, 122, 119, 56, 73, 67, 67, 100, 69, 65, 92, 84, 56, 118, 129, 105, 101, 95, 66, 60, 68, 59, 69, 62, 82, 53, 59, 76, 65, 74, 99, 113, 99, 75, 75, 66, 70, 63, 61, 64], \"darkFraction\": 0, \"stdLuminance\": 64.34327068857081, \"analysisWidth\": 240, \"meanLuminance\": 159.02655464843, \"analysisHeight\": 320, \"brightFraction\": 0.2002734375, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 548.633728154622}','{\"id\": \"d0a97e7e-050f-4398-8234-8c5ebd9e84f9\", \"view\": \"frontal\", \"width\": 960, \"device\": {\"zoom\": 1, \"depth\": null, \"width\": 960, \"height\": 1280, \"mirrored\": false, \"frameRate\": 30, \"facingMode\": \"user\", \"intrinsics\": null, \"cameraLabel\": \"camera 1, facing front\", \"orientation\": null, \"sourceWidth\": 960, \"sourceHeight\": 1280, \"mainCameraVerifiedByOperator\": true}, \"height\": 1280, \"points\": {}, \"burstId\": \"a1c9ce47-cf76-42b9-b39e-25d1a0a81412\", \"photoId\": \"mp_9db577367ca04a9fa2d5aa6e9fc182fd\", \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 216, 233, 121, 110, 111, 106, 101, 107, 118, 219, 244, 217, 205, 255, 255, 253, 187, 233, 199, 178, 168, 164, 143, 119, 101, 106, 210, 227, 255, 255, 255, 195, 253, 217, 190, 180, 170, 168, 159, 154, 162, 171, 94, 255, 255, 255, 255, 172, 255, 181, 149, 166, 173, 167, 156, 102, 105, 125, 78, 255, 253, 255, 255, 222, 242, 166, 143, 141, 107, 100, 120, 116, 119, 150, 104, 140, 255, 255, 255, 255, 247, 184, 181, 180, 157, 150, 137, 141, 135, 147, 120, 221, 254, 212, 255, 254, 218, 181, 153, 179, 152, 141, 138, 127, 137, 146, 164, 253, 253, 166, 254, 255, 205, 179, 176, 198, 128, 119, 104, 121, 131, 138, 255, 251, 235, 167, 254, 255, 80, 181, 165, 165, 130, 122, 110, 123, 120, 131, 252, 254, 208, 176, 142, 70, 117, 64, 161, 166, 146, 126, 122, 119, 56, 73, 67, 67, 100, 69, 65, 92, 84, 56, 118, 129, 105, 101, 95, 66, 60, 68, 59, 69, 62, 82, 53, 59, 76, 65, 74, 99, 113, 99, 75, 75, 66, 70, 63, 61, 64], \"darkFraction\": 0, \"stdLuminance\": 64.34327068857081, \"analysisWidth\": 240, \"meanLuminance\": 159.02655464843, \"analysisHeight\": 320, \"brightFraction\": 0.2002734375, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 548.633728154622}, \"createdAt\": \"2026-11-10T02:30:34.772Z\", \"photoHash\": \"aedf009c4618cc4c16889d924d1e02b2ba8cf798ed7721f56202c224508e6d4f\", \"superseded\": false, \"sampleIndex\": 2, \"measurements\": {}, \"burstAnalysis\": {\"note\": \"Pemilihan berdasarkan detail, pencahayaan dan perubahan gambar. Ini bukan stabilitas landmark atau pengulangan nilai ukur.\", \"rows\": [{\"index\": 0, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 219, 223, 122, 109, 114, 107, 105, 104, 110, 153, 246, 216, 204, 255, 255, 234, 159, 227, 198, 177, 167, 163, 140, 114, 97, 99, 139, 225, 255, 255, 255, 188, 250, 224, 194, 180, 169, 165, 158, 150, 162, 170, 100, 254, 255, 255, 255, 174, 255, 214, 192, 177, 172, 167, 166, 155, 140, 135, 75, 254, 251, 255, 255, 253, 252, 190, 150, 141, 156, 137, 98, 130, 134, 156, 254, 247, 255, 255, 255, 255, 254, 188, 163, 174, 179, 142, 135, 132, 129, 144, 245, 219, 254, 234, 250, 253, 215, 166, 212, 182, 180, 159, 151, 119, 121, 143, 157, 254, 253, 169, 254, 255, 200, 173, 186, 191, 193, 128, 141, 112, 123, 135, 254, 234, 255, 163, 252, 255, 85, 183, 150, 171, 171, 133, 111, 121, 121, 125, 246, 255, 239, 180, 148, 70, 122, 64, 152, 166, 151, 132, 125, 119, 57, 70, 66, 65, 103, 68, 65, 92, 81, 58, 122, 130, 107, 96, 98, 64, 58, 66, 59, 66, 66, 94, 53, 57, 72, 65, 70, 96, 112, 99, 74, 72, 68, 70, 67, 63, 61], \"darkFraction\": 0, \"stdLuminance\": 64.01172832662922, \"analysisWidth\": 240, \"meanLuminance\": 157.68188170572682, \"analysisHeight\": 320, \"brightFraction\": 0.19272135416666664, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 554.1889526826051}, \"selectionScore\": 102.31930851108866, \"frameDifference\": null}, {\"index\": 1, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 213, 217, 122, 110, 114, 103, 104, 107, 114, 254, 245, 218, 207, 255, 255, 247, 159, 226, 198, 181, 167, 164, 149, 130, 98, 104, 189, 229, 255, 255, 255, 199, 251, 220, 195, 179, 172, 166, 160, 154, 160, 171, 93, 255, 255, 255, 255, 167, 255, 169, 136, 157, 169, 167, 140, 97, 104, 113, 74, 255, 251, 255, 255, 248, 252, 172, 123, 137, 105, 132, 119, 104, 115, 148, 130, 252, 255, 255, 255, 255, 250, 187, 178, 176, 161, 157, 126, 140, 136, 145, 128, 221, 254, 237, 248, 254, 218, 182, 156, 177, 110, 141, 115, 125, 132, 145, 158, 252, 253, 173, 253, 255, 203, 178, 188, 208, 129, 122, 103, 129, 130, 138, 254, 236, 253, 157, 250, 255, 81, 183, 158, 169, 139, 123, 101, 124, 122, 130, 238, 254, 204, 173, 152, 71, 125, 64, 167, 165, 154, 133, 124, 120, 57, 73, 64, 72, 104, 64, 67, 91, 79, 55, 121, 127, 110, 101, 96, 65, 60, 70, 60, 66, 66, 89, 55, 54, 75, 64, 71, 94, 110, 100, 76, 71, 71, 67, 66, 60, 59], \"darkFraction\": 0, \"stdLuminance\": 64.06198522944985, \"analysisWidth\": 240, \"meanLuminance\": 158.89106833593817, \"analysisHeight\": 320, \"brightFraction\": 0.1975390625, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 529.0478336837755}, \"selectionScore\": 101.5740293462105, \"frameDifference\": 0.0349468954248366}, {\"index\": 2, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 218, 226, 122, 110, 115, 105, 104, 106, 115, 245, 244, 217, 204, 255, 255, 246, 168, 228, 198, 179, 167, 166, 147, 123, 99, 106, 216, 225, 255, 255, 255, 199, 252, 219, 193, 178, 170, 167, 159, 153, 162, 170, 91, 255, 255, 255, 255, 163, 255, 168, 132, 160, 171, 165, 136, 97, 106, 118, 78, 255, 253, 255, 255, 178, 247, 186, 120, 137, 108, 135, 120, 104, 106, 149, 134, 253, 255, 255, 255, 255, 248, 186, 180, 179, 162, 154, 144, 140, 136, 146, 102, 229, 253, 213, 255, 254, 218, 181, 156, 175, 111, 135, 117, 125, 135, 144, 157, 252, 252, 165, 255, 255, 204, 179, 179, 204, 129, 121, 105, 127, 129, 139, 254, 250, 241, 164, 253, 255, 82, 183, 161, 163, 129, 120, 107, 124, 120, 124, 247, 254, 218, 175, 148, 69, 119, 67, 167, 164, 148, 131, 125, 120, 57, 73, 62, 67, 105, 63, 65, 90, 82, 57, 123, 131, 108, 102, 96, 64, 60, 67, 61, 67, 65, 88, 56, 57, 73, 66, 72, 96, 111, 100, 75, 75, 68, 69, 66, 62, 63], \"darkFraction\": 0, \"stdLuminance\": 64.30409392934628, \"analysisWidth\": 240, \"meanLuminance\": 159.073624770831, \"analysisHeight\": 320, \"brightFraction\": 0.20016927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 538.9295798455837}, \"selectionScore\": 102.0520596383938, \"frameDifference\": 0.011968954248366014}, {\"index\": 3, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 230, 216, 120, 110, 114, 106, 103, 107, 123, 229, 244, 220, 202, 255, 255, 236, 161, 232, 197, 178, 168, 163, 144, 120, 102, 107, 209, 224, 255, 255, 255, 195, 253, 215, 192, 180, 171, 167, 160, 154, 163, 170, 95, 255, 255, 255, 255, 168, 255, 181, 143, 164, 173, 165, 154, 100, 107, 125, 81, 255, 254, 255, 255, 160, 232, 182, 133, 139, 108, 103, 121, 104, 111, 150, 122, 242, 255, 255, 255, 255, 244, 186, 183, 180, 167, 150, 136, 141, 135, 148, 164, 235, 254, 236, 250, 255, 214, 181, 154, 177, 150, 137, 136, 127, 138, 144, 167, 252, 253, 165, 255, 255, 204, 182, 172, 197, 130, 116, 104, 123, 132, 139, 253, 253, 224, 184, 255, 255, 80, 178, 165, 165, 125, 120, 113, 123, 120, 122, 253, 254, 220, 173, 161, 70, 114, 65, 158, 166, 146, 126, 123, 118, 55, 72, 65, 69, 101, 68, 64, 87, 85, 58, 118, 130, 106, 101, 94, 65, 60, 67, 59, 67, 65, 81, 53, 57, 73, 65, 75, 96, 112, 101, 76, 75, 67, 69, 62, 60, 65], \"darkFraction\": 0, \"stdLuminance\": 64.37153551407151, \"analysisWidth\": 240, \"meanLuminance\": 158.97609537239083, \"analysisHeight\": 320, \"brightFraction\": 0.19998697916666663, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 534.3955895714618}, \"selectionScore\": 101.98357778884449, \"frameDifference\": 0.01497140522875817}, {\"index\": 4, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 216, 233, 121, 110, 111, 106, 101, 107, 118, 219, 244, 217, 205, 255, 255, 253, 187, 233, 199, 178, 168, 164, 143, 119, 101, 106, 210, 227, 255, 255, 255, 195, 253, 217, 190, 180, 170, 168, 159, 154, 162, 171, 94, 255, 255, 255, 255, 172, 255, 181, 149, 166, 173, 167, 156, 102, 105, 125, 78, 255, 253, 255, 255, 222, 242, 166, 143, 141, 107, 100, 120, 116, 119, 150, 104, 140, 255, 255, 255, 255, 247, 184, 181, 180, 157, 150, 137, 141, 135, 147, 120, 221, 254, 212, 255, 254, 218, 181, 153, 179, 152, 141, 138, 127, 137, 146, 164, 253, 253, 166, 254, 255, 205, 179, 176, 198, 128, 119, 104, 121, 131, 138, 255, 251, 235, 167, 254, 255, 80, 181, 165, 165, 130, 122, 110, 123, 120, 131, 252, 254, 208, 176, 142, 70, 117, 64, 161, 166, 146, 126, 122, 119, 56, 73, 67, 67, 100, 69, 65, 92, 84, 56, 118, 129, 105, 101, 95, 66, 60, 68, 59, 69, 62, 82, 53, 59, 76, 65, 74, 99, 113, 99, 75, 75, 66, 70, 63, 61, 64], \"darkFraction\": 0, \"stdLuminance\": 64.34327068857081, \"analysisWidth\": 240, \"meanLuminance\": 159.02655464843, \"analysisHeight\": 320, \"brightFraction\": 0.2002734375, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 548.633728154622}, \"selectionScore\": 102.0290233494044, \"frameDifference\": 0.01401143790849673}], \"valid\": true, \"reasons\": [], \"selectedIndices\": [0, 2, 4]}, \"confirmations\": {}, \"automaticPoints\": {}, \"calibrationSpec\": {\"method\": \"marker\", \"widthMm\": null, \"evidence\": {}, \"heightMm\": null, \"lengthMm\": null, \"referencePlane\": \"\"}, \"measurementContext\": {\"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"brand\": \"Kittycraft\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"pdReference\": \"frame_bridge\"}, \"workingDistanceCm\": 40}}','2026-11-10 02:30:36.876033'),('mc_64972513b7154f79acaace03c00ee6c9','mr_2df7aa062c6541369dc3ea6a9eed0771','ms_f590b06bc5d34192bee59f0371955abe','usr_c4b3d45ff0b94ffd','0be62fb0-52e0-4634-a7f7-5461b4625c2e','frontal','mp_3e506397bd034da497ccf9027a599fee','959ccf66b61f59d6f626f7b6a1645518cb7da1cc1b85dde9ecb2a003e817eed4',960,1280,'2026-11-10 02:56:45.220000','null','{}','{\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [218, 218, 222, 221, 222, 225, 224, 223, 227, 229, 231, 234, 236, 249, 254, 255, 233, 232, 231, 228, 227, 227, 233, 220, 232, 231, 241, 247, 253, 255, 255, 255, 243, 242, 239, 229, 234, 230, 234, 232, 240, 243, 247, 252, 255, 255, 255, 255, 253, 253, 250, 247, 242, 233, 229, 229, 239, 235, 245, 251, 255, 255, 255, 255, 255, 255, 254, 250, 245, 208, 111, 105, 112, 119, 135, 150, 180, 216, 255, 255, 255, 255, 255, 255, 252, 127, 169, 169, 168, 166, 171, 170, 156, 163, 251, 252, 255, 255, 255, 255, 134, 142, 135, 174, 171, 169, 172, 169, 178, 143, 235, 220, 215, 249, 248, 243, 156, 105, 89, 136, 162, 132, 122, 151, 145, 173, 253, 255, 253, 217, 235, 221, 156, 161, 155, 161, 157, 127, 153, 136, 146, 163, 244, 232, 255, 255, 244, 232, 166, 160, 152, 141, 135, 115, 147, 155, 144, 137, 255, 255, 255, 255, 254, 255, 170, 112, 131, 123, 123, 147, 93, 140, 131, 136, 137, 255, 255, 206, 249, 252, 158, 137, 136, 128, 120, 122, 131, 123, 116, 75, 79, 253], \"darkFraction\": 0, \"stdLuminance\": 52.17091597216591, \"analysisWidth\": 240, \"meanLuminance\": 201.18653949216025, \"analysisHeight\": 320, \"brightFraction\": 0.32571614583333336, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 405.0529290491211}','{\"id\": \"0be62fb0-52e0-4634-a7f7-5461b4625c2e\", \"view\": \"frontal\", \"width\": 960, \"device\": {\"zoom\": 1, \"depth\": null, \"width\": 960, \"height\": 1280, \"mirrored\": false, \"frameRate\": 30, \"facingMode\": \"user\", \"intrinsics\": null, \"cameraLabel\": \"camera 1, facing front\", \"orientation\": {\"beta\": 55.1, \"gamma\": -4.800000000000001}, \"sourceWidth\": 960, \"sourceHeight\": 1280, \"mainCameraVerifiedByOperator\": true}, \"height\": 1280, \"points\": {}, \"burstId\": \"83522744-f21b-45e9-b1d1-d3c7ea824c99\", \"photoId\": \"mp_3e506397bd034da497ccf9027a599fee\", \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [218, 218, 222, 221, 222, 225, 224, 223, 227, 229, 231, 234, 236, 249, 254, 255, 233, 232, 231, 228, 227, 227, 233, 220, 232, 231, 241, 247, 253, 255, 255, 255, 243, 242, 239, 229, 234, 230, 234, 232, 240, 243, 247, 252, 255, 255, 255, 255, 253, 253, 250, 247, 242, 233, 229, 229, 239, 235, 245, 251, 255, 255, 255, 255, 255, 255, 254, 250, 245, 208, 111, 105, 112, 119, 135, 150, 180, 216, 255, 255, 255, 255, 255, 255, 252, 127, 169, 169, 168, 166, 171, 170, 156, 163, 251, 252, 255, 255, 255, 255, 134, 142, 135, 174, 171, 169, 172, 169, 178, 143, 235, 220, 215, 249, 248, 243, 156, 105, 89, 136, 162, 132, 122, 151, 145, 173, 253, 255, 253, 217, 235, 221, 156, 161, 155, 161, 157, 127, 153, 136, 146, 163, 244, 232, 255, 255, 244, 232, 166, 160, 152, 141, 135, 115, 147, 155, 144, 137, 255, 255, 255, 255, 254, 255, 170, 112, 131, 123, 123, 147, 93, 140, 131, 136, 137, 255, 255, 206, 249, 252, 158, 137, 136, 128, 120, 122, 131, 123, 116, 75, 79, 253], \"darkFraction\": 0, \"stdLuminance\": 52.17091597216591, \"analysisWidth\": 240, \"meanLuminance\": 201.18653949216025, \"analysisHeight\": 320, \"brightFraction\": 0.32571614583333336, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 405.0529290491211}, \"createdAt\": \"2026-11-10T02:56:45.220Z\", \"photoHash\": \"959ccf66b61f59d6f626f7b6a1645518cb7da1cc1b85dde9ecb2a003e817eed4\", \"superseded\": false, \"sampleIndex\": 0, \"measurements\": {}, \"burstAnalysis\": {\"note\": \"Pemilihan berdasarkan detail, pencahayaan dan perubahan gambar. Ini bukan stabilitas landmark atau pengulangan nilai ukur.\", \"rows\": [{\"index\": 0, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [218, 218, 222, 221, 222, 225, 224, 223, 227, 229, 231, 234, 236, 249, 254, 255, 233, 232, 231, 228, 227, 227, 233, 220, 232, 231, 241, 247, 253, 255, 255, 255, 243, 242, 239, 229, 234, 230, 234, 232, 240, 243, 247, 252, 255, 255, 255, 255, 253, 253, 250, 247, 242, 233, 229, 229, 239, 235, 245, 251, 255, 255, 255, 255, 255, 255, 254, 250, 245, 208, 111, 105, 112, 119, 135, 150, 180, 216, 255, 255, 255, 255, 255, 255, 252, 127, 169, 169, 168, 166, 171, 170, 156, 163, 251, 252, 255, 255, 255, 255, 134, 142, 135, 174, 171, 169, 172, 169, 178, 143, 235, 220, 215, 249, 248, 243, 156, 105, 89, 136, 162, 132, 122, 151, 145, 173, 253, 255, 253, 217, 235, 221, 156, 161, 155, 161, 157, 127, 153, 136, 146, 163, 244, 232, 255, 255, 244, 232, 166, 160, 152, 141, 135, 115, 147, 155, 144, 137, 255, 255, 255, 255, 254, 255, 170, 112, 131, 123, 123, 147, 93, 140, 131, 136, 137, 255, 255, 206, 249, 252, 158, 137, 136, 128, 120, 122, 131, 123, 116, 75, 79, 253], \"darkFraction\": 0, \"stdLuminance\": 52.17091597216591, \"analysisWidth\": 240, \"meanLuminance\": 201.18653949216025, \"analysisHeight\": 320, \"brightFraction\": 0.32571614583333336, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 405.0529290491211}, \"selectionScore\": 99.00648351822072, \"frameDifference\": null}, {\"index\": 1, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [215, 219, 221, 220, 221, 225, 223, 222, 227, 228, 231, 233, 235, 248, 254, 253, 232, 231, 231, 229, 227, 228, 232, 211, 231, 228, 242, 246, 253, 255, 255, 255, 243, 242, 239, 226, 234, 230, 234, 235, 240, 243, 245, 252, 255, 255, 255, 255, 253, 252, 249, 247, 242, 233, 229, 229, 238, 241, 247, 249, 255, 255, 255, 255, 255, 255, 254, 250, 245, 205, 155, 109, 110, 114, 134, 151, 202, 250, 255, 255, 255, 255, 255, 255, 251, 118, 167, 169, 167, 165, 169, 170, 145, 165, 252, 252, 255, 255, 255, 255, 146, 148, 144, 174, 172, 170, 166, 164, 177, 140, 234, 209, 213, 251, 249, 245, 153, 130, 91, 141, 158, 138, 128, 148, 145, 178, 253, 255, 254, 235, 166, 202, 159, 161, 153, 163, 156, 129, 155, 144, 151, 165, 247, 229, 255, 255, 245, 217, 167, 163, 148, 140, 130, 118, 153, 152, 142, 139, 255, 255, 255, 255, 254, 255, 168, 115, 124, 125, 123, 146, 100, 140, 129, 157, 148, 255, 255, 234, 248, 253, 156, 136, 135, 131, 120, 122, 129, 123, 117, 77, 93, 253], \"darkFraction\": 0, \"stdLuminance\": 52.07825679479587, \"analysisWidth\": 240, \"meanLuminance\": 201.30632061455543, \"analysisHeight\": 320, \"brightFraction\": 0.32678385416666667, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 400.9612994349925}, \"selectionScore\": 98.74227084660228, \"frameDifference\": 0.012704248366013072}, {\"index\": 2, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [213, 219, 221, 220, 221, 226, 224, 223, 227, 227, 231, 232, 236, 244, 254, 254, 233, 230, 231, 227, 227, 229, 230, 214, 233, 223, 241, 245, 252, 255, 255, 255, 242, 241, 239, 232, 232, 231, 235, 239, 241, 242, 246, 251, 254, 255, 255, 255, 254, 251, 250, 247, 243, 233, 226, 231, 241, 241, 245, 246, 255, 255, 255, 255, 255, 255, 255, 252, 235, 203, 118, 100, 105, 115, 132, 194, 231, 243, 255, 255, 255, 255, 255, 255, 253, 123, 167, 169, 170, 167, 171, 168, 144, 180, 253, 252, 255, 255, 255, 255, 142, 148, 160, 174, 174, 168, 164, 166, 173, 139, 236, 230, 230, 252, 251, 248, 157, 113, 108, 139, 159, 139, 135, 150, 147, 179, 249, 255, 254, 234, 178, 218, 159, 161, 154, 162, 157, 125, 154, 142, 151, 164, 241, 255, 255, 255, 245, 232, 168, 163, 149, 142, 130, 124, 152, 153, 143, 136, 255, 255, 255, 255, 254, 255, 165, 114, 126, 125, 123, 145, 101, 137, 127, 133, 187, 255, 255, 233, 251, 253, 159, 137, 134, 128, 117, 121, 127, 122, 120, 139, 105, 253], \"darkFraction\": 0, \"stdLuminance\": 51.6588382484299, \"analysisWidth\": 240, \"meanLuminance\": 202.05864659373117, \"analysisHeight\": 320, \"brightFraction\": 0.3291927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 411.1410683173094}, \"selectionScore\": 98.75012385950748, \"frameDifference\": 0.013562091503267974}, {\"index\": 3, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [215, 218, 221, 221, 222, 225, 224, 223, 227, 228, 231, 233, 235, 246, 254, 254, 232, 231, 231, 227, 227, 229, 230, 222, 232, 227, 240, 245, 253, 255, 255, 255, 243, 241, 240, 235, 223, 231, 234, 238, 239, 242, 247, 251, 254, 255, 255, 255, 253, 252, 249, 247, 243, 233, 227, 231, 242, 240, 245, 247, 255, 255, 255, 255, 255, 255, 255, 251, 237, 207, 112, 102, 105, 115, 132, 189, 231, 233, 255, 255, 255, 255, 255, 255, 251, 128, 164, 169, 169, 166, 171, 169, 144, 182, 250, 252, 255, 255, 255, 255, 139, 152, 159, 176, 174, 168, 162, 166, 174, 138, 238, 230, 225, 252, 252, 248, 157, 112, 97, 139, 159, 139, 133, 149, 146, 181, 248, 255, 255, 235, 232, 222, 158, 161, 153, 163, 157, 127, 153, 142, 151, 164, 254, 255, 255, 255, 243, 233, 168, 163, 150, 142, 130, 120, 151, 151, 143, 137, 255, 255, 255, 255, 254, 255, 163, 114, 124, 121, 122, 147, 103, 138, 125, 136, 233, 255, 255, 234, 249, 253, 158, 138, 135, 129, 119, 121, 130, 123, 117, 95, 243, 254], \"darkFraction\": 0, \"stdLuminance\": 51.251034352293026, \"analysisWidth\": 240, \"meanLuminance\": 202.93030013019467, \"analysisHeight\": 320, \"brightFraction\": 0.33515625, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 409.49248364964814}, \"selectionScore\": 98.81392624594356, \"frameDifference\": 0.01017156862745098}, {\"index\": 4, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [210, 218, 219, 221, 222, 225, 225, 223, 226, 227, 232, 234, 235, 248, 254, 254, 232, 229, 229, 227, 227, 229, 230, 221, 232, 223, 240, 247, 253, 255, 255, 255, 243, 243, 240, 235, 224, 231, 234, 238, 239, 243, 246, 252, 255, 255, 255, 255, 253, 252, 250, 247, 243, 232, 227, 231, 241, 241, 246, 246, 255, 255, 255, 255, 255, 255, 255, 251, 227, 221, 126, 103, 104, 117, 133, 187, 231, 247, 255, 255, 255, 255, 255, 255, 252, 122, 167, 169, 164, 164, 169, 168, 141, 181, 254, 252, 255, 255, 255, 255, 129, 160, 163, 166, 172, 169, 166, 166, 168, 136, 237, 227, 208, 254, 253, 238, 164, 143, 118, 151, 148, 141, 139, 144, 146, 128, 249, 253, 255, 239, 206, 208, 160, 156, 155, 162, 147, 141, 150, 143, 150, 165, 255, 255, 255, 243, 241, 228, 164, 163, 139, 143, 117, 138, 156, 146, 141, 137, 255, 255, 255, 255, 254, 255, 167, 117, 129, 131, 127, 132, 121, 139, 130, 168, 255, 255, 255, 255, 248, 253, 168, 138, 133, 128, 122, 123, 130, 123, 119, 254, 254, 254], \"darkFraction\": 0, \"stdLuminance\": 51.017993500490995, \"analysisWidth\": 240, \"meanLuminance\": 203.98039984112785, \"analysisHeight\": 320, \"brightFraction\": 0.3467578125, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 404.1870074302451}, \"selectionScore\": 98.6563094915894, \"frameDifference\": 0.017401960784313726}], \"valid\": true, \"reasons\": [], \"selectedIndices\": [0, 3, 2]}, \"confirmations\": {}, \"automaticPoints\": {}, \"calibrationSpec\": {\"method\": \"marker\", \"widthMm\": null, \"evidence\": {}, \"heightMm\": null, \"lengthMm\": null, \"referencePlane\": \"\"}, \"measurementContext\": {\"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"brand\": \"Kittycraft\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"pdReference\": \"frame_bridge\"}, \"workingDistanceCm\": 40}}','2026-11-10 02:56:47.715139'),('mc_80deee86e51c458b8dff6189a4eecdc9','mr_71f19a7b82764acc8ecdc4e262aa73cb','ms_8c2a17db7e0c4b2b8a57029c89623953','usr_c4b3d45ff0b94ffd','f4d7dd7a-a548-4a17-b9f0-5af1f96ed53a','frontal','mp_f83fadbccf7241e4a397dd665b9f2476','c748819db81858c80c9a9f7417ed6a30c0d82290c1a3b48590d4156770fe7c79',960,1280,'2026-11-10 02:30:34.594000','null','{}','{\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 218, 226, 122, 110, 115, 105, 104, 106, 115, 245, 244, 217, 204, 255, 255, 246, 168, 228, 198, 179, 167, 166, 147, 123, 99, 106, 216, 225, 255, 255, 255, 199, 252, 219, 193, 178, 170, 167, 159, 153, 162, 170, 91, 255, 255, 255, 255, 163, 255, 168, 132, 160, 171, 165, 136, 97, 106, 118, 78, 255, 253, 255, 255, 178, 247, 186, 120, 137, 108, 135, 120, 104, 106, 149, 134, 253, 255, 255, 255, 255, 248, 186, 180, 179, 162, 154, 144, 140, 136, 146, 102, 229, 253, 213, 255, 254, 218, 181, 156, 175, 111, 135, 117, 125, 135, 144, 157, 252, 252, 165, 255, 255, 204, 179, 179, 204, 129, 121, 105, 127, 129, 139, 254, 250, 241, 164, 253, 255, 82, 183, 161, 163, 129, 120, 107, 124, 120, 124, 247, 254, 218, 175, 148, 69, 119, 67, 167, 164, 148, 131, 125, 120, 57, 73, 62, 67, 105, 63, 65, 90, 82, 57, 123, 131, 108, 102, 96, 64, 60, 67, 61, 67, 65, 88, 56, 57, 73, 66, 72, 96, 111, 100, 75, 75, 68, 69, 66, 62, 63], \"darkFraction\": 0, \"stdLuminance\": 64.30409392934628, \"analysisWidth\": 240, \"meanLuminance\": 159.073624770831, \"analysisHeight\": 320, \"brightFraction\": 0.20016927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 538.9295798455837}','{\"id\": \"f4d7dd7a-a548-4a17-b9f0-5af1f96ed53a\", \"view\": \"frontal\", \"width\": 960, \"device\": {\"zoom\": 1, \"depth\": null, \"width\": 960, \"height\": 1280, \"mirrored\": false, \"frameRate\": 30, \"facingMode\": \"user\", \"intrinsics\": null, \"cameraLabel\": \"camera 1, facing front\", \"orientation\": null, \"sourceWidth\": 960, \"sourceHeight\": 1280, \"mainCameraVerifiedByOperator\": true}, \"height\": 1280, \"points\": {}, \"burstId\": \"a1c9ce47-cf76-42b9-b39e-25d1a0a81412\", \"photoId\": \"mp_f83fadbccf7241e4a397dd665b9f2476\", \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 218, 226, 122, 110, 115, 105, 104, 106, 115, 245, 244, 217, 204, 255, 255, 246, 168, 228, 198, 179, 167, 166, 147, 123, 99, 106, 216, 225, 255, 255, 255, 199, 252, 219, 193, 178, 170, 167, 159, 153, 162, 170, 91, 255, 255, 255, 255, 163, 255, 168, 132, 160, 171, 165, 136, 97, 106, 118, 78, 255, 253, 255, 255, 178, 247, 186, 120, 137, 108, 135, 120, 104, 106, 149, 134, 253, 255, 255, 255, 255, 248, 186, 180, 179, 162, 154, 144, 140, 136, 146, 102, 229, 253, 213, 255, 254, 218, 181, 156, 175, 111, 135, 117, 125, 135, 144, 157, 252, 252, 165, 255, 255, 204, 179, 179, 204, 129, 121, 105, 127, 129, 139, 254, 250, 241, 164, 253, 255, 82, 183, 161, 163, 129, 120, 107, 124, 120, 124, 247, 254, 218, 175, 148, 69, 119, 67, 167, 164, 148, 131, 125, 120, 57, 73, 62, 67, 105, 63, 65, 90, 82, 57, 123, 131, 108, 102, 96, 64, 60, 67, 61, 67, 65, 88, 56, 57, 73, 66, 72, 96, 111, 100, 75, 75, 68, 69, 66, 62, 63], \"darkFraction\": 0, \"stdLuminance\": 64.30409392934628, \"analysisWidth\": 240, \"meanLuminance\": 159.073624770831, \"analysisHeight\": 320, \"brightFraction\": 0.20016927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 538.9295798455837}, \"createdAt\": \"2026-11-10T02:30:34.594Z\", \"photoHash\": \"c748819db81858c80c9a9f7417ed6a30c0d82290c1a3b48590d4156770fe7c79\", \"superseded\": false, \"sampleIndex\": 1, \"measurements\": {}, \"burstAnalysis\": {\"note\": \"Pemilihan berdasarkan detail, pencahayaan dan perubahan gambar. Ini bukan stabilitas landmark atau pengulangan nilai ukur.\", \"rows\": [{\"index\": 0, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 219, 223, 122, 109, 114, 107, 105, 104, 110, 153, 246, 216, 204, 255, 255, 234, 159, 227, 198, 177, 167, 163, 140, 114, 97, 99, 139, 225, 255, 255, 255, 188, 250, 224, 194, 180, 169, 165, 158, 150, 162, 170, 100, 254, 255, 255, 255, 174, 255, 214, 192, 177, 172, 167, 166, 155, 140, 135, 75, 254, 251, 255, 255, 253, 252, 190, 150, 141, 156, 137, 98, 130, 134, 156, 254, 247, 255, 255, 255, 255, 254, 188, 163, 174, 179, 142, 135, 132, 129, 144, 245, 219, 254, 234, 250, 253, 215, 166, 212, 182, 180, 159, 151, 119, 121, 143, 157, 254, 253, 169, 254, 255, 200, 173, 186, 191, 193, 128, 141, 112, 123, 135, 254, 234, 255, 163, 252, 255, 85, 183, 150, 171, 171, 133, 111, 121, 121, 125, 246, 255, 239, 180, 148, 70, 122, 64, 152, 166, 151, 132, 125, 119, 57, 70, 66, 65, 103, 68, 65, 92, 81, 58, 122, 130, 107, 96, 98, 64, 58, 66, 59, 66, 66, 94, 53, 57, 72, 65, 70, 96, 112, 99, 74, 72, 68, 70, 67, 63, 61], \"darkFraction\": 0, \"stdLuminance\": 64.01172832662922, \"analysisWidth\": 240, \"meanLuminance\": 157.68188170572682, \"analysisHeight\": 320, \"brightFraction\": 0.19272135416666664, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 554.1889526826051}, \"selectionScore\": 102.31930851108866, \"frameDifference\": null}, {\"index\": 1, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 213, 217, 122, 110, 114, 103, 104, 107, 114, 254, 245, 218, 207, 255, 255, 247, 159, 226, 198, 181, 167, 164, 149, 130, 98, 104, 189, 229, 255, 255, 255, 199, 251, 220, 195, 179, 172, 166, 160, 154, 160, 171, 93, 255, 255, 255, 255, 167, 255, 169, 136, 157, 169, 167, 140, 97, 104, 113, 74, 255, 251, 255, 255, 248, 252, 172, 123, 137, 105, 132, 119, 104, 115, 148, 130, 252, 255, 255, 255, 255, 250, 187, 178, 176, 161, 157, 126, 140, 136, 145, 128, 221, 254, 237, 248, 254, 218, 182, 156, 177, 110, 141, 115, 125, 132, 145, 158, 252, 253, 173, 253, 255, 203, 178, 188, 208, 129, 122, 103, 129, 130, 138, 254, 236, 253, 157, 250, 255, 81, 183, 158, 169, 139, 123, 101, 124, 122, 130, 238, 254, 204, 173, 152, 71, 125, 64, 167, 165, 154, 133, 124, 120, 57, 73, 64, 72, 104, 64, 67, 91, 79, 55, 121, 127, 110, 101, 96, 65, 60, 70, 60, 66, 66, 89, 55, 54, 75, 64, 71, 94, 110, 100, 76, 71, 71, 67, 66, 60, 59], \"darkFraction\": 0, \"stdLuminance\": 64.06198522944985, \"analysisWidth\": 240, \"meanLuminance\": 158.89106833593817, \"analysisHeight\": 320, \"brightFraction\": 0.1975390625, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 529.0478336837755}, \"selectionScore\": 101.5740293462105, \"frameDifference\": 0.0349468954248366}, {\"index\": 2, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 218, 226, 122, 110, 115, 105, 104, 106, 115, 245, 244, 217, 204, 255, 255, 246, 168, 228, 198, 179, 167, 166, 147, 123, 99, 106, 216, 225, 255, 255, 255, 199, 252, 219, 193, 178, 170, 167, 159, 153, 162, 170, 91, 255, 255, 255, 255, 163, 255, 168, 132, 160, 171, 165, 136, 97, 106, 118, 78, 255, 253, 255, 255, 178, 247, 186, 120, 137, 108, 135, 120, 104, 106, 149, 134, 253, 255, 255, 255, 255, 248, 186, 180, 179, 162, 154, 144, 140, 136, 146, 102, 229, 253, 213, 255, 254, 218, 181, 156, 175, 111, 135, 117, 125, 135, 144, 157, 252, 252, 165, 255, 255, 204, 179, 179, 204, 129, 121, 105, 127, 129, 139, 254, 250, 241, 164, 253, 255, 82, 183, 161, 163, 129, 120, 107, 124, 120, 124, 247, 254, 218, 175, 148, 69, 119, 67, 167, 164, 148, 131, 125, 120, 57, 73, 62, 67, 105, 63, 65, 90, 82, 57, 123, 131, 108, 102, 96, 64, 60, 67, 61, 67, 65, 88, 56, 57, 73, 66, 72, 96, 111, 100, 75, 75, 68, 69, 66, 62, 63], \"darkFraction\": 0, \"stdLuminance\": 64.30409392934628, \"analysisWidth\": 240, \"meanLuminance\": 159.073624770831, \"analysisHeight\": 320, \"brightFraction\": 0.20016927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 538.9295798455837}, \"selectionScore\": 102.0520596383938, \"frameDifference\": 0.011968954248366014}, {\"index\": 3, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 230, 216, 120, 110, 114, 106, 103, 107, 123, 229, 244, 220, 202, 255, 255, 236, 161, 232, 197, 178, 168, 163, 144, 120, 102, 107, 209, 224, 255, 255, 255, 195, 253, 215, 192, 180, 171, 167, 160, 154, 163, 170, 95, 255, 255, 255, 255, 168, 255, 181, 143, 164, 173, 165, 154, 100, 107, 125, 81, 255, 254, 255, 255, 160, 232, 182, 133, 139, 108, 103, 121, 104, 111, 150, 122, 242, 255, 255, 255, 255, 244, 186, 183, 180, 167, 150, 136, 141, 135, 148, 164, 235, 254, 236, 250, 255, 214, 181, 154, 177, 150, 137, 136, 127, 138, 144, 167, 252, 253, 165, 255, 255, 204, 182, 172, 197, 130, 116, 104, 123, 132, 139, 253, 253, 224, 184, 255, 255, 80, 178, 165, 165, 125, 120, 113, 123, 120, 122, 253, 254, 220, 173, 161, 70, 114, 65, 158, 166, 146, 126, 123, 118, 55, 72, 65, 69, 101, 68, 64, 87, 85, 58, 118, 130, 106, 101, 94, 65, 60, 67, 59, 67, 65, 81, 53, 57, 73, 65, 75, 96, 112, 101, 76, 75, 67, 69, 62, 60, 65], \"darkFraction\": 0, \"stdLuminance\": 64.37153551407151, \"analysisWidth\": 240, \"meanLuminance\": 158.97609537239083, \"analysisHeight\": 320, \"brightFraction\": 0.19998697916666663, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 534.3955895714618}, \"selectionScore\": 101.98357778884449, \"frameDifference\": 0.01497140522875817}, {\"index\": 4, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 216, 233, 121, 110, 111, 106, 101, 107, 118, 219, 244, 217, 205, 255, 255, 253, 187, 233, 199, 178, 168, 164, 143, 119, 101, 106, 210, 227, 255, 255, 255, 195, 253, 217, 190, 180, 170, 168, 159, 154, 162, 171, 94, 255, 255, 255, 255, 172, 255, 181, 149, 166, 173, 167, 156, 102, 105, 125, 78, 255, 253, 255, 255, 222, 242, 166, 143, 141, 107, 100, 120, 116, 119, 150, 104, 140, 255, 255, 255, 255, 247, 184, 181, 180, 157, 150, 137, 141, 135, 147, 120, 221, 254, 212, 255, 254, 218, 181, 153, 179, 152, 141, 138, 127, 137, 146, 164, 253, 253, 166, 254, 255, 205, 179, 176, 198, 128, 119, 104, 121, 131, 138, 255, 251, 235, 167, 254, 255, 80, 181, 165, 165, 130, 122, 110, 123, 120, 131, 252, 254, 208, 176, 142, 70, 117, 64, 161, 166, 146, 126, 122, 119, 56, 73, 67, 67, 100, 69, 65, 92, 84, 56, 118, 129, 105, 101, 95, 66, 60, 68, 59, 69, 62, 82, 53, 59, 76, 65, 74, 99, 113, 99, 75, 75, 66, 70, 63, 61, 64], \"darkFraction\": 0, \"stdLuminance\": 64.34327068857081, \"analysisWidth\": 240, \"meanLuminance\": 159.02655464843, \"analysisHeight\": 320, \"brightFraction\": 0.2002734375, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 548.633728154622}, \"selectionScore\": 102.0290233494044, \"frameDifference\": 0.01401143790849673}], \"valid\": true, \"reasons\": [], \"selectedIndices\": [0, 2, 4]}, \"confirmations\": {}, \"automaticPoints\": {}, \"calibrationSpec\": {\"method\": \"marker\", \"widthMm\": null, \"evidence\": {}, \"heightMm\": null, \"lengthMm\": null, \"referencePlane\": \"\"}, \"measurementContext\": {\"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"brand\": \"Kittycraft\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"pdReference\": \"frame_bridge\"}, \"workingDistanceCm\": 40}}','2026-11-10 02:30:36.876032'),('mc_c3ca283e2ebd4226b418299d4e3d4a79','mr_71f19a7b82764acc8ecdc4e262aa73cb','ms_8c2a17db7e0c4b2b8a57029c89623953','usr_c4b3d45ff0b94ffd','06fad378-1c6a-40bc-8099-6d34adc78350','frontal','mp_4c362829cebe4a9882a8c86f05bc0413','862f10231611ded242bd03689314d0c6e2661d86cc7d14e5006be029261a143c',960,1280,'2026-11-10 02:30:34.378000','null','{}','{\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 219, 223, 122, 109, 114, 107, 105, 104, 110, 153, 246, 216, 204, 255, 255, 234, 159, 227, 198, 177, 167, 163, 140, 114, 97, 99, 139, 225, 255, 255, 255, 188, 250, 224, 194, 180, 169, 165, 158, 150, 162, 170, 100, 254, 255, 255, 255, 174, 255, 214, 192, 177, 172, 167, 166, 155, 140, 135, 75, 254, 251, 255, 255, 253, 252, 190, 150, 141, 156, 137, 98, 130, 134, 156, 254, 247, 255, 255, 255, 255, 254, 188, 163, 174, 179, 142, 135, 132, 129, 144, 245, 219, 254, 234, 250, 253, 215, 166, 212, 182, 180, 159, 151, 119, 121, 143, 157, 254, 253, 169, 254, 255, 200, 173, 186, 191, 193, 128, 141, 112, 123, 135, 254, 234, 255, 163, 252, 255, 85, 183, 150, 171, 171, 133, 111, 121, 121, 125, 246, 255, 239, 180, 148, 70, 122, 64, 152, 166, 151, 132, 125, 119, 57, 70, 66, 65, 103, 68, 65, 92, 81, 58, 122, 130, 107, 96, 98, 64, 58, 66, 59, 66, 66, 94, 53, 57, 72, 65, 70, 96, 112, 99, 74, 72, 68, 70, 67, 63, 61], \"darkFraction\": 0, \"stdLuminance\": 64.01172832662922, \"analysisWidth\": 240, \"meanLuminance\": 157.68188170572682, \"analysisHeight\": 320, \"brightFraction\": 0.19272135416666664, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 554.1889526826051}','{\"id\": \"06fad378-1c6a-40bc-8099-6d34adc78350\", \"view\": \"frontal\", \"width\": 960, \"device\": {\"zoom\": 1, \"depth\": null, \"width\": 960, \"height\": 1280, \"mirrored\": false, \"frameRate\": 30, \"facingMode\": \"user\", \"intrinsics\": null, \"cameraLabel\": \"camera 1, facing front\", \"orientation\": null, \"sourceWidth\": 960, \"sourceHeight\": 1280, \"mainCameraVerifiedByOperator\": true}, \"height\": 1280, \"points\": {}, \"burstId\": \"a1c9ce47-cf76-42b9-b39e-25d1a0a81412\", \"photoId\": \"mp_4c362829cebe4a9882a8c86f05bc0413\", \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 219, 223, 122, 109, 114, 107, 105, 104, 110, 153, 246, 216, 204, 255, 255, 234, 159, 227, 198, 177, 167, 163, 140, 114, 97, 99, 139, 225, 255, 255, 255, 188, 250, 224, 194, 180, 169, 165, 158, 150, 162, 170, 100, 254, 255, 255, 255, 174, 255, 214, 192, 177, 172, 167, 166, 155, 140, 135, 75, 254, 251, 255, 255, 253, 252, 190, 150, 141, 156, 137, 98, 130, 134, 156, 254, 247, 255, 255, 255, 255, 254, 188, 163, 174, 179, 142, 135, 132, 129, 144, 245, 219, 254, 234, 250, 253, 215, 166, 212, 182, 180, 159, 151, 119, 121, 143, 157, 254, 253, 169, 254, 255, 200, 173, 186, 191, 193, 128, 141, 112, 123, 135, 254, 234, 255, 163, 252, 255, 85, 183, 150, 171, 171, 133, 111, 121, 121, 125, 246, 255, 239, 180, 148, 70, 122, 64, 152, 166, 151, 132, 125, 119, 57, 70, 66, 65, 103, 68, 65, 92, 81, 58, 122, 130, 107, 96, 98, 64, 58, 66, 59, 66, 66, 94, 53, 57, 72, 65, 70, 96, 112, 99, 74, 72, 68, 70, 67, 63, 61], \"darkFraction\": 0, \"stdLuminance\": 64.01172832662922, \"analysisWidth\": 240, \"meanLuminance\": 157.68188170572682, \"analysisHeight\": 320, \"brightFraction\": 0.19272135416666664, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 554.1889526826051}, \"createdAt\": \"2026-11-10T02:30:34.378Z\", \"photoHash\": \"862f10231611ded242bd03689314d0c6e2661d86cc7d14e5006be029261a143c\", \"superseded\": false, \"sampleIndex\": 0, \"measurements\": {}, \"burstAnalysis\": {\"note\": \"Pemilihan berdasarkan detail, pencahayaan dan perubahan gambar. Ini bukan stabilitas landmark atau pengulangan nilai ukur.\", \"rows\": [{\"index\": 0, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 219, 223, 122, 109, 114, 107, 105, 104, 110, 153, 246, 216, 204, 255, 255, 234, 159, 227, 198, 177, 167, 163, 140, 114, 97, 99, 139, 225, 255, 255, 255, 188, 250, 224, 194, 180, 169, 165, 158, 150, 162, 170, 100, 254, 255, 255, 255, 174, 255, 214, 192, 177, 172, 167, 166, 155, 140, 135, 75, 254, 251, 255, 255, 253, 252, 190, 150, 141, 156, 137, 98, 130, 134, 156, 254, 247, 255, 255, 255, 255, 254, 188, 163, 174, 179, 142, 135, 132, 129, 144, 245, 219, 254, 234, 250, 253, 215, 166, 212, 182, 180, 159, 151, 119, 121, 143, 157, 254, 253, 169, 254, 255, 200, 173, 186, 191, 193, 128, 141, 112, 123, 135, 254, 234, 255, 163, 252, 255, 85, 183, 150, 171, 171, 133, 111, 121, 121, 125, 246, 255, 239, 180, 148, 70, 122, 64, 152, 166, 151, 132, 125, 119, 57, 70, 66, 65, 103, 68, 65, 92, 81, 58, 122, 130, 107, 96, 98, 64, 58, 66, 59, 66, 66, 94, 53, 57, 72, 65, 70, 96, 112, 99, 74, 72, 68, 70, 67, 63, 61], \"darkFraction\": 0, \"stdLuminance\": 64.01172832662922, \"analysisWidth\": 240, \"meanLuminance\": 157.68188170572682, \"analysisHeight\": 320, \"brightFraction\": 0.19272135416666664, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 554.1889526826051}, \"selectionScore\": 102.31930851108866, \"frameDifference\": null}, {\"index\": 1, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 213, 217, 122, 110, 114, 103, 104, 107, 114, 254, 245, 218, 207, 255, 255, 247, 159, 226, 198, 181, 167, 164, 149, 130, 98, 104, 189, 229, 255, 255, 255, 199, 251, 220, 195, 179, 172, 166, 160, 154, 160, 171, 93, 255, 255, 255, 255, 167, 255, 169, 136, 157, 169, 167, 140, 97, 104, 113, 74, 255, 251, 255, 255, 248, 252, 172, 123, 137, 105, 132, 119, 104, 115, 148, 130, 252, 255, 255, 255, 255, 250, 187, 178, 176, 161, 157, 126, 140, 136, 145, 128, 221, 254, 237, 248, 254, 218, 182, 156, 177, 110, 141, 115, 125, 132, 145, 158, 252, 253, 173, 253, 255, 203, 178, 188, 208, 129, 122, 103, 129, 130, 138, 254, 236, 253, 157, 250, 255, 81, 183, 158, 169, 139, 123, 101, 124, 122, 130, 238, 254, 204, 173, 152, 71, 125, 64, 167, 165, 154, 133, 124, 120, 57, 73, 64, 72, 104, 64, 67, 91, 79, 55, 121, 127, 110, 101, 96, 65, 60, 70, 60, 66, 66, 89, 55, 54, 75, 64, 71, 94, 110, 100, 76, 71, 71, 67, 66, 60, 59], \"darkFraction\": 0, \"stdLuminance\": 64.06198522944985, \"analysisWidth\": 240, \"meanLuminance\": 158.89106833593817, \"analysisHeight\": 320, \"brightFraction\": 0.1975390625, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 529.0478336837755}, \"selectionScore\": 101.5740293462105, \"frameDifference\": 0.0349468954248366}, {\"index\": 2, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 218, 226, 122, 110, 115, 105, 104, 106, 115, 245, 244, 217, 204, 255, 255, 246, 168, 228, 198, 179, 167, 166, 147, 123, 99, 106, 216, 225, 255, 255, 255, 199, 252, 219, 193, 178, 170, 167, 159, 153, 162, 170, 91, 255, 255, 255, 255, 163, 255, 168, 132, 160, 171, 165, 136, 97, 106, 118, 78, 255, 253, 255, 255, 178, 247, 186, 120, 137, 108, 135, 120, 104, 106, 149, 134, 253, 255, 255, 255, 255, 248, 186, 180, 179, 162, 154, 144, 140, 136, 146, 102, 229, 253, 213, 255, 254, 218, 181, 156, 175, 111, 135, 117, 125, 135, 144, 157, 252, 252, 165, 255, 255, 204, 179, 179, 204, 129, 121, 105, 127, 129, 139, 254, 250, 241, 164, 253, 255, 82, 183, 161, 163, 129, 120, 107, 124, 120, 124, 247, 254, 218, 175, 148, 69, 119, 67, 167, 164, 148, 131, 125, 120, 57, 73, 62, 67, 105, 63, 65, 90, 82, 57, 123, 131, 108, 102, 96, 64, 60, 67, 61, 67, 65, 88, 56, 57, 73, 66, 72, 96, 111, 100, 75, 75, 68, 69, 66, 62, 63], \"darkFraction\": 0, \"stdLuminance\": 64.30409392934628, \"analysisWidth\": 240, \"meanLuminance\": 159.073624770831, \"analysisHeight\": 320, \"brightFraction\": 0.20016927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 538.9295798455837}, \"selectionScore\": 102.0520596383938, \"frameDifference\": 0.011968954248366014}, {\"index\": 3, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 230, 216, 120, 110, 114, 106, 103, 107, 123, 229, 244, 220, 202, 255, 255, 236, 161, 232, 197, 178, 168, 163, 144, 120, 102, 107, 209, 224, 255, 255, 255, 195, 253, 215, 192, 180, 171, 167, 160, 154, 163, 170, 95, 255, 255, 255, 255, 168, 255, 181, 143, 164, 173, 165, 154, 100, 107, 125, 81, 255, 254, 255, 255, 160, 232, 182, 133, 139, 108, 103, 121, 104, 111, 150, 122, 242, 255, 255, 255, 255, 244, 186, 183, 180, 167, 150, 136, 141, 135, 148, 164, 235, 254, 236, 250, 255, 214, 181, 154, 177, 150, 137, 136, 127, 138, 144, 167, 252, 253, 165, 255, 255, 204, 182, 172, 197, 130, 116, 104, 123, 132, 139, 253, 253, 224, 184, 255, 255, 80, 178, 165, 165, 125, 120, 113, 123, 120, 122, 253, 254, 220, 173, 161, 70, 114, 65, 158, 166, 146, 126, 123, 118, 55, 72, 65, 69, 101, 68, 64, 87, 85, 58, 118, 130, 106, 101, 94, 65, 60, 67, 59, 67, 65, 81, 53, 57, 73, 65, 75, 96, 112, 101, 76, 75, 67, 69, 62, 60, 65], \"darkFraction\": 0, \"stdLuminance\": 64.37153551407151, \"analysisWidth\": 240, \"meanLuminance\": 158.97609537239083, \"analysisHeight\": 320, \"brightFraction\": 0.19998697916666663, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 534.3955895714618}, \"selectionScore\": 101.98357778884449, \"frameDifference\": 0.01497140522875817}, {\"index\": 4, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 216, 233, 121, 110, 111, 106, 101, 107, 118, 219, 244, 217, 205, 255, 255, 253, 187, 233, 199, 178, 168, 164, 143, 119, 101, 106, 210, 227, 255, 255, 255, 195, 253, 217, 190, 180, 170, 168, 159, 154, 162, 171, 94, 255, 255, 255, 255, 172, 255, 181, 149, 166, 173, 167, 156, 102, 105, 125, 78, 255, 253, 255, 255, 222, 242, 166, 143, 141, 107, 100, 120, 116, 119, 150, 104, 140, 255, 255, 255, 255, 247, 184, 181, 180, 157, 150, 137, 141, 135, 147, 120, 221, 254, 212, 255, 254, 218, 181, 153, 179, 152, 141, 138, 127, 137, 146, 164, 253, 253, 166, 254, 255, 205, 179, 176, 198, 128, 119, 104, 121, 131, 138, 255, 251, 235, 167, 254, 255, 80, 181, 165, 165, 130, 122, 110, 123, 120, 131, 252, 254, 208, 176, 142, 70, 117, 64, 161, 166, 146, 126, 122, 119, 56, 73, 67, 67, 100, 69, 65, 92, 84, 56, 118, 129, 105, 101, 95, 66, 60, 68, 59, 69, 62, 82, 53, 59, 76, 65, 74, 99, 113, 99, 75, 75, 66, 70, 63, 61, 64], \"darkFraction\": 0, \"stdLuminance\": 64.34327068857081, \"analysisWidth\": 240, \"meanLuminance\": 159.02655464843, \"analysisHeight\": 320, \"brightFraction\": 0.2002734375, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 548.633728154622}, \"selectionScore\": 102.0290233494044, \"frameDifference\": 0.01401143790849673}], \"valid\": true, \"reasons\": [], \"selectedIndices\": [0, 2, 4]}, \"confirmations\": {}, \"automaticPoints\": {}, \"calibrationSpec\": {\"method\": \"marker\", \"widthMm\": null, \"evidence\": {}, \"heightMm\": null, \"lengthMm\": null, \"referencePlane\": \"\"}, \"measurementContext\": {\"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"brand\": \"Kittycraft\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"pdReference\": \"frame_bridge\"}, \"workingDistanceCm\": 40}}','2026-11-10 02:30:36.876029'),('mc_eca5a5a1fa4f4ea1b7a631c48a5b2c56','mr_2df7aa062c6541369dc3ea6a9eed0771','ms_f590b06bc5d34192bee59f0371955abe','usr_c4b3d45ff0b94ffd','1106f58f-67c0-49e0-98e5-53a5442593ca','frontal','mp_0caa65dba9494776837d81d5b9d50b4e','468ae7c122c2a20906dc7f8881061cdd2534dd95225bb1b88b43626a34f34049',960,1280,'2026-11-10 02:56:45.412000','null','{}','{\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [215, 218, 221, 221, 222, 225, 224, 223, 227, 228, 231, 233, 235, 246, 254, 254, 232, 231, 231, 227, 227, 229, 230, 222, 232, 227, 240, 245, 253, 255, 255, 255, 243, 241, 240, 235, 223, 231, 234, 238, 239, 242, 247, 251, 254, 255, 255, 255, 253, 252, 249, 247, 243, 233, 227, 231, 242, 240, 245, 247, 255, 255, 255, 255, 255, 255, 255, 251, 237, 207, 112, 102, 105, 115, 132, 189, 231, 233, 255, 255, 255, 255, 255, 255, 251, 128, 164, 169, 169, 166, 171, 169, 144, 182, 250, 252, 255, 255, 255, 255, 139, 152, 159, 176, 174, 168, 162, 166, 174, 138, 238, 230, 225, 252, 252, 248, 157, 112, 97, 139, 159, 139, 133, 149, 146, 181, 248, 255, 255, 235, 232, 222, 158, 161, 153, 163, 157, 127, 153, 142, 151, 164, 254, 255, 255, 255, 243, 233, 168, 163, 150, 142, 130, 120, 151, 151, 143, 137, 255, 255, 255, 255, 254, 255, 163, 114, 124, 121, 122, 147, 103, 138, 125, 136, 233, 255, 255, 234, 249, 253, 158, 138, 135, 129, 119, 121, 130, 123, 117, 95, 243, 254], \"darkFraction\": 0, \"stdLuminance\": 51.251034352293026, \"analysisWidth\": 240, \"meanLuminance\": 202.93030013019467, \"analysisHeight\": 320, \"brightFraction\": 0.33515625, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 409.49248364964814}','{\"id\": \"1106f58f-67c0-49e0-98e5-53a5442593ca\", \"view\": \"frontal\", \"width\": 960, \"device\": {\"zoom\": 1, \"depth\": null, \"width\": 960, \"height\": 1280, \"mirrored\": false, \"frameRate\": 30, \"facingMode\": \"user\", \"intrinsics\": null, \"cameraLabel\": \"camera 1, facing front\", \"orientation\": {\"beta\": 55.1, \"gamma\": -4.800000000000001}, \"sourceWidth\": 960, \"sourceHeight\": 1280, \"mainCameraVerifiedByOperator\": true}, \"height\": 1280, \"points\": {}, \"burstId\": \"83522744-f21b-45e9-b1d1-d3c7ea824c99\", \"photoId\": \"mp_0caa65dba9494776837d81d5b9d50b4e\", \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [215, 218, 221, 221, 222, 225, 224, 223, 227, 228, 231, 233, 235, 246, 254, 254, 232, 231, 231, 227, 227, 229, 230, 222, 232, 227, 240, 245, 253, 255, 255, 255, 243, 241, 240, 235, 223, 231, 234, 238, 239, 242, 247, 251, 254, 255, 255, 255, 253, 252, 249, 247, 243, 233, 227, 231, 242, 240, 245, 247, 255, 255, 255, 255, 255, 255, 255, 251, 237, 207, 112, 102, 105, 115, 132, 189, 231, 233, 255, 255, 255, 255, 255, 255, 251, 128, 164, 169, 169, 166, 171, 169, 144, 182, 250, 252, 255, 255, 255, 255, 139, 152, 159, 176, 174, 168, 162, 166, 174, 138, 238, 230, 225, 252, 252, 248, 157, 112, 97, 139, 159, 139, 133, 149, 146, 181, 248, 255, 255, 235, 232, 222, 158, 161, 153, 163, 157, 127, 153, 142, 151, 164, 254, 255, 255, 255, 243, 233, 168, 163, 150, 142, 130, 120, 151, 151, 143, 137, 255, 255, 255, 255, 254, 255, 163, 114, 124, 121, 122, 147, 103, 138, 125, 136, 233, 255, 255, 234, 249, 253, 158, 138, 135, 129, 119, 121, 130, 123, 117, 95, 243, 254], \"darkFraction\": 0, \"stdLuminance\": 51.251034352293026, \"analysisWidth\": 240, \"meanLuminance\": 202.93030013019467, \"analysisHeight\": 320, \"brightFraction\": 0.33515625, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 409.49248364964814}, \"createdAt\": \"2026-11-10T02:56:45.412Z\", \"photoHash\": \"468ae7c122c2a20906dc7f8881061cdd2534dd95225bb1b88b43626a34f34049\", \"superseded\": false, \"sampleIndex\": 1, \"measurements\": {}, \"burstAnalysis\": {\"note\": \"Pemilihan berdasarkan detail, pencahayaan dan perubahan gambar. Ini bukan stabilitas landmark atau pengulangan nilai ukur.\", \"rows\": [{\"index\": 0, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [218, 218, 222, 221, 222, 225, 224, 223, 227, 229, 231, 234, 236, 249, 254, 255, 233, 232, 231, 228, 227, 227, 233, 220, 232, 231, 241, 247, 253, 255, 255, 255, 243, 242, 239, 229, 234, 230, 234, 232, 240, 243, 247, 252, 255, 255, 255, 255, 253, 253, 250, 247, 242, 233, 229, 229, 239, 235, 245, 251, 255, 255, 255, 255, 255, 255, 254, 250, 245, 208, 111, 105, 112, 119, 135, 150, 180, 216, 255, 255, 255, 255, 255, 255, 252, 127, 169, 169, 168, 166, 171, 170, 156, 163, 251, 252, 255, 255, 255, 255, 134, 142, 135, 174, 171, 169, 172, 169, 178, 143, 235, 220, 215, 249, 248, 243, 156, 105, 89, 136, 162, 132, 122, 151, 145, 173, 253, 255, 253, 217, 235, 221, 156, 161, 155, 161, 157, 127, 153, 136, 146, 163, 244, 232, 255, 255, 244, 232, 166, 160, 152, 141, 135, 115, 147, 155, 144, 137, 255, 255, 255, 255, 254, 255, 170, 112, 131, 123, 123, 147, 93, 140, 131, 136, 137, 255, 255, 206, 249, 252, 158, 137, 136, 128, 120, 122, 131, 123, 116, 75, 79, 253], \"darkFraction\": 0, \"stdLuminance\": 52.17091597216591, \"analysisWidth\": 240, \"meanLuminance\": 201.18653949216025, \"analysisHeight\": 320, \"brightFraction\": 0.32571614583333336, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 405.0529290491211}, \"selectionScore\": 99.00648351822072, \"frameDifference\": null}, {\"index\": 1, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [215, 219, 221, 220, 221, 225, 223, 222, 227, 228, 231, 233, 235, 248, 254, 253, 232, 231, 231, 229, 227, 228, 232, 211, 231, 228, 242, 246, 253, 255, 255, 255, 243, 242, 239, 226, 234, 230, 234, 235, 240, 243, 245, 252, 255, 255, 255, 255, 253, 252, 249, 247, 242, 233, 229, 229, 238, 241, 247, 249, 255, 255, 255, 255, 255, 255, 254, 250, 245, 205, 155, 109, 110, 114, 134, 151, 202, 250, 255, 255, 255, 255, 255, 255, 251, 118, 167, 169, 167, 165, 169, 170, 145, 165, 252, 252, 255, 255, 255, 255, 146, 148, 144, 174, 172, 170, 166, 164, 177, 140, 234, 209, 213, 251, 249, 245, 153, 130, 91, 141, 158, 138, 128, 148, 145, 178, 253, 255, 254, 235, 166, 202, 159, 161, 153, 163, 156, 129, 155, 144, 151, 165, 247, 229, 255, 255, 245, 217, 167, 163, 148, 140, 130, 118, 153, 152, 142, 139, 255, 255, 255, 255, 254, 255, 168, 115, 124, 125, 123, 146, 100, 140, 129, 157, 148, 255, 255, 234, 248, 253, 156, 136, 135, 131, 120, 122, 129, 123, 117, 77, 93, 253], \"darkFraction\": 0, \"stdLuminance\": 52.07825679479587, \"analysisWidth\": 240, \"meanLuminance\": 201.30632061455543, \"analysisHeight\": 320, \"brightFraction\": 0.32678385416666667, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 400.9612994349925}, \"selectionScore\": 98.74227084660228, \"frameDifference\": 0.012704248366013072}, {\"index\": 2, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [213, 219, 221, 220, 221, 226, 224, 223, 227, 227, 231, 232, 236, 244, 254, 254, 233, 230, 231, 227, 227, 229, 230, 214, 233, 223, 241, 245, 252, 255, 255, 255, 242, 241, 239, 232, 232, 231, 235, 239, 241, 242, 246, 251, 254, 255, 255, 255, 254, 251, 250, 247, 243, 233, 226, 231, 241, 241, 245, 246, 255, 255, 255, 255, 255, 255, 255, 252, 235, 203, 118, 100, 105, 115, 132, 194, 231, 243, 255, 255, 255, 255, 255, 255, 253, 123, 167, 169, 170, 167, 171, 168, 144, 180, 253, 252, 255, 255, 255, 255, 142, 148, 160, 174, 174, 168, 164, 166, 173, 139, 236, 230, 230, 252, 251, 248, 157, 113, 108, 139, 159, 139, 135, 150, 147, 179, 249, 255, 254, 234, 178, 218, 159, 161, 154, 162, 157, 125, 154, 142, 151, 164, 241, 255, 255, 255, 245, 232, 168, 163, 149, 142, 130, 124, 152, 153, 143, 136, 255, 255, 255, 255, 254, 255, 165, 114, 126, 125, 123, 145, 101, 137, 127, 133, 187, 255, 255, 233, 251, 253, 159, 137, 134, 128, 117, 121, 127, 122, 120, 139, 105, 253], \"darkFraction\": 0, \"stdLuminance\": 51.6588382484299, \"analysisWidth\": 240, \"meanLuminance\": 202.05864659373117, \"analysisHeight\": 320, \"brightFraction\": 0.3291927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 411.1410683173094}, \"selectionScore\": 98.75012385950748, \"frameDifference\": 0.013562091503267974}, {\"index\": 3, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [215, 218, 221, 221, 222, 225, 224, 223, 227, 228, 231, 233, 235, 246, 254, 254, 232, 231, 231, 227, 227, 229, 230, 222, 232, 227, 240, 245, 253, 255, 255, 255, 243, 241, 240, 235, 223, 231, 234, 238, 239, 242, 247, 251, 254, 255, 255, 255, 253, 252, 249, 247, 243, 233, 227, 231, 242, 240, 245, 247, 255, 255, 255, 255, 255, 255, 255, 251, 237, 207, 112, 102, 105, 115, 132, 189, 231, 233, 255, 255, 255, 255, 255, 255, 251, 128, 164, 169, 169, 166, 171, 169, 144, 182, 250, 252, 255, 255, 255, 255, 139, 152, 159, 176, 174, 168, 162, 166, 174, 138, 238, 230, 225, 252, 252, 248, 157, 112, 97, 139, 159, 139, 133, 149, 146, 181, 248, 255, 255, 235, 232, 222, 158, 161, 153, 163, 157, 127, 153, 142, 151, 164, 254, 255, 255, 255, 243, 233, 168, 163, 150, 142, 130, 120, 151, 151, 143, 137, 255, 255, 255, 255, 254, 255, 163, 114, 124, 121, 122, 147, 103, 138, 125, 136, 233, 255, 255, 234, 249, 253, 158, 138, 135, 129, 119, 121, 130, 123, 117, 95, 243, 254], \"darkFraction\": 0, \"stdLuminance\": 51.251034352293026, \"analysisWidth\": 240, \"meanLuminance\": 202.93030013019467, \"analysisHeight\": 320, \"brightFraction\": 0.33515625, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 409.49248364964814}, \"selectionScore\": 98.81392624594356, \"frameDifference\": 0.01017156862745098}, {\"index\": 4, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [210, 218, 219, 221, 222, 225, 225, 223, 226, 227, 232, 234, 235, 248, 254, 254, 232, 229, 229, 227, 227, 229, 230, 221, 232, 223, 240, 247, 253, 255, 255, 255, 243, 243, 240, 235, 224, 231, 234, 238, 239, 243, 246, 252, 255, 255, 255, 255, 253, 252, 250, 247, 243, 232, 227, 231, 241, 241, 246, 246, 255, 255, 255, 255, 255, 255, 255, 251, 227, 221, 126, 103, 104, 117, 133, 187, 231, 247, 255, 255, 255, 255, 255, 255, 252, 122, 167, 169, 164, 164, 169, 168, 141, 181, 254, 252, 255, 255, 255, 255, 129, 160, 163, 166, 172, 169, 166, 166, 168, 136, 237, 227, 208, 254, 253, 238, 164, 143, 118, 151, 148, 141, 139, 144, 146, 128, 249, 253, 255, 239, 206, 208, 160, 156, 155, 162, 147, 141, 150, 143, 150, 165, 255, 255, 255, 243, 241, 228, 164, 163, 139, 143, 117, 138, 156, 146, 141, 137, 255, 255, 255, 255, 254, 255, 167, 117, 129, 131, 127, 132, 121, 139, 130, 168, 255, 255, 255, 255, 248, 253, 168, 138, 133, 128, 122, 123, 130, 123, 119, 254, 254, 254], \"darkFraction\": 0, \"stdLuminance\": 51.017993500490995, \"analysisWidth\": 240, \"meanLuminance\": 203.98039984112785, \"analysisHeight\": 320, \"brightFraction\": 0.3467578125, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 404.1870074302451}, \"selectionScore\": 98.6563094915894, \"frameDifference\": 0.017401960784313726}], \"valid\": true, \"reasons\": [], \"selectedIndices\": [0, 3, 2]}, \"confirmations\": {}, \"automaticPoints\": {}, \"calibrationSpec\": {\"method\": \"marker\", \"widthMm\": null, \"evidence\": {}, \"heightMm\": null, \"lengthMm\": null, \"referencePlane\": \"\"}, \"measurementContext\": {\"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"brand\": \"Kittycraft\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"pdReference\": \"frame_bridge\"}, \"workingDistanceCm\": 40}}','2026-11-10 02:56:47.715143'),('mc_ee54cea7a6c3447cb2b87916a46c13e8','mr_2df7aa062c6541369dc3ea6a9eed0771','ms_f590b06bc5d34192bee59f0371955abe','usr_c4b3d45ff0b94ffd','7041a10a-e8d7-4cfa-9bd5-48c8aba8afe8','frontal','mp_084dd33987c24014bebdc753dff3420a','59d256b2f5c9270a4d4950536c467875c04535735d04c7d43a3fd5319b08e63f',960,1280,'2026-11-10 02:56:45.603000','null','{}','{\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [213, 219, 221, 220, 221, 226, 224, 223, 227, 227, 231, 232, 236, 244, 254, 254, 233, 230, 231, 227, 227, 229, 230, 214, 233, 223, 241, 245, 252, 255, 255, 255, 242, 241, 239, 232, 232, 231, 235, 239, 241, 242, 246, 251, 254, 255, 255, 255, 254, 251, 250, 247, 243, 233, 226, 231, 241, 241, 245, 246, 255, 255, 255, 255, 255, 255, 255, 252, 235, 203, 118, 100, 105, 115, 132, 194, 231, 243, 255, 255, 255, 255, 255, 255, 253, 123, 167, 169, 170, 167, 171, 168, 144, 180, 253, 252, 255, 255, 255, 255, 142, 148, 160, 174, 174, 168, 164, 166, 173, 139, 236, 230, 230, 252, 251, 248, 157, 113, 108, 139, 159, 139, 135, 150, 147, 179, 249, 255, 254, 234, 178, 218, 159, 161, 154, 162, 157, 125, 154, 142, 151, 164, 241, 255, 255, 255, 245, 232, 168, 163, 149, 142, 130, 124, 152, 153, 143, 136, 255, 255, 255, 255, 254, 255, 165, 114, 126, 125, 123, 145, 101, 137, 127, 133, 187, 255, 255, 233, 251, 253, 159, 137, 134, 128, 117, 121, 127, 122, 120, 139, 105, 253], \"darkFraction\": 0, \"stdLuminance\": 51.6588382484299, \"analysisWidth\": 240, \"meanLuminance\": 202.05864659373117, \"analysisHeight\": 320, \"brightFraction\": 0.3291927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 411.1410683173094}','{\"id\": \"7041a10a-e8d7-4cfa-9bd5-48c8aba8afe8\", \"view\": \"frontal\", \"width\": 960, \"device\": {\"zoom\": 1, \"depth\": null, \"width\": 960, \"height\": 1280, \"mirrored\": false, \"frameRate\": 30, \"facingMode\": \"user\", \"intrinsics\": null, \"cameraLabel\": \"camera 1, facing front\", \"orientation\": {\"beta\": 55.1, \"gamma\": -4.800000000000001}, \"sourceWidth\": 960, \"sourceHeight\": 1280, \"mainCameraVerifiedByOperator\": true}, \"height\": 1280, \"points\": {}, \"burstId\": \"83522744-f21b-45e9-b1d1-d3c7ea824c99\", \"photoId\": \"mp_084dd33987c24014bebdc753dff3420a\", \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [213, 219, 221, 220, 221, 226, 224, 223, 227, 227, 231, 232, 236, 244, 254, 254, 233, 230, 231, 227, 227, 229, 230, 214, 233, 223, 241, 245, 252, 255, 255, 255, 242, 241, 239, 232, 232, 231, 235, 239, 241, 242, 246, 251, 254, 255, 255, 255, 254, 251, 250, 247, 243, 233, 226, 231, 241, 241, 245, 246, 255, 255, 255, 255, 255, 255, 255, 252, 235, 203, 118, 100, 105, 115, 132, 194, 231, 243, 255, 255, 255, 255, 255, 255, 253, 123, 167, 169, 170, 167, 171, 168, 144, 180, 253, 252, 255, 255, 255, 255, 142, 148, 160, 174, 174, 168, 164, 166, 173, 139, 236, 230, 230, 252, 251, 248, 157, 113, 108, 139, 159, 139, 135, 150, 147, 179, 249, 255, 254, 234, 178, 218, 159, 161, 154, 162, 157, 125, 154, 142, 151, 164, 241, 255, 255, 255, 245, 232, 168, 163, 149, 142, 130, 124, 152, 153, 143, 136, 255, 255, 255, 255, 254, 255, 165, 114, 126, 125, 123, 145, 101, 137, 127, 133, 187, 255, 255, 233, 251, 253, 159, 137, 134, 128, 117, 121, 127, 122, 120, 139, 105, 253], \"darkFraction\": 0, \"stdLuminance\": 51.6588382484299, \"analysisWidth\": 240, \"meanLuminance\": 202.05864659373117, \"analysisHeight\": 320, \"brightFraction\": 0.3291927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 411.1410683173094}, \"createdAt\": \"2026-11-10T02:56:45.603Z\", \"photoHash\": \"59d256b2f5c9270a4d4950536c467875c04535735d04c7d43a3fd5319b08e63f\", \"superseded\": false, \"sampleIndex\": 2, \"measurements\": {}, \"burstAnalysis\": {\"note\": \"Pemilihan berdasarkan detail, pencahayaan dan perubahan gambar. Ini bukan stabilitas landmark atau pengulangan nilai ukur.\", \"rows\": [{\"index\": 0, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [218, 218, 222, 221, 222, 225, 224, 223, 227, 229, 231, 234, 236, 249, 254, 255, 233, 232, 231, 228, 227, 227, 233, 220, 232, 231, 241, 247, 253, 255, 255, 255, 243, 242, 239, 229, 234, 230, 234, 232, 240, 243, 247, 252, 255, 255, 255, 255, 253, 253, 250, 247, 242, 233, 229, 229, 239, 235, 245, 251, 255, 255, 255, 255, 255, 255, 254, 250, 245, 208, 111, 105, 112, 119, 135, 150, 180, 216, 255, 255, 255, 255, 255, 255, 252, 127, 169, 169, 168, 166, 171, 170, 156, 163, 251, 252, 255, 255, 255, 255, 134, 142, 135, 174, 171, 169, 172, 169, 178, 143, 235, 220, 215, 249, 248, 243, 156, 105, 89, 136, 162, 132, 122, 151, 145, 173, 253, 255, 253, 217, 235, 221, 156, 161, 155, 161, 157, 127, 153, 136, 146, 163, 244, 232, 255, 255, 244, 232, 166, 160, 152, 141, 135, 115, 147, 155, 144, 137, 255, 255, 255, 255, 254, 255, 170, 112, 131, 123, 123, 147, 93, 140, 131, 136, 137, 255, 255, 206, 249, 252, 158, 137, 136, 128, 120, 122, 131, 123, 116, 75, 79, 253], \"darkFraction\": 0, \"stdLuminance\": 52.17091597216591, \"analysisWidth\": 240, \"meanLuminance\": 201.18653949216025, \"analysisHeight\": 320, \"brightFraction\": 0.32571614583333336, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 405.0529290491211}, \"selectionScore\": 99.00648351822072, \"frameDifference\": null}, {\"index\": 1, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [215, 219, 221, 220, 221, 225, 223, 222, 227, 228, 231, 233, 235, 248, 254, 253, 232, 231, 231, 229, 227, 228, 232, 211, 231, 228, 242, 246, 253, 255, 255, 255, 243, 242, 239, 226, 234, 230, 234, 235, 240, 243, 245, 252, 255, 255, 255, 255, 253, 252, 249, 247, 242, 233, 229, 229, 238, 241, 247, 249, 255, 255, 255, 255, 255, 255, 254, 250, 245, 205, 155, 109, 110, 114, 134, 151, 202, 250, 255, 255, 255, 255, 255, 255, 251, 118, 167, 169, 167, 165, 169, 170, 145, 165, 252, 252, 255, 255, 255, 255, 146, 148, 144, 174, 172, 170, 166, 164, 177, 140, 234, 209, 213, 251, 249, 245, 153, 130, 91, 141, 158, 138, 128, 148, 145, 178, 253, 255, 254, 235, 166, 202, 159, 161, 153, 163, 156, 129, 155, 144, 151, 165, 247, 229, 255, 255, 245, 217, 167, 163, 148, 140, 130, 118, 153, 152, 142, 139, 255, 255, 255, 255, 254, 255, 168, 115, 124, 125, 123, 146, 100, 140, 129, 157, 148, 255, 255, 234, 248, 253, 156, 136, 135, 131, 120, 122, 129, 123, 117, 77, 93, 253], \"darkFraction\": 0, \"stdLuminance\": 52.07825679479587, \"analysisWidth\": 240, \"meanLuminance\": 201.30632061455543, \"analysisHeight\": 320, \"brightFraction\": 0.32678385416666667, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 400.9612994349925}, \"selectionScore\": 98.74227084660228, \"frameDifference\": 0.012704248366013072}, {\"index\": 2, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [213, 219, 221, 220, 221, 226, 224, 223, 227, 227, 231, 232, 236, 244, 254, 254, 233, 230, 231, 227, 227, 229, 230, 214, 233, 223, 241, 245, 252, 255, 255, 255, 242, 241, 239, 232, 232, 231, 235, 239, 241, 242, 246, 251, 254, 255, 255, 255, 254, 251, 250, 247, 243, 233, 226, 231, 241, 241, 245, 246, 255, 255, 255, 255, 255, 255, 255, 252, 235, 203, 118, 100, 105, 115, 132, 194, 231, 243, 255, 255, 255, 255, 255, 255, 253, 123, 167, 169, 170, 167, 171, 168, 144, 180, 253, 252, 255, 255, 255, 255, 142, 148, 160, 174, 174, 168, 164, 166, 173, 139, 236, 230, 230, 252, 251, 248, 157, 113, 108, 139, 159, 139, 135, 150, 147, 179, 249, 255, 254, 234, 178, 218, 159, 161, 154, 162, 157, 125, 154, 142, 151, 164, 241, 255, 255, 255, 245, 232, 168, 163, 149, 142, 130, 124, 152, 153, 143, 136, 255, 255, 255, 255, 254, 255, 165, 114, 126, 125, 123, 145, 101, 137, 127, 133, 187, 255, 255, 233, 251, 253, 159, 137, 134, 128, 117, 121, 127, 122, 120, 139, 105, 253], \"darkFraction\": 0, \"stdLuminance\": 51.6588382484299, \"analysisWidth\": 240, \"meanLuminance\": 202.05864659373117, \"analysisHeight\": 320, \"brightFraction\": 0.3291927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 411.1410683173094}, \"selectionScore\": 98.75012385950748, \"frameDifference\": 0.013562091503267974}, {\"index\": 3, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [215, 218, 221, 221, 222, 225, 224, 223, 227, 228, 231, 233, 235, 246, 254, 254, 232, 231, 231, 227, 227, 229, 230, 222, 232, 227, 240, 245, 253, 255, 255, 255, 243, 241, 240, 235, 223, 231, 234, 238, 239, 242, 247, 251, 254, 255, 255, 255, 253, 252, 249, 247, 243, 233, 227, 231, 242, 240, 245, 247, 255, 255, 255, 255, 255, 255, 255, 251, 237, 207, 112, 102, 105, 115, 132, 189, 231, 233, 255, 255, 255, 255, 255, 255, 251, 128, 164, 169, 169, 166, 171, 169, 144, 182, 250, 252, 255, 255, 255, 255, 139, 152, 159, 176, 174, 168, 162, 166, 174, 138, 238, 230, 225, 252, 252, 248, 157, 112, 97, 139, 159, 139, 133, 149, 146, 181, 248, 255, 255, 235, 232, 222, 158, 161, 153, 163, 157, 127, 153, 142, 151, 164, 254, 255, 255, 255, 243, 233, 168, 163, 150, 142, 130, 120, 151, 151, 143, 137, 255, 255, 255, 255, 254, 255, 163, 114, 124, 121, 122, 147, 103, 138, 125, 136, 233, 255, 255, 234, 249, 253, 158, 138, 135, 129, 119, 121, 130, 123, 117, 95, 243, 254], \"darkFraction\": 0, \"stdLuminance\": 51.251034352293026, \"analysisWidth\": 240, \"meanLuminance\": 202.93030013019467, \"analysisHeight\": 320, \"brightFraction\": 0.33515625, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 409.49248364964814}, \"selectionScore\": 98.81392624594356, \"frameDifference\": 0.01017156862745098}, {\"index\": 4, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [210, 218, 219, 221, 222, 225, 225, 223, 226, 227, 232, 234, 235, 248, 254, 254, 232, 229, 229, 227, 227, 229, 230, 221, 232, 223, 240, 247, 253, 255, 255, 255, 243, 243, 240, 235, 224, 231, 234, 238, 239, 243, 246, 252, 255, 255, 255, 255, 253, 252, 250, 247, 243, 232, 227, 231, 241, 241, 246, 246, 255, 255, 255, 255, 255, 255, 255, 251, 227, 221, 126, 103, 104, 117, 133, 187, 231, 247, 255, 255, 255, 255, 255, 255, 252, 122, 167, 169, 164, 164, 169, 168, 141, 181, 254, 252, 255, 255, 255, 255, 129, 160, 163, 166, 172, 169, 166, 166, 168, 136, 237, 227, 208, 254, 253, 238, 164, 143, 118, 151, 148, 141, 139, 144, 146, 128, 249, 253, 255, 239, 206, 208, 160, 156, 155, 162, 147, 141, 150, 143, 150, 165, 255, 255, 255, 243, 241, 228, 164, 163, 139, 143, 117, 138, 156, 146, 141, 137, 255, 255, 255, 255, 254, 255, 167, 117, 129, 131, 127, 132, 121, 139, 130, 168, 255, 255, 255, 255, 248, 253, 168, 138, 133, 128, 122, 123, 130, 123, 119, 254, 254, 254], \"darkFraction\": 0, \"stdLuminance\": 51.017993500490995, \"analysisWidth\": 240, \"meanLuminance\": 203.98039984112785, \"analysisHeight\": 320, \"brightFraction\": 0.3467578125, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 404.1870074302451}, \"selectionScore\": 98.6563094915894, \"frameDifference\": 0.017401960784313726}], \"valid\": true, \"reasons\": [], \"selectedIndices\": [0, 3, 2]}, \"confirmations\": {}, \"automaticPoints\": {}, \"calibrationSpec\": {\"method\": \"marker\", \"widthMm\": null, \"evidence\": {}, \"heightMm\": null, \"lengthMm\": null, \"referencePlane\": \"\"}, \"measurementContext\": {\"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"brand\": \"Kittycraft\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"pdReference\": \"frame_bridge\"}, \"workingDistanceCm\": 40}}','2026-11-10 02:56:47.715144');
/*!40000 ALTER TABLE `meowsurement_captures` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_captures_bi` BEFORE INSERT ON `meowsurement_captures`
FOR EACH ROW
BEGIN
  IF (NEW.`width` > 0 AND NEW.`height` > 0 AND NEW.`width` * NEW.`height` <= 20000000) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_captures_dimensions failed'; END IF;
  IF (NEW.`view` IN ('frontal','frontal_near','three_quarter_left','three_quarter_right','lateral_left','lateral_right')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_captures_view failed'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_captures_bu` BEFORE UPDATE ON `meowsurement_captures`
FOR EACH ROW
BEGIN
  IF (NEW.`width` > 0 AND NEW.`height` > 0 AND NEW.`width` * NEW.`height` <= 20000000) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_captures_dimensions failed'; END IF;
  IF (NEW.`view` IN ('frontal','frontal_near','three_quarter_left','three_quarter_right','lateral_left','lateral_right')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_captures_view failed'; END IF;
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_captures_bd` BEFORE DELETE ON `meowsurement_captures`
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `meowsurement_measurement_sources`
--

DROP TABLE IF EXISTS `meowsurement_measurement_sources`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `meowsurement_measurement_sources` (
  `measurement_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `capture_row_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `revision_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`measurement_id`,`capture_row_id`),
  KEY `fk_meowsurement_measurement_sources_revision_i_22aced642967` (`revision_id`,`measurement_id`),
  KEY `fk_meowsurement_measurement_sources_revision_i_8050f78eb3c8` (`revision_id`,`capture_row_id`),
  CONSTRAINT `fk_meowsurement_measurement_sources_revision_i_22aced642967` FOREIGN KEY (`revision_id`, `measurement_id`) REFERENCES `meowsurement_measurements` (`revision_id`, `id`),
  CONSTRAINT `fk_meowsurement_measurement_sources_revision_i_8050f78eb3c8` FOREIGN KEY (`revision_id`, `capture_row_id`) REFERENCES `meowsurement_captures` (`revision_id`, `id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `meowsurement_measurement_sources`
--

LOCK TABLES `meowsurement_measurement_sources` WRITE;
/*!40000 ALTER TABLE `meowsurement_measurement_sources` DISABLE KEYS */;
/*!40000 ALTER TABLE `meowsurement_measurement_sources` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_measurement_sources_bu` BEFORE UPDATE ON `meowsurement_measurement_sources`
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_measurement_sources_bd` BEFORE DELETE ON `meowsurement_measurement_sources`
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `meowsurement_measurements`
--

DROP TABLE IF EXISTS `meowsurement_measurements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `meowsurement_measurements` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `revision_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `session_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `parameter` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `side` varchar(8) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `unit` varchar(8) COLLATE utf8mb4_unicode_ci NOT NULL,
  `method` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `algorithm_version` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `valid` tinyint(1) NOT NULL,
  `values` json NOT NULL,
  `quality` json DEFAULT NULL,
  `data` json NOT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_meowsurement_measurements_revision_id_parameter` (`revision_id`,`parameter`),
  UNIQUE KEY `uq_meowsurement_measurements_revision_id_id` (`revision_id`,`id`),
  KEY `fk_meowsurement_measurements_revision_id_sessi_fc78e521e3a2` (`revision_id`,`session_id`,`user_id`),
  CONSTRAINT `fk_meowsurement_measurements_revision_id_sessi_fc78e521e3a2` FOREIGN KEY (`revision_id`, `session_id`, `user_id`) REFERENCES `meowsurement_revisions` (`id`, `session_id`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `meowsurement_measurements`
--

LOCK TABLES `meowsurement_measurements` WRITE;
/*!40000 ALTER TABLE `meowsurement_measurements` DISABLE KEYS */;
/*!40000 ALTER TABLE `meowsurement_measurements` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_measurements_bi` BEFORE INSERT ON `meowsurement_measurements`
FOR EACH ROW
BEGIN
  IF (NEW.`parameter` IN ('distance_pd','near_pd','vertex_right','vertex_left','pantoscopic_right','pantoscopic_left','wrap_right','wrap_left')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_measurements_parameter failed'; END IF;
  IF (NEW.`side` IS NULL OR NEW.`side` IN ('right','left','both')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_measurements_side failed'; END IF;
  IF (NEW.`unit` IN ('mm','deg') AND NEW.`valid` IN (0,1)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_measurements_unit_valid failed'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_measurements_bu` BEFORE UPDATE ON `meowsurement_measurements`
FOR EACH ROW
BEGIN
  IF (NEW.`parameter` IN ('distance_pd','near_pd','vertex_right','vertex_left','pantoscopic_right','pantoscopic_left','wrap_right','wrap_left')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_measurements_parameter failed'; END IF;
  IF (NEW.`side` IS NULL OR NEW.`side` IN ('right','left','both')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_measurements_side failed'; END IF;
  IF (NEW.`unit` IN ('mm','deg') AND NEW.`valid` IN (0,1)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_measurements_unit_valid failed'; END IF;
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_measurements_bd` BEFORE DELETE ON `meowsurement_measurements`
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `meowsurement_photos`
--

DROP TABLE IF EXISTS `meowsurement_photos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `meowsurement_photos` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `session_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `storage_path` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sha256` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `source_sha256` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `mime_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `width` int(11) NOT NULL,
  `height` int(11) NOT NULL,
  `byte_size` int(11) NOT NULL,
  `consent` tinyint(1) NOT NULL,
  `expires_at` datetime(6) NOT NULL,
  `deleted_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_meowsurement_photos_session_id_user_id_id` (`session_id`,`user_id`,`id`),
  KEY `ix_meowsurement_photo_retention` (`deleted_at`,`expires_at`),
  CONSTRAINT `fk_meowsurement_photos_session_id_user_id_meow_ff3248b1d22e` FOREIGN KEY (`session_id`, `user_id`) REFERENCES `meowsurement_sessions` (`id`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `meowsurement_photos`
--

LOCK TABLES `meowsurement_photos` WRITE;
/*!40000 ALTER TABLE `meowsurement_photos` DISABLE KEYS */;
INSERT INTO `meowsurement_photos` VALUES ('mp_084dd33987c24014bebdc753dff3420a','ms_f590b06bc5d34192bee59f0371955abe','usr_c4b3d45ff0b94ffd','mp_084dd33987c24014bebdc753dff3420a.jpg','c6f412aea785a88fa9d10b71b0208e2561b1a11bf75f9004c7aba70e029e7166','59d256b2f5c9270a4d4950536c467875c04535735d04c7d43a3fd5319b08e63f','image/jpeg',960,1280,207131,1,'2026-12-10 02:56:47.591059',NULL,'2026-11-10 02:56:47.591425'),('mp_0caa65dba9494776837d81d5b9d50b4e','ms_f590b06bc5d34192bee59f0371955abe','usr_c4b3d45ff0b94ffd','mp_0caa65dba9494776837d81d5b9d50b4e.jpg','af0a87018c1b1efad89c73eefae9e411e214da502ef7afe45b0ac185a9aa4431','468ae7c122c2a20906dc7f8881061cdd2534dd95225bb1b88b43626a34f34049','image/jpeg',960,1280,206766,1,'2026-12-10 02:56:47.394024',NULL,'2026-11-10 02:56:47.394406'),('mp_3e506397bd034da497ccf9027a599fee','ms_f590b06bc5d34192bee59f0371955abe','usr_c4b3d45ff0b94ffd','mp_3e506397bd034da497ccf9027a599fee.jpg','076841ad4b980cea92bbe61f27f99f6a4b08a946d5064a075effc1c4bd20595a','959ccf66b61f59d6f626f7b6a1645518cb7da1cc1b85dde9ecb2a003e817eed4','image/jpeg',960,1280,209584,1,'2026-12-10 02:56:47.237822',NULL,'2026-11-10 02:56:47.238309'),('mp_4c362829cebe4a9882a8c86f05bc0413','ms_8c2a17db7e0c4b2b8a57029c89623953','usr_c4b3d45ff0b94ffd','mp_4c362829cebe4a9882a8c86f05bc0413.jpg','6492ac4c35b787d11093f0ad56d54a959a4b516f9ad5934e7a33a1cf0ba931bc','862f10231611ded242bd03689314d0c6e2661d86cc7d14e5006be029261a143c','image/jpeg',960,1280,257984,1,'2026-12-10 02:30:36.390711',NULL,'2026-11-10 02:30:36.391906'),('mp_9db577367ca04a9fa2d5aa6e9fc182fd','ms_8c2a17db7e0c4b2b8a57029c89623953','usr_c4b3d45ff0b94ffd','mp_9db577367ca04a9fa2d5aa6e9fc182fd.jpg','aa640236f4af3562867d0f1156072129224df9cf85527d38d9b6b0bcf2f74d3a','aedf009c4618cc4c16889d924d1e02b2ba8cf798ed7721f56202c224508e6d4f','image/jpeg',960,1280,252549,1,'2026-12-10 02:30:36.749829',NULL,'2026-11-10 02:30:36.750347'),('mp_f83fadbccf7241e4a397dd665b9f2476','ms_8c2a17db7e0c4b2b8a57029c89623953','usr_c4b3d45ff0b94ffd','mp_f83fadbccf7241e4a397dd665b9f2476.jpg','a28431eb5cd7c999d3523a5214cf479240ca52c4fd7c2196ac2f7b3666cfe240','c748819db81858c80c9a9f7417ed6a30c0d82290c1a3b48590d4156770fe7c79','image/jpeg',960,1280,258016,1,'2026-12-10 02:30:36.562028',NULL,'2026-11-10 02:30:36.562415');
/*!40000 ALTER TABLE `meowsurement_photos` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_photos_bi` BEFORE INSERT ON `meowsurement_photos`
FOR EACH ROW
BEGIN
  IF (NEW.`consent` = 1) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_photos_consent failed'; END IF;
  IF (NEW.`width` > 0 AND NEW.`height` > 0 AND NEW.`width` * NEW.`height` <= 20000000) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_photos_dimensions failed'; END IF;
  IF (NEW.`mime_type` IN ('image/jpeg','image/png','image/webp')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_photos_mime failed'; END IF;
  IF (NEW.`byte_size` > 0 AND NEW.`byte_size` <= 8388608) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_photos_size failed'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_photos_bu` BEFORE UPDATE ON `meowsurement_photos`
FOR EACH ROW
BEGIN
  IF (NEW.`consent` = 1) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_photos_consent failed'; END IF;
  IF (NEW.`width` > 0 AND NEW.`height` > 0 AND NEW.`width` * NEW.`height` <= 20000000) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_photos_dimensions failed'; END IF;
  IF (NEW.`mime_type` IN ('image/jpeg','image/png','image/webp')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_photos_mime failed'; END IF;
  IF (NEW.`byte_size` > 0 AND NEW.`byte_size` <= 8388608) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_photos_size failed'; END IF;
  IF NOT (NEW.`id` <=> OLD.`id`) OR NOT (NEW.`user_id` <=> OLD.`user_id`) OR NOT (NEW.`session_id` <=> OLD.`session_id`) OR NOT (NEW.`storage_path` <=> OLD.`storage_path`) OR NOT (NEW.`sha256` <=> OLD.`sha256`) OR NOT (NEW.`source_sha256` <=> OLD.`source_sha256`) OR NOT (NEW.`mime_type` <=> OLD.`mime_type`) OR NOT (NEW.`width` <=> OLD.`width`) OR NOT (NEW.`height` <=> OLD.`height`) OR NOT (NEW.`byte_size` <=> OLD.`byte_size`) OR NOT (NEW.`consent` <=> OLD.`consent`) OR NOT (NEW.`created_at` <=> OLD.`created_at`) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Private photo provenance is immutable'; END IF;
  IF OLD.deleted_at IS NOT NULL AND NEW.deleted_at IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A deleted private photo cannot be reactivated'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `meowsurement_reviews`
--

DROP TABLE IF EXISTS `meowsurement_reviews`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `meowsurement_reviews` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `session_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `revision_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `reviewer_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `decision` varchar(24) COLLATE utf8mb4_unicode_ci NOT NULL,
  `note` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `evidence` json NOT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `fk_meowsurement_reviews_revision_id_session_id_3821c201c3bb` (`revision_id`,`session_id`,`user_id`),
  KEY `fk_meowsurement_reviews_reviewer_id_users_user_id` (`reviewer_id`),
  KEY `ix_meowsurement_reviews_session` (`session_id`,`created_at`),
  CONSTRAINT `fk_meowsurement_reviews_reviewer_id_users_user_id` FOREIGN KEY (`reviewer_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `fk_meowsurement_reviews_revision_id_session_id_3821c201c3bb` FOREIGN KEY (`revision_id`, `session_id`, `user_id`) REFERENCES `meowsurement_revisions` (`id`, `session_id`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `meowsurement_reviews`
--

LOCK TABLES `meowsurement_reviews` WRITE;
/*!40000 ALTER TABLE `meowsurement_reviews` DISABLE KEYS */;
/*!40000 ALTER TABLE `meowsurement_reviews` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_reviews_bi` BEFORE INSERT ON `meowsurement_reviews`
FOR EACH ROW
BEGIN
  IF (NEW.`decision` IN ('approved','needs_verification','needs_remeasure')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_reviews_decision failed'; END IF;
  IF (NEW.`reviewer_id` <> NEW.`user_id`) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_reviews_independent failed'; END IF;
  IF NOT EXISTS (SELECT 1 FROM users u WHERE u.user_id = NEW.reviewer_id AND u.is_active = 1 AND (u.role IN ('admin','super_admin') OR (u.role = 'staff' AND EXISTS (SELECT 1 FROM user_permissions p WHERE p.user_id = u.user_id AND p.permission = 'meowsurement.review')))) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'An active authorized web reviewer is required'; END IF;
  IF NOT EXISTS (SELECT 1 FROM meowsurement_sessions s JOIN meowsurement_revisions r ON r.id = s.current_revision_id AND r.session_id = s.id AND r.user_id = s.user_id WHERE s.id = NEW.session_id AND s.user_id = NEW.user_id AND r.id = NEW.revision_id AND s.status IN ('pending_review','needs_verification') AND r.actor_id <> NEW.reviewer_id AND s.user_id <> NEW.reviewer_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Review requires the current independent revision'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_reviews_bu` BEFORE UPDATE ON `meowsurement_reviews`
FOR EACH ROW
BEGIN
  IF (NEW.`decision` IN ('approved','needs_verification','needs_remeasure')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_reviews_decision failed'; END IF;
  IF (NEW.`reviewer_id` <> NEW.`user_id`) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_reviews_independent failed'; END IF;
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_reviews_bd` BEFORE DELETE ON `meowsurement_reviews`
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `meowsurement_revisions`
--

DROP TABLE IF EXISTS `meowsurement_revisions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `meowsurement_revisions` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `session_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `revision_number` int(11) NOT NULL,
  `parent_revision_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `data` json NOT NULL,
  `reason` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `actor_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `algorithm_version` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_meowsurement_revisions_session_id_user_id_id` (`session_id`,`user_id`,`id`),
  UNIQUE KEY `uq_meowsurement_revisions_session_id_revision_number` (`session_id`,`revision_number`),
  UNIQUE KEY `uq_meowsurement_revisions_id_session_id_user_id` (`id`,`session_id`,`user_id`),
  KEY `fk_meowsurement_revisions_session_id_user_id_p_7c6c199459bd` (`session_id`,`user_id`,`parent_revision_id`),
  KEY `ix_meowsurement_revision_actor` (`actor_id`,`created_at`),
  CONSTRAINT `fk_meowsurement_revisions_actor_id_users_user_id` FOREIGN KEY (`actor_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `fk_meowsurement_revisions_session_id_user_id_m_38fd2ad9d211` FOREIGN KEY (`session_id`, `user_id`) REFERENCES `meowsurement_sessions` (`id`, `user_id`),
  CONSTRAINT `fk_meowsurement_revisions_session_id_user_id_p_7c6c199459bd` FOREIGN KEY (`session_id`, `user_id`, `parent_revision_id`) REFERENCES `meowsurement_revisions` (`session_id`, `user_id`, `id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `meowsurement_revisions`
--

LOCK TABLES `meowsurement_revisions` WRITE;
/*!40000 ALTER TABLE `meowsurement_revisions` DISABLE KEYS */;
INSERT INTO `meowsurement_revisions` VALUES ('mr_29190347df2a4429ba3ac8a1c80f8393','ms_f590b06bc5d34192bee59f0371955abe','usr_c4b3d45ff0b94ffd',2,'mr_d25fd2e55e644c618d7b561075d2ec5f','{\"mode\": \"semi_automatic\", \"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"sku\": \"KC-CBY-AN-YLW\", \"size\": \"XS\", \"brand\": \"Kittycraft\", \"color\": \"Kuning\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"variantId\": \"var_efda2ee981f14664\", \"sourceNote\": \"\", \"pdReference\": \"frame_bridge\", \"sourceScope\": \"product\", \"templeLength\": null, \"sourceVersion\": 1}, \"notes\": \"\", \"results\": {}, \"captures\": [], \"consents\": {\"capture\": true, \"thumbnail\": true, \"confirmedAt\": \"2026-11-10T02:55:04.604Z\", \"retainPhotos\": true, \"uploadPhotos\": true}, \"deviceModel\": \"\", \"preparation\": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], \"prescription\": {\"id\": \"rx_8a7793124f314342\", \"od\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"os\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"date\": \"2026-11-09\", \"notes\": \"\", \"source\": \"professional_prescription\", \"pd_left\": null, \"pd_right\": null, \"pd_total\": null}, \"examinationDate\": \"2026-11-10\", \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"workingDistanceCm\": 40, \"manualMeasurements\": {}, \"requiredParameters\": [\"distance_pd\"]}','Persiapan pengukuran dan pilihan persetujuan pasien dicatat.','usr_c4b3d45ff0b94ffd','optifit-local-geometry-1.0.0','2026-11-10 02:55:06.725428'),('mr_2df7aa062c6541369dc3ea6a9eed0771','ms_f590b06bc5d34192bee59f0371955abe','usr_c4b3d45ff0b94ffd',3,'mr_29190347df2a4429ba3ac8a1c80f8393','{\"mode\": \"semi_automatic\", \"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"sku\": \"KC-CBY-AN-YLW\", \"size\": \"XS\", \"brand\": \"Kittycraft\", \"color\": \"Kuning\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"variantId\": \"var_efda2ee981f14664\", \"sourceNote\": \"\", \"pdReference\": \"frame_bridge\", \"sourceScope\": \"product\", \"templeLength\": null, \"sourceVersion\": 1}, \"notes\": \"\", \"results\": {}, \"captures\": [{\"id\": \"0be62fb0-52e0-4634-a7f7-5461b4625c2e\", \"view\": \"frontal\", \"width\": 960, \"device\": {\"zoom\": 1, \"depth\": null, \"width\": 960, \"height\": 1280, \"mirrored\": false, \"frameRate\": 30, \"facingMode\": \"user\", \"intrinsics\": null, \"cameraLabel\": \"camera 1, facing front\", \"orientation\": {\"beta\": 55.1, \"gamma\": -4.800000000000001}, \"sourceWidth\": 960, \"sourceHeight\": 1280, \"mainCameraVerifiedByOperator\": true}, \"height\": 1280, \"points\": {}, \"burstId\": \"83522744-f21b-45e9-b1d1-d3c7ea824c99\", \"photoId\": \"mp_3e506397bd034da497ccf9027a599fee\", \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [218, 218, 222, 221, 222, 225, 224, 223, 227, 229, 231, 234, 236, 249, 254, 255, 233, 232, 231, 228, 227, 227, 233, 220, 232, 231, 241, 247, 253, 255, 255, 255, 243, 242, 239, 229, 234, 230, 234, 232, 240, 243, 247, 252, 255, 255, 255, 255, 253, 253, 250, 247, 242, 233, 229, 229, 239, 235, 245, 251, 255, 255, 255, 255, 255, 255, 254, 250, 245, 208, 111, 105, 112, 119, 135, 150, 180, 216, 255, 255, 255, 255, 255, 255, 252, 127, 169, 169, 168, 166, 171, 170, 156, 163, 251, 252, 255, 255, 255, 255, 134, 142, 135, 174, 171, 169, 172, 169, 178, 143, 235, 220, 215, 249, 248, 243, 156, 105, 89, 136, 162, 132, 122, 151, 145, 173, 253, 255, 253, 217, 235, 221, 156, 161, 155, 161, 157, 127, 153, 136, 146, 163, 244, 232, 255, 255, 244, 232, 166, 160, 152, 141, 135, 115, 147, 155, 144, 137, 255, 255, 255, 255, 254, 255, 170, 112, 131, 123, 123, 147, 93, 140, 131, 136, 137, 255, 255, 206, 249, 252, 158, 137, 136, 128, 120, 122, 131, 123, 116, 75, 79, 253], \"darkFraction\": 0, \"stdLuminance\": 52.17091597216591, \"analysisWidth\": 240, \"meanLuminance\": 201.18653949216025, \"analysisHeight\": 320, \"brightFraction\": 0.32571614583333336, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 405.0529290491211}, \"createdAt\": \"2026-11-10T02:56:45.220Z\", \"photoHash\": \"959ccf66b61f59d6f626f7b6a1645518cb7da1cc1b85dde9ecb2a003e817eed4\", \"superseded\": false, \"sampleIndex\": 0, \"measurements\": {}, \"burstAnalysis\": {\"note\": \"Pemilihan berdasarkan detail, pencahayaan dan perubahan gambar. Ini bukan stabilitas landmark atau pengulangan nilai ukur.\", \"rows\": [{\"index\": 0, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [218, 218, 222, 221, 222, 225, 224, 223, 227, 229, 231, 234, 236, 249, 254, 255, 233, 232, 231, 228, 227, 227, 233, 220, 232, 231, 241, 247, 253, 255, 255, 255, 243, 242, 239, 229, 234, 230, 234, 232, 240, 243, 247, 252, 255, 255, 255, 255, 253, 253, 250, 247, 242, 233, 229, 229, 239, 235, 245, 251, 255, 255, 255, 255, 255, 255, 254, 250, 245, 208, 111, 105, 112, 119, 135, 150, 180, 216, 255, 255, 255, 255, 255, 255, 252, 127, 169, 169, 168, 166, 171, 170, 156, 163, 251, 252, 255, 255, 255, 255, 134, 142, 135, 174, 171, 169, 172, 169, 178, 143, 235, 220, 215, 249, 248, 243, 156, 105, 89, 136, 162, 132, 122, 151, 145, 173, 253, 255, 253, 217, 235, 221, 156, 161, 155, 161, 157, 127, 153, 136, 146, 163, 244, 232, 255, 255, 244, 232, 166, 160, 152, 141, 135, 115, 147, 155, 144, 137, 255, 255, 255, 255, 254, 255, 170, 112, 131, 123, 123, 147, 93, 140, 131, 136, 137, 255, 255, 206, 249, 252, 158, 137, 136, 128, 120, 122, 131, 123, 116, 75, 79, 253], \"darkFraction\": 0, \"stdLuminance\": 52.17091597216591, \"analysisWidth\": 240, \"meanLuminance\": 201.18653949216025, \"analysisHeight\": 320, \"brightFraction\": 0.32571614583333336, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 405.0529290491211}, \"selectionScore\": 99.00648351822072, \"frameDifference\": null}, {\"index\": 1, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [215, 219, 221, 220, 221, 225, 223, 222, 227, 228, 231, 233, 235, 248, 254, 253, 232, 231, 231, 229, 227, 228, 232, 211, 231, 228, 242, 246, 253, 255, 255, 255, 243, 242, 239, 226, 234, 230, 234, 235, 240, 243, 245, 252, 255, 255, 255, 255, 253, 252, 249, 247, 242, 233, 229, 229, 238, 241, 247, 249, 255, 255, 255, 255, 255, 255, 254, 250, 245, 205, 155, 109, 110, 114, 134, 151, 202, 250, 255, 255, 255, 255, 255, 255, 251, 118, 167, 169, 167, 165, 169, 170, 145, 165, 252, 252, 255, 255, 255, 255, 146, 148, 144, 174, 172, 170, 166, 164, 177, 140, 234, 209, 213, 251, 249, 245, 153, 130, 91, 141, 158, 138, 128, 148, 145, 178, 253, 255, 254, 235, 166, 202, 159, 161, 153, 163, 156, 129, 155, 144, 151, 165, 247, 229, 255, 255, 245, 217, 167, 163, 148, 140, 130, 118, 153, 152, 142, 139, 255, 255, 255, 255, 254, 255, 168, 115, 124, 125, 123, 146, 100, 140, 129, 157, 148, 255, 255, 234, 248, 253, 156, 136, 135, 131, 120, 122, 129, 123, 117, 77, 93, 253], \"darkFraction\": 0, \"stdLuminance\": 52.07825679479587, \"analysisWidth\": 240, \"meanLuminance\": 201.30632061455543, \"analysisHeight\": 320, \"brightFraction\": 0.32678385416666667, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 400.9612994349925}, \"selectionScore\": 98.74227084660228, \"frameDifference\": 0.012704248366013072}, {\"index\": 2, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [213, 219, 221, 220, 221, 226, 224, 223, 227, 227, 231, 232, 236, 244, 254, 254, 233, 230, 231, 227, 227, 229, 230, 214, 233, 223, 241, 245, 252, 255, 255, 255, 242, 241, 239, 232, 232, 231, 235, 239, 241, 242, 246, 251, 254, 255, 255, 255, 254, 251, 250, 247, 243, 233, 226, 231, 241, 241, 245, 246, 255, 255, 255, 255, 255, 255, 255, 252, 235, 203, 118, 100, 105, 115, 132, 194, 231, 243, 255, 255, 255, 255, 255, 255, 253, 123, 167, 169, 170, 167, 171, 168, 144, 180, 253, 252, 255, 255, 255, 255, 142, 148, 160, 174, 174, 168, 164, 166, 173, 139, 236, 230, 230, 252, 251, 248, 157, 113, 108, 139, 159, 139, 135, 150, 147, 179, 249, 255, 254, 234, 178, 218, 159, 161, 154, 162, 157, 125, 154, 142, 151, 164, 241, 255, 255, 255, 245, 232, 168, 163, 149, 142, 130, 124, 152, 153, 143, 136, 255, 255, 255, 255, 254, 255, 165, 114, 126, 125, 123, 145, 101, 137, 127, 133, 187, 255, 255, 233, 251, 253, 159, 137, 134, 128, 117, 121, 127, 122, 120, 139, 105, 253], \"darkFraction\": 0, \"stdLuminance\": 51.6588382484299, \"analysisWidth\": 240, \"meanLuminance\": 202.05864659373117, \"analysisHeight\": 320, \"brightFraction\": 0.3291927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 411.1410683173094}, \"selectionScore\": 98.75012385950748, \"frameDifference\": 0.013562091503267974}, {\"index\": 3, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [215, 218, 221, 221, 222, 225, 224, 223, 227, 228, 231, 233, 235, 246, 254, 254, 232, 231, 231, 227, 227, 229, 230, 222, 232, 227, 240, 245, 253, 255, 255, 255, 243, 241, 240, 235, 223, 231, 234, 238, 239, 242, 247, 251, 254, 255, 255, 255, 253, 252, 249, 247, 243, 233, 227, 231, 242, 240, 245, 247, 255, 255, 255, 255, 255, 255, 255, 251, 237, 207, 112, 102, 105, 115, 132, 189, 231, 233, 255, 255, 255, 255, 255, 255, 251, 128, 164, 169, 169, 166, 171, 169, 144, 182, 250, 252, 255, 255, 255, 255, 139, 152, 159, 176, 174, 168, 162, 166, 174, 138, 238, 230, 225, 252, 252, 248, 157, 112, 97, 139, 159, 139, 133, 149, 146, 181, 248, 255, 255, 235, 232, 222, 158, 161, 153, 163, 157, 127, 153, 142, 151, 164, 254, 255, 255, 255, 243, 233, 168, 163, 150, 142, 130, 120, 151, 151, 143, 137, 255, 255, 255, 255, 254, 255, 163, 114, 124, 121, 122, 147, 103, 138, 125, 136, 233, 255, 255, 234, 249, 253, 158, 138, 135, 129, 119, 121, 130, 123, 117, 95, 243, 254], \"darkFraction\": 0, \"stdLuminance\": 51.251034352293026, \"analysisWidth\": 240, \"meanLuminance\": 202.93030013019467, \"analysisHeight\": 320, \"brightFraction\": 0.33515625, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 409.49248364964814}, \"selectionScore\": 98.81392624594356, \"frameDifference\": 0.01017156862745098}, {\"index\": 4, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [210, 218, 219, 221, 222, 225, 225, 223, 226, 227, 232, 234, 235, 248, 254, 254, 232, 229, 229, 227, 227, 229, 230, 221, 232, 223, 240, 247, 253, 255, 255, 255, 243, 243, 240, 235, 224, 231, 234, 238, 239, 243, 246, 252, 255, 255, 255, 255, 253, 252, 250, 247, 243, 232, 227, 231, 241, 241, 246, 246, 255, 255, 255, 255, 255, 255, 255, 251, 227, 221, 126, 103, 104, 117, 133, 187, 231, 247, 255, 255, 255, 255, 255, 255, 252, 122, 167, 169, 164, 164, 169, 168, 141, 181, 254, 252, 255, 255, 255, 255, 129, 160, 163, 166, 172, 169, 166, 166, 168, 136, 237, 227, 208, 254, 253, 238, 164, 143, 118, 151, 148, 141, 139, 144, 146, 128, 249, 253, 255, 239, 206, 208, 160, 156, 155, 162, 147, 141, 150, 143, 150, 165, 255, 255, 255, 243, 241, 228, 164, 163, 139, 143, 117, 138, 156, 146, 141, 137, 255, 255, 255, 255, 254, 255, 167, 117, 129, 131, 127, 132, 121, 139, 130, 168, 255, 255, 255, 255, 248, 253, 168, 138, 133, 128, 122, 123, 130, 123, 119, 254, 254, 254], \"darkFraction\": 0, \"stdLuminance\": 51.017993500490995, \"analysisWidth\": 240, \"meanLuminance\": 203.98039984112785, \"analysisHeight\": 320, \"brightFraction\": 0.3467578125, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 404.1870074302451}, \"selectionScore\": 98.6563094915894, \"frameDifference\": 0.017401960784313726}], \"valid\": true, \"reasons\": [], \"selectedIndices\": [0, 3, 2]}, \"confirmations\": {}, \"automaticPoints\": {}, \"calibrationSpec\": {\"method\": \"marker\", \"widthMm\": null, \"evidence\": {}, \"heightMm\": null, \"lengthMm\": null, \"referencePlane\": \"\"}, \"measurementContext\": {\"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"brand\": \"Kittycraft\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"pdReference\": \"frame_bridge\"}, \"workingDistanceCm\": 40}}, {\"id\": \"1106f58f-67c0-49e0-98e5-53a5442593ca\", \"view\": \"frontal\", \"width\": 960, \"device\": {\"zoom\": 1, \"depth\": null, \"width\": 960, \"height\": 1280, \"mirrored\": false, \"frameRate\": 30, \"facingMode\": \"user\", \"intrinsics\": null, \"cameraLabel\": \"camera 1, facing front\", \"orientation\": {\"beta\": 55.1, \"gamma\": -4.800000000000001}, \"sourceWidth\": 960, \"sourceHeight\": 1280, \"mainCameraVerifiedByOperator\": true}, \"height\": 1280, \"points\": {}, \"burstId\": \"83522744-f21b-45e9-b1d1-d3c7ea824c99\", \"photoId\": \"mp_0caa65dba9494776837d81d5b9d50b4e\", \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [215, 218, 221, 221, 222, 225, 224, 223, 227, 228, 231, 233, 235, 246, 254, 254, 232, 231, 231, 227, 227, 229, 230, 222, 232, 227, 240, 245, 253, 255, 255, 255, 243, 241, 240, 235, 223, 231, 234, 238, 239, 242, 247, 251, 254, 255, 255, 255, 253, 252, 249, 247, 243, 233, 227, 231, 242, 240, 245, 247, 255, 255, 255, 255, 255, 255, 255, 251, 237, 207, 112, 102, 105, 115, 132, 189, 231, 233, 255, 255, 255, 255, 255, 255, 251, 128, 164, 169, 169, 166, 171, 169, 144, 182, 250, 252, 255, 255, 255, 255, 139, 152, 159, 176, 174, 168, 162, 166, 174, 138, 238, 230, 225, 252, 252, 248, 157, 112, 97, 139, 159, 139, 133, 149, 146, 181, 248, 255, 255, 235, 232, 222, 158, 161, 153, 163, 157, 127, 153, 142, 151, 164, 254, 255, 255, 255, 243, 233, 168, 163, 150, 142, 130, 120, 151, 151, 143, 137, 255, 255, 255, 255, 254, 255, 163, 114, 124, 121, 122, 147, 103, 138, 125, 136, 233, 255, 255, 234, 249, 253, 158, 138, 135, 129, 119, 121, 130, 123, 117, 95, 243, 254], \"darkFraction\": 0, \"stdLuminance\": 51.251034352293026, \"analysisWidth\": 240, \"meanLuminance\": 202.93030013019467, \"analysisHeight\": 320, \"brightFraction\": 0.33515625, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 409.49248364964814}, \"createdAt\": \"2026-11-10T02:56:45.412Z\", \"photoHash\": \"468ae7c122c2a20906dc7f8881061cdd2534dd95225bb1b88b43626a34f34049\", \"superseded\": false, \"sampleIndex\": 1, \"measurements\": {}, \"burstAnalysis\": {\"note\": \"Pemilihan berdasarkan detail, pencahayaan dan perubahan gambar. Ini bukan stabilitas landmark atau pengulangan nilai ukur.\", \"rows\": [{\"index\": 0, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [218, 218, 222, 221, 222, 225, 224, 223, 227, 229, 231, 234, 236, 249, 254, 255, 233, 232, 231, 228, 227, 227, 233, 220, 232, 231, 241, 247, 253, 255, 255, 255, 243, 242, 239, 229, 234, 230, 234, 232, 240, 243, 247, 252, 255, 255, 255, 255, 253, 253, 250, 247, 242, 233, 229, 229, 239, 235, 245, 251, 255, 255, 255, 255, 255, 255, 254, 250, 245, 208, 111, 105, 112, 119, 135, 150, 180, 216, 255, 255, 255, 255, 255, 255, 252, 127, 169, 169, 168, 166, 171, 170, 156, 163, 251, 252, 255, 255, 255, 255, 134, 142, 135, 174, 171, 169, 172, 169, 178, 143, 235, 220, 215, 249, 248, 243, 156, 105, 89, 136, 162, 132, 122, 151, 145, 173, 253, 255, 253, 217, 235, 221, 156, 161, 155, 161, 157, 127, 153, 136, 146, 163, 244, 232, 255, 255, 244, 232, 166, 160, 152, 141, 135, 115, 147, 155, 144, 137, 255, 255, 255, 255, 254, 255, 170, 112, 131, 123, 123, 147, 93, 140, 131, 136, 137, 255, 255, 206, 249, 252, 158, 137, 136, 128, 120, 122, 131, 123, 116, 75, 79, 253], \"darkFraction\": 0, \"stdLuminance\": 52.17091597216591, \"analysisWidth\": 240, \"meanLuminance\": 201.18653949216025, \"analysisHeight\": 320, \"brightFraction\": 0.32571614583333336, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 405.0529290491211}, \"selectionScore\": 99.00648351822072, \"frameDifference\": null}, {\"index\": 1, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [215, 219, 221, 220, 221, 225, 223, 222, 227, 228, 231, 233, 235, 248, 254, 253, 232, 231, 231, 229, 227, 228, 232, 211, 231, 228, 242, 246, 253, 255, 255, 255, 243, 242, 239, 226, 234, 230, 234, 235, 240, 243, 245, 252, 255, 255, 255, 255, 253, 252, 249, 247, 242, 233, 229, 229, 238, 241, 247, 249, 255, 255, 255, 255, 255, 255, 254, 250, 245, 205, 155, 109, 110, 114, 134, 151, 202, 250, 255, 255, 255, 255, 255, 255, 251, 118, 167, 169, 167, 165, 169, 170, 145, 165, 252, 252, 255, 255, 255, 255, 146, 148, 144, 174, 172, 170, 166, 164, 177, 140, 234, 209, 213, 251, 249, 245, 153, 130, 91, 141, 158, 138, 128, 148, 145, 178, 253, 255, 254, 235, 166, 202, 159, 161, 153, 163, 156, 129, 155, 144, 151, 165, 247, 229, 255, 255, 245, 217, 167, 163, 148, 140, 130, 118, 153, 152, 142, 139, 255, 255, 255, 255, 254, 255, 168, 115, 124, 125, 123, 146, 100, 140, 129, 157, 148, 255, 255, 234, 248, 253, 156, 136, 135, 131, 120, 122, 129, 123, 117, 77, 93, 253], \"darkFraction\": 0, \"stdLuminance\": 52.07825679479587, \"analysisWidth\": 240, \"meanLuminance\": 201.30632061455543, \"analysisHeight\": 320, \"brightFraction\": 0.32678385416666667, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 400.9612994349925}, \"selectionScore\": 98.74227084660228, \"frameDifference\": 0.012704248366013072}, {\"index\": 2, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [213, 219, 221, 220, 221, 226, 224, 223, 227, 227, 231, 232, 236, 244, 254, 254, 233, 230, 231, 227, 227, 229, 230, 214, 233, 223, 241, 245, 252, 255, 255, 255, 242, 241, 239, 232, 232, 231, 235, 239, 241, 242, 246, 251, 254, 255, 255, 255, 254, 251, 250, 247, 243, 233, 226, 231, 241, 241, 245, 246, 255, 255, 255, 255, 255, 255, 255, 252, 235, 203, 118, 100, 105, 115, 132, 194, 231, 243, 255, 255, 255, 255, 255, 255, 253, 123, 167, 169, 170, 167, 171, 168, 144, 180, 253, 252, 255, 255, 255, 255, 142, 148, 160, 174, 174, 168, 164, 166, 173, 139, 236, 230, 230, 252, 251, 248, 157, 113, 108, 139, 159, 139, 135, 150, 147, 179, 249, 255, 254, 234, 178, 218, 159, 161, 154, 162, 157, 125, 154, 142, 151, 164, 241, 255, 255, 255, 245, 232, 168, 163, 149, 142, 130, 124, 152, 153, 143, 136, 255, 255, 255, 255, 254, 255, 165, 114, 126, 125, 123, 145, 101, 137, 127, 133, 187, 255, 255, 233, 251, 253, 159, 137, 134, 128, 117, 121, 127, 122, 120, 139, 105, 253], \"darkFraction\": 0, \"stdLuminance\": 51.6588382484299, \"analysisWidth\": 240, \"meanLuminance\": 202.05864659373117, \"analysisHeight\": 320, \"brightFraction\": 0.3291927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 411.1410683173094}, \"selectionScore\": 98.75012385950748, \"frameDifference\": 0.013562091503267974}, {\"index\": 3, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [215, 218, 221, 221, 222, 225, 224, 223, 227, 228, 231, 233, 235, 246, 254, 254, 232, 231, 231, 227, 227, 229, 230, 222, 232, 227, 240, 245, 253, 255, 255, 255, 243, 241, 240, 235, 223, 231, 234, 238, 239, 242, 247, 251, 254, 255, 255, 255, 253, 252, 249, 247, 243, 233, 227, 231, 242, 240, 245, 247, 255, 255, 255, 255, 255, 255, 255, 251, 237, 207, 112, 102, 105, 115, 132, 189, 231, 233, 255, 255, 255, 255, 255, 255, 251, 128, 164, 169, 169, 166, 171, 169, 144, 182, 250, 252, 255, 255, 255, 255, 139, 152, 159, 176, 174, 168, 162, 166, 174, 138, 238, 230, 225, 252, 252, 248, 157, 112, 97, 139, 159, 139, 133, 149, 146, 181, 248, 255, 255, 235, 232, 222, 158, 161, 153, 163, 157, 127, 153, 142, 151, 164, 254, 255, 255, 255, 243, 233, 168, 163, 150, 142, 130, 120, 151, 151, 143, 137, 255, 255, 255, 255, 254, 255, 163, 114, 124, 121, 122, 147, 103, 138, 125, 136, 233, 255, 255, 234, 249, 253, 158, 138, 135, 129, 119, 121, 130, 123, 117, 95, 243, 254], \"darkFraction\": 0, \"stdLuminance\": 51.251034352293026, \"analysisWidth\": 240, \"meanLuminance\": 202.93030013019467, \"analysisHeight\": 320, \"brightFraction\": 0.33515625, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 409.49248364964814}, \"selectionScore\": 98.81392624594356, \"frameDifference\": 0.01017156862745098}, {\"index\": 4, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [210, 218, 219, 221, 222, 225, 225, 223, 226, 227, 232, 234, 235, 248, 254, 254, 232, 229, 229, 227, 227, 229, 230, 221, 232, 223, 240, 247, 253, 255, 255, 255, 243, 243, 240, 235, 224, 231, 234, 238, 239, 243, 246, 252, 255, 255, 255, 255, 253, 252, 250, 247, 243, 232, 227, 231, 241, 241, 246, 246, 255, 255, 255, 255, 255, 255, 255, 251, 227, 221, 126, 103, 104, 117, 133, 187, 231, 247, 255, 255, 255, 255, 255, 255, 252, 122, 167, 169, 164, 164, 169, 168, 141, 181, 254, 252, 255, 255, 255, 255, 129, 160, 163, 166, 172, 169, 166, 166, 168, 136, 237, 227, 208, 254, 253, 238, 164, 143, 118, 151, 148, 141, 139, 144, 146, 128, 249, 253, 255, 239, 206, 208, 160, 156, 155, 162, 147, 141, 150, 143, 150, 165, 255, 255, 255, 243, 241, 228, 164, 163, 139, 143, 117, 138, 156, 146, 141, 137, 255, 255, 255, 255, 254, 255, 167, 117, 129, 131, 127, 132, 121, 139, 130, 168, 255, 255, 255, 255, 248, 253, 168, 138, 133, 128, 122, 123, 130, 123, 119, 254, 254, 254], \"darkFraction\": 0, \"stdLuminance\": 51.017993500490995, \"analysisWidth\": 240, \"meanLuminance\": 203.98039984112785, \"analysisHeight\": 320, \"brightFraction\": 0.3467578125, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 404.1870074302451}, \"selectionScore\": 98.6563094915894, \"frameDifference\": 0.017401960784313726}], \"valid\": true, \"reasons\": [], \"selectedIndices\": [0, 3, 2]}, \"confirmations\": {}, \"automaticPoints\": {}, \"calibrationSpec\": {\"method\": \"marker\", \"widthMm\": null, \"evidence\": {}, \"heightMm\": null, \"lengthMm\": null, \"referencePlane\": \"\"}, \"measurementContext\": {\"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"brand\": \"Kittycraft\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"pdReference\": \"frame_bridge\"}, \"workingDistanceCm\": 40}}, {\"id\": \"7041a10a-e8d7-4cfa-9bd5-48c8aba8afe8\", \"view\": \"frontal\", \"width\": 960, \"device\": {\"zoom\": 1, \"depth\": null, \"width\": 960, \"height\": 1280, \"mirrored\": false, \"frameRate\": 30, \"facingMode\": \"user\", \"intrinsics\": null, \"cameraLabel\": \"camera 1, facing front\", \"orientation\": {\"beta\": 55.1, \"gamma\": -4.800000000000001}, \"sourceWidth\": 960, \"sourceHeight\": 1280, \"mainCameraVerifiedByOperator\": true}, \"height\": 1280, \"points\": {}, \"burstId\": \"83522744-f21b-45e9-b1d1-d3c7ea824c99\", \"photoId\": \"mp_084dd33987c24014bebdc753dff3420a\", \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [213, 219, 221, 220, 221, 226, 224, 223, 227, 227, 231, 232, 236, 244, 254, 254, 233, 230, 231, 227, 227, 229, 230, 214, 233, 223, 241, 245, 252, 255, 255, 255, 242, 241, 239, 232, 232, 231, 235, 239, 241, 242, 246, 251, 254, 255, 255, 255, 254, 251, 250, 247, 243, 233, 226, 231, 241, 241, 245, 246, 255, 255, 255, 255, 255, 255, 255, 252, 235, 203, 118, 100, 105, 115, 132, 194, 231, 243, 255, 255, 255, 255, 255, 255, 253, 123, 167, 169, 170, 167, 171, 168, 144, 180, 253, 252, 255, 255, 255, 255, 142, 148, 160, 174, 174, 168, 164, 166, 173, 139, 236, 230, 230, 252, 251, 248, 157, 113, 108, 139, 159, 139, 135, 150, 147, 179, 249, 255, 254, 234, 178, 218, 159, 161, 154, 162, 157, 125, 154, 142, 151, 164, 241, 255, 255, 255, 245, 232, 168, 163, 149, 142, 130, 124, 152, 153, 143, 136, 255, 255, 255, 255, 254, 255, 165, 114, 126, 125, 123, 145, 101, 137, 127, 133, 187, 255, 255, 233, 251, 253, 159, 137, 134, 128, 117, 121, 127, 122, 120, 139, 105, 253], \"darkFraction\": 0, \"stdLuminance\": 51.6588382484299, \"analysisWidth\": 240, \"meanLuminance\": 202.05864659373117, \"analysisHeight\": 320, \"brightFraction\": 0.3291927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 411.1410683173094}, \"createdAt\": \"2026-11-10T02:56:45.603Z\", \"photoHash\": \"59d256b2f5c9270a4d4950536c467875c04535735d04c7d43a3fd5319b08e63f\", \"superseded\": false, \"sampleIndex\": 2, \"measurements\": {}, \"burstAnalysis\": {\"note\": \"Pemilihan berdasarkan detail, pencahayaan dan perubahan gambar. Ini bukan stabilitas landmark atau pengulangan nilai ukur.\", \"rows\": [{\"index\": 0, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [218, 218, 222, 221, 222, 225, 224, 223, 227, 229, 231, 234, 236, 249, 254, 255, 233, 232, 231, 228, 227, 227, 233, 220, 232, 231, 241, 247, 253, 255, 255, 255, 243, 242, 239, 229, 234, 230, 234, 232, 240, 243, 247, 252, 255, 255, 255, 255, 253, 253, 250, 247, 242, 233, 229, 229, 239, 235, 245, 251, 255, 255, 255, 255, 255, 255, 254, 250, 245, 208, 111, 105, 112, 119, 135, 150, 180, 216, 255, 255, 255, 255, 255, 255, 252, 127, 169, 169, 168, 166, 171, 170, 156, 163, 251, 252, 255, 255, 255, 255, 134, 142, 135, 174, 171, 169, 172, 169, 178, 143, 235, 220, 215, 249, 248, 243, 156, 105, 89, 136, 162, 132, 122, 151, 145, 173, 253, 255, 253, 217, 235, 221, 156, 161, 155, 161, 157, 127, 153, 136, 146, 163, 244, 232, 255, 255, 244, 232, 166, 160, 152, 141, 135, 115, 147, 155, 144, 137, 255, 255, 255, 255, 254, 255, 170, 112, 131, 123, 123, 147, 93, 140, 131, 136, 137, 255, 255, 206, 249, 252, 158, 137, 136, 128, 120, 122, 131, 123, 116, 75, 79, 253], \"darkFraction\": 0, \"stdLuminance\": 52.17091597216591, \"analysisWidth\": 240, \"meanLuminance\": 201.18653949216025, \"analysisHeight\": 320, \"brightFraction\": 0.32571614583333336, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 405.0529290491211}, \"selectionScore\": 99.00648351822072, \"frameDifference\": null}, {\"index\": 1, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [215, 219, 221, 220, 221, 225, 223, 222, 227, 228, 231, 233, 235, 248, 254, 253, 232, 231, 231, 229, 227, 228, 232, 211, 231, 228, 242, 246, 253, 255, 255, 255, 243, 242, 239, 226, 234, 230, 234, 235, 240, 243, 245, 252, 255, 255, 255, 255, 253, 252, 249, 247, 242, 233, 229, 229, 238, 241, 247, 249, 255, 255, 255, 255, 255, 255, 254, 250, 245, 205, 155, 109, 110, 114, 134, 151, 202, 250, 255, 255, 255, 255, 255, 255, 251, 118, 167, 169, 167, 165, 169, 170, 145, 165, 252, 252, 255, 255, 255, 255, 146, 148, 144, 174, 172, 170, 166, 164, 177, 140, 234, 209, 213, 251, 249, 245, 153, 130, 91, 141, 158, 138, 128, 148, 145, 178, 253, 255, 254, 235, 166, 202, 159, 161, 153, 163, 156, 129, 155, 144, 151, 165, 247, 229, 255, 255, 245, 217, 167, 163, 148, 140, 130, 118, 153, 152, 142, 139, 255, 255, 255, 255, 254, 255, 168, 115, 124, 125, 123, 146, 100, 140, 129, 157, 148, 255, 255, 234, 248, 253, 156, 136, 135, 131, 120, 122, 129, 123, 117, 77, 93, 253], \"darkFraction\": 0, \"stdLuminance\": 52.07825679479587, \"analysisWidth\": 240, \"meanLuminance\": 201.30632061455543, \"analysisHeight\": 320, \"brightFraction\": 0.32678385416666667, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 400.9612994349925}, \"selectionScore\": 98.74227084660228, \"frameDifference\": 0.012704248366013072}, {\"index\": 2, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [213, 219, 221, 220, 221, 226, 224, 223, 227, 227, 231, 232, 236, 244, 254, 254, 233, 230, 231, 227, 227, 229, 230, 214, 233, 223, 241, 245, 252, 255, 255, 255, 242, 241, 239, 232, 232, 231, 235, 239, 241, 242, 246, 251, 254, 255, 255, 255, 254, 251, 250, 247, 243, 233, 226, 231, 241, 241, 245, 246, 255, 255, 255, 255, 255, 255, 255, 252, 235, 203, 118, 100, 105, 115, 132, 194, 231, 243, 255, 255, 255, 255, 255, 255, 253, 123, 167, 169, 170, 167, 171, 168, 144, 180, 253, 252, 255, 255, 255, 255, 142, 148, 160, 174, 174, 168, 164, 166, 173, 139, 236, 230, 230, 252, 251, 248, 157, 113, 108, 139, 159, 139, 135, 150, 147, 179, 249, 255, 254, 234, 178, 218, 159, 161, 154, 162, 157, 125, 154, 142, 151, 164, 241, 255, 255, 255, 245, 232, 168, 163, 149, 142, 130, 124, 152, 153, 143, 136, 255, 255, 255, 255, 254, 255, 165, 114, 126, 125, 123, 145, 101, 137, 127, 133, 187, 255, 255, 233, 251, 253, 159, 137, 134, 128, 117, 121, 127, 122, 120, 139, 105, 253], \"darkFraction\": 0, \"stdLuminance\": 51.6588382484299, \"analysisWidth\": 240, \"meanLuminance\": 202.05864659373117, \"analysisHeight\": 320, \"brightFraction\": 0.3291927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 411.1410683173094}, \"selectionScore\": 98.75012385950748, \"frameDifference\": 0.013562091503267974}, {\"index\": 3, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [215, 218, 221, 221, 222, 225, 224, 223, 227, 228, 231, 233, 235, 246, 254, 254, 232, 231, 231, 227, 227, 229, 230, 222, 232, 227, 240, 245, 253, 255, 255, 255, 243, 241, 240, 235, 223, 231, 234, 238, 239, 242, 247, 251, 254, 255, 255, 255, 253, 252, 249, 247, 243, 233, 227, 231, 242, 240, 245, 247, 255, 255, 255, 255, 255, 255, 255, 251, 237, 207, 112, 102, 105, 115, 132, 189, 231, 233, 255, 255, 255, 255, 255, 255, 251, 128, 164, 169, 169, 166, 171, 169, 144, 182, 250, 252, 255, 255, 255, 255, 139, 152, 159, 176, 174, 168, 162, 166, 174, 138, 238, 230, 225, 252, 252, 248, 157, 112, 97, 139, 159, 139, 133, 149, 146, 181, 248, 255, 255, 235, 232, 222, 158, 161, 153, 163, 157, 127, 153, 142, 151, 164, 254, 255, 255, 255, 243, 233, 168, 163, 150, 142, 130, 120, 151, 151, 143, 137, 255, 255, 255, 255, 254, 255, 163, 114, 124, 121, 122, 147, 103, 138, 125, 136, 233, 255, 255, 234, 249, 253, 158, 138, 135, 129, 119, 121, 130, 123, 117, 95, 243, 254], \"darkFraction\": 0, \"stdLuminance\": 51.251034352293026, \"analysisWidth\": 240, \"meanLuminance\": 202.93030013019467, \"analysisHeight\": 320, \"brightFraction\": 0.33515625, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 409.49248364964814}, \"selectionScore\": 98.81392624594356, \"frameDifference\": 0.01017156862745098}, {\"index\": 4, \"analysis\": {\"score\": 93, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [210, 218, 219, 221, 222, 225, 225, 223, 226, 227, 232, 234, 235, 248, 254, 254, 232, 229, 229, 227, 227, 229, 230, 221, 232, 223, 240, 247, 253, 255, 255, 255, 243, 243, 240, 235, 224, 231, 234, 238, 239, 243, 246, 252, 255, 255, 255, 255, 253, 252, 250, 247, 243, 232, 227, 231, 241, 241, 246, 246, 255, 255, 255, 255, 255, 255, 255, 251, 227, 221, 126, 103, 104, 117, 133, 187, 231, 247, 255, 255, 255, 255, 255, 255, 252, 122, 167, 169, 164, 164, 169, 168, 141, 181, 254, 252, 255, 255, 255, 255, 129, 160, 163, 166, 172, 169, 166, 166, 168, 136, 237, 227, 208, 254, 253, 238, 164, 143, 118, 151, 148, 141, 139, 144, 146, 128, 249, 253, 255, 239, 206, 208, 160, 156, 155, 162, 147, 141, 150, 143, 150, 165, 255, 255, 255, 243, 241, 228, 164, 163, 139, 143, 117, 138, 156, 146, 141, 137, 255, 255, 255, 255, 254, 255, 167, 117, 129, 131, 127, 132, 121, 139, 130, 168, 255, 255, 255, 255, 248, 253, 168, 138, 133, 128, 122, 123, 130, 123, 119, 254, 254, 254], \"darkFraction\": 0, \"stdLuminance\": 51.017993500490995, \"analysisWidth\": 240, \"meanLuminance\": 203.98039984112785, \"analysisHeight\": 320, \"brightFraction\": 0.3467578125, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 404.1870074302451}, \"selectionScore\": 98.6563094915894, \"frameDifference\": 0.017401960784313726}], \"valid\": true, \"reasons\": [], \"selectedIndices\": [0, 3, 2]}, \"confirmations\": {}, \"automaticPoints\": {}, \"calibrationSpec\": {\"method\": \"marker\", \"widthMm\": null, \"evidence\": {}, \"heightMm\": null, \"lengthMm\": null, \"referencePlane\": \"\"}, \"measurementContext\": {\"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"brand\": \"Kittycraft\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"pdReference\": \"frame_bridge\"}, \"workingDistanceCm\": 40}}], \"consents\": {\"capture\": true, \"thumbnail\": true, \"confirmedAt\": \"2026-11-10T02:55:04.604Z\", \"retainPhotos\": true, \"uploadPhotos\": true}, \"deviceModel\": \"\", \"preparation\": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], \"prescription\": {\"id\": \"rx_8a7793124f314342\", \"od\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"os\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"date\": \"2026-11-09\", \"notes\": \"\", \"source\": \"professional_prescription\", \"pd_left\": null, \"pd_right\": null, \"pd_total\": null}, \"examinationDate\": \"2026-11-10\", \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"workingDistanceCm\": 40, \"manualMeasurements\": {}, \"requiredParameters\": [\"distance_pd\"]}','Pengambilan 3 sampel Frontal — target jauh.','usr_c4b3d45ff0b94ffd','optifit-local-geometry-1.0.0','2026-11-10 02:56:47.698776'),('mr_71f19a7b82764acc8ecdc4e262aa73cb','ms_8c2a17db7e0c4b2b8a57029c89623953','usr_c4b3d45ff0b94ffd',3,'mr_cf4815a4e7f346cda3a7202278e238cd','{\"mode\": \"semi_automatic\", \"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"sku\": \"KC-CBY-AN-YLW\", \"size\": \"XS\", \"brand\": \"Kittycraft\", \"color\": \"Kuning\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"variantId\": \"var_efda2ee981f14664\", \"sourceNote\": \"\", \"pdReference\": \"frame_bridge\", \"sourceScope\": \"product\", \"templeLength\": null, \"sourceVersion\": 1}, \"notes\": \"\", \"results\": {}, \"captures\": [{\"id\": \"06fad378-1c6a-40bc-8099-6d34adc78350\", \"view\": \"frontal\", \"width\": 960, \"device\": {\"zoom\": 1, \"depth\": null, \"width\": 960, \"height\": 1280, \"mirrored\": false, \"frameRate\": 30, \"facingMode\": \"user\", \"intrinsics\": null, \"cameraLabel\": \"camera 1, facing front\", \"orientation\": null, \"sourceWidth\": 960, \"sourceHeight\": 1280, \"mainCameraVerifiedByOperator\": true}, \"height\": 1280, \"points\": {}, \"burstId\": \"a1c9ce47-cf76-42b9-b39e-25d1a0a81412\", \"photoId\": \"mp_4c362829cebe4a9882a8c86f05bc0413\", \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 219, 223, 122, 109, 114, 107, 105, 104, 110, 153, 246, 216, 204, 255, 255, 234, 159, 227, 198, 177, 167, 163, 140, 114, 97, 99, 139, 225, 255, 255, 255, 188, 250, 224, 194, 180, 169, 165, 158, 150, 162, 170, 100, 254, 255, 255, 255, 174, 255, 214, 192, 177, 172, 167, 166, 155, 140, 135, 75, 254, 251, 255, 255, 253, 252, 190, 150, 141, 156, 137, 98, 130, 134, 156, 254, 247, 255, 255, 255, 255, 254, 188, 163, 174, 179, 142, 135, 132, 129, 144, 245, 219, 254, 234, 250, 253, 215, 166, 212, 182, 180, 159, 151, 119, 121, 143, 157, 254, 253, 169, 254, 255, 200, 173, 186, 191, 193, 128, 141, 112, 123, 135, 254, 234, 255, 163, 252, 255, 85, 183, 150, 171, 171, 133, 111, 121, 121, 125, 246, 255, 239, 180, 148, 70, 122, 64, 152, 166, 151, 132, 125, 119, 57, 70, 66, 65, 103, 68, 65, 92, 81, 58, 122, 130, 107, 96, 98, 64, 58, 66, 59, 66, 66, 94, 53, 57, 72, 65, 70, 96, 112, 99, 74, 72, 68, 70, 67, 63, 61], \"darkFraction\": 0, \"stdLuminance\": 64.01172832662922, \"analysisWidth\": 240, \"meanLuminance\": 157.68188170572682, \"analysisHeight\": 320, \"brightFraction\": 0.19272135416666664, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 554.1889526826051}, \"createdAt\": \"2026-11-10T02:30:34.378Z\", \"photoHash\": \"862f10231611ded242bd03689314d0c6e2661d86cc7d14e5006be029261a143c\", \"superseded\": false, \"sampleIndex\": 0, \"measurements\": {}, \"burstAnalysis\": {\"note\": \"Pemilihan berdasarkan detail, pencahayaan dan perubahan gambar. Ini bukan stabilitas landmark atau pengulangan nilai ukur.\", \"rows\": [{\"index\": 0, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 219, 223, 122, 109, 114, 107, 105, 104, 110, 153, 246, 216, 204, 255, 255, 234, 159, 227, 198, 177, 167, 163, 140, 114, 97, 99, 139, 225, 255, 255, 255, 188, 250, 224, 194, 180, 169, 165, 158, 150, 162, 170, 100, 254, 255, 255, 255, 174, 255, 214, 192, 177, 172, 167, 166, 155, 140, 135, 75, 254, 251, 255, 255, 253, 252, 190, 150, 141, 156, 137, 98, 130, 134, 156, 254, 247, 255, 255, 255, 255, 254, 188, 163, 174, 179, 142, 135, 132, 129, 144, 245, 219, 254, 234, 250, 253, 215, 166, 212, 182, 180, 159, 151, 119, 121, 143, 157, 254, 253, 169, 254, 255, 200, 173, 186, 191, 193, 128, 141, 112, 123, 135, 254, 234, 255, 163, 252, 255, 85, 183, 150, 171, 171, 133, 111, 121, 121, 125, 246, 255, 239, 180, 148, 70, 122, 64, 152, 166, 151, 132, 125, 119, 57, 70, 66, 65, 103, 68, 65, 92, 81, 58, 122, 130, 107, 96, 98, 64, 58, 66, 59, 66, 66, 94, 53, 57, 72, 65, 70, 96, 112, 99, 74, 72, 68, 70, 67, 63, 61], \"darkFraction\": 0, \"stdLuminance\": 64.01172832662922, \"analysisWidth\": 240, \"meanLuminance\": 157.68188170572682, \"analysisHeight\": 320, \"brightFraction\": 0.19272135416666664, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 554.1889526826051}, \"selectionScore\": 102.31930851108866, \"frameDifference\": null}, {\"index\": 1, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 213, 217, 122, 110, 114, 103, 104, 107, 114, 254, 245, 218, 207, 255, 255, 247, 159, 226, 198, 181, 167, 164, 149, 130, 98, 104, 189, 229, 255, 255, 255, 199, 251, 220, 195, 179, 172, 166, 160, 154, 160, 171, 93, 255, 255, 255, 255, 167, 255, 169, 136, 157, 169, 167, 140, 97, 104, 113, 74, 255, 251, 255, 255, 248, 252, 172, 123, 137, 105, 132, 119, 104, 115, 148, 130, 252, 255, 255, 255, 255, 250, 187, 178, 176, 161, 157, 126, 140, 136, 145, 128, 221, 254, 237, 248, 254, 218, 182, 156, 177, 110, 141, 115, 125, 132, 145, 158, 252, 253, 173, 253, 255, 203, 178, 188, 208, 129, 122, 103, 129, 130, 138, 254, 236, 253, 157, 250, 255, 81, 183, 158, 169, 139, 123, 101, 124, 122, 130, 238, 254, 204, 173, 152, 71, 125, 64, 167, 165, 154, 133, 124, 120, 57, 73, 64, 72, 104, 64, 67, 91, 79, 55, 121, 127, 110, 101, 96, 65, 60, 70, 60, 66, 66, 89, 55, 54, 75, 64, 71, 94, 110, 100, 76, 71, 71, 67, 66, 60, 59], \"darkFraction\": 0, \"stdLuminance\": 64.06198522944985, \"analysisWidth\": 240, \"meanLuminance\": 158.89106833593817, \"analysisHeight\": 320, \"brightFraction\": 0.1975390625, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 529.0478336837755}, \"selectionScore\": 101.5740293462105, \"frameDifference\": 0.0349468954248366}, {\"index\": 2, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 218, 226, 122, 110, 115, 105, 104, 106, 115, 245, 244, 217, 204, 255, 255, 246, 168, 228, 198, 179, 167, 166, 147, 123, 99, 106, 216, 225, 255, 255, 255, 199, 252, 219, 193, 178, 170, 167, 159, 153, 162, 170, 91, 255, 255, 255, 255, 163, 255, 168, 132, 160, 171, 165, 136, 97, 106, 118, 78, 255, 253, 255, 255, 178, 247, 186, 120, 137, 108, 135, 120, 104, 106, 149, 134, 253, 255, 255, 255, 255, 248, 186, 180, 179, 162, 154, 144, 140, 136, 146, 102, 229, 253, 213, 255, 254, 218, 181, 156, 175, 111, 135, 117, 125, 135, 144, 157, 252, 252, 165, 255, 255, 204, 179, 179, 204, 129, 121, 105, 127, 129, 139, 254, 250, 241, 164, 253, 255, 82, 183, 161, 163, 129, 120, 107, 124, 120, 124, 247, 254, 218, 175, 148, 69, 119, 67, 167, 164, 148, 131, 125, 120, 57, 73, 62, 67, 105, 63, 65, 90, 82, 57, 123, 131, 108, 102, 96, 64, 60, 67, 61, 67, 65, 88, 56, 57, 73, 66, 72, 96, 111, 100, 75, 75, 68, 69, 66, 62, 63], \"darkFraction\": 0, \"stdLuminance\": 64.30409392934628, \"analysisWidth\": 240, \"meanLuminance\": 159.073624770831, \"analysisHeight\": 320, \"brightFraction\": 0.20016927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 538.9295798455837}, \"selectionScore\": 102.0520596383938, \"frameDifference\": 0.011968954248366014}, {\"index\": 3, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 230, 216, 120, 110, 114, 106, 103, 107, 123, 229, 244, 220, 202, 255, 255, 236, 161, 232, 197, 178, 168, 163, 144, 120, 102, 107, 209, 224, 255, 255, 255, 195, 253, 215, 192, 180, 171, 167, 160, 154, 163, 170, 95, 255, 255, 255, 255, 168, 255, 181, 143, 164, 173, 165, 154, 100, 107, 125, 81, 255, 254, 255, 255, 160, 232, 182, 133, 139, 108, 103, 121, 104, 111, 150, 122, 242, 255, 255, 255, 255, 244, 186, 183, 180, 167, 150, 136, 141, 135, 148, 164, 235, 254, 236, 250, 255, 214, 181, 154, 177, 150, 137, 136, 127, 138, 144, 167, 252, 253, 165, 255, 255, 204, 182, 172, 197, 130, 116, 104, 123, 132, 139, 253, 253, 224, 184, 255, 255, 80, 178, 165, 165, 125, 120, 113, 123, 120, 122, 253, 254, 220, 173, 161, 70, 114, 65, 158, 166, 146, 126, 123, 118, 55, 72, 65, 69, 101, 68, 64, 87, 85, 58, 118, 130, 106, 101, 94, 65, 60, 67, 59, 67, 65, 81, 53, 57, 73, 65, 75, 96, 112, 101, 76, 75, 67, 69, 62, 60, 65], \"darkFraction\": 0, \"stdLuminance\": 64.37153551407151, \"analysisWidth\": 240, \"meanLuminance\": 158.97609537239083, \"analysisHeight\": 320, \"brightFraction\": 0.19998697916666663, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 534.3955895714618}, \"selectionScore\": 101.98357778884449, \"frameDifference\": 0.01497140522875817}, {\"index\": 4, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 216, 233, 121, 110, 111, 106, 101, 107, 118, 219, 244, 217, 205, 255, 255, 253, 187, 233, 199, 178, 168, 164, 143, 119, 101, 106, 210, 227, 255, 255, 255, 195, 253, 217, 190, 180, 170, 168, 159, 154, 162, 171, 94, 255, 255, 255, 255, 172, 255, 181, 149, 166, 173, 167, 156, 102, 105, 125, 78, 255, 253, 255, 255, 222, 242, 166, 143, 141, 107, 100, 120, 116, 119, 150, 104, 140, 255, 255, 255, 255, 247, 184, 181, 180, 157, 150, 137, 141, 135, 147, 120, 221, 254, 212, 255, 254, 218, 181, 153, 179, 152, 141, 138, 127, 137, 146, 164, 253, 253, 166, 254, 255, 205, 179, 176, 198, 128, 119, 104, 121, 131, 138, 255, 251, 235, 167, 254, 255, 80, 181, 165, 165, 130, 122, 110, 123, 120, 131, 252, 254, 208, 176, 142, 70, 117, 64, 161, 166, 146, 126, 122, 119, 56, 73, 67, 67, 100, 69, 65, 92, 84, 56, 118, 129, 105, 101, 95, 66, 60, 68, 59, 69, 62, 82, 53, 59, 76, 65, 74, 99, 113, 99, 75, 75, 66, 70, 63, 61, 64], \"darkFraction\": 0, \"stdLuminance\": 64.34327068857081, \"analysisWidth\": 240, \"meanLuminance\": 159.02655464843, \"analysisHeight\": 320, \"brightFraction\": 0.2002734375, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 548.633728154622}, \"selectionScore\": 102.0290233494044, \"frameDifference\": 0.01401143790849673}], \"valid\": true, \"reasons\": [], \"selectedIndices\": [0, 2, 4]}, \"confirmations\": {}, \"automaticPoints\": {}, \"calibrationSpec\": {\"method\": \"marker\", \"widthMm\": null, \"evidence\": {}, \"heightMm\": null, \"lengthMm\": null, \"referencePlane\": \"\"}, \"measurementContext\": {\"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"brand\": \"Kittycraft\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"pdReference\": \"frame_bridge\"}, \"workingDistanceCm\": 40}}, {\"id\": \"f4d7dd7a-a548-4a17-b9f0-5af1f96ed53a\", \"view\": \"frontal\", \"width\": 960, \"device\": {\"zoom\": 1, \"depth\": null, \"width\": 960, \"height\": 1280, \"mirrored\": false, \"frameRate\": 30, \"facingMode\": \"user\", \"intrinsics\": null, \"cameraLabel\": \"camera 1, facing front\", \"orientation\": null, \"sourceWidth\": 960, \"sourceHeight\": 1280, \"mainCameraVerifiedByOperator\": true}, \"height\": 1280, \"points\": {}, \"burstId\": \"a1c9ce47-cf76-42b9-b39e-25d1a0a81412\", \"photoId\": \"mp_f83fadbccf7241e4a397dd665b9f2476\", \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 218, 226, 122, 110, 115, 105, 104, 106, 115, 245, 244, 217, 204, 255, 255, 246, 168, 228, 198, 179, 167, 166, 147, 123, 99, 106, 216, 225, 255, 255, 255, 199, 252, 219, 193, 178, 170, 167, 159, 153, 162, 170, 91, 255, 255, 255, 255, 163, 255, 168, 132, 160, 171, 165, 136, 97, 106, 118, 78, 255, 253, 255, 255, 178, 247, 186, 120, 137, 108, 135, 120, 104, 106, 149, 134, 253, 255, 255, 255, 255, 248, 186, 180, 179, 162, 154, 144, 140, 136, 146, 102, 229, 253, 213, 255, 254, 218, 181, 156, 175, 111, 135, 117, 125, 135, 144, 157, 252, 252, 165, 255, 255, 204, 179, 179, 204, 129, 121, 105, 127, 129, 139, 254, 250, 241, 164, 253, 255, 82, 183, 161, 163, 129, 120, 107, 124, 120, 124, 247, 254, 218, 175, 148, 69, 119, 67, 167, 164, 148, 131, 125, 120, 57, 73, 62, 67, 105, 63, 65, 90, 82, 57, 123, 131, 108, 102, 96, 64, 60, 67, 61, 67, 65, 88, 56, 57, 73, 66, 72, 96, 111, 100, 75, 75, 68, 69, 66, 62, 63], \"darkFraction\": 0, \"stdLuminance\": 64.30409392934628, \"analysisWidth\": 240, \"meanLuminance\": 159.073624770831, \"analysisHeight\": 320, \"brightFraction\": 0.20016927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 538.9295798455837}, \"createdAt\": \"2026-11-10T02:30:34.594Z\", \"photoHash\": \"c748819db81858c80c9a9f7417ed6a30c0d82290c1a3b48590d4156770fe7c79\", \"superseded\": false, \"sampleIndex\": 1, \"measurements\": {}, \"burstAnalysis\": {\"note\": \"Pemilihan berdasarkan detail, pencahayaan dan perubahan gambar. Ini bukan stabilitas landmark atau pengulangan nilai ukur.\", \"rows\": [{\"index\": 0, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 219, 223, 122, 109, 114, 107, 105, 104, 110, 153, 246, 216, 204, 255, 255, 234, 159, 227, 198, 177, 167, 163, 140, 114, 97, 99, 139, 225, 255, 255, 255, 188, 250, 224, 194, 180, 169, 165, 158, 150, 162, 170, 100, 254, 255, 255, 255, 174, 255, 214, 192, 177, 172, 167, 166, 155, 140, 135, 75, 254, 251, 255, 255, 253, 252, 190, 150, 141, 156, 137, 98, 130, 134, 156, 254, 247, 255, 255, 255, 255, 254, 188, 163, 174, 179, 142, 135, 132, 129, 144, 245, 219, 254, 234, 250, 253, 215, 166, 212, 182, 180, 159, 151, 119, 121, 143, 157, 254, 253, 169, 254, 255, 200, 173, 186, 191, 193, 128, 141, 112, 123, 135, 254, 234, 255, 163, 252, 255, 85, 183, 150, 171, 171, 133, 111, 121, 121, 125, 246, 255, 239, 180, 148, 70, 122, 64, 152, 166, 151, 132, 125, 119, 57, 70, 66, 65, 103, 68, 65, 92, 81, 58, 122, 130, 107, 96, 98, 64, 58, 66, 59, 66, 66, 94, 53, 57, 72, 65, 70, 96, 112, 99, 74, 72, 68, 70, 67, 63, 61], \"darkFraction\": 0, \"stdLuminance\": 64.01172832662922, \"analysisWidth\": 240, \"meanLuminance\": 157.68188170572682, \"analysisHeight\": 320, \"brightFraction\": 0.19272135416666664, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 554.1889526826051}, \"selectionScore\": 102.31930851108866, \"frameDifference\": null}, {\"index\": 1, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 213, 217, 122, 110, 114, 103, 104, 107, 114, 254, 245, 218, 207, 255, 255, 247, 159, 226, 198, 181, 167, 164, 149, 130, 98, 104, 189, 229, 255, 255, 255, 199, 251, 220, 195, 179, 172, 166, 160, 154, 160, 171, 93, 255, 255, 255, 255, 167, 255, 169, 136, 157, 169, 167, 140, 97, 104, 113, 74, 255, 251, 255, 255, 248, 252, 172, 123, 137, 105, 132, 119, 104, 115, 148, 130, 252, 255, 255, 255, 255, 250, 187, 178, 176, 161, 157, 126, 140, 136, 145, 128, 221, 254, 237, 248, 254, 218, 182, 156, 177, 110, 141, 115, 125, 132, 145, 158, 252, 253, 173, 253, 255, 203, 178, 188, 208, 129, 122, 103, 129, 130, 138, 254, 236, 253, 157, 250, 255, 81, 183, 158, 169, 139, 123, 101, 124, 122, 130, 238, 254, 204, 173, 152, 71, 125, 64, 167, 165, 154, 133, 124, 120, 57, 73, 64, 72, 104, 64, 67, 91, 79, 55, 121, 127, 110, 101, 96, 65, 60, 70, 60, 66, 66, 89, 55, 54, 75, 64, 71, 94, 110, 100, 76, 71, 71, 67, 66, 60, 59], \"darkFraction\": 0, \"stdLuminance\": 64.06198522944985, \"analysisWidth\": 240, \"meanLuminance\": 158.89106833593817, \"analysisHeight\": 320, \"brightFraction\": 0.1975390625, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 529.0478336837755}, \"selectionScore\": 101.5740293462105, \"frameDifference\": 0.0349468954248366}, {\"index\": 2, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 218, 226, 122, 110, 115, 105, 104, 106, 115, 245, 244, 217, 204, 255, 255, 246, 168, 228, 198, 179, 167, 166, 147, 123, 99, 106, 216, 225, 255, 255, 255, 199, 252, 219, 193, 178, 170, 167, 159, 153, 162, 170, 91, 255, 255, 255, 255, 163, 255, 168, 132, 160, 171, 165, 136, 97, 106, 118, 78, 255, 253, 255, 255, 178, 247, 186, 120, 137, 108, 135, 120, 104, 106, 149, 134, 253, 255, 255, 255, 255, 248, 186, 180, 179, 162, 154, 144, 140, 136, 146, 102, 229, 253, 213, 255, 254, 218, 181, 156, 175, 111, 135, 117, 125, 135, 144, 157, 252, 252, 165, 255, 255, 204, 179, 179, 204, 129, 121, 105, 127, 129, 139, 254, 250, 241, 164, 253, 255, 82, 183, 161, 163, 129, 120, 107, 124, 120, 124, 247, 254, 218, 175, 148, 69, 119, 67, 167, 164, 148, 131, 125, 120, 57, 73, 62, 67, 105, 63, 65, 90, 82, 57, 123, 131, 108, 102, 96, 64, 60, 67, 61, 67, 65, 88, 56, 57, 73, 66, 72, 96, 111, 100, 75, 75, 68, 69, 66, 62, 63], \"darkFraction\": 0, \"stdLuminance\": 64.30409392934628, \"analysisWidth\": 240, \"meanLuminance\": 159.073624770831, \"analysisHeight\": 320, \"brightFraction\": 0.20016927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 538.9295798455837}, \"selectionScore\": 102.0520596383938, \"frameDifference\": 0.011968954248366014}, {\"index\": 3, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 230, 216, 120, 110, 114, 106, 103, 107, 123, 229, 244, 220, 202, 255, 255, 236, 161, 232, 197, 178, 168, 163, 144, 120, 102, 107, 209, 224, 255, 255, 255, 195, 253, 215, 192, 180, 171, 167, 160, 154, 163, 170, 95, 255, 255, 255, 255, 168, 255, 181, 143, 164, 173, 165, 154, 100, 107, 125, 81, 255, 254, 255, 255, 160, 232, 182, 133, 139, 108, 103, 121, 104, 111, 150, 122, 242, 255, 255, 255, 255, 244, 186, 183, 180, 167, 150, 136, 141, 135, 148, 164, 235, 254, 236, 250, 255, 214, 181, 154, 177, 150, 137, 136, 127, 138, 144, 167, 252, 253, 165, 255, 255, 204, 182, 172, 197, 130, 116, 104, 123, 132, 139, 253, 253, 224, 184, 255, 255, 80, 178, 165, 165, 125, 120, 113, 123, 120, 122, 253, 254, 220, 173, 161, 70, 114, 65, 158, 166, 146, 126, 123, 118, 55, 72, 65, 69, 101, 68, 64, 87, 85, 58, 118, 130, 106, 101, 94, 65, 60, 67, 59, 67, 65, 81, 53, 57, 73, 65, 75, 96, 112, 101, 76, 75, 67, 69, 62, 60, 65], \"darkFraction\": 0, \"stdLuminance\": 64.37153551407151, \"analysisWidth\": 240, \"meanLuminance\": 158.97609537239083, \"analysisHeight\": 320, \"brightFraction\": 0.19998697916666663, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 534.3955895714618}, \"selectionScore\": 101.98357778884449, \"frameDifference\": 0.01497140522875817}, {\"index\": 4, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 216, 233, 121, 110, 111, 106, 101, 107, 118, 219, 244, 217, 205, 255, 255, 253, 187, 233, 199, 178, 168, 164, 143, 119, 101, 106, 210, 227, 255, 255, 255, 195, 253, 217, 190, 180, 170, 168, 159, 154, 162, 171, 94, 255, 255, 255, 255, 172, 255, 181, 149, 166, 173, 167, 156, 102, 105, 125, 78, 255, 253, 255, 255, 222, 242, 166, 143, 141, 107, 100, 120, 116, 119, 150, 104, 140, 255, 255, 255, 255, 247, 184, 181, 180, 157, 150, 137, 141, 135, 147, 120, 221, 254, 212, 255, 254, 218, 181, 153, 179, 152, 141, 138, 127, 137, 146, 164, 253, 253, 166, 254, 255, 205, 179, 176, 198, 128, 119, 104, 121, 131, 138, 255, 251, 235, 167, 254, 255, 80, 181, 165, 165, 130, 122, 110, 123, 120, 131, 252, 254, 208, 176, 142, 70, 117, 64, 161, 166, 146, 126, 122, 119, 56, 73, 67, 67, 100, 69, 65, 92, 84, 56, 118, 129, 105, 101, 95, 66, 60, 68, 59, 69, 62, 82, 53, 59, 76, 65, 74, 99, 113, 99, 75, 75, 66, 70, 63, 61, 64], \"darkFraction\": 0, \"stdLuminance\": 64.34327068857081, \"analysisWidth\": 240, \"meanLuminance\": 159.02655464843, \"analysisHeight\": 320, \"brightFraction\": 0.2002734375, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 548.633728154622}, \"selectionScore\": 102.0290233494044, \"frameDifference\": 0.01401143790849673}], \"valid\": true, \"reasons\": [], \"selectedIndices\": [0, 2, 4]}, \"confirmations\": {}, \"automaticPoints\": {}, \"calibrationSpec\": {\"method\": \"marker\", \"widthMm\": null, \"evidence\": {}, \"heightMm\": null, \"lengthMm\": null, \"referencePlane\": \"\"}, \"measurementContext\": {\"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"brand\": \"Kittycraft\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"pdReference\": \"frame_bridge\"}, \"workingDistanceCm\": 40}}, {\"id\": \"d0a97e7e-050f-4398-8234-8c5ebd9e84f9\", \"view\": \"frontal\", \"width\": 960, \"device\": {\"zoom\": 1, \"depth\": null, \"width\": 960, \"height\": 1280, \"mirrored\": false, \"frameRate\": 30, \"facingMode\": \"user\", \"intrinsics\": null, \"cameraLabel\": \"camera 1, facing front\", \"orientation\": null, \"sourceWidth\": 960, \"sourceHeight\": 1280, \"mainCameraVerifiedByOperator\": true}, \"height\": 1280, \"points\": {}, \"burstId\": \"a1c9ce47-cf76-42b9-b39e-25d1a0a81412\", \"photoId\": \"mp_9db577367ca04a9fa2d5aa6e9fc182fd\", \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 216, 233, 121, 110, 111, 106, 101, 107, 118, 219, 244, 217, 205, 255, 255, 253, 187, 233, 199, 178, 168, 164, 143, 119, 101, 106, 210, 227, 255, 255, 255, 195, 253, 217, 190, 180, 170, 168, 159, 154, 162, 171, 94, 255, 255, 255, 255, 172, 255, 181, 149, 166, 173, 167, 156, 102, 105, 125, 78, 255, 253, 255, 255, 222, 242, 166, 143, 141, 107, 100, 120, 116, 119, 150, 104, 140, 255, 255, 255, 255, 247, 184, 181, 180, 157, 150, 137, 141, 135, 147, 120, 221, 254, 212, 255, 254, 218, 181, 153, 179, 152, 141, 138, 127, 137, 146, 164, 253, 253, 166, 254, 255, 205, 179, 176, 198, 128, 119, 104, 121, 131, 138, 255, 251, 235, 167, 254, 255, 80, 181, 165, 165, 130, 122, 110, 123, 120, 131, 252, 254, 208, 176, 142, 70, 117, 64, 161, 166, 146, 126, 122, 119, 56, 73, 67, 67, 100, 69, 65, 92, 84, 56, 118, 129, 105, 101, 95, 66, 60, 68, 59, 69, 62, 82, 53, 59, 76, 65, 74, 99, 113, 99, 75, 75, 66, 70, 63, 61, 64], \"darkFraction\": 0, \"stdLuminance\": 64.34327068857081, \"analysisWidth\": 240, \"meanLuminance\": 159.02655464843, \"analysisHeight\": 320, \"brightFraction\": 0.2002734375, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 548.633728154622}, \"createdAt\": \"2026-11-10T02:30:34.772Z\", \"photoHash\": \"aedf009c4618cc4c16889d924d1e02b2ba8cf798ed7721f56202c224508e6d4f\", \"superseded\": false, \"sampleIndex\": 2, \"measurements\": {}, \"burstAnalysis\": {\"note\": \"Pemilihan berdasarkan detail, pencahayaan dan perubahan gambar. Ini bukan stabilitas landmark atau pengulangan nilai ukur.\", \"rows\": [{\"index\": 0, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 219, 223, 122, 109, 114, 107, 105, 104, 110, 153, 246, 216, 204, 255, 255, 234, 159, 227, 198, 177, 167, 163, 140, 114, 97, 99, 139, 225, 255, 255, 255, 188, 250, 224, 194, 180, 169, 165, 158, 150, 162, 170, 100, 254, 255, 255, 255, 174, 255, 214, 192, 177, 172, 167, 166, 155, 140, 135, 75, 254, 251, 255, 255, 253, 252, 190, 150, 141, 156, 137, 98, 130, 134, 156, 254, 247, 255, 255, 255, 255, 254, 188, 163, 174, 179, 142, 135, 132, 129, 144, 245, 219, 254, 234, 250, 253, 215, 166, 212, 182, 180, 159, 151, 119, 121, 143, 157, 254, 253, 169, 254, 255, 200, 173, 186, 191, 193, 128, 141, 112, 123, 135, 254, 234, 255, 163, 252, 255, 85, 183, 150, 171, 171, 133, 111, 121, 121, 125, 246, 255, 239, 180, 148, 70, 122, 64, 152, 166, 151, 132, 125, 119, 57, 70, 66, 65, 103, 68, 65, 92, 81, 58, 122, 130, 107, 96, 98, 64, 58, 66, 59, 66, 66, 94, 53, 57, 72, 65, 70, 96, 112, 99, 74, 72, 68, 70, 67, 63, 61], \"darkFraction\": 0, \"stdLuminance\": 64.01172832662922, \"analysisWidth\": 240, \"meanLuminance\": 157.68188170572682, \"analysisHeight\": 320, \"brightFraction\": 0.19272135416666664, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 554.1889526826051}, \"selectionScore\": 102.31930851108866, \"frameDifference\": null}, {\"index\": 1, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 213, 217, 122, 110, 114, 103, 104, 107, 114, 254, 245, 218, 207, 255, 255, 247, 159, 226, 198, 181, 167, 164, 149, 130, 98, 104, 189, 229, 255, 255, 255, 199, 251, 220, 195, 179, 172, 166, 160, 154, 160, 171, 93, 255, 255, 255, 255, 167, 255, 169, 136, 157, 169, 167, 140, 97, 104, 113, 74, 255, 251, 255, 255, 248, 252, 172, 123, 137, 105, 132, 119, 104, 115, 148, 130, 252, 255, 255, 255, 255, 250, 187, 178, 176, 161, 157, 126, 140, 136, 145, 128, 221, 254, 237, 248, 254, 218, 182, 156, 177, 110, 141, 115, 125, 132, 145, 158, 252, 253, 173, 253, 255, 203, 178, 188, 208, 129, 122, 103, 129, 130, 138, 254, 236, 253, 157, 250, 255, 81, 183, 158, 169, 139, 123, 101, 124, 122, 130, 238, 254, 204, 173, 152, 71, 125, 64, 167, 165, 154, 133, 124, 120, 57, 73, 64, 72, 104, 64, 67, 91, 79, 55, 121, 127, 110, 101, 96, 65, 60, 70, 60, 66, 66, 89, 55, 54, 75, 64, 71, 94, 110, 100, 76, 71, 71, 67, 66, 60, 59], \"darkFraction\": 0, \"stdLuminance\": 64.06198522944985, \"analysisWidth\": 240, \"meanLuminance\": 158.89106833593817, \"analysisHeight\": 320, \"brightFraction\": 0.1975390625, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 529.0478336837755}, \"selectionScore\": 101.5740293462105, \"frameDifference\": 0.0349468954248366}, {\"index\": 2, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 218, 226, 122, 110, 115, 105, 104, 106, 115, 245, 244, 217, 204, 255, 255, 246, 168, 228, 198, 179, 167, 166, 147, 123, 99, 106, 216, 225, 255, 255, 255, 199, 252, 219, 193, 178, 170, 167, 159, 153, 162, 170, 91, 255, 255, 255, 255, 163, 255, 168, 132, 160, 171, 165, 136, 97, 106, 118, 78, 255, 253, 255, 255, 178, 247, 186, 120, 137, 108, 135, 120, 104, 106, 149, 134, 253, 255, 255, 255, 255, 248, 186, 180, 179, 162, 154, 144, 140, 136, 146, 102, 229, 253, 213, 255, 254, 218, 181, 156, 175, 111, 135, 117, 125, 135, 144, 157, 252, 252, 165, 255, 255, 204, 179, 179, 204, 129, 121, 105, 127, 129, 139, 254, 250, 241, 164, 253, 255, 82, 183, 161, 163, 129, 120, 107, 124, 120, 124, 247, 254, 218, 175, 148, 69, 119, 67, 167, 164, 148, 131, 125, 120, 57, 73, 62, 67, 105, 63, 65, 90, 82, 57, 123, 131, 108, 102, 96, 64, 60, 67, 61, 67, 65, 88, 56, 57, 73, 66, 72, 96, 111, 100, 75, 75, 68, 69, 66, 62, 63], \"darkFraction\": 0, \"stdLuminance\": 64.30409392934628, \"analysisWidth\": 240, \"meanLuminance\": 159.073624770831, \"analysisHeight\": 320, \"brightFraction\": 0.20016927083333333, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 538.9295798455837}, \"selectionScore\": 102.0520596383938, \"frameDifference\": 0.011968954248366014}, {\"index\": 3, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 230, 216, 120, 110, 114, 106, 103, 107, 123, 229, 244, 220, 202, 255, 255, 236, 161, 232, 197, 178, 168, 163, 144, 120, 102, 107, 209, 224, 255, 255, 255, 195, 253, 215, 192, 180, 171, 167, 160, 154, 163, 170, 95, 255, 255, 255, 255, 168, 255, 181, 143, 164, 173, 165, 154, 100, 107, 125, 81, 255, 254, 255, 255, 160, 232, 182, 133, 139, 108, 103, 121, 104, 111, 150, 122, 242, 255, 255, 255, 255, 244, 186, 183, 180, 167, 150, 136, 141, 135, 148, 164, 235, 254, 236, 250, 255, 214, 181, 154, 177, 150, 137, 136, 127, 138, 144, 167, 252, 253, 165, 255, 255, 204, 182, 172, 197, 130, 116, 104, 123, 132, 139, 253, 253, 224, 184, 255, 255, 80, 178, 165, 165, 125, 120, 113, 123, 120, 122, 253, 254, 220, 173, 161, 70, 114, 65, 158, 166, 146, 126, 123, 118, 55, 72, 65, 69, 101, 68, 64, 87, 85, 58, 118, 130, 106, 101, 94, 65, 60, 67, 59, 67, 65, 81, 53, 57, 73, 65, 75, 96, 112, 101, 76, 75, 67, 69, 62, 60, 65], \"darkFraction\": 0, \"stdLuminance\": 64.37153551407151, \"analysisWidth\": 240, \"meanLuminance\": 158.97609537239083, \"analysisHeight\": 320, \"brightFraction\": 0.19998697916666663, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 534.3955895714618}, \"selectionScore\": 101.98357778884449, \"frameDifference\": 0.01497140522875817}, {\"index\": 4, \"analysis\": {\"score\": 96, \"valid\": true, \"width\": 240, \"height\": 320, \"policy\": {\"laplacianMinimum\": 25, \"maximumLuminance\": 215, \"minimumLuminance\": 45, \"maximumClippedFraction\": 0.35}, \"usable\": true, \"reasons\": [], \"unknown\": [\"headPose\", \"cameraDistance\", \"blink\", \"pupilOcclusion\", \"frameClipping\", \"opticalReflections\"], \"exposure\": \"usable\", \"sharpness\": \"usable\", \"signature\": [255, 255, 255, 216, 233, 121, 110, 111, 106, 101, 107, 118, 219, 244, 217, 205, 255, 255, 253, 187, 233, 199, 178, 168, 164, 143, 119, 101, 106, 210, 227, 255, 255, 255, 195, 253, 217, 190, 180, 170, 168, 159, 154, 162, 171, 94, 255, 255, 255, 255, 172, 255, 181, 149, 166, 173, 167, 156, 102, 105, 125, 78, 255, 253, 255, 255, 222, 242, 166, 143, 141, 107, 100, 120, 116, 119, 150, 104, 140, 255, 255, 255, 255, 247, 184, 181, 180, 157, 150, 137, 141, 135, 147, 120, 221, 254, 212, 255, 254, 218, 181, 153, 179, 152, 141, 138, 127, 137, 146, 164, 253, 253, 166, 254, 255, 205, 179, 176, 198, 128, 119, 104, 121, 131, 138, 255, 251, 235, 167, 254, 255, 80, 181, 165, 165, 130, 122, 110, 123, 120, 131, 252, 254, 208, 176, 142, 70, 117, 64, 161, 166, 146, 126, 122, 119, 56, 73, 67, 67, 100, 69, 65, 92, 84, 56, 118, 129, 105, 101, 95, 66, 60, 68, 59, 69, 62, 82, 53, 59, 76, 65, 74, 99, 113, 99, 75, 75, 66, 70, 63, 61, 64], \"darkFraction\": 0, \"stdLuminance\": 64.34327068857081, \"analysisWidth\": 240, \"meanLuminance\": 159.02655464843, \"analysisHeight\": 320, \"brightFraction\": 0.2002734375, \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"laplacianVariance\": 548.633728154622}, \"selectionScore\": 102.0290233494044, \"frameDifference\": 0.01401143790849673}], \"valid\": true, \"reasons\": [], \"selectedIndices\": [0, 2, 4]}, \"confirmations\": {}, \"automaticPoints\": {}, \"calibrationSpec\": {\"method\": \"marker\", \"widthMm\": null, \"evidence\": {}, \"heightMm\": null, \"lengthMm\": null, \"referencePlane\": \"\"}, \"measurementContext\": {\"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"brand\": \"Kittycraft\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"pdReference\": \"frame_bridge\"}, \"workingDistanceCm\": 40}}], \"consents\": {\"capture\": true, \"thumbnail\": true, \"confirmedAt\": \"2026-11-10T02:29:08.471Z\", \"retainPhotos\": true, \"uploadPhotos\": true}, \"deviceModel\": \"\", \"preparation\": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], \"prescription\": {\"id\": \"rx_8a7793124f314342\", \"od\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"os\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"date\": \"2026-11-09\", \"notes\": \"\", \"source\": \"professional_prescription\", \"pd_left\": null, \"pd_right\": null, \"pd_total\": null}, \"examinationDate\": \"2026-11-10\", \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"workingDistanceCm\": 40, \"manualMeasurements\": {}, \"requiredParameters\": [\"distance_pd\"]}','Pengambilan 3 sampel Frontal — target jauh.','usr_c4b3d45ff0b94ffd','optifit-local-geometry-1.0.0','2026-11-10 02:30:36.859836'),('mr_90517ef3d84d40c7be49090f64ccdbe5','ms_28dd1244f2934db28dd0ae7c8996d442','usr_c4b3d45ff0b94ffd',2,'mr_ac99c69597704000a52067ebe7cb1c94','{\"mode\": \"semi_automatic\", \"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"sku\": \"KC-CBY-AN-YLW\", \"size\": \"XS\", \"brand\": \"Kittycraft\", \"color\": \"Kuning\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"variantId\": \"var_efda2ee981f14664\", \"sourceNote\": \"\", \"pdReference\": \"frame_bridge\", \"sourceScope\": \"product\", \"templeLength\": null, \"sourceVersion\": 1}, \"notes\": \"\", \"results\": {}, \"captures\": [], \"consents\": {\"capture\": true, \"thumbnail\": true, \"confirmedAt\": \"2026-11-09T08:48:00.653Z\", \"retainPhotos\": true, \"uploadPhotos\": true}, \"deviceModel\": \"\", \"preparation\": [0, 2, 4, 6, 8, 10, 9, 7, 5, 3, 1], \"prescription\": {\"id\": \"rx_8a7793124f314342\", \"od\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"os\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"date\": \"2026-11-09\", \"notes\": \"\", \"source\": \"professional_prescription\", \"pd_left\": null, \"pd_right\": null, \"pd_total\": null}, \"examinationDate\": \"2026-11-09\", \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"workingDistanceCm\": 40, \"manualMeasurements\": {}, \"requiredParameters\": [\"distance_pd\", \"near_pd\"]}','Persiapan pengukuran dan pilihan persetujuan pasien dicatat.','usr_c4b3d45ff0b94ffd','optifit-local-geometry-1.0.0','2026-11-09 08:48:00.698021'),('mr_92b7c45678234937adc1aa1be5a14943','ms_8c2a17db7e0c4b2b8a57029c89623953','usr_c4b3d45ff0b94ffd',1,NULL,'{\"mode\": \"semi_automatic\", \"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"sku\": \"KC-CBY-AN-YLW\", \"size\": \"XS\", \"brand\": \"Kittycraft\", \"color\": \"Kuning\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"variantId\": \"var_efda2ee981f14664\", \"sourceNote\": \"\", \"pdReference\": \"frame_bridge\", \"sourceScope\": \"product\", \"templeLength\": null, \"sourceVersion\": 1}, \"notes\": \"\", \"results\": {}, \"captures\": [], \"consents\": {\"capture\": false, \"thumbnail\": false, \"retainPhotos\": false, \"uploadPhotos\": false}, \"deviceModel\": \"\", \"preparation\": [], \"prescription\": {\"id\": \"rx_8a7793124f314342\", \"od\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"os\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"date\": \"2026-11-09\", \"notes\": \"\", \"source\": \"professional_prescription\", \"pd_left\": null, \"pd_right\": null, \"pd_total\": null}, \"examinationDate\": \"2026-11-10\", \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"workingDistanceCm\": 40, \"manualMeasurements\": {}, \"requiredParameters\": [\"distance_pd\"]}','Sesi dibuat dari profil customer dan spesifikasi katalog.','usr_c4b3d45ff0b94ffd','optifit-local-geometry-1.0.0','2026-11-10 02:28:50.526679'),('mr_ac99c69597704000a52067ebe7cb1c94','ms_28dd1244f2934db28dd0ae7c8996d442','usr_c4b3d45ff0b94ffd',1,NULL,'{\"mode\": \"semi_automatic\", \"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"sku\": \"KC-CBY-AN-YLW\", \"size\": \"XS\", \"brand\": \"Kittycraft\", \"color\": \"Kuning\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"variantId\": \"var_efda2ee981f14664\", \"sourceNote\": \"\", \"pdReference\": \"frame_bridge\", \"sourceScope\": \"product\", \"templeLength\": null, \"sourceVersion\": 1}, \"notes\": \"\", \"results\": {}, \"captures\": [], \"consents\": {\"capture\": false, \"thumbnail\": false, \"retainPhotos\": false, \"uploadPhotos\": false}, \"deviceModel\": \"\", \"preparation\": [], \"prescription\": {\"id\": \"rx_8a7793124f314342\", \"od\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"os\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"date\": \"2026-11-09\", \"notes\": \"\", \"source\": \"professional_prescription\", \"pd_left\": null, \"pd_right\": null, \"pd_total\": null}, \"examinationDate\": \"2026-11-09\", \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"workingDistanceCm\": 40, \"manualMeasurements\": {}, \"requiredParameters\": [\"distance_pd\", \"near_pd\"]}','Sesi dibuat dari profil customer dan spesifikasi katalog.','usr_c4b3d45ff0b94ffd','optifit-local-geometry-1.0.0','2026-11-09 08:47:37.881094'),('mr_ba31e276320441b0986f7a0b5d41ebbc','ms_b37caba30ed24aafb66185945883f5f1','usr_c4b3d45ff0b94ffd',1,NULL,'{\"mode\": \"semi_automatic\", \"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"sku\": \"KC-CBY-AN-YLW\", \"size\": \"XS\", \"brand\": \"Kittycraft\", \"color\": \"Kuning\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"variantId\": \"var_efda2ee981f14664\", \"sourceNote\": \"\", \"pdReference\": \"frame_bridge\", \"sourceScope\": \"product\", \"templeLength\": null, \"sourceVersion\": 1}, \"notes\": \"\", \"results\": {}, \"captures\": [], \"consents\": {\"capture\": false, \"thumbnail\": false, \"retainPhotos\": false, \"uploadPhotos\": false}, \"deviceModel\": \"\", \"preparation\": [], \"prescription\": {\"id\": \"rx_8a7793124f314342\", \"od\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"os\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"date\": \"2026-11-09\", \"notes\": \"\", \"source\": \"professional_prescription\", \"pd_left\": null, \"pd_right\": null, \"pd_total\": null}, \"examinationDate\": \"2026-11-10\", \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"workingDistanceCm\": 40, \"manualMeasurements\": {}, \"requiredParameters\": [\"distance_pd\"]}','Sesi dibuat dari profil customer dan spesifikasi katalog.','usr_c4b3d45ff0b94ffd','optifit-local-geometry-1.0.0','2026-11-10 02:33:26.686478'),('mr_cf4815a4e7f346cda3a7202278e238cd','ms_8c2a17db7e0c4b2b8a57029c89623953','usr_c4b3d45ff0b94ffd',2,'mr_92b7c45678234937adc1aa1be5a14943','{\"mode\": \"semi_automatic\", \"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"sku\": \"KC-CBY-AN-YLW\", \"size\": \"XS\", \"brand\": \"Kittycraft\", \"color\": \"Kuning\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"variantId\": \"var_efda2ee981f14664\", \"sourceNote\": \"\", \"pdReference\": \"frame_bridge\", \"sourceScope\": \"product\", \"templeLength\": null, \"sourceVersion\": 1}, \"notes\": \"\", \"results\": {}, \"captures\": [], \"consents\": {\"capture\": true, \"thumbnail\": true, \"confirmedAt\": \"2026-11-10T02:29:08.471Z\", \"retainPhotos\": true, \"uploadPhotos\": true}, \"deviceModel\": \"\", \"preparation\": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], \"prescription\": {\"id\": \"rx_8a7793124f314342\", \"od\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"os\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"date\": \"2026-11-09\", \"notes\": \"\", \"source\": \"professional_prescription\", \"pd_left\": null, \"pd_right\": null, \"pd_total\": null}, \"examinationDate\": \"2026-11-10\", \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"workingDistanceCm\": 40, \"manualMeasurements\": {}, \"requiredParameters\": [\"distance_pd\"]}','Persiapan pengukuran dan pilihan persetujuan pasien dicatat.','usr_c4b3d45ff0b94ffd','optifit-local-geometry-1.0.0','2026-11-10 02:29:10.603296'),('mr_d25fd2e55e644c618d7b561075d2ec5f','ms_f590b06bc5d34192bee59f0371955abe','usr_c4b3d45ff0b94ffd',1,NULL,'{\"mode\": \"semi_automatic\", \"frame\": {\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"sku\": \"KC-CBY-AN-YLW\", \"size\": \"XS\", \"brand\": \"Kittycraft\", \"color\": \"Kuning\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"variantId\": \"var_efda2ee981f14664\", \"sourceNote\": \"\", \"pdReference\": \"frame_bridge\", \"sourceScope\": \"product\", \"templeLength\": null, \"sourceVersion\": 1}, \"notes\": \"\", \"results\": {}, \"captures\": [], \"consents\": {\"capture\": false, \"thumbnail\": false, \"retainPhotos\": false, \"uploadPhotos\": false}, \"deviceModel\": \"\", \"preparation\": [], \"prescription\": {\"id\": \"rx_8a7793124f314342\", \"od\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"os\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"date\": \"2026-11-09\", \"notes\": \"\", \"source\": \"professional_prescription\", \"pd_left\": null, \"pd_right\": null, \"pd_total\": null}, \"examinationDate\": \"2026-11-10\", \"algorithmVersion\": \"optifit-local-geometry-1.0.0\", \"workingDistanceCm\": 40, \"manualMeasurements\": {}, \"requiredParameters\": [\"distance_pd\"]}','Sesi dibuat dari profil customer dan spesifikasi katalog.','usr_c4b3d45ff0b94ffd','optifit-local-geometry-1.0.0','2026-11-10 02:51:22.026926');
/*!40000 ALTER TABLE `meowsurement_revisions` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_revisions_bi` BEFORE INSERT ON `meowsurement_revisions`
FOR EACH ROW
BEGIN
  IF (NEW.`revision_number` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_revisions_number failed'; END IF;
  IF (NEW.`parent_revision_id` IS NULL OR NEW.`parent_revision_id` <> NEW.`id`) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_revisions_parent failed'; END IF;
  IF (NEW.revision_number = 1 AND NEW.parent_revision_id IS NOT NULL) OR (NEW.revision_number > 1 AND NOT EXISTS (SELECT 1 FROM meowsurement_revisions WHERE id = NEW.parent_revision_id AND session_id = NEW.session_id AND user_id = NEW.user_id AND revision_number = NEW.revision_number - 1)) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Revision parent sequence is invalid'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_revisions_bu` BEFORE UPDATE ON `meowsurement_revisions`
FOR EACH ROW
BEGIN
  IF (NEW.`revision_number` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_revisions_number failed'; END IF;
  IF (NEW.`parent_revision_id` IS NULL OR NEW.`parent_revision_id` <> NEW.`id`) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_revisions_parent failed'; END IF;
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_revisions_bd` BEFORE DELETE ON `meowsurement_revisions`
FOR EACH ROW
BEGIN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement history is append-only';
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `meowsurement_sessions`
--

DROP TABLE IF EXISTS `meowsurement_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `meowsurement_sessions` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `variant_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `prescription_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `profile_version` int(11) NOT NULL,
  `spec_version` int(11) NOT NULL,
  `spec_scope` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'product',
  `examination_date` date NOT NULL,
  `status` varchar(24) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'draft',
  `current_revision_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `revision_number` int(11) NOT NULL DEFAULT '0',
  `algorithm_version` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `profile_snapshot` json NOT NULL,
  `frame_snapshot` json NOT NULL,
  `device` json DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_meowsurement_sessions_id_user_id` (`id`,`user_id`),
  KEY `fk_meowsurement_sessions_product_id_variant_id_d94cf60cfd94` (`product_id`,`variant_id`),
  KEY `fk_meowsurement_sessions_prescription_id_user__80515a965ad8` (`prescription_id`,`user_id`),
  KEY `ix_meowsurement_review_queue` (`status`,`updated_at`,`id`),
  KEY `ix_meowsurement_user_history` (`user_id`,`created_at`,`id`),
  KEY `fk_meowsurement_current_revision` (`id`,`user_id`,`current_revision_id`),
  CONSTRAINT `fk_meowsurement_current_revision` FOREIGN KEY (`id`, `user_id`, `current_revision_id`) REFERENCES `meowsurement_revisions` (`session_id`, `user_id`, `id`),
  CONSTRAINT `fk_meowsurement_sessions_prescription_id_user__80515a965ad8` FOREIGN KEY (`prescription_id`, `user_id`) REFERENCES `prescriptions` (`id`, `user_id`),
  CONSTRAINT `fk_meowsurement_sessions_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `fk_meowsurement_sessions_product_id_variant_id_d94cf60cfd94` FOREIGN KEY (`product_id`, `variant_id`) REFERENCES `product_variants` (`product_id`, `id`),
  CONSTRAINT `fk_meowsurement_sessions_user_id_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `meowsurement_sessions`
--

LOCK TABLES `meowsurement_sessions` WRITE;
/*!40000 ALTER TABLE `meowsurement_sessions` DISABLE KEYS */;
INSERT INTO `meowsurement_sessions` VALUES ('ms_28dd1244f2934db28dd0ae7c8996d442','usr_c4b3d45ff0b94ffd','prd_898f994b888240ab','var_efda2ee981f14664','rx_8a7793124f314342',1,1,'product','2026-11-09','draft','mr_90517ef3d84d40c7be49090f64ccdbe5',2,'optifit-local-geometry-1.0.0','{\"name\": \"Mira Admin\", \"email\": \"admin@meoweyes.id\", \"phone\": \"0192389823\", \"gender\": null, \"address\": null, \"user_id\": \"usr_c4b3d45ff0b94ffd\", \"version\": 1, \"birth_date\": \"2026-02-12\", \"prescription\": {\"id\": \"rx_8a7793124f314342\", \"od\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"os\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"date\": \"2026-11-09\", \"notes\": \"\", \"pd_left\": null, \"pd_right\": null, \"pd_total\": null}}','{\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"sku\": \"KC-CBY-AN-YLW\", \"size\": \"XS\", \"brand\": \"Kittycraft\", \"color\": \"Kuning\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"variantId\": \"var_efda2ee981f14664\", \"sourceNote\": \"\", \"pdReference\": \"frame_bridge\", \"sourceScope\": \"product\", \"templeLength\": null, \"sourceVersion\": 1}','{}','2026-11-09 08:48:00.702114','2026-11-09 08:47:37.871889'),('ms_8c2a17db7e0c4b2b8a57029c89623953','usr_c4b3d45ff0b94ffd','prd_898f994b888240ab','var_efda2ee981f14664','rx_8a7793124f314342',1,1,'product','2026-11-10','draft','mr_71f19a7b82764acc8ecdc4e262aa73cb',3,'optifit-local-geometry-1.0.0','{\"name\": \"Mira Admin\", \"email\": \"admin@meoweyes.id\", \"phone\": \"0192389823\", \"gender\": null, \"address\": null, \"user_id\": \"usr_c4b3d45ff0b94ffd\", \"version\": 1, \"birth_date\": \"2026-02-12\", \"prescription\": {\"id\": \"rx_8a7793124f314342\", \"od\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"os\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"date\": \"2026-11-09\", \"notes\": \"\", \"pd_left\": null, \"pd_right\": null, \"pd_total\": null}}','{\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"sku\": \"KC-CBY-AN-YLW\", \"size\": \"XS\", \"brand\": \"Kittycraft\", \"color\": \"Kuning\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"variantId\": \"var_efda2ee981f14664\", \"sourceNote\": \"\", \"pdReference\": \"frame_bridge\", \"sourceScope\": \"product\", \"templeLength\": null, \"sourceVersion\": 1}','{}','2026-11-10 02:30:36.909543','2026-11-10 02:28:50.511820'),('ms_b37caba30ed24aafb66185945883f5f1','usr_c4b3d45ff0b94ffd','prd_898f994b888240ab','var_efda2ee981f14664','rx_8a7793124f314342',1,1,'product','2026-11-10','draft','mr_ba31e276320441b0986f7a0b5d41ebbc',1,'optifit-local-geometry-1.0.0','{\"name\": \"Mira Admin\", \"email\": \"admin@meoweyes.id\", \"phone\": \"0192389823\", \"gender\": null, \"address\": null, \"user_id\": \"usr_c4b3d45ff0b94ffd\", \"version\": 1, \"birth_date\": \"2026-02-12\", \"prescription\": {\"id\": \"rx_8a7793124f314342\", \"od\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"os\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"date\": \"2026-11-09\", \"notes\": \"\", \"pd_left\": null, \"pd_right\": null, \"pd_total\": null}}','{\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"sku\": \"KC-CBY-AN-YLW\", \"size\": \"XS\", \"brand\": \"Kittycraft\", \"color\": \"Kuning\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"variantId\": \"var_efda2ee981f14664\", \"sourceNote\": \"\", \"pdReference\": \"frame_bridge\", \"sourceScope\": \"product\", \"templeLength\": null, \"sourceVersion\": 1}','{}','2026-11-10 02:33:26.689435','2026-11-10 02:33:26.682595'),('ms_f590b06bc5d34192bee59f0371955abe','usr_c4b3d45ff0b94ffd','prd_898f994b888240ab','var_efda2ee981f14664','rx_8a7793124f314342',1,1,'product','2026-11-10','draft','mr_2df7aa062c6541369dc3ea6a9eed0771',3,'optifit-local-geometry-1.0.0','{\"name\": \"Mira Admin\", \"email\": \"admin@meoweyes.id\", \"phone\": \"0192389823\", \"gender\": null, \"address\": null, \"user_id\": \"usr_c4b3d45ff0b94ffd\", \"version\": 1, \"birth_date\": \"2026-02-12\", \"prescription\": {\"id\": \"rx_8a7793124f314342\", \"od\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"os\": {\"add\": null, \"cyl\": 0, \"sph\": 0, \"axis\": null}, \"date\": \"2026-11-09\", \"notes\": \"\", \"pd_left\": null, \"pd_right\": null, \"pd_total\": null}}','{\"a\": 50, \"b\": 40, \"ed\": 60, \"dbl\": 18, \"sku\": \"KC-CBY-AN-YLW\", \"size\": \"XS\", \"brand\": \"Kittycraft\", \"color\": \"Kuning\", \"model\": \"Kittycraft Cubby Anak\", \"productId\": \"prd_898f994b888240ab\", \"symmetric\": true, \"variantId\": \"var_efda2ee981f14664\", \"sourceNote\": \"\", \"pdReference\": \"frame_bridge\", \"sourceScope\": \"product\", \"templeLength\": null, \"sourceVersion\": 1}','{}','2026-11-10 02:56:47.751844','2026-11-10 02:51:22.020532');
/*!40000 ALTER TABLE `meowsurement_sessions` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_sessions_bi` BEFORE INSERT ON `meowsurement_sessions`
FOR EACH ROW
BEGIN
  IF (NEW.`spec_scope` IN ('product','variant')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_spec_scope failed'; END IF;
  IF (NEW.`status` IN ('draft','pending_review','needs_verification','needs_remeasure','approved')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_status failed'; END IF;
  IF (NEW.`profile_version` > 0 AND NEW.`spec_version` > 0 AND NEW.`revision_number` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_versions failed'; END IF;
  IF NEW.status <> 'draft' AND NEW.current_revision_id IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A submitted measurement requires a revision'; END IF;
  IF (NEW.current_revision_id IS NULL AND NEW.revision_number <> 0) OR (NEW.current_revision_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM meowsurement_revisions WHERE id = NEW.current_revision_id AND session_id = NEW.id AND user_id = NEW.user_id AND revision_number = NEW.revision_number)) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Current revision pointer and number must agree'; END IF;
  IF NEW.status = 'approved' AND NOT EXISTS (SELECT 1 FROM meowsurement_reviews WHERE session_id = NEW.id AND user_id = NEW.user_id AND revision_id = NEW.current_revision_id AND decision = 'approved' AND reviewer_id <> NEW.user_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Approval requires an independent stored review'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_meowsurement_sessions_bu` BEFORE UPDATE ON `meowsurement_sessions`
FOR EACH ROW
BEGIN
  IF (NEW.`spec_scope` IN ('product','variant')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_spec_scope failed'; END IF;
  IF (NEW.`status` IN ('draft','pending_review','needs_verification','needs_remeasure','approved')) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_status failed'; END IF;
  IF (NEW.`profile_version` > 0 AND NEW.`spec_version` > 0 AND NEW.`revision_number` >= 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_meowsurement_sessions_versions failed'; END IF;
  IF NOT (NEW.`id` <=> OLD.`id`) OR NOT (NEW.`user_id` <=> OLD.`user_id`) OR NOT (NEW.`product_id` <=> OLD.`product_id`) OR NOT (NEW.`variant_id` <=> OLD.`variant_id`) OR NOT (NEW.`prescription_id` <=> OLD.`prescription_id`) OR NOT (NEW.`profile_version` <=> OLD.`profile_version`) OR NOT (NEW.`spec_version` <=> OLD.`spec_version`) OR NOT (NEW.`spec_scope` <=> OLD.`spec_scope`) OR NOT (NEW.`examination_date` <=> OLD.`examination_date`) OR NOT (NEW.`profile_snapshot` <=> OLD.`profile_snapshot`) OR NOT (NEW.`frame_snapshot` <=> OLD.`frame_snapshot`) OR NOT (NEW.`algorithm_version` <=> OLD.`algorithm_version`) OR NOT (NEW.`created_at` <=> OLD.`created_at`) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Measurement source snapshots are immutable'; END IF;
  IF NEW.status <> 'draft' AND NEW.current_revision_id IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A submitted measurement requires a revision'; END IF;
  IF (NEW.current_revision_id IS NULL AND NEW.revision_number <> 0) OR (NEW.current_revision_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM meowsurement_revisions WHERE id = NEW.current_revision_id AND session_id = NEW.id AND user_id = NEW.user_id AND revision_number = NEW.revision_number)) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Current revision pointer and number must agree'; END IF;
  IF NEW.status = 'approved' AND NOT EXISTS (SELECT 1 FROM meowsurement_reviews WHERE session_id = NEW.id AND user_id = NEW.user_id AND revision_id = NEW.current_revision_id AND decision = 'approved' AND reviewer_id <> NEW.user_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Approval requires an independent stored review'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `migration_issues`
--

DROP TABLE IF EXISTS `migration_issues`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `migration_issues` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `run_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `record_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `source_collection` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source_id` varchar(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `field_name` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `issue_code` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `severity` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'error',
  `explanation` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `resolved_at` datetime(6) DEFAULT NULL,
  `resolved_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `fk_migration_issues_record_id_migration_records_id` (`record_id`),
  KEY `fk_migration_issues_resolved_by_users_user_id` (`resolved_by`),
  KEY `ix_migration_issues_resolution` (`run_id`,`severity`,`resolved_at`),
  CONSTRAINT `fk_migration_issues_record_id_migration_records_id` FOREIGN KEY (`record_id`) REFERENCES `migration_records` (`id`),
  CONSTRAINT `fk_migration_issues_resolved_by_users_user_id` FOREIGN KEY (`resolved_by`) REFERENCES `users` (`user_id`),
  CONSTRAINT `fk_migration_issues_run_id_migration_runs_id` FOREIGN KEY (`run_id`) REFERENCES `migration_runs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `migration_issues`
--

LOCK TABLES `migration_issues` WRITE;
/*!40000 ALTER TABLE `migration_issues` DISABLE KEYS */;
INSERT INTO `migration_issues` VALUES ('imp_00756f7bb1505373a5a5c2c23e271f75','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92fd','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.123563'),('imp_051a77d5239350ac81001ecc6d3216f3','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92ff','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.168910'),('imp_054ba543f6a05e468c7e371144b0d065','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92fb','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.186233'),('imp_1453fced9bb5585282f9325b18a31fe7','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92fc','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.147296'),('imp_1bcec27f434455c380ff6f35691ed1e4','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92fa','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.130258'),('imp_229ff3a60736506691dfec775fec999f','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92f7','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.184360'),('imp_22aabf1c1c5f5aa5a4affcb8bfc5af98','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92fe','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.196398'),('imp_288886a628185e3cac6cf4d49d91f61a','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92f9','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.132372'),('imp_2f86209a124e5c1e8fbf13e0b5b0d939','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139c2615a279f5cd9304','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.136210'),('imp_3061f61d01aa561cb4fa934a30501c5d','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd9300','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.117508'),('imp_32aec1f47463553f9db0a6abd76b4841','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd9301','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.151390'),('imp_37bfcf1b9a9259829e270703ee3b4a1e','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92ff','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.171175'),('imp_3bee8272ae235270baa50d4415f5b7e1','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139c2615a279f5cd9306','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.175221'),('imp_3e2c5eee89dc556a83f766826928c79a','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139a2615a279f5cd92f4','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.190170'),('imp_420584871a8b57898cdab294ded179d6','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd9303','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.164705'),('imp_4afaab677be0593095f24591bb46cdc8','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139a2615a279f5cd92f5','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.110939'),('imp_51a06595c198596aa9eb48f6be5e40b2','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd9301','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.153238'),('imp_5c7534f3c4bd5ddb85c88aaf2d75d528','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92f8','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.180170'),('imp_5d7daedf5f905aa78efce4616b72722f','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139a2615a279f5cd92f5','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.108416'),('imp_5fdb7ca7345c55c2a691672d4d0e1330','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd9302','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.113477'),('imp_609576df49d05980a7ae1da9eae18217','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92fa','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.127810'),('imp_6193b25a801c5a51a0618af63aee5e5d','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92fb','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.188148'),('imp_64ccbf46326a52179868844cd65e49fc','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139c2615a279f5cd9306','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.173199'),('imp_651277714e305af1adaee25546b9038d','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139c2615a279f5cd9305','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.160178'),('imp_684035182466510ba8583f6c98a2fa20','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd9303','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.166779'),('imp_813ded9daaf05e198b060aa92e0d3510','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd9302','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.115670'),('imp_94092e84bd8653f1b7a1b81c6f1045d5','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92f6','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.140129'),('imp_99e8991aa88f517e941afb1f3d5842f2','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd9300','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.119522'),('imp_a4fd1916dc67552ab30175dd4826620d','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92f7','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.182245'),('imp_b18b2db1d05f58ee8183cbfb1ba700fb','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139c2615a279f5cd9305','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.162460'),('imp_b3ccb0bf980451549b6245b190d5e02c','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139c2615a279f5cd9307','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.155180'),('imp_bf67c6faeb285c8581dd527afa749a3e','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92f9','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.134278'),('imp_c480599fc9b25ffe9044892fd9abd70e','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'users','6adb13922615a279f5cd92ae','points_balance','points_without_history','warning','Account balance has no exported point history; preserved without generating earnings.',NULL,NULL,'2026-11-09 08:33:46.105474'),('imp_ca28394f0aaa583886173e9102e07e2c','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92fe','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.193795'),('imp_d8b936d421c659d29e562be2996cd5c0','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92fd','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.121546'),('imp_e2ffecc01741531b8951183a7bbb603a','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139c2615a279f5cd9304','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.138226'),('imp_e5a1e358a08e530eb4ccb045dde9fe4f','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92f8','rating_count','legacy_rating_cache_unreconciled','warning','Cached rating count differs from approved exported reviews; original counters retained, no reviews invented.',NULL,NULL,'2026-11-09 08:33:46.177801'),('imp_f2f39177153e53be877a8cc8bbab1108','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139c2615a279f5cd9307','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.157179'),('imp_f76d09fb3e5159c9b8d3a669cf6e22c1','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92f6','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.144801'),('imp_fa45a6fe3054567a9b222828d4e534c3','imp_3f3bbcc2fc835f8990adadc20e4776e8',NULL,'products','6adb139b2615a279f5cd92fc','sold_count','legacy_sales_cache_unreconciled','warning','Cached sold units differ from paid historical order lines; source counters retained, no purchases invented.',NULL,NULL,'2026-11-09 08:33:46.149454');
/*!40000 ALTER TABLE `migration_issues` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_migration_issues_mysql57_guard` BEFORE INSERT ON `migration_issues`
FOR EACH ROW
BEGIN
  IF (NEW.`severity` IN ('info','warning','error')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_migration_issues_severity failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_migration_issues_mysql57_guard` BEFORE UPDATE ON `migration_issues`
FOR EACH ROW
BEGIN
  IF (NEW.`severity` IN ('info','warning','error')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_migration_issues_severity failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `migration_records`
--

DROP TABLE IF EXISTS `migration_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `migration_records` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `run_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `source_collection` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source_id` varchar(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `source_checksum` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `target_table` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `target_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'planned',
  `verified_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_migration_records_run_id_source_collection__93422a0acfa6` (`run_id`,`source_collection`,`source_id`,`target_table`,`target_id`),
  KEY `ix_migration_records_run_id` (`run_id`),
  KEY `ix_migration_records_source` (`source_collection`,`source_id`),
  CONSTRAINT `fk_migration_records_run_id_migration_runs_id` FOREIGN KEY (`run_id`) REFERENCES `migration_runs` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `migration_records`
--

LOCK TABLES `migration_records` WRITE;
/*!40000 ALTER TABLE `migration_records` DISABLE KEYS */;
INSERT INTO `migration_records` VALUES ('imp_0083240e96a453b7bd55be38bbd7f036','imp_3f3bbcc2fc835f8990adadc20e4776e8','vouchers','6adb139c2615a279f5cd9308','124e2caa36bdcad703b117c10a381f786ac29b68c27a78441b4d2a11a2b0505f','vouchers','{\"id\":\"vch_6f8c69cca5274357\"}','verified','2026-11-09 08:33:51.403486'),('imp_0211159db107570fa4d32bf0e434cfd7','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fc','1aa509af845e57eb89c0d156c5a9100fc5dd6475b873ba348593e2c46a81c14f','product_categories','{\"category_id\":\"cat_f9a1ff0356e24b14\",\"product_id\":\"prd_7ba6732284b649c8\"}','verified','2026-11-09 08:33:51.403486'),('imp_029945cacaae5908af6c61bc809ca91a','imp_3f3bbcc2fc835f8990adadc20e4776e8','roulette_rewards','6adb139c2615a279f5cd930d','f53a0f5b3bed180edb4af8a37ba77cbdfb25497f78790a292a6ff8540e97ee11','roulette_rewards','{\"id\":\"rwd_eb0b0638a4834350\"}','verified','2026-11-09 08:33:51.403486'),('imp_02b593b234ad53e3a0bc04d28f12ac40','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c99','6c85152f027351a1f648387046f32b9c5812ab4f9ba120c92c4cac89168f9087','product_knowledge_bullets','{\"kind\":\"con\",\"knowledge_id\":\"pk_404d444bcfca48eb\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_02b954ecfdff5458aee9c19985326926','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9304','72c657a00698274f9e2acad75d58e4e904834957edab3deebfb9dfcc004669bc','product_categories','{\"category_id\":\"cat_1e21dafc7f3c4850\",\"product_id\":\"prd_52253b4c63584c54\"}','verified','2026-11-09 08:33:51.403486'),('imp_02bb6664923e5b9aad22c5f04b2f47e1','imp_3f3bbcc2fc835f8990adadc20e4776e8','games','6adb139d2615a279f5cd9314','be8568e9a89e01734eaee96536e5f6718ca2a99038efedf32bb47698435075b2','games','{\"id\":\"gm_2ec577929cdc49e7\"}','verified','2026-11-09 08:33:51.403486'),('imp_035a8cd111cf5ae68203eb7c5e45d708','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f9','d17743ca6c89ae66907608bc40a89e067c4d59145d1b789a74396be1f1075d97','product_categories','{\"category_id\":\"cat_fc53a5d7fa854ec3\",\"product_id\":\"prd_401170d2b1564810\"}','verified','2026-11-09 08:33:51.403486'),('imp_03ad4f6e04f954a8b3ff655c85eecb3d','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fe','2f929f71eb2245146d0087ec24c1ca88d19e27f1bae0bdb10f9e9c39b0ef51b3','product_images','{\"product_id\":\"prd_fbef635ed7514c8f\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_03b56834b10c5ae981c35e4c8f4531b7','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9305','4b72b62a603a8c1be8db346326205eba5574ce25ac5b82006721ae4cd0385f45','product_images','{\"product_id\":\"prd_a1911ea875294d3a\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_03e73467cdaf550a867c180a817c51ea','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c97','609e8e795f5ce0f268a90f9fe4eeb8a2382ca5cc7dc76a88f823af825c9618fc','product_knowledge_bullets','{\"kind\":\"con\",\"knowledge_id\":\"pk_2171c71a9c864d1a\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_047229553ec95c099fc4e830a9cf7a9a','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c90','2da3d0df6724022145c4e308095c95f727009470595d0a45b56516e0a84345af','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_e5fa757252be4594\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_04ba9c0642c55e52bff49899f6555891','imp_3f3bbcc2fc835f8990adadc20e4776e8','faq_categories','6adb149bdb3269dbc6aa4ca6','b776a6253ce90845ba252fc50286cd94b69237c232cc9e97ecf0bb64f94fb79c','faq_categories','{\"id\":\"fqc_3eb115998c8f4323\"}','verified','2026-11-09 08:33:51.403486'),('imp_0507a196869f55819a17f239395d201b','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fb','4b1c490983eb289380734be486bd4444d45dfc2b5e8145a313db1b25383bbfd2','product_categories','{\"category_id\":\"cat_40be3187b63b4230\",\"product_id\":\"prd_f27e5e8e2c274d16\"}','verified','2026-11-09 08:33:51.403486'),('imp_0735882e727e55b6bb62ba4862dc9f89','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c97','609e8e795f5ce0f268a90f9fe4eeb8a2382ca5cc7dc76a88f823af825c9618fc','product_knowledges','{\"id\":\"pk_2171c71a9c864d1a\"}','verified','2026-11-09 08:33:51.403486'),('imp_07a5704d2a30563dabb2cc9148a4041a','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9305','4b72b62a603a8c1be8db346326205eba5574ce25ac5b82006721ae4cd0385f45','product_categories','{\"category_id\":\"cat_8e2e391496d84aba\",\"product_id\":\"prd_a1911ea875294d3a\"}','verified','2026-11-09 08:33:51.403486'),('imp_0870bb118e965ea78461286de6e12d7a','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c99','6c85152f027351a1f648387046f32b9c5812ab4f9ba120c92c4cac89168f9087','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_404d444bcfca48eb\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_098b04d46ad557a2936709ba77c6450e','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fe','2f929f71eb2245146d0087ec24c1ca88d19e27f1bae0bdb10f9e9c39b0ef51b3','products','{\"id\":\"prd_fbef635ed7514c8f\"}','verified','2026-11-09 08:33:51.403486'),('imp_09b8c9e7e363515b8be8a5ddf18a0a6c','imp_3f3bbcc2fc835f8990adadc20e4776e8','articles','6adb149adb3269dbc6aa4c8a','886e8b6feb973dfa237ecaef6868f241f51cc340aa27d5856640403f68e4b6de','articles','{\"id\":\"art_238afa86a038481e\"}','verified','2026-11-09 08:33:51.403486'),('imp_0a317c56f4ed5d21a96ce9da19bc2791','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4ca0','fad4f51204519db7554ac5fd7594f323570c23c6a4de9e47b34cb4a0e77e8c80','product_knowledges','{\"id\":\"pk_9b8c345b53e648a3\"}','verified','2026-11-09 08:33:51.403486'),('imp_0b4b93ba41775e1980216571afc1ed77','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9305','4b72b62a603a8c1be8db346326205eba5574ce25ac5b82006721ae4cd0385f45','product_images','{\"product_id\":\"prd_a1911ea875294d3a\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_0c6d26973ab55cae8dc3217b1adb9466','imp_3f3bbcc2fc835f8990adadc20e4776e8','lens_indexes','6adb149adb3269dbc6aa4c83','dc9ffcd3d5b83d774a09e8e63bdd7acda2cd3b3644deed8df26a169355e4085a','lens_indexes','{\"id\":\"lens_0463b1e229e744c7\"}','verified','2026-11-09 08:33:51.403486'),('imp_0c81e4742cdd581d805a7862c956c410','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c9e','47a3eb0a4c2971ad4f1e1974c827a611b472cb4115c1b621863de74303fec149','product_knowledge_bullets','{\"kind\":\"con\",\"knowledge_id\":\"pk_f1e4dd9e53b541fa\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_0c86c517ec91527e8480f4f810835082','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9302','167f810d58d1d45323d3da3c1251cd4578740d00f8e58874e299aa3cc3cc6adc','product_images','{\"product_id\":\"prd_0f674d6c51e34ae1\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_0d36f3ea21555663a1d88fca7d7ffb73','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13972615a279f5cd92d2','96726e67420eba573a6413ffd114a9f4aab03f65631abbb6c6e511f1cdf6f316','categories','{\"id\":\"cat_60c7baaf72ae4567\"}','verified','2026-11-09 08:33:51.403486'),('imp_0d85c7024a155214a08d7342ba3e59f3','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c9a','27fdf42b96b0702d0da67e7e1e55a3ccc83bab76d89a1fbf7e89ba9abc36dd3a','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_75000d7042714b61\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_0d934571b77258e792c90e01010799fb','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f8','4350c494dbea28578ed3ce7b0cf4f60abc1fb5c417d1ef7c007391daa7617f5d','product_badges','{\"badge\":\"new\",\"product_id\":\"prd_df7a0e382fa14177\"}','verified','2026-11-09 08:33:51.403486'),('imp_0e477e46822b59de97e4db1927fd2d49','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f4','1cb15a116079d55768b6230f8d2e1440446235fb6a616f7561bc1b02bb6206ba','product_images','{\"product_id\":\"prd_f2d20822dbce4da6\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_0eb8b1347aa156f59b3cdab60c1c4672','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92ff','defd51450ef4c0ab3cbe8cd19efca51611f47ad390e4fffb89206e854ee80ba3','product_categories','{\"category_id\":\"cat_f9a1ff0356e24b14\",\"product_id\":\"prd_cb46f21f4ef446f3\"}','verified','2026-11-09 08:33:51.403486'),('imp_0efb7655679b5de1a612830f9b832863','imp_3f3bbcc2fc835f8990adadc20e4776e8','cms_pages','6adb149bdb3269dbc6aa4cae','adcbe276252e6b9d6b0e45ac0b22d4e5f044d8971ec565a0f52e1034f5abe1c4','cms_pages','{\"id\":\"pg_58293e119d024a8e\"}','verified','2026-11-09 08:33:51.403486'),('imp_0fc003e3b98d545f89a62f0d0b17d7ca','imp_3f3bbcc2fc835f8990adadc20e4776e8','users','6adb13932615a279f5cd92af','4853ea23a8c570103ec62dba2619a8f81544262053e590ad781dff794145bcfa','user_permissions','{\"permission\":\"article.view\",\"user_id\":\"usr_c071c5fd6a6743b4\"}','verified','2026-11-09 08:33:51.403486'),('imp_0fcbb21688b85d0cb612a8596ad9903f','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fd','f5eaa77ce8f584982113477b55031e7169a62342d3bd51b360f31e28c0cf3cb9','product_categories','{\"category_id\":\"cat_90943cf30dee4098\",\"product_id\":\"prd_26aa3608a7084627\"}','verified','2026-11-09 08:33:51.403486'),('imp_105d934d878851b08ee0893427f39545','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f4','1cb15a116079d55768b6230f8d2e1440446235fb6a616f7561bc1b02bb6206ba','product_categories','{\"category_id\":\"cat_67fb4e6c624a4ce0\",\"product_id\":\"prd_f2d20822dbce4da6\"}','verified','2026-11-09 08:33:51.403486'),('imp_107b40e3376257c5b66e5533843f0f37','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9302','167f810d58d1d45323d3da3c1251cd4578740d00f8e58874e299aa3cc3cc6adc','product_segments','{\"product_id\":\"prd_0f674d6c51e34ae1\",\"segment\":\"Unisex\"}','verified','2026-11-09 08:33:51.403486'),('imp_10a4bdf36f7e552f9bb35964370631bd','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9301','2e009b77e41c61666858216e9bb2cb8cb08222e6dcba8b30b06e6c382b88bfcc','product_categories','{\"category_id\":\"cat_ca9d440a48d64e4b\",\"product_id\":\"prd_898f994b888240ab\"}','verified','2026-11-09 08:33:51.403486'),('imp_12b7bd228a035e86b1aa9b9f363b117f','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fa','60e71e9aafca35f2bbe54134ce638ac819a431553b2031b2c529ab1cec69fc18','product_images','{\"product_id\":\"prd_3e8ddf16743d4901\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_12e6c258e548502e9406b0ab065cf939','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c9d','809bc4110ed38376872d0f601e22c2d44b8803ed1df30c32a79d0e7bb66ee2d7','product_knowledges','{\"id\":\"pk_2414f501c7e3484c\"}','verified','2026-11-09 08:33:51.403486'),('imp_13654dc228ed586cbc349692a3b158f4','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fe','2f929f71eb2245146d0087ec24c1ca88d19e27f1bae0bdb10f9e9c39b0ef51b3','product_categories','{\"category_id\":\"cat_b3f1b68fb5a64695\",\"product_id\":\"prd_fbef635ed7514c8f\"}','verified','2026-11-09 08:33:51.403486'),('imp_1434709d0c815d4b81d935c6d779529b','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f9','d17743ca6c89ae66907608bc40a89e067c4d59145d1b789a74396be1f1075d97','product_segments','{\"product_id\":\"prd_401170d2b1564810\",\"segment\":\"Wanita\"}','verified','2026-11-09 08:33:51.403486'),('imp_14e29331eb245837ac0cd39faa60ac68','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f9','d17743ca6c89ae66907608bc40a89e067c4d59145d1b789a74396be1f1075d97','product_categories','{\"category_id\":\"cat_deabeef8b42b4551\",\"product_id\":\"prd_401170d2b1564810\"}','verified','2026-11-09 08:33:51.403486'),('imp_15258974b9a15edb871b1bc721ed83b2','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13952615a279f5cd92c6','eb929142ab6bccfa9b85a5a203a877b6d9bb7034da3e6d6707eec998724b2301','categories','{\"id\":\"cat_90943cf30dee4098\"}','verified','2026-11-09 08:33:51.403486'),('imp_16d5e384874c5029baa85036a3e785e7','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c96','8111c29f25b20009fb1bfa01f5827da822c0d5bad6a80a12a1f7bb73edc7fa07','product_knowledges','{\"id\":\"pk_fd6c135365384fca\"}','verified','2026-11-09 08:33:51.403486'),('imp_175849a4f78a5a7a949d68af87523509','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9304','72c657a00698274f9e2acad75d58e4e904834957edab3deebfb9dfcc004669bc','product_categories','{\"category_id\":\"cat_0882be6403ac4ec8\",\"product_id\":\"prd_52253b4c63584c54\"}','verified','2026-11-09 08:33:51.403486'),('imp_1768d013a54a592a85341e86687b8c0b','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fd','f5eaa77ce8f584982113477b55031e7169a62342d3bd51b360f31e28c0cf3cb9','products','{\"id\":\"prd_26aa3608a7084627\"}','verified','2026-11-09 08:33:51.403486'),('imp_17c6e4d6467054598a1fcd21ae5ca587','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fc','1aa509af845e57eb89c0d156c5a9100fc5dd6475b873ba348593e2c46a81c14f','products','{\"id\":\"prd_7ba6732284b649c8\"}','verified','2026-11-09 08:33:51.403486'),('imp_17f55a99f7415ec0a0e03a35ed3d9f3a','imp_3f3bbcc2fc835f8990adadc20e4776e8','faqs','6adb149bdb3269dbc6aa4cac','342b13f9b9613c0dd6d99f226a8cddffa9e8a6f34fe05d720d702d3ff252cbfc','faqs','{\"id\":\"faq_781f5b95fd1d42db\"}','verified','2026-11-09 08:33:51.403486'),('imp_1812a355dcc95f1cbdd4eb8d0ec450de','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f6','ef15e6433b59f7d54e4e86ecdea71db1b24217817d347198fb43e77028d19c29','product_variants','{\"id\":\"var_70a6856c0eed4bac\"}','verified','2026-11-09 08:33:51.403486'),('imp_183b7137de0a5071bd9359d5a8fba175','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9300','29b94c88985fa3e50253df0d4d5d9c2622c2bdf996df81376bd0ad1098551ba6','product_variants','{\"id\":\"var_36ccf63e6e9d4f85\"}','verified','2026-11-09 08:33:51.403486'),('imp_1950346b667754a8abe70e35d278e624','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fb','4b1c490983eb289380734be486bd4444d45dfc2b5e8145a313db1b25383bbfd2','product_categories','{\"category_id\":\"cat_f9a1ff0356e24b14\",\"product_id\":\"prd_f27e5e8e2c274d16\"}','verified','2026-11-09 08:33:51.403486'),('imp_1b02a3f26d2258a2af7b9ba11e3dc753','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13942615a279f5cd92b9','133c0f6d12cea7ad99d1dd408152cd6669e804af326207b504629510f2efac29','categories','{\"id\":\"cat_e0992e7915e44e55\"}','verified','2026-11-09 08:33:51.403486'),('imp_1b6bc429c82e59569469f1033a20e70f','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c91','361ee2328fc159c5bd743f2d630320bb52a331f54d1334e1311c8aac583ebcc9','product_knowledges','{\"id\":\"pk_65c16b9faf834556\"}','verified','2026-11-09 08:33:51.403486'),('imp_1b6bda7207b35eda8f5c6b686e45625f','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fe','2f929f71eb2245146d0087ec24c1ca88d19e27f1bae0bdb10f9e9c39b0ef51b3','product_segments','{\"product_id\":\"prd_fbef635ed7514c8f\",\"segment\":\"Wanita\"}','verified','2026-11-09 08:33:51.403486'),('imp_1bef6601e511503ab5b566098233caa6','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f5','5b331b8d2d297f872fc913e0ccd0682a890819708f36b365e37fe3ce3604d748','product_categories','{\"category_id\":\"cat_f9a1ff0356e24b14\",\"product_id\":\"prd_0b61644f093f4610\"}','verified','2026-11-09 08:33:51.403486'),('imp_1d27afd1c7375ed7a14e67d79a4e93d1','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c91','361ee2328fc159c5bd743f2d630320bb52a331f54d1334e1311c8aac583ebcc9','product_knowledge_bullets','{\"kind\":\"con\",\"knowledge_id\":\"pk_65c16b9faf834556\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_1e14971c0f2159c3b4dc5a26d5d081b8','imp_3f3bbcc2fc835f8990adadc20e4776e8','article_categories','6adb149adb3269dbc6aa4c85','fbc9595ec6a06ef49d6f8352ab367f949428a275bbcad250696a0706a33ca85d','article_categories','{\"id\":\"acat_009c491770594be0\"}','verified','2026-11-09 08:33:51.403486'),('imp_1f58d0b8b56c53e1a4112513fee5778d','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fd','f5eaa77ce8f584982113477b55031e7169a62342d3bd51b360f31e28c0cf3cb9','product_categories','{\"category_id\":\"cat_2770f9ae4fb747c5\",\"product_id\":\"prd_26aa3608a7084627\"}','verified','2026-11-09 08:33:51.403486'),('imp_1fc0b98771ee5cb69362a61096e8b79b','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fb','4b1c490983eb289380734be486bd4444d45dfc2b5e8145a313db1b25383bbfd2','product_variants','{\"id\":\"var_8fc85f29df264c82\"}','verified','2026-11-09 08:33:51.403486'),('imp_201471c6b8435901b002cde41ae6de89','imp_3f3bbcc2fc835f8990adadc20e4776e8','faq_categories','6adb149bdb3269dbc6aa4ca7','1330df5ba8231ea69e93f762533cb2793a54006a34da37bf7465d994e2f7e444','faq_categories','{\"id\":\"fqc_02dbe523cec2494f\"}','verified','2026-11-09 08:33:51.403486'),('imp_20c6fca4075552eab365dfa56997796c','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9304','72c657a00698274f9e2acad75d58e4e904834957edab3deebfb9dfcc004669bc','product_images','{\"product_id\":\"prd_52253b4c63584c54\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_21ab9e23479e5381ad9b08e8aac812d0','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fa','60e71e9aafca35f2bbe54134ce638ac819a431553b2031b2c529ab1cec69fc18','product_categories','{\"category_id\":\"cat_deabeef8b42b4551\",\"product_id\":\"prd_3e8ddf16743d4901\"}','verified','2026-11-09 08:33:51.403486'),('imp_2299e33a474f52b4956ad537aa2c25ac','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9301','2e009b77e41c61666858216e9bb2cb8cb08222e6dcba8b30b06e6c382b88bfcc','product_categories','{\"category_id\":\"cat_021c207590d34a14\",\"product_id\":\"prd_898f994b888240ab\"}','verified','2026-11-09 08:33:51.403486'),('imp_231e7aa5e097555ea4c444364782e26f','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fb','4b1c490983eb289380734be486bd4444d45dfc2b5e8145a313db1b25383bbfd2','product_images','{\"product_id\":\"prd_f27e5e8e2c274d16\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_23538319664a5885ba69f9d76f9bc53b','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fd','f5eaa77ce8f584982113477b55031e7169a62342d3bd51b360f31e28c0cf3cb9','product_badges','{\"badge\":\"new\",\"product_id\":\"prd_26aa3608a7084627\"}','verified','2026-11-09 08:33:51.403486'),('imp_236d9569a03952aab09c998d5fd5e401','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fe','2f929f71eb2245146d0087ec24c1ca88d19e27f1bae0bdb10f9e9c39b0ef51b3','product_variants','{\"id\":\"var_f62fe3ab39b84901\"}','verified','2026-11-09 08:33:51.403486'),('imp_2465b62c3455543f8a7d2b4f890b22df','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fb','4b1c490983eb289380734be486bd4444d45dfc2b5e8145a313db1b25383bbfd2','product_segments','{\"product_id\":\"prd_f27e5e8e2c274d16\",\"segment\":\"Pria\"}','verified','2026-11-09 08:33:51.403486'),('imp_26331edc0dc657cba05688a6125e4a0d','imp_3f3bbcc2fc835f8990adadc20e4776e8','article_categories','6adb149adb3269dbc6aa4c87','c84569d093aa1de4d9bc450bde82c4beb4291d5434d57662ac881d4c41716524','article_categories','{\"id\":\"acat_fcb176f9b99a4779\"}','verified','2026-11-09 08:33:51.403486'),('imp_27dedf8b0fb65f878c39f933fd86bfcd','imp_3f3bbcc2fc835f8990adadc20e4776e8','roulette_rewards','6adb139c2615a279f5cd930c','16a978e68cafb7c5c553ae4eb6d38eed4d3d8ddb396cc8ad7587b4d986437a8a','roulette_rewards','{\"id\":\"rwd_1baa16f859764bc6\"}','verified','2026-11-09 08:33:51.403486'),('imp_27ed2899621554e19c0cfe4bb4c2f616','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9307','5045de5b2a7815e44f61c6e223fdcf09628b23692db2561f60c7370a9fc05527','product_segments','{\"product_id\":\"prd_98175a8e8a554c55\",\"segment\":\"Anak-anak\"}','verified','2026-11-09 08:33:51.403486'),('imp_27fe35be553a54769f31754eecbabf98','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9306','946414b12d755aac455846dfe413db5c8f19192b44251ebb1e2faacd5360e7d1','product_categories','{\"category_id\":\"cat_d1cf64ed5dbe41af\",\"product_id\":\"prd_d7b3f4cfe9574460\"}','verified','2026-11-09 08:33:51.403486'),('imp_28a5a6eead55536082efb4cf34924d1f','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c91','361ee2328fc159c5bd743f2d630320bb52a331f54d1334e1311c8aac583ebcc9','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_65c16b9faf834556\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_29f495f05aca5adbb69a798819a7960c','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c94','3e62c94f42566cb38c7e75648e3719323d9585713f38e57310e8595e6699dbef','product_knowledge_bullets','{\"kind\":\"con\",\"knowledge_id\":\"pk_1f46da3523494cc3\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_29f97af9ee6459d68bfd3ba017cef8de','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13992615a279f5cd92e5','0bc451e488e80b7fd1d9c87f66f44c43a8e3833073ae2b3e1cb9951a2baf80fc','categories','{\"id\":\"cat_7af8d1b347834588\"}','verified','2026-11-09 08:33:51.403486'),('imp_2a76dda2091c51a2a36d3bea17345015','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9301','2e009b77e41c61666858216e9bb2cb8cb08222e6dcba8b30b06e6c382b88bfcc','product_images','{\"product_id\":\"prd_898f994b888240ab\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_2a7e49634f835bec831585f77e8840ec','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13952615a279f5cd92c1','49865fa68bc3785fc4db7e27ce90d9ffdfb01d5743f5a86edb3e9202392a8fb6','categories','{\"id\":\"cat_189e70b2854142af\"}','verified','2026-11-09 08:33:51.403486'),('imp_2aa9cc4cd37555349f43c8385d77fc9e','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f8','4350c494dbea28578ed3ce7b0cf4f60abc1fb5c417d1ef7c007391daa7617f5d','product_images','{\"product_id\":\"prd_df7a0e382fa14177\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_2b30f738616e5dbda339c96be5a72c9c','imp_3f3bbcc2fc835f8990adadc20e4776e8','banners_v2','6adb149bdb3269dbc6aa4cb4','4bba46cb74dbe0d7a4cf19417225df3d8d486736f51bdcb102f4ffbf4c991dbe','banners','{\"id\":\"ban_fb632f4b46964abf\"}','verified','2026-11-09 08:33:51.403486'),('imp_2c32bebbbe975795a0869c6b926b6c5e','imp_3f3bbcc2fc835f8990adadc20e4776e8','article_categories','6adb149adb3269dbc6aa4c88','cef6cbadb5333c4209775b5455d04faf1ff63e27f1325e17d75ffffb9f397a0c','article_categories','{\"id\":\"acat_b4b83e879b5641f4\"}','verified','2026-11-09 08:33:51.403486'),('imp_2ce5c9d3197254eab8044977eb325fa1','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9307','5045de5b2a7815e44f61c6e223fdcf09628b23692db2561f60c7370a9fc05527','product_categories','{\"category_id\":\"cat_8e2e391496d84aba\",\"product_id\":\"prd_98175a8e8a554c55\"}','verified','2026-11-09 08:33:51.403486'),('imp_2db37c09089e5aaaa01b4729da1a827b','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9300','29b94c88985fa3e50253df0d4d5d9c2622c2bdf996df81376bd0ad1098551ba6','product_images','{\"product_id\":\"prd_1b6d039b016b4131\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_2f3246a9519a594f82e6e15ee86f45c9','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9307','5045de5b2a7815e44f61c6e223fdcf09628b23692db2561f60c7370a9fc05527','product_variants','{\"id\":\"var_9c6775d5e68247fa\"}','verified','2026-11-09 08:33:51.403486'),('imp_3057946536695943a10a1663f838b884','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13982615a279f5cd92e2','b8bd6637399f56c393e659dea73a09a6cb279edb9570adc2fcf13a317f3ed051','categories','{\"id\":\"cat_7b0baaab7c314bdf\"}','verified','2026-11-09 08:33:51.403486'),('imp_30af3af529ed5a1c9ef805f4f518e21a','imp_3f3bbcc2fc835f8990adadc20e4776e8','contact_settings','6adb149bdb3269dbc6aa4cb3','a22c5ea672c0618e6cb67ce952afee76263453950744633113239566fea5ac69','contact_settings','{\"id\":\"cs_ad4b09c4b3c94ed1\"}','verified','2026-11-09 08:33:51.403486'),('imp_3173c07403d4508090df788bcd567ffa','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f5','5b331b8d2d297f872fc913e0ccd0682a890819708f36b365e37fe3ce3604d748','product_categories','{\"category_id\":\"cat_67fb4e6c624a4ce0\",\"product_id\":\"prd_0b61644f093f4610\"}','verified','2026-11-09 08:33:51.403486'),('imp_327b1f7d3fd357c199d9bf5c949f5d9f','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9305','4b72b62a603a8c1be8db346326205eba5574ce25ac5b82006721ae4cd0385f45','products','{\"id\":\"prd_a1911ea875294d3a\"}','verified','2026-11-09 08:33:51.403486'),('imp_33445d8648b255bfaf55a18fb998a2cc','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c8f','31affefcd535287f3f284e1a5de0aadd13944451834791b4912592ba3fe6a29d','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_30cd2cb1236144ec\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_33ea552546ca5c7baf05c734a0e1d1d6','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9306','946414b12d755aac455846dfe413db5c8f19192b44251ebb1e2faacd5360e7d1','products','{\"id\":\"prd_d7b3f4cfe9574460\"}','verified','2026-11-09 08:33:51.403486'),('imp_3507fdb8058b585eb2d695963f98f01e','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f8','4350c494dbea28578ed3ce7b0cf4f60abc1fb5c417d1ef7c007391daa7617f5d','product_categories','{\"category_id\":\"cat_67fb4e6c624a4ce0\",\"product_id\":\"prd_df7a0e382fa14177\"}','verified','2026-11-09 08:33:51.403486'),('imp_3700518f1e635d50b4a7b3f4b9b44d81','imp_3f3bbcc2fc835f8990adadc20e4776e8','roulette_rewards','6adb139c2615a279f5cd9310','c841eb1ba9387ef21863fb493eb51248a4bbdbd77301031b07f16431ada616e1','roulette_rewards','{\"id\":\"rwd_792cc587a2f04196\"}','verified','2026-11-09 08:33:51.403486'),('imp_395b287ce3c653a5b7dbeafe16efffef','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92ff','defd51450ef4c0ab3cbe8cd19efca51611f47ad390e4fffb89206e854ee80ba3','product_categories','{\"category_id\":\"cat_4ab3c4baea774537\",\"product_id\":\"prd_cb46f21f4ef446f3\"}','verified','2026-11-09 08:33:51.403486'),('imp_3a7e3deeaf3d527da213f391baa58caa','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f8','4350c494dbea28578ed3ce7b0cf4f60abc1fb5c417d1ef7c007391daa7617f5d','product_categories','{\"category_id\":\"cat_f4e07e43d00145b7\",\"product_id\":\"prd_df7a0e382fa14177\"}','verified','2026-11-09 08:33:51.403486'),('imp_3b2433e998ee54d9983fa3494c46c20d','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c99','6c85152f027351a1f648387046f32b9c5812ab4f9ba120c92c4cac89168f9087','product_knowledges','{\"id\":\"pk_404d444bcfca48eb\"}','verified','2026-11-09 08:33:51.403486'),('imp_3b38ae650f3654debb40ff017d879aea','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9302','167f810d58d1d45323d3da3c1251cd4578740d00f8e58874e299aa3cc3cc6adc','product_variants','{\"id\":\"var_78b9cf45d29f47c1\"}','verified','2026-11-09 08:33:51.403486'),('imp_3bf39353f0a05396be6042ac72cf08ee','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fc','1aa509af845e57eb89c0d156c5a9100fc5dd6475b873ba348593e2c46a81c14f','product_segments','{\"product_id\":\"prd_7ba6732284b649c8\",\"segment\":\"Wanita\"}','verified','2026-11-09 08:33:51.403486'),('imp_3c1a387900a054d19c67395ee9003301','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fc','1aa509af845e57eb89c0d156c5a9100fc5dd6475b873ba348593e2c46a81c14f','product_images','{\"product_id\":\"prd_7ba6732284b649c8\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_3ccc783ae1f4558e8f5c032f88183c40','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f9','d17743ca6c89ae66907608bc40a89e067c4d59145d1b789a74396be1f1075d97','product_images','{\"product_id\":\"prd_401170d2b1564810\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_3e0c6be9a9935e46bea280e9b87c4c2c','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9304','72c657a00698274f9e2acad75d58e4e904834957edab3deebfb9dfcc004669bc','products','{\"id\":\"prd_52253b4c63584c54\"}','verified','2026-11-09 08:33:51.403486'),('imp_3e8406d3ea7d5c54ab247396ce1890d8','imp_3f3bbcc2fc835f8990adadc20e4776e8','users','6adb13922615a279f5cd92ae','f9e213b61cab73523afe88bf30c3452c96cac53fd88ecb9a04f01839dc345852','users','{\"user_id\":\"usr_bf93cc1fff4a42d1\"}','verified','2026-11-09 08:33:51.403486'),('imp_3ecb2d5a4e445d6d81631e0a7311e7cb','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c98','7498b0bc5c33866dda2b4ff55aa57a216b00d5178dc143c8243f009ff24862a4','product_knowledges','{\"id\":\"pk_6f3104e2d8424751\"}','verified','2026-11-09 08:33:51.403486'),('imp_3f25fd180425528ab2f96be03a3d4f77','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f8','4350c494dbea28578ed3ce7b0cf4f60abc1fb5c417d1ef7c007391daa7617f5d','product_variants','{\"id\":\"var_6148b0dc13f74e21\"}','verified','2026-11-09 08:33:51.403486'),('imp_3fd5085b8d8b5378b38598bd24bc8c2b','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c95','ee26ece75ded102798f1a211a8732a29deb2737409fb670705667b10e34cf213','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_141aea81440b44e5\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_3ff972c1768555259f27246585617092','imp_3f3bbcc2fc835f8990adadc20e4776e8','games','6adb139d2615a279f5cd9315','b77a9e98e39841dedfb5ded6e12d4ff9704b42c67e911f7b244e87ea160ed794','games','{\"id\":\"gm_9ba1aba0bb5743a1\"}','verified','2026-11-09 08:33:51.403486'),('imp_405a2544a3e855e7bfa72a7d289912e8','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9305','4b72b62a603a8c1be8db346326205eba5574ce25ac5b82006721ae4cd0385f45','product_categories','{\"category_id\":\"cat_71b46a9ac639436a\",\"product_id\":\"prd_a1911ea875294d3a\"}','verified','2026-11-09 08:33:51.403486'),('imp_4494c593e2705195ae0f9c4830769826','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f7','a0ecedd25e902b5f1ceec9fa730cb3b0257117bdbe99c348d8c69ad676af4f7e','product_categories','{\"category_id\":\"cat_c8db483f74e047f0\",\"product_id\":\"prd_f1a4277d4ba84cd1\"}','verified','2026-11-09 08:33:51.403486'),('imp_44b11855076059dcb6ba23d0efd28b0c','imp_3f3bbcc2fc835f8990adadc20e4776e8','users','6adb13932615a279f5cd92af','4853ea23a8c570103ec62dba2619a8f81544262053e590ad781dff794145bcfa','user_permissions','{\"permission\":\"review.moderate\",\"user_id\":\"usr_c071c5fd6a6743b4\"}','verified','2026-11-09 08:33:51.403486'),('imp_455c23d4a35059dc890b39cd2e1c2d03','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13952615a279f5cd92c2','66faf4d77d95833c1dfc80da62701baac2ece1f222847bc2f002b7d6507dfbca','categories','{\"id\":\"cat_2770f9ae4fb747c5\"}','verified','2026-11-09 08:33:51.403486'),('imp_456ec2d436ed5028a5b80d70bdf181a0','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c8e','71bbb0026e16a3a380786e24bab6d09eaf9f5cdb3c0bcd84f528cafceed7eef3','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_80532004402849fe\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_46800323e4d352499efcbb3d0d8abd4a','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13942615a279f5cd92bc','0f6030bd6cca8b2e93f561aba32cc9172c350fbb77566dc353cfdaa254504e14','categories','{\"id\":\"cat_5812461f3eca431b\"}','verified','2026-11-09 08:33:51.403486'),('imp_46f10dc5502b5e1eb8ff2bec1e9bc1bd','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9301','2e009b77e41c61666858216e9bb2cb8cb08222e6dcba8b30b06e6c382b88bfcc','product_variants','{\"id\":\"var_efda2ee981f14664\"}','verified','2026-11-09 08:33:51.403486'),('imp_470ee02739db5e9ba07f8d29b0f8d61a','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f9','d17743ca6c89ae66907608bc40a89e067c4d59145d1b789a74396be1f1075d97','product_images','{\"product_id\":\"prd_401170d2b1564810\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_473af14e987157ed8515aeab74dd2acb','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c8f','31affefcd535287f3f284e1a5de0aadd13944451834791b4912592ba3fe6a29d','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_30cd2cb1236144ec\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_478fce99a46455049b820134a86296f2','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9302','167f810d58d1d45323d3da3c1251cd4578740d00f8e58874e299aa3cc3cc6adc','product_images','{\"product_id\":\"prd_0f674d6c51e34ae1\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_4790b6b1a1415d46ba9356d80e00ddcb','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fa','60e71e9aafca35f2bbe54134ce638ac819a431553b2031b2c529ab1cec69fc18','product_segments','{\"product_id\":\"prd_3e8ddf16743d4901\",\"segment\":\"Wanita\"}','verified','2026-11-09 08:33:51.403486'),('imp_48fff53cf900509ea0eb0742ad0164d2','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fe','2f929f71eb2245146d0087ec24c1ca88d19e27f1bae0bdb10f9e9c39b0ef51b3','product_categories','{\"category_id\":\"cat_f9a1ff0356e24b14\",\"product_id\":\"prd_fbef635ed7514c8f\"}','verified','2026-11-09 08:33:51.403486'),('imp_491d19ed354051b08ce9bffd2aabf794','imp_3f3bbcc2fc835f8990adadc20e4776e8','article_categories','6adb149adb3269dbc6aa4c89','2c521a0a6af5ebe55ee020589a3a642b674522d96ea3f6a60e6c5a47fa34e210','article_categories','{\"id\":\"acat_a3920640b41e4715\"}','verified','2026-11-09 08:33:51.403486'),('imp_4b794ff0bf00572ab6f07800a1cd84fd','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fd','f5eaa77ce8f584982113477b55031e7169a62342d3bd51b360f31e28c0cf3cb9','product_variants','{\"id\":\"var_6f0bfb1702ba4164\"}','verified','2026-11-09 08:33:51.403486'),('imp_4b79d39dec5f53c0a8b8d19c27796497','imp_3f3bbcc2fc835f8990adadc20e4776e8','lens_indexes','6adb1499db3269dbc6aa4c81','baf4e652fb29cd958d0312e5ccaa0ed2411b3c506201b361f58ebddfb71dd4fe','lens_indexes','{\"id\":\"lens_0d3867c1d33941bc\"}','verified','2026-11-09 08:33:51.403486'),('imp_4c0fc385e0d1535aa1326442c3e73ec5','imp_3f3bbcc2fc835f8990adadc20e4776e8','flash_sales','6ae1b6f238d2614e8e285fe0','c7d1e19df6f5c69facd3bc5fdd55d66d87458e22a911b4207fa591acc9f766f9','flash_sales','{\"id\":\"fls_d245f914ad8a4c17\"}','verified','2026-11-09 08:33:51.403486'),('imp_4c2c12200c535d6086431d1d1abe7b44','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f6','ef15e6433b59f7d54e4e86ecdea71db1b24217817d347198fb43e77028d19c29','products','{\"id\":\"prd_75466e5b7e5c4775\"}','verified','2026-11-09 08:33:51.403486'),('imp_4c67257a7c99511fbe205b019572f967','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13982615a279f5cd92db','21f33656f57e4f3e27ef2f5659f240b6a6b82720e20c4da76079e6e25031cbc0','categories','{\"id\":\"cat_64cac2c66f40435e\"}','verified','2026-11-09 08:33:51.403486'),('imp_4df82b59893352cf8672ae26bb1a6463','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f5','5b331b8d2d297f872fc913e0ccd0682a890819708f36b365e37fe3ce3604d748','product_images','{\"product_id\":\"prd_0b61644f093f4610\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_4ed4b2c3e0b85c548fe7b4c2efd06671','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9306','946414b12d755aac455846dfe413db5c8f19192b44251ebb1e2faacd5360e7d1','product_images','{\"product_id\":\"prd_d7b3f4cfe9574460\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_4ee24a6f2b5658a1ab0574eb35fb11cf','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fd','f5eaa77ce8f584982113477b55031e7169a62342d3bd51b360f31e28c0cf3cb9','product_categories','{\"category_id\":\"cat_f9a1ff0356e24b14\",\"product_id\":\"prd_26aa3608a7084627\"}','verified','2026-11-09 08:33:51.403486'),('imp_4fab208da5815cdfb744b9cc1569fb08','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c9b','7e6c401e62b94b5cd467bdae3e57dcd354c06d997c1e7d4069cf80f37d930c39','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_9a8e2684030547c1\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_4fb3e48c5a785adba1f5aa72e2b927ba','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9300','29b94c88985fa3e50253df0d4d5d9c2622c2bdf996df81376bd0ad1098551ba6','products','{\"id\":\"prd_1b6d039b016b4131\"}','verified','2026-11-09 08:33:51.403486'),('imp_50083fcffd765c969d1d155c6bb4c682','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9304','72c657a00698274f9e2acad75d58e4e904834957edab3deebfb9dfcc004669bc','product_segments','{\"product_id\":\"prd_52253b4c63584c54\",\"segment\":\"Unisex\"}','verified','2026-11-09 08:33:51.403486'),('imp_50415656190f549ba730086f8e19ffe4','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13952615a279f5cd92bf','4f9c3a5265f1cc7815314d93ecff91afea2092ac16ca5f062452bc5a2170e03f','categories','{\"id\":\"cat_ee34eb85616b40e4\"}','verified','2026-11-09 08:33:51.403486'),('imp_506477a9764353bb895a32d55a15220a','imp_3f3bbcc2fc835f8990adadc20e4776e8','users','6adb13932615a279f5cd92af','4853ea23a8c570103ec62dba2619a8f81544262053e590ad781dff794145bcfa','user_permissions','{\"permission\":\"article.delete\",\"user_id\":\"usr_c071c5fd6a6743b4\"}','verified','2026-11-09 08:33:51.403486'),('imp_50984fe506895c849dee5d609cdc401e','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f5','5b331b8d2d297f872fc913e0ccd0682a890819708f36b365e37fe3ce3604d748','product_segments','{\"product_id\":\"prd_0b61644f093f4610\",\"segment\":\"Pria\"}','verified','2026-11-09 08:33:51.403486'),('imp_5181648003f05bb69fa964ee2a9eaadc','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9303','04f914093fba7f1ee8838b6c19a934c6795a1b3b280f33dde9910ff644ae9c3d','product_segments','{\"product_id\":\"prd_bce0660e41e84eaa\",\"segment\":\"Unisex\"}','verified','2026-11-09 08:33:51.403486'),('imp_51c01c5d4d4d5b3689210ab3832199a1','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fb','4b1c490983eb289380734be486bd4444d45dfc2b5e8145a313db1b25383bbfd2','products','{\"id\":\"prd_f27e5e8e2c274d16\"}','verified','2026-11-09 08:33:51.403486'),('imp_5221ac807b5d55bbabfce087df3ae5d3','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f4','1cb15a116079d55768b6230f8d2e1440446235fb6a616f7561bc1b02bb6206ba','product_variants','{\"id\":\"var_bf5731b0ea724b44\"}','verified','2026-11-09 08:33:51.403486'),('imp_5241b7ffa14052d0bbdeb7082b182d73','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c96','8111c29f25b20009fb1bfa01f5827da822c0d5bad6a80a12a1f7bb73edc7fa07','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_fd6c135365384fca\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_525ce268c26452f1a951628e1bc30161','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13952615a279f5cd92c0','559a682111e338eb4b8ce51d14c1d62df263e14fcc1a6fd97cdd28e97c631a1b','categories','{\"id\":\"cat_bbe67449c51b4ecd\"}','verified','2026-11-09 08:33:51.403486'),('imp_53232c80b26659608b637f80b75aa775','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f7','a0ecedd25e902b5f1ceec9fa730cb3b0257117bdbe99c348d8c69ad676af4f7e','product_variants','{\"id\":\"var_c7679424d9aa4337\"}','verified','2026-11-09 08:33:51.403486'),('imp_53a3973d7c8a5ee9aa5a8e0d576e36d2','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fa','60e71e9aafca35f2bbe54134ce638ac819a431553b2031b2c529ab1cec69fc18','product_images','{\"product_id\":\"prd_3e8ddf16743d4901\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_57c5cf203cb453fd9b1fab15a2aa746e','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c92','5049ae03e06dc482a1fe196f2a6eade9a73cca86143314f36aa767ce6b4cd75f','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_fb7955a67278482c\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_58ed71f7701956f0b26790005e878a8e','imp_3f3bbcc2fc835f8990adadc20e4776e8','brands','6adb139a2615a279f5cd92f0','3ba010164937f0f4ba8bcd2c2ca9f90e8b5009d2005dff05aae97810a45726a0','brands','{\"id\":\"brd_a1a43360a32847d6\"}','verified','2026-11-09 08:33:51.403486'),('imp_59090014aa435b538e2c43ca20978ba2','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f8','4350c494dbea28578ed3ce7b0cf4f60abc1fb5c417d1ef7c007391daa7617f5d','product_variants','{\"id\":\"var_63049956c6d6400e\"}','verified','2026-11-09 08:33:51.403486'),('imp_5980c33e72775c6eabb7bf69f5e6e87d','imp_3f3bbcc2fc835f8990adadc20e4776e8','users','6adb13932615a279f5cd92af','4853ea23a8c570103ec62dba2619a8f81544262053e590ad781dff794145bcfa','user_permissions','{\"permission\":\"article.update\",\"user_id\":\"usr_c071c5fd6a6743b4\"}','verified','2026-11-09 08:33:51.403486'),('imp_5a60626ea3155230b8717716022e623a','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f4','1cb15a116079d55768b6230f8d2e1440446235fb6a616f7561bc1b02bb6206ba','product_badges','{\"badge\":\"new\",\"product_id\":\"prd_f2d20822dbce4da6\"}','verified','2026-11-09 08:33:51.403486'),('imp_5a65f4414e1c534d9797633323223238','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f4','1cb15a116079d55768b6230f8d2e1440446235fb6a616f7561bc1b02bb6206ba','product_images','{\"product_id\":\"prd_f2d20822dbce4da6\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_5aa8f776076258cf98949af5956c7251','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c98','7498b0bc5c33866dda2b4ff55aa57a216b00d5178dc143c8243f009ff24862a4','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_6f3104e2d8424751\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_5b0686c2c50c53cf95177fe3d1fd95e5','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9305','4b72b62a603a8c1be8db346326205eba5574ce25ac5b82006721ae4cd0385f45','product_segments','{\"product_id\":\"prd_a1911ea875294d3a\",\"segment\":\"Unisex\"}','verified','2026-11-09 08:33:51.403486'),('imp_5d0af86b78cd5f77bf0938cbd4665ebb','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c8e','71bbb0026e16a3a380786e24bab6d09eaf9f5cdb3c0bcd84f528cafceed7eef3','product_knowledge_bullets','{\"kind\":\"con\",\"knowledge_id\":\"pk_80532004402849fe\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_5e0f8a0486245ad6947796f479431b72','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f7','a0ecedd25e902b5f1ceec9fa730cb3b0257117bdbe99c348d8c69ad676af4f7e','product_categories','{\"category_id\":\"cat_f9a1ff0356e24b14\",\"product_id\":\"prd_f1a4277d4ba84cd1\"}','verified','2026-11-09 08:33:51.403486'),('imp_5eb58b99e04e5481a7eb156ad61ce310','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13962615a279f5cd92cc','ab73027cf6429c29f19a419e1ac9d9fc920821ca080e338d07d94505c8b3b2ee','categories','{\"id\":\"cat_4ab3c4baea774537\"}','verified','2026-11-09 08:33:51.403486'),('imp_60560fbfecc657e299c4bf9d4a2c5ba6','imp_3f3bbcc2fc835f8990adadc20e4776e8','faqs','6adb149bdb3269dbc6aa4cad','d55693e23d89a74fb680f7a75f4f07c0d96814c1cc9b3cf6ca82d46a279606ff','faqs','{\"id\":\"faq_ea500b2727fa4989\"}','verified','2026-11-09 08:33:51.403486'),('imp_607d51639081542f82c4271985ace3e1','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f7','a0ecedd25e902b5f1ceec9fa730cb3b0257117bdbe99c348d8c69ad676af4f7e','products','{\"id\":\"prd_f1a4277d4ba84cd1\"}','verified','2026-11-09 08:33:51.403486'),('imp_60e09c2252825705a7ebb2c7b600face','imp_3f3bbcc2fc835f8990adadc20e4776e8','faqs','6adb149bdb3269dbc6aa4ca9','834f481e19865d600069feefa0a0640c70ff6fedca891ef33e19747f6e370c18','faqs','{\"id\":\"faq_ac0e639d34234d37\"}','verified','2026-11-09 08:33:51.403486'),('imp_61a7e4e5d320544ab7b5b7ea907081ec','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c9e','47a3eb0a4c2971ad4f1e1974c827a611b472cb4115c1b621863de74303fec149','product_knowledges','{\"id\":\"pk_f1e4dd9e53b541fa\"}','verified','2026-11-09 08:33:51.403486'),('imp_629cfbd62f735cb5a7dd67c5ee2c9091','imp_3f3bbcc2fc835f8990adadc20e4776e8','faq_categories','6adb149bdb3269dbc6aa4ca5','7468821a470d3948a0bcbdd8a457f4693feddefdf5aa9c6711900147ca500e25','faq_categories','{\"id\":\"fqc_47ce480bad944c1b\"}','verified','2026-11-09 08:33:51.403486'),('imp_62e2910bc08c5395945ee86363a6632a','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13962615a279f5cd92cd','ce12ef89cbdd0424ce4a6f35159da5bd7d36257223ee06a8ae981dd16f9fa10c','categories','{\"id\":\"cat_c67d33f78ebb4d52\"}','verified','2026-11-09 08:33:51.403486'),('imp_62fee5edbafd5f8cbe17fcd28be4f0bc','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92ff','defd51450ef4c0ab3cbe8cd19efca51611f47ad390e4fffb89206e854ee80ba3','product_segments','{\"product_id\":\"prd_cb46f21f4ef446f3\",\"segment\":\"Pria\"}','verified','2026-11-09 08:33:51.403486'),('imp_63ad32d585b150398fd35dc455af7dc7','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9305','4b72b62a603a8c1be8db346326205eba5574ce25ac5b82006721ae4cd0385f45','product_images','{\"product_id\":\"prd_a1911ea875294d3a\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_640b768f3a2555f2b53fc71d780383d4','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c9a','27fdf42b96b0702d0da67e7e1e55a3ccc83bab76d89a1fbf7e89ba9abc36dd3a','product_knowledges','{\"id\":\"pk_75000d7042714b61\"}','verified','2026-11-09 08:33:51.403486'),('imp_64d03f38ad6e55de9afe682b4bfd332a','imp_3f3bbcc2fc835f8990adadc20e4776e8','banners_v2','6adb149bdb3269dbc6aa4cb5','aa1abdfca5bb18ce77b63e7336e2175be419bb4beaf658b6bb34da68b6b7d753','banners','{\"id\":\"ban_30728dfde93641cb\"}','verified','2026-11-09 08:33:51.403486'),('imp_6691e2cf253f5785be5ed9389b5b3575','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c90','2da3d0df6724022145c4e308095c95f727009470595d0a45b56516e0a84345af','product_knowledges','{\"id\":\"pk_e5fa757252be4594\"}','verified','2026-11-09 08:33:51.403486'),('imp_670e8adf2f70536198af2dca3c7feeca','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c90','2da3d0df6724022145c4e308095c95f727009470595d0a45b56516e0a84345af','product_knowledge_bullets','{\"kind\":\"con\",\"knowledge_id\":\"pk_e5fa757252be4594\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_69eb533013be57388ef9caaa14947b67','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13982615a279f5cd92e3','427c638d97439ca6efb26a206fb881847ee16d8b317a7170a4a2cd1a50356694','categories','{\"id\":\"cat_021c207590d34a14\"}','verified','2026-11-09 08:33:51.403486'),('imp_700bb8345190545ea59af251a9d615b9','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149bdb3269dbc6aa4ca2','5567256f116dc663254a3ffcf67baa6b5e98da0a78538fdfb668151c4b3353c7','product_knowledges','{\"id\":\"pk_fa4a13b51ee54cd1\"}','verified','2026-11-09 08:33:51.403486'),('imp_704a4e790e3d58ff98e3d49d735c5e9c','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13972615a279f5cd92d3','846c2d2f51575eb9b4e3f15408d2267f904984e668c1666be2ba975f99d3a426','categories','{\"id\":\"cat_c7c70e7520d7451c\"}','verified','2026-11-09 08:33:51.403486'),('imp_70e216b44d015984b0ce457cb241f163','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c94','3e62c94f42566cb38c7e75648e3719323d9585713f38e57310e8595e6699dbef','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_1f46da3523494cc3\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_7185c21ad6da5d6aa17425f882172cbf','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f8','4350c494dbea28578ed3ce7b0cf4f60abc1fb5c417d1ef7c007391daa7617f5d','product_categories','{\"category_id\":\"cat_f9a1ff0356e24b14\",\"product_id\":\"prd_df7a0e382fa14177\"}','verified','2026-11-09 08:33:51.403486'),('imp_7297b55cdcc759c4b1cb843ae69b41fb','imp_3f3bbcc2fc835f8990adadc20e4776e8','articles','6adb149adb3269dbc6aa4c8b','5b1b630dd66bdbdf6f759b48d1577474ce611b99bfc0490fc3715fa38f1fea8e','articles','{\"id\":\"art_73495cf070d543e9\"}','verified','2026-11-09 08:33:51.403486'),('imp_72fcb020a5d45c39950ed600e0a269e9','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fe','2f929f71eb2245146d0087ec24c1ca88d19e27f1bae0bdb10f9e9c39b0ef51b3','product_images','{\"product_id\":\"prd_fbef635ed7514c8f\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_746575cc38655f3aa4041af92d848d16','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f5','5b331b8d2d297f872fc913e0ccd0682a890819708f36b365e37fe3ce3604d748','product_variants','{\"id\":\"var_71ec04bcd9b44d10\"}','verified','2026-11-09 08:33:51.403486'),('imp_749814157b625feab5f1fa6744e0d811','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fd','f5eaa77ce8f584982113477b55031e7169a62342d3bd51b360f31e28c0cf3cb9','product_images','{\"product_id\":\"prd_26aa3608a7084627\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_74dd136cab5355ee98404985d912a8c0','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13982615a279f5cd92e0','401dc4aae79a035fe5834429b35f9821256226377a09d5baecbae3e9be4848c1','categories','{\"id\":\"cat_ca9d440a48d64e4b\"}','verified','2026-11-09 08:33:51.403486'),('imp_74e2298711b757e2b421832b5b808fa9','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13972615a279f5cd92d5','3ef6f5208b1004c5541ef872b374823a658fb8d95c7f1b2b4bff06c707d05aec','categories','{\"id\":\"cat_ed2ac43616284c5e\"}','verified','2026-11-09 08:33:51.403486'),('imp_76cbafb47e2152bf942bb2e5d868b18f','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13972615a279f5cd92d4','40d1afead500254cfe571b781fe51e272870d4a077b5ab9d2fef76f9825f7201','categories','{\"id\":\"cat_2b537e48483a4811\"}','verified','2026-11-09 08:33:51.403486'),('imp_76e8942e74015020a7bd73c3f00895dd','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c97','609e8e795f5ce0f268a90f9fe4eeb8a2382ca5cc7dc76a88f823af825c9618fc','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_2171c71a9c864d1a\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_77006487226b5f31a9fb72b9c5927779','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13982615a279f5cd92dd','01aff5605ee667dcf4a78450fc98ed2b4fc834f063f59d0a0fc0610e4c53b327','categories','{\"id\":\"cat_aa49c313f65e4610\"}','verified','2026-11-09 08:33:51.403486'),('imp_775d799c0e135c3692c412b42a63bc40','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fa','60e71e9aafca35f2bbe54134ce638ac819a431553b2031b2c529ab1cec69fc18','products','{\"id\":\"prd_3e8ddf16743d4901\"}','verified','2026-11-09 08:33:51.403486'),('imp_7871fc96f33e53b2a1e56ae7040a7f93','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb139a2615a279f5cd92ed','61bda5b41782b91c43d9c61d919606bc30ece176cec39a6fac83a494de07e759','categories','{\"id\":\"cat_3502c02ad4ac4d8d\"}','verified','2026-11-09 08:33:51.403486'),('imp_7b93745fd3d158138932cff50ac5f358','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f5','5b331b8d2d297f872fc913e0ccd0682a890819708f36b365e37fe3ce3604d748','product_images','{\"product_id\":\"prd_0b61644f093f4610\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_7c9e6711690753388df4833b078eb29c','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9302','167f810d58d1d45323d3da3c1251cd4578740d00f8e58874e299aa3cc3cc6adc','product_badges','{\"badge\":\"bestseller\",\"product_id\":\"prd_0f674d6c51e34ae1\"}','verified','2026-11-09 08:33:51.403486'),('imp_7d7ea5d3904554fea45b28c3212dee68','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9300','29b94c88985fa3e50253df0d4d5d9c2622c2bdf996df81376bd0ad1098551ba6','product_segments','{\"product_id\":\"prd_1b6d039b016b4131\",\"segment\":\"Pria\"}','verified','2026-11-09 08:33:51.403486'),('imp_7e7bdc86326b541eaa4b6f99547a3390','imp_3f3bbcc2fc835f8990adadc20e4776e8','contact_settings','6adb149bdb3269dbc6aa4cb3','a22c5ea672c0618e6cb67ce952afee76263453950744633113239566fea5ac69','whatsapp_settings','{\"id\":1}','verified','2026-11-09 08:33:51.403486'),('imp_7e89323e7b25580884b58d1056a853e8','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c93','7f41648b882b00a9411a55010d6d6904ef29cd07723f472a4b6a4ad276b8d9d3','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_c88ef6931b2943f5\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_7eaf8a4a342f574ca79e11f3f3053a0a','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f6','ef15e6433b59f7d54e4e86ecdea71db1b24217817d347198fb43e77028d19c29','product_categories','{\"category_id\":\"cat_f9a1ff0356e24b14\",\"product_id\":\"prd_75466e5b7e5c4775\"}','verified','2026-11-09 08:33:51.403486'),('imp_7ff4c76105665a569698a038c23ed460','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13942615a279f5cd92b4','23761f5e67a04bc77b0e3482a6948dc8726d79c8f3f62869e00ae3a7df067585','categories','{\"id\":\"cat_4bb0610322c04fae\"}','verified','2026-11-09 08:33:51.403486'),('imp_81e2c5d4302b5c35a1c02cd98a801eee','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c8e','71bbb0026e16a3a380786e24bab6d09eaf9f5cdb3c0bcd84f528cafceed7eef3','product_knowledges','{\"id\":\"pk_80532004402849fe\"}','verified','2026-11-09 08:33:51.403486'),('imp_83c95e47af715aa1be2dea5675623dbc','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c8e','71bbb0026e16a3a380786e24bab6d09eaf9f5cdb3c0bcd84f528cafceed7eef3','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_80532004402849fe\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_83e8920c5ac85d77a25896a8a7622d79','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fc','1aa509af845e57eb89c0d156c5a9100fc5dd6475b873ba348593e2c46a81c14f','product_categories','{\"category_id\":\"cat_ee34eb85616b40e4\",\"product_id\":\"prd_7ba6732284b649c8\"}','verified','2026-11-09 08:33:51.403486'),('imp_83eb2dddec545c99887c340d9d42c8fc','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fc','1aa509af845e57eb89c0d156c5a9100fc5dd6475b873ba348593e2c46a81c14f','product_images','{\"product_id\":\"prd_7ba6732284b649c8\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_8439f5752d1950749844738b216518d6','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9300','29b94c88985fa3e50253df0d4d5d9c2622c2bdf996df81376bd0ad1098551ba6','product_badges','{\"badge\":\"new\",\"product_id\":\"prd_1b6d039b016b4131\"}','verified','2026-11-09 08:33:51.403486'),('imp_84a48a6f0bfb5066a30261b4e5e89e68','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9300','29b94c88985fa3e50253df0d4d5d9c2622c2bdf996df81376bd0ad1098551ba6','product_images','{\"product_id\":\"prd_1b6d039b016b4131\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_855f40ed64515399826957b2bf57e5ee','imp_3f3bbcc2fc835f8990adadc20e4776e8','cms_pages','6adb149bdb3269dbc6aa4caf','9546d87356bcf2675f986d9cbebdc7bcc29d710bcce4461185b0a7eaad61f6b0','cms_pages','{\"id\":\"pg_88defba273fe49ec\"}','verified','2026-11-09 08:33:51.403486'),('imp_856e6f6d32045539bbdf9993b6795a00','imp_3f3bbcc2fc835f8990adadc20e4776e8','articles','6adb149adb3269dbc6aa4c8d','4de8da8c899e0375468734aded475aaa6ab219e719fd199dbd2d3960e15ce945','articles','{\"id\":\"art_e8f24839239a4b0c\"}','verified','2026-11-09 08:33:51.403486'),('imp_8573e21413455ca3bbc9cde67de848ba','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fa','60e71e9aafca35f2bbe54134ce638ac819a431553b2031b2c529ab1cec69fc18','product_variants','{\"id\":\"var_161a6e6f4ae4495a\"}','verified','2026-11-09 08:33:51.403486'),('imp_857ab4ef8b215967adee4310811262ce','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fe','2f929f71eb2245146d0087ec24c1ca88d19e27f1bae0bdb10f9e9c39b0ef51b3','product_images','{\"product_id\":\"prd_fbef635ed7514c8f\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_8598d2314dd1517a948b95def7dfa6fa','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92ff','defd51450ef4c0ab3cbe8cd19efca51611f47ad390e4fffb89206e854ee80ba3','product_categories','{\"category_id\":\"cat_c67d33f78ebb4d52\",\"product_id\":\"prd_cb46f21f4ef446f3\"}','verified','2026-11-09 08:33:51.403486'),('imp_867697ebcee659168a51a2eadd11caa7','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13952615a279f5cd92c7','6c65ff741b370c8352c6a59e65ff991279cfe64786a5e3185c0ce8abf603491b','categories','{\"id\":\"cat_b3f1b68fb5a64695\"}','verified','2026-11-09 08:33:51.403486'),('imp_8708c1ef185a5e8498e596102ac7aa5c','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c9b','7e6c401e62b94b5cd467bdae3e57dcd354c06d997c1e7d4069cf80f37d930c39','product_knowledges','{\"id\":\"pk_9a8e2684030547c1\"}','verified','2026-11-09 08:33:51.403486'),('imp_870f43ea1c035445880e14524a82ee69','imp_3f3bbcc2fc835f8990adadc20e4776e8','lens_indexes','6adb149adb3269dbc6aa4c82','8015613229b812b5a67275fb044d9b447c0b54ba56404425fe6940865e0f4fd0','lens_indexes','{\"id\":\"lens_ce077e4b7116476e\"}','verified','2026-11-09 08:33:51.403486'),('imp_872c2f77127f5366ab308504858f8c43','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13942615a279f5cd92bd','167d11e287ffa17acbd95a2b7aa38af7b147411efcdd2765b228f9ea21a3bad3','categories','{\"id\":\"cat_7c376dc73fc34a3f\"}','verified','2026-11-09 08:33:51.403486'),('imp_8816a57ab7a057c29323753229a7a899','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f8','4350c494dbea28578ed3ce7b0cf4f60abc1fb5c417d1ef7c007391daa7617f5d','product_segments','{\"product_id\":\"prd_df7a0e382fa14177\",\"segment\":\"Anak-anak\"}','verified','2026-11-09 08:33:51.403486'),('imp_8970949327c052a2a158b8ac78d8ded4','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f6','ef15e6433b59f7d54e4e86ecdea71db1b24217817d347198fb43e77028d19c29','product_images','{\"product_id\":\"prd_75466e5b7e5c4775\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_89f5fc6f644c50eda3b8ccb7367b5f12','imp_3f3bbcc2fc835f8990adadc20e4776e8','article_categories','6adb149adb3269dbc6aa4c86','aa21590038d40a6d260e81a938bda61aa0cb3b87c6f2a5de515103a4f92e728e','article_categories','{\"id\":\"acat_602dcfc180cb4af3\"}','verified','2026-11-09 08:33:51.403486'),('imp_8a2c8c23dd20573facfca69e584fe2bd','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f7','a0ecedd25e902b5f1ceec9fa730cb3b0257117bdbe99c348d8c69ad676af4f7e','product_segments','{\"product_id\":\"prd_f1a4277d4ba84cd1\",\"segment\":\"Wanita\"}','verified','2026-11-09 08:33:51.403486'),('imp_8a9220fcdb6f58f4a4d8800980d98d6e','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9301','2e009b77e41c61666858216e9bb2cb8cb08222e6dcba8b30b06e6c382b88bfcc','product_categories','{\"category_id\":\"cat_f9a1ff0356e24b14\",\"product_id\":\"prd_898f994b888240ab\"}','verified','2026-11-09 08:33:51.403486'),('imp_8aa1a7406a67545abd3a71fdffbdba47','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f7','a0ecedd25e902b5f1ceec9fa730cb3b0257117bdbe99c348d8c69ad676af4f7e','product_images','{\"product_id\":\"prd_f1a4277d4ba84cd1\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_8ac155b2ebc75849b60bd771025363cc','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13962615a279f5cd92cb','633a88cb26da94e76cd138e689a6ad378f9fff1f2340cc1512240e1211d2e458','categories','{\"id\":\"cat_6e7e4df78fbf4fff\"}','verified','2026-11-09 08:33:51.403486'),('imp_8ac18a1091b55631bd309257f3428909','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92ff','defd51450ef4c0ab3cbe8cd19efca51611f47ad390e4fffb89206e854ee80ba3','product_variants','{\"id\":\"var_4cba838eca4f4c77\"}','verified','2026-11-09 08:33:51.403486'),('imp_8dc4298e75195301af48aff889ab61f4','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f6','ef15e6433b59f7d54e4e86ecdea71db1b24217817d347198fb43e77028d19c29','product_badges','{\"badge\":\"bestseller\",\"product_id\":\"prd_75466e5b7e5c4775\"}','verified','2026-11-09 08:33:51.403486'),('imp_8dcc4256e12059f7ba4eb9b2094daeca','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9306','946414b12d755aac455846dfe413db5c8f19192b44251ebb1e2faacd5360e7d1','product_badges','{\"badge\":\"new\",\"product_id\":\"prd_d7b3f4cfe9574460\"}','verified','2026-11-09 08:33:51.403486'),('imp_8e11bf72297d5a5a8fc2fc09f97d9853','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13962615a279f5cd92c8','4c20c60610145730697d8080c48beccde57fa324d1cd6736f27c046cce064079','categories','{\"id\":\"cat_22a34c693a8842d3\"}','verified','2026-11-09 08:33:51.403486'),('imp_8e67507fc4445405b5e25da9d9dfc56c','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c93','7f41648b882b00a9411a55010d6d6904ef29cd07723f472a4b6a4ad276b8d9d3','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_c88ef6931b2943f5\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_8e7b1913780e5f98a48475b2d76067a8','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f5','5b331b8d2d297f872fc913e0ccd0682a890819708f36b365e37fe3ce3604d748','product_categories','{\"category_id\":\"cat_4bb0610322c04fae\",\"product_id\":\"prd_0b61644f093f4610\"}','verified','2026-11-09 08:33:51.403486'),('imp_8f1311f36c745c70a49468ab63476352','imp_3f3bbcc2fc835f8990adadc20e4776e8','brands','6adb139a2615a279f5cd92ee','e01d4d48670269c1f77b211a199082a82180028545eae79b6166035eb4251dbb','brands','{\"id\":\"brd_b1845bf573734de8\"}','verified','2026-11-09 08:33:51.403486'),('imp_8f850918c81d5dfe996d8dfc3c98b9db','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9302','167f810d58d1d45323d3da3c1251cd4578740d00f8e58874e299aa3cc3cc6adc','products','{\"id\":\"prd_0f674d6c51e34ae1\"}','verified','2026-11-09 08:33:51.403486'),('imp_8f90e370e0a75a78a2451b2a1684ff10','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9302','167f810d58d1d45323d3da3c1251cd4578740d00f8e58874e299aa3cc3cc6adc','product_categories','{\"category_id\":\"cat_1e21dafc7f3c4850\",\"product_id\":\"prd_0f674d6c51e34ae1\"}','verified','2026-11-09 08:33:51.403486'),('imp_90179aad8e6456398667d0f62ae706ed','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fb','4b1c490983eb289380734be486bd4444d45dfc2b5e8145a313db1b25383bbfd2','product_categories','{\"category_id\":\"cat_7c376dc73fc34a3f\",\"product_id\":\"prd_f27e5e8e2c274d16\"}','verified','2026-11-09 08:33:51.403486'),('imp_902bceab913855d19d672e735d63aee5','imp_3f3bbcc2fc835f8990adadc20e4776e8','cms_pages','6adb149bdb3269dbc6aa4cb1','adbd7acb615f6794589949964cf252be7fe728cd89d357eb663146287fc67074','cms_pages','{\"id\":\"pg_f94f79e60bce4d25\"}','verified','2026-11-09 08:33:51.403486'),('imp_902d280aaf7e54cea2f2066062771475','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13972615a279f5cd92d7','95577b25c2938e8de76ca7d4fb331ae1adf22a75c852c706352a79268c890781','categories','{\"id\":\"cat_57160db9e3b14d10\"}','verified','2026-11-09 08:33:51.403486'),('imp_903f30193b8c58e19cc524404b1b0cca','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f6','ef15e6433b59f7d54e4e86ecdea71db1b24217817d347198fb43e77028d19c29','product_categories','{\"category_id\":\"cat_67fb4e6c624a4ce0\",\"product_id\":\"prd_75466e5b7e5c4775\"}','verified','2026-11-09 08:33:51.403486'),('imp_90acababe8bf58dea84e35f5fee84885','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13972615a279f5cd92d6','290708964bad30e898ae4c3a515e288340681e3652ee4227673288dfb9a74a63','categories','{\"id\":\"cat_2278c39968f74d39\"}','verified','2026-11-09 08:33:51.403486'),('imp_90b3f37993565a568d87d7e34e7b655b','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c9c','a9410587b48dcf5fe02b35b375e886ceef1e6d1a0d9f9f52e91cbd5bf1e715e1','product_knowledges','{\"id\":\"pk_ecae6a569bd84944\"}','verified','2026-11-09 08:33:51.403486'),('imp_925f2747e1435ab285b772a5c10be903','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92ff','defd51450ef4c0ab3cbe8cd19efca51611f47ad390e4fffb89206e854ee80ba3','product_images','{\"product_id\":\"prd_cb46f21f4ef446f3\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_9262c888e19855eeb973021baa6ed7be','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13992615a279f5cd92e4','26b59a71b21cd6c413261415427b23ff43a424f16daa44cae6d6a24b16380c6a','categories','{\"id\":\"cat_ff7394b7bb934c85\"}','verified','2026-11-09 08:33:51.403486'),('imp_94e30139b04d57f393e6ff780dbb5e60','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149bdb3269dbc6aa4ca1','40d06e43d41725f6c79d02325a77b8f239935107ddb6f86b13688535cddc3f11','product_knowledges','{\"id\":\"pk_e85a7626363549ec\"}','verified','2026-11-09 08:33:51.403486'),('imp_95acededbd9655dcaebdd3a9d9517669','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13962615a279f5cd92d0','0633148ca7b7924c010e9655dd104464a86e525ba212cb99be9c17eefe6adb48','categories','{\"id\":\"cat_f7ac52c8052b4254\"}','verified','2026-11-09 08:33:51.403486'),('imp_965cf48559a7576fa44d3390b9ef219e','imp_3f3bbcc2fc835f8990adadc20e4776e8','roulette_rewards','6adb139c2615a279f5cd930f','608eb3ceb2d5a6e06a64442e1c12cd0dbe831d767f977fb6c92f058db23e6b3d','roulette_rewards','{\"id\":\"rwd_ce18ba551b1345d4\"}','verified','2026-11-09 08:33:51.403486'),('imp_966ed25457f2549f87f04b1df0ba3ac7','imp_3f3bbcc2fc835f8990adadc20e4776e8','roulette_rewards','6adb139d2615a279f5cd9312','f16a7bfc0c295e18712c45f689d2cb6522916aad925448e488d46999305aa8ae','roulette_rewards','{\"id\":\"rwd_724c88a8a5224216\"}','verified','2026-11-09 08:33:51.403486'),('imp_96a18a4cd4ea53d286664d6ff5174be4','imp_3f3bbcc2fc835f8990adadc20e4776e8','lens_indexes','6adb149adb3269dbc6aa4c84','613fe8e73019b97c2d6fc323c3d4f9072fd0a52a45fb18c55233301466a22349','lens_indexes','{\"id\":\"lens_3eabca2c19484e2f\"}','verified','2026-11-09 08:33:51.403486'),('imp_96eacb3526fc5c98b47afc410d51bc5d','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13942615a279f5cd92b7','f1264925a8d68a6387278ff86463ac7d4a6a21bff72ec026e8ab1f6a77748964','categories','{\"id\":\"cat_5895ef68d51c4d2e\"}','verified','2026-11-09 08:33:51.403486'),('imp_97778e8600b65a1d9474facfa110277e','imp_3f3bbcc2fc835f8990adadc20e4776e8','faqs','6adb149bdb3269dbc6aa4cab','70560e9ff4aca0f55fd8cc37a1066ebdb99221aa3ed3266e0c974955bbe70a13','faqs','{\"id\":\"faq_5a6dafe71ec44ca1\"}','verified','2026-11-09 08:33:51.403486'),('imp_982a916147265bdab00d6238f415e2a2','imp_3f3bbcc2fc835f8990adadc20e4776e8','roulette_rewards','6adb139d2615a279f5cd9313','acf4cd6bc17f7738b045340fc0515bc5f652a0c08915120271b25d7861130c26','roulette_rewards','{\"id\":\"rwd_143704cb36864730\"}','verified','2026-11-09 08:33:51.403486'),('imp_98399c9777ab5c099ce2b738cbcd32bb','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9300','29b94c88985fa3e50253df0d4d5d9c2622c2bdf996df81376bd0ad1098551ba6','product_categories','{\"category_id\":\"cat_263c673054d14d28\",\"product_id\":\"prd_1b6d039b016b4131\"}','verified','2026-11-09 08:33:51.403486'),('imp_984bde6a5e7b54e5b7ccc02f70fbc897','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9306','946414b12d755aac455846dfe413db5c8f19192b44251ebb1e2faacd5360e7d1','product_categories','{\"category_id\":\"cat_8e2e391496d84aba\",\"product_id\":\"prd_d7b3f4cfe9574460\"}','verified','2026-11-09 08:33:51.403486'),('imp_99048c8eea2d514f8f69cf9917d236fe','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13942615a279f5cd92b5','067919306c13d7dd571d1a5189b36500ec19521c4ceb1204bbf5853628fee921','categories','{\"id\":\"cat_c8db483f74e047f0\"}','verified','2026-11-09 08:33:51.403486'),('imp_990f36169b9f5a5283af210d396ecd66','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fe','2f929f71eb2245146d0087ec24c1ca88d19e27f1bae0bdb10f9e9c39b0ef51b3','product_badges','{\"badge\":\"bestseller\",\"product_id\":\"prd_fbef635ed7514c8f\"}','verified','2026-11-09 08:33:51.403486'),('imp_99a37f4511d75e38a83728e66ffdcd30','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13992615a279f5cd92ec','40ee361ecb466771560d84883451076cfcdf490e6c0dfb9b9c11134187934240','categories','{\"id\":\"cat_d1cf64ed5dbe41af\"}','verified','2026-11-09 08:33:51.403486'),('imp_9a55c40f5629548387e5af051ef2936b','imp_3f3bbcc2fc835f8990adadc20e4776e8','games','6adb139d2615a279f5cd9316','52905d9a9f805c53bceee4f8abc991f40851eb2dbce61d79e212dd5c302e6e11','games','{\"id\":\"gm_8eeb47ecdcb340c3\"}','verified','2026-11-09 08:33:51.403486'),('imp_9c296f1a47a75c9681956a36a3c2836c','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c9c','a9410587b48dcf5fe02b35b375e886ceef1e6d1a0d9f9f52e91cbd5bf1e715e1','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_ecae6a569bd84944\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_9c309884569050e184a890084e27de86','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13962615a279f5cd92cf','628906b9781266554d6a9ae9066ee5c60b85131767c53040b58e779eacdad95d','categories','{\"id\":\"cat_a15c84a7ca154e17\"}','verified','2026-11-09 08:33:51.403486'),('imp_9ca007f36f7756d080d3c1e6c23ca0b9','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13942615a279f5cd92bb','ca356653b05e1b65a9d418b29d1315ab1bdc6cd9ce1da04273e1f89704f2e739','categories','{\"id\":\"cat_8a7fd6fddc5341fa\"}','verified','2026-11-09 08:33:51.403486'),('imp_9cd2a36ffb0857daad16973fe9085593','imp_3f3bbcc2fc835f8990adadc20e4776e8','users','6adb13932615a279f5cd92af','4853ea23a8c570103ec62dba2619a8f81544262053e590ad781dff794145bcfa','user_permissions','{\"permission\":\"article.create\",\"user_id\":\"usr_c071c5fd6a6743b4\"}','verified','2026-11-09 08:33:51.403486'),('imp_9d8847f42f005db28a96d443ba3fead9','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f6','ef15e6433b59f7d54e4e86ecdea71db1b24217817d347198fb43e77028d19c29','product_images','{\"product_id\":\"prd_75466e5b7e5c4775\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_9defa47d073b5f72b656f69d963f3edc','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9303','04f914093fba7f1ee8838b6c19a934c6795a1b3b280f33dde9910ff644ae9c3d','products','{\"id\":\"prd_bce0660e41e84eaa\"}','verified','2026-11-09 08:33:51.403486'),('imp_9e122d1fa18e5a249dc5cba65519c4b9','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f9','d17743ca6c89ae66907608bc40a89e067c4d59145d1b789a74396be1f1075d97','product_badges','{\"badge\":\"bestseller\",\"product_id\":\"prd_401170d2b1564810\"}','verified','2026-11-09 08:33:51.403486'),('imp_9e36f84f284f5dfd9407b68e16e06c0c','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f6','ef15e6433b59f7d54e4e86ecdea71db1b24217817d347198fb43e77028d19c29','product_categories','{\"category_id\":\"cat_c8db483f74e047f0\",\"product_id\":\"prd_75466e5b7e5c4775\"}','verified','2026-11-09 08:33:51.403486'),('imp_9e55716753df5d0481d5ca1059ecd7d4','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13942615a279f5cd92b6','eaba59a3e96406e572993da685e441638ea4182c447bfd8b889b876169348581','categories','{\"id\":\"cat_f4e07e43d00145b7\"}','verified','2026-11-09 08:33:51.403486'),('imp_9f6fd32e33585d5eb2611cfdc7f42298','imp_3f3bbcc2fc835f8990adadc20e4776e8','faqs','6adb149bdb3269dbc6aa4caa','afbaae3f4329357f61f27a83052c54f21f2864b9d3221364dd9c4ad5a47f6f6d','faqs','{\"id\":\"faq_e225050130d847b5\"}','verified','2026-11-09 08:33:51.403486'),('imp_a050d68efe3c5a82b816466ea2ed7fce','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fc','1aa509af845e57eb89c0d156c5a9100fc5dd6475b873ba348593e2c46a81c14f','product_categories','{\"category_id\":\"cat_7c376dc73fc34a3f\",\"product_id\":\"prd_7ba6732284b649c8\"}','verified','2026-11-09 08:33:51.403486'),('imp_a07186def80e53fba9808d8b60138cf6','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9301','2e009b77e41c61666858216e9bb2cb8cb08222e6dcba8b30b06e6c382b88bfcc','products','{\"id\":\"prd_898f994b888240ab\"}','verified','2026-11-09 08:33:51.403486'),('imp_a26be90c0982506b93340d99074024a4','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f5','5b331b8d2d297f872fc913e0ccd0682a890819708f36b365e37fe3ce3604d748','products','{\"id\":\"prd_0b61644f093f4610\"}','verified','2026-11-09 08:33:51.403486'),('imp_a2a9047fdb4850608129599de7a5698c','imp_3f3bbcc2fc835f8990adadc20e4776e8','roulette_rewards','6adb139c2615a279f5cd930e','a75082038183b33dbe55c9b69ba824a34bf3f25eb0df96a3311b390fea5d69c7','roulette_rewards','{\"id\":\"rwd_4976e36c072049d3\"}','verified','2026-11-09 08:33:51.403486'),('imp_a2aa02727d1e5c619ce510c9b0c92aca','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9304','72c657a00698274f9e2acad75d58e4e904834957edab3deebfb9dfcc004669bc','product_images','{\"product_id\":\"prd_52253b4c63584c54\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_a33d3a1bbc0d5f7d8aeac5c859c261e8','imp_3f3bbcc2fc835f8990adadc20e4776e8','brands','6adb139a2615a279f5cd92ef','0c71c6cc449d715e7c8d68d26db433698a182dd4a3571da669bc65d7e7cafc05','brands','{\"id\":\"brd_5d2a87b6de0a421d\"}','verified','2026-11-09 08:33:51.403486'),('imp_a37d502b977657078d2d35da5be92062','imp_3f3bbcc2fc835f8990adadc20e4776e8','flash_sales','6adb139c2615a279f5cd930b','2151866717d8f20c9ab1ed2e2e0540ee46fa25138bd3c18b2738d7b44d7702d0','flash_sales','{\"id\":\"fls_9d6274e94df94512\"}','verified','2026-11-09 08:33:51.403486'),('imp_a4fcfdaec8995da2a5f171db39bbf49f','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9303','04f914093fba7f1ee8838b6c19a934c6795a1b3b280f33dde9910ff644ae9c3d','product_variants','{\"id\":\"var_b4586763d3f0419c\"}','verified','2026-11-09 08:33:51.403486'),('imp_a56cb179047a5c9ab932ebbd7b92a92d','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9301','2e009b77e41c61666858216e9bb2cb8cb08222e6dcba8b30b06e6c382b88bfcc','product_images','{\"product_id\":\"prd_898f994b888240ab\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_a702dc6b20695867a49f49398c66192b','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f8','4350c494dbea28578ed3ce7b0cf4f60abc1fb5c417d1ef7c007391daa7617f5d','products','{\"id\":\"prd_df7a0e382fa14177\"}','verified','2026-11-09 08:33:51.403486'),('imp_a7082b0820a6534bb48c6fd2c3524b03','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9307','5045de5b2a7815e44f61c6e223fdcf09628b23692db2561f60c7370a9fc05527','products','{\"id\":\"prd_98175a8e8a554c55\"}','verified','2026-11-09 08:33:51.403486'),('imp_a818b3d639cc53859eb187fb8ed36393','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fb','4b1c490983eb289380734be486bd4444d45dfc2b5e8145a313db1b25383bbfd2','product_variants','{\"id\":\"var_88681df03c214cff\"}','verified','2026-11-09 08:33:51.403486'),('imp_a82c0ad0963652dead44bf28a498f82f','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13992615a279f5cd92e8','f94df498ec9f0c8e0ececc2f69eba6c1880bdad6634743bff96aee95724a9d9c','categories','{\"id\":\"cat_86849a3a92084a57\"}','verified','2026-11-09 08:33:51.403486'),('imp_a8a98a5dd3e2570f8cb5fd7ff2bc2090','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c9a','27fdf42b96b0702d0da67e7e1e55a3ccc83bab76d89a1fbf7e89ba9abc36dd3a','product_knowledge_bullets','{\"kind\":\"con\",\"knowledge_id\":\"pk_75000d7042714b61\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_a8ace2e38f8a5228baae9bc214951a89','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9303','04f914093fba7f1ee8838b6c19a934c6795a1b3b280f33dde9910ff644ae9c3d','product_images','{\"product_id\":\"prd_bce0660e41e84eaa\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_a8d5364d91845aef88c7a9dd9a6f8663','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fb','4b1c490983eb289380734be486bd4444d45dfc2b5e8145a313db1b25383bbfd2','product_badges','{\"badge\":\"new\",\"product_id\":\"prd_f27e5e8e2c274d16\"}','verified','2026-11-09 08:33:51.403486'),('imp_a8e0ad7f07145801b154bd8cc122d796','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9303','04f914093fba7f1ee8838b6c19a934c6795a1b3b280f33dde9910ff644ae9c3d','product_categories','{\"category_id\":\"cat_a57421c7ee3b4826\",\"product_id\":\"prd_bce0660e41e84eaa\"}','verified','2026-11-09 08:33:51.403486'),('imp_a8e2103971a3552480a3abaa1c264a41','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f7','a0ecedd25e902b5f1ceec9fa730cb3b0257117bdbe99c348d8c69ad676af4f7e','product_categories','{\"category_id\":\"cat_67fb4e6c624a4ce0\",\"product_id\":\"prd_f1a4277d4ba84cd1\"}','verified','2026-11-09 08:33:51.403486'),('imp_a8e82c47bdca5708975cd2a04018ae77','imp_3f3bbcc2fc835f8990adadc20e4776e8','articles','6adb149adb3269dbc6aa4c8c','59159e4530b9925b193ac44eea942f4940352b50bfcd7c448180ec96a3201908','articles','{\"id\":\"art_a0c9893ace164ee2\"}','verified','2026-11-09 08:33:51.403486'),('imp_a90ed27c4d425299bf18cbd73a34d76d','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9304','72c657a00698274f9e2acad75d58e4e904834957edab3deebfb9dfcc004669bc','product_variants','{\"id\":\"var_7b2d2b3cee7d410f\"}','verified','2026-11-09 08:33:51.403486'),('imp_aa762802fd205f0fbfe5e530d9bcb043','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c9d','809bc4110ed38376872d0f601e22c2d44b8803ed1df30c32a79d0e7bb66ee2d7','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_2414f501c7e3484c\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_aaef7dff598b5101af09f8cabfe8ef2a','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c94','3e62c94f42566cb38c7e75648e3719323d9585713f38e57310e8595e6699dbef','product_knowledges','{\"id\":\"pk_1f46da3523494cc3\"}','verified','2026-11-09 08:33:51.403486'),('imp_aaf69f4a52315d0da5cfd73ce87767a8','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92ff','defd51450ef4c0ab3cbe8cd19efca51611f47ad390e4fffb89206e854ee80ba3','product_images','{\"product_id\":\"prd_cb46f21f4ef446f3\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_ac678439f3c15d008b5e025e334d22cf','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9306','946414b12d755aac455846dfe413db5c8f19192b44251ebb1e2faacd5360e7d1','product_images','{\"product_id\":\"prd_d7b3f4cfe9574460\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_aca903bbdea65f3b8617ee0cb597899c','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f7','a0ecedd25e902b5f1ceec9fa730cb3b0257117bdbe99c348d8c69ad676af4f7e','product_images','{\"product_id\":\"prd_f1a4277d4ba84cd1\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_ae9a12e5536c54f28813a3953bc66f9f','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13992615a279f5cd92e6','19e757c5cbfe85a65d73e4318031e76d286ce5a9a5de724d4f4d70c3a729f03f','categories','{\"id\":\"cat_af51edff4e9841ff\"}','verified','2026-11-09 08:33:51.403486'),('imp_aea67e71e50e5727b7dc20a37ec9357e','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9300','29b94c88985fa3e50253df0d4d5d9c2622c2bdf996df81376bd0ad1098551ba6','product_categories','{\"category_id\":\"cat_64cac2c66f40435e\",\"product_id\":\"prd_1b6d039b016b4131\"}','verified','2026-11-09 08:33:51.403486'),('imp_b1a83edc5789568a912d3c09d1abecd5','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c95','ee26ece75ded102798f1a211a8732a29deb2737409fb670705667b10e34cf213','product_knowledges','{\"id\":\"pk_141aea81440b44e5\"}','verified','2026-11-09 08:33:51.403486'),('imp_b26600b776505faaa69b89b02585becc','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c92','5049ae03e06dc482a1fe196f2a6eade9a73cca86143314f36aa767ce6b4cd75f','product_knowledges','{\"id\":\"pk_fb7955a67278482c\"}','verified','2026-11-09 08:33:51.403486'),('imp_b27c82e73c8950c4bea8cc1a1ba853e4','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13962615a279f5cd92c9','2fdae260f978f7d4be27475d4b3d6fe23b91899621415b824d503e344d0fad35','categories','{\"id\":\"cat_ab44ff7d3aec41d7\"}','verified','2026-11-09 08:33:51.403486'),('imp_b2cdc3a7ec795fc682ff1997dfc4638b','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fd','f5eaa77ce8f584982113477b55031e7169a62342d3bd51b360f31e28c0cf3cb9','product_images','{\"product_id\":\"prd_26aa3608a7084627\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_b3905da340ca53eabb102972241fc4de','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fd','f5eaa77ce8f584982113477b55031e7169a62342d3bd51b360f31e28c0cf3cb9','product_images','{\"product_id\":\"prd_26aa3608a7084627\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_b4b8c730a518517f9dc07cad3fa1bf91','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9300','29b94c88985fa3e50253df0d4d5d9c2622c2bdf996df81376bd0ad1098551ba6','product_variants','{\"id\":\"var_a344ccbec1864693\"}','verified','2026-11-09 08:33:51.403486'),('imp_b56b9eebaffe52efaede6afb807fffa5','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f9','d17743ca6c89ae66907608bc40a89e067c4d59145d1b789a74396be1f1075d97','products','{\"id\":\"prd_401170d2b1564810\"}','verified','2026-11-09 08:33:51.403486'),('imp_b5e1eea6ff4252fcbc11c4ba1ee025cc','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13982615a279f5cd92dc','f8c75914c85c2ada9c1cdffad7795ef323fd11f2e13a2b74b2a569b6eafd49d8','categories','{\"id\":\"cat_263c673054d14d28\"}','verified','2026-11-09 08:33:51.403486'),('imp_b618fcd3591658fc87d46dfacb32c2b1','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9302','167f810d58d1d45323d3da3c1251cd4578740d00f8e58874e299aa3cc3cc6adc','product_categories','{\"category_id\":\"cat_86849a3a92084a57\",\"product_id\":\"prd_0f674d6c51e34ae1\"}','verified','2026-11-09 08:33:51.403486'),('imp_b6846c619c8f563f8db337b811bfc8a1','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9303','04f914093fba7f1ee8838b6c19a934c6795a1b3b280f33dde9910ff644ae9c3d','product_variants','{\"id\":\"var_2b6cec11c2b84fc7\"}','verified','2026-11-09 08:33:51.403486'),('imp_b702e55a7684579c924de612edae75a9','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f8','4350c494dbea28578ed3ce7b0cf4f60abc1fb5c417d1ef7c007391daa7617f5d','product_images','{\"product_id\":\"prd_df7a0e382fa14177\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_b75fc814cf46596081d6fd690d6c3238','imp_3f3bbcc2fc835f8990adadc20e4776e8','flash_sales','6ae1b6f238d2614e8e285fe0','c7d1e19df6f5c69facd3bc5fdd55d66d87458e22a911b4207fa591acc9f766f9','flash_sale_items','{\"id\":\"imp_e8be9a0dfc0b55bf8ce685ba803a5b66\"}','verified','2026-11-09 08:33:51.403486'),('imp_b78a0726294758cfa3eaac5ad4396cef','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13932615a279f5cd92b2','7cef8aa68d6e7d47a820a005de31c049fc35585d12d6b67ffd4b58bf615d315c','categories','{\"id\":\"cat_8e2e391496d84aba\"}','verified','2026-11-09 08:33:51.403486'),('imp_b847a5b33c3654f687c544cc004788de','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13932615a279f5cd92b0','5a8573fe8138fa4deb5994b0bfc8b79d46fb200395577589eca2c8e97318c52f','categories','{\"id\":\"cat_f9a1ff0356e24b14\"}','verified','2026-11-09 08:33:51.403486'),('imp_b90e6ae4055a5bd98572f14ec4ba7638','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9302','167f810d58d1d45323d3da3c1251cd4578740d00f8e58874e299aa3cc3cc6adc','product_variants','{\"id\":\"var_17821973adfb4662\"}','verified','2026-11-09 08:33:51.403486'),('imp_b9b87307a75f52edb5afa1983ce190c3','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fa','60e71e9aafca35f2bbe54134ce638ac819a431553b2031b2c529ab1cec69fc18','product_categories','{\"category_id\":\"cat_f9a1ff0356e24b14\",\"product_id\":\"prd_3e8ddf16743d4901\"}','verified','2026-11-09 08:33:51.403486'),('imp_b9ee98f9edf75fcc96cfe0ee94d65cdf','imp_3f3bbcc2fc835f8990adadc20e4776e8','vouchers','6adb139c2615a279f5cd930a','f4a5f28c95a08e30038a59671fa1925acb6a1147753202ecf7943678d5f38881','vouchers','{\"id\":\"vch_a1d7c53fff644a0e\"}','verified','2026-11-09 08:33:51.403486'),('imp_bad3b037182c59549fc045c327c4af78','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f6','ef15e6433b59f7d54e4e86ecdea71db1b24217817d347198fb43e77028d19c29','product_segments','{\"product_id\":\"prd_75466e5b7e5c4775\",\"segment\":\"Wanita\"}','verified','2026-11-09 08:33:51.403486'),('imp_bc067de8f88d5f1f9bbe8247a3130d0b','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c9d','809bc4110ed38376872d0f601e22c2d44b8803ed1df30c32a79d0e7bb66ee2d7','product_knowledge_bullets','{\"kind\":\"con\",\"knowledge_id\":\"pk_2414f501c7e3484c\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_bc23b86275e85bb6a065555f2f5c40d4','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f7','a0ecedd25e902b5f1ceec9fa730cb3b0257117bdbe99c348d8c69ad676af4f7e','product_images','{\"product_id\":\"prd_f1a4277d4ba84cd1\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_bd0423e9f07350aeaf7e651afc55e8f2','imp_3f3bbcc2fc835f8990adadc20e4776e8','cms_pages','6adb149bdb3269dbc6aa4cb0','e6475ae825d95c4aeff4d4f0f1fbcc3b861789d9325cdc995ad871d9c5d2a8f9','cms_pages','{\"id\":\"pg_633c6cadf6f94a99\"}','verified','2026-11-09 08:33:51.403486'),('imp_bd5e285803d85fb58ca3306b219a9381','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c98','7498b0bc5c33866dda2b4ff55aa57a216b00d5178dc143c8243f009ff24862a4','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_6f3104e2d8424751\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_bd884d5aa1d350c5a36765183e0d14d3','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9301','2e009b77e41c61666858216e9bb2cb8cb08222e6dcba8b30b06e6c382b88bfcc','product_segments','{\"product_id\":\"prd_898f994b888240ab\",\"segment\":\"Anak-anak\"}','verified','2026-11-09 08:33:51.403486'),('imp_bda7871f232e5ad0b77ef54ee434ea7b','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f9','d17743ca6c89ae66907608bc40a89e067c4d59145d1b789a74396be1f1075d97','product_badges','{\"badge\":\"flashsale\",\"product_id\":\"prd_401170d2b1564810\"}','verified','2026-11-09 08:33:51.403486'),('imp_be1991e826555754a4a8bc4dba115368','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9306','946414b12d755aac455846dfe413db5c8f19192b44251ebb1e2faacd5360e7d1','product_images','{\"product_id\":\"prd_d7b3f4cfe9574460\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_be67631b6233521e80d5411751cce2f4','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c8f','31affefcd535287f3f284e1a5de0aadd13944451834791b4912592ba3fe6a29d','product_knowledge_bullets','{\"kind\":\"con\",\"knowledge_id\":\"pk_30cd2cb1236144ec\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_be8d316ca8f9535fa4f1dd9f0053af22','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fd','f5eaa77ce8f584982113477b55031e7169a62342d3bd51b360f31e28c0cf3cb9','product_segments','{\"product_id\":\"prd_26aa3608a7084627\",\"segment\":\"Unisex\"}','verified','2026-11-09 08:33:51.403486'),('imp_bf3bc2e062135ebc8cb86cba7f6636b3','imp_3f3bbcc2fc835f8990adadc20e4776e8','vouchers','6adb139c2615a279f5cd9309','a9512ab483c28d7f4c419db315494b111d05a5ee558d4c1b6ae0499c5aedf53c','vouchers','{\"id\":\"vch_9018711ea1bc49ff\"}','verified','2026-11-09 08:33:51.403486'),('imp_bfca33e9fcd25458b601813bb3f231a6','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13982615a279f5cd92e1','7055010f0306ab54df7083e5bdc46a82403952a24fe0af5045a4663ab77ed85c','categories','{\"id\":\"cat_e1997c95480c4340\"}','verified','2026-11-09 08:33:51.403486'),('imp_c0df832821fb55e18dcddd0eed9c932b','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13952615a279f5cd92c4','6a42d686fec315d56de2420e92b868065b08e1799606a8fcb0aa09955b5b0632','categories','{\"id\":\"cat_7dbdc3b4be924c27\"}','verified','2026-11-09 08:33:51.403486'),('imp_c23cf50409715f839c344251af251c0a','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c9e','47a3eb0a4c2971ad4f1e1974c827a611b472cb4115c1b621863de74303fec149','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_f1e4dd9e53b541fa\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_c2b0c5ee964e55d28d3bc29e12081dc0','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13972615a279f5cd92d1','8dc33f63eab30132ca265eb6f4368577d4cba3805285c5fbd7e7a643e2de02c3','categories','{\"id\":\"cat_6a0f0bacaa6c4ee8\"}','verified','2026-11-09 08:33:51.403486'),('imp_c4fc6851e77956afa3989591dab52dd6','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fc','1aa509af845e57eb89c0d156c5a9100fc5dd6475b873ba348593e2c46a81c14f','product_images','{\"product_id\":\"prd_7ba6732284b649c8\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_c51b08e87d1e57feb92ebdd3a7d12ffa','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c94','3e62c94f42566cb38c7e75648e3719323d9585713f38e57310e8595e6699dbef','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_1f46da3523494cc3\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_c5b3c3b6ac035986840dee34a866fc9f','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c99','6c85152f027351a1f648387046f32b9c5812ab4f9ba120c92c4cac89168f9087','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_404d444bcfca48eb\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_c5b8ce55fea35b4e87af93fb8fc0730f','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13992615a279f5cd92ea','d2b235971f0879d8cf7409187871d4652c3a7079fec8789fe1e20739c54e85bb','categories','{\"id\":\"cat_faefff9a71944a61\"}','verified','2026-11-09 08:33:51.403486'),('imp_c6689f79a3ba5a61ac8a6394e69f30a1','imp_3f3bbcc2fc835f8990adadc20e4776e8','banners_v2','6adb149bdb3269dbc6aa4cb6','5ef512f179a7bf2fab6fc7246bcc1a1e4bf0b35478243553bd796cc29b45760e','banners','{\"id\":\"ban_c4bd63137e7e4d21\"}','verified','2026-11-09 08:33:51.403486'),('imp_c775fd149138519e89a40547aa3e87f3','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f4','1cb15a116079d55768b6230f8d2e1440446235fb6a616f7561bc1b02bb6206ba','product_categories','{\"category_id\":\"cat_4bb0610322c04fae\",\"product_id\":\"prd_f2d20822dbce4da6\"}','verified','2026-11-09 08:33:51.403486'),('imp_c78e655a18475a24ba2a880e27eaca9f','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13982615a279f5cd92da','fee711974bdd57947ad93b462feb35d0315fb7d7281568e1e30d3be4822baa44','categories','{\"id\":\"cat_080745e860734087\"}','verified','2026-11-09 08:33:51.403486'),('imp_c8210d9291645c3cbed512c0b668d941','imp_3f3bbcc2fc835f8990adadc20e4776e8','users','6adb13932615a279f5cd92af','4853ea23a8c570103ec62dba2619a8f81544262053e590ad781dff794145bcfa','user_permissions','{\"permission\":\"review.view\",\"user_id\":\"usr_c071c5fd6a6743b4\"}','verified','2026-11-09 08:33:51.403486'),('imp_c8286175703c5c30a222b0738f0a1fb0','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f4','1cb15a116079d55768b6230f8d2e1440446235fb6a616f7561bc1b02bb6206ba','product_categories','{\"category_id\":\"cat_f9a1ff0356e24b14\",\"product_id\":\"prd_f2d20822dbce4da6\"}','verified','2026-11-09 08:33:51.403486'),('imp_c8d4e536b7255ac3bd4144c687684362','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c97','609e8e795f5ce0f268a90f9fe4eeb8a2382ca5cc7dc76a88f823af825c9618fc','product_knowledge_bullets','{\"kind\":\"con\",\"knowledge_id\":\"pk_2171c71a9c864d1a\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_c924efb36ca95e0f9d9512e7ce38ee71','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f9','d17743ca6c89ae66907608bc40a89e067c4d59145d1b789a74396be1f1075d97','product_categories','{\"category_id\":\"cat_f9a1ff0356e24b14\",\"product_id\":\"prd_401170d2b1564810\"}','verified','2026-11-09 08:33:51.403486'),('imp_c9701285a1295a3681af6d41f2406bb3','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9303','04f914093fba7f1ee8838b6c19a934c6795a1b3b280f33dde9910ff644ae9c3d','product_images','{\"product_id\":\"prd_bce0660e41e84eaa\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_c97097e9393450449aa265e92dd06fa2','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fb','4b1c490983eb289380734be486bd4444d45dfc2b5e8145a313db1b25383bbfd2','product_images','{\"product_id\":\"prd_f27e5e8e2c274d16\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_cb18a20644de57d28d94ec22abcb52ce','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92ff','defd51450ef4c0ab3cbe8cd19efca51611f47ad390e4fffb89206e854ee80ba3','product_images','{\"product_id\":\"prd_cb46f21f4ef446f3\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_cb9e3a661cfd590a84f7e9934e9220a4','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fa','60e71e9aafca35f2bbe54134ce638ac819a431553b2031b2c529ab1cec69fc18','product_categories','{\"category_id\":\"cat_fc53a5d7fa854ec3\",\"product_id\":\"prd_3e8ddf16743d4901\"}','verified','2026-11-09 08:33:51.403486'),('imp_cbc370dd79605305b9ec6eb55457bdac','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9307','5045de5b2a7815e44f61c6e223fdcf09628b23692db2561f60c7370a9fc05527','product_categories','{\"category_id\":\"cat_3502c02ad4ac4d8d\",\"product_id\":\"prd_98175a8e8a554c55\"}','verified','2026-11-09 08:33:51.403486'),('imp_cbd2ab985af65479a6dce2a9a0c55df4','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f4','1cb15a116079d55768b6230f8d2e1440446235fb6a616f7561bc1b02bb6206ba','product_images','{\"product_id\":\"prd_f2d20822dbce4da6\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_cd4d130c3deb5784b619dd6d0df34e58','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fe','2f929f71eb2245146d0087ec24c1ca88d19e27f1bae0bdb10f9e9c39b0ef51b3','product_categories','{\"category_id\":\"cat_ab44ff7d3aec41d7\",\"product_id\":\"prd_fbef635ed7514c8f\"}','verified','2026-11-09 08:33:51.403486'),('imp_cf84a86e03865a558031a5672cbd6f20','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f4','1cb15a116079d55768b6230f8d2e1440446235fb6a616f7561bc1b02bb6206ba','product_badges','{\"badge\":\"bestseller\",\"product_id\":\"prd_f2d20822dbce4da6\"}','verified','2026-11-09 08:33:51.403486'),('imp_cfa0aa135cde593aa2132ec7c2feac3e','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9303','04f914093fba7f1ee8838b6c19a934c6795a1b3b280f33dde9910ff644ae9c3d','product_categories','{\"category_id\":\"cat_1e21dafc7f3c4850\",\"product_id\":\"prd_bce0660e41e84eaa\"}','verified','2026-11-09 08:33:51.403486'),('imp_cffcb2f2d90850bbb2508041343bb47a','imp_3f3bbcc2fc835f8990adadc20e4776e8','brands','6adb139a2615a279f5cd92f2','c18472cd2208a3d9f28fca168b39d4717936527d7dd13d8153365376e0a394db','brands','{\"id\":\"brd_9054aabe325441da\"}','verified','2026-11-09 08:33:51.403486'),('imp_d0624f2134ff51a18dcb1b9424c34c4b','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f4','1cb15a116079d55768b6230f8d2e1440446235fb6a616f7561bc1b02bb6206ba','product_variants','{\"id\":\"var_8d5417e08d9e44b3\"}','verified','2026-11-09 08:33:51.403486'),('imp_d0c0687c36ad53b2893fb29d2ac5d739','imp_3f3bbcc2fc835f8990adadc20e4776e8','user_sessions','6ae1b67b38d2614e8e285fdb','3132088b1776bbad3dd1e1c5e9093ae21bc4ec0757ff49372f7034ea5d70a829','user_sessions','{\"session_id\":\"ses_dc2a424515624a84\"}','verified','2026-11-09 08:33:51.403486'),('imp_d10ae297c15b553e8cd9c9a49f2d6e93','imp_3f3bbcc2fc835f8990adadc20e4776e8','users','6adb13922615a279f5cd92ad','7dc3d9cac0ba6c86c5e3ec1a2cf7fe6d23f5fad78917aec4fee0d7974082ea9a','users','{\"user_id\":\"usr_c4b3d45ff0b94ffd\"}','verified','2026-11-09 08:33:51.403486'),('imp_d1c45fbf3ccc5f8eb54e48f636710d3b','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c8f','31affefcd535287f3f284e1a5de0aadd13944451834791b4912592ba3fe6a29d','product_knowledges','{\"id\":\"pk_30cd2cb1236144ec\"}','verified','2026-11-09 08:33:51.403486'),('imp_d206f3b212b85c9a91afbf47316bd5ce','imp_3f3bbcc2fc835f8990adadc20e4776e8','user_sessions','6aea88c56a695e2f7907443b','4c399cf76d56ee50b4aff8ff147e1d48d57b523666da6e5ef7677201ad6dd083','user_sessions','{\"session_id\":\"ses_93ba276471d84fc1\"}','verified','2026-11-09 08:33:51.403486'),('imp_d2ede6e8f4a55748ab09db208404da2d','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f6','ef15e6433b59f7d54e4e86ecdea71db1b24217817d347198fb43e77028d19c29','product_variants','{\"id\":\"var_66c61297dc0e494b\"}','verified','2026-11-09 08:33:51.403486'),('imp_d302d026bc175dc9840f65a25ece8a04','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c91','361ee2328fc159c5bd743f2d630320bb52a331f54d1334e1311c8aac583ebcc9','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_65c16b9faf834556\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_d334a7479c1e5bafa28c3791f831005a','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13952615a279f5cd92c5','522ff8f13a2cb8a2e7077e57f039eaa2c31d7a4c098a8eaac515bc358a120116','categories','{\"id\":\"cat_da3988e651d349bb\"}','verified','2026-11-09 08:33:51.403486'),('imp_d34b69badd74576c93ee05c7cb30b2f3','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9304','72c657a00698274f9e2acad75d58e4e904834957edab3deebfb9dfcc004669bc','product_images','{\"product_id\":\"prd_52253b4c63584c54\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_d3b877f41bcb5c7fa2e3ef521195a599','imp_3f3bbcc2fc835f8990adadc20e4776e8','users','6adb13932615a279f5cd92af','4853ea23a8c570103ec62dba2619a8f81544262053e590ad781dff794145bcfa','users','{\"user_id\":\"usr_c071c5fd6a6743b4\"}','verified','2026-11-09 08:33:51.403486'),('imp_d49266f79bd85e03a02be489599564c4','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13972615a279f5cd92d9','be2665e17d6f71b4ac82a29863c6788b597bdca41f3343e5d059b98d1f8a5256','categories','{\"id\":\"cat_d64afabb5cd74370\"}','verified','2026-11-09 08:33:51.403486'),('imp_d62f13d689325907a7f761c81c1b8bb9','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f8','4350c494dbea28578ed3ce7b0cf4f60abc1fb5c417d1ef7c007391daa7617f5d','product_images','{\"product_id\":\"prd_df7a0e382fa14177\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_d674c03925b152f9b4d4b4fdf086e8ca','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13932615a279f5cd92b1','fc9706b8a9eb5f4ca3cf4bc688baeee2c016e4fd7ad518c7e6b1aa1f39577f28','categories','{\"id\":\"cat_1e21dafc7f3c4850\"}','verified','2026-11-09 08:33:51.403486'),('imp_d6eecce17980568cb797e93b3e6d4ef4','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f9','d17743ca6c89ae66907608bc40a89e067c4d59145d1b789a74396be1f1075d97','product_variants','{\"id\":\"var_7f9dbd1522c54b35\"}','verified','2026-11-09 08:33:51.403486'),('imp_d7ace085cf4b59adb1470f523ff8f82a','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13942615a279f5cd92b3','726544cff6035f6ca4e7eb2f23f753753759691126770271c9c1a36cf1be5459','categories','{\"id\":\"cat_67fb4e6c624a4ce0\"}','verified','2026-11-09 08:33:51.403486'),('imp_d7b7ed828e5a5e028f0be96a4f470afa','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13972615a279f5cd92d8','a6ab3570ae6d8c9ff7e4b2e06821c559dee7e4b644f9137c8f7e15775c7e8535','categories','{\"id\":\"cat_b869fc45e3484158\"}','verified','2026-11-09 08:33:51.403486'),('imp_d8eb2202301c57a0abff551875e4874f','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13992615a279f5cd92e9','b895b653ae1b3077138369c7947c6bf986c95a1d92b5db0687daa15a6a707afa','categories','{\"id\":\"cat_a57421c7ee3b4826\"}','verified','2026-11-09 08:33:51.403486'),('imp_d9426fe1e2305c7e99c3ffcd3bcbf7a5','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9300','29b94c88985fa3e50253df0d4d5d9c2622c2bdf996df81376bd0ad1098551ba6','product_categories','{\"category_id\":\"cat_f9a1ff0356e24b14\",\"product_id\":\"prd_1b6d039b016b4131\"}','verified','2026-11-09 08:33:51.403486'),('imp_d9ea8f804d89534bb326904161bdb68c','imp_3f3bbcc2fc835f8990adadc20e4776e8','cms_pages','6adb149bdb3269dbc6aa4cb2','5c7077bb00df1506bbe7f60026360017d701f6be501857cbe9aa863998647229','cms_pages','{\"id\":\"pg_556d58cad6cb4055\"}','verified','2026-11-09 08:33:51.403486'),('imp_d9ecba98b326589f989b0b1ec128de71','imp_3f3bbcc2fc835f8990adadc20e4776e8','flash_sales','6adb139c2615a279f5cd930b','2151866717d8f20c9ab1ed2e2e0540ee46fa25138bd3c18b2738d7b44d7702d0','flash_sale_items','{\"id\":\"imp_4411584530a85faf8fbd3370609b914f\"}','verified','2026-11-09 08:33:51.403486'),('imp_da89c92c55b4529685ebb0a8a81aa546','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13952615a279f5cd92c3','ca47b1bcff0ffbc60b0d4ad7499228837fd90024a0aebf922a1ad3aa70661160','categories','{\"id\":\"cat_3bf714e989974562\"}','verified','2026-11-09 08:33:51.403486'),('imp_db407314a8dd58bcab9bfb804793f9c9','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9305','4b72b62a603a8c1be8db346326205eba5574ce25ac5b82006721ae4cd0385f45','product_badges','{\"badge\":\"bestseller\",\"product_id\":\"prd_a1911ea875294d3a\"}','verified','2026-11-09 08:33:51.403486'),('imp_db83781e35ec5e2092e13c788776be2d','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f6','ef15e6433b59f7d54e4e86ecdea71db1b24217817d347198fb43e77028d19c29','product_images','{\"product_id\":\"prd_75466e5b7e5c4775\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_dbcc5ccd71485c49a8c2e95db80942f0','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92ff','defd51450ef4c0ab3cbe8cd19efca51611f47ad390e4fffb89206e854ee80ba3','products','{\"id\":\"prd_cb46f21f4ef446f3\"}','verified','2026-11-09 08:33:51.403486'),('imp_dcbbbe5536d751ea950b6ac6395e355f','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c96','8111c29f25b20009fb1bfa01f5827da822c0d5bad6a80a12a1f7bb73edc7fa07','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_fd6c135365384fca\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_de12724ff7a656bebdaf3f0a5854e01e','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13992615a279f5cd92e7','9c2a92702f78f05b42818a87a1f277a9e3307d1f280b6103e731ccad12e6e106','categories','{\"id\":\"cat_0882be6403ac4ec8\"}','verified','2026-11-09 08:33:51.403486'),('imp_de712fcdc1a05ca7a828387a57fc3084','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fc','1aa509af845e57eb89c0d156c5a9100fc5dd6475b873ba348593e2c46a81c14f','product_variants','{\"id\":\"var_8d9fe36260964fff\"}','verified','2026-11-09 08:33:51.403486'),('imp_dee1b126f8a5521098912d28d9641150','imp_3f3bbcc2fc835f8990adadc20e4776e8','lens_indexes','6adb1499db3269dbc6aa4c80','5527e6427ceb416c197104e26b932e45f9bb5cbd24f0459a99ce7e39aa108c16','lens_indexes','{\"id\":\"lens_754bff09833941d3\"}','verified','2026-11-09 08:33:51.403486'),('imp_deedb62a425856418cbfa6e57d25e15f','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13962615a279f5cd92ce','04e4bc6f75c52455b9d734cb39bf907ce3f9a703c71771ec1b6caf9411f9bbfa','categories','{\"id\":\"cat_2a242467e0f54243\"}','verified','2026-11-09 08:33:51.403486'),('imp_df91578255ca58e4a5b2db70a575d100','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c95','ee26ece75ded102798f1a211a8732a29deb2737409fb670705667b10e34cf213','product_knowledge_bullets','{\"kind\":\"con\",\"knowledge_id\":\"pk_141aea81440b44e5\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_dfa88c73485f5248a0d1dfac6cf8f396','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fd','f5eaa77ce8f584982113477b55031e7169a62342d3bd51b360f31e28c0cf3cb9','product_variants','{\"id\":\"var_9c42dd0a57044732\"}','verified','2026-11-09 08:33:51.403486'),('imp_e058ac01b41b5d34a6439a0173015467','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c98','7498b0bc5c33866dda2b4ff55aa57a216b00d5178dc143c8243f009ff24862a4','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_6f3104e2d8424751\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_e2b3c66a881158d89550fe2209c4548c','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13982615a279f5cd92df','fcab9ac858ed5b6ea0b25fceb32d69113f7b2586ad661e7d507b167a68392e53','categories','{\"id\":\"cat_b9c108beb0fd4d03\"}','verified','2026-11-09 08:33:51.403486'),('imp_e319394ffa66577197875c47e94cc082','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c98','7498b0bc5c33866dda2b4ff55aa57a216b00d5178dc143c8243f009ff24862a4','product_knowledge_bullets','{\"kind\":\"con\",\"knowledge_id\":\"pk_6f3104e2d8424751\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_e3fe0c3a9aa350c7a9aa6bda2b5a1c60','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c9f','7871cc14dbaaaa5f433db595b39b8e35cceaecb6d8c25569bd45de381873835c','product_knowledges','{\"id\":\"pk_b10021bb3bcc49f1\"}','verified','2026-11-09 08:33:51.403486'),('imp_e5b49358e6845e89a42cabded77a75a2','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9307','5045de5b2a7815e44f61c6e223fdcf09628b23692db2561f60c7370a9fc05527','product_images','{\"product_id\":\"prd_98175a8e8a554c55\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_e5b69a2e69685c5696390874fba5e96f','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13992615a279f5cd92eb','f6e63d32ad187b85b55bee4dbee1e2fbfccfab705890f3b267f78c3614d5489c','categories','{\"id\":\"cat_71b46a9ac639436a\"}','verified','2026-11-09 08:33:51.403486'),('imp_e5d80761dd5f5cdd8bc9a6938397a562','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c95','ee26ece75ded102798f1a211a8732a29deb2737409fb670705667b10e34cf213','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_141aea81440b44e5\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_e5e58a9ebb9e57b4ac85eae9cadcb7cd','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c93','7f41648b882b00a9411a55010d6d6904ef29cd07723f472a4b6a4ad276b8d9d3','product_knowledges','{\"id\":\"pk_c88ef6931b2943f5\"}','verified','2026-11-09 08:33:51.403486'),('imp_e79e80fe6b1a5ed2967eb74e76be5818','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f5','5b331b8d2d297f872fc913e0ccd0682a890819708f36b365e37fe3ce3604d748','product_badges','{\"badge\":\"new\",\"product_id\":\"prd_0b61644f093f4610\"}','verified','2026-11-09 08:33:51.403486'),('imp_e8b25295f7de58339a66dea05a9ba508','imp_3f3bbcc2fc835f8990adadc20e4776e8','faqs','6adb149bdb3269dbc6aa4ca8','48dad9b1b459db9aac8fb09bbbe99ddc84ad4c1688c708c8bc6e4c86c4dbc1c9','faqs','{\"id\":\"faq_f9110a6950094f96\"}','verified','2026-11-09 08:33:51.403486'),('imp_e8dd8e06b76d54adbf7423dec24d8d8a','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149bdb3269dbc6aa4ca3','859f1f96be9caf0bd05a5bc912d30ed2ad685154df00c6ecd60809c3bd677ea5','product_knowledges','{\"id\":\"pk_520a512d2d97446e\"}','verified','2026-11-09 08:33:51.403486'),('imp_e9697bee05135073b4cf22cb58b53d50','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9301','2e009b77e41c61666858216e9bb2cb8cb08222e6dcba8b30b06e6c382b88bfcc','product_badges','{\"badge\":\"new\",\"product_id\":\"prd_898f994b888240ab\"}','verified','2026-11-09 08:33:51.403486'),('imp_e9ff40d0198e59c2ba83ca4ac32b2e77','imp_3f3bbcc2fc835f8990adadc20e4776e8','cms_banners','6adb139d2615a279f5cd9318','9cc906c21783da1c4cb767e0a8679d7af935bf86c8f2718dbded75409e737ea7','banners','{\"id\":\"ban_7cb3bed862e74002\"}','verified','2026-11-09 08:33:51.403486'),('imp_ea83d892614d51caa8bf022feb9e185f','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fb','4b1c490983eb289380734be486bd4444d45dfc2b5e8145a313db1b25383bbfd2','product_images','{\"product_id\":\"prd_f27e5e8e2c274d16\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_eb21e5d7595056348a804165d3ed6d8b','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9303','04f914093fba7f1ee8838b6c19a934c6795a1b3b280f33dde9910ff644ae9c3d','product_images','{\"product_id\":\"prd_bce0660e41e84eaa\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_ec1b2758105757498287400dd322a5eb','imp_3f3bbcc2fc835f8990adadc20e4776e8','brands','6adb139a2615a279f5cd92f3','4f0336e85e7f9c706178e7f240f33d14348e6f293449c1a271992695eba0e5f4','brands','{\"id\":\"brd_8d5d28e0ab264d8e\"}','verified','2026-11-09 08:33:51.403486'),('imp_ecd88ff9c2f35638b68723e54becc9ca','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f4','1cb15a116079d55768b6230f8d2e1440446235fb6a616f7561bc1b02bb6206ba','product_segments','{\"product_id\":\"prd_f2d20822dbce4da6\",\"segment\":\"Pria\"}','verified','2026-11-09 08:33:51.403486'),('imp_edc70dad236d597883c00a93127df525','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9307','5045de5b2a7815e44f61c6e223fdcf09628b23692db2561f60c7370a9fc05527','product_images','{\"product_id\":\"prd_98175a8e8a554c55\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_efacb4f7fd575786978c65bb1858f2c6','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f5','5b331b8d2d297f872fc913e0ccd0682a890819708f36b365e37fe3ce3604d748','product_images','{\"product_id\":\"prd_0b61644f093f4610\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_f0073438a2245d0fa509796fb0b51c31','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13942615a279f5cd92ba','b1869ddee1526f78148a4a54ade4db85179e8a3e5af414b64434c1f9d21a847d','categories','{\"id\":\"cat_fc53a5d7fa854ec3\"}','verified','2026-11-09 08:33:51.403486'),('imp_f05f1e93a8ed5dc1a0616d014669b99e','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f9','d17743ca6c89ae66907608bc40a89e067c4d59145d1b789a74396be1f1075d97','product_images','{\"product_id\":\"prd_401170d2b1564810\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_f098412a8d255572a3c7a08075b708db','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c96','8111c29f25b20009fb1bfa01f5827da822c0d5bad6a80a12a1f7bb73edc7fa07','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_fd6c135365384fca\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_f158963755205d5eaba348a92983c0ca','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9307','5045de5b2a7815e44f61c6e223fdcf09628b23692db2561f60c7370a9fc05527','product_images','{\"product_id\":\"prd_98175a8e8a554c55\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_f1b3bb43c8c1500bb36e5355c7e8f246','imp_3f3bbcc2fc835f8990adadc20e4776e8','faq_categories','6adb149bdb3269dbc6aa4ca4','c729613fdf17d5a9093cd057294c0ac09acbc1a376d7dc82f371ba944914bee5','faq_categories','{\"id\":\"fqc_b887263bb8694cf7\"}','verified','2026-11-09 08:33:51.403486'),('imp_f1f1c8c0ad5d574ab7a5f2490a3997c2','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c96','8111c29f25b20009fb1bfa01f5827da822c0d5bad6a80a12a1f7bb73edc7fa07','product_knowledge_bullets','{\"kind\":\"con\",\"knowledge_id\":\"pk_fd6c135365384fca\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_f30d6345bffe5f61ab8a8b9b0fbc9570','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139a2615a279f5cd92f4','1cb15a116079d55768b6230f8d2e1440446235fb6a616f7561bc1b02bb6206ba','products','{\"id\":\"prd_f2d20822dbce4da6\"}','verified','2026-11-09 08:33:51.403486'),('imp_f4502d51edf550778c66974d53bc8803','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92fa','60e71e9aafca35f2bbe54134ce638ac819a431553b2031b2c529ab1cec69fc18','product_images','{\"product_id\":\"prd_3e8ddf16743d4901\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_f4fc52dfa7a455b380367d2d910e6bb8','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c97','609e8e795f5ce0f268a90f9fe4eeb8a2382ca5cc7dc76a88f823af825c9618fc','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_2171c71a9c864d1a\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_f5dc028744b25d148b0aedd34526e764','imp_3f3bbcc2fc835f8990adadc20e4776e8','cms_banners','6adb139d2615a279f5cd9317','48e105d84623d31bfdf3e652fb8931a880b1ebcde9143607458cf166983449c4','banners','{\"id\":\"ban_f532384098fa412e\"}','verified','2026-11-09 08:33:51.403486'),('imp_f6c00301021254e9b614fa2ef1d423be','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9302','167f810d58d1d45323d3da3c1251cd4578740d00f8e58874e299aa3cc3cc6adc','product_images','{\"product_id\":\"prd_0f674d6c51e34ae1\",\"sort_order\":2}','verified','2026-11-09 08:33:51.403486'),('imp_f722ab1788f053e0917e0be4112a3e1d','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13962615a279f5cd92ca','5c952cbd0ac6f203cc562a4dba1bd308ff396f508b6da6d9a6efa359d036f697','categories','{\"id\":\"cat_2b4c108059d64203\"}','verified','2026-11-09 08:33:51.403486'),('imp_f73b53e50bca5757a4300d74ccfdfd13','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13942615a279f5cd92b8','ed804b6962249188043c90fd0cf341fffbcefcbf681ff04de46c756cbb302f42','categories','{\"id\":\"cat_deabeef8b42b4551\"}','verified','2026-11-09 08:33:51.403486'),('imp_f863368ad6de5442939ff0bf4e25729c','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9301','2e009b77e41c61666858216e9bb2cb8cb08222e6dcba8b30b06e6c382b88bfcc','product_images','{\"product_id\":\"prd_898f994b888240ab\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_f900cf4c56cc53d3a603b0b05e0f0e1e','imp_3f3bbcc2fc835f8990adadc20e4776e8','brands','6adb139a2615a279f5cd92f1','25710b63798ea79e38a386a4c909677c598d95a9debbf6a8b21c8b220783ad01','brands','{\"id\":\"brd_e78d6cf8db334a0b\"}','verified','2026-11-09 08:33:51.403486'),('imp_f950a342f8d25b8b841968bba13565ff','imp_3f3bbcc2fc835f8990adadc20e4776e8','roulette_rewards','6adb139d2615a279f5cd9311','eec3ca09e8520f9969cce669e81dfe9ece28507e62399fd2185d40054b8eab4e','roulette_rewards','{\"id\":\"rwd_2ab2dd591fb7425d\"}','verified','2026-11-09 08:33:51.403486'),('imp_fa8e7b7e431150a4aedc6658d6167865','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd92f9','d17743ca6c89ae66907608bc40a89e067c4d59145d1b789a74396be1f1075d97','product_variants','{\"id\":\"var_69aaaae26f094f85\"}','verified','2026-11-09 08:33:51.403486'),('imp_fbb198611443540894611377cc5f66e6','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139b2615a279f5cd9300','29b94c88985fa3e50253df0d4d5d9c2622c2bdf996df81376bd0ad1098551ba6','product_images','{\"product_id\":\"prd_1b6d039b016b4131\",\"sort_order\":0}','verified','2026-11-09 08:33:51.403486'),('imp_fc50e62663545c55933aeeaff87e66b6','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13982615a279f5cd92de','ff1bc7ab52b4b17016dcae3874999c6888e099fce04fb336b15a5eda9d043ce0','categories','{\"id\":\"cat_e286907b48cb4e53\"}','verified','2026-11-09 08:33:51.403486'),('imp_fc6d4edcd1cf5e0f9f4879c980bc1ee0','imp_3f3bbcc2fc835f8990adadc20e4776e8','product_knowledges','6adb149adb3269dbc6aa4c90','2da3d0df6724022145c4e308095c95f727009470595d0a45b56516e0a84345af','product_knowledge_bullets','{\"kind\":\"pro\",\"knowledge_id\":\"pk_e5fa757252be4594\",\"sort_order\":1}','verified','2026-11-09 08:33:51.403486'),('imp_fcb1a6156805559ab6bd30d4699f5dbf','imp_3f3bbcc2fc835f8990adadc20e4776e8','categories','6adb13952615a279f5cd92be','41c47b2138a84d32f02f67417eecce7e10050003d1e32088b7979c7a58600f50','categories','{\"id\":\"cat_40be3187b63b4230\"}','verified','2026-11-09 08:33:51.403486'),('imp_fe8faa3f224c5ec1a23e6215989b1a29','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9306','946414b12d755aac455846dfe413db5c8f19192b44251ebb1e2faacd5360e7d1','product_segments','{\"product_id\":\"prd_d7b3f4cfe9574460\",\"segment\":\"Wanita\"}','verified','2026-11-09 08:33:51.403486'),('imp_ff98aeed1ba5594aa10478d0840428de','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9305','4b72b62a603a8c1be8db346326205eba5574ce25ac5b82006721ae4cd0385f45','product_variants','{\"id\":\"var_d590dd75a59c4fd8\"}','verified','2026-11-09 08:33:51.403486'),('imp_ffbc0c54a73f5b47933b48efd8f82d40','imp_3f3bbcc2fc835f8990adadc20e4776e8','products','6adb139c2615a279f5cd9306','946414b12d755aac455846dfe413db5c8f19192b44251ebb1e2faacd5360e7d1','product_variants','{\"id\":\"var_8c894021e8fc46c8\"}','verified','2026-11-09 08:33:51.403486');
/*!40000 ALTER TABLE `migration_records` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_migration_records_mysql57_guard` BEFORE INSERT ON `migration_records`
FOR EACH ROW
BEGIN
  IF (NEW.`status` IN ('planned','imported','verified','rejected')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_migration_records_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_migration_records_mysql57_guard` BEFORE UPDATE ON `migration_records`
FOR EACH ROW
BEGIN
  IF (NEW.`status` IN ('planned','imported','verified','rejected')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_migration_records_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `migration_runs`
--

DROP TABLE IF EXISTS `migration_runs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `migration_runs` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `source_label` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `export_checksum` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `schema_revision` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'planned',
  `source_count` bigint(20) NOT NULL DEFAULT '0',
  `migrated_count` bigint(20) NOT NULL DEFAULT '0',
  `rejected_count` bigint(20) NOT NULL DEFAULT '0',
  `started_at` datetime(6) DEFAULT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `migration_runs`
--

LOCK TABLES `migration_runs` WRITE;
/*!40000 ALTER TABLE `migration_runs` DISABLE KEYS */;
INSERT INTO `migration_runs` VALUES ('imp_3f3bbcc2fc835f8990adadc20e4776e8','reviewed-local-export','4d07e5eef8170f50c11db6d2f71b2213e004f7f3fd1731ac76c911c483ce9a66','20261109_0003','completed',166,166,0,'2026-11-09 08:33:46.100303','2026-11-09 08:33:51.423274');
/*!40000 ALTER TABLE `migration_runs` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_migration_runs_mysql57_guard` BEFORE INSERT ON `migration_runs`
FOR EACH ROW
BEGIN
  IF (NEW.`source_count` >= 0 AND NEW.`migrated_count` >= 0 AND NEW.`rejected_count` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_migration_runs_counts failed';
  END IF;
  IF (NEW.`status` IN ('planned','running','validated','failed','completed')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_migration_runs_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_migration_runs_mysql57_guard` BEFORE UPDATE ON `migration_runs`
FOR EACH ROW
BEGIN
  IF (NEW.`source_count` >= 0 AND NEW.`migrated_count` >= 0 AND NEW.`rejected_count` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_migration_runs_counts failed';
  END IF;
  IF (NEW.`status` IN ('planned','running','validated','failed','completed')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_migration_runs_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `newsletter_campaigns`
--

DROP TABLE IF EXISTS `newsletter_campaigns`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `newsletter_campaigns` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `subject` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `body` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `segment` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'all',
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sent_count` int(11) NOT NULL DEFAULT '0',
  `failed_count` int(11) NOT NULL DEFAULT '0',
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `newsletter_campaigns`
--

LOCK TABLES `newsletter_campaigns` WRITE;
/*!40000 ALTER TABLE `newsletter_campaigns` DISABLE KEYS */;
/*!40000 ALTER TABLE `newsletter_campaigns` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_newsletter_campaigns_mysql57_guard` BEFORE INSERT ON `newsletter_campaigns`
FOR EACH ROW
BEGIN
  IF (NEW.`sent_count` >= 0 AND NEW.`failed_count` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_newsletter_campaigns_counts failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_newsletter_campaigns_mysql57_guard` BEFORE UPDATE ON `newsletter_campaigns`
FOR EACH ROW
BEGIN
  IF (NEW.`sent_count` >= 0 AND NEW.`failed_count` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_newsletter_campaigns_counts failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `newsletter_subscribers`
--

DROP TABLE IF EXISTS `newsletter_subscribers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `newsletter_subscribers` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_newsletter_subscribers_email` (`email`),
  KEY `fk_newsletter_subscribers_user_id_users_user_id` (`user_id`),
  CONSTRAINT `fk_newsletter_subscribers_user_id_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `newsletter_subscribers`
--

LOCK TABLES `newsletter_subscribers` WRITE;
/*!40000 ALTER TABLE `newsletter_subscribers` DISABLE KEYS */;
/*!40000 ALTER TABLE `newsletter_subscribers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_addresses`
--

DROP TABLE IF EXISTS `order_addresses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `order_addresses` (
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `source_address_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `source_created_at` datetime(6) DEFAULT NULL,
  `source_is_default` tinyint(1) DEFAULT NULL,
  `label` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `recipient` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `street` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `subdistrict` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `district` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `city` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `province` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `postal_code` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `country_code` varchar(2) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ID',
  `everpro_destination_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`order_id`),
  CONSTRAINT `fk_order_addresses_order_id_orders_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_addresses`
--

LOCK TABLES `order_addresses` WRITE;
/*!40000 ALTER TABLE `order_addresses` DISABLE KEYS */;
/*!40000 ALTER TABLE `order_addresses` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_item_components`
--

DROP TABLE IF EXISTS `order_item_components`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `order_item_components` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_item_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `component_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `variant_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `lens_index_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `product_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sku` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `variant_label` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `lens_index_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `quantity` int(11) NOT NULL,
  `unit_price` decimal(18,2) NOT NULL,
  `index_surcharge` decimal(18,2) NOT NULL DEFAULT '0.00',
  `subtotal` decimal(18,2) NOT NULL,
  `sort_order` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_order_item_components_id_order_id_product_id` (`id`,`order_id`,`product_id`),
  UNIQUE KEY `uq_order_item_components_order_item_id_sort_order` (`order_item_id`,`sort_order`),
  KEY `fk_order_item_components_lens_index_id_lens_indexes_id` (`lens_index_id`),
  KEY `fk_order_item_components_order_item_id_order_i_380ae62a849f` (`order_item_id`,`order_id`),
  KEY `fk_order_item_components_product_id_variant_id_30553bf82c9a` (`product_id`,`variant_id`),
  KEY `ix_order_item_components_product_id` (`product_id`),
  CONSTRAINT `fk_order_item_components_lens_index_id_lens_indexes_id` FOREIGN KEY (`lens_index_id`) REFERENCES `lens_indexes` (`id`),
  CONSTRAINT `fk_order_item_components_order_item_id_order_i_380ae62a849f` FOREIGN KEY (`order_item_id`, `order_id`) REFERENCES `order_items` (`id`, `order_id`),
  CONSTRAINT `fk_order_item_components_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `fk_order_item_components_product_id_variant_id_30553bf82c9a` FOREIGN KEY (`product_id`, `variant_id`) REFERENCES `product_variants` (`product_id`, `id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_item_components`
--

LOCK TABLES `order_item_components` WRITE;
/*!40000 ALTER TABLE `order_item_components` DISABLE KEYS */;
/*!40000 ALTER TABLE `order_item_components` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_order_item_components_mysql57_guard` BEFORE INSERT ON `order_item_components`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` > 0 AND NEW.`unit_price` >= 0 AND NEW.`subtotal` >= 0 AND NEW.`index_surcharge` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_item_components_amounts failed';
  END IF;
  IF (NEW.`component_type` IN ('primary','lens')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_item_components_type failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_order_item_components_mysql57_guard` BEFORE UPDATE ON `order_item_components`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` > 0 AND NEW.`unit_price` >= 0 AND NEW.`subtotal` >= 0 AND NEW.`index_surcharge` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_item_components_amounts failed';
  END IF;
  IF (NEW.`component_type` IN ('primary','lens')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_item_components_type failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `order_item_prescriptions`
--

DROP TABLE IF EXISTS `order_item_prescriptions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `order_item_prescriptions` (
  `order_item_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `prescription_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`order_item_id`),
  UNIQUE KEY `uq_order_item_prescriptions_prescription_id` (`prescription_id`),
  KEY `fk_order_item_prescriptions_order_id_user_id_o_97780d5632ac` (`order_id`,`user_id`),
  KEY `fk_order_item_prescriptions_order_item_id_orde_a665d0c8a4a5` (`order_item_id`,`order_id`),
  KEY `fk_order_item_prescriptions_prescription_id_us_3ffb11391bc0` (`prescription_id`,`user_id`),
  CONSTRAINT `fk_order_item_prescriptions_order_id_user_id_o_97780d5632ac` FOREIGN KEY (`order_id`, `user_id`) REFERENCES `orders` (`id`, `user_id`),
  CONSTRAINT `fk_order_item_prescriptions_order_item_id_orde_a665d0c8a4a5` FOREIGN KEY (`order_item_id`, `order_id`) REFERENCES `order_items` (`id`, `order_id`),
  CONSTRAINT `fk_order_item_prescriptions_prescription_id_us_3ffb11391bc0` FOREIGN KEY (`prescription_id`, `user_id`) REFERENCES `prescriptions` (`id`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_item_prescriptions`
--

LOCK TABLES `order_item_prescriptions` WRITE;
/*!40000 ALTER TABLE `order_item_prescriptions` DISABLE KEYS */;
/*!40000 ALTER TABLE `order_item_prescriptions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `order_items`
--

DROP TABLE IF EXISTS `order_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `order_items` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `variant_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `product_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sku` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `variant_label` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `main_image` text COLLATE utf8mb4_unicode_ci,
  `quantity` int(11) NOT NULL,
  `unit_price` decimal(18,2) NOT NULL,
  `subtotal` decimal(18,2) NOT NULL,
  `sort_order` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_order_items_id_order_id_product_id` (`id`,`order_id`,`product_id`),
  UNIQUE KEY `uq_order_items_id_order_id` (`id`,`order_id`),
  UNIQUE KEY `uq_order_items_id_product_id` (`id`,`product_id`),
  UNIQUE KEY `uq_order_items_order_id_sort_order` (`order_id`,`sort_order`),
  KEY `fk_order_items_product_id_variant_id_product_v_7663bb3c8106` (`product_id`,`variant_id`),
  KEY `ix_order_items_product_id` (`product_id`),
  CONSTRAINT `fk_order_items_order_id_orders_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`),
  CONSTRAINT `fk_order_items_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `fk_order_items_product_id_variant_id_product_v_7663bb3c8106` FOREIGN KEY (`product_id`, `variant_id`) REFERENCES `product_variants` (`product_id`, `id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_items`
--

LOCK TABLES `order_items` WRITE;
/*!40000 ALTER TABLE `order_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `order_items` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_order_items_mysql57_guard` BEFORE INSERT ON `order_items`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` > 0 AND NEW.`unit_price` >= 0 AND NEW.`subtotal` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_items_amounts failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_order_items_mysql57_guard` BEFORE UPDATE ON `order_items`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` > 0 AND NEW.`unit_price` >= 0 AND NEW.`subtotal` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_items_amounts failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `order_reviews`
--

DROP TABLE IF EXISTS `order_reviews`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `order_reviews` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `rating` smallint(6) NOT NULL,
  `body` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending',
  `admin_reply` text COLLATE utf8mb4_unicode_ci,
  `moderated_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `moderated_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_order_reviews_order_id` (`order_id`),
  KEY `fk_order_reviews_moderated_by_users_user_id` (`moderated_by`),
  KEY `fk_order_reviews_order_id_user_id_orders_id_orders_user_id` (`order_id`,`user_id`),
  CONSTRAINT `fk_order_reviews_moderated_by_users_user_id` FOREIGN KEY (`moderated_by`) REFERENCES `users` (`user_id`),
  CONSTRAINT `fk_order_reviews_order_id_user_id_orders_id_orders_user_id` FOREIGN KEY (`order_id`, `user_id`) REFERENCES `orders` (`id`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_reviews`
--

LOCK TABLES `order_reviews` WRITE;
/*!40000 ALTER TABLE `order_reviews` DISABLE KEYS */;
/*!40000 ALTER TABLE `order_reviews` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_order_reviews_mysql57_guard` BEFORE INSERT ON `order_reviews`
FOR EACH ROW
BEGIN
  IF (NEW.`rating` BETWEEN 1 AND 5) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_reviews_rating failed';
  END IF;
  IF (NEW.`status` IN ('pending','approved','rejected','hidden')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_reviews_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_order_reviews_mysql57_guard` BEFORE UPDATE ON `order_reviews`
FOR EACH ROW
BEGIN
  IF (NEW.`rating` BETWEEN 1 AND 5) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_reviews_rating failed';
  END IF;
  IF (NEW.`status` IN ('pending','approved','rejected','hidden')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_order_reviews_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `order_status_logs`
--

DROP TABLE IF EXISTS `order_status_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `order_status_logs` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `note` text COLLATE utf8mb4_unicode_ci,
  `admin_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `fk_order_status_logs_admin_id_users_user_id` (`admin_id`),
  KEY `ix_order_status_logs_timeline` (`order_id`,`created_at`,`id`),
  CONSTRAINT `fk_order_status_logs_admin_id_users_user_id` FOREIGN KEY (`admin_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `fk_order_status_logs_order_id_orders_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `order_status_logs`
--

LOCK TABLES `order_status_logs` WRITE;
/*!40000 ALTER TABLE `order_status_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `order_status_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `orders` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_number` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `subtotal` decimal(18,2) NOT NULL,
  `discount` decimal(18,2) NOT NULL DEFAULT '0.00',
  `flash_sale_discount` decimal(18,2) NOT NULL DEFAULT '0.00',
  `voucher_code` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `voucher_discount` decimal(18,2) NOT NULL DEFAULT '0.00',
  `points_used` bigint(20) NOT NULL DEFAULT '0',
  `points_discount` decimal(18,2) NOT NULL DEFAULT '0.00',
  `roulette_discount` decimal(18,2) NOT NULL DEFAULT '0.00',
  `shipping_quote_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `shipping_courier` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `shipping_service` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `shipping_cost` decimal(18,2) NOT NULL,
  `total` decimal(18,2) NOT NULL,
  `currency` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'IDR',
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending_payment',
  `payment_status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending',
  `shipment_status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending',
  `reservation_expires_at` datetime(6) DEFAULT NULL,
  `completed_at` datetime(6) DEFAULT NULL,
  `checkout_idempotency_key` varchar(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_orders_id_user_id` (`id`,`user_id`),
  UNIQUE KEY `uq_orders_order_number` (`order_number`),
  UNIQUE KEY `uq_orders_checkout_idempotency_key` (`checkout_idempotency_key`),
  KEY `fk_orders_shipping_quote_id_user_id_shipping_q_5bb98f5fe9ef` (`shipping_quote_id`,`user_id`),
  KEY `ix_orders_customer_date` (`user_id`,`created_at`,`id`),
  KEY `ix_orders_expiry` (`status`,`reservation_expires_at`,`id`),
  KEY `ix_orders_payment_date` (`payment_status`,`created_at`),
  KEY `ix_orders_shipment_status` (`shipment_status`,`updated_at`),
  CONSTRAINT `fk_orders_shipping_quote_id_user_id_shipping_q_5bb98f5fe9ef` FOREIGN KEY (`shipping_quote_id`, `user_id`) REFERENCES `shipping_quotes` (`id`, `user_id`),
  CONSTRAINT `fk_orders_user_id_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_orders_mysql57_guard` BEFORE INSERT ON `orders`
FOR EACH ROW
BEGIN
  IF (NEW.`points_used` >= 0 AND NEW.`points_discount` >= 0 AND NEW.`roulette_discount` >= 0 AND NEW.`shipping_cost` >= 0 AND NEW.`total` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_amounts failed';
  END IF;
  IF (NEW.`subtotal` >= 0 AND NEW.`discount` >= 0 AND NEW.`flash_sale_discount` >= 0 AND NEW.`voucher_discount` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_discount_amounts failed';
  END IF;
  IF (NEW.`payment_status` IN ('pending','paid','failed','expired','cancelled','refunded')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_payment_status failed';
  END IF;
  IF (NEW.`shipment_status` IN ('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_shipment_status failed';
  END IF;
  IF (NEW.`status` IN ('pending_payment','paid','processing','shipped','completed','cancelled','expired','refunded')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_orders_mysql57_guard` BEFORE UPDATE ON `orders`
FOR EACH ROW
BEGIN
  IF (NEW.`points_used` >= 0 AND NEW.`points_discount` >= 0 AND NEW.`roulette_discount` >= 0 AND NEW.`shipping_cost` >= 0 AND NEW.`total` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_amounts failed';
  END IF;
  IF (NEW.`subtotal` >= 0 AND NEW.`discount` >= 0 AND NEW.`flash_sale_discount` >= 0 AND NEW.`voucher_discount` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_discount_amounts failed';
  END IF;
  IF (NEW.`payment_status` IN ('pending','paid','failed','expired','cancelled','refunded')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_payment_status failed';
  END IF;
  IF (NEW.`shipment_status` IN ('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_shipment_status failed';
  END IF;
  IF (NEW.`status` IN ('pending_payment','paid','processing','shipped','completed','cancelled','expired','refunded')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_orders_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `payment_logs`
--

DROP TABLE IF EXISTS `payment_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `payment_logs` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `payment_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `provider` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `action` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `payload` json DEFAULT NULL,
  `response` json DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `fk_payment_logs_payment_id_order_id_payments_i_50865612f320` (`payment_id`,`order_id`),
  KEY `ix_payment_logs_order_date` (`order_id`,`created_at`,`id`),
  CONSTRAINT `fk_payment_logs_order_id_orders_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`),
  CONSTRAINT `fk_payment_logs_payment_id_order_id_payments_i_50865612f320` FOREIGN KEY (`payment_id`, `order_id`) REFERENCES `payments` (`id`, `order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payment_logs`
--

LOCK TABLES `payment_logs` WRITE;
/*!40000 ALTER TABLE `payment_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `payment_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payments`
--

DROP TABLE IF EXISTS `payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `payments` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `provider` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'doku',
  `request_id` varchar(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `merchant_reference` varchar(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `external_id` varchar(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `amount` decimal(18,2) NOT NULL,
  `currency` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'IDR',
  `method` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `channel` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending',
  `payment_url` text COLLATE utf8mb4_unicode_ci,
  `virtual_account_number` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `expires_at` datetime(6) DEFAULT NULL,
  `paid_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_payments_id_order_id` (`id`,`order_id`),
  UNIQUE KEY `uq_payments_provider_merchant_reference` (`provider`,`merchant_reference`),
  UNIQUE KEY `uq_payments_provider_request_id` (`provider`,`request_id`),
  UNIQUE KEY `uq_payments_provider_external_id` (`provider`,`external_id`),
  KEY `ix_payments_order_status` (`order_id`,`status`,`created_at`),
  CONSTRAINT `fk_payments_order_id_orders_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payments`
--

LOCK TABLES `payments` WRITE;
/*!40000 ALTER TABLE `payments` DISABLE KEYS */;
/*!40000 ALTER TABLE `payments` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_payments_mysql57_guard` BEFORE INSERT ON `payments`
FOR EACH ROW
BEGIN
  IF (NEW.`amount` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_payments_amount failed';
  END IF;
  IF (NEW.`status` IN ('pending','paid','failed','expired','cancelled','refunded')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_payments_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_payments_mysql57_guard` BEFORE UPDATE ON `payments`
FOR EACH ROW
BEGIN
  IF (NEW.`amount` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_payments_amount failed';
  END IF;
  IF (NEW.`status` IN ('pending','paid','failed','expired','cancelled','refunded')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_payments_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `point_logs`
--

DROP TABLE IF EXISTS `point_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `point_logs` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `delta` bigint(20) NOT NULL,
  `balance_after` bigint(20) NOT NULL,
  `type` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `note` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `fk_point_logs_order_id_orders_id` (`order_id`),
  KEY `ix_point_logs_user_type_date` (`user_id`,`type`,`created_at`,`id`),
  CONSTRAINT `fk_point_logs_order_id_orders_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`),
  CONSTRAINT `fk_point_logs_user_id_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `point_logs`
--

LOCK TABLES `point_logs` WRITE;
/*!40000 ALTER TABLE `point_logs` DISABLE KEYS */;
INSERT INTO `point_logs` VALUES ('pts_2e0d1bbc4bd045e9','usr_c4b3d45ff0b94ffd',28,28,'earn_game','Game puzzle score=280',NULL,'2026-11-10 02:21:15.841499'),('pts_622c9fba29c042b6','usr_c4b3d45ff0b94ffd',45,73,'earn_game','Game matching score=450',NULL,'2026-11-10 02:22:00.476186');
/*!40000 ALTER TABLE `point_logs` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_point_logs_mysql57_guard` BEFORE INSERT ON `point_logs`
FOR EACH ROW
BEGIN
  IF (NEW.`balance_after` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_point_logs_balance failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_point_logs_mysql57_guard` BEFORE UPDATE ON `point_logs`
FOR EACH ROW
BEGIN
  IF (NEW.`balance_after` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_point_logs_balance failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `prescription_eyes`
--

DROP TABLE IF EXISTS `prescription_eyes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `prescription_eyes` (
  `prescription_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `eye` varchar(5) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sph` decimal(5,2) DEFAULT NULL,
  `cyl` decimal(5,2) DEFAULT NULL,
  `axis` smallint(6) DEFAULT NULL,
  `add` decimal(5,2) DEFAULT NULL,
  PRIMARY KEY (`prescription_id`,`eye`),
  CONSTRAINT `fk_prescription_eyes_prescription_id_prescriptions_id` FOREIGN KEY (`prescription_id`) REFERENCES `prescriptions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `prescription_eyes`
--

LOCK TABLES `prescription_eyes` WRITE;
/*!40000 ALTER TABLE `prescription_eyes` DISABLE KEYS */;
INSERT INTO `prescription_eyes` VALUES ('rx_8a7793124f314342','left',0.00,0.00,NULL,NULL),('rx_8a7793124f314342','right',0.00,0.00,NULL,NULL);
/*!40000 ALTER TABLE `prescription_eyes` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_prescription_eyes_mysql57_guard` BEFORE INSERT ON `prescription_eyes`
FOR EACH ROW
BEGIN
  IF (NEW.`axis` IS NULL OR NEW.`axis` BETWEEN 0 AND 180) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescription_eyes_axis failed';
  END IF;
  IF (NEW.`eye` IN ('right','left')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescription_eyes_eye failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_prescription_eyes_mysql57_guard` BEFORE UPDATE ON `prescription_eyes`
FOR EACH ROW
BEGIN
  IF (NEW.`axis` IS NULL OR NEW.`axis` BETWEEN 0 AND 180) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescription_eyes_axis failed';
  END IF;
  IF (NEW.`eye` IN ('right','left')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescription_eyes_eye failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `prescriptions`
--

DROP TABLE IF EXISTS `prescriptions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `prescriptions` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `pd_total` decimal(5,2) DEFAULT NULL,
  `pd_right` decimal(5,2) DEFAULT NULL,
  `pd_left` decimal(5,2) DEFAULT NULL,
  `attachment_upload_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `is_order_snapshot` tinyint(1) NOT NULL DEFAULT '0',
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_prescriptions_id_user_id` (`id`,`user_id`),
  KEY `fk_prescriptions_attachment_upload_id_uploads_id` (`attachment_upload_id`),
  KEY `ix_prescriptions_user_id` (`user_id`),
  CONSTRAINT `fk_prescriptions_attachment_upload_id_uploads_id` FOREIGN KEY (`attachment_upload_id`) REFERENCES `uploads` (`id`),
  CONSTRAINT `fk_prescriptions_user_id_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `prescriptions`
--

LOCK TABLES `prescriptions` WRITE;
/*!40000 ALTER TABLE `prescriptions` DISABLE KEYS */;
INSERT INTO `prescriptions` VALUES ('rx_8a7793124f314342','usr_c4b3d45ff0b94ffd',NULL,NULL,NULL,NULL,NULL,0,'2026-11-09 08:42:43.603881','2026-11-09 08:42:43.604003'),('rx_f2471c57bdb444f3','usr_c4b3d45ff0b94ffd',NULL,NULL,NULL,'4065c8756ccb44b0be2936273e648135',NULL,0,'2026-11-09 09:23:03.875548','2026-11-09 09:23:03.875553');
/*!40000 ALTER TABLE `prescriptions` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_prescriptions_mysql57_guard` BEFORE INSERT ON `prescriptions`
FOR EACH ROW
BEGIN
  IF (NEW.`pd_left` IS NULL OR NEW.`pd_left` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_left failed';
  END IF;
  IF (NEW.`pd_total` IS NULL OR (NEW.`pd_right` IS NULL AND NEW.`pd_left` IS NULL)) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_mode failed';
  END IF;
  IF ((NEW.`pd_right` IS NULL AND NEW.`pd_left` IS NULL) OR (NEW.`pd_right` IS NOT NULL AND NEW.`pd_left` IS NOT NULL)) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_pair failed';
  END IF;
  IF (NEW.`pd_right` IS NULL OR NEW.`pd_right` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_right failed';
  END IF;
  IF (NEW.`pd_total` IS NULL OR NEW.`pd_total` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_total failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_prescriptions_mysql57_guard` BEFORE UPDATE ON `prescriptions`
FOR EACH ROW
BEGIN
  IF (NEW.`pd_left` IS NULL OR NEW.`pd_left` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_left failed';
  END IF;
  IF (NEW.`pd_total` IS NULL OR (NEW.`pd_right` IS NULL AND NEW.`pd_left` IS NULL)) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_mode failed';
  END IF;
  IF ((NEW.`pd_right` IS NULL AND NEW.`pd_left` IS NULL) OR (NEW.`pd_right` IS NOT NULL AND NEW.`pd_left` IS NOT NULL)) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_pair failed';
  END IF;
  IF (NEW.`pd_right` IS NULL OR NEW.`pd_right` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_right failed';
  END IF;
  IF (NEW.`pd_total` IS NULL OR NEW.`pd_total` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_prescriptions_pd_total failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `product_badges`
--

DROP TABLE IF EXISTS `product_badges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `product_badges` (
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `badge` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`product_id`,`badge`),
  KEY `ix_product_badges_badge` (`badge`,`product_id`),
  CONSTRAINT `fk_product_badges_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_badges`
--

LOCK TABLES `product_badges` WRITE;
/*!40000 ALTER TABLE `product_badges` DISABLE KEYS */;
INSERT INTO `product_badges` VALUES ('prd_0b61644f093f4610','new'),('prd_0f674d6c51e34ae1','bestseller'),('prd_1b6d039b016b4131','new'),('prd_26aa3608a7084627','new'),('prd_401170d2b1564810','bestseller'),('prd_401170d2b1564810','flashsale'),('prd_75466e5b7e5c4775','bestseller'),('prd_898f994b888240ab','new'),('prd_a1911ea875294d3a','bestseller'),('prd_d7b3f4cfe9574460','new'),('prd_df7a0e382fa14177','new'),('prd_f27e5e8e2c274d16','new'),('prd_f2d20822dbce4da6','bestseller'),('prd_f2d20822dbce4da6','new'),('prd_fbef635ed7514c8f','bestseller');
/*!40000 ALTER TABLE `product_badges` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_categories`
--

DROP TABLE IF EXISTS `product_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `product_categories` (
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `category_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`product_id`,`category_id`),
  KEY `ix_product_categories_category` (`category_id`,`product_id`),
  CONSTRAINT `fk_product_categories_category_id_categories_id` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`),
  CONSTRAINT `fk_product_categories_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_categories`
--

LOCK TABLES `product_categories` WRITE;
/*!40000 ALTER TABLE `product_categories` DISABLE KEYS */;
INSERT INTO `product_categories` VALUES ('prd_0b61644f093f4610','cat_4bb0610322c04fae'),('prd_0b61644f093f4610','cat_67fb4e6c624a4ce0'),('prd_0b61644f093f4610','cat_f9a1ff0356e24b14'),('prd_0f674d6c51e34ae1','cat_1e21dafc7f3c4850'),('prd_0f674d6c51e34ae1','cat_86849a3a92084a57'),('prd_1b6d039b016b4131','cat_263c673054d14d28'),('prd_1b6d039b016b4131','cat_64cac2c66f40435e'),('prd_1b6d039b016b4131','cat_f9a1ff0356e24b14'),('prd_26aa3608a7084627','cat_2770f9ae4fb747c5'),('prd_26aa3608a7084627','cat_90943cf30dee4098'),('prd_26aa3608a7084627','cat_f9a1ff0356e24b14'),('prd_3e8ddf16743d4901','cat_deabeef8b42b4551'),('prd_3e8ddf16743d4901','cat_f9a1ff0356e24b14'),('prd_3e8ddf16743d4901','cat_fc53a5d7fa854ec3'),('prd_401170d2b1564810','cat_deabeef8b42b4551'),('prd_401170d2b1564810','cat_f9a1ff0356e24b14'),('prd_401170d2b1564810','cat_fc53a5d7fa854ec3'),('prd_52253b4c63584c54','cat_0882be6403ac4ec8'),('prd_52253b4c63584c54','cat_1e21dafc7f3c4850'),('prd_75466e5b7e5c4775','cat_67fb4e6c624a4ce0'),('prd_75466e5b7e5c4775','cat_c8db483f74e047f0'),('prd_75466e5b7e5c4775','cat_f9a1ff0356e24b14'),('prd_7ba6732284b649c8','cat_7c376dc73fc34a3f'),('prd_7ba6732284b649c8','cat_ee34eb85616b40e4'),('prd_7ba6732284b649c8','cat_f9a1ff0356e24b14'),('prd_898f994b888240ab','cat_021c207590d34a14'),('prd_898f994b888240ab','cat_ca9d440a48d64e4b'),('prd_898f994b888240ab','cat_f9a1ff0356e24b14'),('prd_98175a8e8a554c55','cat_3502c02ad4ac4d8d'),('prd_98175a8e8a554c55','cat_8e2e391496d84aba'),('prd_a1911ea875294d3a','cat_71b46a9ac639436a'),('prd_a1911ea875294d3a','cat_8e2e391496d84aba'),('prd_bce0660e41e84eaa','cat_1e21dafc7f3c4850'),('prd_bce0660e41e84eaa','cat_a57421c7ee3b4826'),('prd_cb46f21f4ef446f3','cat_4ab3c4baea774537'),('prd_cb46f21f4ef446f3','cat_c67d33f78ebb4d52'),('prd_cb46f21f4ef446f3','cat_f9a1ff0356e24b14'),('prd_d7b3f4cfe9574460','cat_8e2e391496d84aba'),('prd_d7b3f4cfe9574460','cat_d1cf64ed5dbe41af'),('prd_df7a0e382fa14177','cat_67fb4e6c624a4ce0'),('prd_df7a0e382fa14177','cat_f4e07e43d00145b7'),('prd_df7a0e382fa14177','cat_f9a1ff0356e24b14'),('prd_f1a4277d4ba84cd1','cat_67fb4e6c624a4ce0'),('prd_f1a4277d4ba84cd1','cat_c8db483f74e047f0'),('prd_f1a4277d4ba84cd1','cat_f9a1ff0356e24b14'),('prd_f27e5e8e2c274d16','cat_40be3187b63b4230'),('prd_f27e5e8e2c274d16','cat_7c376dc73fc34a3f'),('prd_f27e5e8e2c274d16','cat_f9a1ff0356e24b14'),('prd_f2d20822dbce4da6','cat_4bb0610322c04fae'),('prd_f2d20822dbce4da6','cat_67fb4e6c624a4ce0'),('prd_f2d20822dbce4da6','cat_f9a1ff0356e24b14'),('prd_fbef635ed7514c8f','cat_ab44ff7d3aec41d7'),('prd_fbef635ed7514c8f','cat_b3f1b68fb5a64695'),('prd_fbef635ed7514c8f','cat_f9a1ff0356e24b14');
/*!40000 ALTER TABLE `product_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_frame_specifications`
--

DROP TABLE IF EXISTS `product_frame_specifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `product_frame_specifications` (
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `a` decimal(7,2) DEFAULT NULL,
  `b` decimal(7,2) DEFAULT NULL,
  `dbl` decimal(7,2) DEFAULT NULL,
  `ed` decimal(7,2) DEFAULT NULL,
  `temple_length` decimal(7,2) DEFAULT NULL,
  `symmetric` tinyint(1) NOT NULL DEFAULT '0',
  `enabled` tinyint(1) NOT NULL DEFAULT '0',
  `source_note` text COLLATE utf8mb4_unicode_ci,
  `version` int(11) NOT NULL DEFAULT '1',
  `updated_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`product_id`),
  KEY `fk_product_frame_specifications_updated_by_users_user_id` (`updated_by`),
  CONSTRAINT `fk_product_frame_specifications_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_product_frame_specifications_updated_by_users_user_id` FOREIGN KEY (`updated_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_frame_specifications`
--

LOCK TABLES `product_frame_specifications` WRITE;
/*!40000 ALTER TABLE `product_frame_specifications` DISABLE KEYS */;
INSERT INTO `product_frame_specifications` VALUES ('prd_898f994b888240ab',50.00,40.00,18.00,60.00,NULL,1,1,'',1,'usr_c4b3d45ff0b94ffd','2026-11-09 08:46:40.579311','2026-11-09 08:46:40.579314');
/*!40000 ALTER TABLE `product_frame_specifications` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_product_frame_specifications_bi` BEFORE INSERT ON `product_frame_specifications`
FOR EACH ROW
BEGIN
  IF ((NEW.`a` IS NULL OR NEW.`a` > 0) AND (NEW.`b` IS NULL OR NEW.`b` > 0) AND (NEW.`dbl` IS NULL OR NEW.`dbl` > 0) AND (NEW.`ed` IS NULL OR NEW.`ed` > 0) AND (NEW.`temple_length` IS NULL OR NEW.`temple_length` > 0)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_frame_specifications_dimensions failed'; END IF;
  IF (NEW.`symmetric` IN (0,1) AND NEW.`enabled` IN (0,1)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_frame_specifications_flags failed'; END IF;
  IF (NEW.`version` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_frame_specifications_version failed'; END IF;
  IF NOT EXISTS (SELECT 1 FROM products WHERE id = NEW.product_id AND product_type = 'frame') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Frame specification requires a frame product'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_product_frame_specifications_bu` BEFORE UPDATE ON `product_frame_specifications`
FOR EACH ROW
BEGIN
  IF ((NEW.`a` IS NULL OR NEW.`a` > 0) AND (NEW.`b` IS NULL OR NEW.`b` > 0) AND (NEW.`dbl` IS NULL OR NEW.`dbl` > 0) AND (NEW.`ed` IS NULL OR NEW.`ed` > 0) AND (NEW.`temple_length` IS NULL OR NEW.`temple_length` > 0)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_frame_specifications_dimensions failed'; END IF;
  IF (NEW.`symmetric` IN (0,1) AND NEW.`enabled` IN (0,1)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_frame_specifications_flags failed'; END IF;
  IF (NEW.`version` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_frame_specifications_version failed'; END IF;
  IF NOT EXISTS (SELECT 1 FROM products WHERE id = NEW.product_id AND product_type = 'frame') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Frame specification requires a frame product'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `product_images`
--

DROP TABLE IF EXISTS `product_images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `product_images` (
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `sort_order` int(11) NOT NULL,
  `image_url` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `alt_text` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`product_id`,`sort_order`),
  CONSTRAINT `fk_product_images_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_images`
--

LOCK TABLES `product_images` WRITE;
/*!40000 ALTER TABLE `product_images` DISABLE KEYS */;
INSERT INTO `product_images` VALUES ('prd_0b61644f093f4610',0,'https://images.unsplash.com/photo-1618677366787-9727aacca7ea?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_0b61644f093f4610',1,'https://images.unsplash.com/photo-1574258495973-f010dfbb5371?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_0b61644f093f4610',2,'https://images.unsplash.com/photo-1577803645773-f96470509666?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_0f674d6c51e34ae1',0,'https://images.unsplash.com/photo-1574258495973-f010dfbb5371?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_0f674d6c51e34ae1',1,'https://images.unsplash.com/photo-1577803645773-f96470509666?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_0f674d6c51e34ae1',2,'https://images.unsplash.com/photo-1556306535-0f09a537f0a3?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_1b6d039b016b4131',0,'https://images.unsplash.com/photo-1772009288423-96090d2998c7?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_1b6d039b016b4131',1,'https://images.unsplash.com/photo-1618677366787-9727aacca7ea?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_1b6d039b016b4131',2,'https://images.unsplash.com/photo-1574258495973-f010dfbb5371?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_26aa3608a7084627',0,'https://images.unsplash.com/photo-1601924994987-69e26d50dc26?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_26aa3608a7084627',1,'https://images.unsplash.com/photo-1591076482161-42ce6da69f67?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_26aa3608a7084627',2,'https://images.unsplash.com/photo-1581290447921-b54aaca33ac2?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_3e8ddf16743d4901',0,'https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_3e8ddf16743d4901',1,'https://images.unsplash.com/photo-1508296695146-257a814070b4?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_3e8ddf16743d4901',2,'https://images.unsplash.com/photo-1633621641966-23836fcafd7b?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_401170d2b1564810',0,'https://images.unsplash.com/photo-1511499767150-a48a237f0083?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_401170d2b1564810',1,'https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_401170d2b1564810',2,'https://images.unsplash.com/photo-1508296695146-257a814070b4?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_52253b4c63584c54',0,'https://images.unsplash.com/photo-1556306535-0f09a537f0a3?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_52253b4c63584c54',1,'https://images.unsplash.com/photo-1511499767150-a48a237f0083?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_52253b4c63584c54',2,'https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_75466e5b7e5c4775',0,'https://images.unsplash.com/photo-1574258495973-f010dfbb5371?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_75466e5b7e5c4775',1,'https://images.unsplash.com/photo-1577803645773-f96470509666?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_75466e5b7e5c4775',2,'https://images.unsplash.com/photo-1556306535-0f09a537f0a3?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_7ba6732284b649c8',0,'https://images.unsplash.com/photo-1633621641966-23836fcafd7b?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_7ba6732284b649c8',1,'https://images.unsplash.com/photo-1601924994987-69e26d50dc26?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_7ba6732284b649c8',2,'https://images.unsplash.com/photo-1591076482161-42ce6da69f67?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_898f994b888240ab',0,'https://images.unsplash.com/photo-1618677366787-9727aacca7ea?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_898f994b888240ab',1,'https://images.unsplash.com/photo-1574258495973-f010dfbb5371?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_898f994b888240ab',2,'https://images.unsplash.com/photo-1577803645773-f96470509666?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_98175a8e8a554c55',0,'https://images.unsplash.com/photo-1508296695146-257a814070b4?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_98175a8e8a554c55',1,'https://images.unsplash.com/photo-1633621641966-23836fcafd7b?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_98175a8e8a554c55',2,'https://images.unsplash.com/photo-1601924994987-69e26d50dc26?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_a1911ea875294d3a',0,'https://images.unsplash.com/photo-1511499767150-a48a237f0083?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_a1911ea875294d3a',1,'https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_a1911ea875294d3a',2,'https://images.unsplash.com/photo-1508296695146-257a814070b4?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_bce0660e41e84eaa',0,'https://images.unsplash.com/photo-1577803645773-f96470509666?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_bce0660e41e84eaa',1,'https://images.unsplash.com/photo-1556306535-0f09a537f0a3?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_bce0660e41e84eaa',2,'https://images.unsplash.com/photo-1511499767150-a48a237f0083?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_cb46f21f4ef446f3',0,'https://images.unsplash.com/photo-1581290447921-b54aaca33ac2?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_cb46f21f4ef446f3',1,'https://images.unsplash.com/photo-1772009288423-96090d2998c7?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_cb46f21f4ef446f3',2,'https://images.unsplash.com/photo-1618677366787-9727aacca7ea?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_d7b3f4cfe9574460',0,'https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_d7b3f4cfe9574460',1,'https://images.unsplash.com/photo-1508296695146-257a814070b4?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_d7b3f4cfe9574460',2,'https://images.unsplash.com/photo-1633621641966-23836fcafd7b?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_df7a0e382fa14177',0,'https://images.unsplash.com/photo-1556306535-0f09a537f0a3?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_df7a0e382fa14177',1,'https://images.unsplash.com/photo-1511499767150-a48a237f0083?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_df7a0e382fa14177',2,'https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_f1a4277d4ba84cd1',0,'https://images.unsplash.com/photo-1577803645773-f96470509666?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_f1a4277d4ba84cd1',1,'https://images.unsplash.com/photo-1556306535-0f09a537f0a3?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_f1a4277d4ba84cd1',2,'https://images.unsplash.com/photo-1511499767150-a48a237f0083?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_f27e5e8e2c274d16',0,'https://images.unsplash.com/photo-1508296695146-257a814070b4?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_f27e5e8e2c274d16',1,'https://images.unsplash.com/photo-1633621641966-23836fcafd7b?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_f27e5e8e2c274d16',2,'https://images.unsplash.com/photo-1601924994987-69e26d50dc26?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_f2d20822dbce4da6',0,'https://images.unsplash.com/photo-1772009288423-96090d2998c7?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_f2d20822dbce4da6',1,'https://images.unsplash.com/photo-1618677366787-9727aacca7ea?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_f2d20822dbce4da6',2,'https://images.unsplash.com/photo-1574258495973-f010dfbb5371?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_fbef635ed7514c8f',0,'https://images.unsplash.com/photo-1591076482161-42ce6da69f67?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_fbef635ed7514c8f',1,'https://images.unsplash.com/photo-1581290447921-b54aaca33ac2?crop=entropy&cs=srgb&fm=jpg&w=900',NULL),('prd_fbef635ed7514c8f',2,'https://images.unsplash.com/photo-1772009288423-96090d2998c7?crop=entropy&cs=srgb&fm=jpg&w=900',NULL);
/*!40000 ALTER TABLE `product_images` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_knowledge_bullets`
--

DROP TABLE IF EXISTS `product_knowledge_bullets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `product_knowledge_bullets` (
  `knowledge_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `kind` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sort_order` int(11) NOT NULL,
  `body` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`knowledge_id`,`kind`,`sort_order`),
  CONSTRAINT `fk_product_knowledge_bullets_knowledge_id_prod_841a09e24921` FOREIGN KEY (`knowledge_id`) REFERENCES `product_knowledges` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_knowledge_bullets`
--

LOCK TABLES `product_knowledge_bullets` WRITE;
/*!40000 ALTER TABLE `product_knowledge_bullets` DISABLE KEYS */;
INSERT INTO `product_knowledge_bullets` VALUES ('pk_141aea81440b44e5','con',0,'Kurang cocok wajah minus tinggi'),('pk_141aea81440b44e5','pro',0,'Ringan'),('pk_141aea81440b44e5','pro',1,'Formal'),('pk_1f46da3523494cc3','con',0,'Bisa terlalu besar untuk wajah kecil'),('pk_1f46da3523494cc3','pro',0,'Menutupi lebih banyak wajah'),('pk_1f46da3523494cc3','pro',1,'Trend'),('pk_2171c71a9c864d1a','con',0,'Bisa berat'),('pk_2171c71a9c864d1a','con',1,'Bisa berkarat'),('pk_2171c71a9c864d1a','pro',0,'Tipis'),('pk_2171c71a9c864d1a','pro',1,'Kokoh'),('pk_2414f501c7e3484c','con',0,'Harga tinggi'),('pk_2414f501c7e3484c','pro',0,'Multifungsi'),('pk_30cd2cb1236144ec','con',0,'Kurang cocok wajah persegi'),('pk_30cd2cb1236144ec','pro',0,'Tegas'),('pk_30cd2cb1236144ec','pro',1,'Mudah dipadukan'),('pk_404d444bcfca48eb','con',0,'Terlihat kurang premium'),('pk_404d444bcfca48eb','pro',0,'Fleksibel'),('pk_404d444bcfca48eb','pro',1,'Anti pecah'),('pk_65c16b9faf834556','con',0,'Kurang formal'),('pk_65c16b9faf834556','pro',0,'Timeless'),('pk_65c16b9faf834556','pro',1,'Cocok semua umur'),('pk_6f3104e2d8424751','con',0,'Harga premium'),('pk_6f3104e2d8424751','pro',0,'Sangat ringan'),('pk_6f3104e2d8424751','pro',1,'Hypoallergenic'),('pk_6f3104e2d8424751','pro',2,'Tahan karat'),('pk_75000d7042714b61','con',0,'Sedikit berat'),('pk_75000d7042714b61','pro',0,'Kokoh'),('pk_80532004402849fe','con',0,'Kurang cocok untuk wajah bulat'),('pk_80532004402849fe','pro',0,'Ringan'),('pk_80532004402849fe','pro',1,'Klasik'),('pk_9a8e2684030547c1','pro',0,'Termurah'),('pk_c88ef6931b2943f5','pro',0,'Simpel'),('pk_c88ef6931b2943f5','pro',1,'Serbaguna'),('pk_e5fa757252be4594','con',0,'Mungkin terlihat mencolok'),('pk_e5fa757252be4594','pro',0,'Ikonik'),('pk_e5fa757252be4594','pro',1,'Fashionable'),('pk_ecae6a569bd84944','pro',0,'Baik untuk WFH'),('pk_f1e4dd9e53b541fa','con',0,'Butuh adaptasi'),('pk_f1e4dd9e53b541fa','pro',0,'Untuk usia 40+'),('pk_fb7955a67278482c','pro',0,'Nyaman'),('pk_fd6c135365384fca','con',0,'Bisa memuai bila panas'),('pk_fd6c135365384fca','pro',0,'Ringan'),('pk_fd6c135365384fca','pro',1,'Warna beragam'),('pk_fd6c135365384fca','pro',2,'Nyaman dipakai lama');
/*!40000 ALTER TABLE `product_knowledge_bullets` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_product_knowledge_bullets_mysql57_guard` BEFORE INSERT ON `product_knowledge_bullets`
FOR EACH ROW
BEGIN
  IF (NEW.`kind` IN ('pro','con')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_knowledge_bullets_kind failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_product_knowledge_bullets_mysql57_guard` BEFORE UPDATE ON `product_knowledge_bullets`
FOR EACH ROW
BEGIN
  IF (NEW.`kind` IN ('pro','con')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_knowledge_bullets_kind failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `product_knowledge_products`
--

DROP TABLE IF EXISTS `product_knowledge_products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `product_knowledge_products` (
  `knowledge_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `sort_order` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`knowledge_id`,`product_id`),
  KEY `fk_product_knowledge_products_product_id_products_id` (`product_id`),
  CONSTRAINT `fk_product_knowledge_products_knowledge_id_pro_7120bf35fe3c` FOREIGN KEY (`knowledge_id`) REFERENCES `product_knowledges` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_product_knowledge_products_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_knowledge_products`
--

LOCK TABLES `product_knowledge_products` WRITE;
/*!40000 ALTER TABLE `product_knowledge_products` DISABLE KEYS */;
/*!40000 ALTER TABLE `product_knowledge_products` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_knowledges`
--

DROP TABLE IF EXISTS `product_knowledges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `product_knowledges` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `knowledge_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `slug` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `content` mediumtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `image` text COLLATE utf8mb4_unicode_ci,
  `icon` text COLLATE utf8mb4_unicode_ci,
  `face_shape_recommendation` text COLLATE utf8mb4_unicode_ci,
  `style_recommendation` text COLLATE utf8mb4_unicode_ci,
  `filter_param` json DEFAULT NULL,
  `sort_order` int(11) NOT NULL DEFAULT '0',
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'draft',
  `seo_title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `seo_description` text COLLATE utf8mb4_unicode_ci,
  `published_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_product_knowledges_slug` (`slug`),
  KEY `ix_knowledge_public` (`knowledge_type`,`status`,`sort_order`,`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_knowledges`
--

LOCK TABLES `product_knowledges` WRITE;
/*!40000 ALTER TABLE `product_knowledges` DISABLE KEYS */;
INSERT INTO `product_knowledges` VALUES ('pk_141aea81440b44e5','frame_shape','Frame Rimless','frame-rimless','Tanpa bingkai — invisible frame.','<p>Tanpa bingkai — invisible frame.</p>','https://images.unsplash.com/photo-1508296695146-257a814070b4?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,'Semua wajah','Minimalis, Profesional','{\"badge\": null}',7,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.641540','2026-10-23 08:02:34.641540'),('pk_1f46da3523494cc3','frame_shape','Frame Oversized','frame-oversized','Frame besar, statement piece.','<p>Frame besar, statement piece.</p>','https://images.unsplash.com/photo-1591076482161-42ce6da69f67?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,'Wajah Oval, Kotak','Bold, Fashion','{\"badge\": null}',6,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.616768','2026-10-23 08:02:34.616768'),('pk_2171c71a9c864d1a','material','Metal','material-metal','Frame logam klasik, tipis & elegan.','<p>Frame logam klasik, tipis & elegan.</p>','https://images.unsplash.com/photo-1574258495973-f010dfbb5371?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,NULL,NULL,'null',1,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.702723','2026-10-23 08:02:34.702723'),('pk_2414f501c7e3484c','lens_type','Lensa Photochromic','lensa-photochromic','Berubah gelap saat kena UV.','<p>Berubah gelap saat kena UV.</p>','https://images.unsplash.com/photo-1601924994987-69e26d50dc26?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,NULL,NULL,'null',2,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.907478','2026-10-23 08:02:34.907478'),('pk_30cd2cb1236144ec','frame_shape','Frame Square','frame-square','Frame kotak/persegi memberi kesan tegas & profesional.','<p>Frame kotak/persegi memberi kesan tegas & profesional.</p>','https://images.unsplash.com/photo-1508296695146-257a814070b4?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,'Wajah Bulat, Oval','Formal, Bisnis','{\"badge\": null}',1,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.467211','2026-10-23 08:02:34.467211'),('pk_404d444bcfca48eb','material','TR90','material-tr90','Polimer teknologi tinggi, super lentur.','<p>Polimer teknologi tinggi, super lentur.</p>','https://images.unsplash.com/photo-1574258495973-f010dfbb5371?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,NULL,NULL,'null',3,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.777590','2026-10-23 08:02:34.777590'),('pk_520a512d2d97446e','lens_index','Index 1.74','index-1-74','Paling tipis untuk minus tinggi','<p>Paling tipis untuk minus tinggi</p>','https://images.unsplash.com/photo-1581290447921-b54aaca33ac2?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,NULL,NULL,'null',4,'published',NULL,NULL,NULL,'2026-10-23 08:02:35.069724','2026-10-23 08:02:35.069724'),('pk_65c16b9faf834556','frame_shape','Frame Aviator','frame-aviator','Frame tetesan air klasik dari era 1930-an.','<p>Frame tetesan air klasik dari era 1930-an.</p>','https://images.unsplash.com/photo-1508296695146-257a814070b4?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,'Wajah Oval, Persegi','Vintage, Casual','{\"badge\": null}',3,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.543640','2026-10-23 08:02:34.543640'),('pk_6f3104e2d8424751','material','Titanium','material-titanium','Ringan seperti kertas, kuat seperti baja.','<p>Ringan seperti kertas, kuat seperti baja.</p>','https://images.unsplash.com/photo-1574258495973-f010dfbb5371?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,NULL,NULL,'null',2,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.736055','2026-10-23 08:02:34.736055'),('pk_75000d7042714b61','material','Stainless Steel','material-stainless-steel','Kokoh, awet, harga terjangkau.','<p>Kokoh, awet, harga terjangkau.</p>','https://images.unsplash.com/photo-1574258495973-f010dfbb5371?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,NULL,NULL,'null',4,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.812675','2026-10-23 08:02:34.812675'),('pk_80532004402849fe','frame_shape','Frame Round','frame-round','Frame bulat cocok untuk wajah kotak. Menambah kesan lembut & vintage.','<p>Frame bulat cocok untuk wajah kotak. Menambah kesan lembut & vintage.</p>','https://images.unsplash.com/photo-1591076482161-42ce6da69f67?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,'Wajah Kotak, Persegi','Vintage, Playful','{\"badge\": null}',0,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.424689','2026-10-23 08:02:34.424689'),('pk_9a8e2684030547c1','lens_type','Lensa Single Vision','lensa-vision','Untuk minus, plus, atau silinder tunggal.','<p>Untuk minus, plus, atau silinder tunggal.</p>','https://images.unsplash.com/photo-1601924994987-69e26d50dc26?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,NULL,NULL,'null',0,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.843178','2026-10-23 08:02:34.843178'),('pk_9b8c345b53e648a3','lens_index','Index 1.56','index-1-56','Slightly tipis, populer','<p>Slightly tipis, populer</p>','https://images.unsplash.com/photo-1581290447921-b54aaca33ac2?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,NULL,NULL,'null',1,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.977714','2026-10-23 08:02:34.977714'),('pk_b10021bb3bcc49f1','lens_index','Index 1.50','index-1-50','Standar, cocok minus ringan','<p>Standar, cocok minus ringan</p>','https://images.unsplash.com/photo-1581290447921-b54aaca33ac2?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,NULL,NULL,'null',0,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.956521','2026-10-23 08:02:34.956521'),('pk_c88ef6931b2943f5','frame_shape','Frame Rectangle','frame-rectangle','Frame kotak memanjang, minimalis modern.','<p>Frame kotak memanjang, minimalis modern.</p>','https://images.unsplash.com/photo-1508296695146-257a814070b4?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,'Wajah Bulat, Hati','Minimalis, Profesional','{\"badge\": null}',5,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.591812','2026-10-23 08:02:34.591812'),('pk_e5fa757252be4594','frame_shape','Frame Cat Eye','frame-cat-eye','Frame runcing di ujung, playful dan feminim.','<p>Frame runcing di ujung, playful dan feminim.</p>','https://images.unsplash.com/photo-1591076482161-42ce6da69f67?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,'Wajah Bulat, Hati','Playful, Fashion','{\"badge\": null}',2,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.518010','2026-10-23 08:02:34.518010'),('pk_e85a7626363549ec','lens_index','Index 1.60','index-1-60','Tipis untuk minus 4-5','<p>Tipis untuk minus 4-5</p>','https://images.unsplash.com/photo-1581290447921-b54aaca33ac2?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,NULL,NULL,'null',2,'published',NULL,NULL,NULL,'2026-10-23 08:02:35.000670','2026-10-23 08:02:35.000670'),('pk_ecae6a569bd84944','lens_type','Lensa Blue Cut','lensa-cut','Anti radiasi cahaya biru layar.','<p>Anti radiasi cahaya biru layar.</p>','https://images.unsplash.com/photo-1601924994987-69e26d50dc26?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,NULL,NULL,'null',1,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.877637','2026-10-23 08:02:34.877637'),('pk_f1e4dd9e53b541fa','lens_type','Lensa Progresif','lensa-progresif','Multi jarak — jauh, sedang, dekat.','<p>Multi jarak — jauh, sedang, dekat.</p>','https://images.unsplash.com/photo-1601924994987-69e26d50dc26?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,NULL,NULL,'null',3,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.928423','2026-10-23 08:02:34.928423'),('pk_fa4a13b51ee54cd1','lens_index','Index 1.67','index-1-67','Super tipis untuk minus 6+','<p>Super tipis untuk minus 6+</p>','https://images.unsplash.com/photo-1581290447921-b54aaca33ac2?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,NULL,NULL,'null',3,'published',NULL,NULL,NULL,'2026-10-23 08:02:35.028506','2026-10-23 08:02:35.028506'),('pk_fb7955a67278482c','frame_shape','Frame Round Oval','frame-round-oval','Perpaduan bulat & oval, semi-vintage.','<p>Perpaduan bulat & oval, semi-vintage.</p>','https://images.unsplash.com/photo-1591076482161-42ce6da69f67?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,'Hampir semua wajah','Retro, Cute','{\"badge\": null}',4,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.568003','2026-10-23 08:02:34.568003'),('pk_fd6c135365384fca','material','Acetate','material-acetate','Plastik premium fleksibel, warna kaya, ringan.','<p>Plastik premium fleksibel, warna kaya, ringan.</p>','https://images.unsplash.com/photo-1574258495973-f010dfbb5371?crop=entropy&cs=srgb&fm=jpg&w=800',NULL,NULL,NULL,'null',0,'published',NULL,NULL,NULL,'2026-10-23 08:02:34.669774','2026-10-23 08:02:34.669774');
/*!40000 ALTER TABLE `product_knowledges` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_product_knowledges_mysql57_guard` BEFORE INSERT ON `product_knowledges`
FOR EACH ROW
BEGIN
  IF (NEW.`status` IN ('draft','published','unpublished','archived')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_knowledges_status failed';
  END IF;
  IF (NEW.`knowledge_type` IN ('frame_shape','material','lens_type','lens_index','buying_guide')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_knowledges_type failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_product_knowledges_mysql57_guard` BEFORE UPDATE ON `product_knowledges`
FOR EACH ROW
BEGIN
  IF (NEW.`status` IN ('draft','published','unpublished','archived')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_knowledges_status failed';
  END IF;
  IF (NEW.`knowledge_type` IN ('frame_shape','material','lens_type','lens_index','buying_guide')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_knowledges_type failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `product_review_images`
--

DROP TABLE IF EXISTS `product_review_images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `product_review_images` (
  `review_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `sort_order` int(11) NOT NULL,
  `image_url` text COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`review_id`,`sort_order`),
  CONSTRAINT `fk_product_review_images_review_id_product_reviews_id` FOREIGN KEY (`review_id`) REFERENCES `product_reviews` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_review_images`
--

LOCK TABLES `product_review_images` WRITE;
/*!40000 ALTER TABLE `product_review_images` DISABLE KEYS */;
/*!40000 ALTER TABLE `product_review_images` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_reviews`
--

DROP TABLE IF EXISTS `product_reviews`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `product_reviews` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `order_item_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `order_component_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `verified_purchase` tinyint(1) NOT NULL DEFAULT '0',
  `user_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rating` smallint(6) NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `body` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending',
  `admin_reply` text COLLATE utf8mb4_unicode_ci,
  `moderated_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `moderated_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_product_reviews_order_id_product_id_user_id` (`order_id`,`product_id`,`user_id`),
  KEY `fk_product_reviews_moderated_by_users_user_id` (`moderated_by`),
  KEY `fk_product_reviews_order_component_id_order_id_00f2a90bf233` (`order_component_id`,`order_id`,`product_id`),
  KEY `fk_product_reviews_order_id_user_id_orders_id__9f09bd04e015` (`order_id`,`user_id`),
  KEY `fk_product_reviews_order_item_id_order_id_prod_375484e0a914` (`order_item_id`,`order_id`,`product_id`),
  KEY `fk_product_reviews_user_id_users_user_id` (`user_id`),
  KEY `ix_product_reviews_public` (`product_id`,`status`,`created_at`,`id`),
  CONSTRAINT `fk_product_reviews_moderated_by_users_user_id` FOREIGN KEY (`moderated_by`) REFERENCES `users` (`user_id`),
  CONSTRAINT `fk_product_reviews_order_component_id_order_id_00f2a90bf233` FOREIGN KEY (`order_component_id`, `order_id`, `product_id`) REFERENCES `order_item_components` (`id`, `order_id`, `product_id`),
  CONSTRAINT `fk_product_reviews_order_id_user_id_orders_id__9f09bd04e015` FOREIGN KEY (`order_id`, `user_id`) REFERENCES `orders` (`id`, `user_id`),
  CONSTRAINT `fk_product_reviews_order_item_id_order_id_prod_375484e0a914` FOREIGN KEY (`order_item_id`, `order_id`, `product_id`) REFERENCES `order_items` (`id`, `order_id`, `product_id`),
  CONSTRAINT `fk_product_reviews_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `fk_product_reviews_user_id_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_reviews`
--

LOCK TABLES `product_reviews` WRITE;
/*!40000 ALTER TABLE `product_reviews` DISABLE KEYS */;
/*!40000 ALTER TABLE `product_reviews` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_product_reviews_mysql57_guard` BEFORE INSERT ON `product_reviews`
FOR EACH ROW
BEGIN
  IF ((NEW.`order_item_id` IS NULL AND NEW.`order_component_id` IS NULL) OR NEW.`order_id` IS NOT NULL) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_line_requires_order failed';
  END IF;
  IF (NEW.`order_item_id` IS NULL OR NEW.`order_component_id` IS NULL) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_one_purchase_line failed';
  END IF;
  IF (NEW.`rating` BETWEEN 1 AND 5) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_rating failed';
  END IF;
  IF (NEW.`status` IN ('pending','approved','rejected','hidden')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_status failed';
  END IF;
  IF (NEW.`verified_purchase` = 0 OR (NEW.`order_id` IS NOT NULL AND (NEW.`order_item_id` IS NOT NULL OR NEW.`order_component_id` IS NOT NULL))) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_verified_purchase failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_product_reviews_mysql57_guard` BEFORE UPDATE ON `product_reviews`
FOR EACH ROW
BEGIN
  IF ((NEW.`order_item_id` IS NULL AND NEW.`order_component_id` IS NULL) OR NEW.`order_id` IS NOT NULL) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_line_requires_order failed';
  END IF;
  IF (NEW.`order_item_id` IS NULL OR NEW.`order_component_id` IS NULL) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_one_purchase_line failed';
  END IF;
  IF (NEW.`rating` BETWEEN 1 AND 5) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_rating failed';
  END IF;
  IF (NEW.`status` IN ('pending','approved','rejected','hidden')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_status failed';
  END IF;
  IF (NEW.`verified_purchase` = 0 OR (NEW.`order_id` IS NOT NULL AND (NEW.`order_item_id` IS NOT NULL OR NEW.`order_component_id` IS NOT NULL))) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_reviews_verified_purchase failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `product_segments`
--

DROP TABLE IF EXISTS `product_segments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `product_segments` (
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `segment` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`product_id`,`segment`),
  KEY `ix_product_segments_segment` (`segment`,`product_id`),
  CONSTRAINT `fk_product_segments_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_segments`
--

LOCK TABLES `product_segments` WRITE;
/*!40000 ALTER TABLE `product_segments` DISABLE KEYS */;
INSERT INTO `product_segments` VALUES ('prd_0b61644f093f4610','Pria'),('prd_0f674d6c51e34ae1','Unisex'),('prd_1b6d039b016b4131','Pria'),('prd_26aa3608a7084627','Unisex'),('prd_3e8ddf16743d4901','Wanita'),('prd_401170d2b1564810','Wanita'),('prd_52253b4c63584c54','Unisex'),('prd_75466e5b7e5c4775','Wanita'),('prd_7ba6732284b649c8','Wanita'),('prd_898f994b888240ab','Anak-anak'),('prd_98175a8e8a554c55','Anak-anak'),('prd_a1911ea875294d3a','Unisex'),('prd_bce0660e41e84eaa','Unisex'),('prd_cb46f21f4ef446f3','Pria'),('prd_d7b3f4cfe9574460','Wanita'),('prd_df7a0e382fa14177','Anak-anak'),('prd_f1a4277d4ba84cd1','Wanita'),('prd_f27e5e8e2c274d16','Pria'),('prd_f2d20822dbce4da6','Pria'),('prd_fbef635ed7514c8f','Wanita');
/*!40000 ALTER TABLE `product_segments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_subscriptions`
--

DROP TABLE IF EXISTS `product_subscriptions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `product_subscriptions` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `notify_stock` tinyint(1) NOT NULL DEFAULT '1',
  `notify_price_drop` tinyint(1) NOT NULL DEFAULT '1',
  `notify_flash_sale` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_product_subscriptions_user_id_product_id` (`user_id`,`product_id`),
  KEY `fk_product_subscriptions_product_id_products_id` (`product_id`),
  CONSTRAINT `fk_product_subscriptions_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_product_subscriptions_user_id_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_subscriptions`
--

LOCK TABLES `product_subscriptions` WRITE;
/*!40000 ALTER TABLE `product_subscriptions` DISABLE KEYS */;
/*!40000 ALTER TABLE `product_subscriptions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_variant_frame_specifications`
--

DROP TABLE IF EXISTS `product_variant_frame_specifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `product_variant_frame_specifications` (
  `variant_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `a` decimal(7,2) DEFAULT NULL,
  `b` decimal(7,2) DEFAULT NULL,
  `dbl` decimal(7,2) DEFAULT NULL,
  `ed` decimal(7,2) DEFAULT NULL,
  `temple_length` decimal(7,2) DEFAULT NULL,
  `symmetric` tinyint(1) NOT NULL DEFAULT '0',
  `enabled` tinyint(1) NOT NULL DEFAULT '0',
  `source_note` text COLLATE utf8mb4_unicode_ci,
  `version` int(11) NOT NULL DEFAULT '1',
  `updated_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`variant_id`),
  KEY `fk_product_variant_frame_specifications_produc_c29aa19f0cb2` (`product_id`,`variant_id`),
  KEY `fk_product_variant_frame_specifications_update_133a0245692d` (`updated_by`),
  KEY `ix_variant_frame_specs_product` (`product_id`),
  CONSTRAINT `fk_product_variant_frame_specifications_produc_c29aa19f0cb2` FOREIGN KEY (`product_id`, `variant_id`) REFERENCES `product_variants` (`product_id`, `id`) ON DELETE CASCADE,
  CONSTRAINT `fk_product_variant_frame_specifications_update_133a0245692d` FOREIGN KEY (`updated_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_variant_frame_specifications`
--

LOCK TABLES `product_variant_frame_specifications` WRITE;
/*!40000 ALTER TABLE `product_variant_frame_specifications` DISABLE KEYS */;
/*!40000 ALTER TABLE `product_variant_frame_specifications` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_product_variant_frame_specifications_bi` BEFORE INSERT ON `product_variant_frame_specifications`
FOR EACH ROW
BEGIN
  IF ((NEW.`a` IS NULL OR NEW.`a` > 0) AND (NEW.`b` IS NULL OR NEW.`b` > 0) AND (NEW.`dbl` IS NULL OR NEW.`dbl` > 0) AND (NEW.`ed` IS NULL OR NEW.`ed` > 0) AND (NEW.`temple_length` IS NULL OR NEW.`temple_length` > 0)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_variant_frame_specifications_dimensions failed'; END IF;
  IF (NEW.`symmetric` IN (0,1) AND NEW.`enabled` IN (0,1)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_variant_frame_specifications_flags failed'; END IF;
  IF (NEW.`version` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_variant_frame_specifications_version failed'; END IF;
  IF NOT EXISTS (SELECT 1 FROM products WHERE id = NEW.product_id AND product_type = 'frame') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Frame specification requires a frame product'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `trg_meow3_product_variant_frame_specifications_bu` BEFORE UPDATE ON `product_variant_frame_specifications`
FOR EACH ROW
BEGIN
  IF ((NEW.`a` IS NULL OR NEW.`a` > 0) AND (NEW.`b` IS NULL OR NEW.`b` > 0) AND (NEW.`dbl` IS NULL OR NEW.`dbl` > 0) AND (NEW.`ed` IS NULL OR NEW.`ed` > 0) AND (NEW.`temple_length` IS NULL OR NEW.`temple_length` > 0)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_variant_frame_specifications_dimensions failed'; END IF;
  IF (NEW.`symmetric` IN (0,1) AND NEW.`enabled` IN (0,1)) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_variant_frame_specifications_flags failed'; END IF;
  IF (NEW.`version` > 0) IS FALSE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Rule ck_product_variant_frame_specifications_version failed'; END IF;
  IF NOT EXISTS (SELECT 1 FROM products WHERE id = NEW.product_id AND product_type = 'frame') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Frame specification requires a frame product'; END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `product_variants`
--

DROP TABLE IF EXISTS `product_variants`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `product_variants` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `color` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `color_hex` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `size` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `lens_type` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sku` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `stock` int(11) NOT NULL DEFAULT '0',
  `reserved` int(11) NOT NULL DEFAULT '0',
  `price_override` decimal(18,2) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `sort_order` int(11) NOT NULL DEFAULT '0',
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_product_variants_product_id_id` (`product_id`,`id`),
  UNIQUE KEY `uq_product_variants_sku` (`sku`),
  CONSTRAINT `fk_product_variants_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_variants`
--

LOCK TABLES `product_variants` WRITE;
/*!40000 ALTER TABLE `product_variants` DISABLE KEYS */;
INSERT INTO `product_variants` VALUES ('var_161a6e6f4ae4495a','prd_3e8ddf16743d4901','Putih Mutiara','#F5F5DC','S',NULL,'MO-SWT-WN-WHT',25,0,NULL,1,0,'2026-10-23 07:58:19.241183','2026-10-23 07:58:19.241183'),('var_17821973adfb4662','prd_0f674d6c51e34ae1',NULL,NULL,NULL,'Blue Cut Standard','LNS-BLC-STD',25,0,NULL,1,0,'2026-10-23 07:58:19.880925','2026-10-23 07:58:19.880925'),('var_2b6cec11c2b84fc7','prd_bce0660e41e84eaa',NULL,NULL,NULL,'Photochromic Grey','LNS-PCM-GRY',25,0,NULL,1,0,'2026-10-23 07:58:19.953819','2026-10-23 07:58:19.953819'),('var_36ccf63e6e9d4f85','prd_1b6d039b016b4131','Hitam Sport','#000000','L',NULL,'PL-TRL-PR-BLK',25,0,NULL,1,0,'2026-10-23 07:58:19.710986','2026-10-23 07:58:19.710986'),('var_4cba838eca4f4c77','prd_cb46f21f4ef446f3','Silver','#A0A0A0','M',NULL,'ES-AIR-PR-SLV',25,0,NULL,1,0,'2026-10-23 07:58:19.636667','2026-10-23 07:58:19.636667'),('var_6148b0dc13f74e21','prd_df7a0e382fa14177','Merah','#EF4444','XS',NULL,'LE-MIN-AN-RED',25,0,NULL,1,1,'2026-10-23 07:58:19.108234','2026-10-23 07:58:19.108234'),('var_63049956c6d6400e','prd_df7a0e382fa14177','Biru','#3B82F6','XS',NULL,'LE-MIN-AN-BLU',25,0,NULL,1,0,'2026-10-23 07:58:19.108234','2026-10-23 07:58:19.108234'),('var_66c61297dc0e494b','prd_75466e5b7e5c4775','Pink Soft','#FFB5C5','S',NULL,'LE-PET-WN-PNK',25,0,NULL,1,0,'2026-10-23 07:58:19.000607','2026-10-23 07:58:19.000607'),('var_69aaaae26f094f85','prd_401170d2b1564810','Coral','#FF6B6B','M',NULL,'CT-DIV-WN-COR',25,0,NULL,1,0,'2026-10-23 07:58:19.161433','2026-10-23 07:58:19.161433'),('var_6f0bfb1702ba4164','prd_26aa3608a7084627','Black','#0B192C','M',NULL,'ES-QUD-UN-BLK',25,0,NULL,1,0,'2026-10-23 07:58:19.463599','2026-10-23 07:58:19.463599'),('var_70a6856c0eed4bac','prd_75466e5b7e5c4775','Bening','#F0F0F0','S',NULL,'LE-PET-WN-CLR',25,0,NULL,1,1,'2026-10-23 07:58:19.000607','2026-10-23 07:58:19.000607'),('var_71ec04bcd9b44d10','prd_0b61644f093f4610','Silver','#9CA3AF','L',NULL,'LE-URB-PR-SLV',25,0,NULL,1,0,'2026-10-23 07:58:18.955024','2026-10-23 07:58:18.955024'),('var_78b9cf45d29f47c1','prd_0f674d6c51e34ae1',NULL,NULL,NULL,'Blue Cut Premium','LNS-BLC-PRM',25,0,450000.00,1,1,'2026-10-23 07:58:19.880925','2026-10-23 07:58:19.880925'),('var_7b2d2b3cee7d410f','prd_52253b4c63584c54',NULL,NULL,NULL,'Progresif Hi-Index','LNS-PRG-HI',25,0,NULL,1,0,'2026-10-23 07:58:20.056532','2026-10-23 07:58:20.056532'),('var_7f9dbd1522c54b35','prd_401170d2b1564810','Hitam Glam','#0B192C','M',NULL,'CT-DIV-WN-BLK',25,0,NULL,1,1,'2026-10-23 07:58:19.161433','2026-10-23 07:58:19.161433'),('var_88681df03c214cff','prd_f27e5e8e2c274d16','Gold','#FCA311','M',NULL,'MO-VTG-PR-GLD',25,0,NULL,1,0,'2026-10-23 07:58:19.345939','2026-10-23 07:58:19.345939'),('var_8c894021e8fc46c8','prd_d7b3f4cfe9574460',NULL,NULL,NULL,NULL,'PKG-CT-PCM-001',15,0,NULL,1,0,'2026-10-23 07:58:20.405734','2026-10-23 07:58:20.405734'),('var_8d5417e08d9e44b3','prd_f2d20822dbce4da6','Hitam','#0B192C','M',NULL,'LE-AER-PR-BLK',25,0,NULL,1,0,'2026-10-23 07:58:18.899800','2026-10-23 07:58:18.899800'),('var_8d9fe36260964fff','prd_7ba6732284b649c8','Beige','#D6BFA0','S',NULL,'KC-LOL-WN-BEG',25,0,NULL,1,0,'2026-10-23 07:58:19.410739','2026-10-23 07:58:19.410739'),('var_8fc85f29df264c82','prd_f27e5e8e2c274d16','Black Matte','#1F2937','M',NULL,'MO-VTG-PR-BMT',25,0,NULL,1,1,'2026-10-23 07:58:19.345939','2026-10-23 07:58:19.345939'),('var_9c42dd0a57044732','prd_26aa3608a7084627','Blue Crystal','#1E3A8A','M',NULL,'ES-QUD-UN-BLC',25,0,NULL,1,1,'2026-10-23 07:58:19.463599','2026-10-23 07:58:19.463599'),('var_9c6775d5e68247fa','prd_98175a8e8a554c55',NULL,NULL,NULL,NULL,'PKG-KC-BLC-001',20,0,NULL,1,0,'2026-10-23 07:58:20.483007','2026-10-23 07:58:20.483007'),('var_a344ccbec1864693','prd_1b6d039b016b4131','Hijau Neon','#22C55E','L',NULL,'PL-TRL-PR-GRN',25,0,NULL,1,1,'2026-10-23 07:58:19.710986','2026-10-23 07:58:19.710986'),('var_b4586763d3f0419c','prd_bce0660e41e84eaa',NULL,NULL,NULL,'Photochromic Brown','LNS-PCM-BRN',25,0,NULL,1,1,'2026-10-23 07:58:19.953819','2026-10-23 07:58:19.953819'),('var_bf5731b0ea724b44','prd_f2d20822dbce4da6','Cokelat','#7B4F2D','M',NULL,'LE-AER-PR-BRN',25,0,NULL,1,1,'2026-10-23 07:58:18.899800','2026-10-23 07:58:18.899800'),('var_c7679424d9aa4337','prd_f1a4277d4ba84cd1','Tortoise','#8B5A2B','M',NULL,'LE-BLM-WN-TRT',25,0,NULL,1,0,'2026-10-23 07:58:19.061461','2026-10-23 07:58:19.061461'),('var_d590dd75a59c4fd8','prd_a1911ea875294d3a',NULL,NULL,NULL,NULL,'PKG-LE-BLC-001',30,0,NULL,1,0,'2026-10-23 07:58:20.232579','2026-10-23 07:58:20.232579'),('var_efda2ee981f14664','prd_898f994b888240ab','Kuning','#FCA311','XS',NULL,'KC-CBY-AN-YLW',25,0,NULL,1,0,'2026-11-09 09:00:45.313687','2026-10-23 07:58:19.761519'),('var_f62fe3ab39b84901','prd_fbef635ed7514c8f','Honey','#E0A85A','L',NULL,'CT-AUR-WN-HNY',25,0,NULL,1,0,'2026-10-23 07:58:19.537846','2026-10-23 07:58:19.537846');
/*!40000 ALTER TABLE `product_variants` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_product_variants_mysql57_guard` BEFORE INSERT ON `product_variants`
FOR EACH ROW
BEGIN
  IF (NEW.`stock` >= 0 AND NEW.`reserved` >= 0 AND NEW.`reserved` <= NEW.`stock`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_variants_inventory failed';
  END IF;
  IF (NEW.`price_override` IS NULL OR NEW.`price_override` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_variants_price failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_product_variants_mysql57_guard` BEFORE UPDATE ON `product_variants`
FOR EACH ROW
BEGIN
  IF (NEW.`stock` >= 0 AND NEW.`reserved` >= 0 AND NEW.`reserved` <= NEW.`stock`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_variants_inventory failed';
  END IF;
  IF (NEW.`price_override` IS NULL OR NEW.`price_override` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_product_variants_price failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `products` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `slug` varchar(191) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sku` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `spec` json DEFAULT NULL,
  `product_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'frame',
  `primary_category_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `brand_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `price` decimal(18,2) NOT NULL,
  `discount_price` decimal(18,2) DEFAULT NULL,
  `flash_sale_price` decimal(18,2) DEFAULT NULL,
  `weight_gram` int(11) NOT NULL DEFAULT '100',
  `dimension` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `main_image` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `min_stock_alert` int(11) NOT NULL DEFAULT '5',
  `rating_avg` decimal(3,2) NOT NULL DEFAULT '0.00',
  `rating_count` int(11) NOT NULL DEFAULT '0',
  `sold_count` bigint(20) NOT NULL DEFAULT '0',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `is_new_arrival` tinyint(1) NOT NULL DEFAULT '0',
  `new_arrival_until` datetime(6) DEFAULT NULL,
  `seo_title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `seo_description` text COLLATE utf8mb4_unicode_ci,
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_products_sku` (`sku`),
  UNIQUE KEY `uq_products_slug` (`slug`),
  KEY `ix_products_arrivals` (`is_active`,`product_type`,`is_new_arrival`,`created_at`,`id`),
  KEY `ix_products_brand_id` (`brand_id`),
  KEY `ix_products_price` (`is_active`,`price`,`id`),
  KEY `ix_products_primary_category_id` (`primary_category_id`),
  KEY `ix_products_shop` (`is_active`,`product_type`,`created_at`,`id`),
  FULLTEXT KEY `ft_products_name_description` (`name`,`description`),
  CONSTRAINT `fk_products_brand_id_brands_id` FOREIGN KEY (`brand_id`) REFERENCES `brands` (`id`),
  CONSTRAINT `fk_products_primary_category_id_categories_id` FOREIGN KEY (`primary_category_id`) REFERENCES `categories` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
INSERT INTO `products` VALUES ('prd_0b61644f093f4610','Leinz Urban Pria','leinz-urban-pria','ME-LEINZ-URBA','Leinz Urban Pria — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Italy\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','frame','cat_4bb0610322c04fae','brd_b1845bf573734de8',950000.00,NULL,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1618677366787-9727aacca7ea?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.60,12,17,1,0,NULL,NULL,NULL,'2026-10-23 07:58:18.955062','2026-10-23 07:58:18.955024'),('prd_0f674d6c51e34ae1','Lensa Anti Radiasi Blue Cut','lensa-anti-radiasi-blue-cut','ME-LENSA-ANTI','Lensa Anti Radiasi Blue Cut — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Japan\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','lens','cat_86849a3a92084a57','brd_a1a43360a32847d6',350000.00,280000.00,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1574258495973-f010dfbb5371?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.90,103,38,1,0,NULL,NULL,NULL,'2026-10-23 07:58:19.880974','2026-10-23 07:58:19.880925'),('prd_1b6d039b016b4131','PurrLens Trail Sport','purrlens-trail-sport','ME-PURRLENS-T','PurrLens Trail Sport — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Italy\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','frame','cat_263c673054d14d28','brd_a1a43360a32847d6',950000.00,850000.00,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1772009288423-96090d2998c7?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.70,89,4,1,0,NULL,NULL,NULL,'2026-10-23 07:58:19.711021','2026-10-23 07:58:19.710986'),('prd_26aa3608a7084627','EssenseEye Quad Unisex','essenseeye-quad-unisex','ME-ESSENSEEYE','EssenseEye Quad Unisex — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Italy\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','frame','cat_90943cf30dee4098','brd_8d5d28e0ab264d8e',880000.00,NULL,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1601924994987-69e26d50dc26?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.90,68,153,1,0,NULL,NULL,NULL,'2026-10-23 07:58:19.463637','2026-10-23 07:58:19.463599'),('prd_3e8ddf16743d4901','MeowOptik Sweetie Cat Eye','meowoptik-sweetie-cat-eye','ME-MEOWOPTIK-','MeowOptik Sweetie Cat Eye — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Italy\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','frame','cat_fc53a5d7fa854ec3','brd_5d2a87b6de0a421d',690000.00,599000.00,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.60,47,102,1,0,NULL,NULL,NULL,'2026-10-23 07:58:19.241213','2026-10-23 07:58:19.241183'),('prd_401170d2b1564810','Catlux Diva Cat Eye','catlux-diva-cat-eye','ME-CATLUX-DIV','Catlux Diva Cat Eye — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Italy\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','frame','cat_fc53a5d7fa854ec3','brd_e78d6cf8db334a0b',1200000.00,999000.00,780000.00,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1511499767150-a48a237f0083?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.50,40,85,1,0,NULL,NULL,NULL,'2026-10-23 07:58:19.161472','2026-10-23 07:58:19.161433'),('prd_52253b4c63584c54','Lensa Progresif Premium','lensa-progresif-premium','ME-LENSA-PROG','Lensa Progresif Premium — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Japan\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','lens','cat_0882be6403ac4ec8','brd_a1a43360a32847d6',1500000.00,1300000.00,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1556306535-0f09a537f0a3?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.60,117,72,1,0,NULL,NULL,NULL,'2026-10-23 07:58:20.056567','2026-10-23 07:58:20.056532'),('prd_75466e5b7e5c4775','Leinz Petite Cat Eye','leinz-petite-cat-eye','ME-LEINZ-PETI','Leinz Petite Cat Eye — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Italy\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','frame','cat_c8db483f74e047f0','brd_b1845bf573734de8',880000.00,790000.00,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1574258495973-f010dfbb5371?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.70,19,34,1,0,NULL,NULL,NULL,'2026-10-23 07:58:19.000643','2026-10-23 07:58:19.000607'),('prd_7ba6732284b649c8','Kittycraft Lola Round','kittycraft-lola-round','ME-KITTYCRAFT','Kittycraft Lola Round — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Italy\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','frame','cat_ee34eb85616b40e4','brd_9054aabe325441da',650000.00,550000.00,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1633621641966-23836fcafd7b?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.80,61,136,1,0,NULL,NULL,NULL,'2026-10-23 07:58:19.410781','2026-10-23 07:58:19.410739'),('prd_898f994b888240ab','Kittycraft Cubby Anak','kittycraft-cubby-anak','ME-KITTYCRAFT-CUBBY','Kittycraft Cubby Anak — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Italy\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','frame','cat_021c207590d34a14','brd_9054aabe325441da',420000.00,350000.00,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1618677366787-9727aacca7ea?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.80,96,21,1,1,'2026-11-10 01:00:00.000000',NULL,NULL,'2026-11-09 09:00:45.256528','2026-10-23 07:58:19.761519'),('prd_98175a8e8a554c55','Paket Anak Kittycraft + Blue Cut','paket-anak-kittycraft-blue-cut','ME-PAKET-ANAK','Paket Anak Kittycraft + Blue Cut — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Japan\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','package','cat_3502c02ad4ac4d8d','brd_9054aabe325441da',700000.00,600000.00,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1508296695146-257a814070b4?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.90,138,123,1,0,NULL,NULL,NULL,'2026-10-23 07:58:20.483033','2026-10-23 07:58:20.483007'),('prd_a1911ea875294d3a','Paket Hemat Leinz + Blue Cut','paket-hemat-leinz-blue-cut','ME-PAKET-HEMA','Paket Hemat Leinz + Blue Cut — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Japan\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','package','cat_71b46a9ac639436a','brd_b1845bf573734de8',1100000.00,950000.00,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1511499767150-a48a237f0083?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.70,124,89,1,0,NULL,NULL,NULL,'2026-10-23 07:58:20.232615','2026-10-23 07:58:20.232579'),('prd_bce0660e41e84eaa','Lensa Photochromic','lensa-photochromic','ME-LENSA-PHOT','Lensa Photochromic — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Japan\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','lens','cat_a57421c7ee3b4826','brd_a1a43360a32847d6',550000.00,NULL,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1577803645773-f96470509666?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.50,110,55,1,0,NULL,NULL,NULL,'2026-10-23 07:58:19.953855','2026-10-23 07:58:19.953819'),('prd_cb46f21f4ef446f3','EssenseEye Air Rimless','essenseeye-air-rimless','ME-ESSENSEEYE-AIR','EssenseEye Air Rimless — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Italy\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','frame','cat_c67d33f78ebb4d52','brd_8d5d28e0ab264d8e',1450000.00,NULL,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1581290447921-b54aaca33ac2?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.60,82,187,1,0,NULL,NULL,NULL,'2026-10-23 07:58:19.636703','2026-10-23 07:58:19.636667'),('prd_d7b3f4cfe9574460','Paket Premium Catlux + Photochromic','paket-premium-catlux-photochromic','ME-PAKET-PREM','Paket Premium Catlux + Photochromic — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Japan\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','package','cat_d1cf64ed5dbe41af','brd_e78d6cf8db334a0b',1800000.00,1599000.00,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.80,131,106,1,0,NULL,NULL,NULL,'2026-10-23 07:58:20.405771','2026-10-23 07:58:20.405734'),('prd_df7a0e382fa14177','Leinz Mini Anak','leinz-mini-anak','ME-LEINZ-MINI','Leinz Mini Anak — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Italy\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','frame','cat_f4e07e43d00145b7','brd_b1845bf573734de8',480000.00,380000.00,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1556306535-0f09a537f0a3?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.90,33,68,1,0,NULL,NULL,NULL,'2026-10-23 07:58:19.108263','2026-10-23 07:58:19.108234'),('prd_f1a4277d4ba84cd1','Leinz Bloom Wanita','leinz-bloom-wanita','ME-LEINZ-BLOO','Leinz Bloom Wanita — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Italy\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','frame','cat_c8db483f74e047f0','brd_b1845bf573734de8',750000.00,NULL,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1577803645773-f96470509666?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.80,26,51,1,0,NULL,NULL,NULL,'2026-10-23 07:58:19.061491','2026-10-23 07:58:19.061461'),('prd_f27e5e8e2c274d16','MeowOptik Vintage Round','meowoptik-vintage-round','ME-MEOWOPTIK-VINTAGE','MeowOptik Vintage Round — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Italy\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','frame','cat_40be3187b63b4230','brd_5d2a87b6de0a421d',720000.00,NULL,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1508296695146-257a814070b4?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.70,54,119,1,0,NULL,NULL,NULL,'2026-10-23 07:58:19.345991','2026-10-23 07:58:19.345939'),('prd_f2d20822dbce4da6','Leinz Aero Pria','leinz-aero-pria','ME-LEINZ-AERO','Leinz Aero Pria — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Italy\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','frame','cat_4bb0610322c04fae','brd_b1845bf573734de8',850000.00,720000.00,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1772009288423-96090d2998c7?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.50,5,0,1,0,NULL,NULL,NULL,'2026-10-23 07:58:18.899827','2026-10-23 07:58:18.899800'),('prd_fbef635ed7514c8f','Catlux Aurora Oversized','catlux-aurora-oversized','ME-CATLUX-AUR','Catlux Aurora Oversized — frame berkualitas premium dari Meow Eyes. Ringan, nyaman, dan stylish untuk dipakai sehari-hari.','{\"Wajah\": \"Oval, Bulat, Persegi\", \"Origin\": \"Italy\", \"Garansi\": \"12 bulan\", \"Material\": \"Acetate\"}','frame','cat_ab44ff7d3aec41d7','brd_e78d6cf8db334a0b',1300000.00,1100000.00,NULL,120,'140 x 50 x 145 mm','https://images.unsplash.com/photo-1591076482161-42ce6da69f67?crop=entropy&cs=srgb&fm=jpg&w=900',5,4.50,75,170,1,0,NULL,NULL,NULL,'2026-10-23 07:58:19.537868','2026-10-23 07:58:19.537846');
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_products_mysql57_guard` BEFORE INSERT ON `products`
FOR EACH ROW
BEGIN
  IF (NEW.`rating_avg` BETWEEN 0 AND 5 AND NEW.`rating_count` >= 0 AND NEW.`sold_count` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_counters failed';
  END IF;
  IF (NEW.`weight_gram` >= 0 AND NEW.`min_stock_alert` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_inventory_values failed';
  END IF;
  IF (NEW.`flash_sale_price` IS NULL OR NEW.`flash_sale_price` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_legacy_flash_nonnegative failed';
  END IF;
  IF (NEW.`price` >= 0 AND (NEW.`discount_price` IS NULL OR NEW.`discount_price` >= 0)) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_prices_nonnegative failed';
  END IF;
  IF (NEW.`product_type` IN ('frame','lens','package')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_type failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_products_mysql57_guard` BEFORE UPDATE ON `products`
FOR EACH ROW
BEGIN
  IF (NEW.`rating_avg` BETWEEN 0 AND 5 AND NEW.`rating_count` >= 0 AND NEW.`sold_count` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_counters failed';
  END IF;
  IF (NEW.`weight_gram` >= 0 AND NEW.`min_stock_alert` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_inventory_values failed';
  END IF;
  IF (NEW.`flash_sale_price` IS NULL OR NEW.`flash_sale_price` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_legacy_flash_nonnegative failed';
  END IF;
  IF (NEW.`price` >= 0 AND (NEW.`discount_price` IS NULL OR NEW.`discount_price` >= 0)) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_prices_nonnegative failed';
  END IF;
  IF (NEW.`product_type` IN ('frame','lens','package')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_products_type failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `roulette_redemptions`
--

DROP TABLE IF EXISTS `roulette_redemptions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `roulette_redemptions` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `spin_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'reserved',
  `discount_amount` decimal(18,2) NOT NULL DEFAULT '0.00',
  `resolved_at` datetime(6) DEFAULT NULL,
  `active_spin_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin GENERATED ALWAYS AS ((case when (`status` in ('reserved','redeemed')) then `spin_id` else NULL end)) STORED,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_roulette_redemptions_order_id` (`order_id`),
  UNIQUE KEY `uq_roulette_redemptions_spin_id_order_id` (`spin_id`,`order_id`),
  UNIQUE KEY `uq_roulette_redemptions_active_spin_id` (`active_spin_id`),
  KEY `fk_roulette_redemptions_order_id_user_id_order_a1ca5f3fa8b0` (`order_id`,`user_id`),
  KEY `fk_roulette_redemptions_spin_id_user_id_roulet_332771d0a44a` (`spin_id`,`user_id`),
  CONSTRAINT `fk_roulette_redemptions_order_id_user_id_order_a1ca5f3fa8b0` FOREIGN KEY (`order_id`, `user_id`) REFERENCES `orders` (`id`, `user_id`),
  CONSTRAINT `fk_roulette_redemptions_spin_id_user_id_roulet_332771d0a44a` FOREIGN KEY (`spin_id`, `user_id`) REFERENCES `roulette_spins` (`id`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roulette_redemptions`
--

LOCK TABLES `roulette_redemptions` WRITE;
/*!40000 ALTER TABLE `roulette_redemptions` DISABLE KEYS */;
/*!40000 ALTER TABLE `roulette_redemptions` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_roulette_redemptions_mysql57_guard` BEFORE INSERT ON `roulette_redemptions`
FOR EACH ROW
BEGIN
  IF (NEW.`discount_amount` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_redemptions_discount failed';
  END IF;
  IF (NEW.`status` IN ('reserved','redeemed','released')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_redemptions_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_roulette_redemptions_mysql57_guard` BEFORE UPDATE ON `roulette_redemptions`
FOR EACH ROW
BEGIN
  IF (NEW.`discount_amount` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_redemptions_discount failed';
  END IF;
  IF (NEW.`status` IN ('reserved','redeemed','released')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_redemptions_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `roulette_rewards`
--

DROP TABLE IF EXISTS `roulette_rewards`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `roulette_rewards` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `label` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` decimal(18,2) NOT NULL DEFAULT '0.00',
  `color` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '#FF6B6B',
  `probability` decimal(18,8) NOT NULL DEFAULT '0.10000000',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roulette_rewards`
--

LOCK TABLES `roulette_rewards` WRITE;
/*!40000 ALTER TABLE `roulette_rewards` DISABLE KEYS */;
INSERT INTO `roulette_rewards` VALUES ('rwd_143704cb36864730','Coba Lagi','nothing',0.00,'#94A3B8',0.10000000,1),('rwd_1baa16f859764bc6','50 Poin','points',50.00,'#FCA311',0.25000000,1),('rwd_2ab2dd591fb7425d','Diskon Rp 100.000','discount',100000.00,'#2A9D8F',0.05000000,1),('rwd_4976e36c072049d3','Gratis Ongkir','free_shipping',0.00,'#06D6A0',0.15000000,1),('rwd_724c88a8a5224216','200 Poin','points',200.00,'#0B192C',0.05000000,1),('rwd_792cc587a2f04196','Diskon Rp 50.000','discount',50000.00,'#FF6B6B',0.10000000,1),('rwd_ce18ba551b1345d4','Diskon Rp 25.000','discount',25000.00,'#FF8FA3',0.15000000,1),('rwd_eb0b0638a4834350','100 Poin','points',100.00,'#FFD166',0.15000000,1);
/*!40000 ALTER TABLE `roulette_rewards` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_roulette_rewards_mysql57_guard` BEFORE INSERT ON `roulette_rewards`
FOR EACH ROW
BEGIN
  IF (NEW.`value` >= 0 AND NEW.`probability` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_rewards_amounts failed';
  END IF;
  IF (NEW.`type` IN ('points','voucher','free_shipping','discount','nothing')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_rewards_type failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_roulette_rewards_mysql57_guard` BEFORE UPDATE ON `roulette_rewards`
FOR EACH ROW
BEGIN
  IF (NEW.`value` >= 0 AND NEW.`probability` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_rewards_amounts failed';
  END IF;
  IF (NEW.`type` IN ('points','voucher','free_shipping','discount','nothing')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_rewards_type failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `roulette_spins`
--

DROP TABLE IF EXISTS `roulette_spins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `roulette_spins` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `reward_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `reward_label` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `reward_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `reward_value` decimal(18,2) NOT NULL,
  `used` tinyint(1) NOT NULL DEFAULT '0',
  `expires_at` datetime(6) NOT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_roulette_spins_id_user_id` (`id`,`user_id`),
  KEY `fk_roulette_spins_reward_id_roulette_rewards_id` (`reward_id`),
  KEY `ix_roulette_spins_eligibility` (`user_id`,`used`,`expires_at`),
  KEY `ix_roulette_spins_user_date` (`user_id`,`created_at`),
  CONSTRAINT `fk_roulette_spins_reward_id_roulette_rewards_id` FOREIGN KEY (`reward_id`) REFERENCES `roulette_rewards` (`id`),
  CONSTRAINT `fk_roulette_spins_user_id_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roulette_spins`
--

LOCK TABLES `roulette_spins` WRITE;
/*!40000 ALTER TABLE `roulette_spins` DISABLE KEYS */;
INSERT INTO `roulette_spins` VALUES ('spn_af9c2bd1bcba40ae','usr_c4b3d45ff0b94ffd','rwd_4976e36c072049d3','Gratis Ongkir','free_shipping',0.00,0,'2026-11-24 01:36:34.119873','2026-11-10 01:36:34.120373'),('spn_e08ed14fc7044fa1','usr_c4b3d45ff0b94ffd','rwd_ce18ba551b1345d4','Diskon Rp 25.000','discount',25000.00,0,'2026-11-24 01:36:08.420915','2026-11-10 01:36:08.422632'),('spn_ef3b8d5a7fe540c9','usr_c4b3d45ff0b94ffd','rwd_2ab2dd591fb7425d','Diskon Rp 100.000','discount',100000.00,0,'2026-11-24 01:36:15.339269','2026-11-10 01:36:15.339624');
/*!40000 ALTER TABLE `roulette_spins` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_roulette_spins_mysql57_guard` BEFORE INSERT ON `roulette_spins`
FOR EACH ROW
BEGIN
  IF (NEW.`reward_value` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_spins_value failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_roulette_spins_mysql57_guard` BEFORE UPDATE ON `roulette_spins`
FOR EACH ROW
BEGIN
  IF (NEW.`reward_value` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_roulette_spins_value failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `settings`
--

DROP TABLE IF EXISTS `settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `settings` (
  `key` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` json NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `is_public` tinyint(1) NOT NULL DEFAULT '0',
  `updated_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`key`),
  KEY `fk_settings_updated_by_users_user_id` (`updated_by`),
  CONSTRAINT `fk_settings_updated_by_users_user_id` FOREIGN KEY (`updated_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `settings`
--

LOCK TABLES `settings` WRITE;
/*!40000 ALTER TABLE `settings` DISABLE KEYS */;
/*!40000 ALTER TABLE `settings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shipment_logs`
--

DROP TABLE IF EXISTS `shipment_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shipment_logs` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `shipment_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `provider` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `action` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `payload` json DEFAULT NULL,
  `response` json DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `fk_shipment_logs_shipment_id_order_id_shipment_d1998a94a236` (`shipment_id`,`order_id`),
  KEY `ix_shipment_logs_order_date` (`order_id`,`created_at`,`id`),
  CONSTRAINT `fk_shipment_logs_order_id_orders_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`),
  CONSTRAINT `fk_shipment_logs_shipment_id_order_id_shipment_d1998a94a236` FOREIGN KEY (`shipment_id`, `order_id`) REFERENCES `shipments` (`id`, `order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shipment_logs`
--

LOCK TABLES `shipment_logs` WRITE;
/*!40000 ALTER TABLE `shipment_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `shipment_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shipments`
--

DROP TABLE IF EXISTS `shipments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shipments` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `provider` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'everpro',
  `request_id` varchar(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `external_id` varchar(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `courier_code` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `service_code` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tracking_number` varchar(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `label_url` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending',
  `carrier_status` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cost` decimal(18,2) NOT NULL,
  `currency` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'IDR',
  `last_checked_at` datetime(6) DEFAULT NULL,
  `shipped_at` datetime(6) DEFAULT NULL,
  `delivered_at` datetime(6) DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_shipments_id_order_id` (`id`,`order_id`),
  UNIQUE KEY `uq_shipments_provider_request_id` (`provider`,`request_id`),
  UNIQUE KEY `uq_shipments_provider_external_id` (`provider`,`external_id`),
  KEY `ix_shipments_order` (`order_id`,`created_at`),
  KEY `ix_shipments_poll` (`status`,`last_checked_at`),
  KEY `ix_shipments_tracking` (`provider`,`tracking_number`),
  CONSTRAINT `fk_shipments_order_id_orders_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shipments`
--

LOCK TABLES `shipments` WRITE;
/*!40000 ALTER TABLE `shipments` DISABLE KEYS */;
/*!40000 ALTER TABLE `shipments` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_shipments_mysql57_guard` BEFORE INSERT ON `shipments`
FOR EACH ROW
BEGIN
  IF (NEW.`cost` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_shipments_cost failed';
  END IF;
  IF (NEW.`status` IN ('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_shipments_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_shipments_mysql57_guard` BEFORE UPDATE ON `shipments`
FOR EACH ROW
BEGIN
  IF (NEW.`cost` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_shipments_cost failed';
  END IF;
  IF (NEW.`status` IN ('pending','created','picked_up','in_transit','delivered','failed','returned','cancelled')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_shipments_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `shipping_quotes`
--

DROP TABLE IF EXISTS `shipping_quotes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shipping_quotes` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `provider` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'everpro',
  `provider_quote_id` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `origin_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `destination_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `courier_code` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `service_code` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `service_label` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `weight_gram` int(11) NOT NULL,
  `cost` decimal(18,2) NOT NULL,
  `insurance_cost` decimal(18,2) NOT NULL DEFAULT '0.00',
  `currency` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'IDR',
  `estimated_delivery` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cart_fingerprint` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `expires_at` datetime(6) NOT NULL,
  `request_payload` json DEFAULT NULL,
  `response_payload` json DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_shipping_quotes_id_user_id` (`id`,`user_id`),
  KEY `ix_shipping_quotes_user_expiry` (`user_id`,`expires_at`),
  CONSTRAINT `fk_shipping_quotes_user_id_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shipping_quotes`
--

LOCK TABLES `shipping_quotes` WRITE;
/*!40000 ALTER TABLE `shipping_quotes` DISABLE KEYS */;
/*!40000 ALTER TABLE `shipping_quotes` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_shipping_quotes_mysql57_guard` BEFORE INSERT ON `shipping_quotes`
FOR EACH ROW
BEGIN
  IF (NEW.`weight_gram` > 0 AND NEW.`cost` >= 0 AND NEW.`insurance_cost` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_shipping_quotes_amounts failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_shipping_quotes_mysql57_guard` BEFORE UPDATE ON `shipping_quotes`
FOR EACH ROW
BEGIN
  IF (NEW.`weight_gram` > 0 AND NEW.`cost` >= 0 AND NEW.`insurance_cost` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_shipping_quotes_amounts failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `stock_movements`
--

DROP TABLE IF EXISTS `stock_movements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `stock_movements` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `variant_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `reservation_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `type` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `quantity` int(11) NOT NULL,
  `delta` int(11) DEFAULT NULL,
  `reserved_delta` int(11) DEFAULT NULL,
  `stock_after` int(11) DEFAULT NULL,
  `reserved_after` int(11) DEFAULT NULL,
  `note` text COLLATE utf8mb4_unicode_ci,
  `admin_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `fk_stock_movements_admin_id_users_user_id` (`admin_id`),
  KEY `fk_stock_movements_product_id_variant_id_produ_3a401ac45048` (`product_id`,`variant_id`),
  KEY `fk_stock_movements_reservation_id_stock_reservations_id` (`reservation_id`),
  KEY `ix_stock_movements_order_id` (`order_id`),
  KEY `ix_stock_movements_product_date` (`product_id`,`created_at`,`id`),
  CONSTRAINT `fk_stock_movements_admin_id_users_user_id` FOREIGN KEY (`admin_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `fk_stock_movements_order_id_orders_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`),
  CONSTRAINT `fk_stock_movements_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `fk_stock_movements_product_id_variant_id_produ_3a401ac45048` FOREIGN KEY (`product_id`, `variant_id`) REFERENCES `product_variants` (`product_id`, `id`),
  CONSTRAINT `fk_stock_movements_reservation_id_stock_reservations_id` FOREIGN KEY (`reservation_id`) REFERENCES `stock_reservations` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_movements`
--

LOCK TABLES `stock_movements` WRITE;
/*!40000 ALTER TABLE `stock_movements` DISABLE KEYS */;
/*!40000 ALTER TABLE `stock_movements` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_stock_movements_mysql57_guard` BEFORE INSERT ON `stock_movements`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_movements_quantity failed';
  END IF;
  IF (NEW.`reserved_after` IS NULL OR NEW.`reserved_after` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_movements_reserved_after failed';
  END IF;
  IF (NEW.`stock_after` IS NULL OR NEW.`stock_after` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_movements_stock_after failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_stock_movements_mysql57_guard` BEFORE UPDATE ON `stock_movements`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_movements_quantity failed';
  END IF;
  IF (NEW.`reserved_after` IS NULL OR NEW.`reserved_after` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_movements_reserved_after failed';
  END IF;
  IF (NEW.`stock_after` IS NULL OR NEW.`stock_after` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_movements_stock_after failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `stock_reservations`
--

DROP TABLE IF EXISTS `stock_reservations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `stock_reservations` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_item_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `variant_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `quantity` int(11) NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active',
  `expires_at` datetime(6) NOT NULL,
  `resolved_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `fk_stock_reservations_order_item_id_order_id_o_b9f7577dedc3` (`order_item_id`,`order_id`),
  KEY `fk_stock_reservations_product_id_variant_id_pr_ea500bef0394` (`product_id`,`variant_id`),
  KEY `ix_stock_reservations_expiry` (`status`,`expires_at`,`id`),
  KEY `ix_stock_reservations_order` (`order_id`,`status`),
  CONSTRAINT `fk_stock_reservations_order_id_orders_id` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`),
  CONSTRAINT `fk_stock_reservations_order_item_id_order_id_o_b9f7577dedc3` FOREIGN KEY (`order_item_id`, `order_id`) REFERENCES `order_items` (`id`, `order_id`),
  CONSTRAINT `fk_stock_reservations_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `fk_stock_reservations_product_id_variant_id_pr_ea500bef0394` FOREIGN KEY (`product_id`, `variant_id`) REFERENCES `product_variants` (`product_id`, `id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_reservations`
--

LOCK TABLES `stock_reservations` WRITE;
/*!40000 ALTER TABLE `stock_reservations` DISABLE KEYS */;
/*!40000 ALTER TABLE `stock_reservations` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_stock_reservations_mysql57_guard` BEFORE INSERT ON `stock_reservations`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_reservations_quantity failed';
  END IF;
  IF (NEW.`status` IN ('active','confirmed','expired','cancelled')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_reservations_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_stock_reservations_mysql57_guard` BEFORE UPDATE ON `stock_reservations`
FOR EACH ROW
BEGIN
  IF (NEW.`quantity` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_reservations_quantity failed';
  END IF;
  IF (NEW.`status` IN ('active','confirmed','expired','cancelled')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_stock_reservations_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `uploads`
--

DROP TABLE IF EXISTS `uploads`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `uploads` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `url` text COLLATE utf8mb4_unicode_ci,
  `filename` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `mime` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `size` bigint(20) NOT NULL,
  `subdir` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `disk_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `storage_provider` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'local',
  `storage_key` text COLLATE utf8mb4_unicode_ci,
  `visibility` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'public',
  `sha256` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `uploaded_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `uploaded_by_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `ix_uploads_uploaded_by` (`uploaded_by`),
  CONSTRAINT `fk_uploads_uploaded_by_users_user_id` FOREIGN KEY (`uploaded_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `uploads`
--

LOCK TABLES `uploads` WRITE;
/*!40000 ALTER TABLE `uploads` DISABLE KEYS */;
INSERT INTO `uploads` VALUES ('3eed6e246ddb4844beb7c8935e2fd691','/api/uploads-files/2026-11/3eed6e246ddb4844beb7c8935e2fd691.png','Gemini_Generated_Image_9i8b549i8b549i8b-removebg-preview.png','image/png',50732,'2026-11','3eed6e246ddb4844beb7c8935e2fd691.png','local','2026-11/3eed6e246ddb4844beb7c8935e2fd691.png','public','4011ed1300c69e19d5145b0dfd3ee07bc05aac9cf3e0925566d5b411f491c0e4','usr_c4b3d45ff0b94ffd','Mira Admin','2026-11-10 00:52:36.511838'),('4065c8756ccb44b0be2936273e648135','/api/prescriptions/uploads/4065c8756ccb44b0be2936273e648135','29605.png','image/jpeg',36891,'prescriptions/2026-11','4065c8756ccb44b0be2936273e648135.jpg','local','prescriptions/2026-11/4065c8756ccb44b0be2936273e648135.jpg','private','4b4dce5c2943246f3181c49cbd846084e8efc96dd78c0dad6c2adb74f9bca55f','usr_c4b3d45ff0b94ffd','Mira Admin','2026-11-09 09:23:03.808629'),('542a872b5b464ee9988609765c6595f9','/api/uploads-files/2026-11/542a872b5b464ee9988609765c6595f9.png','Gemini_Generated_Image_cv8urgcv8urgcv8u-removebg-preview.png','image/png',69898,'2026-11','542a872b5b464ee9988609765c6595f9.png','local','2026-11/542a872b5b464ee9988609765c6595f9.png','public','b5e06bcfe6080444e72d0e2aca06d15bf8f488d749f6607ca572634b60768d35','usr_c4b3d45ff0b94ffd','Mira Admin','2026-11-10 01:01:24.329725'),('5da31d90d3d34b85923d87cee36ffade','/api/uploads-files/2026-11/5da31d90d3d34b85923d87cee36ffade.png','Gemini_Generated_Image_9i8b549i8b549i8b-removebg-preview.png','image/png',50732,'2026-11','5da31d90d3d34b85923d87cee36ffade.png','local','2026-11/5da31d90d3d34b85923d87cee36ffade.png','public','4011ed1300c69e19d5145b0dfd3ee07bc05aac9cf3e0925566d5b411f491c0e4','usr_c4b3d45ff0b94ffd','Mira Admin','2026-11-10 00:52:42.281936'),('63366d1229cc44fb9cbce106a51aa37b','/api/uploads-files/2026-11/63366d1229cc44fb9cbce106a51aa37b.png','LUNAS LOGO.png','image/png',27440,'2026-11','63366d1229cc44fb9cbce106a51aa37b.png','local','2026-11/63366d1229cc44fb9cbce106a51aa37b.png','public','54a7b9e23d0889e8be25f6b1b4761cf51f904a802cd9ec866a1df6b3265f894c','usr_c4b3d45ff0b94ffd','Mira Admin','2026-11-09 10:00:56.407642'),('9f47f9979d854aceaceb7edcd5082d8d','/api/uploads-files/2026-11/9f47f9979d854aceaceb7edcd5082d8d.png','Gemini_Generated_Image_cceyrscceyrsccey-removebg-preview.png','image/png',69227,'2026-11','9f47f9979d854aceaceb7edcd5082d8d.png','local','2026-11/9f47f9979d854aceaceb7edcd5082d8d.png','public','e3f7930f40697a3c1b869f96f158c176e8f7bfd8cc63a2006c4c618411419b55','usr_c4b3d45ff0b94ffd','Mira Admin','2026-11-10 00:12:35.191819'),('b00dd2a1231440c79cf0f853bfbf5c03','/api/uploads-files/2026-11/b00dd2a1231440c79cf0f853bfbf5c03.jpg','5FAkX1btyAsvEGXZDn6CA6sfCBS.jpg','image/jpeg',1088704,'2026-11','b00dd2a1231440c79cf0f853bfbf5c03.jpg','local','2026-11/b00dd2a1231440c79cf0f853bfbf5c03.jpg','public','26187b03e8145bf4765f30bd8683c2ce510c4de4b926b9fae5a45386a785c51c','usr_c4b3d45ff0b94ffd','Mira Admin','2026-11-10 01:33:56.309194'),('b1233b64f2e0436e9043ae8844192626','/api/uploads-files/2026-11/b1233b64f2e0436e9043ae8844192626.png','Gemini_Generated_Image_cceyrscceyrsccey-removebg-preview.png','image/png',69227,'2026-11','b1233b64f2e0436e9043ae8844192626.png','local','2026-11/b1233b64f2e0436e9043ae8844192626.png','public','e3f7930f40697a3c1b869f96f158c176e8f7bfd8cc63a2006c4c618411419b55','usr_c4b3d45ff0b94ffd','Mira Admin','2026-11-10 00:12:43.632588'),('bb59151189804c248e3aa87da5c70991','/api/uploads-files/2026-11/bb59151189804c248e3aa87da5c70991.png','LUNAS LOGO.png','image/png',27440,'2026-11','bb59151189804c248e3aa87da5c70991.png','local','2026-11/bb59151189804c248e3aa87da5c70991.png','public','54a7b9e23d0889e8be25f6b1b4761cf51f904a802cd9ec866a1df6b3265f894c','usr_c4b3d45ff0b94ffd','Mira Admin','2026-11-09 10:01:16.483539'),('bcdbe02d956c4acbaefc84844a643b79','/api/uploads-files/2026-11/bcdbe02d956c4acbaefc84844a643b79.jpg','5FAkX1btyAsvEGXZDn6CA6sfCBS.jpg','image/jpeg',1088704,'2026-11','bcdbe02d956c4acbaefc84844a643b79.jpg','local','2026-11/bcdbe02d956c4acbaefc84844a643b79.jpg','public','26187b03e8145bf4765f30bd8683c2ce510c4de4b926b9fae5a45386a785c51c','usr_c4b3d45ff0b94ffd','Mira Admin','2026-11-10 01:34:01.111325'),('d40db435cb2545fea4cee72853e3f772','/api/uploads-files/2026-11/d40db435cb2545fea4cee72853e3f772.png','Gemini_Generated_Image_cv8urgcv8urgcv8u-removebg-preview.png','image/png',69898,'2026-11','d40db435cb2545fea4cee72853e3f772.png','local','2026-11/d40db435cb2545fea4cee72853e3f772.png','public','b5e06bcfe6080444e72d0e2aca06d15bf8f488d749f6607ca572634b60768d35','usr_c4b3d45ff0b94ffd','Mira Admin','2026-11-10 01:01:19.090750'),('d5419dd7180c47c8be57f421ea96ab5e','/api/uploads-files/2026-11/d5419dd7180c47c8be57f421ea96ab5e.jpg','5FAkX1btyAsvEGXZDn6CA6sfCBS.jpg','image/jpeg',1088704,'2026-11','d5419dd7180c47c8be57f421ea96ab5e.jpg','local','2026-11/d5419dd7180c47c8be57f421ea96ab5e.jpg','public','26187b03e8145bf4765f30bd8683c2ce510c4de4b926b9fae5a45386a785c51c','usr_c4b3d45ff0b94ffd','Mira Admin','2026-11-10 02:36:56.958581');
/*!40000 ALTER TABLE `uploads` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_uploads_mysql57_guard` BEFORE INSERT ON `uploads`
FOR EACH ROW
BEGIN
  IF (NEW.`size` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_uploads_size failed';
  END IF;
  IF (NEW.`visibility` IN ('public','private')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_uploads_visibility failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_uploads_mysql57_guard` BEFORE UPDATE ON `uploads`
FOR EACH ROW
BEGIN
  IF (NEW.`size` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_uploads_size failed';
  END IF;
  IF (NEW.`visibility` IN ('public','private')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_uploads_visibility failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `user_permissions`
--

DROP TABLE IF EXISTS `user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_permissions` (
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `permission` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`user_id`,`permission`),
  CONSTRAINT `fk_user_permissions_user_id_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_permissions`
--

LOCK TABLES `user_permissions` WRITE;
/*!40000 ALTER TABLE `user_permissions` DISABLE KEYS */;
INSERT INTO `user_permissions` VALUES ('usr_c071c5fd6a6743b4','article.create'),('usr_c071c5fd6a6743b4','article.delete'),('usr_c071c5fd6a6743b4','article.update'),('usr_c071c5fd6a6743b4','article.view'),('usr_c071c5fd6a6743b4','review.moderate'),('usr_c071c5fd6a6743b4','review.view');
/*!40000 ALTER TABLE `user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_sessions`
--

DROP TABLE IF EXISTS `user_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_sessions` (
  `session_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `token_hash` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `expires_at` datetime(6) NOT NULL,
  `revoked_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`session_id`),
  UNIQUE KEY `uq_user_sessions_token_hash` (`token_hash`),
  KEY `ix_user_sessions_expiry` (`expires_at`),
  KEY `ix_user_sessions_user_id` (`user_id`),
  CONSTRAINT `fk_user_sessions_user_id_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_sessions`
--

LOCK TABLES `user_sessions` WRITE;
/*!40000 ALTER TABLE `user_sessions` DISABLE KEYS */;
INSERT INTO `user_sessions` VALUES ('ses_16012d9c8f494795','526a69d6a64843fa6a52ccb98736b8711a927d34943a4e15a8b46b0253cee9be','usr_c4b3d45ff0b94ffd','2026-11-16 08:34:53.001903',NULL,'2026-11-09 08:34:53.069899'),('ses_3514f08476274c8c','f05931ac088ce85974e8fa62d19b73d9099acde77f76b0e8fc35ffcba2677459','usr_c4b3d45ff0b94ffd','2026-11-17 00:13:27.632043',NULL,'2026-11-10 00:13:27.635981'),('ses_5eb20817174a451b','8ca6a19bc25b5160482fbeacc03bac1601009d238bf5f3ae289d869d3117a165','usr_c4b3d45ff0b94ffd','2026-11-17 02:28:34.776892',NULL,'2026-11-10 02:28:34.783081'),('ses_93ba276471d84fc1','d94fcc93b03fd828d2bbda4e0c01f5a37220bfe07050a8afbfca12a39f007465','usr_bf93cc1fff4a42d1','2026-11-11 01:22:13.000302',NULL,'2026-11-04 01:22:13.000540'),('ses_dc2a424515624a84','48f6764c015e0a662d484e2b8b64d79acb0c8729949185337e8e1ce0f522ddde','usr_c4b3d45ff0b94ffd','2026-11-04 08:46:51.901001',NULL,'2026-10-28 08:46:51.901185');
/*!40000 ALTER TABLE `user_sessions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `picture` text COLLATE utf8mb4_unicode_ci,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `pin_hash` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `pin_failed_attempts` int(11) NOT NULL DEFAULT '0',
  `pin_locked_until` datetime(6) DEFAULT NULL,
  `role` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'customer',
  `provider` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'password',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `points_balance` bigint(20) NOT NULL DEFAULT '0',
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `uq_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES ('usr_bf93cc1fff4a42d1','customer@meoweyes.id','Lulu Customer',NULL,'$2b$12$VVM0n73HPwM9wzdl1wCAI.OjZhN85j3lxXpbOYywQkWZi/sXxv/tq','$2b$12$BzL3fjCBpFtRPZMFfrL60uv9FnPlTFEvQnt7NUJ8DcHT3QicRqRAW',0,NULL,'customer','password',1,500,'2026-10-23 07:58:10.911690','2026-10-23 07:58:10.911672'),('usr_c071c5fd6a6743b4','staff@meoweyes.id','Staff Content',NULL,'$2b$12$AVrsFGRf4HtygV0XxUV8A.nIKrdbEGqcDxs2133h0EDTyZjz3xWA6','$2b$12$VVXO9di.HXgAG/vimJwgBu6Bdbb.tveHtwxrxUnfb26pWbW6izbr6',0,NULL,'staff','password',1,0,'2026-10-23 07:58:11.770223','2026-10-23 07:58:11.770205'),('usr_c4b3d45ff0b94ffd','admin@meoweyes.id','Mira Admin',NULL,'$2b$12$xkyFQ5ENjVdce7gDNBRmj.etdFA2Ac1v.vwA96DFwf7IL9wK9OR02','$2b$12$3ondzdlTsf8H5mV/5M1pw.B5DO2l0arthATYALu7qIjlcLGZLnUrO',0,NULL,'super_admin','password',1,73,'2026-11-10 02:22:00.480728','2026-10-23 07:58:10.162702');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_users_mysql57_guard` BEFORE INSERT ON `users`
FOR EACH ROW
BEGIN
  IF (NEW.`pin_failed_attempts` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_users_pin_attempts_nonnegative failed';
  END IF;
  IF (NEW.`points_balance` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_users_points_nonnegative failed';
  END IF;
  IF (NEW.`role` IN ('customer','staff','admin','super_admin')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_users_role failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_users_mysql57_guard` BEFORE UPDATE ON `users`
FOR EACH ROW
BEGIN
  IF (NEW.`pin_failed_attempts` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_users_pin_attempts_nonnegative failed';
  END IF;
  IF (NEW.`points_balance` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_users_points_nonnegative failed';
  END IF;
  IF (NEW.`role` IN ('customer','staff','admin','super_admin')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_users_role failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `virtual_try_on_assets`
--

DROP TABLE IF EXISTS `virtual_try_on_assets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `virtual_try_on_assets` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `variant_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `asset_type` varchar(8) COLLATE utf8mb4_unicode_ci NOT NULL,
  `upload_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `source_url` text COLLATE utf8mb4_unicode_ci,
  `preview_url` text COLLATE utf8mb4_unicode_ci,
  `scale` decimal(10,5) NOT NULL DEFAULT '1.00000',
  `offset_x` decimal(10,5) NOT NULL DEFAULT '0.00000',
  `offset_y` decimal(10,5) NOT NULL DEFAULT '0.00000',
  `offset_z` decimal(10,5) NOT NULL DEFAULT '0.00000',
  `rotation_x` decimal(10,5) NOT NULL DEFAULT '0.00000',
  `rotation_y` decimal(10,5) NOT NULL DEFAULT '0.00000',
  `rotation_z` decimal(10,5) NOT NULL DEFAULT '0.00000',
  `calibration` json DEFAULT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'draft',
  `sort_order` int(11) NOT NULL DEFAULT '0',
  `updated_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `fk_virtual_try_on_assets_product_id_variant_id_eacdeed585b2` (`product_id`,`variant_id`),
  KEY `fk_virtual_try_on_assets_updated_by_users_user_id` (`updated_by`),
  KEY `fk_virtual_try_on_assets_upload_id_uploads_id` (`upload_id`),
  KEY `ix_vto_product_status` (`product_id`,`status`,`sort_order`),
  CONSTRAINT `fk_virtual_try_on_assets_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `fk_virtual_try_on_assets_product_id_variant_id_eacdeed585b2` FOREIGN KEY (`product_id`, `variant_id`) REFERENCES `product_variants` (`product_id`, `id`),
  CONSTRAINT `fk_virtual_try_on_assets_updated_by_users_user_id` FOREIGN KEY (`updated_by`) REFERENCES `users` (`user_id`),
  CONSTRAINT `fk_virtual_try_on_assets_upload_id_uploads_id` FOREIGN KEY (`upload_id`) REFERENCES `uploads` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `virtual_try_on_assets`
--

LOCK TABLES `virtual_try_on_assets` WRITE;
/*!40000 ALTER TABLE `virtual_try_on_assets` DISABLE KEYS */;
INSERT INTO `virtual_try_on_assets` VALUES ('1bcc8c3543ea42748f3ab302b340088c','prd_898f994b888240ab',NULL,'image',NULL,'/api/uploads-files/2026-11/d40db435cb2545fea4cee72853e3f772.png','/api/uploads-files/2026-11/542a872b5b464ee9988609765c6595f9.png',1.00000,0.00000,0.00000,0.00000,0.00000,0.00000,0.00000,'null','published',0,'usr_c4b3d45ff0b94ffd','2026-11-10 01:01:30.489701','2026-11-10 00:12:55.289720');
/*!40000 ALTER TABLE `virtual_try_on_assets` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_virtual_try_on_assets_mysql57_guard` BEFORE INSERT ON `virtual_try_on_assets`
FOR EACH ROW
BEGIN
  IF (NEW.`asset_type` IN ('image','glb','gltf')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_virtual_try_on_assets_asset_type failed';
  END IF;
  IF (NEW.`scale` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_virtual_try_on_assets_scale failed';
  END IF;
  IF (NEW.`upload_id` IS NOT NULL OR NEW.`source_url` IS NOT NULL) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_virtual_try_on_assets_source failed';
  END IF;
  IF (NEW.`status` IN ('draft','published','archived')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_virtual_try_on_assets_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_virtual_try_on_assets_mysql57_guard` BEFORE UPDATE ON `virtual_try_on_assets`
FOR EACH ROW
BEGIN
  IF (NEW.`asset_type` IN ('image','glb','gltf')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_virtual_try_on_assets_asset_type failed';
  END IF;
  IF (NEW.`scale` > 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_virtual_try_on_assets_scale failed';
  END IF;
  IF (NEW.`upload_id` IS NOT NULL OR NEW.`source_url` IS NOT NULL) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_virtual_try_on_assets_source failed';
  END IF;
  IF (NEW.`status` IN ('draft','published','archived')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_virtual_try_on_assets_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `voucher_redemptions`
--

DROP TABLE IF EXISTS `voucher_redemptions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `voucher_redemptions` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `voucher_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `order_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `discount_amount` decimal(18,2) NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'reserved',
  `resolved_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_voucher_redemptions_order_id` (`order_id`),
  KEY `fk_voucher_redemptions_order_id_user_id_orders_958e8f3a8056` (`order_id`,`user_id`),
  KEY `ix_voucher_redemptions_quota` (`voucher_id`,`user_id`,`status`),
  CONSTRAINT `fk_voucher_redemptions_order_id_user_id_orders_958e8f3a8056` FOREIGN KEY (`order_id`, `user_id`) REFERENCES `orders` (`id`, `user_id`),
  CONSTRAINT `fk_voucher_redemptions_voucher_id_vouchers_id` FOREIGN KEY (`voucher_id`) REFERENCES `vouchers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `voucher_redemptions`
--

LOCK TABLES `voucher_redemptions` WRITE;
/*!40000 ALTER TABLE `voucher_redemptions` DISABLE KEYS */;
/*!40000 ALTER TABLE `voucher_redemptions` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_voucher_redemptions_mysql57_guard` BEFORE INSERT ON `voucher_redemptions`
FOR EACH ROW
BEGIN
  IF (NEW.`discount_amount` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_voucher_redemptions_amount failed';
  END IF;
  IF (NEW.`status` IN ('reserved','redeemed','released')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_voucher_redemptions_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_voucher_redemptions_mysql57_guard` BEFORE UPDATE ON `voucher_redemptions`
FOR EACH ROW
BEGIN
  IF (NEW.`discount_amount` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_voucher_redemptions_amount failed';
  END IF;
  IF (NEW.`status` IN ('reserved','redeemed','released')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_voucher_redemptions_status failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `vouchers`
--

DROP TABLE IF EXISTS `vouchers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `vouchers` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `code` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `discount_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `discount_value` decimal(18,2) NOT NULL DEFAULT '0.00',
  `min_purchase` decimal(18,2) NOT NULL DEFAULT '0.00',
  `max_discount` decimal(18,2) DEFAULT NULL,
  `quota` int(11) NOT NULL DEFAULT '100',
  `used_count` int(11) NOT NULL DEFAULT '0',
  `quota_per_user` int(11) NOT NULL DEFAULT '1',
  `start_at` datetime(6) NOT NULL,
  `end_at` datetime(6) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_vouchers_code` (`code`),
  KEY `ix_vouchers_window` (`is_active`,`start_at`,`end_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vouchers`
--

LOCK TABLES `vouchers` WRITE;
/*!40000 ALTER TABLE `vouchers` DISABLE KEYS */;
INSERT INTO `vouchers` VALUES ('vch_6f8c69cca5274357','MEOWWELCOME','Diskon Selamat Datang 15%','percent',15.00,250000.00,100000.00,500,0,1,'2026-10-23 07:58:20.536577','2027-10-23 07:58:20.536577',1,'2026-10-23 07:58:20.556745'),('vch_9018711ea1bc49ff','GRATISONGKIR','Gratis Ongkir','free_shipping',0.00,200000.00,NULL,300,0,1,'2026-10-23 07:58:20.536577','2027-10-23 07:58:20.536577',1,'2026-10-23 07:58:20.653947'),('vch_a1d7c53fff644a0e','MEOW50K','Potongan Rp 50.000','nominal',50000.00,500000.00,NULL,200,0,1,'2026-10-23 07:58:20.536577','2027-10-23 07:58:20.536577',1,'2026-10-23 07:58:20.708264');
/*!40000 ALTER TABLE `vouchers` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_vouchers_mysql57_guard` BEFORE INSERT ON `vouchers`
FOR EACH ROW
BEGIN
  IF (NEW.`discount_value` >= 0 AND NEW.`min_purchase` >= 0 AND (NEW.`max_discount` IS NULL OR NEW.`max_discount` >= 0)) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_amounts failed';
  END IF;
  IF (NEW.`discount_type` <> 'percent' OR NEW.`discount_value` <= 100) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_percentage failed';
  END IF;
  IF (NEW.`quota` >= 0 AND NEW.`used_count` >= 0 AND NEW.`used_count` <= NEW.`quota` AND NEW.`quota_per_user` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_quotas failed';
  END IF;
  IF (NEW.`discount_type` IN ('percent','nominal','free_shipping')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_type failed';
  END IF;
  IF (NEW.`end_at` > NEW.`start_at`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_window failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_vouchers_mysql57_guard` BEFORE UPDATE ON `vouchers`
FOR EACH ROW
BEGIN
  IF (NEW.`discount_value` >= 0 AND NEW.`min_purchase` >= 0 AND (NEW.`max_discount` IS NULL OR NEW.`max_discount` >= 0)) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_amounts failed';
  END IF;
  IF (NEW.`discount_type` <> 'percent' OR NEW.`discount_value` <= 100) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_percentage failed';
  END IF;
  IF (NEW.`quota` >= 0 AND NEW.`used_count` >= 0 AND NEW.`used_count` <= NEW.`quota` AND NEW.`quota_per_user` >= 0) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_quotas failed';
  END IF;
  IF (NEW.`discount_type` IN ('percent','nominal','free_shipping')) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_type failed';
  END IF;
  IF (NEW.`end_at` > NEW.`start_at`) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_vouchers_window failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `whatsapp_settings`
--

DROP TABLE IF EXISTS `whatsapp_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `whatsapp_settings` (
  `id` smallint(6) NOT NULL,
  `phone` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `default_text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_enabled` tinyint(1) NOT NULL DEFAULT '0',
  `updated_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  KEY `fk_whatsapp_settings_updated_by_users_user_id` (`updated_by`),
  CONSTRAINT `fk_whatsapp_settings_updated_by_users_user_id` FOREIGN KEY (`updated_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `whatsapp_settings`
--

LOCK TABLES `whatsapp_settings` WRITE;
/*!40000 ALTER TABLE `whatsapp_settings` DISABLE KEYS */;
INSERT INTO `whatsapp_settings` VALUES (1,'6281234567890','Saya ingin order kacamata, boleh tolong dibantu kak.',1,'usr_c4b3d45ff0b94ffd','2026-11-09 23:42:06.231590');
/*!40000 ALTER TABLE `whatsapp_settings` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bi_whatsapp_settings_mysql57_guard` BEFORE INSERT ON `whatsapp_settings`
FOR EACH ROW
BEGIN
  IF (NEW.`id` = 1) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_whatsapp_settings_singleton failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`meowsysadmin`@`192.168.%`*/ /*!50003 TRIGGER `bu_whatsapp_settings_mysql57_guard` BEFORE UPDATE ON `whatsapp_settings`
FOR EACH ROW
BEGIN
  IF (NEW.`id` = 1) IS FALSE THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Integrity rule ck_whatsapp_settings_singleton failed';
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `wishlists`
--

DROP TABLE IF EXISTS `wishlists`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wishlists` (
  `id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `product_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_wishlists_user_id_product_id` (`user_id`,`product_id`),
  KEY `fk_wishlists_product_id_products_id` (`product_id`),
  CONSTRAINT `fk_wishlists_product_id_products_id` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_wishlists_user_id_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wishlists`
--

LOCK TABLES `wishlists` WRITE;
/*!40000 ALTER TABLE `wishlists` DISABLE KEYS */;
/*!40000 ALTER TABLE `wishlists` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'db_meoweyes'
--

--
-- Dumping routines for database 'db_meoweyes'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-10 11:05:12
