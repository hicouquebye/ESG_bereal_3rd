from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from ..database import get_db
from ..models import DashboardEmission, IndustryBenchmark
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["dashboard"]
)

class CompanyResponse(BaseModel):
    id: int
    name: str 
    base_emissions: Optional[float] = None
    
    s1: float
    s2: float
    s3: float
    allowance: Optional[float] = None  # 🌟 DB에 있는 진짜 값을 그대로 가져옵니다!
    revenue: float
    history: List[dict] = []
    
    class Config:
        from_attributes = True

@router.get("/companies", response_model=List[dict])
def get_companies(db: Session = Depends(get_db)):
    # [수정] 모든 연도 데이터 조회하여 history 구성
    emissions = db.query(DashboardEmission).order_by(DashboardEmission.company_id, DashboardEmission.year).all()

    # 회사별 그룹핑
    companies = {}
    for e in emissions:
        if e.company_id not in companies:
            companies[e.company_id] = {
                "id": e.company_id,
                "name": e.company_name,
                "dartCode": None,
                "baseEmissions": 0,
                "investCapex": 0,
                "targetSavings": 0,
                "s1": 0, "s2": 0, "s3": 0,
                "allowance": e.allowance or 0,
                "revenue": 0,
                "production": 0,
                "energy_intensity": 0,
                "carbon_intensity": 0,
                # [추가] DB의 탄소 집약도 값 전달
                "carbon_intensity_scope1": 0,
                "carbon_intensity_scope2": 0,
                "carbon_intensity_scope3": 0,
                "history": []
            }

        # [수정] history에 탄소 집약도 값도 포함
        companies[e.company_id]["history"].append({
            "year": e.year,
            "s1": e.scope1 or 0,
            "s2": e.scope2 or 0,
            "s3": e.scope3 or 0,
            "revenue": e.revenue or 0,
            "carbon_intensity_scope1": e.carbon_intensity_scope1 or 0,
            "carbon_intensity_scope2": e.carbon_intensity_scope2 or 0,
            "carbon_intensity_scope3": e.carbon_intensity_scope3 or 0
        })

        # 최신 데이터 설정 (2024년 우선, 없으면 가장 최신 연도)
        if e.year == 2024:
            companies[e.company_id].update({
                "baseEmissions": e.base_emissions,
                "s1": e.scope1 or 0,
                "s2": e.scope2 or 0,
                "s3": e.scope3 or 0,
                "revenue": e.revenue or 0,
                "energy_intensity": e.energy_intensity or 0,
                "carbon_intensity": e.carbon_intensity or 0,
                # [추가] DB의 탄소 집약도 값
                "carbon_intensity_scope1": e.carbon_intensity_scope1 or 0,
                "carbon_intensity_scope2": e.carbon_intensity_scope2 or 0,
                "carbon_intensity_scope3": e.carbon_intensity_scope3 or 0,
                "allowance": e.allowance or 0
            })
        elif e.year != 2024:
            # 2024년 데이터 없으면 가장 최신 연도로 계속 덮어쓰기 (year 오름차순이므로 마지막이 최신)
            companies[e.company_id].update({
                "baseEmissions": e.base_emissions,
                "s1": e.scope1 or 0,
                "s2": e.scope2 or 0,
                "s3": e.scope3 or 0,
                "revenue": e.revenue or 0,
                "energy_intensity": e.energy_intensity or 0,
                "carbon_intensity": e.carbon_intensity or 0,
                "carbon_intensity_scope1": e.carbon_intensity_scope1 or 0,
                "carbon_intensity_scope2": e.carbon_intensity_scope2 or 0,
                "carbon_intensity_scope3": e.carbon_intensity_scope3 or 0,
                "allowance": e.allowance or 0
            })

    return list(companies.values())

@router.get("/benchmarks")
def get_benchmarks(db: Session = Depends(get_db)):
    """업계 벤치마크 데이터 조회 (최신 연도 기준)"""
    # 가장 최신 연도의 건설업 데이터 조회
    benchmark = db.query(IndustryBenchmark)\
        .filter(IndustryBenchmark.industry == "건설업")\
        .order_by(IndustryBenchmark.year.desc())\
        .first()
    
    if not benchmark:
        return {
            "revenue": {"top10": 0, "median": 0, "avg": 0},
            "energy": {"top10": 0, "median": 0, "avg": 0}
        }
    
    return {
        "revenue": {
            "top10": benchmark.carbon_intensity_top10,
            "median": benchmark.carbon_intensity_median,
            "avg": benchmark.carbon_intensity_avg
        },
        "energy": {
            "top10": benchmark.energy_intensity_top10,
            "median": benchmark.energy_intensity_median,
            "avg": benchmark.energy_intensity_avg
        }
    }

class CompareInsightRequest(BaseModel):
    my_company: str
    intensity_type: str
    my_intensity: float
    median_intensity: float
    top10_intensity: float
    best_company: str
    is_better_than_median: bool

def _percentile(values: List[float], p: float) -> float:
    """Return linear-interpolated percentile (0.0-1.0) for non-empty numeric values."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])

    idx = (len(sorted_vals) - 1) * p
    low = int(idx)
    high = min(low + 1, len(sorted_vals) - 1)
    frac = idx - low
    return float(sorted_vals[low] + (sorted_vals[high] - sorted_vals[low]) * frac)

@router.get("/benchmarks", response_model=Dict[str, Dict[str, float]])
def get_benchmarks(db: Session = Depends(get_db)):
    """
    Compare 탭 기준선(상위 10%, 중앙값) 반환.
    - revenue: 탄소 집약도(기본은 S1+S2 집약도 사용)
    - energy: 에너지 집약도
    """
    emissions = db.query(DashboardEmission).order_by(
        DashboardEmission.company_id, DashboardEmission.year
    ).all()

    if not emissions:
        return {
            "revenue": {"top10": 0.0, "median": 0.0},
            "energy": {"top10": 0.0, "median": 0.0},
        }

    # 회사별 최신 레코드 선정 (2024 우선, 없으면 최신 연도)
    latest_by_company: Dict[int, DashboardEmission] = {}
    for row in emissions:
        existing = latest_by_company.get(row.company_id)
        if existing is None:
            latest_by_company[row.company_id] = row
            continue
        if row.year == 2024 and existing.year != 2024:
            latest_by_company[row.company_id] = row
        elif existing.year != 2024 and row.year >= existing.year:
            latest_by_company[row.company_id] = row

    revenue_values: List[float] = []
    energy_values: List[float] = []
    for row in latest_by_company.values():
        revenue_intensity = (row.carbon_intensity_scope1 or 0.0) + (row.carbon_intensity_scope2 or 0.0)
        energy_intensity = row.energy_intensity or 0.0
        if revenue_intensity > 0:
            revenue_values.append(float(revenue_intensity))
        if energy_intensity > 0:
            energy_values.append(float(energy_intensity))

    return {
        "revenue": {
            "top10": round(_percentile(revenue_values, 0.10), 2),
            "median": round(_percentile(revenue_values, 0.50), 2),
        },
        "energy": {
            "top10": round(_percentile(energy_values, 0.10), 2),
            "median": round(_percentile(energy_values, 0.50), 2),
        },
    }

@router.post("/compare/insight")
async def get_compare_insight(req: CompareInsightRequest):
    try:
        from ..services.ai_service import ai_service
        insight = await ai_service.generate_compare_insight(
            my_company=req.my_company,
            intensity_type=req.intensity_type,
            my_intensity=req.my_intensity,
            median_intensity=req.median_intensity,
            top10_intensity=req.top10_intensity,
            best_company=req.best_company,
            is_better_than_median=req.is_better_than_median
        )
        return {"insight": insight}
    except Exception as e:
        print(f"Error generating insight: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate insight")
