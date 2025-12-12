import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from schemas import (
    LogEvent,
    Platform,
    ContentsType,
    TrafficSource,
    ReasonType,
    InquiryType,
    UserActivityLevel
)
from src.db_client import DBClient
from src.log_events import LogEventFactory
from src.user_register import UserRegister


class UserController:
    """
    유저 행동 제어 및 로그 생성
    
    책임:
    - 유저 상태 머신 (subscribed/non_subscribed)
    - 활동 레벨별 행동 빈도 조정
    - 확률 기반 행동 선택
    - 행동별 로그 시퀀스 생성
    """
    
    def __init__(
        self,
        user_id: int,
        activity_level: UserActivityLevel,
        db_client: DBClient,
        log_factory: LogEventFactory,
        user_register: UserRegister,
        config: dict
    ):
        """
        Args:
            user_id: 유저 ID
            activity_level: 활동 레벨 (HIGH/MEDIUM/LOW)
            db_client: DBClient 인스턴스
            log_factory: LogEventFactory 인스턴스
            user_register: UserRegister 인스턴스
            config: config.toml 딕셔너리
        """
        self.user_id = user_id
        self.activity_level = activity_level
        self.db_client = db_client
        self.log_factory = log_factory
        self.user_register = user_register
        self.config = config
        
        # 활동 레벨별 배율 가져오기
        level_name = activity_level.name.lower()  # "HIGH" → "high"
        level_config = config["user"]["activity_levels"][level_name]
        
        self.log_frequency_multiplier = level_config["log_frequency_multiplier"]
        self.watching_time_multiplier = level_config["watching_time_multiplier"]
        
        # 플랫폼 선택 (유저당 고정)
        self.platform = random.choice(list(Platform))
        
        # 상태 확률
        self.state_probs = config["state_probabilities"]
    
    def get_current_state(self) -> str:
        """
        현재 유저 상태 확인
        
        Returns:
            "subscribed" 또는 "non_subscribed"
        """
        subscription_id = self.db_client.get_user_subscription_id(self.user_id)
        return "subscribed" if subscription_id else "non_subscribed"
    
    def select_action(self, current_state: str) -> str:
        """
        확률 기반 행동 선택
        
        Args:
            current_state: "subscribed" 또는 "non_subscribed"
        
        Returns:
            행동 이름 (예: "contents_click", "search", ...)
        """
        probs = self.state_probs[current_state]
        actions = list(probs.keys())
        weights = list(probs.values())
        
        # 활동 레벨에 따라 일부 행동 빈도 조정 (선택적)
        # 여기서는 단순히 확률대로 선택
        selected_action = random.choices(actions, weights=weights, k=1)[0]
        
        return selected_action
    
    def execute_action(
        self,
        timestamp: datetime,
        action: Optional[str] = None
    ) -> List[LogEvent]:
        """
        행동 실행 및 로그 시퀀스 생성
        
        Args:
            timestamp: 로그 시작 타임스탬프
            action: 강제 실행할 행동 (None이면 확률 기반 선택)
        
        Returns:
            로그 이벤트 리스트
        """
        current_state = self.get_current_state()
        
        if action is None:
            action = self.select_action(current_state)
        
        # 행동별 메서드 매핑
        action_handlers = {
            "access_out": self._handle_access_out,
            "contents_click": self._handle_contents_click,
            "subscription_stop": self._handle_subscription_stop,
            "subscription_start": self._handle_subscription_start,
            "register_out": self._handle_register_out,
            "search": self._handle_search,
            "support_inquiry": self._handle_support_inquiry,
        }
        
        handler = action_handlers.get(action)
        if handler:
            return handler(timestamp)
        else:
            # 알 수 없는 행동은 빈 리스트 반환
            print(f"⚠️ 알 수 없는 행동: {action}")
            return []
    
    # ========== 행동별 핸들러 메서드 ==========
    
    def _handle_access_out(self, timestamp: datetime) -> List[LogEvent]:
        """로그아웃"""
        events = []
        
        # access-out
        events.append(self.log_factory.access_out(
            user_id=self.user_id,
            platform=self.platform,
            timestamp=timestamp
        ))
        
        return events
    
    def _handle_contents_click(self, timestamp: datetime) -> List[LogEvent]:
        """
        콘텐츠 클릭 → 시작 → 재생 → 종료 시퀀스
        
        활동 레벨에 따라 시청 시간 조정
        """
        events = []
        current_time = timestamp
        
        # 콘텐츠 선택 (Featured 가중치 적용)
        contents = self.log_factory.select_contents()
        contents_id = contents["content_id"]
        contents_type = ContentsType.TV if contents["type"] == "tv" else ContentsType.MOVIE
        
        # Episode ID (TV 시리즈만)
        episode_id = None
        if contents_type == ContentsType.TV:
            episode_id = f"episode_{random.randint(1, 10)}"
        
        # 1. contents-click
        events.append(self.log_factory.contents_click(
            user_id=self.user_id,
            platform=self.platform,
            contents_id=contents_id,
            contents_type=contents_type,
            timestamp=current_time
        ))
        current_time += timedelta(seconds=random.randint(1, 3))
        
        # 2. contents-start
        events.append(self.log_factory.contents_start(
            user_id=self.user_id,
            platform=self.platform,
            contents_id=contents_id,
            contents_type=contents_type,
            episode_id=episode_id,
            timestamp=current_time
        ))
        current_time += timedelta(seconds=random.randint(1, 2))
        
        # 3. contents-playing (30초마다 발생)
        # 시청 시간: 영화 60~120분, TV 30~60분
        if contents_type == ContentsType.MOVIE:
            base_watch_time = random.randint(60, 120) * 60  # 초 단위
        else:
            base_watch_time = random.randint(30, 60) * 60
        
        # 활동 레벨 배율 적용
        watch_time = int(base_watch_time * self.watching_time_multiplier)
        
        # 30초마다 playing 로그 발생
        playing_interval = 30
        playing_count = watch_time // playing_interval
        
        for _ in range(playing_count):
            events.append(self.log_factory.contents_playing(
                user_id=self.user_id,
                platform=self.platform,
                contents_id=contents_id,
                contents_type=contents_type,
                episode_id=episode_id,
                timestamp=current_time
            ))
            current_time += timedelta(seconds=playing_interval)
        
        # 4. contents-stop
        events.append(self.log_factory.contents_stop(
            user_id=self.user_id,
            platform=self.platform,
            contents_id=contents_id,
            contents_type=contents_type,
            episode_id=episode_id,
            timestamp=current_time
        ))
        
        # 5. (선택) like_on (20% 확률)
        if random.random() < 0.2:
            current_time += timedelta(seconds=random.randint(1, 5))
            events.append(self.log_factory.contents_like_on(
                user_id=self.user_id,
                platform=self.platform,
                contents_id=contents_id,
                contents_type=contents_type,
                timestamp=current_time
            ))
        
        # 6. (선택) review (10% 확률)
        if random.random() < 0.1:
            current_time += timedelta(seconds=random.randint(5, 30))
            events.append(self.log_factory.review_review(
                user_id=self.user_id,
                contents_id=contents_id,
                timestamp=current_time
            ))
        
        return events
    
    def _handle_subscription_stop(self, timestamp: datetime) -> List[LogEvent]:
        """구독 취소"""
        events = []
        
        # 현재 구독 ID 가져오기
        subscription_id = self.db_client.get_user_subscription_id(self.user_id)
        
        if subscription_id:
            # subscription-stop 로그
            events.append(self.log_factory.subscription_stop(
                user_id=self.user_id,
                subscription_id=subscription_id,
                timestamp=timestamp
            ))
            
            # DB 업데이트
            self.db_client.cancel_user_subscription(self.user_id)
        
        return events
    
    def _handle_subscription_start(self, timestamp: datetime) -> List[LogEvent]:
        """구독 시작"""
        events = []
        
        # 랜덤 플랜 선택
        plans = self.db_client._subscription_plans
        plan = random.choice(plans)
        subscription_id = plan["subscription_id"]
        
        # subscription-start 로그
        events.append(self.log_factory.subscription_start(
            user_id=self.user_id,
            subscription_id=subscription_id,
            timestamp=timestamp
        ))
        
        # DB 업데이트
        self.db_client.insert_user_subscription(
            user_id=self.user_id,
            subscription_id=subscription_id,
            start_timestamp=timestamp
        )
        
        return events
    
    def _handle_register_out(self, timestamp: datetime) -> List[LogEvent]:
        """회원 탈퇴"""
        events = []
        
        # 탈퇴 사유 랜덤 선택
        reason_type = random.choice(list(ReasonType))
        
        # register-out 로그
        events.append(self.log_factory.register_out(
            user_id=self.user_id,
            reason_type=reason_type,
            timestamp=timestamp
        ))
        
        # DB 업데이트 (soft delete)
        self.db_client.update_delete_user(self.user_id)
        
        return events
    
    def _handle_search(self, timestamp: datetime) -> List[LogEvent]:
        """검색"""
        events = []
        
        # search-search 로그 (검색어는 랜덤)
        events.append(self.log_factory.search_search(
            user_id=self.user_id,
            timestamp=timestamp
        ))
        
        return events
    
    def _handle_support_inquiry(self, timestamp: datetime) -> List[LogEvent]:
        """고객 문의"""
        events = []
        
        # 문의 유형 랜덤 선택
        inquiry_type = random.choice(list(InquiryType))
        
        # support-inquiry 로그
        events.append(self.log_factory.support_inquiry(
            user_id=self.user_id,
            inquiry_type=inquiry_type,
            timestamp=timestamp
        ))
        
        return events
    
    # ========== 특수 행동 (main.py에서 직접 호출) ==========
    
    def handle_new_user_register(
        self,
        timestamp: datetime,
        traffic_source: Optional[TrafficSource] = None
    ) -> tuple[int, List[LogEvent]]:
        """
        신규 유저 회원가입
        
        Args:
            timestamp: 회원가입 타임스탬프
            traffic_source: 유입 경로 (None이면 랜덤)
        
        Returns:
            (new_user_id, events)
        """
        events = []
        
        # 1. 유저 데이터 생성
        user_data = self.user_register.create_user_data(timestamp)
        
        # 2. DB 삽입
        new_user_id = self.db_client.insert_user(user_data)
        
        # 3. register-in 로그
        if traffic_source is None:
            traffic_source = random.choice(list(TrafficSource))
        
        events.append(self.log_factory.register_in(
            user_id=new_user_id,
            traffic_source=traffic_source,
            timestamp=timestamp
        ))
        
        # 4. access-in 로그 (회원가입 직후 로그인)
        login_time = timestamp + timedelta(seconds=random.randint(1, 3))
        events.append(self.log_factory.access_in(
            user_id=new_user_id,
            platform=self.platform,
            timestamp=login_time
        ))
        
        return new_user_id, events
    
    def handle_access_in(self, timestamp: datetime) -> List[LogEvent]:
        """로그인"""
        events = []
        
        # access-in 로그
        events.append(self.log_factory.access_in(
            user_id=self.user_id,
            platform=self.platform,
            timestamp=timestamp
        ))
        
        # DB 업데이트 (last_login_date)
        self.db_client.update_last_login_date(self.user_id, timestamp)
        
        return events