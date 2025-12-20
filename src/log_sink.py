import os
import json
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import defaultdict
import boto3
from botocore.exceptions import ClientError
import pandas as pd


class LogSink:
    """
    로그 최종 처리 클래스

    책임:
    - 로그 출력 방식 결정 (로컬/S3/Kinesis)
    - MSK S3 Sink Connector와 동일한 폴더 구조/파일명 생성
    - MPS(Messages Per Second) 제어
    """

    def __init__(self, config: dict):
        """
        Args:
            config: config.toml 전체 dict
        """
        self.config = config

        # Global 설정
        global_config = config.get("global", {})
        self.mode = global_config.get("generation_mode", "batch")

        # MPS 설정
        target_mps = global_config.get("target_mps", 0)
        if target_mps > 0:
            self.interval = 1.0 / target_mps
        else:
            self.interval = 0  # MPS 제한 없음

        # LogSink 전용 설정
        sink_config = config.get("log_sink", {})

        self.sink_type = sink_config.get("sink_type", "local")  # local, s3, kinesis

        # 로컬 저장 설정
        self.output_dir = sink_config.get("output_dir", "./output")
        self.topic = sink_config.get("topic", "user-logs")
        self.partition = sink_config.get("partition", 0)

        # S3 설정
        self.s3_bucket = sink_config.get("s3_bucket", "sesac-l1")
        self.s3_prefix = sink_config.get("s3_prefix", "raw-userlog")

        # Kinesis 설정
        self.kinesis_stream_name = sink_config.get("kinesis_stream_name", "user-logs-stream")
        self.kinesis_region = sink_config.get("kinesis_region", "ap-northeast-2")

        # Kinesis client 초기화 (kinesis 모드일 때만)
        self.kinesis_client = None
        if self.sink_type == "kinesis":
            self.kinesis_client = boto3.client('kinesis', region_name=self.kinesis_region)

        # 시간별 오프셋 카운터 (파일명용)
        self.hourly_offsets: Dict[str, int] = defaultdict(int)

        # 시간별 로그 버퍼 (시간별로 버퍼 분리하여 관리)
        # key: "YYYY-MM-DD-HH", value: 로그 리스트
        self.hourly_buffers: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # 현재 처리 중인 시간대 추적
        self.current_hour_key: Optional[str] = None

        print(f"✅ LogSink 초기화 완료")
        print(f"   Mode: {self.mode}")
        print(f"   Sink Type: {self.sink_type}")
        print(f"   Target MPS: {target_mps if target_mps > 0 else '제한 없음'}")
        if self.sink_type == "local":
            print(f"   Output Dir: {self.output_dir}")
            print(f"   Topic: {self.topic}")
        elif self.sink_type == "s3":
            print(f"   S3 Bucket: {self.s3_bucket}")
            print(f"   S3 Prefix: {self.s3_prefix}")
        elif self.sink_type == "kinesis":
            print(f"   Kinesis Stream: {self.kinesis_stream_name}")
            print(f"   Kinesis Region: {self.kinesis_region}")


    def write(self, log_event: Dict[str, Any]) -> None:
        """
        로그 쓰기

        Args:
            log_event: 로그 딕셔너리
        """
        if log_event is None:
            return

        # Sink Type에 따라 처리
        if self.sink_type == "local":
            self._write_to_local(log_event)
        elif self.sink_type == "s3":
            self._write_to_s3(log_event)
        elif self.sink_type == "kinesis":
            self._write_to_kinesis(log_event)

        # MPS 제어
        if self.interval > 0:
            time.sleep(self.interval)


    def _write_to_local(self, log_event: Dict[str, Any]) -> None:
        """
        로컬 파일에 Parquet 형식으로 저장

        폴더 구조: {output_dir}/{topic}/year={YYYY}/month={MM}/day={DD}/hour={HH}/
        파일명: {topic}-{offset(6자리)}-{uuid}.parquet

        시간별로 버퍼에 쌓고, 시간이 바뀌면 자동 flush
        """
        timestamp_str = log_event.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

        year = timestamp.strftime("%Y")
        month = timestamp.strftime("%m")
        day = timestamp.strftime("%d")
        hour = timestamp.strftime("%H")

        hour_key = f"{year}-{month}-{day}-{hour}"

        # 시간이 바뀌면 이전 시간대 로그를 flush
        if self.current_hour_key is not None and self.current_hour_key != hour_key:
            self._flush_buffer_to_parquet(self.current_hour_key)

        # 현재 시간대 업데이트
        self.current_hour_key = hour_key

        # 시간별 버퍼에 로그 추가
        self.hourly_buffers[hour_key].append(log_event)


    def _flush_buffer_to_parquet(self, hour_key: str) -> None:
        """
        특정 시간대 버퍼에 쌓인 로그를 Parquet 파일로 저장

        Args:
            hour_key: "YYYY-MM-DD-HH" 형식의 시간 키
        """
        if hour_key not in self.hourly_buffers or not self.hourly_buffers[hour_key]:
            return

        # 시간순으로 정렬
        sorted_logs = sorted(self.hourly_buffers[hour_key], key=lambda x: x.get("timestamp", ""))

        # 첫 번째 로그의 타임스탬프로 경로 결정
        first_log = sorted_logs[0]
        timestamp_str = first_log.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

        year = timestamp.strftime("%Y")
        month = timestamp.strftime("%m")
        day = timestamp.strftime("%d")
        hour = timestamp.strftime("%H")

        # 폴더 구조 생성
        dir_path = Path(self.output_dir) / self.topic / f"year={year}" / f"month={month}" / f"day={day}" / f"hour={hour}"
        dir_path.mkdir(parents=True, exist_ok=True)

        # 파일명 생성: {topic}-{offset(6자리)}-{uuid}.parquet
        offset = self.hourly_offsets[hour_key]
        file_uuid = str(uuid.uuid4())[:6]  # 짧은 UUID
        filename = f"{self.topic}-{offset:06d}-{file_uuid}.parquet"
        file_path = dir_path / filename

        # detail에서 null 값 제거
        def remove_nulls(detail: dict) -> dict:
            return {k: v for k, v in detail.items() if v is not None}

        # DataFrame 생성
        df_data = []
        for log in sorted_logs:
            df_data.append({
                "timestamp": log["timestamp"],
                "user_id": log["user_id"],
                "event_category": log["event_category"],
                "event_type": log["event_type"],
                "detail": remove_nulls(log["detail"])
            })

        df = pd.DataFrame(df_data)

        # Parquet 파일로 저장
        df.to_parquet(str(file_path), engine='pyarrow', compression='snappy', index=False)

        print(f"💾 Parquet 저장: {filename} ({len(sorted_logs)}개 로그)")

        # 버퍼 초기화 및 offset 증가
        del self.hourly_buffers[hour_key]
        self.hourly_offsets[hour_key] += 1


    def _write_to_s3(self, log_event: Dict[str, Any]) -> None:
        """
        S3에 저장 (향후 구현)

        TODO: boto3를 사용하여 S3에 업로드
        """
        # 일단 로컬에 저장한 후 S3 업로드하는 방식으로 구현 가능
        self._write_to_local(log_event)

        # TODO: S3 업로드 로직
        # import boto3
        # s3_client = boto3.client('s3')
        # s3_client.upload_file(local_file, bucket, key)


    def _write_to_kinesis(self, log_event: Dict[str, Any]) -> None:
        """
        Kinesis Data Streams로 전송

        Args:
            log_event: 로그 딕셔너리
        """
        if self.kinesis_client is None:
            print("❌ Kinesis client가 초기화되지 않았습니다.")
            return

        try:
            # user_id를 partition key로 사용 (같은 유저의 로그는 같은 샤드로)
            partition_key = str(log_event.get("user_id", "default"))

            # JSON을 바이트로 변환
            data = json.dumps(log_event, ensure_ascii=False).encode('utf-8')

            # Kinesis로 전송
            response = self.kinesis_client.put_record(
                StreamName=self.kinesis_stream_name,
                Data=data,
                PartitionKey=partition_key
            )

            # 성공 로그 (선택적)
            # print(f"✅ Kinesis 전송 성공: ShardId={response['ShardId']}, SequenceNumber={response['SequenceNumber']}")

        except ClientError as e:
            print(f"❌ Kinesis 전송 실패: {e}")
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")


    def close(self) -> None:
        """리소스 정리 및 마지막 버퍼 flush"""
        # 모든 시간대 버퍼를 parquet로 저장
        for hour_key in list(self.hourly_buffers.keys()):
            self._flush_buffer_to_parquet(hour_key)

        print("✅ LogSink 종료")
