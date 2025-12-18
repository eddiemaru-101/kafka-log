import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from schemas.enum import (
    ActivityLevel,
    Platform,
    TrafficSource,
    ReasonType,
    InquiryType
)
from db_client import DBClient


class LogContents:
    """
    로그 내용 생성 클래스

    책임:
    - 로그 타입별 로그 내용 생성
    - DB 데이터 조회 (DBClient 사용)
    - 로그 포맷 구성
    - 활성도 등급별 시청시간 계산
    """

    def __init__(self, config: dict, db_client: DBClient):
        """
        Args:
            config: config.toml 전체 dict
            db_client: DB 작업용 클라이언트
        """
        self.config = config
        self.db_client = db_client

        # 활성도 등급별 시청시간 설정
        self.activity_config = config.get("user_activity", {})

        # LogContents 전용 설정
        self.log_contents_config = config.get("log_contents", {})

        # 플랫폼별 비율
        self.platform_ratio = self.log_contents_config.get("platform_ratio", {
            "android": 0.35,
            "ios": 0.30,
            "pc": 0.25,
            "tv": 0.10
        })

        # 확률 설정
        self.review_detail_ratio = self.log_contents_config.get("review_detail_ratio", 0.70)
        self.register_out_detail_ratio = self.log_contents_config.get("register_out_detail_ratio", 0.50)

        # 샘플 데이터
        self.search_terms = self.log_contents_config.get("search_terms", ["해리포터", "어벤져스"])
        self.review_samples = self.log_contents_config.get("review_samples", ["재밌어요", "별로예요"])
        self.register_out_reasons = self.log_contents_config.get("register_out_reasons", ["콘텐츠가 부족해요"])
        self.inquiry_samples = self.log_contents_config.get("inquiry_samples", ["문의합니다"])

        print(f"✅ LogContents 초기화 완료")


    def generate(
        self,
        user,
        event_type: Optional[str],
        timestamp: datetime,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        로그 타입에 따른 로그 내용 생성

        Args:
            user: User 객체
            event_type: 이벤트 타입 (예: "access-in", "contents-start")
            timestamp: 로그 발생 시간
            additional_data: 추가 데이터 (user_controller에서 전달)

        Returns:
            로그 딕셔너리 또는 None (로그 없는 이벤트의 경우)
        """
        if event_type is None:
            return None

        if additional_data is None:
            additional_data = {}

        # event_type 파싱 (category-type)
        parts = event_type.split("-")
        category = parts[0]
        type_name = parts[1] if len(parts) > 1 else ""

        # 카테고리별 로그 생성 메서드 호출
        if category == "access":
            if type_name == "in":
                return self._generate_access_in(user, timestamp)
            elif type_name == "out":
                return self._generate_access_out(user, timestamp)

        elif category == "contents":
            if type_name == "click":
                return self._generate_contents_click(user, timestamp, additional_data)
            elif type_name == "start":
                return self._generate_contents_start(user, timestamp, additional_data)
            elif type_name == "stop":
                return self._generate_contents_stop(user, timestamp, additional_data)
            elif type_name == "pause":
                return self._generate_contents_pause(user, timestamp, additional_data)
            elif type_name == "resume":
                return self._generate_contents_resume(user, timestamp, additional_data)
            elif type_name == "like_on":
                return self._generate_contents_like_on(user, timestamp, additional_data)
            elif type_name == "like_off":
                return self._generate_contents_like_off(user, timestamp, additional_data)

        elif category == "review":
            if type_name == "review":
                return self._generate_review_review(user, timestamp, additional_data)

        elif category == "subscription":
            if type_name == "start":
                return self._generate_subscription_start(user, timestamp)
            elif type_name == "stop":
                return self._generate_subscription_stop(user, timestamp)

        elif category == "register":
            if type_name == "in":
                return self._generate_register_in(user, timestamp)
            elif type_name == "out":
                return self._generate_register_out(user, timestamp, additional_data)

        elif category == "search":
            if type_name == "search":
                return self._generate_search_search(user, timestamp)

        elif category == "support":
            if type_name == "inquiry":
                return self._generate_support_inquiry(user, timestamp)

        return None


    # ========== 플랫폼 랜덤 선택 ==========
    def _get_random_platform(self) -> int:
        """랜덤 플랫폼 선택 (비율 기반)"""
        platforms = [Platform.ANDROID, Platform.IOS, Platform.PC, Platform.TV]
        weights = [
            self.platform_ratio.get("android", 0.35),
            self.platform_ratio.get("ios", 0.30),
            self.platform_ratio.get("pc", 0.25),
            self.platform_ratio.get("tv", 0.10)
        ]
        return random.choices(platforms, weights=weights)[0].value


    # ========== 시청시간 계산 ==========
    def _calculate_watch_duration(self, activity_level: Optional[ActivityLevel]) -> int:
        """
        활성도 등급에 따른 시청시간 계산 (분 단위)

        Args:
            activity_level: 활성도 등급

        Returns:
            시청시간 (분)
        """
        if activity_level is None:
            activity_level = ActivityLevel.MEDIUM

        watch_time_config = self.activity_config.get("watch_time", {})

        if activity_level == ActivityLevel.HIGH:
            avg_minutes = watch_time_config.get("high_avg_minutes", 45)
            noise_range = self.activity_config.get("high_noise", 10)
        elif activity_level == ActivityLevel.MEDIUM:
            avg_minutes = watch_time_config.get("medium_avg_minutes", 25)
            noise_range = self.activity_config.get("medium_noise", 8)
        else:  # LOW
            avg_minutes = watch_time_config.get("low_avg_minutes", 10)
            noise_range = self.activity_config.get("low_noise", 5)

        # noise 추가 (±noise_range)
        noise = random.randint(-noise_range, noise_range)
        duration = max(1, avg_minutes + noise)

        return duration


    # ========== 접속 로그 (access) ==========
    def _generate_access_in(self, user, timestamp: datetime) -> Dict[str, Any]:
        """access-in 로그 생성"""
        return {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 1,  # access
            "event_type": 1,  # in
            "platform": self._get_random_platform()
        }


    def _generate_access_out(self, user, timestamp: datetime) -> Dict[str, Any]:
        """access-out 로그 생성"""
        return {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 1,  # access
            "event_type": 2,  # out
            "platform": self._get_random_platform()
        }


    # ========== 콘텐츠 로그 (contents) ==========
    def _generate_contents_click(
        self,
        user,
        timestamp: datetime,
        additional_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """contents-click 로그 생성"""
        # DB에서 랜덤 콘텐츠 조회
        content = self.db_client.get_random_content()

        if not content:
            # 콘텐츠 없으면 기본값
            content = {
                "content_id": "movie_0",
                "content_type": "movie"
            }

        # User 객체에 콘텐츠 정보 저장
        user.current_content_id = content["content_id"]

        # content_type → TINYINT 변환
        content_type_code = 1 if content["content_type"] == "tv" else 2

        return {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 2,  # contents
            "event_type": 3,  # click
            "platform": self._get_random_platform(),
            "contents_id": content["content_id"],
            "contents_type": content_type_code
        }


    def _generate_contents_start(
        self,
        user,
        timestamp: datetime,
        additional_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """contents-start 로그 생성"""
        content_id = user.current_content_id

        if not content_id:
            # 콘텐츠 없으면 랜덤 조회
            content = self.db_client.get_random_content()
            content_id = content["content_id"] if content else "movie_0"
            user.current_content_id = content_id

        # 콘텐츠 정보 조회
        content = self.db_client.get_content_by_id(content_id)

        if not content:
            content = {"content_type": "movie"}

        content_type_code = 1 if content["content_type"] == "tv" else 2

        # TV 시리즈면 에피소드 ID 필요
        episode_id = None
        if content["content_type"] == "tv":
            episodes = self.db_client.get_episodes_by_content_id(content_id)
            if episodes:
                episode = random.choice(episodes)
                episode_id = episode["episode_id"]
                user.current_episode_id = episode_id

        log = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 2,  # contents
            "event_type": 4,  # start
            "platform": self._get_random_platform(),
            "contents_id": content_id,
            "contents_type": content_type_code
        }

        if episode_id:
            log["episode_id"] = episode_id

        return log


    def _generate_contents_stop(
        self,
        user,
        timestamp: datetime,
        additional_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """contents-stop 로그 생성"""
        content_id = user.current_content_id or "movie_0"
        episode_id = user.current_episode_id

        # 콘텐츠 정보 조회
        content = self.db_client.get_content_by_id(content_id)
        if not content:
            content = {"content_type": "movie"}

        content_type_code = 1 if content["content_type"] == "tv" else 2

        log = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 2,  # contents
            "event_type": 5,  # stop
            "platform": self._get_random_platform(),
            "contents_id": content_id,
            "contents_type": content_type_code
        }

        if episode_id:
            log["episode_id"] = episode_id

        return log


    def _generate_contents_pause(
        self,
        user,
        timestamp: datetime,
        additional_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """contents-pause 로그 생성"""
        content_id = user.current_content_id or "movie_0"
        episode_id = user.current_episode_id

        content = self.db_client.get_content_by_id(content_id)
        if not content:
            content = {"content_type": "movie"}

        content_type_code = 1 if content["content_type"] == "tv" else 2

        log = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 2,  # contents
            "event_type": 6,  # pause
            "platform": self._get_random_platform(),
            "contents_id": content_id,
            "contents_type": content_type_code
        }

        if episode_id:
            log["episode_id"] = episode_id

        return log


    def _generate_contents_resume(
        self,
        user,
        timestamp: datetime,
        additional_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """contents-resume 로그 생성"""
        content_id = user.current_content_id or "movie_0"
        episode_id = user.current_episode_id

        content = self.db_client.get_content_by_id(content_id)
        if not content:
            content = {"content_type": "movie"}

        content_type_code = 1 if content["content_type"] == "tv" else 2

        log = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 2,  # contents
            "event_type": 7,  # resume
            "platform": self._get_random_platform(),
            "contents_id": content_id,
            "contents_type": content_type_code
        }

        if episode_id:
            log["episode_id"] = episode_id

        return log


    def _generate_contents_like_on(
        self,
        user,
        timestamp: datetime,
        additional_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """contents-like_on 로그 생성"""
        content_id = user.current_content_id or "movie_0"

        content = self.db_client.get_content_by_id(content_id)
        if not content:
            content = {"content_type": "movie"}

        content_type_code = 1 if content["content_type"] == "tv" else 2

        return {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 2,  # contents
            "event_type": 8,  # like_on
            "contents_id": content_id,
            "contents_type": content_type_code
        }


    def _generate_contents_like_off(
        self,
        user,
        timestamp: datetime,
        additional_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """contents-like_off 로그 생성"""
        content_id = user.current_content_id or "movie_0"

        content = self.db_client.get_content_by_id(content_id)
        if not content:
            content = {"content_type": "movie"}

        content_type_code = 1 if content["content_type"] == "tv" else 2

        return {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 2,  # contents
            "event_type": 9,  # like_off
            "contents_id": content_id,
            "contents_type": content_type_code
        }


    # ========== 리뷰 로그 (review) ==========
    def _generate_review_review(
        self,
        user,
        timestamp: datetime,
        additional_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """review-review 로그 생성"""
        content_id = user.current_content_id or "movie_0"

        # 평점: 0.5 단위 (0.5 ~ 5.0)
        rating = round(random.uniform(0.5, 5.0) * 2) / 2

        # 리뷰 내용 (config의 review_detail_ratio 확률로 작성)
        review_detail = None
        if random.random() < self.review_detail_ratio:
            review_detail = random.choice(self.review_samples)

        log = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 3,  # review
            "event_type": 10,  # review
            "contents_id": content_id,
            "rating": rating
        }

        if review_detail:
            log["review_detail"] = review_detail

        return log


    # ========== 구독 로그 (subscription) ==========
    def _generate_subscription_start(self, user, timestamp: datetime) -> Dict[str, Any]:
        """subscription-start 로그 생성"""
        # DB에서 랜덤 구독 상품 조회
        subscription = self.db_client.get_random_subscription()

        if not subscription:
            subscription = {"subscription_id": "s_1"}

        return {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 4,  # subscription
            "event_type": 4,  # start
            "subscription_id": subscription["subscription_id"]
        }


    def _generate_subscription_stop(self, user, timestamp: datetime) -> Dict[str, Any]:
        """subscription-stop 로그 생성"""
        # 임의의 구독 상품 ID (실제로는 유저의 현재 구독 조회 필요)
        subscription = self.db_client.get_random_subscription()

        if not subscription:
            subscription = {"subscription_id": "s_1"}

        return {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 4,  # subscription
            "event_type": 5,  # stop
            "subscription_id": subscription["subscription_id"]
        }


    # ========== 회원 로그 (register) ==========
    def _generate_register_in(self, user, timestamp: datetime) -> Dict[str, Any]:
        """register-in 로그 생성"""
        # 유입 경로 랜덤 선택
        traffic_sources = [
            TrafficSource.SEARCH,
            TrafficSource.SOCIAL,
            TrafficSource.AD_SEARCH,
            TrafficSource.AD_SOCIAL,
            TrafficSource.REFERRAL,
            TrafficSource.MISC
        ]
        traffic_source = random.choice(traffic_sources).value

        return {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 5,  # register
            "event_type": 1,  # in
            "traffic_source": traffic_source
        }


    def _generate_register_out(
        self,
        user,
        timestamp: datetime,
        additional_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """register-out 로그 생성"""
        # 탈퇴 이유 타입 랜덤 선택
        reason_types = [ReasonType.CONTENTS, ReasonType.CHARGE, ReasonType.MISC]
        reason_type = random.choice(reason_types).value

        # 탈퇴 이유 상세 (config의 register_out_detail_ratio 확률로 작성)
        reason_detail = None
        if random.random() < self.register_out_detail_ratio:
            reason_detail = random.choice(self.register_out_reasons)

        log = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 5,  # register
            "event_type": 2,  # out
            "reason_type": reason_type
        }

        if reason_detail:
            log["reason_detail"] = reason_detail

        return log


    # ========== 검색 로그 (search) ==========
    def _generate_search_search(self, user, timestamp: datetime) -> Dict[str, Any]:
        """search-search 로그 생성"""
        # 검색어 후보 (config에서 읽기)
        term = random.choice(self.search_terms)

        return {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 6,  # search
            "event_type": 11,  # search
            "term": term
        }


    # ========== 고객센터 로그 (support) ==========
    def _generate_support_inquiry(self, user, timestamp: datetime) -> Dict[str, Any]:
        """support-inquiry 로그 생성"""
        # 문의 타입 랜덤 선택
        inquiry_types = [
            InquiryType.CONTENTS,
            InquiryType.REFUND,
            InquiryType.SUBSCRIPTION,
            InquiryType.INFORMATION
        ]
        inquiry_type = random.choice(inquiry_types).value

        # 문의 내용 (config에서 읽기)
        inquiry_detail = random.choice(self.inquiry_samples)

        return {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 7,  # support
            "event_type": 12,  # inquiry
            "inquiry_type": inquiry_type,
            "inquiry_detail": inquiry_detail
        }
