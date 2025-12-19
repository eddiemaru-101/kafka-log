import sqlite3
import pandas as pd
from pathlib import Path

def convert_mock_db_to_parquet(db_path: str, output_dir: str):
    """
    SQLite Mock DB의 각 테이블을 개별 Parquet 파일로 저장하는 유틸리티
    """
    # 1. 저장 경로 설정 및 생성
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 2. SQLite 연결
    if not Path(db_path).exists():
        print(f"❌ 오류: DB 파일을 찾을 수 없습니다. ({db_path})")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 3. 사용자 테이블 목록 조회 (sqlite_로 시작하는 시스템 테이블 제외)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"🚀 Parquet 변환 시작 (대상: {len(tables)}개 테이블)")
        print("-" * 50)
        
        for table_name in tables:
            # 4. 테이블 데이터 로드
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            
            # 5. Parquet 파일로 저장 (Snappy 압축 사용)
            target_file = output_path / f"{table_name}.parquet"
            df.to_parquet(target_file, engine='pyarrow', index=False, compression='snappy')
            
            print(f" ✅ 저장 완료: {target_file}")
            
    except Exception as e:
        print(f" ❌ 실행 중 오류 발생: {e}")
    finally:
        conn.close()
        print("-" * 50)
        print("✨ 모든 변환 작업이 완료되었습니다.")

if __name__ == "__main__":
    # 설정된 경로 및 DB 파일명
    DB_FILE = "./ott_test.db"  # 실제 파일 위치에 맞춰 수정 가능
    SAVE_DIR = "./table_file/"
    
    convert_mock_db_to_parquet(DB_FILE, SAVE_DIR)