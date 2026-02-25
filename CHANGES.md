# 수정 내역 (Change Log)

> 수정할 때마다 이 파일을 업데이트합니다.
> 형식: 날짜 | 수정 내용 (최대 3줄) | 수정 파일 (경로#줄번호)

---

## 2026-02-25

### [fix+feat] 업계 벤치마크(Industry Benchmark) 시스템 구축 및 데이터 정합성 강화
- `IndustryBenchmark` 모델 추가 및 기존 `revenue/production` 기준에서 `carbon_intensity/energy_intensity` 기반 컬럼으로 전면 수정
- `GET /api/v1/dashboard/benchmarks` 엔드포인트 구현을 통해 프론트엔드 비교 분석 데이터 실시간 연동 (404 에러 해결)
- `backend/patch_ground_truth.py` 내 탄소 집약도(ci_s1, ci_s2 등) 자동 계산 로직 추가 및 기존 데이터 강제 업데이트 기능 구현
- 최신 연도(2024년) 데이터를 분석하여 업계 벤치마크를 자동 산출하는 `backend/update_benchmarks.py` 스크립트 구축
- `backend/app/models.py` / `backend/app/routers/dashboard.py` / `backend/app/init_db.py` / `backend/patch_ground_truth.py`

---

## 2026-02-22

### [fix+feat] Dashboard 탭 KPI 및 UI 연동 오류 수정
- 상단 "탄소 집약도" 카드가 Compare 탭 선택 상태에 영향받지 않도록 S1+S2 실적 기반으로 고정 (하드코딩 제거)
- "2030 목표 달성 확률" 카드가 하단 S1~S3 필터 작동 시 난수 발생으로 흔들리던 현상 수정 (훅 분리)
- TrendChart(연간 배출 추이) 그래프가 S1~S3 필터를 실시간 반영하도록 연동 구조 개선
- K-ETS 가격 카드를 시뮬레이터 탭의 KAU25 실시간 가격 데이터와 동일하게 연동
- `frontend/src/App.tsx` / `frontend/src/features/대시보드/DashboardTab.tsx` / `frontend/src/features/대시보드/components/KPICards.tsx`

### [feat+fix] Compare (업계 벤치마킹 분석) 탭 개선
- OpenAI API 기반 프롬프트 3-Shot 적용을 통한 "전략적 인사이트(Efficiency Gap)" 자동 생성 연동 및 백엔드 라우터 추가
- API 오류 발생 시 "AI 분석됨" 뱃지 미노출 및 간소화된 Default 에러 문구 표시
- 불필요한 "리포트 내보내기" 버튼 제거 및 시뮬레이터 탭 진입 라우팅 적용
- `backend/app/services/ai_service.py` / `frontend/src/features/경쟁사비교/CompareTab.tsx`

### [fix+ui] Profile 및 Target 탭 개선
- 프로필 탭 사이드바 메뉴 순서 재배치 및 불필요한 아이콘(톱니바퀴, 잎사귀) 제거, 하위 내비게이션 탭 아이콘 리렌더링 버그 수정
- Target 탭 "감축 속도 분석" / "2030 목표 달성 시뮬레이션" 텍스트/그래프 색상 디자인 가이드에 맞게 통일 및 4.2% 감축 툴팁 추가
- `frontend/src/features/profile/Profile.tsx` / `frontend/src/features/목표설정/TargetTab.tsx`

---

## 2026-02-21

### [fix] Simulator 신규 UI 연동 버그 수정
- KAU25, EUA 상단 KPI 카드가 하드코딩된 mockData 대신 실시간 `market_data` 통신 로직을 타도록 수정
- 1개월(1M) 필터 클릭 시 X축 데이터가 잘리거나 밀리는 차트 렌더링 버그 수정
- `backend/app/services/market_data.py` / `frontend/src/features/시뮬레이터/SimulatorTab.tsx`

---
## 2026-02-19

### [docs] 전체 문서 현행화
- `README.md`: Dashboard·Compare·Simulator(4-Step)·Target·Profile 섹션 전면 업데이트
- `backend/docs/DB_SCHEMA_DASHBOARD.md`: `carbon_intensity_scope1/2/3` 필드 추가, Phase 2/3 완료 상태 반영
- `README.md` / `backend/docs/DB_SCHEMA_DASHBOARD.md`

---

## 2026-02-18

### [fix+refactor] Simulator 탭 전반 개선
- 시간 범위 버튼(1개월/3개월/1년/전체) 미작동 수정: `timeRange` 초기값 `'1y'`→`'1년'`, useMemo 비교값 영문→한글 정합화
- "포트폴리오 확정" 버튼 제거 → `totalCarbonCost` 실시간 자동 계산으로 전환 (`confirmedPurchaseCost` 상태 삭제)
- ETS 가격 시나리오 레이블 `'보수적'/'스트레스'` → `'낙관'/'비관'` 전망형 통일, EU-ETS 차트 색상 `#a5d8ff`→`#4dabf7`
- `frontend/src/App.tsx#168` / `frontend/src/features/시뮬레이터/SimulatorTab.tsx#51` / `frontend/src/data/mockData.ts#5`

### [feat+fix] Profile 설정 전반 개선
- 회사명 `<input>` → API 목록 기반 `<select>` 드롭다운으로 교체
- QuizBadge: 닉네임 동물 키워드(눈표범/물방개/판다/호랑이/독수리) 감지 → 해당 멸종위기 퀴즈, 미감지 시 탄소중립 기본 퀴즈
- QuizBadge hover→click 방식으로 변경, X 버튼 `absolute top-3 right-3` 고정, 눈 아이콘 상태 분리(`showEmailPassword`), 폰트 `font-display` 통일
- 사이드바 `top-28 h-[calc(100vh-7rem)] z-40` 고정, `compare`/`simulator` 탭 라우팅 `navigateTo('dashboard', tab)`으로 수정
- `frontend/src/features/profile/Profile.tsx` / `frontend/src/features/profile/DropoutModal.tsx#74`

### [ui] Header 꽃 아이콘 전탭 확장 및 Profile Setting 통합
- 모든 탭(dashboard 포함)에 꽃+줄기+잎 애니메이션 표시, dashboard 탭 라벨 `'Home'`으로 변경
- Profile 뷰 진입 시 Header 중앙에 꽃 아이콘 + "Profile Setting" 표시, Profile.tsx 내 중복 헤더 블록 제거
- `frontend/src/components/layout/Header.tsx#128`

### [feat] Compare 탭 세부실행계획 → Simulator 탭 연결
- `onNavigateToSimulator` prop 추가, 버튼 클릭 시 `navigateTo('dashboard', 'simulator')` 호출
- `frontend/src/features/경쟁사비교/CompareTab.tsx#236` / `frontend/src/App.tsx#1254`

### [fix+ui] Dashboard TrendChart 툴팁 개선
- actual 값이 있는 연도에서 forecast가 툴팁에 중복 표시되던 문제 수정 (`TrendChartTooltip` 컴포넌트 추가)
- `frontend/src/features/대시보드/components/TrendChart.tsx#17`

### [fix+ui] Target 탭 개선
- SBTi 목표달성도 판정 오류 수정: `yearsElapsed` 기준 `currentYear`→`latestDataYear` (동일 연도 비교)
- 차트 제목 `"Net Zero 경로 (SBTi 1.5°C)"` → `"온실가스 감축 로드맵 (Net Zero 경로)"`, 방법론 주석 `"SBTi 경로:"` → `"온실가스 감축 경로:"`
- `frontend/src/App.tsx#861` / `frontend/src/features/목표설정/TargetTab.tsx#152`

---

## 2026-02-17 이전

### [docs] README 전면 업데이트
- Compare Tab 섹션 신규 추가, Simulator 설명을 실제 K-ETS 로직에 맞게 재작성
- 누락된 API 명세(Dashboard, Profile), 환경변수, DB 스키마 테이블 추가
- 시스템 아키텍처 다이어그램 수정 (HuggingFace → Ollama 로컬 LLM 반영)
- `README.md`
