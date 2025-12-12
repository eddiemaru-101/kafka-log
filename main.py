import time
import random
import toml
from datetime import datetime

from schemas import UserActivityLevel
from src.db_client import DBClient
from src.log_events import LogEventFactory
from src.log_sink import LogSink
from src.log_date_generator import LogDateGenerator
from src.user_register import UserRegister
from src.user_controller import UserController


def main():
    """
    로그 생성기 메인 실행 함수
    
    실행 흐름:
    1. Config 로딩
    2. 모듈 초기화
    3. 월별 루프
    4. 타임스탬프별 로그 생성
    5. MPS 제어
    6. 리소스 정리
    """
    
    print("=" * 60)
    print("🚀 Ver02 로그 생성기 시작")
    print("=" * 60)
    
    # ========== 1. Config 로딩 ==========
    config_path = "config/config.toml"
    config = toml.load(config_path)
    print(f"\n✅ Config 로딩 완료: {config_path}")
    
    # ========== 2. 모듈 초기화 ==========
    print("\n" + "=" * 60)
    print("📦 모듈 초기화 중...")
    print("=" * 60 + "\n")
    
    # 변경 후
    db_client = DBClient(config)
    log_factory = LogEventFactory(config, db_client.get_all_contents())
    log_sink = LogSink(config)
    date_generator = LogDateGenerator(config)
    user_register = UserRegister(config)
    
    # ========== 3. 활동 레벨 분포 ==========
    activity_level_ratios = {
        UserActivityLevel.HIGH: config["user"]["activity_levels"]["high"]["ratio"],
        UserActivityLevel.MEDIUM: config["user"]["activity_levels"]["medium"]["ratio"],
        UserActivityLevel.LOW: config["user"]["activity_levels"]["low"]["ratio"]
    }
    
    activity_levels = list(activity_level_ratios.keys())
    activity_weights = list(activity_level_ratios.values())
    
    print(f"\n✅ 활동 레벨 분포: HIGH={activity_weights[0]}, MEDIUM={activity_weights[1]}, LOW={activity_weights[2]}")
    
    # ========== 4. 신규 유저 생성 비율 ==========
    new_user_ratio = config["user"]["new_user_ratio"]
    print(f"✅ 신규 유저 생성 비율: {new_user_ratio * 100}%")
    
    # ========== 5. MPS 설정 ==========
    target_mps = config["global"]["target_mps"]
    print(f"✅ Target MPS: {target_mps}")
    
    # MPS 제어용 (간단한 sleep 방식)
    # 실제로는 배치 단위로 처리하지만, 여기서는 개별 로그 기준
    sleep_interval = 1.0 / target_mps if target_mps > 0 else 0
    
    # ========== 6. 월별 로그 생성 ==========
    target_months = config["global"]["target_months"]
    
    for month in target_months:
        print("\n" + "=" * 60)
        print(f"📅 {month} 로그 생성 시작")
        print("=" * 60 + "\n")
        
        # 해당 월의 총 로그 개수 계산
        active_user_count = len(db_client._active_users)
        total_logs = date_generator.get_total_logs_for_month(
            target_month=month,
            mps=target_mps,
            active_user_count=active_user_count
        )
        
        print(f"📊 예상 총 로그 개수: {total_logs:,}")
        print(f"👥 활성 유저 수: {active_user_count:,}\n")
        
        # 타임스탬프 생성
        timestamp_generator = date_generator.generate_timestamps(month, total_logs)
        
        # 진행 상황 추적
        log_count = 0
        start_time = time.time()
        
        # 타임스탬프별 로그 생성
        for timestamp in timestamp_generator:
            log_count += 1
            
            # 신규 유저 생성 여부 결정
            if random.random() < new_user_ratio:
                # 신규 유저 회원가입
                activity_level = random.choices(activity_levels, weights=activity_weights)[0]
                
                # UserController 생성 (임시, 회원가입 전용)
                temp_controller = UserController(
                    user_id=0,  # 임시 ID
                    activity_level=activity_level,
                    db_client=db_client,
                    log_factory=log_factory,
                    user_register=user_register,
                    config=config
                )
                
                new_user_id, events = temp_controller.handle_new_user_register(timestamp)
                log_sink.write_batch(events)
                
                # 신규 유저를 캐시에 추가 (선택적, DB에서 다시 로딩하려면 _load_initial_data 호출)
                # 여기서는 단순화를 위해 스킵
                
            else:
                # 기존 유저 선택
                user = db_client.get_random_user()
                user_id = user["user_id"]
                
                # 활동 레벨 할당 (매번 랜덤)
                activity_level = random.choices(activity_levels, weights=activity_weights)[0]
                
                # UserController 생성
                controller = UserController(
                    user_id=user_id,
                    activity_level=activity_level,
                    db_client=db_client,
                    log_factory=log_factory,
                    user_register=user_register,
                    config=config
                )
                
                # 로그인 처리 (50% 확률로 access-in 발생)
                if random.random() < 0.5:
                    events = controller.handle_access_in(timestamp)
                    log_sink.write_batch(events)
                
                # 행동 실행
                events = controller.execute_action(timestamp)
                
                # 로그 출력
                if events:
                    log_sink.write_batch(events)
            
            # MPS 제어 (sleep)
            if sleep_interval > 0:
                time.sleep(sleep_interval)
            
            # 진행 상황 출력 (1000개마다)
            if log_count % 1000 == 0:
                elapsed = time.time() - start_time
                progress = (log_count / total_logs) * 100
                print(f"   진행: {log_count:,}/{total_logs:,} ({progress:.2f}%) | 경과 시간: {elapsed:.1f}초")
        
        # 월별 완료
        total_elapsed = time.time() - start_time
        print(f"\n✅ {month} 로그 생성 완료!")
        print(f"   총 로그: {log_count:,}개")
        print(f"   소요 시간: {total_elapsed:.1f}초")
        print(f"   평균 처리 속도: {log_count / total_elapsed:.1f} logs/sec")
    
    # ========== 7. 최종 flush 및 종료 ==========
    print("\n" + "=" * 60)
    print("🔄 최종 flush 및 리소스 정리 중...")
    print("=" * 60 + "\n")
    
    log_sink.close()
    
    print("\n" + "=" * 60)
    print("✅ 로그 생성기 종료")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()