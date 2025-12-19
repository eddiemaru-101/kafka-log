import os
import sqlite3
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Optional, Any
from contextlib import contextmanager
from dotenv import load_dotenv
import random
import string
from datetime import date, timedelta
import uuid


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

        # DB 타입 선택 (config.toml 우선, 없으면 .env, 기본값 sqlite)
        db_config = config.get("database", {})
        self.db_type = db_config.get("db_type", os.getenv("DB_TYPE", "sqlite")).lower()

        if self.db_type == "mysql":
            # MySQL (AWS RDS) 연결 정보
            self.host = os.getenv("DB_HOST", "localhost")
            self.port = int(os.getenv("DB_PORT", "3306"))
            self.database = os.getenv("DB_NAME", "ott_service")
            self.user = os.getenv("DB_USER", "root")
            self.password = os.getenv("DB_PASSWORD", "")

            # 커넥션 풀 설정
            self.pool_name = "mypool"
            self.pool_size = int(os.getenv("DB_POOL_SIZE", "5"))

            # MySQL 커넥션 풀 생성
            self._create_mysql_pool()

            print(f"✅ DB Client 초기화 완료 (MySQL)")
            print(f"   Host: {self.host}:{self.port}")
            print(f"   Database: {self.database}")
            print(f"   Pool Size: {self.pool_size}")

        elif self.db_type == "sqlite":
            # SQLite (Mock DB) 연결 정보 (config.toml 우선, 없으면 .env)
            self.sqlite_path = db_config.get("sqlite_db_path", os.getenv("SQLITE_DB_PATH", "mock_db/ott_test.db"))
            self.pool = None  # SQLite는 풀 사용 안함

            # SQLite DB 파일 존재 확인
            if not os.path.exists(self.sqlite_path):
                raise FileNotFoundError(f"SQLite DB 파일을 찾을 수 없습니다: {self.sqlite_path}")

            print(f"✅ DB Client 초기화 완료 (SQLite)")
            print(f"   DB Path: {self.sqlite_path}")

        else:
            raise ValueError(f"지원하지 않는 DB_TYPE: {self.db_type}. 'mysql' 또는 'sqlite'를 사용하세요.")
    
    
    def _create_mysql_pool(self):
        """MySQL 커넥션 풀 생성"""
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
            print(f"❌ MySQL 커넥션 풀 생성 실패: {e}")
            raise


    @contextmanager
    def get_connection(self):
        """DB 연결 가져오기 (Context Manager) - MySQL/SQLite 자동 선택"""
        if self.db_type == "mysql":
            conn = self.pool.get_connection()  # type: ignore
            try:
                yield conn
            finally:
                conn.close()
        elif self.db_type == "sqlite":
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row  # dict-like access
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
            email = f"G_user_{uuid.uuid4().hex}@ottservice.com"
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

            if self.db_type == "mysql":
                placeholder = "%s"
                now_func = "NOW()"
            else:  # sqlite
                placeholder = "?"
                now_func = "datetime('now')"

            query = f"""
                INSERT INTO users (
                    email, password_hash, name, gender, birth_date,
                    country, city, signup_date, account_status,
                    is_adult_verified, push_opt_in, created_at, updated_at
                )
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder},
                        {placeholder}, {placeholder}, {placeholder}, {placeholder},
                        {placeholder}, {placeholder}, {now_func}, {now_func})
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

            if self.db_type == "sqlite":
                conn.commit()

            user_id = cursor.lastrowid  # type: ignore
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
            if self.db_type == "mysql":
                cursor = conn.cursor(dictionary=True)
                random_func = "RAND()"
            else:  # sqlite
                cursor = conn.cursor()
                random_func = "RANDOM()"

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
                ORDER BY {random_func}
                LIMIT {limit}
            """
            cursor.execute(query)

            if self.db_type == "mysql":
                users = cursor.fetchall()
            else:  # sqlite
                rows = cursor.fetchall()
                users = [dict(row) for row in rows]

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
            placeholder = "%s" if self.db_type == "mysql" else "?"

            if is_subscribed:
                # 구독 활성화: user_subscriptions 테이블에 INSERT 또는 UPDATE
                # (실제로는 subscription_id, start_date, end_date 등 필요)
                pass
            else:
                # 구독 해지: status를 'cancelled'로 변경
                query = f"""
                    UPDATE user_subscriptions
                    SET status = 'cancelled'
                    WHERE user_id = {placeholder} AND status = 'active'
                """
                cursor.execute(query, (user_id,))

            if self.db_type == "sqlite":
                conn.commit()

            cursor.close()


    def delete_user(self, user_id: int):
        """
        유저 탈퇴 (account_status를 'deleted'로 변경)

        Args:
            user_id: 유저 ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = "%s" if self.db_type == "mysql" else "?"

            query = f"""
                UPDATE users
                SET account_status = 'deleted'
                WHERE user_id = {placeholder}
            """
            cursor.execute(query, (user_id,))

            if self.db_type == "sqlite":
                conn.commit()

            cursor.close()
    
    
    # ========== 콘텐츠 관련 메서드 ==========
    
    def get_random_content(self) -> Optional[Dict]:
        """
        인기도 기반 가중치 콘텐츠 1개 조회

        tmdb_contents 테이블에서 인기도(popularity) 내림차순 상위 100개 중
        인기도를 가중치로 사용하여 1개 선택

        Returns:
            콘텐츠 정보 dict {"contents_id": "movie_123", "contents_type": "movie", ...}
        """
        with self.get_connection() as conn:
            if self.db_type == "mysql":
                cursor = conn.cursor(dictionary=True)
                table_name = "contents"
            else:  # sqlite
                cursor = conn.cursor()
                table_name = "tmdb_contents"

            # 인기도 상위 100개 조회
            query = f"""
                SELECT content_id as contents_id, content_type as contents_type, title, genre_names as genre, runtime, popularity
                FROM {table_name}
                ORDER BY popularity DESC
                LIMIT 100
            """
            cursor.execute(query)

            if self.db_type == "mysql":
                contents = cursor.fetchall()
            else:  # sqlite
                rows = cursor.fetchall()
                contents = [dict(row) for row in rows]

            cursor.close()

            if not contents:
                return None

            # 인기도를 가중치로 사용하여 1개 선택
            popularities = [c['popularity'] for c in contents]
            selected = random.choices(contents, weights=popularities, k=1)[0]

            # popularity 필드 제거 (로그에 불필요)
            selected.pop('popularity', None)

            return selected
    
    
    def get_content_by_id(self, contents_id: str) -> Optional[Dict]:
        """
        특정 콘텐츠 조회

        Args:
            contents_id: 콘텐츠 ID (예: "movie_123", "tv_456")

        Returns:
            콘텐츠 정보 dict
        """
        with self.get_connection() as conn:
            if self.db_type == "mysql":
                cursor = conn.cursor(dictionary=True)
                placeholder = "%s"
                table_name = "contents"
            else:  # sqlite
                cursor = conn.cursor()
                placeholder = "?"
                table_name = "tmdb_contents"

            query = f"""
                SELECT content_id as contents_id, content_type as contents_type, title, genre_names as genre, runtime
                FROM {table_name}
                WHERE content_id = {placeholder}
            """
            cursor.execute(query, (contents_id,))

            if self.db_type == "mysql":
                content = cursor.fetchone()
            else:  # sqlite
                row = cursor.fetchone()
                content = dict(row) if row else None

            cursor.close()

            return content
    
    
    def get_episodes_by_content_id(self, contents_id: str) -> List[Dict]:
        """
        episodes 테이블 대신 tmdb_contents의 정보를 기반으로 
        가상의 에피소드 리스트를 동적 생성하여 반환
        """
        with self.get_connection() as conn:
            if self.db_type == "mysql":
                cursor = conn.cursor(dictionary=True)
                placeholder = "%s"
                table_name = "tmdb_contents"
            else:  # sqlite
                cursor = conn.cursor()
                placeholder = "?"
                table_name = "tmdb_contents"

            # 1. 해당 콘텐츠의 총 에피소드 수와 제목 조회
            query = f"""
                SELECT title, number_of_episodes, number_of_seasons
                FROM {table_name}
                WHERE content_id = {placeholder}
            """
            cursor.execute(query, (contents_id,))

            if self.db_type == "mysql":
                row = cursor.fetchone()
            else:
                res = cursor.fetchone()
                row = dict(res) if res else None
            
            cursor.close()

            # 2. 데이터가 없거나 TV 시리즈가 아닌 경우(에피소드 수 0) 빈 리스트 반환
            if not row or not row.get('number_of_episodes'):
                return []

            # 3. number_of_episodes 수만큼 episode_id 리스트 생성
            num_episodes = int(row['number_of_episodes'])
            episodes = [{"episode_id": f"ep_{i:02d}"} for i in range(1, num_episodes + 1)]

            return episodes
    
    
    # ========== 구독 관련 메서드 ==========
    
    def get_random_subscription(self) -> Optional[Dict]:
        """
        랜덤 구독 상품 1개 조회

        Returns:
            구독 정보 dict {"subscription_id": "subs_1", "name": "베이직", "price": 9900, ...}
        """
        with self.get_connection() as conn:
            if self.db_type == "mysql":
                cursor = conn.cursor(dictionary=True)
                random_func = "RAND()"
                table_name = "subscriptions"
            else:  # sqlite
                cursor = conn.cursor()
                random_func = "RANDOM()"
                table_name = "subscription_plans"

            query = f"""
                SELECT subscription_id, subscription_type as name, price
                FROM {table_name}
                ORDER BY {random_func}
                LIMIT 1
            """
            cursor.execute(query)

            if self.db_type == "mysql":
                subscription = cursor.fetchone()
            else:  # sqlite
                row = cursor.fetchone()
                subscription = dict(row) if row else None

            cursor.close()

            return subscription
    
    
    # ========== 리소스 정리 ==========
    
    def close(self):
        """
        커넥션 풀 종료
        """
        # 커넥션 풀은 자동으로 정리되므로 특별한 처리 불필요
        print("✅ DB Client 종료")