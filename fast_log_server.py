from fastapi import FastAPI
from kafka import KafkaProducer
import json
import asyncio
import threading
from user_controller import User
from log_info import UserState

app = FastAPI()

# Kafka Producer 설정
# producer = KafkaProducer(
#     bootstrap_servers=["b-1.msk-cluster.example.kafka.ap-northeast-2.amazonaws.com:9092"],
#     value_serializer=lambda v: json.dumps(v).encode("utf-8")
# )

TOPIC_NAME = "ott-log-topic"

# User 업데이트 실행 함수
async def run_user(user: User):
    while True:
        if user.state == UserState.NONE:
            break

        await asyncio.sleep(user.update_tick)
        user.update()

        # 생성된 로그 전송
        log = user.cur_log
        print(log)

        # if log is not None:
        #     producer.send(TOPIC_NAME, log)

# FastAPI 시작 시 User 여러 명 실행
@app.on_event("startup")
async def start_background_tasks():
    users = [User() for _ in range(10)]
    for u in users:
        asyncio.create_task(run_user(u))

# 수동 로그 전송 API
@app.post("/produce")
def produce_custom_log(payload: dict):
    #producer.send(TOPIC_NAME, payload)
    return {"status": "sent", "data": payload}

# 헬스 체크
@app.get("/health")
def health():
    return {"status": "ok"}
