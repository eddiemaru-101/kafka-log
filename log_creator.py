import random
import uuid
from datetime import datetime
import pytz
import log_info as li

def current_timestamp():
    tz = pytz.timezone("Asia/Seoul")
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")


def generate_id(prefix="id"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def base_event(user_id, event_category, event_type):
    return {
        "timestamp": current_timestamp(),
        "user_id": user_id,
        "event_category": li.CATEGORY_MAP[event_category],
        "event_type": li.TYPE_MAP[event_type],
        "detail": {}
    }

def make_access_event(user_id, event_type, platform):
    event = base_event(user_id, "access", event_type)
    event["detail"] = {
        "platform": li.PLATFORM_MAP[platform]
    }
    return event

def make_contents_event(user_id, event_type, platform, contents_id,
                        contents_type, episode_id=None, progress_time=None):
    event = base_event(user_id, "contents", event_type)

    detail = {
        "platform": li.PLATFORM_MAP[platform],
        "contents_id": contents_id,
        "contents_type": li.CONTENTS_TYPE_MAP[contents_type]
    }

    if event_type not in ["like_on", "like_off"]:
        if episode_id and contents_type == "tv":
            detail["episode_id"] = episode_id
        # if not event_type == "click" and progress_time is not None:
        #     progress_time = int(progress_time)
        #     hours = progress_time // 3600
        #     minutes = (progress_time % 3600) // 60
        #     seconds = progress_time % 60
        #     detail["progress_time"] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    event["detail"] = detail
    return event

def make_review_event(user_id, contents_id, rating, detail_text=None):
    # 평점 보정
    rating = round(rating * 2) / 2

    event = base_event(user_id, "review", "review")
    event["detail"] = {
        "contents_id": contents_id,
        "rating": rating,
        "detail": detail_text
    }
    return event

def make_subscription_event(user_id, event_type, subscription_id):
    event = base_event(user_id, "subscription", event_type)
    event["detail"] = {
        "subscription_id": subscription_id
    }
    return event

def make_register_event(user_id, event_type, traffic_source=None,
                        reason_type=None, reason_detail=None):
    event = base_event(user_id, "register", event_type)

    if event_type == "in":
        event["detail"] = {"traffic_source": li.TRAFFIC_SOURCE_MAP[traffic_source]}
    else:
        event["detail"] = {
            "reason_type": li.REASON_TYPE_MAP[reason_type],
            "reason_detail": reason_detail
        }

    return event

def make_search_event(user_id, term):
    event = base_event(user_id, "search", "search")
    event["detail"] = {
        "term": term
    }
    return event

def make_support_event(user_id, inquiry_type, detail_text):
    event = base_event(user_id, "support", "inquiry")
    event["detail"] = {
        "inquiry_type": li.INQUIRY_TYPE_MAP[inquiry_type],
        "inquiry_detail": detail_text
    }
    return event
