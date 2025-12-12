import random
from dataclasses import dataclass
import log_creator as lc
import os
import json
import log_info as li
import db_connector as dc


@dataclass
class User:
    cur_log: dict

    user_id: str
    cur_platform: str
    cur_contents_id: str
    cur_contents_type: str
    cur_episode_id: str
    # cur_progress_time: int
    is_subscribed: bool
    cur_subs_id: str
    cur_con_epi_num: int

    is_fresh_user: bool
    
    state: li.UserState
    update_tick: float

    def __init__(self): # 초기화는 rds와 연결 후 수정 필요
        self.user_id = None
        self.cur_platform = None
        self.cur_contents_id = None
        self.cur_contents_type = None
        self.cur_episode_id = None
        self.cur_subs_id = None
        
        # self.cur_progress_time = 0
        self.update_tick = 0
        self.state = li.UserState.INIT
        
        # 신규 유저 비율 5%
        n = random.randint(1, 100)
        self.is_fresh_user = n > 95

        if self.is_fresh_user:
            # 신규 유저 아이디 생성 - RDS에 없는 아이디로 할당 필요, 신규 데이터 RDS에 삽입
            new_user = dc.get_new_user()
            self.user_id = new_user

            self.is_subscribed = False
            self.enter(li.UserState.IDLE, "register in")
        else:
            # 기존 유저 아이디 - RDS에서 랜덤으로 할당
            self.user_id = dc.get_random_user()["user_id"]
            dc.update_last_login_date(self.user_id)
            subs = dc.get_user_subscription_id(self.user_id)
            if subs is not None:
                self.cur_subs_id = subs
                self.is_subscribed = True
            else:
                self.is_subscribed = False

            self.enter(li.UserState.IDLE, "access in")

    def generate_log(self, log_type: str):
        if log_type == "":
            return None
        category = log_type.split(" ")[0]
        event_type = log_type.split(" ")[1]
        match category:
            case "access":
                return lc.make_access_event(
                    user_id=self.user_id,
                    event_type=event_type,
                    platform=self.cur_platform
                )
            case "contents":
                return lc.make_contents_event(
                    user_id=self.user_id,
                    event_type=event_type,
                    platform=self.cur_platform,
                    contents_id=self.cur_contents_id,
                    contents_type=self.cur_contents_type,
                    episode_id=self.cur_episode_id
                    # progress_time=self.cur_progress_time
                )
            case "review":
                return lc.make_review_event(
                    user_id=self.user_id,
                    contents_id=self.cur_contents_id,
                    rating=random.uniform(1.0, 5.0),
                    detail_text=li.REVIEW_SENTENCES[random.randint(0, len(li.REVIEW_SENTENCES)-1)]
                )
            case "subscription":
                if event_type == "start":
                    self.is_subscribed = True
                    self.cur_subs_id = "s_" + str(random.randint(1, 16)) # 구독 상품 랜덤 선택
                    dc.insert_user_subscription(self.user_id, self.cur_subs_id)
                elif event_type == "stop":
                    self.is_subscribed = False
                    # dc.delete_user_subscription(self.user_id)
                    dc.cancel_user_subscription(self.user_id)
                return lc.make_subscription_event(
                    user_id=self.user_id,
                    event_type=event_type,
                    subscription_id=self.cur_subs_id
                )
            case "register":
                return lc.make_register_event(
                    user_id=self.user_id,
                    event_type=event_type,
                    traffic_source=li.TRAFFIC_SOURCES[random.randint(0, len(li.TRAFFIC_SOURCES)-1)] if event_type == "in" else None,
                    reason_type=li.REASON_TYPES[random.randint(0, len(li.REASON_TYPES)-1)] if event_type == "out" else None,
                    reason_detail=li.INQUIRY_SENTENCES[random.randint(0, len(li.INQUIRY_SENTENCES)-1)] if event_type == "out" else None
                )
            case "search":
                return lc.make_search_event(
                    user_id=self.user_id,
                    term=li.SEARCH_TERMS[random.randint(0, len(li.SEARCH_TERMS)-1)]
                )
            case "support":
                return lc.make_support_event(
                    user_id=self.user_id,
                    inquiry_type=li.INQUIRY_TYPES[random.randint(0, len(li.INQUIRY_TYPES)-1)],
                    detail_text=li.INQUIRY_SENTENCES[random.randint(0, len(li.INQUIRY_SENTENCES)-1)]
                )

    def enter(self, next_state: li.UserState, log_type: str):
        self.state = next_state
        match self.state:
            case li.UserState.IDLE:
                if self.cur_platform is None:
                    self.cur_platform = random.choice(li.PLATFORMS)
                self.update_tick = random.uniform(0.5, 1.0)
            case li.UserState.OUT:
                if log_type == "contents click":
                    contents_info = dc.get_random_contents()
                    self.cur_contents_id = contents_info["content_id"]
                    self.cur_contents_type = contents_info["content_type"]
                    if contents_info["number_of_episodes"] is not None:
                        self.cur_con_epi_num = contents_info["number_of_episodes"]
                    else:
                        self.cur_con_epi_num = 1
                    # self.cur_contents_id = f"contents_{random.randint(100, 200)}" # TODO: RDS에서 랜덤 할당 필요
                    # self.cur_contents_type = random.choice(li.CONTENTS_TYPES) # TODO: RDS에서 받아온 콘텐츠 데이터에 맞는 타입 할당
                self.update_tick = random.uniform(0.5, 1.0)
            case li.UserState.IN_START:
                self.cur_episode_id = f"episode_{random.randint(1, self.cur_con_epi_num + 1)}" 
                # self.cur_progress_time = random.randint(0, 3600)
                self.update_tick = random.uniform(3.0, 5.0)
            case li.UserState.IN_PAUSE:
                self.update_tick = random.uniform(3.0, 5.0)
            case li.UserState.IN_IDLE:
                self.update_tick = random.uniform(3.0, 5.0)
            case li.UserState.NONE:
                if log_type == "register out":
                    dc.update_delete_user(self.user_id)
        print(f"User {self.user_id} update tick {self.update_tick}.")

        new_log = self.generate_log(log_type)
        if new_log is None:
            return        
        self.cur_log = new_log

        # TODO: 실시간 전송 시 파일 저장 부분 제거 필요
        log_path = f"logs_{self.user_id}.json"

        if not os.path.exists(log_path):
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump([new_log], f, ensure_ascii=False, indent=2)
            return

        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data.append(new_log)

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def update(self):
        match self.state:
            case li.UserState.IDLE:
                self.update_idle()
            case li.UserState.OUT:
                self.update_out()
            case li.UserState.IN_START:
                self.update_in_idle()
            case li.UserState.IN_PAUSE:
                self.update_in_pause()
            case li.UserState.IN_IDLE:
                self.update_in_idle()

    def exit(self):
        match self.state:
            case li.UserState.IDLE:
                pass
            case li.UserState.OUT:
                pass
            case li.UserState.IN_START:
                # self.cur_progress_time += self.update_tick
                pass
            case li.UserState.IN_PAUSE:
                pass
            case li.UserState.IN_IDLE:
                # self.cur_progress_time += self.update_tick
                pass
            case li.UserState.NONE:
                print(f"User {self.user_id} exits the system.")
        
    def update_idle(self):
        n = random.randint(1, 100)
        log_type = ""
        # 유료구독 구독자
        if self.is_subscribed:
            if n <= 10:
                log_type = "access out"
            elif n <= 70:
                log_type = "contents click" # 테스트용 contents click과 비율 변경
            elif n <= 78:
                log_type = "subscription stop"
            elif n <= 79:
                log_type = "register out"
            elif n <= 99:
                log_type = "search search"
            else:
                log_type = "support inquiry"
        # 비구독자
        else:
            if n <= 30:
                log_type = "subscription start"
            elif n <= 70:
                log_type = "contents click"
            elif n <= 90:
                log_type = "search search"
            elif n <= 99:
                log_type = "register out"
            else:
                log_type = "support inquiry"
        
        self.exit()
        next_state = li.EVENT_TO_STATE[log_type]
        self.enter(next_state, log_type)

    def update_out(self):
        n = random.randint(1, 100)
        log_type = ""
        next_state = li.UserState.INIT

        if self.is_subscribed:
            if n <= 40:
                log_type = "contents start"
            elif n <= 50:
                log_type = "contents like_on"
            elif n <= 55:
                log_type = "contents like_off"
            elif n <= 60:
                log_type = "review review"
            else:
                next_state = li.UserState.IDLE
        else:
            if n <= 80:
                next_state = li.UserState.IDLE
            elif n <= 95:
                log_type = "contents like_on"
            else:
                log_type = "contents like_off"
        
        self.exit()
        if next_state == li.UserState.INIT:
            next_state = li.EVENT_TO_STATE[log_type]
        self.enter(next_state, log_type)

    def update_in_idle(self):
        n = random.randint(1, 100)
        log_type = ""
        next_state = li.UserState.INIT

        if n <= 5:
            log_type = "access out"
            self.generate_log("contents stop")
        elif n <= 10:
            log_type = "contents pause"
        elif n <= 95:
            next_state = li.UserState.IN_IDLE
        else:
            log_type = "contents stop"

        self.exit()
        if next_state == li.UserState.INIT:
            next_state = li.EVENT_TO_STATE[log_type]
        self.enter(next_state, log_type)

    def update_in_pause(self):
        n = random.randint(1, 100)
        log_type = ""

        if n <= 90:
            log_type = "contents resume"
        else:
            log_type = "access out"
            self.generate_log("contents stop")

        self.exit()
        next_state = li.EVENT_TO_STATE[log_type]
        self.enter(next_state, log_type)