# 🏛️ ESG Carbon Dashboard 시스템 아키텍처 (System Architecture)

현재 프로젝트(`ESG_Wep`)의 코드 및 기술 스택을 기반으로 분석한 시스템 아키텍처입니다.
크게 **클라이언트(Frontend)**, **서버(Backend)**, **데이터 및 AI 계층(Data & AI Layer)**, 그리고 외부에서 데이터를 가져오는 **외부 데이터 소스(External Data Sources)** 4가지 영역으로 구성됩니다.

## 1. 다이어그램 (Mermaid)

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[웹 브라우저]
    end

    subgraph "Frontend (React 18 + TypeScript + Vite)"
        UI[UI Components<br/>Recharts / TailwindCSS 4]
        State[State Management<br/>React Hooks + localStorage]
        Router[View State Router<br/>React Router DOM]
    end

    subgraph "Backend (FastAPI + Uvicorn)"
        Auth[Auth Router<br/>/auth (JWT)]
        Profile[Profile Router<br/>/profile]
        Dashboard[Dashboard Router<br/>/api/v1/dashboard]
        Sim[Simulator Router<br/>/api/v1/sim]
        AI[AI Router<br/>/api/v1/ai]
    end

    subgraph "Data & AI Layer"
        MySQL[(MySQL DB<br/>users / dashboard_emissions)]
        ChromaDB[(ChromaDB<br/>Vector Store / RAG)]
        OpenAI[OpenAI API<br/>gpt-4o / gpt-4o-mini]
        BGE[BGE Embedding & Reranker<br/>bge-m3, bge-reranker]
    end

    subgraph "External Data Sources"
        yfinance[Yahoo Finance<br/>EU-ETS 단가 조회]
        FDR[FinanceDataReader<br/>K-ETS KAU 단가 조회]
    end

    %% 연결 관계
    Browser --> UI
    UI --> State --> Router
    Router -->|Axios / REST API| Auth & Profile & Dashboard & Sim & AI
    Auth -->|User 인증/가입| MySQL
    Profile --> MySQL
    Dashboard --> MySQL
    Sim -->|실시간 탄소/에너지 단가| yfinance & FDR
    AI -->|문서 검색| ChromaDB
    AI -->|프롬프트 질의응답| OpenAI
    ChromaDB -->|벡터화/검색| BGE
```

## 2. 주요 구성 요소 설명

### 2.1 Frontend (프론트엔드)
* **핵심 기술**: React 18, TypeScript, Vite
* **스타일링 및 UI**: TailwindCSS 4, Framer Motion (애니메이션), Recharts (차트 시각화)
* **상태 및 라우팅**: React Hooks, `react-router-dom`을 활용한 탭(Dashboard, Compare, Simulator, Target 등) 라우팅
* **역할**: 사용자에게 실시간 배출량 현황, 경쟁사 비교 데이터, 시뮬레이터 UI 및 RAG 챗봇 인터페이스 등 제공.

### 2.2 Backend (백엔드)
* **핵심 기술**: FastAPI, Uvicorn, SQLAlchemy 구조
* **Router 구성**:
  * **Auth**: 회원가입, 로그인 및 JWT 기반 세션 관리 (passlib, python-jose 활용).
  * **Dashboard** & **Profile**: 사용자 정보 및 KPI 데이터베이스 조달.
  * **Simulator**: 탄소 배출 규제 노출량(Net Exposure) 로직 및 최적 조달 전략 비용 제공.
  * **AI**: 챗봇 및 RAG 검색을 위한 엔드포인트 지원 (StreamingResponse 방식으로 답변 즉각 렌더링).

### 2.3 Data & AI Layer (데이터베이스 및 인공지능)
* **RDBMS (MySQL)**: `users`(사용자 및 권한), `dashboard_emissions`(연도별/기업별 배출량, 매출 데이터 등) 데이터 보관.
* **Vector DB (ChromaDB)**: 비정형 ESG 보고서 PDF 등을 파싱(Docling, PyMuPDF 활용)해 벡터로 적재 후 시맨틱 검색.
* **Embedding & Reranker (BAAI/bge-m3)**: 문서를 벡터화하고 유사도를 기반으로 검색 퀄리티 향상 (safetensors 지원).
* **LLM (OpenAI API)**: GPT-4o / GPT-4o-mini를 활용하여 시장 데이터에 기반한 챗봇 전략 문안 생성 및 응답 제공.

### 2.4 External Data Sources (외부 데이터 연동)
* **yfinance / yahoo_fin**: 글로벌 데이터, 특히 EU-ETS 탄소 배출권 가격 연동 조회.
* **FinanceDataReader**: 국내 데이터(K-ETS KAU 종목 단가)의 시계열 처리 및 결측치 Fallback 담당.
