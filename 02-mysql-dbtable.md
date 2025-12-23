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

content_id   |tmdb_id|content_type|title                                                                                   |release_date|release_year|genre_names                                     |runtime|episode_runtime|number_of_seasons|number_of_episodes|popularity|vote_average|director_names                                  |cast_names                                                                                                         |collected_at       |updated_at         |
-------------+-------+------------+----------------------------------------------------------------------------------------+------------+------------+------------------------------------------------+-------+---------------+-----------------+------------------+----------+------------+------------------------------------------------+-------------------------------------------------------------------------------------------------------------------+-------------------+-------------------+
movie_533533 | 533533|movie       |트론: 아레스                                                                                 |  2025-10-08|        2025|SF, 모험, 액션                                      |    119|               |                 |                  |   533.218|         6.5|요아킴 뢴닝                                          |자레드 레토, 그레타 리, 에반 피터스, 질리언 앤더슨, 조디 터너스미스                                                                           |2025-12-08 17:36:49|2025-12-17 06:08:28|
movie_1180831|1180831|movie       |트롤의 습격 2                                                                                |  2025-11-30|        2025|액션, 판타지, 스릴러                                    |    105|               |                 |                  |   530.183|         6.8|로아르 우테우                                         |Ine Marie Wilmann, Kim S. Falck-Jørgensen, Mads Sjøgård Pettersen, Sara Khorami, Karoline Viktoria Sletteng Garvang|2025-12-08 17:36:49|2025-12-17 06:08:28|
tv_66732     |  66732|tv          |기묘한 이야기                                                                                 |  2016-07-15|        2016|Sci-Fi & Fantasy, 미스터리, Action & Adventure      |       |               |                5|                42|   529.501|         8.6|로스 더퍼, 맷 더퍼                                     |밀리 바비 브라운, 위노나 라이더, 데이비드 하버, 핀 울프하드, 게이튼 매터래조                                                                      |2025-12-08 13:48:12|2025-12-19 21:02:29|
movie_425274 | 425274|movie       |나우 유 씨 미 3                                                                              |  2025-11-12|        2025|스릴러, 범죄, 미스터리                                   |    112|               |                 |                  |   470.612|         6.4|루벤 플레셔                                          |제시 아이젠버그, 도미닉 세사, 아리아나 그린블랫, 저스티스 스미스, 로저먼드 파이크                                                                    |2025-12-08 17:36:49|2025-12-19 21:01:13|
movie_1084242|1084242|movie       |주토피아 2                                                                                  |  2025-11-26|        2025|애니메이션, 코미디, 모험, 가족, 미스터리                        |    108|               |                 |                  |   463.280|         7.7|재러드 부시, 바이런 하워드                                 |지니퍼 굿윈, 제이슨 베이트먼, 키호이콴, 포춘 페임스터, 앤디 샘버그                                                                            |2025-12-08 17:36:49|2025-12-17 06:08:28|
tv_200875    | 200875|tv          |그것: 웰컴 투 데리                                                                             |  2025-10-26|        2025|드라마, 미스터리                                       |       |               |                1|                 8|   428.060|         8.3|앤디 무시에티, 바바라 무시에티, 제이슨 푹스                       |테일러 페이지, 조반 아데포, Matilda Lawler, Amanda Christine, Clara Stack                                                     |2025-12-08 17:56:46|2025-12-21 21:02:49|
movie_1228246|1228246|movie       |프레디의 피자가게 2                                                                             |  2025-12-03|        2025|공포, 스릴러, 가족                                     |    104|               |                 |                  |   312.723|         6.4|Emma Tammi                                      |조쉬 허처슨, Piper Rubio, 엘리자베스 레일, 매튜 릴라드, Freddy Carter                                                               |2025-12-08 17:36:49|2025-12-17 06:08:28|
tv_210318    | 210318|tv          |The Boys from Brazil: Rise of the Bolsonaros                                            |  2022-09-05|        2022|다큐멘터리                                           |       |               |                1|                 3|   291.035|         7.0|                                                |                                                                                                                   |2025-12-08 15:03:00|2025-12-17 06:08:28|
movie_1246049|1246049|movie       |드라큘라: 어 러브 테일                                                                           |  2025-07-30|        2025|공포, 판타지, 로맨스                                    |    130|               |                 |                  |   211.550|         7.1|뤽 베송                                            |케일럽 랜드리 존스, Zoë Bleu Sidel, 크리스토프 발츠, Matilda De Angelis, Ewens Abid                                               |2025-12-08 17:36:49|2025-12-17 06:08:28|
movie_1419406|1419406|movie       |포풍추영                                                                                    |  2025-08-16|        2025|액션, 범죄, 스릴러                                     |    142|               |                 |                  |   195.111|         6.5|Larry Yang                                      |성룡, 张子枫, 양가휘, 차사, 준                                                                                                |2025-12-08 17:36:49|2025-12-17 06:08:28|
movie_1448560|1448560|movie       |Wildcat                                                                                 |  2025-11-19|        2025|액션, 스릴러, 범죄                                     |     99|               |                 |                  |   193.332|         5.8|James Nunn                                      |케이트 베킨세일, 루이스 탠, Alice Krige, 찰스 댄스, Rasmus Hardiker                                                               |2025-12-08 17:36:49|2025-12-17 06:08:28|
tv_106379    | 106379|tv          |폴아웃                                                                                     |  2024-04-10|        2024|Action & Adventure, 드라마, Sci-Fi & Fantasy       |       |               |                2|                16|   192.375|         8.2|그레이엄 와그너, 제니바 로버트슨드워렛                           |엘라 퍼넬, 에런 모튼, 모이세스 아리아스, 월튼 고긴스, Frances Turner                                                                    |2025-12-08 17:16:35|2025-12-19 21:03:15|
movie_1242898|1242898|movie       |프레데터: 죽음의 땅                                                                             |  2025-11-05|        2025|액션, SF, 모험                                      |    107|               |                 |                  |   191.975|         7.4|댄 트랙턴버그                                         |엘르 패닝, Dimitrius Schuster-Koloamatangi, Ravi Narayan, Michael Homick, Stefan Grube                                 |2025-12-08 17:36:49|2025-12-17 06:08:28|
tv_240459    | 240459|tv          |스파르타쿠스: 하우스 오브 아슈르                                                                      |  2025-12-05|        2025|드라마, Action & Adventure                         |       |               |                1|                10|   191.137|         5.7|Steven S. DeKnight                              |Nick E. Tarabay, Graham McTavish, Tenika Davis, Jamaica Vaughan, Ivana Baquero                                     |2025-12-08 17:56:46|2025-12-17 06:08:28|
movie_949709 | 949709|movie       |하이포스                                                                                    |  2024-09-29|        2024|액션, 범죄                                          |    115|               |                 |                  |   181.051|         5.9|彭順                                              |유덕화, 张子枫, 屈楚萧, 류타오, 곽효동                                                                                            |2025-12-08 16:50:30|2025-12-17 06:08:28|
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