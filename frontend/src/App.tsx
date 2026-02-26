import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import type {
  TabType, MarketType, IntensityType, TimeRangeType,
  TrendData, Tranche, ChatMessage, CompanyConfig,
  PriceScenarioType, AllocationChangeType, SimResult, StrategyDetail
} from './types';
import {
  MARKET_DATA, MOCK_COMPANIES,
  ETS_PRICE_SCENARIOS, ALLOCATION_SCENARIOS, AUCTION_CONFIG
} from './data/mockData';
import { API_BASE_URL } from './config';
import { Header } from './components/layout/Header';
import { DashboardTab } from './features/\uB300\uC2DC\uBCF4\uB4DC/DashboardTab';
import { CompareTab } from './features/\uACBD\uC7C1\uC0AC\uBE44\uAD50/CompareTab';
import { SimulatorTab } from './features/\uC2DC\uBBAC\uB808\uC774\uD130/SimulatorTab';
import { TargetTab } from './features/\uBAA9\uD45C\uC124\uC815/TargetTab';
import { ChatBot } from './features/\uCC57\uBD07/ChatBot';
import { Login } from './features/auth/Login';
import { WelcomePage } from './features/auth/WelcomePage';
import { Signup } from './features/auth/Signup';
import { DataInput } from './features/data-input/DataInput';
import { Reports } from './features/reports/Reports';
import { Analytics } from './features/analytics/Analytics';
import { Profile } from './features/profile/Profile';
import { AiService, MarketService } from './services/api';
import { getToken, removeToken } from './services/authApi';
import { fetchProfile } from './services/profileApi';
import type { ProfileResponse } from './services/profileApi';

const generateMessageId = () => {

  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {

    return crypto.randomUUID();

  }

  return `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`;

};

const createMessage = (role: string, text: string): ChatMessage => ({

  id: generateMessageId(),

  role,

  text

});

// Default empty company to prevent crashes

const EMPTY_COMPANY: CompanyConfig = {

  id: 0,

  name: "No Data",

  dartCode: "",

  baseEmissions: 0,
  allowance: 0,

  investCapex: 0,

  targetSavings: 0,

  s1: 0, s2: 0, s3: 0, revenue: 0, production: 0

};

const tabs = [
  { id: 'dashboard' as TabType, label: 'Dashboard' },
  { id: 'compare' as TabType, label: 'Compare' },
  { id: 'simulator' as TabType, label: 'Simulator' },
  { id: 'target' as TabType, label: 'Targets' },
];

type ViewType = 'login' | 'signup' | 'welcome' | 'dashboard' | 'profile' | 'data-input' | 'reports' | 'analytics';

const resolveRoute = (pathname: string): { view: ViewType; tab: TabType } => {
  if (pathname === '/login') return { view: 'login', tab: 'dashboard' };
  if (pathname === '/signup') return { view: 'signup', tab: 'dashboard' };
  if (pathname === '/welcome') return { view: 'welcome', tab: 'dashboard' };
  if (pathname === '/profile') return { view: 'profile', tab: 'dashboard' };
  if (pathname === '/data-input') return { view: 'data-input', tab: 'dashboard' };
  if (pathname === '/reports') return { view: 'reports', tab: 'dashboard' };
  if (pathname === '/analytics') return { view: 'analytics', tab: 'dashboard' };
  if (pathname === '/dashboard/compare') return { view: 'dashboard', tab: 'compare' };
  if (pathname === '/dashboard/simulator') return { view: 'dashboard', tab: 'simulator' };
  if (pathname === '/dashboard/target') return { view: 'dashboard', tab: 'target' };
  return { view: 'dashboard', tab: 'dashboard' };
};

const buildPath = (view: ViewType, tab: TabType): string => {
  if (view === 'login') return '/login';
  if (view === 'signup') return '/signup';
  if (view === 'welcome') return '/welcome';
  if (view === 'profile') return '/profile';
  if (view === 'data-input') return '/data-input';
  if (view === 'reports') return '/reports';
  if (view === 'analytics') return '/analytics';
  if (tab === 'compare') return '/dashboard/compare';
  if (tab === 'simulator') return '/dashboard/simulator';
  if (tab === 'target') return '/dashboard/target';
  return '/dashboard';
};

const App: React.FC = () => {

  // --- Data State ---

  const [companies, setCompanies] = useState<CompanyConfig[]>([]);

  const [benchmarks, setBenchmarks] = useState<any>({});

  const [isLoading, setIsLoading] = useState<boolean>(true);

  const [userProfile, setUserProfile] = useState<ProfileResponse | null>(null);

  // --- State ---
  const location = useLocation();
  const navigate = useNavigate();

  const initialRoute = resolveRoute(location.pathname);
  const [view, setView] = useState<ViewType>(initialRoute.view);

  const [activeTab, setActiveTab] = useState<TabType>(initialRoute.tab);

  useEffect(() => {

    const loadProfile = async () => {

      try {

        const profile = await fetchProfile();

        setUserProfile(profile);

      } catch (error) {

        setUserProfile(null);

      }

    };

    if (getToken()) {

      loadProfile();

    } else {

      setUserProfile(null);

    }

  }, [location.pathname]);

  const [intensityType, setIntensityType] = useState<IntensityType>('revenue');

  const [activeScopes, setActiveScopes] = useState({ s1: true, s2: true, s3: false });

  // Market Data State

  const [fullHistoryData, setFullHistoryData] = useState<TrendData[]>([]);

  // Simulator State

  const [selectedMarket, setSelectedMarket] = useState<MarketType>('K-ETS');

  const [timeRange, setTimeRange] = useState<TimeRangeType>('1년');

  const [tranches, setTranches] = useState<Tranche[]>([

    { id: 1, market: 'K-ETS', price: 15200, month: '25.10', isFuture: false, percentage: 30 },

    { id: 2, market: 'EU-ETS', price: 74.20, month: '26.01', isFuture: false, percentage: 50 },

  ]);

  const [simBudget, setSimBudget] = useState<number>(350);
  const [eurKrwRate, setEurKrwRate] = useState<number>(1450);

  const [simRisk, setSimRisk] = useState<number>(25);

  const [activeMarkets] = useState<MarketType[]>(['K-ETS', 'EU-ETS']);

  // === K-ETS Simulator State ===

  const [priceScenario, setPriceScenario] = useState<PriceScenarioType>('base');

  const [customPrice, setCustomPrice] = useState<number>(15000);

  const [allocationChange, setAllocationChange] = useState<AllocationChangeType>('maintain');

  const [emissionChange, setEmissionChange] = useState<number>(0);

  const [auctionEnabled, setAuctionEnabled] = useState<boolean>(true);

  const [auctionTargetPct, setAuctionTargetPct] = useState<number>(10);

  const [selectedCompId, setSelectedCompId] = useState<number>(1);

  const selectedCompany = MOCK_COMPANIES.find(c => c.id === selectedCompId) || MOCK_COMPANIES[0];

  const [isChatOpen, setIsChatOpen] = useState<boolean>(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>(() => [
    createMessage(
      'assistant',
      "\uC548\uB155\uD558\uC138\uC694! ESG AI \uC5B4\uB4DC\uBC14\uC774\uC800\uC785\uB2C8\uB2E4. \uBB34\uC5C7\uC744 \uB3C4\uC640\uB4DC\uB9B4\uAE4C\uC694?"
    )
  ]);
  const [inputMessage, setInputMessage] = useState<string>('');

  // 경로 기반 네비게이션
  const navigateTo = useCallback((newView: ViewType, newTab: TabType = activeTab) => {
    setView(newView);
    setActiveTab(newTab);
    navigate(buildPath(newView, newTab));
  }, [activeTab, navigate]);

  // UI State

  const [isInsightOpen, setIsInsightOpen] = useState<boolean>(true);

  const [reportScope, setReportScope] = useState<'latest' | 'history'>('latest');

  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // activeTab 변경 시 localStorage에 저장 (기존 동작 호환)

  useEffect(() => {

    localStorage.setItem('activeTab', activeTab);

  }, [activeTab]);

  // URL -> 상태 동기화
  useEffect(() => {
    const { view: routeView, tab: routeTab } = resolveRoute(location.pathname);
    setView(routeView);
    setActiveTab(routeTab);
  }, [location.pathname]);

  // 인증 가드 및 기본 경로 리다이렉트
  useEffect(() => {
    const hasToken = Boolean(getToken());
    const publicPaths = new Set(['/login', '/signup']);
    const isKnownPath =
      location.pathname === '/' ||
      location.pathname === '/login' ||
      location.pathname === '/signup' ||
      location.pathname === '/welcome' ||
      location.pathname === '/profile' ||
      location.pathname === '/data-input' ||
      location.pathname === '/reports' ||
      location.pathname === '/analytics' ||
      location.pathname === '/dashboard' ||
      location.pathname === '/dashboard/compare' ||
      location.pathname === '/dashboard/simulator' ||
      location.pathname === '/dashboard/target';

    if (!isKnownPath) {
      navigate(hasToken ? '/dashboard' : '/login', { replace: true });
      return;
    }

    if (!hasToken && !publicPaths.has(location.pathname)) {
      navigate('/login', { replace: true });
      return;
    }

    if (hasToken && (location.pathname === '/' || publicPaths.has(location.pathname))) {
      navigate('/dashboard', { replace: true });
    }
  }, [location.pathname, navigate]);

  // --- Effects: Fetch Data from API ---

  useEffect(() => {

    const fetchData = async () => {

      try {

        // 1. Market Trends
        const trendsController = new AbortController();
        const trendsTimeout = setTimeout(() => trendsController.abort(), 10000); // 10s timeout for trends

        try {
          const trends = await MarketService.getMarketTrends('all', trendsController.signal);
          clearTimeout(trendsTimeout);
          if (trends.chart_data && trends.chart_data.length > 0) {
            const mappedData = trends.chart_data.map((d: any) => ({
              date: d.date,
              krPrice: d['K-ETS'] || d.krPrice,
              euPrice: d['EU-ETS'] || d.euPrice,
              type: d.type || 'actual'
            }));
            setFullHistoryData(mappedData);
          }
        } catch (err) {
          console.warn('[System] Market trends fetch failed or timed out:', err);
        }

        // 2. Dashboard Data (Companies & Benchmarks)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 8000); // 8s timeout

        try {
          const dashboardRes = await fetch(`${API_BASE_URL}/api/v1/dashboard/companies`, {
            signal: controller.signal
          });
          clearTimeout(timeoutId);

          if (dashboardRes.ok) {
            const dashboardJson = await dashboardRes.json();
            if (Array.isArray(dashboardJson) && dashboardJson.length > 0) {
              setCompanies(dashboardJson);
              console.log('[System] Companies loaded from API:', dashboardJson.length);
              setSelectedCompId(dashboardJson[0].id);
            } else {
              throw new Error('Empty company list');
            }
          } else {
            throw new Error(`API error: ${dashboardRes.status}`);
          }
        } catch (err) {
          console.warn('[System] Dashboard API failed or timed out. Falling back to Mock Data.', err);
          setCompanies(MOCK_COMPANIES);
          if (MOCK_COMPANIES.length > 0) {
            setSelectedCompId(MOCK_COMPANIES[0].id);
          }
        }

        const benchRes = await fetch(`${API_BASE_URL}/api/v1/dashboard/benchmarks`);

        const benchJson = await benchRes.json();

        if (benchJson && benchJson.revenue) {

          setBenchmarks(benchJson);

        }

      } catch (err) {

        console.error('[System] Failed to fetch startup data:', err);

      } finally {

        setIsLoading(false);

      }

    };

    fetchData();

    const interval = setInterval(fetchData, 60000);

    return () => clearInterval(interval);

  }, []);

  useEffect(() => {
    let isMounted = true;

    const fetchFxRate = async () => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);
      try {
        const res = await fetch('https://open.er-api.com/v6/latest/EUR', {
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        if (!res.ok) return;
        const json = await res.json();
        const krwRate = Number(json?.rates?.KRW);
        if (isMounted && Number.isFinite(krwRate) && krwRate > 0) {
          setEurKrwRate(Math.round(krwRate));
        }
      } catch {
        // Keep fallback value (1450) when live FX fetch fails
      }
    };

    fetchFxRate();
    const interval = setInterval(fetchFxRate, 60 * 60 * 1000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const trendData = useMemo<any[]>(() => {

    if (fullHistoryData.length === 0) return [];

    let filtered = [...fullHistoryData];

    const todayIndex = filtered.findIndex(d => d.type === 'forecast');

    const splitIndex = todayIndex === -1 ? filtered.length : todayIndex;

    if (timeRange === '1개월') {
      const start = Math.max(0, splitIndex - 22);
      const end = Math.min(filtered.length, splitIndex + 22);
      filtered = filtered.slice(start, end);
    } else if (timeRange === '3개월') {
      const start = Math.max(0, splitIndex - 66);
      const end = Math.min(filtered.length, splitIndex + 66);
      filtered = filtered.slice(start, end);
    } else if (timeRange === '1년') {
      const start = Math.max(0, splitIndex - 250);
      const end = Math.min(filtered.length, splitIndex + 125);
      filtered = filtered.slice(start, end);
    } else if (timeRange === '전체') {
      // Do not filter out points to preserve real volatility
    }

    return filtered;

  }, [timeRange, fullHistoryData]);

  // --- Calculations ---

  // Use companies state for selection

  const selectedConfig = useMemo(() => {

    if (companies.length === 0) return EMPTY_COMPANY;

    return companies.find((c: CompanyConfig) => c.id === selectedCompId) || companies[0];

  }, [companies, selectedCompId]);

  const selectedComp = useMemo(() => {

    return {

      id: selectedConfig.id,

      name: selectedConfig.name,

      s1: selectedConfig.s1,

      s2: selectedConfig.s2,

      s3: selectedConfig.s3,

      revenue: selectedConfig.revenue,

      production: selectedConfig.production || 0,

      trustScore: 95,

      trajectory: [],

      intensityValue: 0,

      // Pass through new fields if available

      carbon_intensity_scope1: selectedConfig.carbon_intensity_scope1,

      carbon_intensity_scope2: selectedConfig.carbon_intensity_scope2,

      carbon_intensity_scope3: selectedConfig.carbon_intensity_scope3,

      energy_intensity: selectedConfig.energy_intensity,

      history: (selectedConfig as any).history // Explicit cast to avoid lingering type issues

    };

  }, [selectedConfig]);

  const totalExposure = useMemo(() => {

    return (activeScopes.s1 ? selectedComp.s1 : 0) +

      (activeScopes.s2 ? selectedComp.s2 : 0) +

      (activeScopes.s3 ? selectedComp.s3 : 0);

  }, [selectedComp, activeScopes]);

  const costEU_KRW = totalExposure * MARKET_DATA['EU-ETS'].price * 1450;

  const activeTranches = tranches.filter(t => activeMarkets.includes(t.market));

  const totalAllocatedPct = activeTranches.reduce((sum: number, t: Tranche) => sum + t.percentage, 0);

  const budgetInWon = simBudget * 100000000;

  const estimatedSavings = budgetInWon * (0.1 + (simRisk * 0.002));

  // === 실시간 K-ETS 가격 (API 데이터 기반) ===
  const latestKetsData = useMemo(() => {
    if (fullHistoryData.length === 0) return { price: 15200, change: 0 };
    const actuals = fullHistoryData.filter((d: TrendData) => d.type === 'actual');
    if (actuals.length < 2) return { price: 15200, change: 0 };
    const latest = actuals[actuals.length - 1];
    const previous = actuals[actuals.length - 2];
    const latestPrice = latest.krPrice || 15200;
    const previousPrice = previous.krPrice || 15200;
    const change = previousPrice === 0 ? 0 : ((latestPrice - previousPrice) / previousPrice) * 100;
    return { price: latestPrice, change: parseFloat(change.toFixed(1)) };
  }, [fullHistoryData]);

  // === 실시간 EU-ETS 가격 (API 데이터 기반) ===
  const latestEutsData = useMemo(() => {
    if (fullHistoryData.length === 0) return { price: 74.20, change: 0 };
    const actuals = fullHistoryData.filter((d: TrendData) => d.type === 'actual');
    if (actuals.length < 2) return { price: 74.20, change: 0 };
    const latest = actuals[actuals.length - 1];
    const previous = actuals[actuals.length - 2];
    const latestPrice = latest.euPrice || 74.20;
    const previousPrice = previous.euPrice || 74.20;
    const change = previousPrice === 0 ? 0 : ((latestPrice - previousPrice) / previousPrice) * 100;
    return { price: latestPrice, change: parseFloat(change.toFixed(1)) };
  }, [fullHistoryData]);

  // API 호출 완료 후 기본 편입 비중(트랜치)의 단가를 최신가로 1회 스냅 업데이트
  useEffect(() => {
    if (fullHistoryData.length > 0) {
      setTranches(prev => prev.map(t => {
        if (t.id === 1 && t.price === 15200 && latestKetsData.price !== 15200) {
          return { ...t, price: latestKetsData.price };
        }
        if (t.id === 2 && t.price === 74.20 && latestEutsData.price !== 74.20) {
          return { ...t, price: latestEutsData.price };
        }
        return t;
      }));
    }
  }, [latestKetsData.price, latestEutsData.price, fullHistoryData.length]);

  // === 경매 절감률 동적 계산: (연평균시장가 - 연평균경매낙찰가) / 연평균시장가 × 100 ===
  const auctionSavingsRate = useMemo(() => {
    const actuals = fullHistoryData.filter((d: TrendData) => d.type === 'actual');
    if (actuals.length === 0) return 0;
    const avgMarketPrice = actuals.reduce((sum: number, d: TrendData) => sum + (d.krPrice || 0), 0) / actuals.length;
    if (avgMarketPrice <= 0) return 0;
    const rate = ((avgMarketPrice - AUCTION_CONFIG.avgAuctionPrice) / avgMarketPrice) * 100;
    return parseFloat(Math.max(0, rate).toFixed(1));
  }, [fullHistoryData]);

  // === K-ETS Simulator Calculation (3-Step Formula) ===

  const currentETSPrice = priceScenario === 'custom' ? customPrice : latestKetsData.price;

  const simResult = useMemo<SimResult>(() => {

    const s1s2 = selectedComp.s1 + selectedComp.s2;

    // === Step 1: 배출량 조정 ===

    const adjustedEmissions = Math.round(s1s2 * (1 + emissionChange / 100));

    // DB allowance 우선, 없으면 기준 배출량의 90%를 fallback으로 사용
    const baseAllocation = (selectedConfig.allowance ?? 0) > 0
      ? (selectedConfig.allowance as number)
      : selectedConfig.baseEmissions * 0.9;

    const adjustedAllocation = Math.round(baseAllocation * ALLOCATION_SCENARIOS[allocationChange].factor);

    const enabledOptions: any[] = [];
    const thisYearReduction = 0;
    const nextYearReduction = 0;

    const netExposure = Math.max(0, adjustedEmissions - adjustedAllocation - thisYearReduction);

    // === Step 2: 이행비용 (기준 = 실시간 시장가) ===

    const complianceCostBase = netExposure * MARKET_DATA['K-ETS'].price;

    // === Step 3: 감축비용 (내부 감축 투자비) ===

    const totalAbatementCost = 0;

    // === 합산 ===
    let complianceCostCurrent = netExposure * currentETSPrice;

    // 경매 참여 시 할인율 적용 (조달 비중만큼 할인)
    if (auctionEnabled && netExposure > 0) {
      const auctionVol = netExposure * (auctionTargetPct / 100);
      const marketVol = netExposure - auctionVol;
      const discountFactor = 1 - (auctionSavingsRate / 100);
      const auctionPrice = currentETSPrice * discountFactor;
      complianceCostCurrent = (auctionVol * auctionPrice + marketVol * currentETSPrice);
    }

    // 포트폴리오 확정값이 있으면 덮어씌움 (기능 제거됨: 실시간으로 계산 결과 표시)
    const finalComplianceCost = complianceCostCurrent;

    const totalCarbonCost = finalComplianceCost + totalAbatementCost;

    // === 수익성 영향 ===


    const operatingProfit = selectedConfig.revenue * 0.08;

    const profitImpact = operatingProfit > 0 ? (totalCarbonCost / operatingProfit) * 100 : 0;

    const economicAbatementPotential = 0;

    const totalHandled = adjustedAllocation + thisYearReduction + netExposure;

    const effectiveCarbonPrice = totalHandled > 0 ? totalCarbonCost / totalHandled : 0;

    // === 전략 비교 ===

    const baseNetExposure = Math.max(0, adjustedEmissions - adjustedAllocation);

    const economicOptions: any[] = [];

    const econReduction = economicOptions.reduce((s, r) => s + r.annualReduction, 0);

    const econAbatementCost = economicOptions.reduce((s, r) => s + r.cost, 0);

    const econPurchase = Math.max(0, baseNetExposure - econReduction);

    const stratA: StrategyDetail = {

      name: 'A', label: '최적 전략',

      complianceCost: econPurchase * currentETSPrice,

      abatementCost: econAbatementCost * 1e8,

      totalCost: (econPurchase * currentETSPrice) + (econAbatementCost * 1e8),

      appliedReductions: economicOptions.map(r => r.name),

      purchaseVolume: econPurchase,

      explanation: economicOptions.length > 0

        ? `${economicOptions.map(r => `${r.name}(${r.annualReduction.toLocaleString()}t, MAC ₩${(r.mac / 1000).toFixed(0)}k)`).join(' + ')} 나머지 ${econPurchase.toLocaleString()}t 구매`


        : `경제적 감축 옵션 없음 - 전량 ${baseNetExposure.toLocaleString()}t 구매`


    };

    const stratB: StrategyDetail = {

      name: 'B', label: '전량 구매',


      complianceCost: baseNetExposure * currentETSPrice / 1e8,

      abatementCost: 0,

      totalCost: baseNetExposure * currentETSPrice / 1e8,

      appliedReductions: [],

      purchaseVolume: baseNetExposure,

      explanation: `순노출량 ${baseNetExposure.toLocaleString()}t × ₩${currentETSPrice.toLocaleString()} = ₩${(baseNetExposure * currentETSPrice).toLocaleString()}`

    };

    const allThisYearOptions: any[] = [];

    const allReduction = allThisYearOptions.reduce((s, r) => s + r.annualReduction, 0);

    const allAbatementCost = allThisYearOptions.reduce((s, r) => s + r.cost, 0);

    const allPurchase = Math.max(0, baseNetExposure - allReduction);

    const stratC: StrategyDetail = {

      name: 'C', label: '공격적 (전체 감축)',

      complianceCost: allPurchase * currentETSPrice,

      abatementCost: allAbatementCost * 1e8,

      totalCost: (allPurchase * currentETSPrice) + (allAbatementCost * 1e8),

      appliedReductions: allThisYearOptions.map(r => r.name),

      purchaseVolume: allPurchase,

      explanation: `${allThisYearOptions.map(r => r.name).join(' + ')} 전체 적용 (${allReduction.toLocaleString()}t 감축) 나머지 ${allPurchase.toLocaleString()}t 구매`

    };

    const strategies = [stratA, stratB, stratC];

    const optimalStrategyIndex = strategies.reduce((minIdx, s, i, arr) =>

      s.totalCost < arr[minIdx].totalCost ? i : minIdx, 0);

    return {

      adjustedEmissions, adjustedAllocation, thisYearReduction, nextYearReduction, netExposure,

      complianceCostBase: finalComplianceCost,

      totalAbatementCost, totalCarbonCost, effectiveCarbonPrice,

      profitImpact, operatingProfit, economicAbatementPotential,

      strategies, optimalStrategyIndex

    };

  }, [selectedComp, emissionChange, allocationChange, selectedConfig, currentETSPrice, auctionEnabled, auctionTargetPct]);

  // [핵심] DB의 집약도 데이터로 집약도 계산


  const getIntensityFromDB = (c: any) => {

    if (intensityType === 'revenue') {

      // 매출 집약도 = DB의 carbon_intensity_scope1/2/3 합산 (tCO2e / 매출 1억원)


      const s1Intensity = activeScopes.s1 ? (c.carbon_intensity_scope1 || 0) : 0;

      const s2Intensity = activeScopes.s2 ? (c.carbon_intensity_scope2 || 0) : 0;

      const s3Intensity = activeScopes.s3 ? (c.carbon_intensity_scope3 || 0) : 0;

      return s1Intensity + s2Intensity + s3Intensity;

    } else {

      // 에너지 집약도 = DB의 energy_intensity (TJ / 매출 1억원)


      return c.energy_intensity || 0;

    }

  };

  const chartData = useMemo(() => {

    // [핵심] DB 데이터로 companies 배열에서 집약도 계산


    if (companies.length === 0) return [];

    return companies.map(c => ({

      id: c.id,

      name: c.name,

      s1: c.s1,

      s2: c.s2,

      s3: c.s3,

      revenue: c.revenue,

      production: (c as any).production || 0,

      trustScore: 85,

      trajectory: [],

      // DB의 집약도 데이터 전달


      carbon_intensity_scope1: (c as any).carbon_intensity_scope1 || 0,

      carbon_intensity_scope2: (c as any).carbon_intensity_scope2 || 0,

      carbon_intensity_scope3: (c as any).carbon_intensity_scope3 || 0,

      energy_intensity: (c as any).energy_intensity || 0,

      intensityValue: getIntensityFromDB(c)

    })).sort((a, b) => (a.intensityValue || 0) - (b.intensityValue || 0));

  }, [companies, intensityType, activeScopes]);

  // 에너지 집약도 벤치마크 데이터 처리


  const topThreshold = intensityType === 'energy'

    ? (chartData.length > 0 ? chartData[Math.floor(chartData.length * 0.1)]?.intensityValue || 0 : 0)

    : (benchmarks[intensityType]?.top10 || 0);

  const medianThreshold = intensityType === 'energy'

    ? (chartData.length > 0 ? chartData[Math.floor(chartData.length * 0.5)]?.intensityValue || 0 : 0)

    : (benchmarks[intensityType]?.median || 0);

  const ytdAnalysis = useMemo(() => {

    // [핵심] DB의 carbon_intensity 데이터로 집약도 계산


    const history = selectedComp.history || [];

    // history에서 최근 2개년 데이터를 비교 (데이터가 있는 최신 2개년)


    const sortedYears = history.map((h: any) => h.year).sort((a: number, b: number) => b - a);

    const latestYear = sortedYears[0];

    const previousYear = sortedYears[1];

    const currentYearData = history.find((h: any) => h.year === latestYear);

    const lastYearData = history.find((h: any) => h.year === previousYear);

    if (!currentYearData) {

      return { currentIntensity: '0.0', percentChange: '0.0', delta: '0.0', period: '-', scopeLabel: 'None' };

    }

    // [핵심] 대시보드 탭의 집약도 카드는 필터 및 Compare 탭의 토글 상태와 무관하게 항상 S1+S2 탄소집약도 사용
    const getIntensity = (data: any) => {
      return (data.carbon_intensity_scope1 || 0) + (data.carbon_intensity_scope2 || 0);
    };

    const ty_intensity = getIntensity(currentYearData);
    const ly_intensity = lastYearData ? getIntensity(lastYearData) : ty_intensity;
    const diff = ty_intensity - ly_intensity;
    const pct = ly_intensity !== 0 ? (diff / ly_intensity) * 100 : 0;

    return {

      currentIntensity: ty_intensity.toFixed(2),

      percentChange: pct.toFixed(1),

      delta: diff.toFixed(2),

      period: lastYearData ? `${latestYear} vs ${previousYear}` : `${latestYear} (비교할 데이터 없음)`,


      scopeLabel: 'S1+S2'

    };

  }, [selectedComp, intensityType, activeScopes]);

  const sbtiAnalysis = useMemo(() => {
    const baseYear = 2021;
    const targetYear = 2030;
    const reductionRate = 0.042;
    const betaPrior = Math.log(1 - reductionRate);
    const history = Array.isArray((selectedComp as any).history) ? (selectedComp as any).history : [];

    // 필터 여부와 상관없이 항상 Scope 1 + Scope 2 고정
    const sumScopes = (row: any) => (row?.s1 || 0) + (row?.s2 || 0);

    const actualEmissionNow = sumScopes(selectedComp);
    const currentYear = new Date().getFullYear();
    const latestDataYear = history.length > 0 ? Math.max(...history.map((h: any) => h.year)) : currentYear;

    let baseEmission = 0;
    const baseYearData = history.find((h: any) => h.year === baseYear);
    if (baseYearData) {
      baseEmission = sumScopes(baseYearData);
    } else if (history.length > 0) {
      const oldestData = history.reduce((oldest: any, row: any) => (!oldest || row.year < oldest.year ? row : oldest), null);
      baseEmission = sumScopes(oldestData);
    } else {
      baseEmission = actualEmissionNow;
    }
    if (baseEmission <= 0) {
      baseEmission = actualEmissionNow;
    }

    const yearsElapsed = Math.max(0, latestDataYear - baseYear);
    const targetReductionPct = reductionRate * yearsElapsed;
    const targetEmissionNow = Math.max(0, baseEmission * (1 - targetReductionPct));
    const actualReductionPct = baseEmission > 0 ? (baseEmission - actualEmissionNow) / baseEmission : 0;
    const currentReductionPctNum = Math.max(0, actualReductionPct * 100);
    const remainingGapNum = Math.max(0, 90 - currentReductionPctNum);
    const gap = actualEmissionNow - targetEmissionNow;
    const isAhead = gap <= 0;

    const regPoints = history
      .map((row: any) => ({ year: row.year, emission: sumScopes(row) }))
      .filter((p: any) => Number.isFinite(p.year) && p.emission > 0);

    let regressionValid = false;
    let alpha = 0;
    let beta = betaPrior;
    let sigma = 0;
    let seBeta = 0;
    let tMean = currentYear;
    let yMean = Math.log(Math.max(actualEmissionNow, 1));
    let n = regPoints.length;
    let stt = 0;

    if (n >= 2) {
      regressionValid = true;
      const years = regPoints.map((p: any) => p.year);
      const logY = regPoints.map((p: any) => Math.log(p.emission));

      tMean = years.reduce((a: number, b: number) => a + b, 0) / n;
      yMean = logY.reduce((a: number, b: number) => a + b, 0) / n;
      stt = years.reduce((acc: number, year: number) => acc + (year - tMean) ** 2, 0);

      if (stt > 0) {
        const sty = years.reduce((acc: number, year: number, idx: number) => acc + (year - tMean) * (logY[idx] - yMean), 0);
        beta = sty / stt;
        alpha = yMean - beta * tMean;

        if (n > 2) {
          const ssr = years.reduce((acc: number, year: number, idx: number) => {
            const fitted = alpha + beta * year;
            return acc + (logY[idx] - fitted) ** 2;
          }, 0);
          sigma = Math.sqrt(ssr / (n - 2));
          seBeta = Math.sqrt((sigma ** 2) / stt);
        }
      } else {
        regressionValid = false;
      }
    } else if (n === 1) {
      const t0 = regPoints[0].year;
      const e0 = regPoints[0].emission;
      tMean = t0;
      yMean = Math.log(e0);
      beta = betaPrior;
      alpha = Math.log(e0) - beta * t0;
    } else {
      const safeActual = Math.max(actualEmissionNow, 1);
      beta = betaPrior;
      alpha = Math.log(safeActual) - beta * currentYear;
    }

    let betaForecast = beta;
    let alphaForecast = alpha;
    if (regressionValid && beta > 0) {
      const nPrior = 4;
      betaForecast = Math.min((n * beta + nPrior * betaPrior) / (n + nPrior), 0);
      alphaForecast = yMean - betaForecast * tMean;
    }

    const trajectory = [];
    for (let y = baseYear; y <= targetYear; y++) {
      const sbtiVal = Math.max(0, baseEmission * (1 - reductionRate * (y - baseYear)));
      const histRow = history.find((row: any) => row.year === y);
      const actual = histRow ? sumScopes(histRow) : null;
      let forecast: number | null = null;

      if (y < latestDataYear && actual != null) {
        forecast = null;
      } else if (y === latestDataYear && actual != null) {
        forecast = Math.max(0, actual);
      } else {
        forecast = Math.max(0, Math.exp(alphaForecast + betaForecast * y));
      }

      trajectory.push({
        year: y.toString(),
        actual: actual != null ? Math.round(actual) : null,
        forecast: forecast != null ? Math.round(forecast) : null,
        sbti: Math.round(sbtiVal),
      });
    }

    const sbtiTarget2030 = Math.max(0, baseEmission * (1 - reductionRate * (targetYear - baseYear)));
    const logE2030Mean = alpha + beta * targetYear;

    let predSigma = 0;
    if (n >= 2 && stt > 0) {
      predSigma = sigma * Math.sqrt(1 + 1 / n + ((targetYear - tMean) ** 2) / stt);
    }

    const simulations = 10000;
    let success = 0;
    if (predSigma > 0) {
      for (let i = 0; i < simulations; i++) {
        const u = Math.max(Math.random(), Number.EPSILON);
        const v = Math.max(Math.random(), Number.EPSILON);
        const z = Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
        const sample = Math.exp(logE2030Mean + predSigma * z);
        if (sample <= sbtiTarget2030) success += 1;
      }
    } else {
      success = Math.exp(logE2030Mean) <= sbtiTarget2030 ? simulations : 0;
    }

    const achievementProbability = Math.round((success / simulations) * 100);
    const annualRateNum = (Math.exp(beta) - 1) * 100;
    const speedGapNum = annualRateNum - (-4.2);
    const requiredAcceleration = Math.max(0, speedGapNum);

    return {
      baseYear,
      currentYear,
      latestDataYear,
      hasScope3: activeScopes.s3,
      baseEmission: Math.round(Math.max(0, baseEmission)),
      targetEmissionNow: Math.round(Math.max(0, targetEmissionNow)),
      actualEmissionNow: Math.round(Math.max(0, actualEmissionNow)),
      gap: Math.round(gap),
      isAhead,
      trajectory,
      regressionValid,
      achievementProbability,
      annualRate: annualRateNum.toFixed(1),
      speedGap: speedGapNum.toFixed(1),
      seBeta: (Math.abs(Math.exp(seBeta) - 1) * 100).toFixed(2),
      actualReductionPct: (actualReductionPct * 100).toFixed(1),
      targetReductionPct: (targetReductionPct * 100).toFixed(1),
      currentReductionPct: currentReductionPctNum.toFixed(1),
      remainingGap: remainingGapNum.toFixed(1),
      requiredAcceleration: requiredAcceleration.toFixed(1),
    };
  }, [selectedComp]); // Remove activeScopes from dependency array for fixed KPIs

  // 새롭게 분리한 추이 그래프용 데이터 (필터에 반응함)
  const trajectoryData = useMemo(() => {
    const baseYear = 2021;
    const targetYear = 2030;
    const reductionRate = 0.042;
    const betaPrior = Math.log(1 - reductionRate);
    const history = Array.isArray((selectedComp as any).history) ? (selectedComp as any).history : [];

    // 필터 연동
    const sumScopes = (row: any) => {
      let sum = 0;
      if (activeScopes.s1) sum += row?.s1 || 0;
      if (activeScopes.s2) sum += row?.s2 || 0;
      if (activeScopes.s3) sum += row?.s3 || 0;
      return sum;
    };

    const actualEmissionNow = sumScopes(selectedComp);
    const currentYear = new Date().getFullYear();
    const latestDataYear = history.length > 0 ? Math.max(...history.map((h: any) => h.year)) : currentYear;

    let baseEmission = 0;
    const baseYearData = history.find((h: any) => h.year === baseYear);
    if (baseYearData) {
      baseEmission = sumScopes(baseYearData);
    } else if (history.length > 0) {
      const oldestData = history.reduce((oldest: any, row: any) => (!oldest || row.year < oldest.year ? row : oldest), null);
      baseEmission = sumScopes(oldestData);
    } else {
      baseEmission = actualEmissionNow;
    }
    if (baseEmission <= 0) {
      baseEmission = actualEmissionNow;
    }

    const regPoints = history
      .map((row: any) => ({ year: row.year, emission: sumScopes(row) }))
      .filter((p: any) => Number.isFinite(p.year) && p.emission > 0);

    let regressionValid = false;
    let alpha = 0;
    let beta = betaPrior;
    let sigma = 0;
    let seBeta = 0;
    let tMean = currentYear;
    let yMean = Math.log(Math.max(actualEmissionNow, 1));
    let n = regPoints.length;
    let stt = 0;

    if (n >= 2) {
      regressionValid = true;
      const years = regPoints.map((p: any) => p.year);
      const logY = regPoints.map((p: any) => Math.log(p.emission));

      tMean = years.reduce((a: number, b: number) => a + b, 0) / n;
      yMean = logY.reduce((a: number, b: number) => a + b, 0) / n;
      stt = years.reduce((acc: number, year: number) => acc + (year - tMean) ** 2, 0);

      if (stt > 0) {
        const sty = years.reduce((acc: number, year: number, idx: number) => acc + (year - tMean) * (logY[idx] - yMean), 0);
        beta = sty / stt;
        alpha = yMean - beta * tMean;

        if (n > 2) {
          const ssr = years.reduce((acc: number, year: number, idx: number) => {
            const fitted = alpha + beta * year;
            return acc + (logY[idx] - fitted) ** 2;
          }, 0);
          sigma = Math.sqrt(ssr / (n - 2));
          seBeta = Math.sqrt((sigma ** 2) / stt);
        }
      } else {
        regressionValid = false;
      }
    } else if (n === 1) {
      const t0 = regPoints[0].year;
      const e0 = regPoints[0].emission;
      tMean = t0;
      yMean = Math.log(e0);
      beta = betaPrior;
      alpha = Math.log(e0) - beta * t0;
    } else {
      const safeActual = Math.max(actualEmissionNow, 1);
      beta = betaPrior;
      alpha = Math.log(safeActual) - beta * currentYear;
    }

    let betaForecast = beta;
    let alphaForecast = alpha;
    if (regressionValid && beta > 0) {
      const nPrior = 4;
      betaForecast = Math.min((n * beta + nPrior * betaPrior) / (n + nPrior), 0);
      alphaForecast = yMean - betaForecast * tMean;
    }

    const trajectory = [];
    for (let y = baseYear; y <= targetYear; y++) {
      const sbtiVal = Math.max(0, baseEmission * (1 - reductionRate * (y - baseYear)));
      const histRow = history.find((row: any) => row.year === y);
      const actual = histRow ? sumScopes(histRow) : null;
      let forecast: number | null = null;

      if (y < latestDataYear && actual != null) {
        forecast = null;
      } else if (y === latestDataYear && actual != null) {
        forecast = Math.max(0, actual);
      } else {
        forecast = Math.max(0, Math.exp(alphaForecast + betaForecast * y));
      }

      trajectory.push({
        year: y.toString(),
        actual: actual != null ? Math.round(actual) : null,
        forecast: forecast != null ? Math.round(forecast) : null,
        sbti: Math.round(sbtiVal),
      });
    }

    return trajectory;
  }, [selectedComp, activeScopes]);

  const handleChartClick = (data: any) => {

    if (data && data.activePayload && data.activePayload[0]) {

      const point = data.activePayload[0].payload;

      const priceKey = selectedMarket === 'K-ETS' ? 'krPrice' : 'euPrice';

      let price = point[priceKey];

      const totalPct = tranches.reduce((sum, t) => sum + t.percentage, 0);

      if (totalPct >= 100) return;

      setTranches([...tranches, { id: Date.now(), market: selectedMarket, price, month: point.date.slice(2, 7).replace('-', '.'), isFuture: false, percentage: Math.min(10, 100 - totalPct) }]);

    }

  };

  const generateAIPlan = () => {

    setIsChatOpen(true);

    setChatMessages((prev: ChatMessage[]) => [...prev, createMessage('user', 'Market is volatile. Recommend a staged buying plan.')]);

    setTimeout(() => {

      const market = MARKET_DATA[selectedMarket];

      const isHighV = market.volatility === 'High';

      const basePrice = selectedMarket === 'EU-ETS' ? latestEutsData.price : market.price;

      const newTranches: Tranche[] = [

        { id: Date.now(), market: selectedMarket, price: Math.round(basePrice * 0.98), month: '26.02', isFuture: true, percentage: isHighV ? 20 : 40 },

        { id: Date.now() + 1, market: selectedMarket, price: Math.round(basePrice * 0.95), month: '26.05', isFuture: true, percentage: isHighV ? 20 : 30 },

        { id: Date.now() + 2, market: selectedMarket, price: Math.round(basePrice * 1.02), month: '26.09', isFuture: true, percentage: isHighV ? 20 : 30 },

      ];

      setTranches(newTranches);

      const strategyText = isHighV
        ? `Current ${market.name} volatility is high. A staged buying plan over 3-4 tranches reduces risk.`
        : `Current ${market.name} volatility is moderate. Focus on key levels with a lighter staged plan.`;

      setChatMessages((prev: ChatMessage[]) => [...prev, createMessage('assistant', `${strategyText}

Recommended staged plan
- 26.02 (40%): slight pullback zone
- 26.05 (30%): additional correction zone
- 26.09 (30%): trend confirmation entry`)]);

    }, 1500);

  };

  const appendToMessage = (id: string, text: string) => {

    if (!text) return;

    setChatMessages((prev: ChatMessage[]) => prev.map(msg => msg.id === id ? { ...msg, text: msg.text + text } : msg));

  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const userText = inputMessage.trim();
    setChatMessages((prev: ChatMessage[]) => [...prev, createMessage('user', userText)]);
    setInputMessage('');

    // 1. 통신 시작 전, AI의 답변이 들어갈 '빈 칸'을 먼저 화면에 만들어 줍니다.
    const assistantId = generateMessageId();
    setChatMessages((prev: ChatMessage[]) => [
      ...prev,
      { id: assistantId, role: 'assistant', text: '' },
    ]);

    try {
      const historyPayload = chatMessages.slice(-8).map((msg) => ({
        role: msg.role,
        text: msg.text,
      }));
      const selectedYear =
        reportScope === "latest" ? selectedConfig?.latestReportYear ?? null : null;
      const activeCompany =
        companies.find((c) => c.id === selectedCompId) ||
        companies[0] ||
        selectedCompany;

      await AiService.chatStream(
        {
          message: userText,
          history: historyPayload,
          companyName: activeCompany?.name,
          companyKey: activeCompany?.dartCode,
          reportScope,
          reportYear: selectedYear,
        },
        (chunk) => {
          setChatMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantId ? { ...msg, text: msg.text + chunk } : msg
            )
          );
        });
    } catch (error) {
      console.error('Chat API Error:', error);
      setChatMessages((prev: ChatMessage[]) => prev.map(msg =>
        msg.id === assistantId ? { ...msg, text: '죄송합니다. 서버와 연결할 수 없습니다. 백엔드가 실행 중인지 확인해주세요.' } : msg
      ));
    }
  };

  // Early return for views ensuring selectedCompany is available
  if (view === 'login') return <Login onLogin={(companyName) => {

    navigateTo('welcome');

  }} onSignup={() => navigateTo('signup')} />;

  if (view === 'signup') return <Signup onBack={() => navigateTo('login')} onComplete={(companyName) => {

    navigateTo('welcome');

  }} />;

  if (view === 'welcome') return <WelcomePage onContinue={() => navigateTo('dashboard')} companyName={selectedCompany?.name || 'My Company'} />;


  // 🌟 여기서부터는 로그인 이후 화면! Header를 절대 사라지지 않는 "뼈대"로 고정합니다.
  return (

    <div className="min-h-screen bg-slate-50 flex flex-col font-display relative overflow-hidden">

      {/* Background Layer: Ambient Warmth & Daylight Cycle */}

      <div className="fixed inset-0 pointer-events-none z-0">

        <div className="ambient-warmth opacity-60"></div>

        <div className="absolute inset-0 bg-sunrise-glow opacity-0 pointer-events-none"></div>

      </div>

      {/* 🌟 Header는 맨 위에 고정 */}
      <Header

        user={userProfile ? { nickname: userProfile.nickname, email: userProfile.email } : undefined}

        activeTab={activeTab}
        // 탭 이동 시에도 히스토리에 기록되게 변경
        setActiveTab={(tab: TabType) => navigateTo('dashboard', tab)}
        tabs={tabs}

        selectedCompany={companies.find(c => c.id === selectedCompId) || companies[0] || EMPTY_COMPANY}

        setSelectedCompanyId={setSelectedCompId}

        companies={companies}

        // 로고나 프로필 클릭 시 navigateTo 사용
        onLogoClick={() => navigateTo('dashboard', 'dashboard')} // Header 컴포넌트에 이 props를 추가해야 합니다!
        onProfileClick={() => navigateTo('profile')}

        onLogout={() => {

          removeToken();

          navigateTo('login');

          setUserProfile(null);

        }}

      />

      <main className="flex-1 p-6 lg:p-10 max-w-7xl mx-auto w-full space-y-8 animate-in fade-in duration-500">

        {/* 🌟 view 상태에 따라 알맹이(Main)만 쏙쏙 갈아끼웁니다. Header는 안전합니다! */}
        {view === 'profile' && (
          <Profile
            onBack={() => navigateTo('dashboard')}
            onProfileUpdated={setUserProfile}
            onNavigate={(next) => {
              if (next === 'profile') {
                navigateTo('profile');
              } else {
                navigateTo('dashboard', next as any);
              }
            }}
          />
        )}
        {view === 'data-input' && <DataInput onBack={() => navigateTo('dashboard')} />}
        {view === 'reports' && <Reports onBack={() => navigateTo('dashboard')} />}
        {view === 'analytics' && <Analytics onBack={() => navigateTo('dashboard')} />}

        {/* 대시보드 화면일 때만 기존 탭들(DashboardTab, CompareTab 등)을 보여줌 */}
        {view === 'dashboard' && (
          <>
            {companies.length === 0 && !isLoading ? (
              <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl shadow-sm border border-slate-100">
                <p className="text-xl font-medium text-slate-800 mb-2">데이터가 없습니다</p>
                <p className="text-slate-500">PDF 문서를 추출하여 데이터를 추가해주세요.</p>
              </div>
            ) : (
              <>
                {activeTab === 'dashboard' && (
                  <DashboardTab
                    selectedComp={selectedComp}
                    costEU_KRW={costEU_KRW}
                    ytdAnalysis={ytdAnalysis}
                    intensityType={intensityType}
                    sbtiAnalysis={sbtiAnalysis}
                    trajectoryData={trajectoryData}
                    activeScopes={activeScopes}
                    setActiveScopes={setActiveScopes}
                    compareData={{
                      rank: chartData.findIndex(c => c.id === selectedCompId) + 1,
                      totalCompanies: chartData.length,
                      intensityValue: chartData.find(c => c.id === selectedCompId)?.intensityValue || 0
                    }}
                    simulatorData={{
                      ketsPrice: latestKetsData.price,
                      ketsChange: latestKetsData.change
                    }}
                    onNavigateToSimulator={() => navigateTo('dashboard', 'simulator')}
                    onNavigateToTab={(tabId) => navigateTo('dashboard', tabId as TabType)}
                  />
                )}

                {activeTab === 'compare' && (
                  <CompareTab
                    intensityType={intensityType}
                    setIntensityType={setIntensityType}
                    chartData={chartData}
                    selectedCompId={selectedCompId}
                    setSelectedCompId={setSelectedCompId}
                    activeScopes={activeScopes}
                    setActiveScopes={setActiveScopes}
                    topThreshold={topThreshold}
                    medianThreshold={medianThreshold}
                    isInsightOpen={isInsightOpen}
                    setIsInsightOpen={setIsInsightOpen}
                    myCompanyId={selectedCompId}
                    onNavigateToSimulator={() => navigateTo('dashboard', 'simulator')}
                  />
                )}

                {activeTab === 'simulator' && (
                  <SimulatorTab
                    selectedMarket={selectedMarket}
                    setSelectedMarket={setSelectedMarket}
                    timeRange={timeRange}
                    setTimeRange={setTimeRange}
                    trendData={trendData}
                    fullHistoryData={fullHistoryData}
                    handleChartClick={handleChartClick}
                    priceScenario={priceScenario}
                    setPriceScenario={setPriceScenario}
                    customPrice={customPrice}
                    setCustomPrice={setCustomPrice}
                    allocationChange={allocationChange}
                    setAllocationChange={setAllocationChange}
                    emissionChange={emissionChange}
                    setEmissionChange={setEmissionChange}
                    auctionEnabled={auctionEnabled}
                    setAuctionEnabled={setAuctionEnabled}
                    auctionTargetPct={auctionTargetPct}
                    setAuctionTargetPct={setAuctionTargetPct}
                    simResult={simResult}
                    currentETSPrice={currentETSPrice}
                    baseAllocation={(selectedConfig.allowance ?? 0) > 0 ? (selectedConfig.allowance as number) : selectedConfig.baseEmissions * 0.9}
                    overseasBaseEmissions={Math.max(
                      0,
                      (selectedConfig.s1Overseas ?? selectedConfig.s1 ?? 0) +
                      (selectedConfig.s2Overseas ?? selectedConfig.s2 ?? 0)
                    )}
                    tranches={tranches}
                    setTranches={setTranches}
                    simBudget={simBudget}
                    setSimBudget={setSimBudget}
                    liveKetsPrice={latestKetsData.price}
                    liveEutsPrice={latestEutsData.price}
                    eurKrwRate={eurKrwRate}
                    auctionSavingsRate={auctionSavingsRate}
                  />
                )}

                {activeTab === 'target' && (
                  <TargetTab sbtiAnalysis={sbtiAnalysis} />
                )}

              </>
            )}
          </>
        )}
      </main>

      <ChatBot
        isChatOpen={isChatOpen}
        setIsChatOpen={setIsChatOpen}
        chatMessages={chatMessages}
        inputMessage={inputMessage}
        setInputMessage={setInputMessage}
        handleSendMessage={handleSendMessage}
        chatEndRef={chatEndRef}
      />
    </div>
  );
};

export default App;
