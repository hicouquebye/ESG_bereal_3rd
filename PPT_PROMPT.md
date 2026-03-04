# PPT 생성 명령 프롬프트

> 아래 프롬프트를 Genspark, Manus, ChatGPT, Gamma 등 PPT 생성 AI에 복사-붙여넣기하세요.

---

## 🔹 프롬프트 (전체 복사용)

```
당신은 전문 PPT 디자이너입니다. 아래 슬라이드 구조에 따라 프레젠테이션을 제작해 주세요.

[프로젝트 정보]
- 프로젝트명: ESG 대시보드 — 기업의 탄소 전략을 데이터로 설계하다
- 팀명: Be-REAL
- 발표 시간: 총 18분 분량 대응 (15~20분, 발표 상황에 맞춰 조절)
- 디자인 톤: ESG/친환경 테마, 밝고 깨끗한 화이트·라이트 그레이 배경, 그린·블루 계열 포인트 컬러, 모던한 산세리프 폰트, 밝고 신뢰감 있는 레이아웃. 텍스트 최소화, 시각 자료 중심. 전체적으로 환하고 전문적인 분위기.

[디자인 규칙]
1. 슬라이드당 텍스트 bullet은 최대 5개
2. 핵심 수치는 크고 굵게 (예: "₩50,000/톤", "+37.6억 원")
3. 모든 기능 설명 슬라이드에는 "화면 캡처 삽입 영역"을 표시해 주세요 (플레이스홀더)
4. 색상 팔레트: 배경 #FFFFFF(화이트) 또는 #F5F7FA(라이트 그레이), 메인 #10B981(에메랄드 그린), 보조 #3B82F6(스카이 블루), 강조 #F59E0B(앰버 오렌지), 텍스트 #1E293B(다크 슬레이트), 서브 텍스트 #64748B(슬레이트 그레이)
5. 전환 효과 최소화, 깔끔한 페이드 인/아웃만 사용
6. 각 슬라이드 하단에 슬라이드 번호 표시

---

[슬라이드 #1] 타이틀 & 아이스브레이킹
- 제목: "ESG 대시보드: 기업의 탄소 전략을 데이터로 설계하다"
- 부제: Be-REAL Team
- 팀원 이름 4명: 희선, 현이, 정민, 상훈
- 아이스브레이킹 문구: "잼민이, 클로드, GPT 모두 26조 원을 추천합니다"
- 디자인: 풀스크린 타이틀, 중앙 정렬, 하단에 팀원 이름 나열

[슬라이드 #2] 목차 (Agenda)
- 제목: "목차 (Agenda)"
- 내용:
  1. The Problem: 왜 지금 ESG 데이터 관리가 필요한가?
  2. The Product: Be-REAL ESG 대시보드 & 시뮬레이터
  3. The Value: 우리의 차별점과 향후 비전
- 시각 자료: 1, 2, 3 단계로 이어지는 심플한 가로형 파이프라인/플로우 그래픽

[슬라이드 #3] 국내 ESG 공시 의무화
- 제목: "국내 ESG 공시 의무화 — 더 이상 선택이 아닌 규제"
- 내용: 금융위원회 주도로 2026년부터 단계적 ESG 공시 의무화 추진, 2030년 모든 상장사 확대
- 시각 자료: 타임라인 인포그래픽 (2026 → 2028 → 2030)

[슬라이드 #4] 글로벌 ESG 공시 동향
- 제목: "글로벌 ESG 공시 — ISSB·CSRD가 만드는 표준 물결"
- 내용: ISSB 36개국 채택 (GDP 60%+ 지역), EU CSRD 2025년 첫 의무 발행
- 시각 자료: 세계 지도에 채택 국가 하이라이트

[슬라이드 #5] 국내 탄소 배출권 시장 현황
- 제목: "K-ETS 제4차 계획기간 — 탄소의 가격이 오른다"
- 내용: 2026년 제4차 배출권 거래제 시작, 현재 13,000원 → 5년 내 50,000원 돌파 전망
- 시각 자료: KAU 가격 추이 라인 차트 + 미래 예측 구간 표시

[슬라이드 #6] 기존 데이터의 한계 → 솔루션 필요성
- 제목: "기업 ESG 데이터의 현실 — 왜 AI 기반 대시보드가 필요한가"
- 레이아웃: "AS-IS (조회 불편, 비교 불가)" vs "TO-BE (자동 추출 구조화 및 시뮬레이션)" 비교
- 시각 자료: Before/After 비교 다이어그램

[슬라이드 #7] 시스템 아키텍처 & 기술 스택
- 제목: "시스템 구조 — PDF에서 대시보드까지"
- 흐름: 보고서 PDF → 파이프라인 → AI 추출 → Relational/Vector DB → 대시보드/챗봇
- 기술 스택: FastAPI, React, PostgreSQL, ChromaDB
- 시각 자료: 아키텍처 플로우 다이어그램

[슬라이드 #8] AI 하이브리드 추출 파이프라인 (핵심 기술)
- 제목: "핵심 기술: AI 하이브리드 추출 엔진"
- 내용: 무조건 비싼 Vision AI를 쓰지 않고, Docling 레이아웃 분석과 자체 규칙 필터(Rule-based)를 거쳐 중요 표/이미지만 최적화된 Vision 모델(GPT-4o-mini)로 최소한 처리, 나머지는 PyMuPDF/RapidOCR 등 로컬 파싱으로 처리하여 API 비용 극적으로 절감.
- 시각 자료: 하이브리드 추출 로직 분기 다이어그램 (정확도 🎯, 비용 📉 강조)

[슬라이드 #9] 대시보드 탭 Overview
- 제목: "대시보드 — 기업 탄소 현황을 한눈에"
- 내용: 총 배출량(Scope 1+2+3) KPI, 연간 배출 추이 차트, 탄소 집약도
- 시각 자료: [화면 캡처 삽입 영역] 대시보드 메인 화면 (번호 어노테이션)

[슬라이드 #10] 시뮬레이터: 글로벌 가격 동향
- 제목: "실시간 시장 분석 — K-ETS & EU-ETS 가격 추이"
- 내용: 실시간 시세 카드, KAU 및 EU-ETS 역사적 추이 비교 분석 차트
- 시각 자료: [화면 캡처 삽입 영역] 시뮬레이터 상단 시세카드 + 차트

[슬라이드 #11] 시뮬레이터: K-ETS 4단계 시뮬레이션
- 제목: "K-ETS 고급 시뮬레이션 — 4단계 의사결정 지원"
- 내용: [Step 1]배출량 설정 → [Step 2]전략 배분 → [Step 3]포트폴리오 구성 → [Step 4]최종 리포트
- 시각 자료: 4단계 프로세스 플로우 다이어그램

[슬라이드 #12] 시뮬레이터: Step 1 심층 분석
- 제목: "Step 1 심층 분석 — 시나리오가 비용을 바꾼다"
- 핵심 수치: "무상할당 30% 축소 시 추가 부담금 +₩37.6억"
- 내용: 3대 KPI(순 노출량/탄소비용/구매예상), 무상할당 시나리오 극적인 비용 변화 시연
- 시각 자료: [화면 캡처 삽입 영역] Step 1 전체 화면, 시나리오 카드

[슬라이드 #13] 시뮬레이터: Step 2 & 3 포트폴리오 최적화
- 제목: "최적의 대응 전략 도출 — 투자 vs 매수"
- 내용:
  • Step 2: 배출권 구매 vs 친환경 설비 투자 비율 최적화 (MAC 비교 고려)
  • Step 3: 한국(K-ETS)/유럽(EU-ETS) 분할 매수 전략. VWAP 계산 및 Carbon Risk 구간 경고
- 시각 자료: [화면 캡처 삽입 영역] 슬라이더 조작 화면, 카본 리스크 게이지 화면 확대

[슬라이드 #14] 타겟 탭: Net Zero 경로 예측
- 제목: "감축 목표 경로 분석 — SBTi × 몬테카를로 시뮬레이션"
- 내용: SBTi 목표 vs 현재 속도 비교, 로그 회귀 및 몬테카를로 2030 달성 확률 예측
- 시각 자료: [화면 캡처 삽입 영역] SBTi 궤적 차트 + 몬테카를로 확률 분포 차트

[슬라이드 #15] AI 챗봇 & RAG
- 제목: "ESG 챗봇 — 보고서 기반 질의응답"
- 내용: PDF 텍스트 전문 ChromaDB 저장, 질문 시 근거 페이지와 함께 설명 제공
- 시각 자료: [화면 캡처 삽입 영역] RAG 아키텍처 다이어그램 + 챗봇 UI 캡처

[슬라이드 #16] 프로젝트 강점
- 제목: "우리 프로젝트의 핵심 가치"
- 3가지 강점: 신뢰성(원본 표 제공), End-to-End 통합, 비용 효율성(자체 필터 및 로컬 추출 도입으로 API 비용 최소화)
- 시각 자료: 3열 카드 레이아웃 (아이콘 중심)

[슬라이드 #17] 한계 및 향후 방향 + 마무리
- 제목: "한계와 발전 방향"
- 현재 한계: PDF 중심, Scope 3 데이터 소스 한계
- 발전 방향: 실시간 IoT 센서 연동, ERP 시스템 통합 확대
- 마무리: "감사합니다."

[슬라이드 #18] 부록 — 용어 정리 (Q&A 대비)
- 제목: "부록 — 용어 정리 & 기술 상세"
- 내용: ESG, SBTi, MAC, VWAP, Net Exposure 등 핵심 용어 사전 및 API 명세 정리 표 형식

---

총 18슬라이드, 밝고 깨끗한 화이트 배경 + 그린·블루 포인트 ESG 테마로 제작해 주세요.
전체적으로 환하고 전문적인 분위기를 유지해 주세요.
화면 캡처 삽입 영역은 비워두되, 해당 위치를 명확히 표시해 주세요.
```

---

## 🔹 간결 버전 프롬프트 (슬라이드 수 제한이 있는 도구용)

```
ESG 대시보드 프로젝트 발표 PPT를 제작해 주세요.

[프로젝트] 기업 ESG 보고서(PDF)를 AI로 자동 추출하여 데이터를 구조화하고, K-ETS 배출권 비용 시뮬레이션 및 분할 매수 전략까지 지원하는 의사결정 대시보드.

[디자인] 밝은 화이트 배경, 그린·블루 포인트 컬러, 미니멀, 수치 강조, 화면 캡처 중심, 환하고 전문적인 분위기

[슬라이드 구성 - 총 18장]
1. 타이틀 (ESG 대시보드 + 팀 Be-REAL)
2. 목차 (Agenda) - The Problem / The Product / The Value
3. 국내 규제 현황 (2030년 모든 상장사 공시)
4. 글로벌 동향 (ISSB, EU CSRD 의무 대상 확대)
5. K-ETS 배출권 시장 현황 (현재가 vs 5만 원 돌파 전망)
6. 기존 데이터의 문제점 vs 본 솔루션 가치
7. 시스템 아키텍처 전체 흐름도
8. 핵심 기술: AI 하이브리드 추출 엔진 (비용 효율 극대화)
9. 대시보드 메인 화면 기능 (캡처)
10. 시뮬레이터: 실시간 글로벌 시장 가격 분석
11. K-ETS 4단계 시뮬레이션 플로우 개요
12. Step 1 심층: 배출량 & 무상할당 시나리오별 총 비용 영향 (캡처)
13. Step 2 & 3 심층: 감축 투자 vs 매수 비율 최적화 및 분할 매수 포트폴리오 (캡처)
14. 타겟 탭: SBTi 경로 비교 및 몬테카를로 달성 확률 (캡처)
15. ESG AI 챗봇 (RAG 기반 질의응답 구조)
16. 3대 강점 (신뢰성, 통합성, 비용효율성)
17. 한계 및 향후 개선 과제 + 인사
18. 부록: 전문 용어 정리 및 API 명세
```

---

## 🔹 Gamma.app 전용 프롬프트

```
Create a 18-slide presentation about an ESG Dashboard and Carbon simulator project.

Theme: Bright white background with emerald green and sky blue accent colors, modern, clean, minimal, professional, data-driven.
Language: Korean

Title: ESG 대시보드 — 기업의 탄소 전략을 데이터로 설계하다
Team: Be-REAL

Slides:
1. Title slide with team name and icebreaker
2. Agenda (The Problem / The Product / The Value)
3. Korea ESG disclosure regulation timeline (2026-2030)
4. Global ESG trends (ISSB, EU CSRD)
5. Carbon market context (Price inflation forecast)
6. Current limitations vs Our AI Dashboard solution
7. End-to-End System architecture flowchart
8. Core Tech: Hybrid AI Extraction Pipeline (Docling & LLM cost-efficiency)
9. Main Dashboard UI overview (Screenshot placeholder)
10. Simulator: Real-time K-ETS and EU-ETS price
11. Simulator: 4-step decision-making process flowchart
12. Simulator Step 1: Scenario impact (+₩3.76B case)
13. Simulator Step 2 & 3: Strategic allocation (Reduction vs Purchase) & Portfolio builder
14. Target Tab: SBTi trajectory & Monte Carlo prediction
15. ESG Chatbot using RAG
16. 3 key strengths (Trust, E2E, Cost-Efficiency)
17. Limitations + Future improvements + Thank you
18. Appendix: Glossary table

Use placeholder boxes for screenshots. Emphasize key numbers in bold large text. Keep the overall mood professional and bright.
```
