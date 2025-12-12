"""
SQLite 목업 DB 초기화 및 샘플 데이터 생성 스크립트
"""
import sqlite3
from datetime import datetime, timedelta, date
from faker import Faker
import random
import os

fake_kr = Faker('ko_KR')
fake_us = Faker('en_US')

def init_mock_db(db_path: str = "./mock_db/ott_test.db"):
    """SQLite 목업 DB 초기화 및 샘플 데이터 생성"""
    
    # DB 파일이 이미 있으면 삭제 (깨끗한 상태로 시작)
    if os.path.exists(db_path):
        print(f"⚠️  기존 DB 파일 삭제: {db_path}")
        os.remove(db_path)
    
    # mock_db 폴더 생성
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # 1. DB 연결
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🚀 SQLite 목업 DB 초기화 시작")
    print("=" * 60)
    
    # 2. 스키마 생성
    schema_path = os.path.join(os.path.dirname(db_path), "init_schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())
    
    print("\n✅ 테이블 스키마 생성 완료")
    
    # 3. subscription_plans 삽입
    print("\n📋 구독 플랜 생성 중...")
    plans = [
        ("basic", "베이직", 9900, 30, 1, "HD"),
        ("standard", "스탠다드", 13900, 30, 2, "HD"),
        ("premium", "프리미엄", 17900, 30, 4, "UHD")
    ]
    
    cursor.executemany("""
        INSERT INTO subscription_plans 
        (subscription_id, plan_name, price, duration_days, max_devices, quality)
        VALUES (?, ?, ?, ?, ?, ?)
    """, plans)
    print(f"✅ 구독 플랜 {len(plans)}개 생성 완료")
    
    # 4. tmdb_contents 샘플 데이터
    print("\n🎬 콘텐츠 생성 중...")
    content_types = ["movie", "tv"]
    genres_list = [
        "28,12",    # Action, Adventure
        "35",       # Comedy
        "18",       # Drama
        "27",       # Horror
        "10749",    # Romance
        "878",      # Science Fiction
        "53",       # Thriller
        "16",       # Animation
        "80",       # Crime
        "99"        # Documentary
    ]
    countries = ["KR", "US", "JP", "GB", "FR"]
    
    for i in range(200):  # 200개 콘텐츠
        content_type = random.choice(content_types)
        release_date = fake_kr.date_between(start_date='-10y', end_date='today')
        
        cursor.execute("""
            INSERT INTO tmdb_contents (
                tmdb_id, title, original_title, content_type, genre_ids,
                release_date, runtime, country, adult_only, popularity, vote_average
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            100000 + i,
            fake_kr.catch_phrase()[:50],  # 한글 제목
            fake_us.catch_phrase()[:50],  # 영문 제목
            content_type,
            random.choice(genres_list),
            release_date,
            random.randint(30, 180) if content_type == 'movie' else random.randint(20, 60),
            random.choice(countries),
            random.choices([0, 1], weights=[85, 15])[0],  # 15% adult
            round(random.uniform(1.0, 100.0), 1),
            round(random.uniform(5.0, 9.5), 1)
        ))
    
    print(f"✅ 콘텐츠 200개 생성 완료")
    
    # 5. users 샘플 데이터
    print("\n👥 유저 생성 중...")
    genders = ["male", "female", "other"]
    devices = ["Android", "iOS", "Web", "SmartTV", "FireTV"]
    
    user_count = 100
    for i in range(user_count):
        gender = random.choice(genders)
        signup_date = fake_kr.date_between(start_date='-3y', end_date='-7d')
        last_login = fake_kr.date_between(start_date=signup_date, end_date='today')
        
        # 성별에 따라 name 생성
        if gender == 'male':
            name = fake_kr.name_male()
        elif gender == 'female':
            name = fake_kr.name_female()
        else:
            name = fake_kr.name()
        
        cursor.execute("""
            INSERT INTO users (
                email, password_hash, name, gender, birth_date, country, city,
                signup_date, account_status, is_adult_verified, last_login_date,
                device_last_used, push_opt_in
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fake_kr.email(),
            fake_kr.sha256(),
            name,
            gender,
            fake_kr.date_of_birth(minimum_age=15, maximum_age=70),
            "South Korea",
            fake_kr.city(),
            signup_date,
            random.choices(['active', 'dormant'], weights=[90, 10])[0],  # 90% active
            random.choices([0, 1], weights=[30, 70])[0],  # 70% 성인 인증
            last_login,
            random.choice(devices),
            random.choices([0, 1], weights=[20, 80])[0]  # 80% push 동의
        ))
    
    print(f"✅ 유저 {user_count}명 생성 완료")
    
    # 6. user_subscriptions (active 유저 중 60%만 구독 중)
    print("\n💳 구독 데이터 생성 중...")
    cursor.execute("SELECT user_id, signup_date FROM users WHERE account_status = 'active'")
    active_users = cursor.fetchall()
    
    subscription_count = 0
    for user_id, signup_date in active_users:
        # 60% 확률로 구독
        if random.random() < 0.6:
            plan = random.choice(["basic", "standard", "premium"])
            
            # signup_date 이후부터 시작 가능
            signup_dt = datetime.strptime(signup_date, '%Y-%m-%d').date()
            days_since_signup = (date.today() - signup_dt).days
            
            if days_since_signup > 30:
                # 최근 3개월 내 구독 시작
                start_date = fake_kr.date_between(
                    start_date=max(signup_dt, date.today() - timedelta(days=90)),
                    end_date='today'
                )
            else:
                start_date = signup_dt
            
            end_date = start_date + timedelta(days=30)
            
            # 90% active, 10% cancelled
            status = random.choices(['active', 'cancelled'], weights=[90, 10])[0]
            auto_renew = 1 if status == 'active' else 0
            
            cursor.execute("""
                INSERT INTO user_subscriptions (
                    user_id, subscription_id, start_date, end_date, status,
                    auto_renew_flag, cancel_reserved_flag, payment_method, trial_used_flag
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, plan, start_date, end_date, status,
                auto_renew, 0, 
                random.choice(["card", "mobile_pay", "account_transfer"]), 
                random.choices([0, 1], weights=[70, 30])[0]  # 30% 무료체험 사용
            ))
            subscription_count += 1
    
    print(f"✅ 구독 데이터 {subscription_count}개 생성 완료")
    
    # 7. 커밋 및 통계 출력
    conn.commit()
    
    print("\n" + "=" * 60)
    print("📊 최종 통계")
    print("=" * 60)
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE account_status = 'active'")
    active_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tmdb_contents")
    contents_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_subscriptions WHERE status = 'active'")
    active_subs = cursor.fetchone()[0]
    
    print(f"  Active Users: {active_count}")
    print(f"  Total Contents: {contents_count}")
    print(f"  Active Subscriptions: {active_subs}")
    print(f"  Subscription Plans: {len(plans)}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"✅ 목업 DB 생성 완료: {db_path}")
    print("=" * 60)
    
    return db_path


if __name__ == "__main__":
    init_mock_db()