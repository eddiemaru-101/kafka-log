import os
import random
import hashlib
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv
from faker import Faker
import pytz


class DBClient:
    """
    DB 연결 및 데이터 접근 관리
    
    책임:
    - MySQL 연결 관리 (connection pool)
    - 초기 데이터 로딩 및 캐싱
    - Users, Contents, Subscriptions CRUD
    - 신규 유저 생성 (Faker 기반)
    """
    
    def __init__(self):
        # 1. .env 로딩
        load_dotenv()
        
        # 2. Connection pool 생성
        self.pool = pooling.MySQLConnectionPool(
            pool_name="ott_pool",
            pool_size=5,
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306))
        )
        
        # 3. 타임존 설정
        self.tz = pytz.timezone("Asia/Seoul")
        
        # 4. 데이터 캐싱
        self._active_users: List[Dict] = []
        self._tmdb_contents: List[Dict] = []
        self._subscription_plans: List[Dict] = []
        
        # 5. Faker 인스턴스 (신규 유저 생성용)
        self.fake_kr = Faker('ko_KR')
        self.fake_us = Faker('en_US')
        self.fake_jp = Faker('ja_JP')
        self.fake_cn = Faker('zh_CN')
        self.fake_vn = Faker('vi_VN')
        
        # 6. 유저 생성 분포 설정
        self.countries = ['KR', 'CN', 'US', 'JP', 'VN']
        self.country_weights = [95.5, 3, 1, 1, 0.5]
        
        self.genders = [0, 1, 2]
        self.gender_weights = [49.5, 49.5, 1]
        
        self.age_ranges = [(15, 19), (20, 29), (30, 39), (40, 49), (50, 59), (60, 70)]
        self.age_weights = [8, 16, 21, 26, 21, 7]
        
        self.devices = ['mobile', 'tv', 'tablet', 'desktop', 'console']
        self.device_weights = [60.9, 18, 11, 10, 0.1]
        
        self.kr_cities = ['서울', '경기', '인천', '부산', '대구', '울산', '경북', '경남',
                         '대전', '세종', '충북', '충남', '광주', '전북', '전남', '강원', '제주']
        self.kr_city_weights = [18, 26, 6, 7, 5, 2, 5, 6, 3, 1, 3, 4, 3, 3, 4, 3, 1]
        
        self.us_cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Seattle']
        self.jp_cities = ['Tokyo', 'Osaka', 'Kyoto', 'Yokohama', 'Nagoya']
        self.cn_cities = ['Beijing', 'Shanghai', 'Shenzhen', 'Guangzhou', 'Chengdu']
        self.vn_cities = ['Hanoi', 'Ho Chi Minh', 'Da Nang']
        
        # 7. 초기 데이터 로딩
        self._load_initial_data()
    
    def _load_initial_data(self):
        """초기 데이터 로딩 (메모리 캐싱)"""
        conn = self.pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # users (active만)
        cursor.execute("SELECT * FROM users WHERE account_status = 'active';")
        self._active_users = cursor.fetchall()
        
        # tmdb_contents
        cursor.execute("SELECT * FROM tmdb_contents;")
        self._tmdb_contents = cursor.fetchall()
        
        # subscription_plans
        cursor.execute("SELECT * FROM subscription_plans;")
        self._subscription_plans = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        print(f"✅ DB 초기 데이터 로딩 완료:")
        print(f"   - Active Users: {len(self._active_users)}")
        print(f"   - Contents: {len(self._tmdb_contents)}")
        print(f"   - Plans: {len(self._subscription_plans)}")
    
    # ========== READ 작업 ==========
    
    def get_random_user(self) -> Dict:
        """랜덤 active 유저 반환"""
        return random.choice(self._active_users)
    
    def get_random_contents(self) -> Dict:
        """랜덤 콘텐츠 반환"""
        return random.choice(self._tmdb_contents)
    
    def get_all_contents(self) -> List[Dict]:
        """전체 콘텐츠 리스트 반환 (LogEventFactory에서 사용)"""
        return self._tmdb_contents.copy()
    
    def get_user_subscription_id(self, user_id: int) -> Optional[str]:
        """유저의 활성 구독 ID 반환 (없으면 None)"""
        conn = self.pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT subscription_id, status
            FROM user_subscriptions
            WHERE user_id = %s
            ORDER BY start_date DESC
            LIMIT 1;
        """, (user_id,))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row and row["status"] == "active":
            return row["subscription_id"]
        return None
    
    # ========== CREATE 작업 ==========
    
    def _generate_password_hash(self) -> str:
        """비밀번호 해시 생성"""
        raw_pw = self.fake_kr.password()
        return hashlib.sha256(raw_pw.encode()).hexdigest()
    
    def _get_faker_by_country(self, country: str):
        """국가별 Faker 반환"""
        return {
            'KR': self.fake_kr,
            'US': self.fake_us,
            'JP': self.fake_jp,
            'CN': self.fake_cn,
            'VN': self.fake_vn
        }[country]
    
    def _get_city_by_country(self, country: str) -> str:
        """국가별 도시 생성"""
        if country == 'KR':
            return random.choices(self.kr_cities, weights=self.kr_city_weights)[0]
        if country == 'US':
            return random.choice(self.us_cities)
        if country == 'JP':
            return random.choice(self.jp_cities)
        if country == 'CN':
            return random.choice(self.cn_cities)
        if country == 'VN':
            return random.choice(self.vn_cities)
    
    def _generate_birth_date(self) -> datetime.date:
        """연령대 분포 기반 생일 생성"""
        age_range = random.choices(self.age_ranges, weights=self.age_weights)[0]
        age = random.randint(age_range[0], age_range[1])
        
        today = datetime.now(self.tz)
        birth_year = today.year - age
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        
        return datetime(birth_year, birth_month, birth_day).date()
    
    def _generate_is_adult_verified(self, birth_date: datetime.date) -> int:
        """성인 인증 여부 (만 20세 이상 95% 확률)"""
        age = (datetime.now(self.tz).date() - birth_date).days // 365
        if age < 20:
            return 0
        return random.choices([0, 1], weights=[5, 95])[0]
    
    def insert_new_user(self) -> int:
        """
        신규 유저 생성 및 DB 삽입 (Faker 기반)
        
        Returns:
            생성된 유저의 user_id
        """
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now(self.tz).date()
        now_datetime = datetime.now(self.tz)
        
        # 국가 선택
        country = random.choices(self.countries, weights=self.country_weights)[0]
        fake = self._get_faker_by_country(country)
        
        # 생일 생성
        birth_date = self._generate_birth_date()
        
        # 이메일 생성
        email = f"user_{random.randint(10000, 99999)}@ottservice.com"
        
        insert_sql = """
            INSERT INTO users (
                email, password_hash, name, gender, birth_date, country, city,
                signup_date, account_status, is_adult_verified, last_login_date,
                device_last_used, push_opt_in
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        user_data = (
            email,
            self._generate_password_hash(),
            fake.name(),
            random.choices(self.genders, weights=self.gender_weights)[0],
            birth_date,
            country,
            self._get_city_by_country(country),
            today,
            'active',
            self._generate_is_adult_verified(birth_date),
            now_datetime,
            random.choices(self.devices, weights=self.device_weights)[0],
            random.choices([0, 1], weights=[45, 55])[0]
        )
        
        cursor.execute(insert_sql, user_data)
        conn.commit()
        
        new_user_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        print(f"✅ 신규 유저 생성 완료: user_id={new_user_id}, email={email}")
        return new_user_id
    
    def insert_user_subscription(
        self,
        user_id: int,
        subscription_id: str
    ) -> int:
        """신규 구독 생성"""
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now(self.tz).date()
        start_date = today
        end_date = today + timedelta(days=30)
        
        payment_methods = ["card", "mobile_pay", "account_transfer"]
        payment_method = random.choice(payment_methods)
        trial_used_flag = random.choices([0, 1], weights=[80, 20])[0]
        
        cursor.execute("""
            INSERT INTO user_subscriptions (
                user_id, subscription_id, start_date, end_date,
                status, auto_renew_flag, cancel_reserved_flag,
                payment_method, trial_used_flag
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            user_id, subscription_id, start_date, end_date,
            "active", 1, 0, payment_method, trial_used_flag
        ))
        
        conn.commit()
        inserted_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        print(f"✅ 신규 구독 생성 완료: user_subscription_id={inserted_id}")
        return inserted_id
    
    # ========== UPDATE 작업 ==========
    
    def update_last_login_date(self, user_id: int):
        """마지막 로그인 날짜 업데이트"""
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now(self.tz).date()
        cursor.execute("""
            UPDATE users
            SET last_login_date = %s
            WHERE user_id = %s;
        """, (now, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def cancel_user_subscription(self, user_id: int):
        """구독 취소 (status='cancelled')"""
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE user_subscriptions
            SET status = %s,
                auto_renew_flag = %s,
                cancel_reserved_flag = %s
            WHERE user_id = %s
            AND start_date = (
                SELECT latest_start
                FROM (
                    SELECT MAX(start_date) AS latest_start
                    FROM user_subscriptions
                    WHERE user_id = %s
                ) AS t
            );
        """, ("cancelled", 0, 0, user_id, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ 구독 취소 완료: user_id={user_id}")
    
    def update_delete_user(self, user_id: int):
        """유저 삭제 (상태만 'deleted'로 변경)"""
        self.cancel_user_subscription(user_id)
        
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users
            SET account_status = %s
            WHERE user_id = %s;
        """, ("deleted", user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ 유저 삭제 완료: user_id={user_id}")