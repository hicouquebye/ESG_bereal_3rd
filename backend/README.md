# Backend README

ESG Dashboard 백엔드(FastAPI) 실행/구성 문서입니다.

## 1. 개요

- 언어/프레임워크: `Python + FastAPI + SQLAlchemy`
- 기본 DB: `MySQL` (`users`, `dashboard_emissions`)
- 주요 기능:
  - 인증/회원 (`/auth/*`)
  - 프로필 관리 (`/profile/*`)
  - 대시보드 데이터 (`/api/v1/dashboard/*`)
  - 시뮬레이터 시장 데이터 (`/api/v1/sim/*`)
  - AI 전략/챗봇 (`/api/v1/ai/*`)

## 2. 디렉토리 구조

```text
backend/
├── app/
│   ├── main.py                 # 코어 API 서버 엔트리포인트
│   ├── config.py               # .env 설정 로더
│   ├── database.py             # SQLAlchemy/MySQL 연결
│   ├── models.py               # User, DashboardEmission 모델
│   ├── schemas.py              # Pydantic 스키마
│   ├── init_db.py              # 테이블 초기화/시드
│   ├── routers/
│   │   ├── auth.py
│   │   ├── profile.py
│   │   ├── dashboard.py
│   │   ├── simulator.py
│   │   └── ai.py
│   ├── services/
│   │   ├── ai_service.py
│   │   ├── market_data.py
│   │   ├── eex_scraper.py
│   │   └── emission_extractor.py
│   └── static/profile/         # 업로드된 프로필 이미지
├── main.py                     # 통합 엔트리포인트 (search/stats 보조 API 포함)
├── requirements.txt
├── start.sh
├── debug_api.py
└── test_api.py
```

## 3. 빠른 실행

프로젝트 루트(`ESG_Dashboard`) 기준:

```bash
python3.11 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -r backend/requirements.txt
```

DB 초기화:

```bash
cd backend/app
python init_db.py
cd ../..
```

서버 실행(권장):

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Swagger: `http://127.0.0.1:8000/docs`

## 4. 엔트리포인트 2종

### A. `app.main` (권장)

```bash
uvicorn app.main:app --reload --port 8000
```

- 앱 핵심 라우터만 사용:
  - `/auth/*`
  - `/profile/*`
  - `/api/v1/dashboard/*`
  - `/api/v1/sim/*`
  - `/api/v1/ai/*`
- 프로필 이미지 정적 경로: `/static/*`

### B. `main` (통합 모드)

```bash
uvicorn main:app --reload --port 8000
```

- 위 핵심 라우터 + 보조 엔드포인트 제공:
  - `/api/health`
  - `/api/search`
  - `/api/companies`
  - `/api/stats`

## 5. 환경 변수 (`.env`)

루트 `.env`를 사용합니다.

```env
# DB
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=esg

# JWT
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# API behavior
USE_MOCK_DATA=true

# RAG/LLM
OPENAI_API_KEY=
VECTOR_DB_PATH=
CHROMA_HOST=
CHROMA_PORT=8000
OLLAMA_API_URL=http://localhost:11434
```

## 6. API 요약

### Auth

- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/me`

### Profile

- `GET /profile/me`
- `PUT /profile/me`
- `POST /profile/me/password`
- `POST /profile/me/email`
- `POST /profile/me/delete`
- `POST /profile/me/avatar` (`multipart/form-data`)

### Dashboard

- `GET /api/v1/dashboard/companies`
- `POST /api/v1/dashboard/compare/insight`

### Simulator

- `GET /api/v1/sim/dashboard/market-trends`
- `GET /api/v1/sim/dashboard/trend-combined`

### AI

- `POST /api/v1/ai/strategy`
- `POST /api/v1/ai/chat` (streaming)
- `POST /api/v1/ai/text-to-sql`

## 7. 인증 방식

- 로그인 성공 시 JWT access token 발급
- 보호 API 호출 시 헤더 사용:

```http
Authorization: Bearer <token>
```

- 비밀번호 해시는 `passlib`의 `pbkdf2_sha256` 사용

## 8. RAG/Chroma 동작 방식

`ai_service.py` 기준:

- `CHROMA_HOST`가 설정되면 원격 Chroma(`HttpClient`) 사용
- 미설정이면 로컬 Persistent Chroma 경로 탐색:
  - `VECTOR_DB_PATH` 우선
  - 없으면 기본 후보 경로(`PDF_Extraction/vector_db`) 탐색
- 벡터DB가 없더라도 서버는 기동되며, 챗봇 RAG 품질만 제한될 수 있음

## 9. 트러블슈팅

### 포트 충돌 (`[Errno 48] Address already in use`)

```bash
lsof -i :8000
kill -9 <PID>
```

### DB 테이블 없음 (`Table ... doesn't exist`)

- `cd backend/app && python init_db.py` 재실행
- `.env`의 `DB_NAME`, `DB_USER`, `DB_PASSWORD` 확인

### 로그인 401

- 토큰 만료 또는 잘못된 토큰
- 프론트 저장 토큰 삭제 후 재로그인
