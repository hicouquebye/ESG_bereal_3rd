import random
import sys
import time
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Callable, Generator, List, Optional, Tuple, Union
import openai

from ..config import settings
from ..database import SessionLocal
from ..models import DashboardEmission

# [Ours] PDF 검색 모듈을 동적으로 로딩하는 헬퍼 함수 추가
def _load_pdf_search_helper() -> Optional[Callable]:
    try:
        from search_vector_db import search_vector_db as _search
        return _search
    except ModuleNotFoundError:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        pdf_src = base_dir / "PDF_Extraction" / "src"
        if pdf_src.exists():
            if str(pdf_src) not in sys.path:
                sys.path.append(str(pdf_src))
            try:
                from search_vector_db import search_vector_db as _search
                return _search
            except:
                return None
        return None

search_vector_db = _load_pdf_search_helper()

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    HAS_RAG_LIBS = True
except ImportError:
    HAS_RAG_LIBS = False

class AIService:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY

        self.chroma_client = None
        self.chunk_collection = None
        self.page_collection = None
        self.embedding_model = None
        self.vector_db_path = self._resolve_vector_db_path()
        self.search_top_k = 5
        self.max_history_messages = 8
        self._initialization_lock = asyncio.Lock()
        self._is_initialized = False

    def _resolve_vector_db_path(self) -> Optional[Path]:
        if settings.VECTOR_DB_PATH:
            candidate = Path(settings.VECTOR_DB_PATH).expanduser()
            if candidate.exists(): return candidate
        
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        candidate = base_dir / "PDF_Extraction" / "vector_db"
        return candidate if candidate.exists() else None

    async def initialize(self):
        if self._is_initialized: return
        async with self._initialization_lock:
            if self._is_initialized: return
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self._init_vector_db_sync)
                self._is_initialized = True
            except Exception as e:
                print(f"❌ [RAG Error] {e}")
                self._is_initialized = True

    def _init_vector_db_sync(self):
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
            if not self.vector_db_path: return
            self.chroma_client = chromadb.PersistentClient(path=str(self.vector_db_path))
            try: self.chunk_collection = self.chroma_client.get_collection("esg_chunks")
            except: pass
            model_name = settings.RAG_EMBEDDING_MODEL or "BAAI/bge-m3"
            self.embedding_model = SentenceTransformer(model_name)
        except: pass

    @staticmethod
    def _content_to_text(content: Union[str, List, None]) -> str:
        if content is None: return ""
        if isinstance(content, str): return content
        if isinstance(content, list):
            return "".join([part.get("text", "") if isinstance(part, dict) else getattr(part, "text", "") for part in content])
        return str(content)

    def _fast_path_response(self, message: str) -> Optional[str]:
        normalized = (message or "").strip().lower()
        if normalized in {"안녕", "안녕하세요", "ㅎㅇ", "hi"}: return "안녕하세요. 무엇을 도와드릴까요?"
        return None

    def _should_use_rag(self, message: str) -> bool:
        rag_keywords = ["esg", "보고서", "온실가스", "배출", "탄소", "감축", "scope", "매수", "집약도", "기업", "연도"]
        return any(k in message.lower() for k in rag_keywords)

    def _retrieve_db_data(self, company_name: Optional[str], year: Optional[int]) -> str:
        if not company_name: return ""
        db = SessionLocal()
        try:
            query = db.query(DashboardEmission).filter(DashboardEmission.company_name.like(f"%{company_name}%"))
            if year: query = query.filter(DashboardEmission.year == year)
            record = query.order_by(DashboardEmission.year.desc()).first()
            if not record: return ""
            
            data_str = f"\n[Dashboard DB 데이터 - {record.company_name} {record.year}년]\n"
            data_str += f"- Scope 1 배출량: {record.scope1 or 0:,.2f} tCO2e\n"
            data_str += f"- Scope 2 배출량: {record.scope2 or 0:,.2f} tCO2e\n"
            data_str += f"- Scope 3 배출량: {record.scope3 or 0:,.2f} tCO2e\n"
            data_str += f"- 매출액: {record.revenue or 0:,} 원\n"
            data_str += f"- 탄소 집약도: {record.carbon_intensity or 0:,.4f} tCO2e/억원\n"
            return data_str
        except: return ""
        finally: db.close()

    async def _extract_entities(self, message: str) -> Tuple[Optional[str], Optional[int]]:
        if not settings.OPENAI_API_KEY or len(message) < 2: return None, None
        prompt = f"질문: \"{message}\"\n위 질문에서 기업명과 연도를 추출해 JSON으로 답하세요. 예: {{\"company\": \"삼성전자\", \"year\": 2023}}"
        try:
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model="gpt-4o", messages=[{"role": "user", "content": prompt}],
                temperature=0, max_tokens=50, response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            return data.get("company"), data.get("year")
        except: return None, None

    def _build_messages(self, message: str, context: str, history: List[dict], company_name: Optional[str], report_year: Optional[int]) -> List[dict]:
        system_prompt = (
            "You are an expert ESG consultant. Answer based STRICTLY on the provided [Context].\n"
            "1. If [Dashboard DB 데이터] exists, use those numbers as the primary truth.\n"
            "2. Cite sources naturally (e.g., '시스템 데이터에 따르면...').\n"
            "3. If no data exists, say you don't know. Stay professional and polite in Korean."
        )
        messages = [{"role": "system", "content": system_prompt}]
        for turn in history[-8:]:
            messages.append({"role": "assistant" if turn.get("role") == "assistant" else "user", "content": turn.get("text", "")})
        
        user_content = f"{message}\n\n[Context]\n{context}"
        messages.append({"role": "user", "content": user_content})
        return messages

    async def stream_chat_response(self, message: str, history: List[dict], company_name: Optional[str] = None, company_key: Optional[str] = None, report_year: Optional[int] = None) -> Generator[str, None, None]:
        if not self._is_initialized: await self.initialize()
        
        # 인사말 등은 바로 처리
        fast = self._fast_path_response(message)
        if fast: 
            yield fast
            return

        # 개체명 추출
        ext_company, ext_year = await self._extract_entities(message)
        eff_company = company_name or company_key or ext_company
        eff_year = report_year or ext_year

        context = ""
        source_info = []
        if self._should_use_rag(message):
            db_data = self._retrieve_db_data(eff_company, eff_year)
            # RAG 검색 (검색어와 필터 적용)
            try:
                from search_vector_db import search_vector_db as _search
                results = _search(message, top_k=3, vector_db_path=str(self.vector_db_path), filter_company=eff_company, filter_year=eff_year)
                for item in results or []:
                    context += f"[{item.get('metadata', {}).get('company_name')} {item.get('metadata', {}).get('report_year')}]: {item.get('content')}\n"
            except: pass
            context = db_data + "\n" + context

        messages = self._build_messages(message, context, history, eff_company, eff_year)
        
        try:
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            stream = await client.chat.completions.create(model="gpt-4o", messages=messages, temperature=0.7, stream=True)
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except: yield "답변 생성 중 오류가 발생했습니다."

    async def generate_compare_insight(self, my_company: str, intensity_type: str, my_intensity: float, median_intensity: float, top10_intensity: float, best_company: str, is_better_than_median: bool) -> str:
        """대시보드 경쟁사 비교 탭의 전략적 인사이트 생성 (복구 버전)"""
        if not my_company or my_intensity == 0: return "분석할 기업을 선택해 주세요."
        
        intensity_label = "탄소 집약도" if intensity_type == 'revenue' else "에너지 집약도"
        diff_to_top10 = max(0, my_intensity - top10_intensity)
        pct_to_top10 = (diff_to_top10 / my_intensity * 100) if my_intensity > 0 else 0

        prompt = f"""당신은 날카로운 ESG 전략 컨설턴트입니다. 
다음 데이터를 바탕으로 <strong class="text-white">{my_company}</strong>의 {intensity_label} 전략 인사이트를 2문장으로 작성하세요.
HTML 태그(<strong class="text-white">, <span class="text-[#10b77f] font-bold"> 등)를 반드시 사용하여 핵심을 강조하세요.

[데이터]
- 대상: {my_company}, 지표: {my_intensity:.2f}, 업계평균: {median_intensity:.2f}, 상위10%: {top10_intensity:.2f}
- 상위 10% 진입을 위한 필요 감축률: 약 {pct_to_top10:.1f}%
- 선두 기업: {best_company}

작성 가이드:
1. 수치 중심의 날카로운 분석을 제시할 것.
2. <span class="text-[#10b77f] font-bold"> 태그로 감축 목표나 핵심 수치를 강조할 것.
3. 마크다운(**)은 절대 사용하지 말 것.
"""
        try:
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], temperature=0.7, max_tokens=300)
            return response.choices[0].message.content.strip()
        except: return f"{my_company}은(는) 현재 업계 평균 대비 분석 중입니다."

ai_service = AIService()
