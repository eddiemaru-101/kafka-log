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

        # Kinesis 배치 전송 설정
        self.batch_size = sink_config.get("batch_size", 500)
        self.batch_timeout_ms = sink_config.get("batch_timeout_ms", 1000)

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
        self.aws_profile = sink_config.get("aws_profile", None)  # AWS CLI Profile

        # Kinesis 재시도 설정
        self.max_retries = sink_config.get("max_retries", 3)
        self.initial_backoff_ms = sink_config.get("initial_backoff_ms", 100)
        self.max_backoff_ms = sink_config.get("max_backoff_ms", 5000)

        # Kinesis client 초기화 (kinesis 모드일 때만)
        self.kinesis_client = None
        if self.sink_type == "kinesis":
            # AWS Profile이 지정된 경우 session 사용
            if self.aws_profile:
                session = boto3.Session(profile_name=self.aws_profile)
                self.kinesis_client = session.client('kinesis', region_name=self.kinesis_region)
            else:
                # Profile 미지정 시 기본 인증 방법 사용 (환경 변수, IAM Role 등)
                self.kinesis_client = boto3.client('kinesis', region_name=self.kinesis_region)

        # 시간별 오프셋 카운터 (파일명용)
        self.hourly_offsets: Dict[str, int] = defaultdict(int)

        # 현재 시간대 버퍼와 다음 시간대 버퍼 (두 개의 버퍼로 관리)
        self.current_hour_key: Optional[str] = None
        self.current_hour_buffer: List[Dict[str, Any]] = []

        self.next_hour_key: Optional[str] = None
        self.next_hour_buffer: List[Dict[str, Any]] = []

        # Kinesis 배치 전송용 버퍼 (streaming-batch 모드 전용)
        self.kinesis_batch_buffer: List[Dict[str, Any]] = []
        self.last_batch_send_time = time.time()

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
            if self.mode == "streaming-batch":
                print(f"   Batch Size: {self.batch_size}")
                print(f"   Batch Timeout: {self.batch_timeout_ms}ms")


    def write(self, log_event: Dict[str, Any]) -> None:
        """
        로그 쓰기 (모드에 따라 분기)

        Args:
            log_event: 로그 딕셔너리
        """
        if log_event is None:
            return

        if self.mode == "streaming-single":
            self.streaming_single_write(log_event)
        elif self.mode == "streaming-batch":
            self.streaming_batch_write(log_event)
        else:  # batch
            self.batch_write(log_event)


    def streaming_single_write(self, log_event: Dict[str, Any]) -> None:
        """
        Streaming Single 모드: Kinesis로 즉시 단일 전송 (put_record)

        지원: Kinesis만
        미지원: Local, S3

        Args:
            log_event: 로그 딕셔너리
        """
        if self.sink_type == "kinesis":
            self._write_to_kinesis_single(log_event)
        else:
            print(f"❌ Streaming 모드는 Kinesis만 지원합니다. (현재 sink_type: {self.sink_type})")
            return

        # MPS 제어
        if self.interval > 0:
            time.sleep(self.interval)

    def streaming_batch_write(self, log_event: Dict[str, Any]) -> None:
        """
        Streaming Batch 모드: Kinesis로 배치 전송 (put_records)

        지원: Kinesis만
        미지원: Local, S3

        Args:
            log_event: 로그 딕셔너리
        """
        if self.sink_type != "kinesis":
            print(f"❌ Streaming 모드는 Kinesis만 지원합니다. (현재 sink_type: {self.sink_type})")
            return

        # 버퍼에 추가
        self.kinesis_batch_buffer.append(log_event)

        # 배치 전송 조건 체크
        current_time = time.time()
        buffer_full = len(self.kinesis_batch_buffer) >= self.batch_size
        timeout_reached = (current_time - self.last_batch_send_time) * 1000 >= self.batch_timeout_ms

        if buffer_full or timeout_reached:
            self._flush_kinesis_batch()

        # MPS 제어
        if self.interval > 0:
            time.sleep(self.interval)


    def batch_write(self, log_event: Dict[str, Any]) -> None:
        """
        Batch 모드: 버퍼에 모아서 파일로 저장

        지원: Local, S3
        미지원: Kinesis

        Args:
            log_event: 로그 딕셔너리
        """
        if self.sink_type == "local":
            self._write_to_local(log_event)
        elif self.sink_type == "s3":
            self._write_to_s3(log_event)
        else:
            print(f"❌ Batch 모드는 Local/S3만 지원합니다. (현재 sink_type: {self.sink_type})")
            return

        # MPS 제어
        if self.interval > 0:
            time.sleep(self.interval)


    def _write_to_local(self, log_event: Dict[str, Any]) -> None:
        """
        로컬 파일에 JSON 형식으로 저장

        폴더 구조: {output_dir}/{topic}/year={YYYY}/month={MM}/day={DD}/hour={HH}/
        파일명: {topic}-{offset(6자리)}-{uuid}.json

        현재 시간대 버퍼와 다음 시간대 버퍼 두 개로 관리
        - 현재 시간대 로그 → 현재 버퍼에 추가
        - 다음 시간대 로그 → 다음 버퍼에 추가
        - 시간대 변경 시 → 현재 버퍼 flush, 다음 버퍼를 현재 버퍼로 승격
        """
        timestamp_str = log_event.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # ISO 8601 형식 지원 (2025-09-01T01:18:20.000Z)
        if "T" in timestamp_str:
            # 밀리초 제거 후 파싱
            timestamp_str_clean = timestamp_str.replace("Z", "").split(".")[0]
            timestamp = datetime.strptime(timestamp_str_clean, "%Y-%m-%dT%H:%M:%S")
        else:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

        year = timestamp.strftime("%Y")
        month = timestamp.strftime("%m")
        day = timestamp.strftime("%d")
        hour = timestamp.strftime("%H")

        hour_key = f"{year}-{month}-{day}-{hour}"

        # 첫 번째 로그인 경우 초기화
        if self.current_hour_key is None:
            self.current_hour_key = hour_key
            self.current_hour_buffer.append(log_event)
            return

        # 현재 시간대 로그인 경우
        if hour_key == self.current_hour_key:
            self.current_hour_buffer.append(log_event)

        # 다음 시간대 로그인 경우
        elif self.next_hour_key is None or hour_key == self.next_hour_key:
            if self.next_hour_key is None:
                self.next_hour_key = hour_key
            self.next_hour_buffer.append(log_event)

        # 새로운 시간대로 전환 (현재 → 다음 → 새로운)
        else:
            # 1. 현재 시간대 버퍼를 flush
            self._flush_buffer_to_json(self.current_hour_key, self.current_hour_buffer)

            # 2. 다음 시간대 버퍼를 현재 시간대로 승격
            self.current_hour_key = self.next_hour_key
            self.current_hour_buffer = self.next_hour_buffer

            # 3. 새로운 다음 시간대 설정
            self.next_hour_key = hour_key
            self.next_hour_buffer = [log_event]


    def _flush_buffer_to_json(self, hour_key: str, buffer: List[Dict[str, Any]]) -> None:
        """
        특정 시간대 버퍼에 쌓인 로그를 JSON 파일로 저장

        Args:
            hour_key: "YYYY-MM-DD-HH" 형식의 시간 키
            buffer: 저장할 로그 리스트
        """
        if not buffer:
            return

        # 시간순으로 정렬
        sorted_logs = sorted(buffer, key=lambda x: x.get("timestamp", ""))

        # 첫 번째 로그의 타임스탬프로 경로 결정
        first_log = sorted_logs[0]
        timestamp_str = first_log.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # ISO 8601 형식 지원 (2025-09-01T01:18:20.000Z)
        if "T" in timestamp_str:
            # 밀리초 제거 후 파싱
            timestamp_str_clean = timestamp_str.replace("Z", "").split(".")[0]
            timestamp = datetime.strptime(timestamp_str_clean, "%Y-%m-%dT%H:%M:%S")
        else:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

        year = timestamp.strftime("%Y")
        month = timestamp.strftime("%m")
        day = timestamp.strftime("%d")
        hour = timestamp.strftime("%H")

        # 폴더 구조 생성
        dir_path = Path(self.output_dir) / self.topic / f"year={year}" / f"month={month}" / f"day={day}" / f"hour={hour}"
        dir_path.mkdir(parents=True, exist_ok=True)

        # 파일명 생성: {topic}-{offset(6자리)}-{uuid}.json
        offset = self.hourly_offsets[hour_key]
        file_uuid = str(uuid.uuid4())[:6]  # 짧은 UUID
        filename = f"{self.topic}-{offset:06d}-{file_uuid}.json"
        file_path = dir_path / filename

        # detail에서 null 값 제거
        def remove_nulls(detail: dict) -> dict:
            return {k: v for k, v in detail.items() if v is not None}

        # NDJSON (Newline Delimited JSON) 형식으로 저장
        # Kinesis에서 처리하기 위해 각 로그를 한 줄씩 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            for log in sorted_logs:
                log_entry = {
                    "timestamp": log["timestamp"],
                    "user_id": log["user_id"],
                    "event_category": log["event_category"],
                    "event_type": log["event_type"],
                    "detail": remove_nulls(log["detail"])
                }
                # 각 로그를 한 줄로 작성 (줄바꿈으로 구분)
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        print(f"💾 JSON 저장: {filename} ({len(sorted_logs)}개 로그)")

        # offset 증가
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


    def _write_to_kinesis_single(self, log_event: Dict[str, Any]) -> None:
        """
        Kinesis Data Streams로 단일 전송 (put_record)

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
            print(f"✅ Kinesis 단일 전송 성공: ShardId={response['ShardId']}, SequenceNumber={response['SequenceNumber']}")

        except ClientError as e:
            print(f"❌ Kinesis 전송 실패: {e}")
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")

    def _flush_kinesis_batch(self) -> None:
        """
        Kinesis 배치 버퍼를 비우고 put_records로 전송
        """
        if not self.kinesis_batch_buffer:
            return

        if self.kinesis_client is None:
            print("❌ Kinesis client가 초기화되지 않았습니다.")
            return

        try:
            # put_records 요청 준비
            records = []
            for log_event in self.kinesis_batch_buffer:
                partition_key = str(log_event.get("user_id", "default"))
                data = json.dumps(log_event, ensure_ascii=False).encode('utf-8')

                records.append({
                    'Data': data,
                    'PartitionKey': partition_key
                })

            # Kinesis로 배치 전송
            response = self.kinesis_client.put_records(
                StreamName=self.kinesis_stream_name,
                Records=records
            )

            # 결과 확인
            failed_count = response.get('FailedRecordCount', 0)
            success_count = len(records) - failed_count

            print(f"✅ Kinesis 배치 전송: {success_count}/{len(records)}개 성공", end="")
            if failed_count > 0:
                print(f" ({failed_count}개 실패)", end="")
            print()

            # 실패한 레코드 재시도 (선택적)
            if failed_count > 0:
                failed_records = []
                for i, record_response in enumerate(response['Records']):
                    if 'ErrorCode' in record_response:
                        failed_records.append(self.kinesis_batch_buffer[i])

                if failed_records:
                    print(f"⚠️  {len(failed_records)}개 레코드 재시도 필요")
                    # TODO: 재시도 로직 구현 (옵션)

            # 버퍼 초기화
            self.kinesis_batch_buffer.clear()
            self.last_batch_send_time = time.time()

        except ClientError as e:
            print(f"❌ Kinesis 배치 전송 실패: {e}")
            # 버퍼 유지 (재시도 가능)
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            # 버퍼 초기화 (복구 불가능한 오류)
            self.kinesis_batch_buffer.clear()
            self.last_batch_send_time = time.time()


    def close(self) -> None:
        """리소스 정리 및 마지막 버퍼 flush"""
        # Kinesis 배치 버퍼 flush (streaming-batch 모드)
        if self.mode == "streaming-batch" and self.kinesis_batch_buffer:
            print(f"🔄 마지막 Kinesis 배치 전송 중... ({len(self.kinesis_batch_buffer)}개)")
            self._flush_kinesis_batch()

        # 현재 시간대 버퍼 flush
        if self.current_hour_key is not None and self.current_hour_buffer:
            self._flush_buffer_to_json(self.current_hour_key, self.current_hour_buffer)

        # 다음 시간대 버퍼 flush
        if self.next_hour_key is not None and self.next_hour_buffer:
            self._flush_buffer_to_json(self.next_hour_key, self.next_hour_buffer)

        print("✅ LogSink 종료")
