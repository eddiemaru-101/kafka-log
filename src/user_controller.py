import random
from typing import Tuple, Optional

# schemas에서 Enum 가져오기
from schemas.enum import (
    UserState,
    ActivityLevel,
    EventCategory,
    EventType
)


class UserEventController:
    """
    유저 상태 기반 이벤트 결정 컨트롤러

    책임:
    - 유저의 현재 상태를 기반으로 발생 가능한 로그 타입 결정
    - 선택된 로그 타입에 따른 다음 상태 결정
    - 상태 전이 확률 관리
    
    주의:
    - User 객체는 UserSelector가 관리
    - 이 클래스는 User 인스턴스를 받아서 어떤 로그를 발생시킬지만 결정
    """

    def __init__(self, config: dict):
        """
        Args:
            config: config.toml의 전체 설정
        """
        self.config = config
        
        # 상태별 전이 확률 (config에서 읽거나 기본값 사용)
        self.state_transitions = self._load_state_transitions()
        
        print(f"✅ UserEventController 초기화 완료")

    def _load_state_transitions(self) -> dict:
        """
        상태별 이벤트 발생 확률 로드

        Returns:
            상태별 전이 확률 딕셔너리
        """
        # config에서 읽어오거나 기본값 사용
        return self.config.get("user_event_transitions", {
            "MAIN_PAGE": {
                "subscribed": {
                    "access-out": 0.10,
                    "contents-click": 0.50,
                    "subscription-stop": 0.05,
                    "register-out": 0.02,
                    "search-search": 0.25,
                    "support-inquiry": 0.08,
                },
                "not_subscribed": {
                    "subscription-start": 0.30,
                    "contents-click": 0.40,
                    "search-search": 0.20,
                    "register-out": 0.02,
                    "support-inquiry": 0.08,
                }
            },
            "CONTENT_PAGE": {
                "subscribed": {
                    "contents-start": 0.67,
                    "contents-like_on": 0.16,
                    "contents-like_off": 0.06,
                    "review-review": 0.11,
                },
                "not_subscribed": {
                    "contents-like_on": 0.75,
                    "contents-like_off": 0.25,
                }
            }
        })

    def select_event(
        self,
        user,
        current_state: UserState
    ) -> Tuple[Optional[str], UserState, Optional[dict]]:
        """
        유저 상태 기반 다음 이벤트 선택

        Args:
            user: User 객체
            current_state: 현재 유저 상태

        Returns:
            (event_type, next_state, additional_data)
        """
        # 오늘 처음 선택되는 경우 access-in 로그 먼저 발생
        if hasattr(user, 'has_logged_in_today') and not user.has_logged_in_today:
            user.has_logged_in_today = True
            return "access-in", UserState.MAIN_PAGE, None

        if current_state == UserState.MAIN_PAGE:
            return self._handle_main_page(user.is_subscribed)

        elif current_state == UserState.CONTENT_PAGE:
            return self._handle_content_page(user.is_subscribed, user.activity_level)

        elif current_state == UserState.USER_OUT:
            return None, UserState.USER_OUT, None

        else:
            return None, UserState.USER_OUT, None
        
        

    def _handle_main_page(self, is_subscribed: bool) -> Tuple[str, UserState, Optional[dict]]:
        """MAIN_PAGE 상태 처리"""
        
        if is_subscribed:
            probs = self.state_transitions["MAIN_PAGE"]["subscribed"]
        else:
            probs = self.state_transitions["MAIN_PAGE"]["not_subscribed"]
        
        # 가중치 기반 랜덤 선택
        event = random.choices(
            list(probs.keys()),
            weights=list(probs.values())
        )[0]
        
        # 이벤트별 다음 상태 결정
        if event == "access-out":
            return "access-out", UserState.USER_OUT, None
        
        elif event == "contents-click":
            return "contents-click", UserState.CONTENT_PAGE, {"need_content": True}
        
        elif event == "subscription-stop":
            return "subscription-stop", UserState.MAIN_PAGE, {"update_subscription": False}
        
        elif event == "register-out":
            return "register-out", UserState.USER_OUT, {"delete_user": True}
        
        elif event == "search-search":
            return "search-search", UserState.MAIN_PAGE, None
        
        elif event == "support-inquiry":
            return "support-inquiry", UserState.MAIN_PAGE, None
        
        elif event == "subscription-start":
            return "subscription-start", UserState.MAIN_PAGE, {"update_subscription": True}
        
        else:
            # 기본값
            return "access-out", UserState.USER_OUT, None

    def _handle_content_page(
        self,
        is_subscribed: bool,
        activity_level: Optional[ActivityLevel] = None
    ) -> Tuple[Optional[str], UserState, Optional[dict]]:
        """
        CONTENT_PAGE 상태 처리

        contents-start 이벤트는 패턴에 따라 모든 로그를 한번에 생성하고
        바로 MAIN_PAGE로 전이

        모든 이벤트 후 CONTENT_PAGE → MAIN_PAGE로 전이
        (콘텐츠 상세 페이지에서 행동 후 메인으로 돌아가는 흐름)
        """
        if is_subscribed:
            probs = self.state_transitions["CONTENT_PAGE"]["subscribed"]
        else:
            probs = self.state_transitions["CONTENT_PAGE"]["not_subscribed"]

        event = random.choices(
            list(probs.keys()),
            weights=list(probs.values())
        )[0]

        if event == "contents-start":
            # activity_level을 additional_data에 포함 (로그 생성 시 시청시간 계산용)
            # 패턴에 따라 모든 재생 로그 생성 후 MAIN_PAGE로 전이
            return "contents-start", UserState.MAIN_PAGE, {
                "need_episode": True,
                "activity_level": activity_level
            }

        elif event == "contents-like_on":
            return "contents-like_on", UserState.MAIN_PAGE, None

        elif event == "contents-like_off":
            return "contents-like_off", UserState.MAIN_PAGE, None

        elif event == "review-review":
            return "review-review", UserState.MAIN_PAGE, None

        else:
            # 알 수 없는 이벤트는 MAIN_PAGE로
            return None, UserState.MAIN_PAGE, None

    def get_event_category_code(self, event_type: str) -> int:
        """
        event_type에서 카테고리 코드 추출
        
        Args:
            event_type: "category-type" 형식 (예: "access-in")
            
        Returns:
            카테고리 코드 (1~7)
        """
        category = event_type.split("-")[0]
        
        mapping = {
            "access": EventCategory.ACCESS.value,
            "contents": EventCategory.CONTENTS.value,
            "review": EventCategory.REVIEW.value,
            "subscription": EventCategory.SUBSCRIPTION.value,
            "register": EventCategory.REGISTER.value,
            "search": EventCategory.SEARCH.value,
            "support": EventCategory.SUPPORT.value,
        }
        
        return mapping.get(category, 1)

    def get_event_type_code(self, event_type: str) -> int:
        """
        event_type에서 타입 코드 추출
        
        Args:
            event_type: "category-type" 형식 (예: "access-in")
            
        Returns:
            타입 코드 (1~12)
        """
        type_name = event_type.split("-")[1]
        
        mapping = {
            "in": EventType.IN.value,
            "out": EventType.OUT.value,
            "click": EventType.CLICK.value,
            "start": EventType.START.value,
            "stop": EventType.STOP.value,
            "pause": EventType.PAUSE.value,
            "resume": EventType.RESUME.value,
            "like_on": EventType.LIKE_ON.value,
            "like_off": EventType.LIKE_OFF.value,
            "review": EventType.REVIEW.value,
            "search": EventType.SEARCH.value,
            "inquiry": EventType.INQUIRY.value,
        }
        
        return mapping.get(type_name, 1)