from enum import Enum, auto

class UserState(Enum):
    IDLE = auto()
    OUT = auto()
    IN_START = auto()
    IN_PAUSE = auto()
    IN_IDLE = auto()
    NONE = auto()
    INIT = auto() # 존재 불가 상태(초기값)

EVENT_TO_STATE = {
    "access in": UserState.IDLE,
    "access out": UserState.NONE,

    "contents click": UserState.OUT,
    "contents start": UserState.IN_START,
    "contents stop": UserState.OUT,
    "contents pause": UserState.IN_PAUSE,
    "contents resume": UserState.IN_IDLE,
    "contents playing": UserState.IN_IDLE,

    "contents like_on": UserState.OUT,
    "contents like_off": UserState.OUT,

    "review review": UserState.OUT,

    "search search": UserState.IDLE,

    "subscription start": UserState.IDLE,
    "subscription stop": UserState.IDLE,

    "register in": UserState.IDLE,
    "register out": UserState.NONE,
    
    "support inquiry": UserState.IDLE,
}

PLATFORMS = ["android", "ios", "pc", "tv"]
CONTENTS_TYPES = ["series", "single"]
INQUIRY_TYPES = ["contents", "refund", "subscription", "information"]
TRAFFIC_SOURCES = ["search", "social", "ad_search", "ad_social", "referral", "misc"]
REASON_TYPES = ["contents", "charge", "misc"]

CATEGORY_MAP = {
    "access": 1,
    "contents": 2,
    "review": 3,
    "subscription": 4,
    "register": 5,
    "search": 6,
    "support": 7
}

TYPE_MAP = {
    "in": 1,
    "out": 2,
    "click": 3,
    "start": 4,
    "stop": 5,
    "pause": 6,
    "resume": 7,
    "like_on": 8,
    "like_off": 9,
    "review": 10,
    "search": 11,
    "inquiry": 12
}

PLATFORM_MAP = {
    "android": 1,
    "ios": 2,
    "pc": 3,
    "tv": 4
}

CONTENTS_TYPE_MAP = {
    "tv": 1,
    "movie": 2
}

TRAFFIC_SOURCE_MAP = {
    "search": 1,
    "social": 2,
    "ad_search": 3,
    "ad_social": 4,
    "referral": 5,
    "misc": 6
}

REASON_TYPE_MAP = {
    "contents": 1,
    "charge": 2,
    "misc": 3
}

INQUIRY_TYPE_MAP = {
    "contents": 1,
    "refund": 2,
    "subscription": 3,
    "information": 4
}

SEARCH_TERMS = [
    "해리포터", "어벤져스", "겨울왕국", "스파이더맨", "라라랜드",
    "부산행", "파친코", "오징어게임", "수리남"
]

REVIEW_SENTENCES = [
    "재밌어요", "지루했어요", "다시 보고 싶어요", "연기가 좋았어요",
    "스토리가 약했어요", "영상미가 뛰어나요"
]

INQUIRY_SENTENCES = [
    "25일 쓴 이용권 환불 가능?", "결제가 중복된 것 같아요",
    "콘텐츠 재생이 안됩니다", "구독 변경은 어떻게 하나요?"
]