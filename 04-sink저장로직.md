### config 설정값
- sink_type = "local"
- generation_mode:  "batch"  일때
- sink_type : "local","s3"일 때

### sink 폴더 구조
- generation_mode:  "batch"  일때
- sink_type : "local","s3"일 때
- 목적: kinesis저장 로직과 동일한 폴더 구조, 파일명이 생성되도록하는게 목적
```
#S3 tree 구조
s3://<bucket>/<prefix>/
└── year=2025/
    └── month=01/
        └── day=15/
            └── hour=14/
                └── <delivery-stream-name>-<uuid>.parquet
#예시
s3://sesac-ott-project/bronze/user-activity-log/
└── year=2025/
    └── month=01/
        └── day=15/
            └── hour=14/
                ├── user-logs-000000-abcdef.parquet
                ├── user-logs-000001-ghijkl.parquet
```

### 저장파일
- 파일은 parquet로 저장된다.
- 로그 발생시간에 따라 prefix 파티셔닝에 맞게 저장된다.
- 시간당 하나의 parquet파일로 저장된다.
