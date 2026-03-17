# Be-REAL Carbon Decision OS 기능 명세서

## 1. 문서 목적

이 문서는 Be-REAL Carbon Decision OS의 주요 기능을 화면 및 사용자 흐름 기준으로 정리한 기능 명세서이다.

문서 목적은 다음과 같다.

- 현재 구현된 기능의 범위를 명확히 정리한다.
- 각 기능의 목적과 사용자 가치를 설명한다.
- 프론트엔드와 백엔드의 연결 지점을 정리한다.
- 향후 어떤 방향으로 확장할지 기준을 만든다.

본 문서는 PRD의 방향성을 실제 제품 기능 단위로 풀어낸 문서이며, 이후 개발 우선순위 및 API 설계의 기준 문서로 사용한다.

## 2. 제품 내 주요 기능 구조

현재 제품은 아래 기능 영역으로 구성된다.

- 인증 및 접근 제어
- 대시보드
- 경쟁사 비교
- 시뮬레이터
- 목표관리
- AI 챗봇 및 전략 보조
- 프로필 관리
- 데이터 입력
- 리포트
- 분석

이 중 실제 핵심 사용자 가치를 제공하는 영역은 `대시보드`, `비교`, `시뮬레이터`, `목표관리`, `AI 보조`이며, 나머지는 보조 기능 또는 준비 중인 영역이다.

## 3. 공통 기능

### 3.1 라우팅 및 접근 제어

목적:

- 인증 상태에 따라 접근 가능한 화면을 제어한다.

현재 구현 상태:

- 로그인하지 않은 사용자는 보호된 페이지 접근 시 로그인 화면으로 이동한다.
- 로그인한 사용자는 `/dashboard` 계열 화면과 `/profile` 등에 접근할 수 있다.
- 라우트는 단순하고 명시적인 경로 기반으로 관리된다.

주요 경로:

- `/login`
- `/signup`
- `/welcome`
- `/dashboard`
- `/dashboard/compare`
- `/dashboard/simulator`
- `/dashboard/target`
- `/profile`
- `/data-input`
- `/reports`
- `/analytics`

관련 파일:

- [App.tsx](/Users/jm/ESG_bereal_3rd/frontend/src/App.tsx)

향후 확장:

- 회사별 권한 분리
- 관리자/승인자/실무자 역할 기반 접근 제어
- 요청 승인 화면별 권한 제어

### 3.2 초기 데이터 로딩

목적:

- 제품 진입 시 핵심 데이터 세트를 미리 로드해 주요 화면이 즉시 동작하도록 한다.

현재 구현 상태:

- 시장 가격 데이터 조회
- 회사별 배출 데이터 조회
- 업계 벤치마크 조회
- EUR/KRW 환율 조회
- 일부 API 실패 시 fallback 동작 존재

입력:

- 사용자 인증 상태
- 기본 API 엔드포인트

출력:

- 회사 목록
- 시장 히스토리 데이터
- 벤치마크 데이터
- 환율 정보

관련 파일:

- [App.tsx](/Users/jm/ESG_bereal_3rd/frontend/src/App.tsx)
- [api.ts](/Users/jm/ESG_bereal_3rd/frontend/src/services/api.ts)

향후 확장:

- 공통 로딩/에러 상태 분리
- 캐시 전략 도입
- 회사 선택 상태의 URL 동기화

## 4. 인증 기능

### 4.1 로그인

목적:

- 사용자가 제품에 인증된 상태로 진입하도록 한다.

현재 구현 상태:

- 이메일/비밀번호 입력
- 이메일 형식 검증
- 로그인 API 호출
- JWT 토큰 저장
- 성공 시 메인 플로우로 진입

입력:

- 이메일
- 비밀번호

출력:

- `access_token`
- 로그인 상태

관련 API:

- `POST /auth/login`
- `GET /auth/me`

관련 파일:

- [Login.tsx](/Users/jm/ESG_bereal_3rd/frontend/src/features/auth/Login.tsx)
- [authApi.ts](/Users/jm/ESG_bereal_3rd/frontend/src/services/authApi.ts)
- [auth.py](/Users/jm/ESG_bereal_3rd/backend/app/routers/auth.py)

예외 처리:

- 입력값 누락
- 이메일 형식 오류
- 잘못된 계정 정보
- 백엔드 연결 실패

향후 확장:

- 회사별 SSO
- 비밀번호 재설정
- 로그인 시 최근 작업 복원

### 4.2 회원가입

목적:

- 신규 사용자가 서비스를 사용할 수 있도록 계정을 만든다.

현재 구현 상태:

- 회사 선택
- 이메일 입력
- 비밀번호 정책 검증
- 비밀번호 확인
- 회원가입 API 호출

입력:

- 회사명
- 이메일
- 비밀번호

출력:

- 신규 사용자 계정 생성

관련 API:

- `POST /auth/signup`

관련 파일:

- [Signup.tsx](/Users/jm/ESG_bereal_3rd/frontend/src/features/auth/Signup.tsx)
- [auth.py](/Users/jm/ESG_bereal_3rd/backend/app/routers/auth.py)

향후 확장:

- 회사 초대 기반 가입
- 승인 후 활성화 방식
- 부서 및 역할 초기 설정

### 4.3 웰컴 플로우

목적:

- 로그인/가입 직후 제품 컨텍스트로 자연스럽게 진입시킨다.

현재 구현 상태:

- 짧은 인트로 화면 후 자동 이동

관련 파일:

- [WelcomePage.tsx](/Users/jm/ESG_bereal_3rd/frontend/src/features/auth/WelcomePage.tsx)

향후 확장:

- 첫 사용자용 온보딩
- 역할별 시작 가이드

## 5. 대시보드 기능

### 5.1 기능 목적

- 사용자가 회사의 현재 탄소 배출 현황과 핵심 지표를 가장 먼저 확인하는 메인 화면이다.

### 5.2 현재 구현 상태

- KPI 카드 표시
- Scope별 배출 비중 시각화
- 연도별 배출 추이 차트
- 관련 탭으로 이동하는 빠른 액션 제공

### 5.3 사용자 가치

- 회사의 현재 상태를 한눈에 파악할 수 있다.
- 어떤 영역을 추가로 분석해야 하는지 바로 판단할 수 있다.

### 5.4 입력값

- 선택된 회사 정보
- 회사별 배출량 이력
- 벤치마크 및 시뮬레이션 결과 일부
- Scope 선택 상태

### 5.5 출력값

- 총 배출량
- 탄소 또는 에너지 집약도
- ETS 관련 비용 지표
- SBTi 달성 확률
- Scope별 비중
- 배출량 추이 차트

### 5.6 관련 API

- `GET /api/v1/dashboard/companies`
- `GET /api/v1/dashboard/benchmarks`

### 5.7 관련 파일

- [DashboardTab.tsx](/Users/jm/ESG_bereal_3rd/frontend/src/features/대시보드/DashboardTab.tsx)
- [dashboard.py](/Users/jm/ESG_bereal_3rd/backend/app/routers/dashboard.py)

### 5.8 향후 확장

- KPI 클릭 시 세부 설명 패널 제공
- 최근 의사결정 및 요청 상태 요약 추가
- 회사 선택 UI 고도화
- 대시보드에서 바로 구매 워크플로우 진입

## 6. 경쟁사 비교 기능

### 6.1 기능 목적

- 자사의 탄소 및 에너지 집약도를 경쟁사와 비교해 상대적 위치를 파악하도록 한다.

### 6.2 현재 구현 상태

- 탄소 집약도/에너지 집약도 모드 전환
- 경쟁사 순위 카드
- 바차트 시각화
- 업계 중앙값 및 상위 10% 기준선 표시
- Scope 1/2 반영 토글
- AI 인사이트 요청
- 시뮬레이터 이동 버튼 제공

### 6.3 사용자 가치

- 자사의 상대적 성과 수준을 직관적으로 이해할 수 있다.
- 전략 우선순위를 정할 때 외부 기준을 참고할 수 있다.

### 6.4 입력값

- 회사 목록
- 회사별 집약도 값
- 업계 벤치마크 값
- 선택된 회사 ID
- Scope 토글 상태

### 6.5 출력값

- 경쟁사 정렬 리스트
- 집약도 비교 차트
- 기준선 비교 결과
- AI 해석 결과

### 6.6 관련 API

- `GET /api/v1/dashboard/companies`
- `GET /api/v1/dashboard/benchmarks`
- `POST /api/v1/dashboard/compare/insight`

### 6.7 관련 파일

- [CompareTab.tsx](/Users/jm/ESG_bereal_3rd/frontend/src/features/경쟁사비교/CompareTab.tsx)
- [dashboard.py](/Users/jm/ESG_bereal_3rd/backend/app/routers/dashboard.py)

### 6.8 예외 및 유의사항

- 인사이트 호출 주소 일부가 하드코딩되어 있어 환경 설정 정리가 필요하다.
- 벤치마크 데이터가 없을 경우 기본값 처리 필요성이 높다.

### 6.9 향후 확장

- 업종 필터
- 연도별 비교 모드
- 경쟁사 그룹 커스터마이징
- 비교 결과 기반 자동 전략 추천 연결

## 7. 시뮬레이터 기능

### 7.1 기능 목적

- 탄소 비용, 무상할당, 배출량 변화, 시장 가격을 반영해 조달 전략을 비교하는 핵심 의사결정 화면이다.

### 7.2 현재 구현 상태

- K-ETS / EU-ETS 시장 선택
- 가격 추이 차트
- 기간 필터
- 탄소 가격 시나리오 선택
- 사용자 정의 가격 입력
- 배출량 변화 입력
- 무상할당 변화 선택
- 경매 비율 설정
- 분할매수 트랜치 설정
- 예산 입력
- 국내/해외 노출 비용 및 통합 예산 리스크 계산

### 7.3 사용자 가치

- 단순 조회를 넘어서 전략적 선택을 비교할 수 있다.
- 예산 한도 내에서 어떤 조달 방식이 적합한지 판단할 수 있다.

### 7.4 입력값

- 시장 가격 이력
- 현재 ETS 가격
- 배출량 변화율
- 무상할당 변화
- 사용자 정의 가격
- 경매 여부 및 비율
- 분할매수 트랜치
- 예산
- 환율

### 7.5 출력값

- 시장 가격 변화
- 조정 배출량
- 순노출량
- 컴플라이언스 비용
- 감축 비용
- 해외 예상 비용
- 통합 총 비용
- 예산 대비 리스크 등급

### 7.6 관련 API

- `GET /api/v1/sim/dashboard/market-trends`
- `GET /api/v1/sim/dashboard/trend-combined`

### 7.7 관련 파일

- [SimulatorTab.tsx](/Users/jm/ESG_bereal_3rd/frontend/src/features/시뮬레이터/SimulatorTab.tsx)
- [api.ts](/Users/jm/ESG_bereal_3rd/frontend/src/services/api.ts)
- [simulator.py](/Users/jm/ESG_bereal_3rd/backend/app/routers/simulator.py)

### 7.8 현재 한계

- 전략 추천이 구조화된 제품 기능으로 아직 분리되지 않았다.
- 구매 요청 생성 흐름이 없다.
- 승인 및 실행 단계와 연결되지 않는다.

### 7.9 향후 확장

- 추천 전략 카드 3종 제안
- 전략별 비용/리스크/추천 사유 표시
- 선택 전략으로 구매 요청 생성
- 요청 상태와 주문 이력 연결

## 8. 목표관리 기능

### 8.1 기능 목적

- 현재 배출 추세가 장기 감축 목표와 얼마나 정렬되는지를 보여준다.

### 8.2 현재 구현 상태

- 기준연도 배출량 표시
- 최신 배출량 표시
- SBTi 달성 여부 판단
- Net Zero 2050 격차 표시
- 실적, 회귀 예측, SBTi 경로 차트
- Monte Carlo 기반 2030 목표 달성 확률 표시

### 8.3 사용자 가치

- 단기 조달 전략과 장기 감축 전략을 함께 볼 수 있다.
- 현재 성과가 충분한지 아닌지 정량적으로 이해할 수 있다.

### 8.4 입력값

- 회사별 배출 이력
- 최신 보고 연도
- 기준연도 정보
- 회귀 계산 결과
- 확률 시뮬레이션 결과

### 8.5 출력값

- 기준 배출량
- 최신 배출량
- 감축률
- 목표 대비 초과/미달
- 목표 달성 확률
- 남은 감축 격차

### 8.6 관련 파일

- [TargetTab.tsx](/Users/jm/ESG_bereal_3rd/frontend/src/features/목표설정/TargetTab.tsx)
- [App.tsx](/Users/jm/ESG_bereal_3rd/frontend/src/App.tsx)

### 8.7 향후 확장

- 목표 시나리오 직접 설정
- 감축 투자 계획과 연결
- 구매 전략과 목표 정렬도 자동 평가

## 9. AI 기능

### 9.1 AI 챗봇

목적:

- 사용자가 시장, 배출, 전략에 대해 자연어로 질문하고 해석을 받을 수 있게 한다.

현재 구현 상태:

- 플로팅 챗봇 UI
- 메시지 입력
- 추천 질문 버튼
- 스트리밍 응답
- 대화 히스토리 전달
- 회사 맥락 전달
- 리포트 범위 컨텍스트 전달

입력:

- 사용자 메시지
- 대화 이력
- 선택 회사 정보
- 리포트 범위

출력:

- 텍스트 기반 AI 응답

관련 API:

- `POST /api/v1/ai/chat`

관련 파일:

- [ChatBot.tsx](/Users/jm/ESG_bereal_3rd/frontend/src/features/챗봇/ChatBot.tsx)
- [ai.py](/Users/jm/ESG_bereal_3rd/backend/app/routers/ai.py)

향후 확장:

- 추천 전략에 대한 설명형 응답
- 구매 요청 초안 생성
- 회의용 요약 생성

### 9.2 AI 전략 생성 API

목적:

- 선택한 맥락에 따라 전략 문안을 생성하는 백엔드 기반 기능이다.

현재 구현 상태:

- 전략 생성 API 존재
- 텍스트 기반 SQL 생성 API 존재
- 프론트 측 완전한 사용 시나리오는 아직 제한적

관련 API:

- `POST /api/v1/ai/strategy`
- `POST /api/v1/ai/text-to-sql`

관련 파일:

- [ai.py](/Users/jm/ESG_bereal_3rd/backend/app/routers/ai.py)

향후 확장:

- 시뮬레이터 추천 카드 자동 생성
- 승인 사유 문안 작성
- 경영진 보고서 텍스트 자동 생성

## 10. 프로필 기능

### 10.1 기능 목적

- 사용자 계정 정보와 프로필 데이터를 관리한다.

### 10.2 현재 구현 상태

- 프로필 조회
- 닉네임, 회사명, 분류, 소개 수정
- 프로필 이미지 업로드
- 이메일 변경
- 비밀번호 변경
- 회원 탈퇴

### 10.3 입력값

- 프로필 텍스트 정보
- 이미지 파일
- 현재 비밀번호
- 새 이메일 또는 새 비밀번호

### 10.4 출력값

- 갱신된 사용자 정보
- 성공/실패 메시지

### 10.5 관련 API

- `GET /profile/me`
- `PUT /profile/me`
- `POST /profile/me/avatar`
- `POST /profile/me/email`
- `POST /profile/me/password`
- `POST /profile/me/delete`

### 10.6 관련 파일

- [Profile.tsx](/Users/jm/ESG_bereal_3rd/frontend/src/features/profile/Profile.tsx)
- [profileApi.ts](/Users/jm/ESG_bereal_3rd/frontend/src/services/profileApi.ts)
- [profile.py](/Users/jm/ESG_bereal_3rd/backend/app/routers/profile.py)

### 10.7 향후 확장

- 회사 소속 정보 강화
- 사용자 역할 및 권한 표시
- 알림 및 선호 설정

## 11. 보조 및 준비 중 기능

### 11.1 데이터 입력

목적:

- 사용자가 직접 배출 데이터를 입력 및 관리하도록 하는 화면이다.

현재 구현 상태:

- Scope 1, 2, 3 입력 UI만 존재
- 계산값과 저장 기능은 실제 연결되지 않음

관련 파일:

- [DataInput.tsx](/Users/jm/ESG_bereal_3rd/frontend/src/features/data-input/DataInput.tsx)

향후 확장:

- 데이터 저장 API
- 배출계수 기반 계산
- 업로드/임시저장/검증 기능

### 11.2 리포트

목적:

- ESG 리포트 생성 및 다운로드 기능의 진입점이다.

현재 구현 상태:

- 준비 중 안내 화면만 존재

관련 파일:

- [Reports.tsx](/Users/jm/ESG_bereal_3rd/frontend/src/features/reports/Reports.tsx)

향후 확장:

- 경영진 보고서 생성
- PDF/Excel 다운로드
- 시뮬레이션 결과 요약 리포트

### 11.3 분석

목적:

- 심화 분석 기능의 확장 영역이다.

현재 구현 상태:

- 준비 중 안내 화면만 존재

관련 파일:

- [Analytics.tsx](/Users/jm/ESG_bereal_3rd/frontend/src/features/analytics/Analytics.tsx)

향후 확장:

- 비용 추세 분석
- 민감도 분석
- 배출/시장/전략 상관분석

## 12. 다음 단계에서 우선 명세가 필요한 기능

현재 제품을 더 완성도 있게 만들기 위해 다음 기능에 대한 상세 명세가 가장 먼저 필요하다.

- 시뮬레이터 내 추천 전략 카드
- 구매 요청 생성 플로우
- 구매 요청 목록 및 상세 화면
- 승인 상태 모델
- 주문 및 실행 이력 모델

이 영역은 현재 제품을 `분석 도구`에서 `실행 가능한 의사결정 시스템`으로 전환시키는 핵심 구간이다.

## 13. 후속 문서 추천

이 문서 다음으로 만들면 좋은 문서는 아래와 같다.

- `ROADMAP.md`
- `SYSTEM_DESIGN.md`
- `DOMAIN_MODEL.md`
- `API_SPEC.md`

권장 순서:

1. 로드맵 문서로 우선순위 확정
2. 도메인 모델 문서로 구매 요청 및 승인 구조 정의
3. 시스템 설계 문서로 프론트/백엔드/DB 구조 정리
