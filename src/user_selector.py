import random
from datetime import datetime, date
from typing import Tuple, Optional, List
from schemas.enum import UserState, ActivityLevel
from src.db_client import DBClient


class User:
    """
    유저 객체

    책임:
    - 유저 정보 저장
    - 현재 상태 관리
    - 활성도 등급 관리
    """
    def __init__(
        self,
        user_id: int,
        is_subscribed: bool,
        current_state: UserState = UserState.MAIN_PAGE,
        current_content_id: Optional[str] = None,
        current_episode_id: Optional[str] = None,
        activity_level: Optional[ActivityLevel] = None
    ):
        self.user_id = user_id
        self.is_subscribed = is_subscribed
        self.current_state = current_state

        # 현재 시청 중인 콘텐츠 정보
        self.current_content_id = current_content_id
        self.current_episode_id = current_episode_id

        # 활성도 등급 (추가)
        self.activity_level = activity_level

        # 오늘 처음 로그인 여부 (일별 로드 시 False로 초기화됨)
        self.has_logged_in_today = False

        # 패턴 재생 중 차단 시간 (contents-start 패턴 재생 중에는 다른 이벤트 발생 방지)
        self.blocked_until: Optional[datetime] = None


class UserSelector:
    """
    유저 선택 및 상태 관리

    책임:
    - config.toml의 DAU 기반으로 일별 유저 선정
    - 유저 선정 시 신규/기존 결정 및 상태값 부여
    - UserEventController로부터 받은 상태값으로 유저 상태 업데이트
    """

    def __init__(self, config: dict, db_client: 'DBClient'):
        """
        Args:
            config: config.toml 전체 dict
            db_client: DB 작업용 클라이언트
        """
        self.config = config
        self.db_client = db_client

        # DAU (Daily Active Users)
        self.dau = config["date_generator"]["dau"]

        # 당일 활성 유저 풀 (매일 초기화)
        # key: user_id, value: User 객체
        self.daily_users: dict[int, User] = {}
        self.current_date: Optional[date] = None

        # 신규 유저 생성 비율 (config에서 읽거나 기본값: 5%)
        self.new_user_ratio = config.get("user", {}).get("new_user_ratio", 0.03)

        print(f"✅ UserSelector 초기화 완료")
        print(f"   DAU: {self.dau}")
        print(f"   신규 유저 비율: {self.new_user_ratio * 100:.1f}%")


    def select_user(self, timestamp: datetime) -> Tuple[User, UserState]:
        """
        유저 선택 (DAU 기반) + 현재 상태 반환

        Args:
            timestamp: 현재 타임스탬프

        Returns:
            (User 객체, 현재 상태)

        로직:
        1. 날짜가 바뀌면 daily_users 풀 재설정 (DB에서 DAU만큼 랜덤 선택)
        2. daily_users 풀에서 랜덤 선택
        3. 신규 유저 생성 확률 적용:
           - 신규 유저: DB에 생성 + MAIN_PAGE 상태로 시작
           - 기존 유저: daily_users에서 선택 + 현재 상태 반환
        """
        target_date = timestamp.date()  # 오늘날짜 = target_date로 선언(2025-12-15)


        # 초기 오늘 날짜와 다르므로 daily_users 첫 생성 + 날짜가 바뀌면 daily_users 재설정
        if self.current_date != target_date:
            self._load_daily_users(target_date)
            self.current_date = target_date

        # 신규 유저 생성 여부 결정
        if random.random() < self.new_user_ratio:
            # 신규 유저 생성
            user = self._create_new_user(signup_date=target_date)
            return user, UserState.MAIN_PAGE

        else:  # daily_users 풀에서 랜덤 선택


            #DB에 user가 비어있는 경우, self.daily_users가 비어져있을 경우
            if not self.daily_users:
                # daily_users가 비어있으면 신규 생성
                user = self._create_new_user(signup_date=target_date)
                return user, UserState.MAIN_PAGE

            # blocked_until이 설정되지 않았거나 이미 지난 유저만 선택 가능
            available_users = {
                uid: u for uid, u in self.daily_users.items()
                if u.blocked_until is None or u.blocked_until <= timestamp
            }

            # 선택 가능한 유저가 없으면 신규 생성
            if not available_users:
                user = self._create_new_user(signup_date=target_date)
                return user, UserState.MAIN_PAGE

            # 여기서 available_users 풀에서 랜덤 선택
            user_id = random.choice(list(available_users.keys()))
            user = available_users[user_id]
            return user, user.current_state
            # user객체, 인스턴스 상태값


    def update_user_state(self, user: User, next_state: UserState):
        """
        유저 상태 업데이트

        Args:
            user: User 객체
            next_state: 다음 상태
        """
        user.current_state = next_state

        # USER_OUT 상태면 daily_users 풀에서 제거
        if next_state == UserState.USER_OUT:
            if user.user_id in self.daily_users:
                del self.daily_users[user.user_id]
        else:
            # 그 외 상태면 daily_users 풀에 추가/업데이트
            self.daily_users[user.user_id] = user


    def _load_daily_users(self, target_date: date):
        """
        일별 활성 유저 로드 (DB에서 DAU만큼 랜덤 선택)

        Args:
            target_date: 대상 날짜

        로직:
        1. daily_users 풀 초기화
        2. DB에서 DAU만큼 유저 랜덤 조회
        3. User 객체 생성 후 daily_users에 추가
        """
        print(f"\n📅 {target_date} 일별 유저 로드 중...")

        # 풀 초기화
        self.daily_users.clear()

        # DB에서 DAU만큼 랜덤 유저 가져오기
        users_data = self.db_client.get_random_users(limit=self.dau)
        # [ {'user_id': 10231, 'is_subscribed': 1}, 
        #   {'user_id': 48752, 'is_subscribed': 0}, 
        #   {'user_id': 33109, 'is_subscribed': 1}...  ]

        if not users_data:
            print(f"⚠️  DB에 유저가 없습니다. 신규 유저를 생성합니다.")
            return

        # User 객체 생성 및 daily_users에 추가
        # 일별 로드 시 모든 유저는 NOT_LOGGED_IN 상태로 시작
        for user_data in users_data:
            user = User(
                user_id=user_data["user_id"],
                is_subscribed=user_data["is_subscribed"],
                current_state=UserState.NOT_LOGGED_IN,  # 로그인 전 상태로 시작
                activity_level=self._assign_activity_level()
            )
            user.has_logged_in_today = False  # 오늘 아직 로그인 안함
            self.daily_users[user.user_id] = user

        print(f"✅ {len(self.daily_users)}명의 유저 로드 완료")



    def _create_new_user(self, signup_date: Optional[date] = None) -> User:
        """신규 유저 생성 (DB에 INSERT)"""
        user_id = self.db_client.create_new_user(signup_date=signup_date)

        user = User(
            user_id=user_id,
            is_subscribed=False,
            current_state=UserState.NOT_LOGGED_IN,  # 로그인 전 상태로 시작
            activity_level=self._assign_activity_level()
        )
        user.has_logged_in_today = False  # 신규 유저도 아직 로그인 안함

        self.daily_users[user_id] = user
        return user
    

    
    def _assign_activity_level(self) -> ActivityLevel:
        """
        활성도 등급 할당 (확률 기반)

        Returns:
            ActivityLevel enum
        """
        activity_config = self.config.get("user_activity", {})
        high_ratio = activity_config.get("high_ratio", 0.20)
        medium_ratio = activity_config.get("medium_ratio", 0.50)
        low_ratio = activity_config.get("low_ratio", 0.30)
        
        levels = [ActivityLevel.HIGH, ActivityLevel.MEDIUM, ActivityLevel.LOW]
        weights = [high_ratio, medium_ratio, low_ratio]
        
        return random.choices(levels, weights=weights)[0]