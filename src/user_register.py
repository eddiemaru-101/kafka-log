import random
import hashlib
from datetime import datetime
from typing import Dict
import time
from faker import Faker
import pytz


class UserRegister:
    """
    신규 유저 데이터 생성
    
    책임:
    - Faker 기반 유저 정보 생성
    - 국가/도시/연령대 분포 적용
    - 타임스탬프 기반 signup_date 설정
    """
    
    def __init__(self, config: dict):
        """
        Args:
            config: config.toml 로딩된 딕셔너리
        """
        self.config = config
        
        # 타임존 설정
        self.tz = pytz.timezone(config["global"]["timezone"])
        
        # Faker 인스턴스 (국가별)
        self.fake_kr = Faker('ko_KR')
        self.fake_us = Faker('en_US')
        self.fake_jp = Faker('ja_JP')
        self.fake_cn = Faker('zh_CN')
        self.fake_vn = Faker('vi_VN')
        
        # 유저 생성 분포 설정
        self.countries = ['KR', 'CN', 'US', 'JP', 'VN']
        self.country_weights = [95.5, 3, 1, 1, 0.5]
        
        self.genders = [0, 1, 2]
        self.gender_weights = [49.5, 49.5, 1]
        
        self.age_ranges = [(15, 19), (20, 29), (30, 39), (40, 49), (50, 59), (60, 70)]
        self.age_weights = [8, 16, 21, 26, 21, 7]
        
        self.devices = ['mobile', 'tv', 'tablet', 'desktop', 'console']
        self.device_weights = [60.9, 18, 11, 10, 0.1]
        
        # 도시 설정
        self.kr_cities = ['서울', '경기', '인천', '부산', '대구', '울산', '경북', '경남',
                         '대전', '세종', '충북', '충남', '광주', '전북', '전남', '강원', '제주']
        self.kr_city_weights = [18, 26, 6, 7, 5, 2, 5, 6, 3, 1, 3, 4, 3, 3, 4, 3, 1]
        
        self.us_cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Seattle']
        self.jp_cities = ['Tokyo', 'Osaka', 'Kyoto', 'Yokohama', 'Nagoya']
        self.cn_cities = ['Beijing', 'Shanghai', 'Shenzhen', 'Guangzhou', 'Chengdu']
        self.vn_cities = ['Hanoi', 'Ho Chi Minh', 'Da Nang']
        
        print(f"✅ UserRegister 초기화 완료")
    
    def _get_faker_by_country(self, country: str):
        """국가별 Faker 반환"""
        return {
            'KR': self.fake_kr,
            'US': self.fake_us,
            'JP': self.fake_jp,
            'CN': self.fake_cn,
            'VN': self.fake_vn
        }[country]
    
    def _get_city_by_country(self, country: str) -> str:
        """국가별 도시 생성"""
        if country == 'KR':
            return random.choices(self.kr_cities, weights=self.kr_city_weights)[0]
        if country == 'US':
            return random.choice(self.us_cities)
        if country == 'JP':
            return random.choice(self.jp_cities)
        if country == 'CN':
            return random.choice(self.cn_cities)
        if country == 'VN':
            return random.choice(self.vn_cities)
    
    def _generate_birth_date(self, signup_timestamp: datetime) -> datetime.date:
        """연령대 분포 기반 생일 생성"""
        age_range = random.choices(self.age_ranges, weights=self.age_weights)[0]
        age = random.randint(age_range[0], age_range[1])
        
        signup_date = signup_timestamp.astimezone(self.tz)
        birth_year = signup_date.year - age
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        
        return datetime(birth_year, birth_month, birth_day).date()
    
    def _generate_is_adult_verified(self, birth_date: datetime.date, signup_timestamp: datetime) -> int:
        """성인 인증 여부 (만 20세 이상 95% 확률)"""
        signup_date = signup_timestamp.astimezone(self.tz).date()
        age = (signup_date - birth_date).days // 365
        if age < 20:
            return 0
        return random.choices([0, 1], weights=[5, 95])[0]
    
    def _generate_password_hash(self) -> str:
        """비밀번호 해시 생성"""
        raw_pw = self.fake_kr.password()
        return hashlib.sha256(raw_pw.encode()).hexdigest()
    
    def create_user_data(self, signup_timestamp: datetime) -> Dict:
        """
        신규 유저 데이터 생성
        
        Args:
            signup_timestamp: 회원가입 타임스탬프
        
        Returns:
            유저 데이터 딕셔너리 (DB INSERT용)
        """
        signup_date = signup_timestamp.astimezone(self.tz).date()
        
        # 국가 선택
        country = random.choices(self.countries, weights=self.country_weights)[0]
        fake = self._get_faker_by_country(country)
        
        # 생일 생성
        birth_date = self._generate_birth_date(signup_timestamp)
        
        # 이메일 생성
        email = f"user_{signup_timestamp.timestamp()}_{random.randint(1000, 9999)}@ottservice.com"
        
        user_data = {
            'email': email,
            'password_hash': self._generate_password_hash(),
            'name': fake.name(),
            'gender': random.choices(self.genders, weights=self.gender_weights)[0],
            'birth_date': birth_date,
            'country': country,
            'city': self._get_city_by_country(country),
            'signup_date': signup_date,
            'account_status': 'active',
            'is_adult_verified': self._generate_is_adult_verified(birth_date, signup_timestamp),
            'last_login_date': signup_timestamp,
            'device_last_used': random.choices(self.devices, weights=self.device_weights)[0],
            'push_opt_in': random.choices([0, 1], weights=[45, 55])[0]
        }
        
        return user_data