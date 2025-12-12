import random
from datetime import datetime
from typing import Optional, Dict, List

from schemas import (
    LogEvent,
    EventCategory,
    EventType,
    Platform,
    ContentsType,
    TrafficSource,
    ReasonType,
    InquiryType,
    AccessDetail,
    ContentsDetail,
    ReviewDetail,
    SubscriptionDetail,
    RegisterDetail,
    SearchDetail,
    SupportDetail,
)


class LogEventFactory:
    """
    로그 이벤트 생성 팩토리
    
    책임:
    - 각 이벤트 타입별 LogEvent 객체 생성
    - Featured contents 가중치 적용
    - config.toml 기반 검색어/리뷰/문의 문장 선택
    - Pydantic 모델 기반 타입 안전한 로그 생성
    """
    
    def __init__(self, config: dict, all_contents: List[Dict]):
        """
        Args:
            config: config.toml 로딩된 딕셔너리
            all_contents: DBClient.get_all_contents() 결과
        """
        self.config = config
        self.all_contents = all_contents
        
        # Featured contents 설정
        self.featured_content_ids = config["contents"]["featured_content_ids"]
        self.featured_weight = config["contents"].get("featured_weight", 0.3)
        
        # Featured contents 필터링
        self.featured_contents = [
            c for c in all_contents
            if c["content_id"] in self.featured_content_ids
        ]
        
        # 검색어/리뷰/문의 문장
        self.search_terms = config["contents"]["search_terms"]
        self.review_sentences = config["contents"]["review_sentences"]
        self.inquiry_sentences = config["contents"]["inquiry_sentences"]
        
        print(f"✅ LogEventFactory 초기화 완료:")
        print(f"   - 전체 콘텐츠: {len(self.all_contents)}")
        print(f"   - Featured 콘텐츠: {len(self.featured_contents)}")
        print(f"   - Featured 가중치: {self.featured_weight}")
    
    # ========== Contents 선택 로직 ==========
    
    def select_contents(self) -> Dict:
        """
        Featured contents 가중치를 적용해서 콘텐츠 선택
        
        Returns:
            선택된 콘텐츠 딕셔너리
        """
        # featured_weight 확률로 featured contents에서 선택
        if self.featured_contents and random.random() < self.featured_weight:
            return random.choice(self.featured_contents)
        
        # 나머지는 전체 콘텐츠에서 선택
        return random.choice(self.all_contents)
    
    # ========== ACCESS 이벤트 ==========
    
    def access_in(
        self,
        user_id: int,
        platform: Platform,
        timestamp: Optional[datetime] = None
    ) -> LogEvent:
        """access-in 이벤트"""
        return LogEvent(
            timestamp=timestamp or datetime.now(),
            user_id=user_id,
            event_category=EventCategory.ACCESS,
            event_type=EventType.IN,
            detail=AccessDetail(platform=platform)
        )
    
    def access_out(
        self,
        user_id: int,
        platform: Platform,
        timestamp: Optional[datetime] = None
    ) -> LogEvent:
        """access-out 이벤트"""
        return LogEvent(
            timestamp=timestamp or datetime.now(),
            user_id=user_id,
            event_category=EventCategory.ACCESS,
            event_type=EventType.OUT,
            detail=AccessDetail(platform=platform)
        )
    
    # ========== CONTENTS 이벤트 ==========
    
    def contents_click(
        self,
        user_id: int,
        platform: Platform,
        contents_id: str,
        contents_type: ContentsType,
        timestamp: Optional[datetime] = None
    ) -> LogEvent:
        """contents-click 이벤트"""
        return LogEvent(
            timestamp=timestamp or datetime.now(),
            user_id=user_id,
            event_category=EventCategory.CONTENTS,
            event_type=EventType.CLICK,
            detail=ContentsDetail(
                platform=platform,
                contents_id=contents_id,
                contents_type=contents_type
            )
        )
    
    def contents_start(
        self,
        user_id: int,
        platform: Platform,
        contents_id: str,
        contents_type: ContentsType,
        episode_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> LogEvent:
        """contents-start 이벤트"""
        detail = ContentsDetail(
            platform=platform,
            contents_id=contents_id,
            contents_type=contents_type
        )
        
        if contents_type == ContentsType.TV and episode_id:
            detail.episode_id = episode_id
        
        return LogEvent(
            timestamp=timestamp or datetime.now(),
            user_id=user_id,
            event_category=EventCategory.CONTENTS,
            event_type=EventType.START,
            detail=detail
        )
    
    def contents_stop(
        self,
        user_id: int,
        platform: Platform,
        contents_id: str,
        contents_type: ContentsType,
        episode_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> LogEvent:
        """contents-stop 이벤트"""
        detail = ContentsDetail(
            platform=platform,
            contents_id=contents_id,
            contents_type=contents_type
        )
        
        if contents_type == ContentsType.TV and episode_id:
            detail.episode_id = episode_id
        
        return LogEvent(
            timestamp=timestamp or datetime.now(),
            user_id=user_id,
            event_category=EventCategory.CONTENTS,
            event_type=EventType.STOP,
            detail=detail
        )
    
    def contents_pause(
        self,
        user_id: int,
        platform: Platform,
        contents_id: str,
        contents_type: ContentsType,
        episode_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> LogEvent:
        """contents-pause 이벤트"""
        detail = ContentsDetail(
            platform=platform,
            contents_id=contents_id,
            contents_type=contents_type
        )
        
        if contents_type == ContentsType.TV and episode_id:
            detail.episode_id = episode_id
        
        return LogEvent(
            timestamp=timestamp or datetime.now(),
            user_id=user_id,
            event_category=EventCategory.CONTENTS,
            event_type=EventType.PAUSE,
            detail=detail
        )
    
    def contents_resume(
        self,
        user_id: int,
        platform: Platform,
        contents_id: str,
        contents_type: ContentsType,
        episode_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> LogEvent:
        """contents-resume 이벤트"""
        detail = ContentsDetail(
            platform=platform,
            contents_id=contents_id,
            contents_type=contents_type
        )
        
        if contents_type == ContentsType.TV and episode_id:
            detail.episode_id = episode_id
        
        return LogEvent(
            timestamp=timestamp or datetime.now(),
            user_id=user_id,
            event_category=EventCategory.CONTENTS,
            event_type=EventType.RESUME,
            detail=detail
        )
    
    def contents_playing(
        self,
        user_id: int,
        platform: Platform,
        contents_id: str,
        contents_type: ContentsType,
        episode_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> LogEvent:
        """contents-playing 이벤트"""
        detail = ContentsDetail(
            platform=platform,
            contents_id=contents_id,
            contents_type=contents_type
        )
        
        if contents_type == ContentsType.TV and episode_id:
            detail.episode_id = episode_id
        
        return LogEvent(
            timestamp=timestamp or datetime.now(),
            user_id=user_id,
            event_category=EventCategory.CONTENTS,
            event_type=EventType.PLAYING,
            detail=detail
        )
    
    def contents_like_on(
        self,
        user_id: int,
        platform: Platform,
        contents_id: str,
        contents_type: ContentsType,
        timestamp: Optional[datetime] = None
    ) -> LogEvent:
        """contents-like_on 이벤트 (episode_id 없음)"""
        return LogEvent(
            timestamp=timestamp or datetime.now(),
            user_id=user_id,
            event_category=EventCategory.CONTENTS,
            event_type=EventType.LIKE_ON,
            detail=ContentsDetail(
                platform=platform,
                contents_id=contents_id,
                contents_type=contents_type
            )
        )
    
    def contents_like_off(
        self,
        user_id: int,
        platform: Platform,
        contents_id: str,
        contents_type: ContentsType,
        timestamp: Optional[datetime] = None
    ) -> LogEvent:
        """contents-like_off 이벤트 (episode_id 없음)"""
        return LogEvent(
            timestamp=timestamp or datetime.now(),
            user_id=user_id,
            event_category=EventCategory.CONTENTS,
            event_type=EventType.LIKE_OFF,
            detail=ContentsDetail(
                platform=platform,
                contents_id=contents_id,
                contents_type=contents_type
            )
        )
    
    # ========== REVIEW 이벤트 ==========
    
    def review_review(
        self,
        user_id: int,
        contents_id: str,
        rating: Optional[float] = None,
        review_text: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> LogEvent:
        """review-review 이벤트 (평점 + 리뷰 텍스트)"""
        # 평점이 없으면 랜덤 생성 (1.0 ~ 5.0)
        if rating is None:
            rating = round(random.uniform(1.0, 5.0), 1)
        
        # 리뷰 텍스트가 없으면 랜덤 선택
        if review_text is None:
            review_text = random.choice(self.review_sentences)
        
        return LogEvent(
            timestamp=timestamp or datetime.now(),
            user_id=user_id,
            event_category=EventCategory.REVIEW,
            event_type=EventType.REVIEW,
            detail=ReviewDetail(
                contents_id=contents_id,
                rating=rating,
                review_text=review_text
            )
        )
    
    # ========== SUBSCRIPTION 이벤트 ==========
    
    def subscription_start(
        self,
        user_id: int,
        subscription_id: str,
        timestamp: Optional[datetime] = None
    ) -> LogEvent:
        """subscription-start 이벤트"""
        return LogEvent(
            timestamp=timestamp or datetime.now(),
            user_id=user_id,
            event_category=EventCategory.SUBSCRIPTION,
            event_type=EventType.START,
            detail=SubscriptionDetail(subscription_id=subscription_id)
        )
    
    def subscription_stop(
        self,
        user_id: int,
        subscription_id: str,
        timestamp: Optional[datetime] = None
    ) -> LogEvent:
        """subscription-stop 이벤트"""
        return LogEvent(
            timestamp=timestamp or datetime.now(),
            user_id=user_id,
            event_category=EventCategory.SUBSCRIPTION,
            event_type=EventType.STOP,
            detail=SubscriptionDetail(subscription_id=subscription_id)
        )
    
    # ========== REGISTER 이벤트 ==========
    
    def register_in(
        self,
        user_id: int,
        traffic_source: TrafficSource,
        timestamp: Optional[datetime] = None
    ) -> LogEvent:
        """register-in 이벤트 (회원가입)"""
        return LogEvent(
            timestamp=timestamp or datetime.now(),
            user_id=user_id,
            event_category=EventCategory.REGISTER,
            event_type=EventType.IN,
            detail=RegisterDetail(traffic_source=traffic_source)
        )
    
    def register_out(
        self,
        user_id: int,
        reason_type: ReasonType,
        reason_detail: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> LogEvent:
        """register-out 이벤트 (탈퇴)"""
        # 탈퇴 사유가 없으면 랜덤 선택
        if reason_detail is None:
            reason_detail = random.choice(self.inquiry_sentences)
        
        return LogEvent(
            timestamp=timestamp or datetime.now(),
            user_id=user_id,
            event_category=EventCategory.REGISTER,
            event_type=EventType.OUT,
            detail=RegisterDetail(
                reason_type=reason_type,
                reason_detail=reason_detail
            )
        )
    
    # ========== SEARCH 이벤트 ==========
    
    def search_search(
        self,
        user_id: int,
        search_term: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> LogEvent:
        """search-search 이벤트"""
        # 검색어가 없으면 랜덤 선택
        if search_term is None:
            search_term = random.choice(self.search_terms)
        
        return LogEvent(
            timestamp=timestamp or datetime.now(),
            user_id=user_id,
            event_category=EventCategory.SEARCH,
            event_type=EventType.SEARCH,
            detail=SearchDetail(search_term=search_term)
        )
    
    # ========== SUPPORT 이벤트 ==========
    
    def support_inquiry(
        self,
        user_id: int,
        inquiry_type: InquiryType,
        inquiry_detail: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> LogEvent:
        """support-inquiry 이벤트"""
        # 문의 내용이 없으면 랜덤 선택
        if inquiry_detail is None:
            inquiry_detail = random.choice(self.inquiry_sentences)
        
        return LogEvent(
            timestamp=timestamp or datetime.now(),
            user_id=user_id,
            event_category=EventCategory.SUPPORT,
            event_type=EventType.INQUIRY,
            detail=SupportDetail(
                inquiry_type=inquiry_type,
                inquiry_detail=inquiry_detail
            )
        )