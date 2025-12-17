# 07. log-제너레이터 (코드작성)

상태: 시작 전

목적

- 유저 상태에 따른 로그 발생조건을 준수하는 로그 발생
- MSK- MSK S3 Connect를 통해 저장된 방식과 동일한 로컬에 저장하는 로직 구현
- 한달치 데이터를 생성 - 사용자의 요일별, 시간대별 발생 비율 설정에 따른 로그 발생시간 결정

1. 객체
- UserEventContoller
    - 유저 상태를 기반으로 어떤 로그를 발생시킬지 결정
    - 로그 카테고리 및 타입 결정
    - 결정된 로그 타입에 따라 유저의 상태값을 어떤값으로 업데이트할지 결정한다.
- UserSelector
    - config.toml의 user수 기반으로 로그생성에 사용할 유저를 선정한다.
    - 유저 선정시 상태값을 부여한다.
    - 로그 생성에 따라 UserEventController로 부터 받은 상태값으로 유저별 상태값을 업데이트한다.
- LogContents
    - 로그타입별 로그 내용 생성
    - DB데이터 - DBclient로 받음
    - 로그내용,비율 - config파일 기반으로 입력
    - 로그날짜 - LogDateGenerator를 통해 입력
- DBClient
    - 유저생성시 필요한 유저 정보 호출
    - 로그에 필요한 콘텐츠 정보 호출
    - 로그타입에 따른 유저,콘텐츠,구독상품 구매 정보 업데이트
- DateGenerator
    - 로그발생 시간 정보를 반환
    - config.toml의 생성모드가 batch일경우 설정파일에 입력된 월을 바탕으로 날짜 생성
    - config.toml의 생성모드가 streaming일 경우 현재시간 반환
    - config.toml의 생성모드가 batch일경우 한달치 로그가 생성됨
- LogSink
    - 로그 최종 처리방식 결정
    - config.toml의 생성모드가 batch일경우, config.toml의 sink모드 값에 따라 S3전송 또는 local 저장
    - config.toml의 생성모드가 streaming일 경우 aws kinesis stream으로 전송


1. 기타 설정
- Config파일 - config.toml로 관리
- DBclient 접속 정보는 .env에 넣고 관리한다.
- 로그발생량(mps) 조절가능해야함
- requirements.txt → pyproject.toml로 관리

1. 유저설정
- 유저기반으로 로그가 발생
- 동시접속자수를 가정해서 여러 유저의 로그생성이 비동기로 동시에 발생하도록 작성
- 유저에 활성도 등급 상,중,하를 부여하고 설정한 비율에 의해 유저에 할당되어 로그 생성함
- 활성도 등급에 따라 로그발생건수, 콘텐츠 시청시간이 달라짐

1. 콘텐츠 설정
- 주요 콘텐츠 후보를 기반으로 콘텐츠 정보를 불러와서 로그를 발생시켜야한다.
- 주요 콘텐츠 후보를 config파일에 입력할수있게 해줘.
- 주요콘텐츠 후보는 rds(mysql)의 content_id값으로 설정한다.
- 주요콘텐츠 후보마다  search-search 로그 타입에 사용될 복수개의 검색어를 config파일에 입력할수있게 해줘.

1. LogDateGenerator
- 월단위를 config파일을 통해 변경할수 있어야 한다.
- 요일에 대한 로그발생건수를 config파일을 통해 지정할수 있어야한다.
- 요일별 시간에 따른 로그 발생건수를 config파일을 통해 지정할수 있어야 한다.

1. LogEvents
- 유저 객체에서의 활성도 등급별 로그 발생빈도를 config파일을 통해 지정할수 있어야 한다.
- 유저 객체에서의 활성도 등급별 시청시간이 정해져 있다. 시청시간은 (contents-stop) - (contents-start) 로그 시간을 기준으로 한다. 그러므로 contents-stop 로그 타입의 시간을 결정할때 유저 객체에서의 활성도 등급에 따라 로그 발생시간을 정해야 한다.
- 로그 내용에서 데이터타입에 대한 정의와 관리될수있도록 해줘.
- 메소드는 로그타입명을 기반으로 명명해줘.

1. 로그 발생조건

**사용자 상태별 상태 전이 로직**

event_type = `{category}-{type}`

상태명 = `MAIN_PAGE`, `CONTENT_PAGE`, `IN_START`, `IN_PLAYING`, `IN_PAUSE`, `USER_OUT`

**1. 초기 진입 (User 객체 생성 시)**

**신규 유저**

- 로그: `register-in`
- 동작: DB 신규 유저 생성, is_subscribed=False
- 다음 상태: MAIN_PAGE

**기존 유저**

- 로그: `access-in`
- 동작: DB active 유저 조회, last_login_date 업데이트
- 다음 상태: MAIN_PAGE

**2. MAIN_PAGE 상태 (기존 IDLE)**

**<구독자인 경우>**

**로그아웃**

- 로그: `access-out`
- 다음 상태: USER_OUT

**콘텐츠 클릭**

- 로그: `contents-click`
- 동작: 콘텐츠 조회
- 다음 상태: CONTENT_PAGE

**구독 해지**

- 로그: `subscription-stop`
- 동작: DB 상태 업데이트
- 다음 상태: MAIN_PAGE

**회원 탈퇴**

- 로그: `register-out`
- 동작: DB deleted 상태 업데이트
- 다음 상태: USER_OUT

**검색**

- 로그: `search-search`
- 다음 상태: MAIN_PAGE

**고객 문의**

- 로그: `support-inquiry`
- 다음 상태: MAIN_PAGE

**<비구독자인 경우>**

**구독 시작**

- 로그: `subscription-start`
- 동작: 구독 생성, is_subscribed=True
- 다음 상태: MAIN_PAGE

**콘텐츠 클릭**

- 로그: `contents-click`
- 다음 상태: CONTENT_PAGE

**검색**

- 로그: `search-search`
- 다음 상태: MAIN_PAGE

**회원 탈퇴**

- 로그: `register-out`
- 다음 상태: USER_OUT

**고객 문의**

- 로그: `support-inquiry`
- 다음 상태: MAIN_PAGE

**3. CONTENT_PAGE 상태 (기존 OUT)**

**<구독자인 경우>**

**재생 시작**

- 로그: `contents-start`
- 동작: episode 선택, cur_episode_id 설정
- 다음 상태: IN_START

**좋아요 등록**

- 로그: `contents-like_on`
- 다음 상태: CONTENT_PAGE

**좋아요 취소**

- 로그: `contents-like_off`
- 다음 상태: CONTENT_PAGE

**리뷰 작성**

- 로그: `review-review`
- 다음 상태: CONTENT_PAGE

**뒤로가기 (로그 없음)**

- 다음 상태: MAIN_PAGE

**<비구독자인 경우>**

**좋아요 등록**

- 로그: `contents-like_on`
- 다음 상태: CONTENT_PAGE

**좋아요 취소**

- 로그: `contents-like_off`
- 다음 상태: CONTENT_PAGE

**뒤로가기 (로그 없음)**

- 다음 상태: MAIN_PAGE

**4. IN_START 상태 (재생 시작 직후)**

- 로그 없음
- episode 설정 후
- 다음 상태: IN_PLAYING

**5. IN_PLAYING 상태 (기존 IN_IDLE — 재생 중)**

**시청 중단 + 로그아웃**

- 로그 순서:
    1. `contents-stop`
    2. `access-out`
- 다음 상태: USER_OUT

**일시정지**

- 로그: `contents-pause`
- 다음 상태: IN_PAUSE

**계속 재생 (로그 없음)**

- 다음 상태: IN_PLAYING

**재생 종료**

- 로그: `contents-stop`
- 다음 상태: CONTENT_PAGE


**시청 중단 + 로그아웃**

- 로그 순서:
    1. `contents-stop`
    2. `access-out`
- 다음 상태: USER_OUT

**7. USER_OUT 상태 (기존 NONE)**

- 로그 없음
- 사용자 세션 종료
- User 객체 종료

```

================================================================================
                            로그 타입별 상세 정보
================================================================================

┌─────────────┬──────────┬────────────────────────────────────────────────┐
│ Category    │ Type     │ 필수 데이터                                    │
├─────────────┼──────────┼────────────────────────────────────────────────┤
│ access      │ in       │ platform                                       │
│             │ out      │ platform                                       │
├─────────────┼──────────┼────────────────────────────────────────────────┤
│ contents    │ click    │ platform, contents_id, contents_type           │
│             │          │ + episode_id (if contents_type == "tv")        │
│             │ start    │ platform, contents_id, contents_type           │
│             │          │ + episode_id (if contents_type == "tv")        │
│             │ stop     │ platform, contents_id, contents_type           │
│             │          │ + episode_id (if contents_type == "tv")        │
│             │ pause    │ platform, contents_id, contents_type           │
│             │          │ + episode_id (if contents_type == "tv")        │
│             │ resume   │ platform, contents_id, contents_type           │
│             │          │ + episode_id (if contents_type == "tv")        │
│             │ like_on  │ platform, contents_id, contents_type           │
│             │ like_off │ platform, contents_id, contents_type           │
├─────────────┼──────────┼────────────────────────────────────────────────┤
│ review      │ review   │ contents_id, rating, detail (리뷰 텍스트)      │
├─────────────┼──────────┼────────────────────────────────────────────────┤
│subscription │ start    │ subscription_id                                │
│             │ stop     │ subscription_id                                │
├─────────────┼──────────┼────────────────────────────────────────────────┤
│ register    │ in       │ traffic_source                                 │
│             │ out      │ reason_type, reason_detail                     │
├─────────────┼──────────┼────────────────────────────────────────────────┤
│ search      │ search   │ term (검색어)                                  │
├─────────────┼──────────┼────────────────────────────────────────────────┤
│ support     │ inquiry  │ inquiry_type, inquiry_detail                   │
└─────────────┴──────────┴────────────────────────────────────────────────┘

================================================================================
                            특수 케이스
================================================================================

[2개 로그 동시 발생]
  - IN_IDLE에서 access out 선택 시:
      1. contents stop 로그 먼저 발생
      2. access out 로그 발생

  - IN_PAUSE에서 access out 선택 시:
      1. contents stop 로그 먼저 발생
      2. access out 로그 발생

[DB 연동 필수 케이스]
  - register in: 신규 유저 생성
  - register out: 유저 상태 deleted로 변경
  - subscription start: 신규 구독 생성
  - subscription stop: 구독 취소
  - contents click: 랜덤 콘텐츠 조회
  - access in: 기존 유저 조회, last_login_date 업데이트
```

1. 로그 포맷,타입

| 분류 | 분류 코드(event_category) | 이벤트 이름 | 이벤트 코드(event_type) | 필요 정보(detail) |
| --- | --- | --- | --- | --- |
| 접속 | `access` / 1 | 로그인 | `in` / 1 | user_id, platform, timestamp |
|  |  | 로그아웃 | `out` / 2 | user_id, platform, timestamp |
| 콘텐츠 | `contents` / 2 | 콘텐츠 클릭 | `click` / 3 | user_id, contents_id, contents_type, platform, timestamp |
|  |  | 콘텐츠 재생 | `start` / 4 | user_id, contents_id, contents_type, episode_id, ~~progress_time,~~ platform, timestamp |
|  |  | 콘텐츠 중지 | `stop` / 5 | user_id, contents_id, contents_type, episode_id, ~~progress_time,~~ platform, timestamp |
|  |  | 콘텐츠 일시정지 | `pause` / 6 | user_id, contents_id, contents_type, episode_id, ~~progress_time,~~ platform, timestamp |
|  |  | 콘텐츠 재시작 | `resume` / 7 | user_id, contents_id, contents_type, episode_id, ~~progress_time,~~ platform, timestamp |
|  |  | 콘텐츠 좋아요 | `like_on` / 8 | user_id, contents_id, contents_type, timestamp |
|  |  | 콘텐츠 좋아요 취소 | `like_off` /9 | user_id, contents_id, contents_type, timestamp |
| 리뷰 | `review` / 3 | 콘텐츠 리뷰 작성 | `review` / 10 | user_id, contents_id, rating, review_detail, timestamp |
| 구독 | `subscription`  / 4 | 유료 구독 결제 | `start` / 4 | user_id, subscription_id, timestamp |
|  |  | 유료 구독 해지 | `stop` / 5 | user_id, subscription_id, timestamp |

| 회원 | `register` / 5 | 회원 가입 | `in` / 1 | user_id, traffic_source, timestamp |
|  |  | 회원 탈퇴 | `out` / 2 | user_id, reason_type, reason_detail, timestamp |
| 검색 | `search` / 6 | 콘텐츠 검색 | `search` / 11 | user_id, term, timestamp |
| 고객센터 | `support` / 7 | 문의 | `inquiry` / 12 | user_id, inquiry_type, inquiry_detail, timestamp |

| 항목 | 내용 | 데이터 타입 | 예시 | Options |
| --- | --- | --- | --- | --- |
| timestamp | 이벤트 발생 시간 | TIMESTAMP | YYYY-MM-DD HH:MM:SS | - |
| user_id | 유저 ID | VARCHAR(50) | user_1234 | *유저 테이블 참고 |
| event_category | 이벤트 분류 | TINYINT | 1 | • 1: access• 2: contents• 3: review• 4: subscription• 5: register• 6: search• 7: support |
| event_type | 이벤트 속성 | TINYINT | 1 | • 1: in• 2: out• 3: click• 4: start• 5: stop• 6: pause• 7: resume• 8: like_on• 9: like_off• 10: review• 11: search• 12: inquiry |
| platform | 접속 환경 | TINYINT | android | • 1: android• 2: ios• 3: pc• 4: tv |
| contents_id | 콘텐츠 ID | VARCHAR(50) | contents_1234 | *콘텐츠 테이블 참고 |
| contents_type | 콘텐츠 유형 | TINYINT | 1 | • 1: series - 시리즈 물• 2: single - 단편 |
| episode_id | 에피소드 ID | VARCHAR(50)NULLABLE | episode_1234 | *콘텐츠 테이블 참고 |
| progress_time | 콘텐츠 시청 시간 | VARCHAR(50) | mm:ss | - |
| rating | 리뷰 평점 | FLOAT | 3.5 | 평점 범위 (0~5, 0.5 단위)0.5 단위 외의 숫자 들어올 경우 round |
| review_detail | 리뷰 내용 | VARCHAR(255), NULLABLE | “재밌어요” | - |
| subscription_id | 구독 상품 ID | VARCHAR(50) | subs_1 | *구독 테이블 참고 |
| traffic_source | 유입 경로 | TINYINTNULLABLE | 1 | • 1: search - 검색• 2: social - SNS• 3: ad_searc - 포털 사이트 광고• 4: ad_social - SNS 광고• 5: referral - 추천• 6: misc - 기타 |
| reason_type | 탈퇴 이유 타입 | VARCHAR(10) | 1 | • 1: contents - 콘텐츠 관련 불만• 2: charge - 요금 관련 불만• 3: misc - 기타 |
| reason_detail | 탈퇴 이유 상세 | VARCHAR(255), NULLABLE | “너무 비싸요” | - |
| term | 검색어 | VARCHAR(255), NULLABLE | “해리포터” | - |
| inquiry_type | 문의 타입 | TINYINT | 1 | • 1: contents - 콘텐츠 관련 문의• 2: refund - 환불, 결제 관련 문의• 3: subscription - 구독 관련 문의• 4: information - 회원 정보 관련 문의 |
| inquiry_detail | 문의 내용 | VARCHAR(255) | “25일 쓴 이용권 환불 가능?” | - |

1. LogSink 설정
- 3가지 케이스 각각 생성해야함
    - S3에 저장
    - 로컬 특정 폴더에 저장
    - kafka로 전송
- 로그 전송속도(mps설정)
    - **config.toml에 mps 값 넣고, LogSink 초기화 시 읽어서 interval 계산**
    
    **구조**
    
    - `config.toml` → mps 값 정의
    - `LogSink.__init__()` → config 읽어서 `self.interval = 1.0 / mps` 계산
    - `LogSink.send()` → 매 전송 후 `time.sleep(self.interval)`
- 저장방식(S3,로컬)
    
    목적:
    설정값 기반으로 MSK S3 Sink Connector와 동일한 폴더 구조/파일명 생성
    
    저장 위치:
    
    1. 로컬 (개발/테스트용)
    2. S3 (운영용) - s3://sesac-l1/raw-userlog/
    
    폴더 구조:
    {output_dir}/{topic}/year={YYYY}/month={MM}/day={DD}/hour={HH}/
    
    파일명:
    {topic}+{partition}+{offset(10자리 zero-padding)}.json
    
    예시:
    ./output/user-logs/year=2025/month=01/day=15/hour=14/user-logs+0+0000000000.json
    
- kafka로 보내는 producer.py는 일단 holding (급한게 아니라서)
    
    
1. rds(mysql) 테이블스키마 

### **필수 테이블**

1. ✅ **users** - 유저 정보 CRUD

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
) ENGINE=InnoDB AUTO_INCREMENT=200066 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

user_id|email                      |password_hash                                                   |name          |gender|birth_date|country|city       |signup_date|account_status|is_adult_verified|last_login_date    |device_last_used|push_opt_in|created_at         |updated_at         |
-------+---------------------------+----------------------------------------------------------------+--------------+------+----------+-------+-----------+-----------+--------------+-----------------+-------------------+----------------+-----------+-------------------+-------------------+
 100001|user1_6078@ottservice.com  |4efabaf882f7ee7b116c0d14722dfc3007a67fd21d45e5a900c8d85efced2d1e|김하윤           |     1|1993-11-15|KR     |제주         | 2023-05-27|active        |                1|2023-12-08 10:50:42|mobile          |          0|2025-12-08 07:11:07|2025-12-08 07:11:07|
 100002|user2_9095@ottservice.com  |b4d4918a2a203a47596898cfcc9f0614cc04a08e920ed06b35235090a8fc787c|최미영           |     1|1981-10-19|KR     |경남         | 2022-11-27|active        |                1|2024-08-08 06:38:35|tablet          |          0|2025-12-08 07:11:07|2025-12-08 07:11:07|
 100003|user3_1535@ottservice.com  |b3316020e1f563c1f005d20e1a30ab05c70b4660f6fe6289dacfae3169844c55|박준혁           |     1|1977-04-20|KR     |부산         | 2020-12-17|active        |                1|2021-02-12 13:40:50|mobile          |          0|2025-12-08 07:11:07|2025-12-08 07:11:07|
 100004|user4_4078@ottservice.com  |101b66c70c508b52fdfdb07667b20dcece8912e274ce89cb5f2ab6f8bae006b6|배승민           |     0|2004-02-14|KR     |전남         | 2020-08-23|deleted       |                1|2023-12-19 02:08:11|mobile          |          1|2025-12-08 07:11:07|2025-12-08 07:11:07|
 100005|user5_9046@ottservice.com  |0e1cdb7f1c45a6cde5135008149bb5d31af08a1fdf963a08ab6595e2a906626f|김성진           |     0|1988-04-15|KR     |경기         | 2023-09-08|active        |                1|2024-04-11 14:50:31|tablet          |          0|2025-12-08 07:11:07|2025-12-08 07:11:07|
 100006|user6_4142@ottservice.com  |32d26b744e80b322cdc23741b419877a8d97e806148fe3021575ec0af6db07b6|김은정           |     0|1972-08-20|KR     |부산         | 2024-08-13|suspended     |                1|2025-03-25 01:15:23|tv              |          0|2025-12-08 07:11:07|2025-12-08 07:11:07|
 100007|user7_1914@ottservice.com  |edae4cdc3ec917309fcef1f77267b0b7af625881525d779ed8746ae141b4e5e5|김정훈           |     0|1964-02-22|KR     |경기         | 2020-07-05|active        |                1|2023-06-08 16:11:21|tablet          |          0|2025-12-08 07:11:07|2025-12-08 07:11:07|
 100008|user8_1254@ottservice.com  |67a82ebdffcd1abb7d16457139451d42f2a91ebe7bc1d08a4ed98fc4517741a3|김동현           |     1|1985-06-20|KR     |울산         | 2024-08-08|active        |                1|2025-07-31 22:22:01|tv              |          1|2025-12-08 07:11:07|2025-12-08 07:11:07|
```

1. ✅ **user_subscriptions** - 구독 정보 CRUD
    
    ```sql
    -- ott_service.subscription_plans definition
    
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
    ) ENGINE=InnoDB AUTO_INCREMENT=162963 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    
    id |user_id|subscription_id|start_date|end_date  |status   |auto_renew_flag|cancel_reserved_flag|payment_method  |trial_used_flag|created_at         |updated_at         |
    ---+-------+---------------+----------+----------+---------+---------------+--------------------+----------------+---------------+-------------------+-------------------+
      1| 100285|s_9            |2024-01-08|2024-02-08|expired  |              0|                   0|card            |              1|2025-12-08 07:35:58|2025-12-08 07:35:58|
      2| 105288|s_4            |2024-04-11|2025-04-11|cancelled|              0|                   0|card            |              1|2025-12-08 07:35:58|2025-12-08 07:35:58|
      3| 107639|s_6            |2021-09-30|2021-12-30|cancelled|              0|                   0|card            |              0|2025-12-08 07:35:58|2025-12-08 07:35:58|
      4| 107639|s_13           |2022-07-29|2022-08-29|cancelled|              0|                   0|card            |              0|2025-12-08 07:35:58|2025-12-08 07:35:58|
      5| 107639|s_4            |2025-11-23|2026-11-23|active   |              1|                   0|account_transfer|              0|2025-12-08 07:35:58|2025-12-08 07:35:58|
      6| 119552|s_6            |2021-02-01|2021-05-01|expired  |              0|                   0|mobile_pay      |              0|2025-12-08 07:35:58|2025-12-08 07:35:58|
      7| 119552|s_15           |2025-06-19|2025-12-19|active   |              1|                   0|mobile_pay      |              0|2025-12-08 07:35:58|2025-12-08 07:35:58|
      8| 126240|s_4            |2021-02-12|2022-02-12|expired  |              0|                   0|card            |              1|2025-12-08 07:35:58|2025-12-08 07:35:58|
      9| 126240|s_7            |2022-01-15|2022-07-15|cancelled|              0|                   0|card            |              0|2025-12-08 07:35:58|2025-12-08 07:35:58|
    ```
    
2. ✅ **tmdb_contents** - 콘텐츠 정보 READ
    
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
    
    content_id   |tmdb_id|content_type|title                                                                                   |release_date|release_year|genre_names                                     |runtime|episode_runtime|number_of_seasons|number_of_episodes|popularity|vote_average|director_names                                  |cast_names                                                                                                         |collected_at       |
    -------------+-------+------------+----------------------------------------------------------------------------------------+------------+------------+------------------------------------------------+-------+---------------+-----------------+------------------+----------+------------+------------------------------------------------+-------------------------------------------------------------------------------------------------------------------+-------------------+
    tv_66732     |  66732|tv          |기묘한 이야기                                                                                 |  2016-07-15|        2016|Sci-Fi & Fantasy, 미스터리, Action & Adventure      |       |               |                5|                42|   925.818|         8.6|로스 더퍼, 맷 더퍼                                     |밀리 바비 브라운, 위노나 라이더, 데이비드 하버, 핀 울프하드, 게이튼 매터래조                                                                      |2025-12-08 13:48:12|
    movie_533533 | 533533|movie       |트론: 아레스                                                                                 |  2025-10-08|        2025|SF, 모험, 액션                                      |    119|               |                 |                  |   533.218|         6.5|요아킴 뢴닝                                          |자레드 레토, 그레타 리, 에반 피터스, 질리언 앤더슨, 조디 터너스미스                                                                           |2025-12-08 17:36:49|
    movie_1180831|1180831|movie       |트롤의 습격 2                                                                                |  2025-11-30|        2025|액션, 판타지, 스릴러                                    |    105|               |                 |                  |   530.183|         6.8|로아르 우테우                                         |Ine Marie Wilmann, Kim S. Falck-Jørgensen, Mads Sjøgård Pettersen, Sara Khorami, Karoline Viktoria Sletteng Garvang|2025-12-08 17:36:49|
    movie_1084242|1084242|movie       |주토피아 2                                                                                  |  2025-11-26|        2025|애니메이션, 코미디, 모험, 가족, 미스터리                        |    108|               |                 |                  |   463.280|         7.7|재러드 부시, 바이런 하워드                                 |지니퍼 굿윈, 제이슨 베이트먼, 키호이콴, 포춘 페임스터, 앤디 샘버그                                                                            |2025-12-08 17:36:49|
    movie_1228246|1228246|movie       |프레디의 피자가게 2                                                                             |  2025-12-03|        2025|공포, 스릴러, 가족                                     |    104|               |                 |                  |   312.723|         6.4|Emma Tammi                                      |조쉬 허처슨, Piper Rubio, 엘리자베스 레일, 매튜 릴라드, Freddy Carter                                                               |2025-12-08 17:36:49|
    tv_210318    | 210318|tv          |The Boys from Brazil: Rise of the Bolsonaros                                            |  2022-09-05|        2022|다큐멘터리                                           |       |               |                1|                 3|   291.035|         7.0|                                                |                                                                                                                   |2025-12-08 15:03:00|
    tv_200875    | 200875|tv          |그것: 웰컴 투 데리                                                                             |  2025-10-26|        2025|드라마, 미스터리                                       |       |               |                1|                 8|   284.646|         8.2|앤디 무시에티, 바바라 무시에티, 제이슨 푹스                       |테일러 페이지, 조반 아데포, Matilda Lawler, Amanda Christine, Clara Stack                                                     |2025-12-08 17:56:46|
    ```
    

