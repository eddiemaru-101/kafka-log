import os
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Optional
from contextlib import contextmanager
from dotenv import load_dotenv
import random
import string
from datetime import date, timedelta



class DBClient:
    """
    DB 작업 전담 클라이언트
    
    책임:
    - MySQL 연결 관리
    - 유저 CRUD (생성, 조회, 업데이트)
    - 콘텐츠 조회
    - 구독 정보 조회
    """
    
    def __init__(self, config: dict):
        """
        Args:
            config: config.toml 전체 dict
        """
        self.config = config
        
        # .env 파일 로드
        load_dotenv()
        
        # DB 연결 정보 (.env에서 읽기)
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "3306"))
        self.database = os.getenv("DB_DATABASE", "ott_service")
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "")
        
        # 커넥션 풀 설정
        self.pool_name = "mypool"
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        
        # 커넥션 풀 생성
        self._create_pool()
        
        print(f"✅ DB Client 초기화 완료")
        print(f"   Host: {self.host}:{self.port}")
        print(f"   Database: {self.database}")
        print(f"   Pool Size: {self.pool_size}")
    
    
    def _create_pool(self):
        """커넥션 풀 생성"""
        try:
            self.pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name=self.pool_name,
                pool_size=self.pool_size,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                autocommit=True
            )
        except Error as e:
            print(f"❌ DB 커넥션 풀 생성 실패: {e}")
            raise
    
    
    @contextmanager
    def get_connection(self):
        """커넥션 풀에서 연결 가져오기 (Context Manager)"""
        conn = self.pool.get_connection()
        try:
            yield conn
        finally:
            conn.close()
    
    
    # ========== 유저 관련 메서드 ==========
    
    def create_new_user(self, signup_date: Optional[date] = None) -> int:
        """
        신규 유저 생성 (DB INSERT)
        
        Returns:
            생성된 user_id
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 랜덤 데이터 생성
            random_suffix = ''.join(random.choices(string.digits, k=6))
            email = f"G_user_{random_suffix}@ottservice.com"  # G_ 접두사 추가
            password_hash = ''.join(random.choices(string.hexdigits.lower(), k=64))
            
            names = ["김민준", "이서윤", "박지호", "최수빈", "정예은", "강도윤", "조시우", "윤하은"]
            cities = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
            
            name = random.choice(names)
            gender = random.randint(0, 1)  # 0=남성, 1=여성, 2=기타
            
            # 생년월일: 1970~2005년생
            birth_date = date(random.randint(1970, 2005), random.randint(1, 12), random.randint(1, 28))
            city = random.choice(cities)
            if signup_date is None:
                signup_date = date.today()
            
            query = """
                INSERT INTO users (
                    email, password_hash, name, gender, birth_date,
                    country, city, signup_date, account_status, 
                    is_adult_verified, push_opt_in, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            
            cursor.execute(query, (
                email,
                password_hash,
                name,
                gender,
                birth_date,
                'KR',  # country
                city,
                signup_date,
                'active',  # account_status
                1 if (date.today() - birth_date).days >= 365*19 else 0,  # is_adult_verified (19세 이상)
                random.choice([0, 1])  # push_opt_in
            ))
            
            user_id = cursor.lastrowid
            cursor.close()
            
            return user_id
    
    
    def get_random_users(self, limit: int) -> List[Dict]:
        """
        DB에서 랜덤 유저 조회 (DAU만큼)
        
        Args:
            limit: 가져올 유저 수 (DAU)
        
        Returns:
            유저 정보 리스트 [{"user_id": 1, "is_subscribed": True}, ...]
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # 랜덤 유저 조회
            query = f"""
                SELECT 
                    u.user_id,
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 
                            FROM user_subscriptions us 
                            WHERE us.user_id = u.user_id 
                            AND us.status = 'active'
                        ) THEN 1
                        ELSE 0
                    END AS is_subscribed
                FROM users u
                WHERE u.account_status = 'active'
                ORDER BY RAND()
                LIMIT {limit}
            """
            cursor.execute(query)
            
            users = cursor.fetchall()
            cursor.close()
            
            return users 
            #[{'user_id': 10231, 'is_subscribed': 1}, 
            # {'user_id': 48752, 'is_subscribed': 0}, 
            # {'user_id': 33109, 'is_subscribed': 1}]
    
    
    def update_user_subscription(self, user_id: int, is_subscribed: bool):
        """
        유저 구독 상태 업데이트
        
        Args:
            user_id: 유저 ID
            is_subscribed: 구독 여부 (True/False)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if is_subscribed:
                # 구독 활성화: user_subscriptions 테이블에 INSERT 또는 UPDATE
                # (실제로는 subscription_id, start_date, end_date 등 필요)
                pass
            else:
                # 구독 해지: status를 'cancelled'로 변경
                query = """
                    UPDATE user_subscriptions
                    SET status = 'cancelled'
                    WHERE user_id = %s AND status = 'active'
                """
                cursor.execute(query, (user_id,))
            
            cursor.close()
    
    
    def delete_user(self, user_id: int):
        """
        유저 탈퇴 (DELETE)
        
        Args:
            user_id: 유저 ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "DELETE FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            cursor.close()
    
    
    # ========== 콘텐츠 관련 메서드 ==========
    
    def get_random_content(self) -> Optional[Dict]:
        """
        랜덤 콘텐츠 1개 조회
        
        Returns:
            콘텐츠 정보 dict {"contents_id": "movie_123", "contents_type": "movie", ...}
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT contents_id, contents_type, title, genre, runtime
                FROM contents
                ORDER BY RAND()
                LIMIT 1
            """
            cursor.execute(query)
            
            content = cursor.fetchone()
            cursor.close()
            
            return content
    
    
    def get_content_by_id(self, contents_id: str) -> Optional[Dict]:
        """
        특정 콘텐츠 조회
        
        Args:
            contents_id: 콘텐츠 ID (예: "movie_123", "tv_456")
        
        Returns:
            콘텐츠 정보 dict
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT contents_id, contents_type, title, genre, runtime
                FROM contents
                WHERE contents_id = %s
            """
            cursor.execute(query, (contents_id,))
            
            content = cursor.fetchone()
            cursor.close()
            
            return content
    
    
    def get_episodes_by_content_id(self, contents_id: str) -> List[Dict]:
        """
        시리즈의 에피소드 목록 조회 (TV 시리즈용)
        
        Args:
            contents_id: 콘텐츠 ID (예: "tv_456")
        
        Returns:
            에피소드 리스트 [{"episode_id": "tv_456_ep1", "episode_num": 1, ...}, ...]
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT episode_id, episode_num, season_num, title
                FROM episodes
                WHERE contents_id = %s
                ORDER BY season_num, episode_num
            """
            cursor.execute(query, (contents_id,))
            
            episodes = cursor.fetchall()
            cursor.close()
            
            return episodes
    
    
    # ========== 구독 관련 메서드 ==========
    
    def get_random_subscription(self) -> Optional[Dict]:
        """
        랜덤 구독 상품 1개 조회
        
        Returns:
            구독 정보 dict {"subscription_id": "subs_1", "name": "베이직", "price": 9900, ...}
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT subscription_id, name, price
                FROM subscriptions
                ORDER BY RAND()
                LIMIT 1
            """
            cursor.execute(query)
            
            subscription = cursor.fetchone()
            cursor.close()
            
            return subscription
    
    
    # ========== 리소스 정리 ==========
    
    def close(self):
        """
        커넥션 풀 종료
        """
        # 커넥션 풀은 자동으로 정리되므로 특별한 처리 불필요
        print("✅ DB Client 종료")