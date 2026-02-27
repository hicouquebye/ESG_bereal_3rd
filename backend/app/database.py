import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# .env 파일 로드 (프로젝트 루트 기준)
load_dotenv()

# MySQL 연결 설정
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "esg")

# 비밀번호에 특수문자(@, # 등)가 있을 수 있으므로 URL 인코딩
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,          # 다시 5로 하향 조정
    max_overflow=0,       # 초과 연결 허용 안 함 (안정성 우선)
    pool_pre_ping=True,
    pool_recycle=1800,    # 재활용 주기를 30분으로 단축
    pool_timeout=10,      # 연결 대기 시간 10초 제한
    connect_args={"connect_timeout": 5}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI Dependency용 DB 세션"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
