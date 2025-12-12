import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import pytz

from schemas import LogEvent


class LogSink:
    """
    로그 출력 관리
    
    책임:
    - 3가지 출력 모드 지원
      1. local: 로컬 파일 시스템에 배치 저장 (MSK S3 Sink 구조)
      2. s3: AWS S3에 배치 업로드 (MSK S3 Sink 구조)
      3. kafka: 즉시 전송 (배치 없음)
    - JSON Lines 포맷
    """
    
    def __init__(self, config: dict):
        """
        Args:
            config: config.toml 로딩된 딕셔너리
        """
        self.config = config
        self.output_mode = config["log_sink"]["output_mode"]
        
        # 타임존
        self.tz = pytz.timezone(config["global"]["timezone"])
        
        # 모드별 초기화
        if self.output_mode == "local":
            self.base_path = config["log_sink"]["local_base_path"]
            self.batch_size = config["log_sink"].get("batch_size", 100)
            self.topic_name = config["log_sink"].get("topic_name", "user-logs")
            
            # 배치 처리용
            self.partition_counters: Dict[str, int] = {}
            self.offset_counters: Dict[str, int] = {}
            self.buffers: Dict[str, List[LogEvent]] = {}
            
            self._init_local()
            
        elif self.output_mode == "s3":
            self.s3_bucket = config["log_sink"]["s3_bucket"]
            self.s3_prefix = config["log_sink"].get("s3_prefix", "logs")
            self.batch_size = config["log_sink"].get("batch_size", 100)
            self.topic_name = config["log_sink"].get("topic_name", "user-logs")
            
            # 배치 처리용
            self.partition_counters: Dict[str, int] = {}
            self.offset_counters: Dict[str, int] = {}
            self.buffers: Dict[str, List[LogEvent]] = {}
            
            self._init_s3()
            
        elif self.output_mode == "kafka":
            self.kafka_topic = config["log_sink"]["kafka_topic"]
            self.kafka_brokers = config["log_sink"]["kafka_brokers"]
            
            # Kafka는 배치 불필요
            self.batch_size = None
            self.buffers = None
            
            self._init_kafka()
        
        print(f"✅ LogSink 초기화 완료:")
        print(f"   - 출력 모드: {self.output_mode}")
        if self.output_mode == "local":
            print(f"   - Base Path: {self.base_path}")
            print(f"   - Batch Size: {self.batch_size}")
        elif self.output_mode == "s3":
            print(f"   - S3 Bucket: {self.s3_bucket}")
            print(f"   - S3 Prefix: {self.s3_prefix}")
            print(f"   - Batch Size: {self.batch_size}")
        elif self.output_mode == "kafka":
            print(f"   - Kafka Topic: {self.kafka_topic}")
            print(f"   - 즉시 전송 모드 (배치 없음)")
    
    def _init_local(self):
        """로컬 파일 모드 초기화"""
        Path(self.base_path).mkdir(parents=True, exist_ok=True)
        print(f"   - 로컬 디렉토리 생성: {self.base_path}")
    
    def _init_s3(self):
        """S3 모드 초기화"""
        try:
            import boto3
            self.s3_client = boto3.client('s3')
            print(f"   - S3 클라이언트 초기화 성공")
        except ImportError:
            print("   - ⚠️ boto3 미설치. pip install boto3 필요")
            self.s3_client = None
        except Exception as e:
            print(f"   - ⚠️ S3 초기화 실패: {e}")
            self.s3_client = None
    
    def _init_kafka(self):
        """Kafka 모드 초기화"""
        try:
            from kafka import KafkaProducer
            
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_brokers,
                value_serializer=lambda v: v.encode('utf-8'),
                acks='all',
                retries=3,
                compression_type='gzip'
            )
            print(f"   - Kafka Producer 연결 성공")
        except ImportError:
            print("   - ⚠️ kafka-python 미설치. pip install kafka-python 필요")
            self.producer = None
        except Exception as e:
            print(f"   - ⚠️ Kafka 연결 실패: {e}")
            self.producer = None
    
    # ========== 공통 헬퍼 메서드 ==========
    
    def _get_hour_key(self, timestamp: datetime) -> str:
        """시간대 키 생성 (버퍼 분리용)"""
        dt = timestamp.astimezone(self.tz)
        return f"{dt.year}-{dt.month:02d}-{dt.day:02d}-{dt.hour:02d}"
    
    def _get_partition_path(self, timestamp: datetime) -> str:
        """MSK S3 Sink 호환 파티션 경로"""
        dt = timestamp.astimezone(self.tz)
        return f"year={dt.year}/month={dt.month:02d}/day={dt.day:02d}/hour={dt.hour:02d}"
    
    def _get_partition_number(self, hour_key: str) -> int:
        """파티션 번호 생성 (0, 1, 2 순환)"""
        if hour_key not in self.partition_counters:
            self.partition_counters[hour_key] = 0
        
        partition = self.partition_counters[hour_key] % 3
        self.partition_counters[hour_key] += 1
        return partition
    
    def _get_offset(self, partition_key: str, batch_size: int) -> int:
        """
        파티션별 오프셋 반환 및 증가
        
        Args:
            partition_key: "2025-01-15-14-p0" 형태
            batch_size: 이번 배치 크기
        
        Returns:
            현재 오프셋 (파일명에 사용)
        """
        if partition_key not in self.offset_counters:
            self.offset_counters[partition_key] = 0
        
        current_offset = self.offset_counters[partition_key]
        
        # 다음을 위해 오프셋 증가
        self.offset_counters[partition_key] += batch_size
        
        return current_offset
    
    def _get_file_name(self, partition: int, offset: int) -> str:
        """MSK S3 Sink 호환 파일명"""
        return f"{self.topic_name}+{partition}+{offset:010d}.json"
    
    # ========== Write 메서드 ==========
    
    def write(self, log_event: LogEvent):
        """
        로그 이벤트 출력
        
        - Kafka: 즉시 전송
        - Local/S3: 버퍼에 추가 → batch_size 도달 시 flush
        """
        if self.output_mode == "kafka":
            self._send_to_kafka(log_event)
        else:
            self._add_to_buffer(log_event)
    
    def write_batch(self, log_events: List[LogEvent]):
        """여러 로그 이벤트를 한 번에 출력"""
        for log_event in log_events:
            self.write(log_event)
    
    # ========== Kafka 즉시 전송 ==========
    
    def _send_to_kafka(self, log_event: LogEvent):
        """Kafka로 즉시 전송 (배치 없음)"""
        if not self.producer:
            print("⚠️ Kafka Producer 없음")
            return
        
        try:
            json_str = log_event.model_dump_json(exclude_none=True)
            self.producer.send(self.kafka_topic, value=json_str)
        except Exception as e:
            print(f"⚠️ Kafka 전송 실패: {e}")
    
    # ========== Local/S3 배치 처리 ==========
    
    def _add_to_buffer(self, log_event: LogEvent):
        """버퍼에 추가 (Local/S3용)"""
        hour_key = self._get_hour_key(log_event.timestamp)
        
        if hour_key not in self.buffers:
            self.buffers[hour_key] = []
        
        self.buffers[hour_key].append(log_event)
        
        # batch_size 도달 시 flush
        if len(self.buffers[hour_key]) >= self.batch_size:
            self._flush_hour_buffer(hour_key)
    
    def _flush_hour_buffer(self, hour_key: str):
        """특정 시간대 버퍼 flush"""
        if hour_key not in self.buffers or not self.buffers[hour_key]:
            return
        
        buffer = self.buffers[hour_key]
        
        if self.output_mode == "local":
            self._flush_local(buffer, hour_key)
        elif self.output_mode == "s3":
            self._flush_s3(buffer, hour_key)
        
        # 버퍼 비우기
        self.buffers[hour_key].clear()
    
    def flush(self):
        """모든 버퍼 flush"""
        if self.output_mode == "kafka":
            if self.producer:
                self.producer.flush()
                print("✅ Kafka Producer flush 완료")
        else:
            for hour_key in list(self.buffers.keys()):
                self._flush_hour_buffer(hour_key)
    
    def _flush_local(self, buffer: List[LogEvent], hour_key: str):
        """로컬 파일 저장"""
        if not buffer:
            return
        
        first_log = buffer[0]
        partition_path = self._get_partition_path(first_log.timestamp)
        
        partition = self._get_partition_number(hour_key)
        partition_key = f"{hour_key}-p{partition}"
        
        # 실제 배치 크기 전달
        actual_batch_size = len(buffer)
        offset = self._get_offset(partition_key, actual_batch_size)
        
        file_name = self._get_file_name(partition, offset)
        
        full_dir = Path(self.base_path) / partition_path
        full_dir.mkdir(parents=True, exist_ok=True)
        full_path = full_dir / file_name
        
        with open(full_path, 'w', encoding='utf-8') as f:
            for log_event in buffer:
                json_line = log_event.model_dump_json(exclude_none=True)
                f.write(json_line + '\n')
        
        print(f"✅ 로그 {len(buffer)}건 저장: {full_path}")
    
    def _flush_s3(self, buffer: List[LogEvent], hour_key: str):
        """S3 업로드"""
        if not self.s3_client:
            print("⚠️ S3 클라이언트 없음")
            return
        
        if not buffer:
            return
        
        first_log = buffer[0]
        partition_path = self._get_partition_path(first_log.timestamp)
        
        partition = self._get_partition_number(hour_key)
        partition_key = f"{hour_key}-p{partition}"
        
        # 실제 배치 크기 전달
        actual_batch_size = len(buffer)
        offset = self._get_offset(partition_key, actual_batch_size)
        
        file_name = self._get_file_name(partition, offset)
        s3_key = f"{self.s3_prefix}/{partition_path}/{file_name}"
        
        json_lines = '\n'.join([
            log_event.model_dump_json(exclude_none=True)
            for log_event in buffer
        ]) + '\n'
        
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=json_lines.encode('utf-8'),
                ContentType='application/json'
            )
            print(f"✅ 로그 {len(buffer)}건 S3 업로드: s3://{self.s3_bucket}/{s3_key}")
        except Exception as e:
            print(f"⚠️ S3 업로드 실패: {e}")
    
    def close(self):
        """리소스 정리"""
        self.flush()
        
        if self.output_mode == "kafka" and self.producer:
            self.producer.close()
            print("   - Kafka Producer 종료")
        
        print("✅ LogSink 종료")