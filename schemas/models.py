from datetime import datetime
from pydantic import BaseModel, Field
from .enums import (
    EventCategory,
    EventType,
    Platform,
    ContentsType,
    TrafficSource,
    ReasonType,
    InquiryType,
)


# 1. access 이벤트 detail
class AccessDetail(BaseModel):
    platform: Platform


# 2. contents 이벤트 detail
class ContentsDetail(BaseModel):
    platform: Platform
    contents_id: str  # 예: "tv_12345", "movie_67890"
    contents_type: ContentsType
    episode_id: str | None = None  # TV 시리즈만 필요 (예: "episode_3")


# 3. review 이벤트 detail
class ReviewDetail(BaseModel):
    contents_id: str
    rating: float  # 1.0 ~ 5.0
    review_text: str


# 4. subscription 이벤트 detail
class SubscriptionDetail(BaseModel):
    subscription_id: str  # 예: "s_1", "s_2", ...


# 5. register 이벤트 detail
class RegisterDetail(BaseModel):
    traffic_source: TrafficSource | None = None  # register-in만 사용
    reason_type: ReasonType | None = None        # register-out만 사용
    reason_detail: str | None = None             # register-out만 사용


# 6. search 이벤트 detail
class SearchDetail(BaseModel):
    search_term: str  # 검색어


# 7. support 이벤트 detail
class SupportDetail(BaseModel):
    inquiry_type: InquiryType
    inquiry_detail: str


# 최종 로그 이벤트 모델
class LogEvent(BaseModel):
    timestamp: datetime
    user_id: int = Field(..., gt=0)  # 양수만 허용
    event_category: EventCategory
    event_type: EventType
    detail: (
        AccessDetail
        | ContentsDetail
        | ReviewDetail
        | SubscriptionDetail
        | RegisterDetail
        | SearchDetail
        | SupportDetail
    )

    class Config:
        use_enum_values = True  # JSON 직렬화 시 Enum을 int로 변환