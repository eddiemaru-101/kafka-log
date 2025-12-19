# DB테이블 - DDL
- DB는 목업db, rds(mysql)
- 목업db, rds(mysql)의 스키마는 모두 아래와동일
### Tables

1. **subscription_plans**
2. **tmdb_contents**
3. **tmdb_contents_raw**
4. **user_likes**
5. **user_subscriptions**
6. **users**


1. **subscription_plans**

| subscription_id | subscription_type | subscription_period | price |
| --- | --- | --- | --- |
| s_1 | standard | 1 | 9,900 |
| s_2 | standard | 3 | 26,900 |
| s_3 | standard | 6 | 49,900 |
| s_4 | standard | 12 | 89,900 |
| s_5 | premium | 1 | 14,900 |
| s_6 | premium | 3 | 39,900 |
| s_7 | premium | 6 | 74,900 |
| s_8 | premium | 12 | 134,900 |
| s_9 | family | 1 | 19,900 |
| s_10 | family | 3 | 54,900 |
| s_11 | family | 6 | 99,900 |
| s_12 | family | 12 | 179,900 |
| s_13 | mobile_only | 1 | 5,900 |
| s_14 | mobile_only | 3 | 15,900 |
| s_15 | mobile_only | 6 | 29,900 |
| s_16 | mobile_only | 12 | 53,900 |


```sql
-- ott_service.subscription_plans definition

CREATE TABLE `subscription_plans` (
  `subscription_id` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `subscription_type` varchar(15) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'standard, premium, family, mobile_only',
  `subscription_period` int NOT NULL COMMENT '1, 3, 6, 12 (개월)',
  `price` int NOT NULL COMMENT '단위: 원',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`subscription_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

subscription_id|subscription_type|subscription_period|price |created_at         |updated_at         |
---------------+-----------------+-------------------+------+-------------------+-------------------+
s_1            |standard         |                  1|  9900|2025-12-08 05:58:11|2025-12-08 05:58:11|
s_10           |family           |                  3| 54900|2025-12-08 05:58:11|2025-12-08 05:58:11|
s_11           |family           |                  6| 99900|2025-12-08 05:58:11|2025-12-08 05:58:11|
s_12           |family           |                 12|179900|2025-12-08 05:58:11|2025-12-08 05:58:11|
s_13           |mobile_only      |                  1|  5900|2025-12-08 05:58:11|2025-12-08 05:58:11|
s_14           |mobile_only      |                  3| 15900|2025-12-08 05:58:11|2025-12-08 05:58:11|
s_15           |mobile_only      |                  6| 29900|2025-12-08 05:58:11|2025-12-08 05:58:11|
s_16           |mobile_only      |                 12| 53900|2025-12-08 05:58:11|2025-12-08 05:58:11|
s_2            |standard         |                  3| 26900|2025-12-08 05:58:11|2025-12-08 05:58:11|
s_3            |standard         |                  6| 49900|2025-12-08 05:58:11|2025-12-08 05:58:11|
s_4            |standard         |                 12| 89900|2025-12-08 05:58:11|2025-12-08 05:58:11|
s_5            |premium          |                  1| 14900|2025-12-08 05:58:11|2025-12-08 05:58:11|
s_6            |premium          |                  3| 39900|2025-12-08 05:58:11|2025-12-08 05:58:11|
s_7            |premium          |                  6| 74900|2025-12-08 05:58:11|2025-12-08 05:58:11|
s_8            |premium          |                 12|134900|2025-12-08 05:58:11|2025-12-08 05:58:11|
s_9            |family           |                  1| 19900|2025-12-08 05:58:11|2025-12-08 05:58:11|
```

1. **tmdb_contents**

```sql
-- ott_service.tmdb_contents definition

CREATE TABLE `tmdb_contents` (
  `content_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tmdb_id` int unsigned NOT NULL,
  `content_type` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'movie, tv',
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `release_date` date DEFAULT NULL,
  `release_year` int DEFAULT NULL,
  `genre_names` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `runtime` int DEFAULT NULL COMMENT '영화 러닝타임(분)',
  `episode_runtime` int DEFAULT NULL COMMENT '에피소드 러닝타임(분)',
  `number_of_seasons` int DEFAULT NULL,
  `number_of_episodes` int DEFAULT NULL,
  `popularity` decimal(10,3) DEFAULT NULL,
  `vote_average` decimal(3,1) DEFAULT NULL,
  `director_names` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cast_names` varchar(1000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `collected_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`content_id`),
  KEY `idx_tmdb_id` (`tmdb_id`),
  KEY `idx_content_type` (`content_type`),
  KEY `idx_release_year` (`release_year`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

content_id   |tmdb_id|content_type|title                                                    |release_date|release_year|genre_names            |runtime|episode_runtime|number_of_seasons|number_of_episodes|popularity|vote_average|director_names                            |cast_names                                                                                                  |collected_at       |
-------------+-------+------------+---------------------------------------------------------+------------+------------+-----------------------+-------+---------------+-----------------+------------------+----------+------------+------------------------------------------+------------------------------------------------------------------------------------------------------------+-------------------+
movie_1000012|1000012|movie       |Gangstresses                                             |  2000-02-02|        2000|다큐멘터리                  |     90|               |                 |                  |     1.211|         0.0|Harry A. Davis                            |메리 J. 블리지, Lil' Kim, Deanna Uneek Bennett, Mocha Brown, Toy Connor                                   |2025-12-09 01:32:19|
movie_1000058|1000058|movie       |귀환                                                       |  2023-07-12|        2023|드라마                    |    110|               |                 |                  |     2.197|         6.1|Catherine Corsini                         |Aissatou Diallo Sagna, Esther Gohourou, Suzy Bemba, Lomane de Dietrich, Cédric Appietto                  |2025-12-08 15:46:21|
movie_1000064|1000064|movie       |Fario                                                    |  2024-10-10|        2024|드라마, 코미디               |     90|               |                 |                  |     3.826|         6.3|Lucie Prost                               |Finnegan Oldfield, Florence Loiret Caille, Megan Northam, Andranic Manet, Léna Laurent                  |2025-12-08 16:52:05|
movie_1000073|1000073|movie       |Pour l'honneur                                           |  2023-05-03|        2023|코미디                    |     97|               |                 |                  |     1.256|         6.2|Philippe Guillard                         |Olivier Marchal, Olivia Bonamy, Philippe Duquesne, Mathieu Madénian, Lucie Fagedet                         |2025-12-08 15:52:47|
movie_1000075|1000075|movie       |라르고 윈치: 프라이스 오브 머니                                       |  2024-07-31|        2024|액션, 모험, 스릴러            |    100|               |                 |                  |     3.945|         5.9|Olivier Masset-Depasse                    |토머 시슬리, 제임스 프랭코, Clotilde Hesme, Elise Tilloloy, 데니스 오헤어                         |2025-12-08 16:51:52|
movie_1000079|1000079|movie       |Pourquoi tu souris ?                                     |  2024-07-03|        2024|코미디, 드라마               |     95|               |                 |                  |     1.697|         5.8|Christine Paillard, Chad Chenouga         |Jean-Pascal Zadi, Judith Magre, 엠마누엘 드보스, Raphaël Quenard, Camille Rutherford                       |2025-12-08 16:56:18|
```

1. **tmdb_contents_raw**

```sql

```

1. **user_likes**

```sql
-- ott_service.user_likes definition

CREATE TABLE `user_likes` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `content_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_content` (`user_id`,`content_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_content_id` (`content_id`),
  CONSTRAINT `fk_user_likes_content` FOREIGN KEY (`content_id`) REFERENCES `tmdb_contents_raw` (`content_id`),
  CONSTRAINT `fk_user_likes_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=943408 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

id |user_id|content_id   |created_at         |
---+-------+-------------+-------------------+
  1| 100285|movie_314241 |2021-04-20 00:00:00|
  2| 104732|tv_96262     |2022-07-16 00:00:00|
  3| 104732|movie_1167027|2020-09-25 00:00:00|

```

1. **user_subscriptions**

```sql
-- ott_service.user_subscriptions definition

CREATE TABLE `user_subscriptions` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `subscription_id` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `status` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active' COMMENT 'active, cancelled, expired',
  `auto_renew_flag` tinyint(1) NOT NULL DEFAULT '1' COMMENT '0=미사용, 1=사용',
  `cancel_reserved_flag` tinyint(1) NOT NULL DEFAULT '0' COMMENT '0=미예약, 1=예약',
  `payment_method` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'card, mobile_pay, account_transfer',
  `trial_used_flag` tinyint(1) NOT NULL DEFAULT '0' COMMENT '0=미사용, 1=사용',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_subscription_id` (`subscription_id`),
  KEY `idx_status` (`status`),
  KEY `idx_start_date` (`start_date`),
  CONSTRAINT `fk_user_subscriptions_plan` FOREIGN KEY (`subscription_id`) REFERENCES `subscription_plans` (`subscription_id`),
  CONSTRAINT `fk_user_subscriptions_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=170954 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

id |user_id|subscription_id|start_date|end_date  |status   |auto_renew_flag|cancel_reserved_flag|payment_method  |trial_used_flag|created_at         |updated_at         |
---+-------+---------------+----------+----------+---------+---------------+--------------------+----------------+---------------+-------------------+-------------------+
  1| 100285|s_9            |2024-01-08|2024-02-08|expired  |              0|                   0|card            |              1|2025-12-08 07:35:58|2025-12-08 07:35:58|
  2| 105288|s_4            |2024-04-11|2025-04-11|cancelled|              0|                   0|card            |              1|2025-12-08 07:35:58|2025-12-08 07:35:58|
  3| 107639|s_6            |2021-09-30|2021-12-30|cancelled|              0|                   0|card            |              0|2025-12-08 07:35:58|2025-12-08 07:35:58|
```

1. **users**

```sql
-- ott_service.users definition

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
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_country` (`country`),
  KEY `idx_signup_date` (`signup_date`),
  KEY `idx_account_status` (`account_status`)
) ENGINE=InnoDB AUTO_INCREMENT=200768 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

user_id|email                      |password_hash                                                   |name         |gender|birth_date|country|city     |signup_date|account_status|is_adult_verified|last_login_date    |device_last_used|push_opt_in|created_at         |updated_at         |
-------+---------------------------+----------------------------------------------------------------+-------------+------+----------+-------+---------+-----------+--------------+-----------------+-------------------+----------------+-----------+-------------------+-------------------+
 100001|user1_6078@ottservice.com  |4efabaf882f7ee7b116c0d14722dfc3007a67fd21d45e5a900c8d85efced2d1e|김하윤          |     1|1993-11-15|KR     |제주       | 2023-05-27|active        |                1|2025-12-12 00:00:00|mobile          |          0|2025-12-08 07:11:07|2025-12-12 00:11:08|
 100002|user2_9095@ottservice.com  |b4d4918a2a203a47596898cfcc9f0614cc04a08e920ed06b35235090a8fc787c|최미영          |     1|1981-10-19|KR     |경남       | 2022-11-27|active        |                1|2024-08-08 06:38:35|tablet          |          0|2025-12-08 07:11:07|2025-12-08 07:11:07|
 100003|user3_1535@ottservice.com  |b3316020e1f563c1f005d20e1a30ab05c70b4660f6fe6289dacfae3169844c55|박준혁          |     1|1977-04-20|KR     |부산       | 2020-12-17|deleted       |                1|2025-12-12 00:00:00|mobile          |          0|2025-12-08 07:11:07|2025-12-12 00:15:59|
```