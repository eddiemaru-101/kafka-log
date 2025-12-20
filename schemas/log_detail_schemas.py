"""
로그 타입별 detail 스키마 정의
"""
from typing import TypedDict, Optional


# ========== 접속(access) 로그 ==========
class AccessInDetail(TypedDict):
    """access-in 로그의 detail 스키마"""
    platform: int  # 1: android, 2: ios, 3: pc, 4: tv


class AccessOutDetail(TypedDict):
    """access-out 로그의 detail 스키마"""
    platform: int  # 1: android, 2: ios, 3: pc, 4: tv


# ========== 콘텐츠(contents) 로그 ==========
class ContentsClickDetail(TypedDict):
    """contents-click 로그의 detail 스키마"""
    platform: int  # 1: android, 2: ios, 3: pc, 4: tv
    contents_id: str
    contents_type: int  # 1: series, 2: single


class ContentsStartDetail(TypedDict):
    """contents-start 로그의 detail 스키마"""
    platform: int  # 1: android, 2: ios, 3: pc, 4: tv
    contents_id: str
    contents_type: int  # 1: series, 2: single
    episode_id: Optional[str]  # series인 경우에만


class ContentsStopDetail(TypedDict):
    """contents-stop 로그의 detail 스키마"""
    platform: int  # 1: android, 2: ios, 3: pc, 4: tv
    contents_id: str
    contents_type: int  # 1: series, 2: single
    episode_id: Optional[str]  # series인 경우에만


class ContentsPauseDetail(TypedDict):
    """contents-pause 로그의 detail 스키마"""
    platform: int  # 1: android, 2: ios, 3: pc, 4: tv
    contents_id: str
    contents_type: int  # 1: series, 2: single
    episode_id: Optional[str]  # series인 경우에만


class ContentsResumeDetail(TypedDict):
    """contents-resume 로그의 detail 스키마"""
    platform: int  # 1: android, 2: ios, 3: pc, 4: tv
    contents_id: str
    contents_type: int  # 1: series, 2: single
    episode_id: Optional[str]  # series인 경우에만


class ContentsPlayingDetail(TypedDict):
    """contents-playing 로그의 detail 스키마"""
    platform: int  # 1: android, 2: ios, 3: pc, 4: tv
    contents_id: str
    contents_type: int  # 1: series, 2: single
    episode_id: Optional[str]  # series인 경우에만


class ContentsLikeOnDetail(TypedDict):
    """contents-like_on 로그의 detail 스키마"""
    contents_id: str
    contents_type: int  # 1: series, 2: single


class ContentsLikeOffDetail(TypedDict):
    """contents-like_off 로그의 detail 스키마"""
    contents_id: str
    contents_type: int  # 1: series, 2: single


# ========== 리뷰(review) 로그 ==========
class ReviewReviewDetail(TypedDict):
    """review-review 로그의 detail 스키마"""
    contents_id: str
    rating: float  # 0.5 ~ 5.0 (0.5 단위)
    detail: Optional[str]  # 리뷰 내용 (선택)


# ========== 구독(subscription) 로그 ==========
class SubscriptionStartDetail(TypedDict):
    """subscription-start 로그의 detail 스키마"""
    subscription_id: str


class SubscriptionStopDetail(TypedDict):
    """subscription-stop 로그의 detail 스키마"""
    subscription_id: str


class SubscriptionChangeDetail(TypedDict):
    """subscription-change 로그의 detail 스키마"""
    subscription_id: str


# ========== 회원(register) 로그 ==========
class RegisterInDetail(TypedDict):
    """register-in 로그의 detail 스키마"""
    traffic_source: int  # 1: search, 2: social, 3: ad_search, 4: ad_social, 5: referral, 6: misc


class RegisterOutDetail(TypedDict):
    """register-out 로그의 detail 스키마"""
    reason_type: int  # 1: contents, 2: charge, 3: misc
    reason_detail: Optional[str]  # 탈퇴 이유 상세 (선택)


# ========== 검색(search) 로그 ==========
class SearchSearchDetail(TypedDict):
    """search-search 로그의 detail 스키마"""
    term: str  # 검색어


# ========== 고객센터(support) 로그 ==========
class SupportInquiryDetail(TypedDict):
    """support-inquiry 로그의 detail 스키마"""
    inquiry_type: int  # 1: contents, 2: refund, 3: subscription, 4: information
    inquiry_detail: str  # 문의 내용
