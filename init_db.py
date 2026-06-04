import sqlite3

# 1. 데이터베이스 파일 생성 및 연결 (폴더 내에 rpg-database.db 파일이 생깁니다)
conn = sqlite3.connect("rpg-database.db")
cursor = conn.cursor()

# 2. 난이도 기준표 테이블 생성
cursor.execute("""
CREATE TABLE IF NOT EXISTS difficulty_config (
    difficulty TEXT PRIMARY KEY,
    reward_xp INTEGER,
    reward_gold INTEGER
)
""")

# 3. 주기 코드표 테이블 생성
cursor.execute("""
CREATE TABLE IF NOT EXISTS frequency_config (
    code INTEGER PRIMARY KEY,
    type_name TEXT
)
""")

# 4. 퀘스트 마스터 DB 테이블 생성 (외래키 등으로 엮을 수 있지만, 우선 직관적으로 설계)
cursor.execute("""
CREATE TABLE IF NOT EXISTS master_quest_db (
    quest_id TEXT PRIMARY KEY,
    quest_name TEXT,
    difficulty TEXT,
    reward_xp INTEGER,
    reward_gold INTEGER,
    frequency INTEGER,
    status TEXT
)
""")

# 4-2. 매일 밤의 정산 로그를 기록할 테이블 생성
cursor.execute("""
CREATE TABLE IF NOT EXISTS quest_history_log (
    log_date TEXT PRIMARY KEY,
    day_of_week TEXT,
    completed_ids TEXT,
    total_xp INTEGER,
    total_gold INTEGER
)
""")

# 5. 초기 데이터 마이그레이션 (기존 넘버스/CSV 데이터 주입)
# 5-1. 난이도 데이터
cursor.executemany("""
INSERT OR IGNORE INTO difficulty_config VALUES (?, ?, ?)
""", [('E', 10, 5), ('N', 30, 15), ('H', 50, 25)])

# 5-2. 주기 데이터
cursor.executemany("""
INSERT OR IGNORE INTO frequency_config VALUES (?, ?)
""", [
    (1, '일요일'), (2, '월요일'), (3, '화요일'), (4, '수요일'), 
    (5, '목요일'), (6, '금요일'), (7, '토요일'), (8, 'Daily'), 
    (9, 'Monthly'), (10, 'Month_First'), (11, 'Month_Last')
])

# 5-3. 샘플 퀘스트 데이터
cursor.executemany("""
INSERT OR IGNORE INTO master_quest_db VALUES (?, ?, ?, ?, ?, ?, ?)
""", [
    ('Q2606-01', '기상 후 스트레칭', 'E', 10, 5, 8, 'Active'),
    ('Q2606-02', '스페인어 원서 3페이지 읽기', 'N', 30, 15, 8, 'Active'),
    ('Q2606-03', '풋볼 전술 분석 로그 작성', 'H', 50, 25, 3, 'Active'),
    ('Q2606-04', '월말 피지컬 트레이닝 리포트 정산', 'H', 50, 25, 11, 'Active')
])

# 변경사항 저장 및 연결 종료
conn.commit()
conn.close()

print("🎉 SQLite 인생 RPG 데이터베이스가 완벽하게 초기화되었습니다!")