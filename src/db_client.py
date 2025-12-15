import os
import random
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv
import pytz


class DBClient:
    """
    DB 연결 및 데이터 접근 관리
    
    책임:
    - MySQL/SQLite 연결 관리
    - 초기 데이터 로딩 및 캐싱
    - Users, Contents, Subscriptions CRUD
    """
    
    def __init__(self, config: dict):
        """
        Args:
            config: config.toml 전체 dict
        """
        # 1. .env 로딩
        load_dotenv()
        
        # 2. DB 모드 선택
        self.db_mode = config.get("database", {}).get("mode", "mysql")
        
        if self.db_mode == "sqlite":
            self.sqlite_path = config["database"]["sqlite_path"]
            print(f"📂 SQLite 모드: {self.sqlite_path}")
            self._check_sqlite_file()
        else:
            print(f"🔗 MySQL 모드")
            self._init_mysql_pool()
        
        # 3. 타임존 설정
        self.tz = pytz.timezone(config["global"]["timezone"])
        
        # 4. 데이터 캐싱
        self._active_users: List[Dict] = []
        self._tmdb_contents: List[Dict] = []
        self._subscription_plans: List[Dict] = []
        
        # 5. 초기 데이터 로딩
        self._load_initial_data()
    
    def _check_sqlite_file(self):
        """SQLite 파일 존재 여부 체크"""
        if not os.path.exists(self.sqlite_path):
            raise FileNotFoundError(
                f"❌ SQLite DB 파일이 없습니다: {self.sqlite_path}\n"
                f"   다음 명령으로 생성하세요: python mock_db/seed_data.py"
            )
    
    def _init_mysql_pool(self):
        """MySQL Connection Pool 생성"""
        self.pool = pooling.MySQLConnectionPool(
            pool_name="ott_pool",
            pool_size=5,
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306))
        )
    
    def _get_connection(self):
        """DB 연결 반환 (모드별 분기)"""
        if self.db_mode == "sqlite":
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row  # dict처럼 사용
            return conn
        else:
            return self.pool.get_connection()
    
    def _get_cursor(self, conn):
        """커서 반환 (모드별 분기)"""
        if self.db_mode == "sqlite":
            return conn.cursor()
        else:
            return conn.cursor(dictionary=True)
    
    def _row_to_dict(self, row) -> Dict:
        """Row를 dict로 변환 (SQLite 전용)"""
        if self.db_mode == "sqlite":
            return dict(row)
        return row
    
    def _get_placeholder(self) -> str:
        """SQL placeholder 반환 (SQLite: ?, MySQL: %s)"""
        return "?" if self.db_mode == "sqlite" else "%s"
    
    def _load_initial_data(self):
        """초기 데이터 로딩 (메모리 캐싱)"""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        
        # users (active만)
        cursor.execute("SELECT * FROM users WHERE account_status = 'active';")
        rows = cursor.fetchall()
        self._active_users = [self._row_to_dict(row) for row in rows]
        
        # tmdb_contents
        cursor.execute("SELECT * FROM tmdb_contents;")
        rows = cursor.fetchall()
        self._tmdb_contents = [self._row_to_dict(row) for row in rows]
        
        # subscription_plans
        cursor.execute("SELECT * FROM subscription_plans;")
        rows = cursor.fetchall()
        self._subscription_plans = [self._row_to_dict(row) for row in rows]
        
        cursor.close()
        conn.close()
        
        print(f"✅ DB 초기 데이터 로딩 완료 ({self.db_mode}):")
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
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        
        ph = self._get_placeholder()
        cursor.execute(f"""
            SELECT subscription_id, status
            FROM user_subscriptions
            WHERE user_id = {ph}
            ORDER BY start_date DESC
            LIMIT 1;
        """, (user_id,))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            row_dict = self._row_to_dict(row)
            if row_dict["status"] == "active":
                return row_dict["subscription_id"]
        return None
    
    # ========== CREATE 작업 ==========
    
    def insert_user(self, user_data: Dict) -> int:
        """
        유저 데이터를 DB에 삽입
        
        Args:
            user_data: UserRegister.create_user_data()로 생성된 데이터
        
        Returns:
            생성된 유저의 user_id
        """
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        
        ph = self._get_placeholder()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        insert_sql = f"""
            INSERT INTO users (
                email, password_hash, name, gender, birth_date, country, city,
                signup_date, account_status, is_adult_verified, last_login_date,
                device_last_used, push_opt_in, created_at, updated_at
            ) VALUES ({', '.join([ph] * 15)})
        """

        values = (
            user_data['email'],
            user_data['password_hash'],
            user_data['name'],
            user_data['gender'],
            user_data['birth_date'],
            user_data['country'],
            user_data['city'],
            user_data['signup_date'],
            user_data['account_status'],
            user_data['is_adult_verified'],
            user_data['last_login_date'],
            user_data['device_last_used'],
            user_data['push_opt_in'],
            now,
            now
        )
        
        cursor.execute(insert_sql, values)
        conn.commit()

        new_user_id = cursor.lastrowid
        cursor.close()
        conn.close()

        if new_user_id is None:
            raise RuntimeError("User insertion failed: no ID returned")

        print(f"✅ 신규 유저 생성 완료: user_id={new_user_id}, email={user_data['email']}")
        return new_user_id
    
    def insert_user_subscription(
        self,
        user_id: int,
        subscription_id: str,
        start_timestamp: datetime
    ) -> int:
        """
        신규 구독 생성
        
        Args:
            user_id: 유저 ID
            subscription_id: 구독 플랜 ID
            start_timestamp: 구독 시작 타임스탬프
        """
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        
        start_date = start_timestamp.astimezone(self.tz).date()
        end_date = start_date + timedelta(days=30)
        
        payment_methods = ["card", "mobile_pay", "account_transfer"]
        payment_method = random.choice(payment_methods)
        trial_used_flag = random.choices([0, 1], weights=[80, 20])[0]
        
        ph = self._get_placeholder()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(f"""
            INSERT INTO user_subscriptions (
                user_id, subscription_id, start_date, end_date,
                status, auto_renew_flag, cancel_reserved_flag,
                payment_method, trial_used_flag, created_at, updated_at
            ) VALUES ({', '.join([ph] * 11)});
        """, (
            user_id, subscription_id, start_date, end_date,
            "active", 1, 0, payment_method, trial_used_flag, now, now
        ))
        
        conn.commit()
        inserted_id = cursor.lastrowid
        cursor.close()
        conn.close()

        if inserted_id is None:
            raise RuntimeError("Subscription insertion failed: no ID returned")

        print(f"✅ 신규 구독 생성 완료: user_subscription_id={inserted_id}")
        return inserted_id
    
    # ========== UPDATE 작업 ==========
    
    def update_last_login_date(self, user_id: int, login_timestamp: datetime):
        """
        마지막 로그인 날짜 업데이트
        
        Args:
            user_id: 유저 ID
            login_timestamp: 로그인 타임스탬프
        """
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        
        login_date = login_timestamp.astimezone(self.tz).date()
        
        ph = self._get_placeholder()
        cursor.execute(f"""
            UPDATE users
            SET last_login_date = {ph}
            WHERE user_id = {ph};
        """, (login_date, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def cancel_user_subscription(self, user_id: int):
        """구독 취소 (status='cancelled')"""
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        
        ph = self._get_placeholder()
        
        if self.db_mode == "sqlite":
            # SQLite는 subquery 방식
            cursor.execute(f"""
                UPDATE user_subscriptions
                SET status = {ph},
                    auto_renew_flag = {ph},
                    cancel_reserved_flag = {ph}
                WHERE user_id = {ph}
                AND start_date = (
                    SELECT MAX(start_date)
                    FROM user_subscriptions
                    WHERE user_id = {ph}
                );
            """, ("cancelled", 0, 0, user_id, user_id))
        else:
            # MySQL 원본 쿼리
            cursor.execute(f"""
                UPDATE user_subscriptions
                SET status = {ph},
                    auto_renew_flag = {ph},
                    cancel_reserved_flag = {ph}
                WHERE user_id = {ph}
                AND start_date = (
                    SELECT latest_start
                    FROM (
                        SELECT MAX(start_date) AS latest_start
                        FROM user_subscriptions
                        WHERE user_id = {ph}
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
        
        conn = self._get_connection()
        cursor = self._get_cursor(conn)
        
        ph = self._get_placeholder()
        cursor.execute(f"""
            UPDATE users
            SET account_status = {ph}
            WHERE user_id = {ph};
        """, ("deleted", user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ 유저 삭제 완료: user_id={user_id}")