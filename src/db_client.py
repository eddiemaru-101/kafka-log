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

        # 콘텐츠 캐시 초기화
        self.contents_cache = None
        self.contents_weights = None


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

            # 랜덤 유저 조회 (subscription_status 컬럼 기반으로 구독 여부 판단)
            query = f"""
                SELECT
                    u.user_id,
                    CASE
                        WHEN u.subscription_status = 'active' THEN 1
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
    
    
    def activate_subscription(self, user_id: int, subscription_id: str):
        """
        유저 구독 활성화 (subscription-start 로그 발생 시 호출)
        users 테이블의 subscription_status를 'active'로 변경

        Args:
            user_id: 유저 ID
            subscription_id: 구독 상품 ID (예: "s_1")
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = "%s" if self.db_type == "mysql" else "?"

            # subscription_status를 'active'로 업데이트
            # subscription_start_date는 오늘, subscription_end_date는 1개월 후, subscription_id도 저장
            query = f"""
                UPDATE users
                SET subscription_status = 'active',
                    subscription_start_date = CURRENT_DATE,
                    subscription_end_date = DATE_ADD(CURRENT_DATE, INTERVAL 1 MONTH),
                    subscription_id = {placeholder}
                WHERE user_id = {placeholder}
            """ if self.db_type == "mysql" else f"""
                UPDATE users
                SET subscription_status = 'active',
                    subscription_start_date = DATE('now'),
                    subscription_end_date = DATE('now', '+1 month'),
                    subscription_id = {placeholder}
                WHERE user_id = {placeholder}
            """

            cursor.execute(query, (subscription_id, user_id))

            if self.db_type == "sqlite":
                conn.commit()

            cursor.close()


    def deactivate_subscription(self, user_id: int):
        """
        유저 구독 해지 (subscription-stop 로그 발생 시 호출)
        users 테이블의 subscription_status를 'expired' 또는 'cancelled'로 랜덤 변경

        Args:
            user_id: 유저 ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            placeholder = "%s" if self.db_type == "mysql" else "?"

            # 'expired' 또는 'cancelled' 랜덤 선택
            new_status = random.choice(['expired', 'cancelled'])

            query = f"""
                UPDATE users
                SET subscription_status = {placeholder}
                WHERE user_id = {placeholder}
            """
            cursor.execute(query, (new_status, user_id))

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

    def load_contents_cache(self):
        """
        인기도 상위 50개 콘텐츠를 DB에서 조회하여 캐시에 저장
        초기화 시 한 번만 호출하여 성능 최적화
        """
        with self.get_connection() as conn:
            if self.db_type == "mysql":
                cursor = conn.cursor(dictionary=True)
                table_name = "tmdb_contents"
            else:  # sqlite
                cursor = conn.cursor()
                table_name = "tmdb_contents"

            # 인기도 상위 50개 조회 (에피소드 정보 포함)
            query = f"""
                SELECT content_id as contents_id, content_type as contents_type, title, genre_names as genre, runtime, popularity, number_of_episodes
                FROM {table_name}
                ORDER BY popularity DESC
                LIMIT 50
            """
            cursor.execute(query)

            if self.db_type == "mysql":
                contents = cursor.fetchall()
            else:  # sqlite
                rows = cursor.fetchall()
                contents = [dict(row) for row in rows]

            cursor.close()

            if contents:
                # popularity를 float로 변환하여 가중치 리스트 생성
                self.contents_cache = contents
                self.contents_weights = [float(c['popularity']) for c in contents]
                print(f"✅ 콘텐츠 캐시 로드 완료 ({len(contents)}개)")
            else:
                print("⚠️  콘텐츠가 없어 캐시를 생성하지 못했습니다.")

    def get_random_content(self) -> Optional[Dict]:
        """
        캐시된 콘텐츠 중에서 인기도 기반 가중치로 1개 선택

        Returns:
            콘텐츠 정보 dict {"contents_id": "movie_123", "contents_type": "movie", ...}
        """
        # 캐시가 없으면 None 반환
        if not self.contents_cache or not self.contents_weights:
            return None

        # 캐시에서 인기도 가중치로 1개 선택
        selected = random.choices(self.contents_cache, weights=self.contents_weights, k=1)[0]

        # popularity 필드 제거하여 복사본 반환 (원본 캐시 보호)
        result = selected.copy()
        result.pop('popularity', None)

        return result
    
    
    def get_content_by_id(self, contents_id: str) -> Optional[Dict]:
        """
        특정 콘텐츠 조회 (캐시에서 검색)

        Args:
            contents_id: 콘텐츠 ID (예: "movie_123", "tv_456")

        Returns:
            콘텐츠 정보 dict
        """
        # 캐시에서 검색
        if self.contents_cache:
            for content in self.contents_cache:
                if content.get('contents_id') == contents_id:
                    # popularity 제거한 복사본 반환
                    result = content.copy()
                    result.pop('popularity', None)
                    return result

        # 캐시에 없으면 None 반환
        return None
    
    
    def get_episodes_by_content_id(self, contents_id: str) -> List[Dict]:
        """
        캐시에서 콘텐츠 정보를 찾아 에피소드 리스트를 동적 생성하여 반환
        """
        # 캐시에서 콘텐츠 찾기
        if self.contents_cache:
            for content in self.contents_cache:
                if content.get('contents_id') == contents_id:
                    # number_of_episodes가 없거나 0이면 빈 리스트 반환
                    num_episodes = content.get('number_of_episodes')
                    if not num_episodes:
                        return []

                    # episode_id 리스트 생성
                    episodes = [{"episode_id": f"ep_{i:02d}"} for i in range(1, int(num_episodes) + 1)]
                    return episodes

        # 캐시에 없으면 빈 리스트 반환
        return []
    
    
    # ========== 구독 관련 메서드 ========== (삭제됨: subscription_plans 테이블 삭제)
    
    
    # ========== 리소스 정리 ==========
    
    def close(self):
        """
        커넥션 풀 종료
        """
        # 커넥션 풀은 자동으로 정리되므로 특별한 처리 불필요
        print("✅ DB Client 종료")