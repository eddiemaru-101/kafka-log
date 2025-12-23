from enum import Enum


class UserState(Enum):
    """
    유저 상태 (가이드 문서 기반)

    contents-start 이벤트는 패턴에 따라 모든 로그를 한번에 생성하므로
    IN_START, IN_PLAYING, IN_PAUSE 상태는 존재하지 않음
    """
    NOT_LOGGED_IN = "NOT_LOGGED_IN"  # 로그인 전 (오늘 첫 로그인 전)
    MAIN_PAGE = "MAIN_PAGE"          # 메인 페이지
    CONTENT_PAGE = "CONTENT_PAGE"    # 콘텐츠 상세 페이지
    USER_OUT = "USER_OUT"            # 로그아웃/세션 종료

class ActivityLevel(Enum):
    """유저 활성도 등급"""
    HIGH = "high"      # 상
    MEDIUM = "medium"  # 중
    LOW = "low"        # 하

class EventCategory(Enum):
    """로그 카테고리"""
    ACCESS = 1
    CONTENTS = 2
    REVIEW = 3
    SUBSCRIPTION = 4
    REGISTER = 5
    SEARCH = 6
    SUPPORT = 7


class EventType(Enum):
    """로그 타입"""
    IN = 1
    OUT = 2
    CLICK = 3
    START = 4
    STOP = 5
    PAUSE = 6
    RESUME = 7
    LIKE_ON = 8
    LIKE_OFF = 9
    REVIEW = 10
    SEARCH = 11
    INQUIRY = 12


class Platform(Enum):
    """접속 플랫폼"""
    ANDROID = 1
    IOS = 2
    PC = 3
    TV = 4


class ContentType(Enum):
    """콘텐츠 유형"""
    SERIES = 1  # 시리즈물
    SINGLE = 2  # 단편


class TrafficSource(Enum):
    """유입 경로"""
    SEARCH = 1       # 검색
    SOCIAL = 2       # SNS
    AD_SEARCH = 3    # 포털 사이트 광고
    AD_SOCIAL = 4    # SNS 광고
    REFERRAL = 5     # 추천
    MISC = 6         # 기타


class ReasonType(Enum):
    """탈퇴 이유 타입"""
    CONTENTS = 1  # 콘텐츠 관련 불만
    CHARGE = 2    # 요금 관련 불만
    MISC = 3      # 기타


class InquiryType(Enum):
    """문의 타입"""
    CONTENTS = 1      # 콘텐츠 관련 문의
    REFUND = 2        # 환불, 결제 관련 문의
    SUBSCRIPTION = 3  # 구독 관련 문의
    INFORMATION = 4   # 회원 정보 관련 문의