import mysql.connector
import user_creator as uc
import random
from datetime import datetime, timedelta
import pytz

# 1. DB Connection (전역 1개만 사용)
conn = mysql.connector.connect(
    host="--",
    user="-",
    password="--",
    database="--"
)

# 2. 초기 로딩
# users 로딩
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM users;")
user_rows = cursor.fetchall()
cursor.close()
# user_subscriptions 로딩
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM user_subscriptions;")
user_subs_rows = cursor.fetchall()
cursor.close()
# user_likes 로딩
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM user_likes;")
user_likes_rows = cursor.fetchall()
cursor.close()
# tmdb_contents 로딩
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM tmdb_contents;")
tmdb_contents_rows = cursor.fetchall()
cursor.close()
# subscription_plans 로딩
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM subscription_plans;")
subscription_plans_rows = cursor.fetchall()
cursor.close()

# 서울 타임존 설정
tz = pytz.timezone("Asia/Seoul")

# 3. 랜덤 Active User 반환
def get_random_user():
    """account_status가 active인 유저 중 랜덤 선택"""
    active_users = [u for u in user_rows if u["account_status"] == "active"]
    return random.choice(active_users)

# 4. 새로운 유저 생성 후 DB에서 다시 읽기
def get_new_user():
    # 1) INSERT 실행 → user_id 받기
    new_user_id = uc.insert_new_user()
    print("new_user_id (from insert) =", new_user_id)

    # 2) user_id 기준으로 select
    # cursor = conn.cursor(dictionary=True)
    # cursor.execute("SELECT * FROM users WHERE user_id = %s;", (new_user_id,))
    # new_user = cursor.fetchone()
    # cursor.close()

    return new_user_id

def update_last_login_date(user_id: int):
    cursor = conn.cursor(dictionary=True)

    now_datetime = datetime.now(tz).date()

    cursor.execute("""
        UPDATE users
        SET last_login_date = %s
        WHERE user_id = %s;
    """, (now_datetime, user_id))

    conn.commit()
    cursor.close()

    print(f"user_id={user_id} last_login_date 업데이트 완료")

# 5. user_id 기반으로 유저 + 구독 모두 삭제
def delete_user(user_id: int):
    cursor = conn.cursor(dictionary=True)

    # user_subscriptions → FK 때문에 먼저 삭제
    cursor.execute("DELETE FROM user_subscriptions WHERE user_id = %s;", (user_id,))
    cursor.execute("DELETE FROM users WHERE user_id = %s;", (user_id,))

    conn.commit()
    cursor.close()

    print(f"user_id={user_id} 삭제 완료")

# 5-2. user_id 기반으로 유저 상태만 deleted로 변경
def update_delete_user(user_id: int):
    cancel_user_subscription(user_id)

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        UPDATE users
        SET account_status = %s
        WHERE user_id = %s;
    """, ("deleted", user_id))

    conn.commit()
    cursor.close()

    print(f"user_id={user_id} 계정 상태를 deleted로 변경 완료")

# 6. 특정 user_id의 구독만 삭제
def delete_user_subscription(user_id: int):
    cursor = conn.cursor(dictionary=True)

    cursor.execute("DELETE FROM user_subscriptions WHERE user_id = %s;", (user_id,))
    conn.commit()

    cursor.close()
    print(f"user_id={user_id} 구독 삭제 완료")

# 6-2. 특정 user_id의 구독 취소 (status='cancelled'로 변경)
def cancel_user_subscription(user_id: int):
    cursor = conn.cursor(dictionary=True)

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

    print(f"user_id={user_id} 구독 취소 완료 (가장 최신 start_date 1건만 반영)")

# 7. 특정 user_id의 subscription_id 반환
def get_user_subscription_id(user_id: int):
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

    # 데이터 없음 → None 반환
    if row is None:
        return None
    
    # 최신 구독의 상태가 active인 경우만 subscription_id 반환
    if row["status"] == "active":
        return row["subscription_id"]
    
    return None

# 8. user_subscriptions 테이블에 신규 구독 생성
def insert_user_subscription(user_id: int, subscription_id: str):
    cursor = conn.cursor(dictionary=True)

    today = datetime.now(tz).date()
    start_date = today
    end_date = today + timedelta(days=30)

    status = "active"
    auto_renew_flag = 1
    cancel_reserved_flag = 0

    payment_methods = ["card", "mobile_pay", "account_transfer"]
    payment_method = random.choice(payment_methods)

    trial_used_flag = random.choices([0, 1], weights=[80, 20])[0]

    insert_sql = """
        INSERT INTO user_subscriptions (
            user_id, subscription_id, start_date, end_date,
            status, auto_renew_flag, cancel_reserved_flag,
            payment_method, trial_used_flag
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    values = (
        user_id,
        subscription_id,
        start_date,
        end_date,
        status,
        auto_renew_flag,
        cancel_reserved_flag,
        payment_method,
        trial_used_flag
    )

    cursor.execute(insert_sql, values)
    conn.commit()

    inserted_id = cursor.lastrowid
    cursor.close()

    print(f"신규 구독 생성 완료: user_subscription.id={inserted_id}")
    return inserted_id

def get_random_contents():
    return random.choice(tmdb_contents_rows)