# Be-REAL Carbon Decision OS API 명세서

## 1. 문서 목적

이 문서는 Be-REAL Carbon Decision OS의 현재 API와 앞으로 우선 구현해야 할 신규 API를 정리한 문서이다.

문서 목적은 다음과 같다.

- 현재 구현된 API를 한 번에 파악할 수 있게 한다.
- 앞으로 추가해야 할 핵심 API를 우선순위 기준으로 정의한다.
- 프론트엔드와 백엔드가 어떤 데이터 계약을 가져야 하는지 정리한다.
- 도메인 모델 문서의 개념을 실제 엔드포인트 수준으로 구체화한다.

본 문서는 모든 API를 완벽히 세세하게 적는 백엔드 참조 문서라기보다, 제품 구현 우선순위를 반영한 실전용 명세서다.

## 2. API 설계 원칙

- 현재 동작 중인 API와 신규 API를 구분해서 관리한다.
- 신규 API는 제품 흐름상 중요한 순서대로 설계한다.
- 요청과 응답은 프론트에서 바로 사용할 수 있을 정도로 명확해야 한다.
- 조회용 API와 운영용 API를 분리한다.
- 상태 변경이 있는 도메인은 명시적인 상태 전환 API를 둔다.

## 3. API 범주

현재 및 목표 API는 아래 범주로 나뉜다.

- 인증 API
- 프로필 API
- 대시보드 API
- 시뮬레이터 API
- AI API
- 시뮬레이션 저장 API
- 전략 추천 API
- 구매 요청 API
- 승인 API
- 주문/포지션 API

## 4. 현재 구현된 API

### 4.1 인증 API

#### `POST /auth/signup`

설명:

- 신규 사용자 계정을 생성한다.

요청 예시:

```json
{
  "email": "user@company.com",
  "password": "Password123",
  "company_name": "HDEC"
}
```

응답 예시:

```json
{
  "id": 1,
  "email": "user@company.com",
  "company_name": "HDEC",
  "created_at": "2026-03-15T12:00:00"
}
```

#### `POST /auth/login`

설명:

- 사용자 로그인 후 access token을 반환한다.

요청 예시:

```json
{
  "email": "user@company.com",
  "password": "Password123"
}
```

응답 예시:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

#### `GET /auth/me`

설명:

- 현재 로그인한 사용자 정보를 조회한다.

### 4.2 프로필 API

#### `GET /profile/me`

설명:

- 로그인 사용자 프로필 조회

#### `PUT /profile/me`

설명:

- 프로필 수정

#### `POST /profile/me/avatar`

설명:

- 프로필 이미지 업로드

#### `POST /profile/me/email`

설명:

- 이메일 변경

#### `POST /profile/me/password`

설명:

- 비밀번호 변경

#### `POST /profile/me/delete`

설명:

- 계정 삭제

### 4.3 대시보드 API

#### `GET /api/v1/dashboard/companies`

설명:

- 회사별 최신 및 연도별 배출량 데이터를 반환한다.

응답 핵심 필드 예시:

```json
[
  {
    "id": 1,
    "name": "현대건설",
    "latestReportYear": 2024,
    "s1": 1000,
    "s2": 500,
    "s3": 3000,
    "allowance": 1200,
    "revenue": 1000000000,
    "energy_intensity": 1.2,
    "carbon_intensity_scope1": 0.1,
    "carbon_intensity_scope2": 0.05,
    "carbon_intensity_scope3": 0.3,
    "history": []
  }
]
```

#### `GET /api/v1/dashboard/benchmarks`

설명:

- 업계 탄소 및 에너지 집약도 기준선을 반환한다.

#### `POST /api/v1/dashboard/compare/insight`

설명:

- 경쟁사 비교 화면용 AI 인사이트를 생성한다.

요청 예시:

```json
{
  "my_company": "현대건설",
  "intensity_type": "revenue",
  "my_intensity": 2.1,
  "median_intensity": 2.6,
  "top10_intensity": 1.8,
  "best_company": "A Company",
  "is_better_than_median": true
}
```

### 4.4 시뮬레이터 API

#### `GET /api/v1/sim/dashboard/market-trends`

설명:

- K-ETS / EU-ETS 시장 가격 추이 데이터를 반환한다.

쿼리 파라미터:

- `period`

#### `GET /api/v1/sim/dashboard/trend-combined`

설명:

- 특정 회사 기준으로 시뮬레이션용 리스크 차트 데이터를 반환한다.

### 4.5 AI API

#### `POST /api/v1/ai/chat`

설명:

- 스트리밍 기반 챗봇 응답을 생성한다.

요청 예시:

```json
{
  "message": "현재 시장 트렌드 알려줘",
  "history": [],
  "companyName": "현대건설",
  "reportScope": "latest",
  "reportYear": 2024
}
```

#### `POST /api/v1/ai/strategy`

설명:

- 전략 설명 또는 전략 문안 생성

#### `POST /api/v1/ai/text-to-sql`

설명:

- 자연어 기반 SQL 초안 생성

## 5. 신규 API 우선순위

가장 먼저 추가해야 할 신규 API는 아래 순서다.

1. 시뮬레이션 저장 API
2. 전략 추천 API
3. 구매 요청 생성 API
4. 구매 요청 목록 API
5. 구매 요청 상태 변경 API
6. 승인 이력 API

이 순서가 중요한 이유는, 제품 가치가 `시뮬레이션 -> 전략 추천 -> 구매 요청` 흐름에서 가장 크게 올라가기 때문이다.

## 6. 신규 API 상세 명세

## 6.1 시뮬레이션 저장 API

### `POST /api/v1/sim/scenarios`

설명:

- 사용자가 현재 화면에서 구성한 시뮬레이션 입력값과 결과를 저장한다.

목적:

- 시뮬레이션 이력 보존
- 전략 추천의 기반 데이터 생성
- 구매 요청 생성의 출발점 확보

요청 예시:

```json
{
  "company_id": 1,
  "base_year": 2024,
  "price_scenario": "custom",
  "custom_price": 16500,
  "allocation_change": "decrease",
  "emission_change": 5,
  "auction_enabled": true,
  "auction_target_pct": 10,
  "budget": 350,
  "eur_krw_rate": 1450,
  "result_summary": {
    "net_exposure": 120000,
    "compliance_cost": 1980000000,
    "overseas_cost": 420000000,
    "integrated_total_cost": 2400000000,
    "risk_label": "CAUTION"
  }
}
```

응답 예시:

```json
{
  "id": 101,
  "company_id": 1,
  "status": "saved",
  "created_at": "2026-03-15T23:30:00"
}
```

### `GET /api/v1/sim/scenarios`

설명:

- 특정 회사의 저장된 시뮬레이션 목록 조회

쿼리 파라미터 예시:

- `company_id`
- `limit`

### `GET /api/v1/sim/scenarios/{scenario_id}`

설명:

- 특정 시뮬레이션 상세 조회

## 6.2 전략 추천 API

### `POST /api/v1/strategies/recommendations`

설명:

- 저장된 시뮬레이션 또는 전달된 시뮬레이션 입력값을 바탕으로 추천 전략을 생성한다.

목적:

- 계산 결과를 사람이 선택 가능한 전략안으로 변환한다.

요청 예시:

```json
{
  "scenario_id": 101
}
```

또는

```json
{
  "company_id": 1,
  "simulation_input": {
    "price_scenario": "base",
    "allocation_change": "maintain",
    "emission_change": 0,
    "budget": 350
  }
}
```

응답 예시:

```json
{
  "scenario_id": 101,
  "recommendations": [
    {
      "id": 1,
      "strategy_type": "immediate_buy",
      "title": "즉시 매수형",
      "summary": "현재 가격 구간에서 대부분 물량을 빠르게 확보하는 전략",
      "rationale": "가격 상승 리스크가 높고 예산 여유가 제한적이므로 조기 확보가 유리합니다.",
      "estimated_volume": 70000,
      "estimated_total_cost": 1100000000,
      "estimated_budget_ratio": 31.4,
      "risk_level": "medium",
      "target_alignment_score": 62,
      "recommended": true
    },
    {
      "id": 2,
      "strategy_type": "split_buy",
      "title": "분할 매수형",
      "summary": "단기 급등 리스크를 분산하기 위해 3회 분할 매수하는 전략",
      "rationale": "시장 변동성이 높아 평균 단가 방어가 가능합니다.",
      "estimated_volume": 70000,
      "estimated_total_cost": 1080000000,
      "estimated_budget_ratio": 30.8,
      "risk_level": "low",
      "target_alignment_score": 58,
      "recommended": false
    }
  ]
}
```

### `GET /api/v1/strategies/recommendations/{scenario_id}`

설명:

- 특정 시뮬레이션 기준 추천 전략 목록 조회

## 6.3 구매 요청 API

### `POST /api/v1/purchase-requests`

설명:

- 사용자가 선택한 전략 또는 시뮬레이션 결과를 바탕으로 구매 요청을 생성한다.

목적:

- 제품의 핵심 전환점
- 분석 결과를 실행 가능한 내부 요청으로 저장

요청 예시:

```json
{
  "company_id": 1,
  "scenario_id": 101,
  "strategy_recommendation_id": 1,
  "title": "2026년 2분기 K-ETS 조기 확보 요청",
  "description": "예산 범위 내에서 가격 상승 리스크를 줄이기 위한 조기 매수 요청",
  "request_type": "allowance_purchase",
  "market": "K-ETS",
  "requested_volume": 70000,
  "estimated_price": 16500,
  "estimated_total_cost": 1155000000,
  "currency": "KRW",
  "budget_limit": 35000000000,
  "risk_level": "medium"
}
```

응답 예시:

```json
{
  "id": 5001,
  "status": "draft",
  "created_at": "2026-03-15T23:40:00"
}
```

### `GET /api/v1/purchase-requests`

설명:

- 회사 기준 구매 요청 목록 조회

쿼리 파라미터 예시:

- `company_id`
- `status`
- `limit`

응답 예시:

```json
{
  "items": [
    {
      "id": 5001,
      "title": "2026년 2분기 K-ETS 조기 확보 요청",
      "market": "K-ETS",
      "requested_volume": 70000,
      "estimated_total_cost": 1155000000,
      "risk_level": "medium",
      "status": "submitted",
      "requested_by": {
        "id": 1,
        "name": "홍길동"
      },
      "created_at": "2026-03-15T23:40:00"
    }
  ],
  "total": 1
}
```

### `GET /api/v1/purchase-requests/{request_id}`

설명:

- 구매 요청 상세 조회

응답 예시:

```json
{
  "id": 5001,
  "company_id": 1,
  "scenario_id": 101,
  "strategy_recommendation_id": 1,
  "title": "2026년 2분기 K-ETS 조기 확보 요청",
  "description": "예산 범위 내에서 가격 상승 리스크를 줄이기 위한 조기 매수 요청",
  "request_type": "allowance_purchase",
  "market": "K-ETS",
  "requested_volume": 70000,
  "estimated_price": 16500,
  "estimated_total_cost": 1155000000,
  "currency": "KRW",
  "budget_limit": 35000000000,
  "risk_level": "medium",
  "status": "submitted",
  "requested_by": {
    "id": 1,
    "name": "홍길동"
  },
  "approval_history": [],
  "created_at": "2026-03-15T23:40:00",
  "updated_at": "2026-03-15T23:40:00"
}
```

### `PATCH /api/v1/purchase-requests/{request_id}`

설명:

- 초안 상태의 구매 요청 수정

수정 가능 범위 예시:

- 제목
- 설명
- 볼륨
- 예상 단가
- 예상 비용

### `POST /api/v1/purchase-requests/{request_id}/submit`

설명:

- 초안 상태의 요청을 승인 프로세스로 제출한다.

응답 예시:

```json
{
  "id": 5001,
  "status": "submitted",
  "submitted_at": "2026-03-15T23:50:00"
}
```

## 6.4 승인 API

### `POST /api/v1/purchase-requests/{request_id}/approve`

설명:

- 승인자가 요청을 승인한다.

요청 예시:

```json
{
  "comment": "예산 범위 내에서 진행 가능"
}
```

응답 예시:

```json
{
  "id": 5001,
  "status": "approved",
  "approved_at": "2026-03-16T09:00:00"
}
```

### `POST /api/v1/purchase-requests/{request_id}/reject`

설명:

- 승인자가 요청을 반려한다.

요청 예시:

```json
{
  "comment": "예산 조정 후 다시 제출 필요"
}
```

응답 예시:

```json
{
  "id": 5001,
  "status": "rejected",
  "rejected_at": "2026-03-16T09:10:00"
}
```

### `GET /api/v1/purchase-requests/{request_id}/approvals`

설명:

- 특정 요청의 승인 이력 조회

응답 예시:

```json
{
  "items": [
    {
      "id": 1,
      "action_type": "submit",
      "actor": {
        "id": 1,
        "name": "홍길동"
      },
      "comment": "",
      "acted_at": "2026-03-15T23:50:00"
    },
    {
      "id": 2,
      "action_type": "approve",
      "actor": {
        "id": 5,
        "name": "김승인"
      },
      "comment": "예산 범위 내에서 진행 가능",
      "acted_at": "2026-03-16T09:00:00"
    }
  ]
}
```

## 6.5 주문 및 포지션 API

이 범주는 우선순위가 더 낮지만 장기적으로 필요하다.

### `POST /api/v1/orders`

설명:

- 승인된 구매 요청으로부터 실행 주문 생성

### `GET /api/v1/orders`

설명:

- 주문 목록 조회

### `GET /api/v1/orders/{order_id}`

설명:

- 주문 상세 조회

### `GET /api/v1/positions`

설명:

- 회사별 현재 보유 포지션 조회

## 7. 권장 응답 공통 구조

운영형 API는 응답 형식을 가능한 한 통일하는 것이 좋다.

### 단건 조회

```json
{
  "data": {}
}
```

### 목록 조회

```json
{
  "items": [],
  "total": 0
}
```

### 상태 변경 응답

```json
{
  "id": 1,
  "status": "approved",
  "message": "요청이 승인되었습니다."
}
```

현재 구현된 API는 이 형식이 완전히 통일되어 있지 않으므로, 신규 운영 API부터 먼저 통일하는 것을 권장한다.

## 8. 인증 및 권한 처리 원칙

### 인증

- 모든 운영형 API는 JWT 인증을 기본으로 한다.

### 권한

권장 역할:

- `viewer`: 조회만 가능
- `analyst`: 시뮬레이션 및 전략 조회 가능
- `requester`: 구매 요청 생성 및 제출 가능
- `approver`: 승인/반려 가능
- `admin`: 전체 관리 가능

권한 예시:

- 시뮬레이션 저장: `analyst` 이상
- 구매 요청 생성: `requester` 이상
- 승인/반려: `approver` 이상

## 9. 상태 코드 가이드

- `200 OK`: 조회/수정 성공
- `201 Created`: 생성 성공
- `400 Bad Request`: 잘못된 입력
- `401 Unauthorized`: 인증 실패
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 대상 없음
- `409 Conflict`: 상태 충돌

상태 충돌 예시:

- 이미 승인된 요청을 다시 수정하려는 경우
- 이미 제출된 요청을 다시 제출하려는 경우

## 10. 추천 구현 순서

### 1차 구현

- `POST /api/v1/sim/scenarios`
- `POST /api/v1/strategies/recommendations`
- `POST /api/v1/purchase-requests`
- `GET /api/v1/purchase-requests`
- `GET /api/v1/purchase-requests/{request_id}`

### 2차 구현

- `POST /api/v1/purchase-requests/{request_id}/submit`
- `POST /api/v1/purchase-requests/{request_id}/approve`
- `POST /api/v1/purchase-requests/{request_id}/reject`
- `GET /api/v1/purchase-requests/{request_id}/approvals`

### 3차 구현

- 주문 생성 API
- 주문 조회 API
- 포지션 조회 API

## 11. 다음 작업 제안

이 문서 다음으로 가장 자연스럽게 이어지는 작업은 두 가지다.

1. 실제 백엔드 구현을 위한 DB 스키마 초안 작성
2. 구매 요청 플로우 기준 와이어프레임 또는 화면 명세 작성

특히 지금 단계에서는 아래 두 문서를 추가로 만들면 좋다.

- `DB_SCHEMA_NEXT.md`
- `USER_FLOW.md`

이 두 문서가 있으면, 문서 체계가 기획 -> 기능 -> 구조 -> 도메인 -> API -> 구현 설계 흐름으로 거의 완성된다.
