import random
import calendar
from datetime import datetime
from typing import Generator
import pytz


class LogDateGenerator:
    """
    타임스탬프 생성기
    
    책임:
    - 월별 총 로그 개수 계산 (DAU × 1인당 로그 × 일수)
    - 요일/시간대별 가중치 기반 타임스탬프 생성
    - Generator 패턴으로 메모리 효율적 반환
    """
    
    def __init__(self, config: dict):
        """
        Args:
            config: config_v2.toml 전체 dict
        """
        self.config = config
        
        # 타임존 설정
        timezone = config["global"]["timezone"]
        self.tz = pytz.timezone(timezone)
        
        print(f"✅ LogDateGenerator 초기화 완료 (timezone: {timezone})")
    
    
    def calculate_total_logs(
        self,
        target_month: str,
        dau: int,
        logs_per_user_per_day: int
    ) -> int:
        """
        월별 총 로그 개수 계산
        
        Args:
            target_month: "2025-01" 형식
            dau: Daily Active Users
            logs_per_user_per_day: 1인당 일일 로그 발생 수
        
        Returns:
            해당 월의 총 로그 개수
        
        계산식:
            총 로그 수 = DAU × 1인당 로그 × 월 일수
        """
        year, month = map(int, target_month.split('-'))
        _, days_in_month = calendar.monthrange(year, month)
        
        total_logs = dau * logs_per_user_per_day * days_in_month
        
        return total_logs
    
    
    def generate_now(self) -> datetime:
        """
        현재 시간 반환 (Streaming 모드용)

        Returns:
            현재 시간 (타임존 적용됨)
        """
        return datetime.now(self.tz)


    def generate_timestamps(
        self,
        target_month: str,
        total_logs: int
    ) -> Generator[datetime, None, None]:
        """
        지정된 월의 타임스탬프 생성 (Batch 모드용)

        Args:
            target_month: "2025-01" 형식
            total_logs: 해당 월에 생성할 총 로그 개수

        Yields:
            datetime 객체 (타임존 적용됨, 시간 순서대로 정렬됨)

        특징:
            - 요일별 가중치 적용 (config에서 읽음)
            - 시간대별 가중치 적용 (config에서 읽음)
            - 분/초는 랜덤 생성
        """
        year, month = map(int, target_month.split('-'))
        _, days_in_month = calendar.monthrange(year, month)
        
        # 요일별/시간대별 가중치 로딩
        day_weights = self._load_day_weights()  
        # 예시: [0.10, 0.12, 0.13, 0.12, 0.20, 0.15, 0.18]  
        # [월, 화, 수, 목, 금, 토, 일]
        hour_weights = self._load_hour_weights()
        # 실제 반환값 (24개 요소):
        # [
        #     0.00833, 0.00833, 0.00833, 0.00833, 0.00833, 0.00833,  # 0-5시
        #     0.03333, 0.03333, 0.03333,                              # 6-8시
        #     0.05, 0.05, 0.05,                                       # 9-11시
        #     0.05, 0.05,                                             # 12-13시
        #     0.025, 0.025, 0.025, 0.025,                             # 14-17시
        #     0.0875, 0.0875, 0.0875, 0.0875,                         # 18-21시
        #     0.075, 0.075                                            # 22-23시
        # ]


        # 모든 날짜/시간 조합과 가중치 계산
        all_datetimes = []
        weights = []
        
        for day in range(1, days_in_month + 1):
            dt = datetime(year, month, day, tzinfo=self.tz)
            weekday = dt.weekday()  # 0=월요일, 6=일요일
            day_weight = day_weights[weekday]
            
            for hour in range(24):
                hour_weight = hour_weights[hour]
                combined_weight = day_weight * hour_weight
                
                if combined_weight > 0:
                    all_datetimes.append((year, month, day, hour))
                    weights.append(combined_weight)
        
        # 가중치 정규화 (합이 1이 되도록)
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        
        # total_logs 개수만큼 샘플링
        sampled_datetimes = random.choices(
            all_datetimes,
            weights=normalized_weights,
            k=total_logs
        )
        
        # 분/초까지 포함한 완전한 타임스탬프 리스트 생성
        full_timestamps = []
        for year, month, day, hour in sampled_datetimes:
            minute = random.randint(0, 59)
            second = random.randint(0, 59)

            timestamp = datetime(
                year, month, day, hour, minute, second,
                tzinfo=self.tz
            )
            full_timestamps.append(timestamp)

        # 시간 순서대로 정렬 (분/초까지 포함)
        full_timestamps.sort()

        # Generator로 반환
        for timestamp in full_timestamps:
            yield timestamp
    
    
    def _load_day_weights(self) -> list:
        """
        요일별 가중치 로딩
        
        Returns:
            7개 요소 리스트 [월, 화, 수, 목, 금, 토, 일]
        """
        # config에 date_generator 섹션이 있으면 사용, 없으면 균등 분포
        if "date_generator" in self.config:
            day_ratio = self.config["date_generator"].get("day_of_week_ratio", {})
            return [
                day_ratio.get("monday", 1/7), # "monday"가 딕셔너리에 있으면 → 그 값을 반환, 없으면 → 1/7 (default)를 반환
                day_ratio.get("tuesday", 1/7),
                day_ratio.get("wednesday", 1/7),
                day_ratio.get("thursday", 1/7),
                day_ratio.get("friday", 1/7),
                day_ratio.get("saturday", 1/7),
                day_ratio.get("sunday", 1/7)
            ]
        # 반환값 예시: [0.10, 0.12, 0.13, 0.12, 0.20, 0.15, 0.18]
        # [월,   화,   수,   목,   금,   토,   일]

        else:
            # 균등 분포
            return [1/7] * 7
    
    
    def _load_hour_weights(self) -> list:
        """
        시간대별 가중치 로딩
        
        Returns:
            24개 요소 리스트 [0시, 1시, ..., 23시]
        """
        # config에 date_generator 섹션이 있으면 사용, 없으면 균등 분포
        if "date_generator" in self.config:
            hour_dist = self.config["date_generator"].get("hour_distribution", {})
            return self._parse_hour_distribution(hour_dist)
        else:
            # 균등 분포
            return [1/24] * 24
    
    
    def _parse_hour_distribution(self, hour_dist: dict) -> list:
        """
        시간대별 가중치를 24시간 배열로 변환
        
        Args:
            hour_dist: {"0-6": 0.05, "6-9": 0.10, ...}
        
        Returns:
            24개 요소의 가중치 리스트
        """
        hour_weights = [0.0] * 24  # [0.0, 0.0, 0.0, ..., 0.0]  # 총 24개
        
        for time_range, weight in hour_dist.items():  # ex) time_range = "0-6", weight = 0.05
            start, end = map(int, time_range.split('-'))  # start = 0, end = 6
            hours_in_range = end - start    # hours_in_range = 6 (0,1,2,3,4,5)
            weight_per_hour = weight / hours_in_range  # weight_per_hour = 0.05 / 6 ≈ 0.0083333333
            
            for hour in range(start, end):
                hour_weights[hour] = weight_per_hour
                #hour_weights[0] = 0.00833
                #hour_weights[1] = 0.00833
                #hour_weights[2] = 0.00833
                #hour_weights[3] = 0.00833
                #hour_weights[4] = 0.00833
                #hour_weights[5] = 0.00833
        
        return hour_weights
        # hour_weights = [
        #   0.00833,  # 0
        #   0.00833,  # 1
        #   0.00833,  # 2
        #   0.00833,  # 3
        #   0.00833,  # 4
        #   0.00833,  # 5
        #   0.03333,  # 6  (0.10 / 3)
        #   0.03333,  # 7
        #   0.03333,  # 8
        #   0.05,     # 9  (0.15 / 3)
        #   0.05,     # 10
        #   0.05,     # 11
        #   0.05,     # 12 (0.10 / 2)
        #   0.05,     # 13
        #   0.025,    # 14 (0.10 / 4)
        #   0.025,    # 15
        #   0.025,    # 16
        #   0.025,    # 17
        #   0.0875,   # 18 (0.35 / 4)
        #   0.0875,   # 19
        #   0.0875,   # 20
        #   0.0875,   # 21
        #   0.075,    # 22 (0.15 / 2)
        #   0.075     # 23
        #   ]