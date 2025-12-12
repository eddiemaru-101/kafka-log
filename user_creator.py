import mysql.connector
from faker import Faker
import random
import hashlib
from datetime import datetime

# ==============================
# 1. Faker 인스턴스 생성 (국가별)
# ==============================
fake_kr = Faker('ko_KR')
fake_us = Faker('en_US')
fake_jp = Faker('ja_JP')
fake_cn = Faker('zh_CN')
fake_vn = Faker('vi_VN')

# ==============================
# 2. 분포 정의
# ==============================
countries = ['KR', 'CN', 'US', 'JP', 'VN']
country_weights = [95.5, 3, 1, 1, 0.5]

genders = [0, 1, 2]
gender_weights = [49.5, 49.5, 1]

age_ranges = [(15, 19), (20, 29), (30, 39), (40, 49), (50, 59), (60, 70)]
age_weights = [8, 16, 21, 26, 21, 7]

kr_cities = ['서울', '경기', '인천', '부산', '대구', '울산', '경북', '경남',
             '대전', '세종', '충북', '충남', '광주', '전북', '전남', '강원', '제주']
kr_city_weights = [18, 26, 6, 7, 5, 2, 5, 6, 3, 1, 3, 4, 3, 3, 4, 3, 1]

us_cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Seattle']
jp_cities = ['Tokyo', 'Osaka', 'Kyoto', 'Yokohama', 'Nagoya']
cn_cities = ['Beijing', 'Shanghai', 'Shenzhen', 'Guangzhou', 'Chengdu']
vn_cities = ['Hanoi', 'Ho Chi Minh', 'Da Nang']

devices = ['mobile', 'tv', 'tablet', 'desktop', 'console']
device_weights = [60.9, 18, 11, 10, 0.1]

# statuses = ['active', 'suspended', 'deleted']
# status_weights = [85, 5, 10]


# ==============================
# 3. 데이터 생성용 함수
# ==============================

def generate_password_hash():
    """비밀번호를 faker로 생성하고 SHA-256 해시로 변환"""
    raw_pw = fake_kr.password()
    return hashlib.sha256(raw_pw.encode()).hexdigest()

def get_faker_by_country(country):
    """국가별 Faker 선택"""
    return {
        'KR': fake_kr,
        'US': fake_us,
        'JP': fake_jp,
        'CN': fake_cn,
        'VN': fake_vn
    }[country]

def get_city_by_country(country):
    """국가별 도시 생성"""
    if country == 'KR':
        return random.choices(kr_cities, weights=kr_city_weights)[0]
    if country == 'US':
        return random.choice(us_cities)
    if country == 'JP':
        return random.choice(jp_cities)
    if country == 'CN':
        return random.choice(cn_cities)
    if country == 'VN':
        return random.choice(vn_cities)

def generate_birth_date():
    """연령대 분포 기반으로 생일 생성"""
    age_range = random.choices(age_ranges, weights=age_weights)[0]
    age = random.randint(age_range[0], age_range[1])

    today = datetime.now()
    birth_year = today.year - age
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)

    return datetime(birth_year, birth_month, birth_day).date()

def generate_is_adult_verified(birth_date):
    """만 20세 이상: 95% 확률 인증 / 미만은 0"""
    age = (datetime.now().date() - birth_date).days // 365
    if age < 20:
        return 0
    return random.choices([0, 1], weights=[5, 95])[0]


# ==============================
# 4. 유저 1명 생성 함수
# ==============================
def generate_single_user():
    """유저 한 명을 생성하여 튜플로 반환"""

    today = datetime.now().date()
    now_datetime = datetime.now()

    country = random.choices(countries, weights=country_weights)[0]
    fake = get_faker_by_country(country)

    birth_date = generate_birth_date()

    # 요청사항 반영: signup_date = 오늘
    signup_date = today

    # 요청사항 반영: last_login_date = 오늘(최신 시점)
    last_login_date = now_datetime

    email = f"user_{random.randint(10000, 99999)}@ottservice.com"

    return (
        email,
        generate_password_hash(),
        fake.name(),
        random.choices(genders, weights=gender_weights)[0],
        birth_date,
        country,
        get_city_by_country(country),
        signup_date,
        'active',  # account_status
        generate_is_adult_verified(birth_date),
        last_login_date,
        random.choices(devices, weights=device_weights)[0],
        random.choices([0, 1], weights=[45, 55])[0]
    )


# ==============================
# 5. DB Insert 수행
# ==============================

# RDS 연결
connection = mysql.connector.connect(
    host = "ott-project-db.c5coqywgszdi.ap-northeast-2.rds.amazonaws.com",
    user = "admin",
    password = "sesac123!",
    database = "ott_service"
)

def insert_new_user():
    cursor = connection.cursor(dictionary=True)

    insert_sql = """
        INSERT INTO users (
            email, password_hash, name, gender, birth_date, country, city,
            signup_date, account_status, is_adult_verified, last_login_date,
            device_last_used, push_opt_in
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    # 1명 생성
    user = generate_single_user()

    print("생성된 유저 데이터:")
    print(user)

    cursor.execute(insert_sql, user)
    connection.commit()
    new_user_id = cursor.lastrowid
    cursor.close()
    return new_user_id