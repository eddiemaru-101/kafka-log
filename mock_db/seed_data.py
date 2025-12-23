"""
SQLite Mock DB 생성 스크립트
실제 MySQL 스키마를 기반으로 테스트용 SQLite DB 생성
"""

import sqlite3
import random
from datetime import datetime, timedelta, date
from pathlib import Path
import hashlib

# ==================== 설정 ====================
DB_PATH = "./ott_test.db"
USER_COUNT = 200000  # 유저 20만명
CONTENT_COUNT = 200
SUBSCRIPTION_COUNT = 200000  # 구독 20만개 (유저당 최대 1개씩 active 가능)
USER_LIKES_COUNT = 150

# ==================== DB 연결 ====================
#Path("./mock_db").mkdir(exist_ok=True)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 60)
print("🚀 SQLite Mock DB 생성 시작")
print("=" * 60)

# ==================== 테이블 생성 ====================
print("\n📋 테이블 생성 중...")

# 1. subscription_plans 테이블
cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscription_plans (
        subscription_id TEXT PRIMARY KEY,
        subscription_type TEXT NOT NULL,
        subscription_period INTEGER NOT NULL,
        price INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
""")

# 2. tmdb_contents 테이블
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tmdb_contents (
        content_id TEXT PRIMARY KEY,
        tmdb_id INTEGER NOT NULL,
        content_type TEXT NOT NULL,
        title TEXT NOT NULL,
        release_date TEXT,
        release_year INTEGER,
        genre_names TEXT,
        runtime INTEGER,
        episode_runtime INTEGER,
        number_of_seasons INTEGER,
        number_of_episodes INTEGER,
        popularity REAL,
        vote_average REAL,
        director_names TEXT,
        cast_names TEXT,
        collected_at TEXT NOT NULL
    )
""")

# 인덱스 생성
cursor.execute("CREATE INDEX IF NOT EXISTS idx_tmdb_id ON tmdb_contents(tmdb_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_type ON tmdb_contents(content_type)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_release_year ON tmdb_contents(release_year)")

# 3. users 테이블
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        gender INTEGER NOT NULL,
        birth_date TEXT NOT NULL,
        country TEXT NOT NULL DEFAULT 'KR',
        city TEXT NOT NULL,
        signup_date TEXT NOT NULL,
        account_status TEXT NOT NULL DEFAULT 'active',
        is_adult_verified INTEGER NOT NULL DEFAULT 0,
        last_login_date TEXT,
        device_last_used TEXT,
        push_opt_in INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
""")

# 인덱스 생성
cursor.execute("CREATE INDEX IF NOT EXISTS idx_country ON users(country)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_signup_date ON users(signup_date)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_account_status ON users(account_status)")

# 4. user_subscriptions 테이블
cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subscription_id TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        auto_renew_flag INTEGER NOT NULL DEFAULT 1,
        cancel_reserved_flag INTEGER NOT NULL DEFAULT 0,
        payment_method TEXT NOT NULL,
        trial_used_flag INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (subscription_id) REFERENCES subscription_plans(subscription_id)
    )
""")

# 인덱스 생성
cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON user_subscriptions(user_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscription_id ON user_subscriptions(subscription_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON user_subscriptions(status)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_start_date ON user_subscriptions(start_date)")

# 5. user_likes 테이블
cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (content_id) REFERENCES tmdb_contents(content_id),
        UNIQUE(user_id, content_id)
    )
""")

# 인덱스 생성
cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_likes_user_id ON user_likes(user_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_likes_content_id ON user_likes(content_id)")

print("✅ 테이블 생성 완료")

# ==================== 데이터 삽입 ====================
print("\n📦 데이터 삽입 중...")

# 1. subscription_plans 데이터 삽입 (실제 MySQL 데이터 기반)
subscription_plans_data = [
    ('s_1', 'standard', 1, 9900),
    ('s_2', 'standard', 3, 26900),
    ('s_3', 'standard', 6, 49900),
    ('s_4', 'standard', 12, 89900),
    ('s_5', 'premium', 1, 14900),
    ('s_6', 'premium', 3, 39900),
    ('s_7', 'premium', 6, 74900),
    ('s_8', 'premium', 12, 134900),
    ('s_9', 'family', 1, 19900),
    ('s_10', 'family', 3, 54900),
    ('s_11', 'family', 6, 99900),
    ('s_12', 'family', 12, 179900),
    ('s_13', 'mobile_only', 1, 5900),
    ('s_14', 'mobile_only', 3, 15900),
    ('s_15', 'mobile_only', 6, 29900),
    ('s_16', 'mobile_only', 12, 53900),
]

now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
for sub_id, sub_type, period, price in subscription_plans_data:
    cursor.execute("""
        INSERT INTO subscription_plans 
        (subscription_id, subscription_type, subscription_period, price, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (sub_id, sub_type, period, price, now, now))

print(f"✅ subscription_plans: {len(subscription_plans_data)}개 삽입")

# 2. tmdb_contents 데이터 삽입
genres_list = [
    "액션", "모험", "애니메이션", "코미디", "범죄", "다큐멘터리",
    "드라마", "가족", "판타지", "역사", "공포", "음악",
    "미스터리", "로맨스", "SF", "TV 영화", "스릴러", "전쟁", "서부"
]

movie_titles = [
    "어벤져스", "타이타닉", "인셉션", "다크 나이트", "포레스트 검프", 
    "매트릭스", "인터스텔라", "글래디에이터", "레옹", "쇼생크 탈출",
    "시민 케인", "대부", "펄프 픽션", "반지의 제왕", "스타워즈",
    "기생충", "올드보이", "마더", "살인의 추억", "부산행"
]

tv_titles = [
    "브레이킹 배드", "왕좌의 게임", "스트레인저 씽즈", "더 크라운", "오징어 게임",
    "종이의 집", "더 맨달로리안", "위쳐", "블랙 미러", "프렌즈",
    "오피스", "빅뱅 이론", "슈츠", "지옥", "킹덤"
]

korean_names = ["김민준", "이서준", "박도윤", "최예준", "정시우", "강지호", "윤준서", "장우진", "임수현", "한지민"]

for i in range(1, CONTENT_COUNT + 1):
    is_movie = random.random() < 0.6  # 60% 영화, 40% TV
    
    if is_movie:
        content_type = "movie"
        title = random.choice(movie_titles) + f" ({i})"
        runtime = random.randint(80, 180)
        episode_runtime = None
        number_of_seasons = None
        number_of_episodes = None
    else:
        content_type = "tv"
        title = random.choice(tv_titles) + f" ({i})"
        runtime = None
        episode_runtime = random.randint(30, 70)
        number_of_seasons = random.randint(1, 3)
        number_of_episodes = random.randint(1, 10)
    
    tmdb_id = 100000 + i
    content_id = f"{content_type}_{tmdb_id}"
    release_year = random.randint(2015, 2024)
    release_date = f"{release_year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
    
    selected_genres = random.sample(genres_list, k=random.randint(1, 3))
    genre_names = ", ".join(selected_genres)
    
    popularity = round(random.uniform(0.5, 100.0), 3)
    vote_average = round(random.uniform(5.0, 9.5), 1)
    
    director_names = ", ".join(random.sample(korean_names, k=random.randint(1, 2)))
    cast_names = ", ".join(random.sample(korean_names, k=random.randint(3, 7)))
    
    collected_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute("""
        INSERT INTO tmdb_contents (
            content_id, tmdb_id, content_type, title, release_date, release_year,
            genre_names, runtime, episode_runtime, number_of_seasons, number_of_episodes,
            popularity, vote_average, director_names, cast_names, collected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        content_id, tmdb_id, content_type, title, release_date, release_year,
        genre_names, runtime, episode_runtime, number_of_seasons, number_of_episodes,
        popularity, vote_average, director_names, cast_names, collected_at
    ))

print(f"✅ tmdb_contents: {CONTENT_COUNT}개 삽입")

# 3. users 데이터 삽입
korean_surnames = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임"]
korean_given_names = ["민준", "서준", "도윤", "예준", "시우", "지호", "준서", "우진", "수현", "지민",
                       "서연", "민서", "지우", "서윤", "지유", "채원", "하은", "예은", "수아", "윤서"]
korean_cities = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원", 
                 "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
devices = ["mobile", "tablet", "desktop", "tv", "console"]

for i in range(1, USER_COUNT + 1):
    email = f"user{i}_{random.randint(1000, 9999)}@ottservice.com"
    
    # 간단한 해시 (실제로는 bcrypt 등을 사용)
    password_hash = hashlib.sha256(f"password{i}".encode()).hexdigest()
    
    name = random.choice(korean_surnames) + random.choice(korean_given_names)
    gender = random.randint(0, 2)  # 0=남, 1=여, 2=기타
    
    birth_year = random.randint(1960, 2005)
    birth_date = date(birth_year, random.randint(1, 12), random.randint(1, 28))
    
    country = "KR"
    city = random.choice(korean_cities)
    
    signup_year = random.randint(2020, 2024)
    signup_date = date(signup_year, random.randint(1, 12), random.randint(1, 28))
    
    account_status = random.choices(
        ["active", "suspended", "deleted"],
        weights=[85, 5, 10]
    )[0]
    
    is_adult_verified = 1 if (datetime.now().year - birth_year) >= 19 else 0
    
    last_login_date = None
    if account_status == "active" and random.random() < 0.8:
        days_ago = random.randint(0, 30)
        last_login_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
    
    device_last_used = random.choice(devices) if last_login_date else None
    push_opt_in = random.choices([0, 1], weights=[30, 70])[0]
    
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    updated_at = last_login_date if last_login_date else created_at
    
    cursor.execute("""
        INSERT INTO users (
            email, password_hash, name, gender, birth_date, country, city,
            signup_date, account_status, is_adult_verified, last_login_date,
            device_last_used, push_opt_in, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        email, password_hash, name, gender, birth_date.isoformat(), country, city,
        signup_date.isoformat(), account_status, is_adult_verified, last_login_date,
        device_last_used, push_opt_in, created_at, updated_at
    ))

print(f"✅ users: {USER_COUNT}개 삽입")

# 4. user_subscriptions 데이터 삽입
payment_methods = ["card", "mobile_pay", "account_transfer"]
subscription_statuses = ["active", "cancelled", "expired"]

# active 유저만 구독 생성
cursor.execute("SELECT user_id FROM users WHERE account_status = 'active'")
active_users = [row[0] for row in cursor.fetchall()]

subscription_ids = [f"s_{i}" for i in range(1, 17)]

# active 유저의 90%가 active 구독을 가지도록 설정
target_active_subscribers = int(len(active_users) * 0.90)
subscription_count = 0

print(f"  - 목표: {len(active_users)}명 중 {target_active_subscribers}명이 active 구독자 (90%)")

for user_id in random.sample(active_users, target_active_subscribers):
    subscription_id = random.choice(subscription_ids)

    # 구독 시작일: 2025-01-01 (로그 생성 시작일 이전)
    start_date = datetime(2025, 1, 1).date()

    # 구독 기간 (subscription_id에서 추출)
    cursor.execute("SELECT subscription_period FROM subscription_plans WHERE subscription_id = ?", (subscription_id,))
    period_months = cursor.fetchone()[0]
    end_date = start_date + timedelta(days=period_months * 30)

    # 90%는 active 상태로 생성
    status = "active"
    auto_renew_flag = 1
    cancel_reserved_flag = 0
    payment_method = random.choice(payment_methods)
    trial_used_flag = random.choices([0, 1], weights=[60, 40])[0]

    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    updated_at = created_at

    cursor.execute("""
        INSERT INTO user_subscriptions (
            user_id, subscription_id, start_date, end_date, status,
            auto_renew_flag, cancel_reserved_flag, payment_method, trial_used_flag,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, subscription_id, start_date.isoformat(), end_date.isoformat(), status,
        auto_renew_flag, cancel_reserved_flag, payment_method, trial_used_flag,
        created_at, updated_at
    ))

    subscription_count += 1

    if subscription_count % 10000 == 0:
        print(f"  - 진행: {subscription_count:,}/{target_active_subscribers:,}...")
        conn.commit()

print(f"✅ user_subscriptions: {subscription_count}개 삽입 (active 구독자 비율: 90%)")

# 5. user_likes 데이터 삽입
cursor.execute("SELECT content_id FROM tmdb_contents")
all_content_ids = [row[0] for row in cursor.fetchall()]

for _ in range(USER_LIKES_COUNT):
    user_id = random.choice(active_users)
    content_id = random.choice(all_content_ids)
    
    # 과거 랜덤 날짜
    days_ago = random.randint(0, 730)  # 2년 이내
    created_at = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        cursor.execute("""
            INSERT INTO user_likes (user_id, content_id, created_at)
            VALUES (?, ?, ?)
        """, (user_id, content_id, created_at))
    except sqlite3.IntegrityError:
        # UNIQUE 제약 위반 시 스킵
        pass

print(f"✅ user_likes: 최대 {USER_LIKES_COUNT}개 삽입 (중복 제외)")

# ==================== 커밋 및 종료 ====================
conn.commit()
conn.close()

print("\n" + "=" * 60)
print("✅ Mock DB 생성 완료!")
print(f"📁 파일 위치: {DB_PATH}")
print("=" * 60)

# ==================== 검증 ====================
print("\n🔍 데이터 검증 중...")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM subscription_plans")
print(f"  - subscription_plans: {cursor.fetchone()[0]}개")

cursor.execute("SELECT COUNT(*) FROM tmdb_contents")
print(f"  - tmdb_contents: {cursor.fetchone()[0]}개")

cursor.execute("SELECT COUNT(*) FROM users WHERE account_status = 'active'")
print(f"  - active users: {cursor.fetchone()[0]}개")

cursor.execute("SELECT COUNT(*) FROM user_subscriptions WHERE status = 'active'")
print(f"  - active subscriptions: {cursor.fetchone()[0]}개")

cursor.execute("SELECT COUNT(*) FROM user_likes")
print(f"  - user_likes: {cursor.fetchone()[0]}개")

conn.close()
print("\n✅ 검증 완료!")