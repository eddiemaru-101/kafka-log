import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from schemas.enum import (
    ActivityLevel,
    Platform,
    TrafficSource,
    ReasonType,
    InquiryType
)
from src.db_client import DBClient


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

        # 시청 패턴 확률 설정
        self.watch_pattern_prob = self.log_contents_config.get("watch_pattern_probability", {
            "play_stop": 0.15,
            "play_pause_stop": 0.25,
            "play_pause_resume_stop": 0.50,
            "play_pause_resume_pause_stop": 0.10
        })

        # 구독 상품 타입별 선택 비율
        self.subscription_type_ratio = self.log_contents_config.get("subscription_type_ratio", {
            "standard": 0.40,
            "premium": 0.25,
            "family": 0.20,
            "mobile_only": 0.15
        })

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
    ) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """
        로그 타입에 따른 로그 내용 생성

        Args:
            user: User 객체
            event_type: 이벤트 타입 (예: "access-in", "contents-start")
            timestamp: 로그 발생 시간
            additional_data: 추가 데이터 (user_controller에서 전달)

        Returns:
            로그 딕셔너리, 로그 리스트, 또는 None (로그 없는 이벤트의 경우)
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
                # contents-start는 패턴에 따라 여러 로그를 생성 (Play, Pause, Resume, Stop)
                # 리스트로 반환하여 main.py에서 순차적으로 sink에 전달
                logs = self._generate_contents_pattern(user, timestamp, additional_data)
                return logs  # 리스트 반환 (2~5개 로그)
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
            "detail": {
                "platform": self._get_random_platform()
            }
        }


    def _generate_access_out(self, user, timestamp: datetime) -> Dict[str, Any]:
        """access-out 로그 생성"""
        # 로그아웃 시 플래그 리셋 (같은 날 재로그인 시 access-in 발생 가능하도록)
        if hasattr(user, 'has_logged_in_today'):
            user.has_logged_in_today = False

        return {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 1,  # access
            "event_type": 2,  # out
            "detail": {
                "platform": self._get_random_platform()
            }
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
                "contents_id": "movie_0",
                "contents_type": "movie"
            }

        # User 객체에 콘텐츠 정보 저장
        user.current_content_id = content["contents_id"]

        # content_type → TINYINT 변환
        content_type_code = 1 if content["contents_type"] == "tv" else 2

        return {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 2,  # contents
            "event_type": 3,  # click
            "detail": {
                "platform": self._get_random_platform(),
                "contents_id": content["contents_id"],
                "contents_type": content_type_code
            }
        }


    def _generate_contents_pattern(
        self,
        user,
        timestamp: datetime,
        additional_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        contents-start 발생 시 패턴에 따라 여러 로그를 한 번에 생성

        Returns:
            로그 딕셔너리 리스트
        """
        logs = []

        # 1. 패턴 타입 랜덤 선택
        pattern_types = list(self.watch_pattern_prob.keys())
        pattern_weights = list(self.watch_pattern_prob.values())
        selected_pattern = random.choices(pattern_types, weights=pattern_weights)[0]

        # 2. 활성도 등급에 따른 총 시청시간 계산 (분 단위)
        total_watch_minutes = self._calculate_watch_duration(user.activity_level)

        # 3. 콘텐츠 정보 가져오기
        content_id = user.current_content_id
        if not content_id:
            content = self.db_client.get_random_content()
            content_id = content["contents_id"] if content else "movie_0"
            user.current_content_id = content_id

        content = self.db_client.get_content_by_id(content_id)
        if not content:
            content = {"contents_type": "movie"}

        content_type_code = 1 if content["contents_type"] == "tv" else 2

        # TV 시리즈면 에피소드 ID
        episode_id = None
        if content["contents_type"] == "tv":
            episodes = self.db_client.get_episodes_by_content_id(content_id)
            if episodes:
                episode = random.choice(episodes)
                episode_id = episode["episode_id"]
                user.current_episode_id = episode_id

        # 4. 패턴에 따라 로그 생성
        current_time = timestamp
        platform = self._get_random_platform()

        # Play (contents-start) 로그
        detail = {
            "platform": platform,
            "contents_id": content_id,
            "contents_type": content_type_code
        }
        if episode_id:
            detail["episode_id"] = episode_id

        play_log = {
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 2,
            "event_type": 4,  # start
            "detail": detail
        }
        logs.append(play_log)

        # 패턴별 로그 생성 및 시간 할당
        if selected_pattern == "play_stop":
            # Play → stop (즉시 이탈)
            current_time += timedelta(minutes=total_watch_minutes)

        elif selected_pattern == "play_pause_stop":
            # Play → Pause → stop (중단 이탈)
            pause_time = total_watch_minutes * random.uniform(0.3, 0.7)
            current_time += timedelta(minutes=pause_time)

            pause_detail = {
                "platform": platform,
                "contents_id": content_id,
                "contents_type": content_type_code
            }
            if episode_id:
                pause_detail["episode_id"] = episode_id

            pause_log = {
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "user_id": user.user_id,
                "event_category": 2,
                "event_type": 6,  # pause
                "detail": pause_detail
            }
            logs.append(pause_log)

            # 일시정지 후 대기 시간
            current_time += timedelta(minutes=total_watch_minutes - pause_time)

        elif selected_pattern == "play_pause_resume_stop":
            # Play → Pause → Resume → stop (정상 시청)
            pause_time = total_watch_minutes * random.uniform(0.2, 0.4)
            current_time += timedelta(minutes=pause_time)

            # Pause 로그
            pause_detail = {
                "platform": platform,
                "contents_id": content_id,
                "contents_type": content_type_code
            }
            if episode_id:
                pause_detail["episode_id"] = episode_id

            pause_log = {
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "user_id": user.user_id,
                "event_category": 2,
                "event_type": 6,  # pause
                "detail": pause_detail
            }
            logs.append(pause_log)

            # 일시정지 대기 시간 (1-5분)
            wait_time = random.uniform(1, 5)
            current_time += timedelta(minutes=wait_time)

            # Resume 로그
            resume_detail = {
                "platform": platform,
                "contents_id": content_id,
                "contents_type": content_type_code
            }
            if episode_id:
                resume_detail["episode_id"] = episode_id

            resume_log = {
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "user_id": user.user_id,
                "event_category": 2,
                "event_type": 7,  # resume
                "detail": resume_detail
            }
            logs.append(resume_log)

            # 나머지 시청 시간
            remaining_time = total_watch_minutes - pause_time
            current_time += timedelta(minutes=remaining_time)

        elif selected_pattern == "play_pause_resume_pause_stop":
            # Play → Pause → Resume → Pause → stop (잦은 끊김)
            first_pause_time = total_watch_minutes * random.uniform(0.15, 0.25)
            current_time += timedelta(minutes=first_pause_time)

            # 첫 번째 Pause
            pause_detail1 = {
                "platform": platform,
                "contents_id": content_id,
                "contents_type": content_type_code
            }
            if episode_id:
                pause_detail1["episode_id"] = episode_id

            pause_log1 = {
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "user_id": user.user_id,
                "event_category": 2,
                "event_type": 6,  # pause
                "detail": pause_detail1
            }
            logs.append(pause_log1)

            # 대기
            current_time += timedelta(minutes=random.uniform(1, 3))

            # Resume
            resume_detail = {
                "platform": platform,
                "contents_id": content_id,
                "contents_type": content_type_code
            }
            if episode_id:
                resume_detail["episode_id"] = episode_id

            resume_log = {
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "user_id": user.user_id,
                "event_category": 2,
                "event_type": 7,  # resume
                "detail": resume_detail
            }
            logs.append(resume_log)

            # 재시청
            second_watch_time = total_watch_minutes * random.uniform(0.2, 0.35)
            current_time += timedelta(minutes=second_watch_time)

            # 두 번째 Pause
            pause_detail2 = {
                "platform": platform,
                "contents_id": content_id,
                "contents_type": content_type_code
            }
            if episode_id:
                pause_detail2["episode_id"] = episode_id

            pause_log2 = {
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "user_id": user.user_id,
                "event_category": 2,
                "event_type": 6,  # pause
                "detail": pause_detail2
            }
            logs.append(pause_log2)

            # 나머지 시간
            remaining = total_watch_minutes - first_pause_time - second_watch_time
            current_time += timedelta(minutes=remaining)

        # 마지막 Stop 로그 (모든 패턴 공통)
        stop_detail = {
            "platform": platform,
            "contents_id": content_id,
            "contents_type": content_type_code
        }
        if episode_id:
            stop_detail["episode_id"] = episode_id

        stop_log = {
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 2,
            "event_type": 5,  # stop
            "detail": stop_detail
        }
        logs.append(stop_log)

        return logs


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
            content = {"contents_type": "movie"}

        content_type_code = 1 if content["contents_type"] == "tv" else 2

        return {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 2,  # contents
            "event_type": 8,  # like_on
            "detail": {
                "contents_id": content_id,
                "contents_type": content_type_code
            }
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
            content = {"contents_type": "movie"}

        content_type_code = 1 if content["contents_type"] == "tv" else 2

        return {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 2,  # contents
            "event_type": 9,  # like_off
            "detail": {
                "contents_id": content_id,
                "contents_type": content_type_code
            }
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

        detail = {
            "contents_id": content_id,
            "rating": rating
        }

        if review_detail:
            detail["detail"] = review_detail

        log = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 3,  # review
            "event_type": 10,  # review
            "detail": detail
        }

        return log


    # ========== 구독 로그 (subscription) ==========
    def _generate_subscription_start(self, user, timestamp: datetime) -> Dict[str, Any]:
        """subscription-start 로그 생성"""
        # config 비율에 따라 subscription_type 선택
        subscription_types = list(self.subscription_type_ratio.keys())
        weights = list(self.subscription_type_ratio.values())
        selected_type = random.choices(subscription_types, weights=weights)[0]

        # subscription_type에 따른 ID 매핑
        # standard: s_1~s_4, premium: s_5~s_8, family: s_9~s_12, mobile_only: s_13~s_16
        type_to_id_range = {
            "standard": (1, 4),
            "premium": (5, 8),
            "family": (9, 12),
            "mobile_only": (13, 16)
        }

        start_id, end_id = type_to_id_range.get(selected_type, (1, 4))
        subscription_id = f"s_{random.randint(start_id, end_id)}"

        return {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 4,  # subscription
            "event_type": 4,  # start
            "detail": {
                "subscription_id": subscription_id
            }
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
            "detail": {
                "subscription_id": subscription["subscription_id"]
            }
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
            "detail": {
                "traffic_source": traffic_source
            }
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

        detail = {
            "reason_type": reason_type
        }

        if reason_detail:
            detail["reason_detail"] = reason_detail

        log = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.user_id,
            "event_category": 5,  # register
            "event_type": 2,  # out
            "detail": detail
        }

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
            "detail": {
                "term": term
            }
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
            "detail": {
                "inquiry_type": inquiry_type,
                "inquiry_detail": inquiry_detail
            }
        }
