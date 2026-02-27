import React, { useState, useEffect } from 'react';
import {
    BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, Label, ResponsiveContainer
} from 'recharts';
import {
    Star, TrendingUp, TrendingDown, Lightbulb, ArrowRight, ChevronUp, ChevronDown
} from 'lucide-react';
import { cn } from '../../components/ui/utils';
import { CustomTooltip } from '../../components/ui/CustomTooltip';
import type { Competitor, IntensityType } from '../../types';
import { CompareHeader } from './components/CompareHeader';

interface CompareTabProps {
    intensityType: IntensityType;
    setIntensityType: (type: IntensityType) => void;
    chartData: any[]; // sorted competitors
    selectedCompId: number;
    setSelectedCompId: (id: number) => void;
    activeScopes: { s1: boolean, s2: boolean, s3: boolean };
    setActiveScopes: React.Dispatch<React.SetStateAction<{ s1: boolean, s2: boolean, s3: boolean }>>;
    topThreshold: number;
    medianThreshold: number;
    isInsightOpen: boolean;
    setIsInsightOpen: (open: boolean) => void;
    myCompanyId?: number; // [추가] 자사 회사 ID (첫 번째 회사)
    onNavigateToSimulator?: () => void;
}

export const CompareTab: React.FC<CompareTabProps> = ({
    intensityType,
    setIntensityType,
    chartData,
    selectedCompId,
    setSelectedCompId,
    activeScopes,
    setActiveScopes,
    topThreshold,
    medianThreshold,
    isInsightOpen,
    setIsInsightOpen,
    myCompanyId,
    onNavigateToSimulator,
}) => {
    // 자사 ID가 없으면 첫 번째 회사를 자사로 취급
    const actualMyCompanyId = myCompanyId ?? (chartData.length > 0 ? chartData[0]?.id : -1);

    // [추가] 헤더에서 회사를 변경하면 내부 선택도 업데이트
    const [internalSelectedCompId, setInternalSelectedCompId] = useState(actualMyCompanyId);

    // AI 인사이트 상태
    const [insightText, setInsightText] = useState<string>('');
    const [isInsightLoading, setIsInsightLoading] = useState<boolean>(false);
    const [isInsightError, setIsInsightError] = useState<boolean>(false);
    useEffect(() => {
        setInternalSelectedCompId(actualMyCompanyId);
    }, [actualMyCompanyId]);

    // 인사이트 데이터 로딩
    useEffect(() => {
        if (!isInsightOpen || chartData.length === 0) return;

        const fetchInsight = async () => {
            setIsInsightLoading(true);
            setIsInsightError(false);
            try {
                const myComp = chartData.find(c => c.id === internalSelectedCompId) || chartData[0];
                const bestComp = chartData[0]; // sorted ascending (lowest is best)

                const reqData = {
                    my_company: myComp.name,
                    intensity_type: intensityType,
                    my_intensity: myComp.intensityValue,
                    median_intensity: medianThreshold,
                    top10_intensity: topThreshold,
                    best_company: bestComp.name,
                    is_better_than_median: myComp.intensityValue <= medianThreshold
                };

                const res = await fetch(`http://localhost:8000/api/v1/dashboard/compare/insight`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(reqData)
                });

                if (res.ok) {
                    const data = await res.json();
                    setInsightText(data.insight);
                    if (data.insight.includes("현재 일부 오류가 있어")) {
                        setIsInsightError(true);
                    }
                } else {
                    console.error('Failed to fetch insight');
                    setIsInsightError(true);
                }
            } catch (err) {
                console.error('Error fetching insight:', err);
                setIsInsightError(true);
                setInsightText("현재 일부 오류가 있어 인사이트를 출력하지 못했습니다.");
            } finally {
                setIsInsightLoading(false);
            }
        };

        fetchInsight();
    }, [isInsightOpen, internalSelectedCompId, intensityType, chartData, medianThreshold, topThreshold]);


    return (
        <div className="space-y-6">
            <CompareHeader />

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8">
                {/* LEFT PANEL */}
                <div className="lg:col-span-4 flex flex-col gap-6">
                    {/* Filter */}
                    <div className="bg-white p-1 rounded-xl border border-slate-200 shadow-sm">
                        <div className="grid grid-cols-2 gap-1 h-10">
                            <button
                                onClick={() => setIntensityType('revenue')}
                                className={cn("relative flex items-center justify-center rounded-lg text-sm font-medium transition-all", intensityType === 'revenue' ? "bg-[#10b77f]/10 text-[#10b77f] ring-1 ring-[#10b77f]" : "text-slate-500 hover:bg-slate-50")}
                            >
                                탄소 집약도 (Carbon)
                            </button>
                            <button
                                onClick={() => setIntensityType('energy')}
                                className={cn("relative flex items-center justify-center rounded-lg text-sm font-medium transition-all", intensityType === 'energy' ? "bg-[#10b77f]/10 text-[#10b77f] ring-1 ring-[#10b77f]" : "text-slate-500 hover:bg-slate-50")}
                            >
                                에너지 집약도 (Energy)
                            </button>
                        </div>
                    </div>

                    {/* Rankings */}
                    <div className="flex flex-col gap-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-lg font-bold text-slate-900">경쟁사 순위</h3>
                        </div>
                        <p className="text-sm text-slate-500 leading-snug">
                            {intensityType === 'revenue' ? '탄소 집약도 (tCO2e / 매출 1억원)' : '에너지 집약도 (TJ / 매출 1억원)'}. 낮을수록 우수합니다.
                        </p>

                        <div className="flex flex-col gap-3">
                            {chartData.map((comp, idx) => {
                                const isMe = comp.id === actualMyCompanyId;
                                const isSelected = internalSelectedCompId === comp.id;
                                return (
                                    <div
                                        key={comp.id}
                                        onClick={() => setInternalSelectedCompId(comp.id)}
                                        className={cn(
                                            "group flex items-center gap-4 p-4 rounded-xl border transition-all cursor-pointer relative overflow-hidden",
                                            isSelected ? "ring-2 ring-offset-2 ring-[#10b77f]/50" : "hover:shadow-md",
                                            isMe
                                                ? (isSelected ? "border-[#10b77f] bg-[#10b77f]/10" : "border-[#10b77f]/50 bg-[#10b77f]/5")
                                                : (isSelected ? "border-slate-400 bg-slate-50" : "border-slate-200 bg-white")
                                        )}
                                    >
                                        <div className={cn("flex items-center justify-center size-8 rounded-full font-bold text-sm transition-colors",
                                            isMe ? "bg-[#10b77f] text-white shadow-sm" : (isSelected ? "bg-slate-800 text-white" : "bg-slate-100 text-slate-600")
                                        )}>
                                            {isMe ? <Star size={14} fill="white" /> : idx + 1}
                                        </div>
                                        <div className="flex-1">
                                            <h4 className="font-bold text-slate-900 flex items-center gap-2">
                                                {comp.name}
                                                {isMe && <span className="text-[10px] text-[#10b77f] bg-[#10b77f]/10 px-1.5 py-0.5 rounded font-bold">Me</span>}
                                            </h4>
                                            <p className={cn("text-xs", isMe ? "text-[#10b77f] font-medium" : "text-slate-400")}>
                                                {isMe ? "현재 성과" : "글로벌 피어"}
                                            </p>
                                        </div>
                                        <div className="text-right">
                                            <span className={cn("block text-lg font-bold", isMe ? "text-[#10b77f]" : "text-slate-900")}>
                                                {comp.intensityValue?.toFixed(2)}
                                            </span>
                                            <span className="text-xs text-slate-500">
                                                {intensityType === 'revenue' ? 'tCO2e' : 'TJ'}
                                            </span>
                                        </div>
                                        {isSelected && <div className="absolute right-0 top-0 p-1.5"><div className="w-2 h-2 rounded-full bg-[#10b77f]"></div></div>}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>

                {/* RIGHT PANEL: Chart */}
                <div className="lg:col-span-8 flex flex-col h-full min-h-[500px]">
                    <div className="flex-1 bg-white rounded-xl border border-slate-200 p-6 lg:p-8 flex flex-col relative shadow-sm">
                        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                            <div>
                                <h3 className="text-lg font-bold text-slate-900">
                                    {intensityType === 'revenue' ? '탄소 집약도 비교 (Carbon Intensity)' : '에너지 집약도 비교 (Energy Intensity)'}
                                </h3>
                                <div className="flex items-center gap-4 mt-2">
                                    <p className="text-sm text-slate-500">
                                        {intensityType === 'revenue' ? '매출액 대비 탄소 배출량' : '매출액 대비 에너지 사용량'}
                                    </p>
                                    {intensityType === 'revenue' && (
                                        <>
                                            <div className="h-4 w-px bg-slate-200"></div>
                                            <div className="flex gap-1">
                                                {(['s1', 's2'] as const).map(scope => (
                                                    <button
                                                        key={scope}
                                                        onClick={() => setActiveScopes(prev => ({ ...prev, [scope]: !prev[scope] }))}
                                                        className={cn(
                                                            "w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold transition-all border",
                                                            activeScopes[scope]
                                                                ? "bg-[#10b77f]/10 text-[#10b77f] border-[#10b77f]/30"
                                                                : "bg-slate-50 text-slate-400 border-slate-200 hover:bg-slate-100"
                                                        )}
                                                    >
                                                        {scope.replace('s', 'S')}
                                                    </button>
                                                ))}
                                            </div>
                                        </>
                                    )}
                                </div>
                            </div>
                            {/* Legend */}
                            <div className="flex gap-4 text-xs font-medium">
                                <div className="flex items-center gap-2"><div className="w-3 h-3 bg-[#10b77f] rounded-sm"></div>자사 (Our Co)</div>
                                <div className="flex items-center gap-2"><div className="w-3 h-3 bg-slate-800 rounded-sm"></div>선택됨</div>
                                <div className="flex items-center gap-2"><div className="w-3 h-3 bg-slate-300 rounded-sm"></div>기타</div>
                            </div>
                        </div>
                        <div className="flex flex-wrap gap-4 mb-3 text-xs">
                            <div
                                className="inline-flex items-center gap-2 text-[#10b77f] cursor-help"
                                title={`상위 10% 기준선: ${topThreshold.toFixed(2)} (낮을수록 우수)`}
                            >
                                <svg width="18" height="4"><line x1="0" y1="2" x2="18" y2="2" stroke="#10b77f" strokeWidth="2" strokeDasharray="3 3" /></svg>
                                상위 10% 기준선 ({topThreshold.toFixed(2)})
                            </div>
                            <div
                                className="inline-flex items-center gap-2 text-slate-500 cursor-help"
                                title={`중앙값 기준선: ${medianThreshold.toFixed(2)} (업계 중간 수준)`}
                            >
                                <svg width="18" height="4"><line x1="0" y1="2" x2="18" y2="2" stroke="#94a3b8" strokeWidth="2" strokeDasharray="5 5" /></svg>
                                중앙값 기준선 ({medianThreshold.toFixed(2)})
                            </div>
                        </div>

                        {/* Recharts Implementation */}
                        <div className="flex-1 w-full min-h-[350px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={chartData} margin={{ top: 20, right: 0, left: -20, bottom: 0 }} barSize={60}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12, fontWeight: 600 }} dy={10} />
                                    <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'transparent' }} />
                                    <ReferenceLine y={topThreshold} stroke="#10b77f" strokeDasharray="3 3">
                                        <Label value={`상위 10% (${topThreshold})`} position="right" fill="#10b77f" fontSize={11} fontWeight={700} />
                                    </ReferenceLine>
                                    <ReferenceLine y={medianThreshold} stroke="#94a3b8" strokeDasharray="5 5">
                                        <Label value={`중앙값 (${medianThreshold})`} position="right" fill="#94a3b8" fontSize={11} fontWeight={700} />
                                    </ReferenceLine>
                                    <Bar dataKey="intensityValue" radius={[8, 8, 0, 0]}>
                                        {chartData.map((entry, index) => {
                                            const isMe = entry.id === actualMyCompanyId;
                                            const isSelected = entry.id === internalSelectedCompId;
                                            let fillColor = '#cbd5e1'; // Default Gray

                                            if (isMe) {
                                                fillColor = isSelected ? '#059669' : '#10b77f'; // Darker green if selected
                                            } else if (isSelected) {
                                                fillColor = '#1e293b'; // Dark Slate for selected competitor
                                            }

                                            return <Cell key={`cell-${index}`} fill={fillColor} />;
                                        })}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>
            </div>

            {/* Strategic Insight Footer */}
            <div className="w-full transition-all duration-300">
                {isInsightOpen ? (
                    <div className="bg-[#111814] text-white rounded-xl p-6 lg:p-8 flex flex-col md:flex-row gap-6 md:items-start shadow-xl relative overflow-hidden">
                        <div className="absolute right-0 top-0 w-64 h-full opacity-10 pointer-events-none bg-gradient-to-l from-[#10b77f] to-transparent"></div>

                        <div className="flex-shrink-0 bg-white/10 p-3 rounded-lg text-[#10b77f]">
                            <Lightbulb size={24} />
                        </div>

                        <div className="flex-1 flex flex-col gap-2 relative z-10">
                            {/* Title & Content */}
                            <h3 className="text-xl font-bold tracking-tight flex items-center gap-2">
                                전략적 인사이트: 효율성 격차 (Efficiency Gap)
                                {!isInsightError && insightText && !isInsightLoading && (
                                    <span className="text-[10px] font-bold bg-[#10b77f]/20 text-[#10b77f] px-2 py-0.5 rounded-full border border-[#10b77f]/30">AI 분석됨</span>
                                )}
                            </h3>
                            <div className="text-slate-300 leading-relaxed max-w-3xl text-sm min-h-[4rem]">
                                {isInsightLoading ? (
                                    <div className="flex items-center gap-2 animate-pulse text-[#10b77f]">
                                        <div className="w-4 h-4 rounded-full border-2 border-[#10b77f] border-t-transparent animate-spin"></div>
                                        <span>AI가 다각도 데이터를 분석하여 전략을 도출하고 있습니다...</span>
                                    </div>
                                ) : (
                                    <p dangerouslySetInnerHTML={{ __html: insightText || "인사이트 데이터를 불러올 수 없습니다." }}></p>
                                )}
                            </div>
                        </div>

                        <div className="flex flex-col justify-center min-w-[140px] gap-2 relative z-10">
                            <button
                                onClick={onNavigateToSimulator}
                                className="bg-[#10b77f] hover:bg-[#0e9f6e] text-white font-bold py-2.5 px-4 rounded-lg transition-colors flex items-center justify-center gap-2 text-sm shadow-lg shadow-[#10b77f]/20">
                                세부 실행 계획
                                <ArrowRight size={16} />
                            </button>
                            <button
                                onClick={() => setIsInsightOpen(false)}
                                className="text-slate-400 hover:text-white text-sm font-medium py-1 px-4 text-center transition-colors flex items-center justify-center gap-1"
                            >
                                접기 <ChevronUp size={14} />
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="flex justify-center">
                        <button
                            onClick={() => setIsInsightOpen(true)}
                            className="bg-[#111814] text-white hover:bg-slate-800 px-6 py-3 rounded-full shadow-lg flex items-center gap-2 text-sm font-bold transition-all hover:scale-105 border border-slate-700"
                        >
                            <Lightbulb size={16} className="text-[#10b77f]" />
                            전략적 인사이트 보기 (Efficiency Gap)
                            <ChevronDown size={16} className="text-slate-400" />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};
