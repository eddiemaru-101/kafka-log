import random
from datetime import datetime, timedelta
from typing import Generator
import calendar
import pytz


class LogDateGenerator:
    """
    월별 타임스탬프 생성기
    
    책임:
    - 지정된 월의 모든 날짜에 대해 타임스탬프 생성
    - 요일별 가중치 적용 (월~일)
    - 시간대별 가중치 적용 (0-6시, 6-9시, ...)
    - Generator 패턴으로 메모리 효율적 반환
    """
    
    def __init__(self, config: dict):
        """
        Args:
            config: config.toml 로딩된 딕셔너리
        """
        self.config = config
        
        # 타임존 설정
        self.tz = pytz.timezone(config["global"]["timezone"])
        
        # 요일별 가중치 (월~일)
        day_ratio = config["date_generation"]["day_of_week_ratio"]
        self.day_weights = [
            day_ratio["monday"],
            day_ratio["tuesday"],
            day_ratio["wednesday"],
            day_ratio["thursday"],
            day_ratio["friday"],
            day_ratio["saturday"],
            day_ratio["sunday"]
        ]
        
        # 시간대별 가중치 파싱
        hour_dist = config["date_generation"]["hour_distribution"]
        self.hour_weights = self._parse_hour_distribution(hour_dist)
        
        print(f"✅ LogDateGenerator 초기화 완료")
        print(f"   - 요일 가중치: {self.day_weights}")
        print(f"   - 시간대별 가중치 설정 완료")
    
    def _parse_hour_distribution(self, hour_dist: dict) -> list:
        """
        시간대별 가중치를 24시간 배열로 변환
        
        Args:
            hour_dist: {"0-6": 0.05, "6-9": 0.10, ...}
        
        Returns:
            24개 요소의 가중치 리스트 [0시, 1시, ..., 23시]
        """
        hour_weights = [0.0] * 24
        
        for time_range, weight in hour_dist.items():
            start, end = map(int, time_range.split('-'))
            hours_in_range = end - start
            weight_per_hour = weight / hours_in_range
            
            for hour in range(start, end):
                hour_weights[hour] = weight_per_hour
        
        return hour_weights
    
    def generate_timestamps(
        self,
        target_month: str,
        total_logs: int
    ) -> Generator[datetime, None, None]:
        """
        지정된 월의 타임스탬프 생성
        
        Args:
            target_month: "2025-01" 형식
            total_logs: 해당 월에 생성할 총 로그 개수
        
        Yields:
            datetime 객체 (타임존 적용됨)
        """
        year, month = map(int, target_month.split('-'))
        
        # 해당 월의 일수 계산
        _, days_in_month = calendar.monthrange(year, month)
        
        # 모든 날짜/시간 조합과 가중치 계산
        all_datetimes = []
        weights = []
        
        for day in range(1, days_in_month + 1):
            dt = datetime(year, month, day, tzinfo=self.tz)
            weekday = dt.weekday()  # 0=월, 6=일
            day_weight = self.day_weights[weekday]
            
            for hour in range(24):
                hour_weight = self.hour_weights[hour]
                combined_weight = day_weight * hour_weight
                
                if combined_weight > 0:
                    # 분/초는 랜덤하게 생성할 준비
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
        
        # 정렬 (시간 순서대로)
        sampled_datetimes.sort()
        
        # Generator로 반환
        for year, month, day, hour in sampled_datetimes:
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            timestamp = datetime(
                year, month, day, hour, minute, second,
                tzinfo=self.tz
            )
            
            yield timestamp
    
    def get_total_logs_for_month(
        self,
        target_month: str,
        mps: int,
        active_user_count: int
    ) -> int:
        """
        해당 월에 생성할 총 로그 개수 추정
        
        Args:
            target_month: "2025-01" 형식
            mps: Messages Per Second
            active_user_count: 활성 유저 수
        
        Returns:
            해당 월의 총 로그 개수
        """
        year, month = map(int, target_month.split('-'))
        _, days_in_month = calendar.monthrange(year, month)
        
        # 초당 mps * 86400초(1일) * 일수
        total_logs = mps * 86400 * days_in_month
        
        return total_logs