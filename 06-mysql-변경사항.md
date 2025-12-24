

1. user_subscriptions 테이블 삭제
2. users 테이블에 컬럼추가됨
- 추가된 컬럼
    - subscription_status
    - subscription_start_date
    - subscription_end_date
    - subscription_id

CREATE TABLE `users` (
  `user_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `email` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `gender` tinyint(1) NOT NULL COMMENT '0=남성, 1=여성, 2=기타',
  `birth_date` date NOT NULL,
  `country` char(2) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'KR',
  `city` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `signup_date` date NOT NULL,
  `account_status` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active' COMMENT 'active, suspended, deleted',
  `is_adult_verified` tinyint(1) NOT NULL DEFAULT '0' COMMENT '0=미인증, 1=인증',
  `last_login_date` datetime DEFAULT NULL,
  `device_last_used` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'mobile, tablet, desktop, tv, console',
  `push_opt_in` tinyint(1) NOT NULL DEFAULT '1' COMMENT '0=미수신, 1=수신',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `subscription_status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `subscription_start_date` date DEFAULT NULL,
  `subscription_end_date` date DEFAULT NULL,
  `subscription_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_country` (`country`),
  KEY `idx_signup_date` (`signup_date`),
  KEY `idx_account_status` (`account_status`)
) ENGINE=InnoDB AUTO_INCREMENT=201272 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

user_id|email                        |password_hash                                                   |name                |gender|birth_date|country|city       |signup_date|account_status|is_adult_verified|last_login_date    |device_last_used|push_opt_in|created_at         |updated_at         |subscription_status|subscription_start_date|subscription_end_date|subscription_id|
-------+-----------------------------+----------------------------------------------------------------+--------------------+------+----------+-------+-----------+-----------+--------------+-----------------+-------------------+----------------+-----------+-------------------+-------------------+-------------------+-----------------------+---------------------+---------------+
 100001|user1_6078@ottservice.com    |4efabaf882f7ee7b116c0d14722dfc3007a67fd21d45e5a900c8d85efced2d1e|김하윤                 |     1|1993-11-15|KR     |제주         | 2023-05-27|active        |                1|2025-12-12 00:00:00|mobile          |          0|2025-12-08 07:11:07|2025-12-23 06:03:17|active             |             2025-01-29|           2026-01-29|s_4            |
 100002|user2_9095@ottservice.com    |b4d4918a2a203a47596898cfcc9f0614cc04a08e920ed06b35235090a8fc787c|최미영                 |     1|1981-10-19|KR     |경남         | 2022-11-27|active        |                1|2024-08-08 06:38:35|tablet          |          0|2025-12-08 07:11:07|2025-12-23 06:03:17|expired            |             2025-04-03|           2025-05-03|s_5            |
 100003|user3_1535@ottservice.com    |b3316020e1f563c1f005d20e1a30ab05c70b4660f6fe6289dacfae3169844c55|박준혁                 |     1|1977-04-20|KR     |부산         | 2020-12-17|deleted       |                1|2025-12-12 00:00:00|mobile          |          0|2025-12-08 07:11:07|2025-12-23 06:03:17|cancelled          |             2025-12-12|           2026-01-11|s_8            |
 100004|user4_4078@ottservice.com    |101b66c70c508b52fdfdb07667b20dcece8912e274ce89cb5f2ab6f8bae006b6|배승민                 |     0|2004-02-14|KR     |전남         | 2020-08-23|deleted       |                1|2023-12-19 02:08:11|mobile          |          1|2025-12-08 07:11:07|2025-12-23 06:03:17|expired            |             2023-11-27|           2023-12-27|s_1            |
 100005|user5_9046@ottservice.com    |0e1cdb7f1c45a6cde5135008149bb5d31af08a1fdf963a08ab6595e2a906626f|김성진                 |     0|1988-04-15|KR     |경기         | 2023-09-08|active        |                1|2024-04-11 14:50:31|tablet          |          0|2025-12-08 07:11:07|2025-12-23 06:03:17|cancelled          |             2025-07-26|           2025-08-26|s_9            |
 100006|user6_4142@ottservice.com    |32d26b744e80b322cdc23741b419877a8d97e806148fe3021575ec0af6db07b6|김은정                 |     0|1972-08-20|KR     |부산         | 2024-08-13|suspended     |                1|2025-03-25 01:15:23|tv              |          0|2025-12-08 07:11:07|2025-12-08 07:11:07|                   |                       |                     |               |
 100007|user7_1914@ottservice.com    |edae4cdc3ec917309fcef1f77267b0b7af625881525d779ed8746ae141b4e5e5|김정훈                 |     0|1964-02-22|KR     |경기         | 2020-07-05|active        |                1|2025-12-19 00:00:00|tablet          |          0|2025-12-08 07:11:07|2025-12-23 06:03:17|cancelled          |             2025-12-19|           2026-01-18|s_6            |
 100008|user8_1254@ottservice.com    |67a82ebdffcd1abb7d16457139451d42f2a91ebe7bc1d08a4ed98fc4517741a3|김동현                 |     1|1985-06-20|KR     |울산         | 2024-08-08|active        |                1|2025-07-31 22:22:01|tv              |          1|2025-12-08 07:11:07|2025-12-08 07:11:07|                   |                       |                     |               |
 100009|user9_8535@ottservice.com    |6fda84c0446987a551081db6b0928da68379ca3c7ed82b6394395df7288d7588|이민재                 |     0|1972-11-24|KR     |대구         | 2025-10-15|active        |                1|2025-11-13 03:02:47|tv              |          1|2025-12-08 07:11:07|2025-12-23 06:03:17|active             |             2025-11-02|           2026-02-02|s_6            |
 100010|user10_6497@ottservice.com   |b7705afc963b8e7b9df5e329f78a6d08d6f7413c3b9fb20efda4d1865dce667a|이영미                 |     1|1977-11-26|KR     |서울         | 2024-04-14|active        |                1|2025-02-28 18:56:26|mobile          |          0|2025-12-08 07:11:07|2025-12-08 07:11:07|                   |                       |                     |               |
 100011|user11_8028@ottservice.com   |78eb2514098e93a9922638ec96c7cd1aec1ecb28d514b742c9b9e5bdc9274c36|松本 加奈               |     1|1971-03-07|JP     |Osaka      | 2025-12-20|active        |                1|2025-12-20 00:00:01|tv              |          0|2025-12-08 07:11:07|2025-12-23 06:03:17|cancelled          |             2025-12-21|           2026-01-21|s_5            
 100012|user12_8222@ottservice.com   |72ae0af519e84278cd3d04ab45e0b387dba127b4347af6d09b2b837980ef9981|강정남                 |     1|1999-06-12|KR     |제주         | 2022-06-22|active        |                1|2023-12-27 12:25:19|desktop         |          1|2025-12-08 07:11:07|2025-12-23 06:03:17|expired            |             2023-03-07|           2024-03-07|s_4            |
 100013|user13_2043@ottservice.com   |9c9f0be72ba999f1799fc493d41342bfb00ecb90116eb94a272343e327d40616|罗建华                 |     0|1973-07-10|CN     |Chengdu    | 2023-01-18|active        |                1|2024-10-20 11:26:48|mobile          |          1|2025-12-08 07:11:07|2025-12-23 06:03:17|expired            |             2023-04-24|           2024-04-24|s_4            
 100014|user14_5801@ottservice.com   |0ec39fd263a3383df05337b2b409899225e2cc4e81c70c60d51bc023812cba6c|양영식                 |     0|1977-09-03|KR     |인천         | 2024-02-24|active        |                1|2024-11-18 19:50:59|mobile          |          1|2025-12-08 07:11:07|2025-12-23 06:03:17|expired            |             2024-07-05|           2024-10-05|s_2            |



 3. users 테이블 관련 코드 수정필요
 kafka-log\src\user_selector.py
 kafka-log\src\user_controller.py
 kafka-log\src\log_contents.py
 kafka-log\src\db_client.py

 - 유저의 구독여부를 users테이블의 subscription_status컬럼의 값이 'active'일 때 구독중인 유저로 판단해야함, 나머지는 구독하지않는 상태로 처리해야함(subscription_status컬럼의 값 : null, cancelled, expired)
 - subscription-start 로그 발생시 DB에 연결해서 user테이블에서 해당유저의 subscription_status컬럼의 값이 'active'로 변경해야한다
 - subscription-stop  로그 발생시 DB에 연결해서 user테이블에서 해당유저의 subscription_status컬럼의 값이 'expired'또는 'cancelled' 랜덤으로 변경해야한다


 4. db_type 설정값
 - config.toml의 db_type 값이  "sqlite", "mysql" 둘다 동일하게 변경된 내용을 반영해야한다.