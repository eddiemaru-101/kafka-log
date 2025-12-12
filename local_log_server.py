import asyncio
from user_controller import User
from log_info import UserState

async def run_user(user: User):
    # 비동기로 user의 update 메서드 호출
    while True:
        if user.state == UserState.NONE:
            break
        await asyncio.sleep(user.update_tick)
        user.update()

async def main():
    users = [User() for _ in range(100)]

    tasks = []
    for u in users:
        tasks.append(asyncio.create_task(run_user(u)))

    # 모든 Task를 병렬 실행
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
