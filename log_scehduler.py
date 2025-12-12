import asyncio
import random
from datetime import datetime, timedelta

from user_controller import User
from log_info import UserState

# 1. 하루 시간대 분포 설정
HOUR_DISTRIBUTION = {
    (0, 6): 0.05,
    (6, 9): 0.10,
    (9, 12): 0.15,
    (12, 14): 0.10,
    (14, 18): 0.10,
    (18, 22): 0.35,
    (22, 24): 0.15,
}


def generate_daily_distribution(variation_range=0.2):
    # variation_range: 하루마다 각 비율이 어느 정도 변동할지 (0.2 = ±20%)
    new_dist = {}
    weighted_values = []

    # 1) 구간별 multiplier 적용
    for key, base_ratio in BASE_HOUR_DISTRIBUTION.items():
        # multiplier = 0.8 ~ 1.2 (variation_range=0.2일 때)
        multiplier = 1 + random.uniform(-variation_range, variation_range)
        new_ratio = base_ratio * multiplier

        new_dist[key] = new_ratio
        weighted_values.append(new_ratio)

    # 2) normalize (합 = 1)
    total = sum(weighted_values)
    for key in new_dist:
        new_dist[key] /= total

    return new_dist


# 전체 스케줄 값 저장용
TODAY_USER_TARGET = 0
HOURLY_PLAN = {}   # hour → user_count

async def run_user(user: User):
    # 비동기로 user의 update 메서드 호출
    while True:
        if user.state == UserState.NONE:
            break
        await asyncio.sleep(user.update_tick)
        user.update()

# 2. 오늘 하루 생성할 User 수 그리고 시간대별 분포량 계산
def generate_daily_plan(min_users=800, max_users=1200):
    global TODAY_USER_TARGET, HOURLY_PLAN

    daily_dist = generate_daily_distribution()

    TODAY_USER_TARGET = random.randint(min_users, max_users)
    HOURLY_PLAN = {h: 0 for h in range(24)}

    for (start, end), ratio in daily_dist.items():
        count = int(TODAY_USER_TARGET * ratio)
        hours = end - start
        per_hour = count // hours if hours > 0 else 0

        for h in range(start, end):
            HOURLY_PLAN[h] = per_hour

    print("[DAILY PLAN GENERATED]")
    print("Total Users Today:", TODAY_USER_TARGET)
    print("Hourly:", HOURLY_PLAN)


# 3. 현재 시간대의 User 생성 스케줄 실행
async def scheduler_generate_users():
    while True:
        now = datetime.now()
        current_hour = now.hour

        # 이번 시간에 생성할 총량
        to_create = HOURLY_PLAN.get(current_hour, 0)

        # 1시간 → 60분 → 분당 배분
        per_minute = max(1, to_create // 60)

        print(f"[SCHEDULER] {current_hour}h → total={to_create}, per_minute={per_minute}")

        for _ in range(60):
            # 1분에 여러 명 User 생성
            for _ in range(per_minute):
                user = User()
                asyncio.create_task(run_user(user))

            await asyncio.sleep(60)  # 1분 대기


# 4. 자정이 되면 새로운 Daily Plan 생성
async def scheduler_midnight_reset():
    while True:
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        sleep_for = (tomorrow - now).total_seconds()

        await asyncio.sleep(sleep_for)
        generate_daily_plan()


# 5. 메인 실행 - 기존 main을 대체
async def main():
    # 서버 시작 시, 오늘 계획 생성
    generate_daily_plan()

    # 자정 스케줄러 시작
    asyncio.create_task(scheduler_midnight_reset())

    # 시간대별 분당 생성 스케줄러 실행
    await scheduler_generate_users()


if __name__ == "__main__":
    asyncio.run(main())
