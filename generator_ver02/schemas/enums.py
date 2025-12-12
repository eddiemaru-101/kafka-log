from enum import IntEnum


# 로그 이벤트 카테고리 (7개)
class EventCategory(IntEnum):
    ACCESS = 1
    CONTENTS = 2
    REVIEW = 3
    SUBSCRIPTION = 4
    REGISTER = 5
    SEARCH = 6
    SUPPORT = 7


# 로그 이벤트 타입 (13개)
class EventType(IntEnum):
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
    PLAYING = 13


# 플랫폼 (4개)
class Platform(IntEnum):
    ANDROID = 1
    IOS = 2
    PC = 3
    TV = 4


# 콘텐츠 타입 (2개)
class ContentsType(IntEnum):
    TV = 1
    MOVIE = 2


# 유입 경로 (6개)
class TrafficSource(IntEnum):
    SEARCH = 1
    SOCIAL = 2
    AD_SEARCH = 3
    AD_SOCIAL = 4
    REFERRAL = 5
    MISC = 6


# 탈퇴 사유 유형 (3개)
class ReasonType(IntEnum):
    CONTENTS = 1
    CHARGE = 2
    MISC = 3


# 문의 유형 (4개)
class InquiryType(IntEnum):
    CONTENTS = 1
    REFUND = 2
    SUBSCRIPTION = 3
    INFORMATION = 4


# 유저 활동 레벨 (3개) - config.toml의 user_activity와 매핑
class UserActivityLevel(IntEnum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3