import random
from datetime import datetime, date
from typing import Tuple, Optional, List
from enum import Enum


class UserState(Enum):
    """
    유저 상태 (가이드 문서 기반)
    """
    MAIN_PAGE = "MAIN_PAGE"          # 메인 페이지
    CONTENT_PAGE = "CONTENT_PAGE"    # 콘텐츠 상세 페이지
    IN_START = "IN_START"            # 재생 시작 직후
    IN_PLAYING = "IN_PLAYING"        # 재생 중
    IN_PAUSE = "IN_PAUSE"            # 일시정지
    USER_OUT = "USER_OUT"            # 로그아웃/세션 종료


class User:
    """
    유저 객체

    책임:
    - 유저 정보 저장
    - 현재 상태 관리
    """
    def __init__(
        self,
        user_id: int,
        is_subscribed: bool,
        current_state: UserState = UserState.MAIN_PAGE,
        current_content_id: Optional[str] = None,
        current_episode_id: Optional[str] = None
    ):
        self.user_id = user_id
        self.is_subscribed = is_subscribed
        self.current_state = current_state

        # 현재 시청 중인 콘텐츠 정보 (IN_START, IN_PLAYING, IN_PAUSE 상태에서 사용)
        self.current_content_id = current_content_id
        self.current_episode_id = current_episode_id


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
        self.new_user_ratio = config.get("user", {}).get("new_user_ratio", 0.05)

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
        target_date = timestamp.date()


        # 날짜가 바뀌면 daily_users 재설정
        if self.current_date != target_date:
            self._load_daily_users(target_date)
            self.current_date = target_date

        # 신규 유저 생성 여부 결정
        if random.random() < self.new_user_ratio:
            # 신규 유저 생성
            user = self._create_new_user()
            return user, UserState.MAIN_PAGE

        else:
            # daily_users 풀에서 랜덤 선택
            if not self.daily_users:
                # daily_users가 비어있으면 신규 생성
                user = self._create_new_user()
                return user, UserState.MAIN_PAGE

            user_id = random.choice(list(self.daily_users.keys()))
            user = self.daily_users[user_id]
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

        if not users_data:
            print(f"⚠️  DB에 유저가 없습니다. 신규 유저를 생성합니다.")
            return

        # User 객체 생성 및 daily_users에 추가
        for user_data in users_data:
            user = User(
                user_id=user_data["user_id"],
                is_subscribed=user_data["is_subscribed"],
                current_state=UserState.MAIN_PAGE  # 초기 진입 시 MAIN_PAGE
            )
            self.daily_users[user.user_id] = user

        print(f"✅ {len(self.daily_users)}명의 유저 로드 완료")


    def _create_new_user(self) -> User:
        """
        신규 유저 생성 (DB에 INSERT)

        Returns:
            새로 생성된 User 객체
        """
        # DB에 신규 유저 생성 (register-in 로그 발생 전에 먼저 생성)
        user_id = self.db_client.create_new_user()

        # User 객체 생성
        user = User(
            user_id=user_id,
            is_subscribed=False,  # 신규 유저는 비구독자
            current_state=UserState.MAIN_PAGE
        )

        # daily_users 풀에 추가
        self.daily_users[user_id] = user

        return user