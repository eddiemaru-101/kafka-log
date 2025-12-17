import time
import toml
from datetime import datetime

from src.db_client import DBClient
from src.date_generator import LogDateGenerator
from src.user_selector import UserSelector
from src.user_event_controller import UserEventController
from src.log_contents import LogContents
from src.log_sink import LogSink


def main():
    """
    로그 생성 오케스트레이터 V2

    아키텍처 (01-log_gen_guide.md 기반):
    - DBClient: 모든 DB 작업 (유저/콘텐츠/구독 CRUD)
    - DateGenerator: 타임스탬프 생성
    - UserSelector: 유저 선정 및 상태 관리
    - UserEventController: 유저 상태 → 로그 타입 결정 & 상태 전이
    - LogContents: 로그 타입별 실제 내용 생성
    - LogSink: 최종 출력 (S3/로컬/Kafka)
    """

    print("=" * 80)
    print("🚀 로그 생성기 V2 시작")
    print("=" * 80)

    # ========== 1. Config 로딩 ==========
    config = toml.load("config/config.toml")
    print(f"\n✅ Config 로딩 완료")


    # ========== 2. 모듈 초기화 ==========
    print("\n📦 모듈 초기화 중...\n")

    db_client = DBClient(config)
    print("✅ DB Client 초기화 완료")

    date_generator = LogDateGenerator(config)
    user_selector = UserSelector(config, db_client)
    user_event_controller = UserEventController(config)
    log_contents = LogContents(config, db_client)
    log_sink = LogSink(config)

    print("✅ 모든 모듈 초기화 완료")


    # ========== 3. 실행 모드 확인 ==========
    generation_mode = config["global"].get("generation_mode", "batch")

    print(f"\n⚙️  실행 모드: {generation_mode}")


    if generation_mode == "batch":
        # ========== 4. Batch 모드 실행 ==========
        run_batch_mode(
            config=config,
            date_generator=date_generator,
            user_selector=user_selector,
            user_event_controller=user_event_controller,
            log_contents=log_contents,
            log_sink=log_sink
        )

    elif generation_mode == "streaming":
        # ========== 5. Streaming 모드 실행 ==========
        run_streaming_mode(
            config=config,
            date_generator=date_generator,
            user_selector=user_selector,
            user_event_controller=user_event_controller,
            log_contents=log_contents,
            log_sink=log_sink
        )

    else:
        raise ValueError(f"❌ 지원하지 않는 generation_mode: {generation_mode}")


    # ========== 6. 종료 처리 ==========
    print("\n🔄 최종 flush 및 리소스 정리 중...")
    log_sink.close()
    db_client.close()

    print("\n" + "=" * 80)
    print("✅ 로그 생성기 종료")
    print("=" * 80)


def run_batch_mode(
    config: dict,
    date_generator: 'LogDateGenerator',
    user_selector: 'UserSelector',
    user_event_controller: 'UserEventController',
    log_contents: 'LogContents',
    log_sink: 'LogSink'
):
    """
    Batch 모드 실행

    실행 흐름:
    1. DateGenerator: 월별 타임스탬프 생성
    2. 각 타임스탬프마다:
       - UserSelector: 유저 선택 (신규/기존) + 현재 상태 확인
       - UserEventController: 상태 기반 다음 액션(로그 타입) 결정 + 상태 전이
       - LogContents: 해당 로그 타입의 실제 내용 생성 (DB 조회 포함)
       - LogSink: 로그 출력 (MPS 제어 포함)
    """
    target_months = config["global"]["target_months"]
    target_mps = config["global"]["target_mps"]
    sleep_interval = 1.0 / target_mps if target_mps > 0 else 0

    # DAU 및 1인당 로그 발생 수
    dau = config["date_generator"]["dau"]
    logs_per_user_per_day = config["date_generator"]["logs_per_user_per_day"]

    for month in target_months:
        print("\n" + "=" * 80)
        print(f"📅 {month} 로그 생성 시작")
        print("=" * 80 + "\n")

        # 총 로그 개수 계산
        total_logs = date_generator.calculate_total_logs(
            target_month=month,
            dau=dau,
            logs_per_user_per_day=logs_per_user_per_day
        )

        print(f"📊 총 로그 개수: {total_logs:,}")
        print(f"👥 DAU: {dau:,}")
        print(f"📈 1인당 일일 로그: {logs_per_user_per_day}개\n")

        # ===== 실행 =====
        log_count = 0
        start_time = time.time()

        # Stage 1: 타임스탬프 생성
        timestamps = date_generator.generate_timestamps(month, total_logs)

        # Stage 2-5: 각 타임스탬프 처리
        for timestamp in timestamps:
            # Stage 2: 유저 선택 (신규/기존 + 현재 상태)
            user, current_state = user_selector.select_user(timestamp)

            # Stage 3: 상태 기반 다음 액션 결정 + 상태 전이
            event_type, next_state = user_event_controller.decide_next_event(
                user=user,
                current_state=current_state
            )

            # Stage 4: 로그 내용 생성 (DB 조회 포함)
            log_event = log_contents.generate(
                user=user,
                event_type=event_type,
                timestamp=timestamp
            )

            # 상태 업데이트
            user_selector.update_user_state(user, next_state)

            # Stage 5: 로그 출력
            if log_event:
                log_sink.write(log_event)
                log_count += 1

            # MPS 제어
            if sleep_interval > 0:
                time.sleep(sleep_interval)

            # 진행 상황 출력
            if log_count % 1000 == 0:
                elapsed = time.time() - start_time
                progress = (log_count / total_logs) * 100
                current_mps = log_count / elapsed if elapsed > 0 else 0
                print(f"   진행: {log_count:,}/{total_logs:,} ({progress:.2f}%) | "
                      f"경과: {elapsed:.1f}초 | MPS: {current_mps:.1f}")

        # 월별 완료
        total_elapsed = time.time() - start_time
        print(f"\n✅ {month} 로그 생성 완료!")
        print(f"   총 로그: {log_count:,}개")
        print(f"   목표: {total_logs:,}개")
        print(f"   달성률: {(log_count / total_logs * 100):.2f}%")
        print(f"   소요 시간: {total_elapsed:.1f}초")
        if total_elapsed > 0:
            print(f"   평균 MPS: {log_count / total_elapsed:.1f}")




def run_streaming_mode(
    config: dict,
    date_generator: 'LogDateGenerator',
    user_selector: 'UserSelector',
    user_event_controller: 'UserEventController',
    log_contents: 'LogContents',
    log_sink: 'LogSink'
):
    """
    Streaming 모드 실행

    실행 흐름:
    1. DateGenerator: 현재 시간 반환
    2. 각 루프마다:
       - UserSelector: 유저 선택 (신규/기존) + 현재 상태 확인
       - UserEventController: 상태 기반 다음 액션 결정 + 상태 전이
       - LogContents: 로그 내용 생성
       - LogSink: 로그 출력 (MPS 제어 포함)
    """
    target_mps = config["global"]["target_mps"]
    sleep_interval = 1.0 / target_mps if target_mps > 0 else 0

    print(f"\n🌊 Streaming 모드")
    print(f"⚠️  종료하려면 Ctrl+C를 누르세요\n")

    log_count = 0
    start_time = time.time()

    try:
        while True:
            # Stage 1: 현재 타임스탬프
            timestamp = date_generator.generate_now()

            # Stage 2: 유저 선택
            user, current_state = user_selector.select_user(timestamp)

            # Stage 3: 상태 기반 다음 액션 결정
            event_type, next_state = user_event_controller.decide_next_event(
                user=user,
                current_state=current_state
            )

            # Stage 4: 로그 내용 생성
            log_event = log_contents.generate(
                user=user,
                event_type=event_type,
                timestamp=timestamp
            )

            # 상태 업데이트
            user_selector.update_user_state(user, next_state)

            # Stage 5: 로그 출력
            if log_event:
                log_sink.write(log_event)
                log_count += 1

            # MPS 제어
            if sleep_interval > 0:
                time.sleep(sleep_interval)

            # 진행 상황 출력
            if log_count % 100 == 0:
                elapsed = time.time() - start_time
                current_mps = log_count / elapsed if elapsed > 0 else 0
                print(f"   총 로그: {log_count:,}개 | 현재 MPS: {current_mps:.1f}")

    except KeyboardInterrupt:
        print("\n⚠️  사용자에 의해 중단됨")
        total_elapsed = time.time() - start_time
        print(f"   총 로그: {log_count:,}개")
        print(f"   소요 시간: {total_elapsed:.1f}초")
        if total_elapsed > 0:
            print(f"   평균 MPS: {log_count / total_elapsed:.1f}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()