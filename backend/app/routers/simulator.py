from fastapi import APIRouter, Query
from sqlalchemy import text
from ..database import engine
from ..services.market_data import market_service
from datetime import datetime, timedelta
import FinanceDataReader as fdr
import pandas as pd

router = APIRouter(prefix="/api/v1/sim", tags=["simulator"])

# --- [API 1] 대시보드 리스크 시뮬레이션 (1개월, 3개월, 1년, 전체 등) ---
@router.get("/dashboard/trend-combined")
async def get_trend_combined(
    company: str = "현대건설",
    period: str = "1y",  
    start_year: int = Query(2019), 
    end_year: int = Query(2023)
):
    if period in ["1m", "3m", "1y"]:
        end_date = datetime.now()
        days = {"1m": 30, "3m": 90, "1y": 365}.get(period, 365)
        start_date = end_date - timedelta(days=days)
            
        sql = """
            SELECT numeric_value FROM table_cells tc
            JOIN documents d ON tc.doc_id = d.id
            WHERE d.company_name LIKE :company 
              AND (tc.content LIKE '%Scope 1%' OR tc.content LIKE '%Scope 2%')
              AND tc.unit LIKE '%tCO2%'
            ORDER BY d.report_year DESC LIMIT 1
        """
        fixed_emission = 1250000.0
        with engine.connect() as conn:
            try:
                res = conn.execute(text(sql), {"company": f"%{company}%"}).fetchone()
                if res: fixed_emission = float(res[0])
            except:
                pass

        try:
            df_price = fdr.DataReader('069500', start_date, end_date)
        except:
            dates = pd.date_range(start_date, end_date)
            df_price = pd.DataFrame(index=dates, data={'Close': [30000]*len(dates)})

        chart_data = []
        for date, row in df_price.iterrows():
            mock_price = row['Close'] / 3
            chart_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "risk_cost": fixed_emission * mock_price,
                "unit_price": mock_price
            })
        return {"mode": "daily", "period": period, "chart_data": chart_data}

    else:
        s_year = start_year
        e_year = end_year
        curr_price = market_service.get_carbon_price_krx()['price']

        sql = """
            SELECT d.report_year, SUM(tc.numeric_value)
            FROM table_cells tc
            JOIN documents d ON tc.doc_id = d.id
            WHERE d.company_name LIKE :company 
              AND d.report_year BETWEEN :s_year AND :e_year
              AND (tc.content LIKE '%Scope 1%' OR tc.content LIKE '%Scope 2%')
              AND tc.unit LIKE '%tCO2%'
            GROUP BY d.report_year ORDER BY d.report_year ASC
        """
        chart_data = []
        with engine.connect() as conn:
            try:
                rows = conn.execute(text(sql), {"company": f"%{company}%", "s_year": s_year, "e_year": e_year}).fetchall()
                db_map = {row[0]: float(row[1]) for row in rows}
                
                for y in range(s_year, e_year + 1):
                    ems = db_map.get(y, 0)
                    if ems == 0 and period == "all": continue
                    chart_data.append({
                        "date": str(y),
                        "risk_cost": ems * curr_price,
                        "unit_price": curr_price
                    })
            except:
                # 테이블 없을 시 빈 데이터 반환
                pass
        return {"mode": "yearly", "period": period, "chart_data": chart_data}


# --- [API 2] 글로벌 탄소 가격 동향 ---
@router.get("/dashboard/market-trends")
async def get_market_trends(period: str = "1y"):
    """
    [Simulator Tab] 글로벌 탄소 가격 동향 차트 데이터
    """
    try:
        chart_data = await market_service.get_dual_market_history(period)
        return {
            "period": period,
            "chart_data": chart_data
        }
    except Exception as e:
        print(f"Market Trends Error: {e}")
        return {"period": period, "chart_data": [], "error": str(e)}

