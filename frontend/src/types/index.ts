export type TabType = 'dashboard' | 'compare' | 'simulator' | 'target';
export type MarketType = 'K-ETS' | 'EU-ETS';
export type IntensityType = 'revenue' | 'production';
export type TimeRangeType = '1개월' | '3개월' | '1년' | '전체';

export interface TrajectoryData {
    year: string;
    v: number;
}

export interface CompanyConfig {
    id: number;
    name: string;
    dartCode: string;
    baseEmissions: number; // 기준 배출량
    allowance?: number; // 무상 할당량 (DB 값 우선 사용)
    targetSavings: number; // 목표 절감률
    // Extra data for simulation/dashboard
    s1: number;
    s2: number;
    s3: number;
    s1Domestic?: number;
    s2Domestic?: number;
    s1Overseas?: number;
    s2Overseas?: number;
    revenue: number;
    production: number;
    // New fields
    carbon_intensity_scope1?: number;
    carbon_intensity_scope2?: number;
    carbon_intensity_scope3?: number;
    energy_intensity?: number;
    latestReportYear?: number;
}

export interface Competitor {
    id: number;
    name: string;
    s1: number;
    s2: number;
    s3: number;
    revenue: number;
    production: number;
    trustScore: number;
    trajectory: TrajectoryData[];
    intensityValue?: number;
    // New fields
    carbon_intensity_scope1?: number;
    carbon_intensity_scope2?: number;
    carbon_intensity_scope3?: number;
    energy_intensity?: number;
}

export interface TrendData {
    date: string;
    type?: 'actual' | 'forecast';
    krPrice?: number;
    euPrice?: number;
    month?: string;
}

export interface Tranche {
    id: number;
    market: MarketType;
    price: number;
    month: string;
    isFuture: boolean;
    percentage: number;
}

export interface MarketInfo {
    id: MarketType;
    name: string;
    ticker: string;
    price: number;
    currency: string;
    change: number;
    color: string;
    desc: string;
    high: number;
    low: number;
    volatility: string;
}

export interface ChatMessage {
    id: string;
    role: string; // 'user' | 'assistant'
    text: string;
}

// ── K-ETS Simulator Types ──
export type PriceScenarioType = 'base' | 'custom';
export type AllocationChangeType = 'maintain' | 'decrease10' | 'decrease30' | 'zero';

export interface ReductionOption {
    id: string;
    name: string;
    annualReduction: number;  // tCO₂e
    cost: number;             // 억원
    mac: number;              // 원/tCO₂e (Marginal Abatement Cost)
    leadTime: number;         // 개월
    enabled: boolean;
    thisYearApplicable: boolean;  // 리드타임 ≤12개월 → true
}

export interface RiskTrigger {
    id: string;
    type: 'price' | 'volume' | 'financial';
    label: string;
    threshold: number;
    currentValue: number;
    unit: string;
    isTriggered: boolean;
}

export interface ProcurementMix {
    freeAllocation: number;  // %
    auction: number;         // %
    market: number;          // %
}

export interface StrategyDetail {
    name: string;
    label: string;
    totalCost: number;              // 억원
    complianceCost: number;         // 억원
    abatementCost: number;          // 억원
    appliedReductions: string[];    // 적용된 감축 옵션 이름
    purchaseVolume: number;         // 구매량 tCO₂e
    explanation: string;            // 추천 근거
}

export interface SimResult {
    // Step 1: 순노출
    adjustedEmissions: number;      // tCO₂e (배출변화 적용)
    adjustedAllocation: number;     // tCO₂e (할당변화 적용)
    thisYearReduction: number;      // tCO₂e (올해 반영 가능 감축)
    nextYearReduction: number;      // tCO₂e (차년도 반영 감축)
    netExposure: number;            // tCO₂e (순노출)
    // Step 2: 컴플라이언스 비용
    complianceCostBase: number;     // 원
    // Step 3: 감축 비용
    totalAbatementCost: number;     // 억원
    // 합산
    totalCarbonCost: number;        // 억원 (compliance + abatement)
    // 파생 지표
    effectiveCarbonPrice: number;   // 원/tCO₂e (가중평균)
    profitImpact: number;           // % (총탄소비용/영업이익)
    operatingProfit: number;        // 억원
    economicAbatementPotential: number; // tCO₂e (MAC<ETS인 옵션 합계)
    // 전략
    strategies: StrategyDetail[];
    optimalStrategyIndex: number;
}
