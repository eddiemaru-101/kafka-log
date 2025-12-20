import sqlite3
import random

db_path = r"c:\Users\SBA\Desktop\sesac-log\kafka-log\mock_db\ott_test.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Users 테이블 account_status 업데이트 중...")

# 모든 유저의 account_status를 랜덤하게 설정 (85% active, 5% suspended, 10% deleted)
cursor.execute("SELECT user_id FROM users")
users = cursor.fetchall()

active_count = 0
suspended_count = 0
deleted_count = 0

for (user_id,) in users:
    account_status = random.choices(
        ["active", "suspended", "deleted"],
        weights=[85, 5, 10]
    )[0]

    cursor.execute(
        "UPDATE users SET account_status = ? WHERE user_id = ?",
        (account_status, user_id)
    )

    if account_status == "active":
        active_count += 1
    elif account_status == "suspended":
        suspended_count += 1
    else:
        deleted_count += 1

conn.commit()

print(f"\n✅ 업데이트 완료!")
print(f"  - Active: {active_count}명")
print(f"  - Suspended: {suspended_count}명")
print(f"  - Deleted: {deleted_count}명")
print(f"  - 총: {len(users)}명")

# 검증
cursor.execute("SELECT account_status, COUNT(*) FROM users GROUP BY account_status")
print("\n📊 최종 상태:")
for status, count in cursor.fetchall():
    print(f"  - {status}: {count}명")

conn.close()
