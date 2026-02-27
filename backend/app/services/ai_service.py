import random
import sys
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Callable, Generator, List, Optional, Tuple, Union
import openai

from ..config import settings

# [Ours] PDF 검색 모듈을 동적으로 로딩하는 헬퍼 함수 추가 (경로 문제 해결)
# RAG 라이브러리(chromadb 등)가 없어도 서버가 죽지 않도록 예외 처리
def _load_pdf_search_helper() -> Optional[Callable]:
    """Attempt to import search_vector_db from PDF_Extraction/src."""
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
            except Exception as exc:
                print(f"⚠️ [RAG] search_vector_db import failed: {exc}")
        return None
    except Exception as exc:
        print(f"⚠️ [RAG] search_vector_db import error: {exc}")
        return None


search_vector_db = _load_pdf_search_helper()

# RAG Libraries (Try import)
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
        self.collection = None  # legacy single collection
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
            if candidate.exists():
                return candidate
            print(f"⚠️ [RAG] VECTOR_DB_PATH not found: {candidate}")

        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        candidates = [base_dir / "PDF_Extraction" / "vector_db"]

        parent_dir = base_dir.parent    
        for repo_name in ("esg_pdf_extraction", "ESG_AIagent"):
            candidates.append(parent_dir / repo_name / "vector_db")

        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    async def initialize(self):
        """Asynchronously initialize Vector DB and Embedding Model"""
        if self._is_initialized:
            return

        async with self._initialization_lock:
            if self._is_initialized:
                return

            print("⏳ [RAG] Initializing AI Service (Loading models... this may take time)")
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self._init_vector_db_sync)
                self._is_initialized = True
                print("✅ [RAG] AI Service initialized.")
            except Exception as e:
                print(f"❌ [RAG Error] Failed to initialize Vector DB: {e}")
                self._is_initialized = True # Mark as initialized even if failed to avoid retry loop

    def _init_vector_db_sync(self):
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
        except ImportError:
            print("⚠️ [RAG] Required libraries (chromadb, sentence_transformers) not found. AI features limited.")
            return

        try:
            if settings.CHROMA_HOST:
                port = settings.CHROMA_PORT or 8000
                self.chroma_client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=port)
                print(f"🌐 [RAG] Connected to remote Chroma at {settings.CHROMA_HOST}:{port}")
            else:
                db_path = self.vector_db_path

                if not db_path:
                    print("⚠️ Vector DB 경로를 찾지 못했습니다. PDF Extraction 파이프라인을 먼저 실행해주세요.")
                    return

                self.chroma_client = chromadb.PersistentClient(path=str(db_path))
                print(f"📁 [RAG] Using local Chroma path: {db_path}")

            connected = False
            try:
                self.chunk_collection = self.chroma_client.get_collection("esg_chunks")
                connected = True
                print("✅ [RAG] Connected to collection: esg_chunks")
            except Exception as e:
                print(f"⚠️ [RAG] Collection 'esg_chunks' not found: {e}")

            try:
                self.page_collection = self.chroma_client.get_collection("esg_pages")
                print("✅ [RAG] Connected to collection: esg_pages")
            except Exception as e:
                print(f"⚠️ [RAG] Collection 'esg_pages' not found: {e}")

            if self.chunk_collection is None:
                try:
                    self.collection = self.chroma_client.get_collection("esg_documents")
                    connected = True
                    print("✅ [RAG] Connected to collection: esg_documents (legacy)")
                except Exception as e:
                    print(f"⚠️ [RAG] Collection 'esg_documents' not found: {e}")

            if not connected:
                print("⚠️ [RAG] 사용할 수 있는 컬렉션을 찾지 못했습니다.")
                return

            model_name = settings.RAG_EMBEDDING_MODEL or "BAAI/bge-m3"
            print(f"⏳ [RAG] Loading embedding model: {model_name}")
            try:
                # IMPORTANT: query embedding model must match the index embedding model.
                # Vector DB is built with bge-m3, so we do not fallback to a different model.
                self.embedding_model = SentenceTransformer(model_name)
                print(f"✅ [RAG] Embedding model loaded: {model_name}")
            except Exception as emb_exc:
                self.embedding_model = None
                print(f"❌ [RAG] Embedding model load failed ({model_name}). Semantic search disabled: {emb_exc}")

        except Exception as e:
            print(f"❌ [RAG Error] Failed to initialize Vector DB: {e}")

    @staticmethod
    def _content_to_text(content: Union[str, List, None]) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts: List[str] = []
            for part in content:
                if isinstance(part, dict):
                    texts.append(part.get("text", ""))
                else:
                    text_value = getattr(part, "text", "")
                    texts.append(text_value)
            return "".join(texts)
        return str(content)

    async def generate_strategy(self, company_id: int, market: str, current_price: float):
        """
        탄소 배출권 매수 전략 생성 (Mock Data)
        """
        is_high_volatility = random.choice([True, False])
        
        tranches = []
        months = ["26.02", "26.03", "26.04", "26.05", "26.06", "26.07", "26.08", "26.09"]
        selected_months = random.sample(months, 3)
        selected_months.sort()

        if is_high_volatility:
            strategy_text = f"⚠️ [고변동성 감지] {market} 시장의 변동성이 높습니다. 리스크 분산을 위해 3회에 걸친 분할 매수 전략을 추천합니다."
            percentages = [30, 40, 30]
        else:
            strategy_text = f"✅ [안정적 추세] {market} 시장이 안정적인 흐름을 보이고 있습니다. 저점 확보를 위한 공격적 매수 전략이 유효합니다."
            percentages = [50, 30, 20]

        for i, month in enumerate(selected_months):
            forecast_price = current_price * (1 + random.uniform(-0.05, 0.05))
            tranches.append({
                "id": int(datetime.now().timestamp() * 1000) + i,
                "market": market,
                "price": round(forecast_price, 2) if market == "EU-ETS" else int(forecast_price),
                "month": month,
                "isFuture": True,
                "percentage": percentages[i]
            })

        return {
            "strategy_text": strategy_text,
            "tranches": tranches,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    def _fast_path_response(self, message: str) -> Optional[str]:
        normalized = (message or "").strip().lower()
        if normalized in {"안녕", "안녕하세요", "ㅎㅇ", "hi", "hello", "hey"}:
            return "안녕하세요. 무엇을 도와드릴까요?"
        if "시뮬레이터" in message:
            return "상단의 '시뮬레이터' 탭을 누르시면 탄소 비용 예측 대시보드를 보실 수 있습니다."
        return None

    def _should_use_rag(self, message: str) -> bool:
        text = (message or "").strip().lower()
        if not text:
            return False

        # Smalltalk/짧은 인사에는 RAG를 태우지 않는다.
        smalltalk = {
            "안녕", "안녕하세요", "ㅎㅇ", "hi", "hello", "hey", "thanks", "thank you",
            "고마워", "감사", "뭐해", "반가워"
        }
        if text in smalltalk:
            return False

        # 보고서/ESG/시장 데이터 질문에서만 RAG를 활성화한다.
        rag_keywords = [
            "esg", "지속가능", "보고서", "온실가스", "배출", "탄소", "감축", "scope",
            "ifrs", "esrs", "sbti", "시장", "매수", "kau", "eua", "ets", "벤치마크",
            "지표", "배출량", "집약도", "시뮬레이터", "회사", "기업", "연도",
        ]
        return any(keyword in text for keyword in rag_keywords)


    def _is_last_year_query(self, message: str) -> bool:
        if not message:
            return False
        lower = message.lower()
        korean_keys = ["\uC791\uB144", "\uC9C0\uB09C\uD574", "\uC9C0\uB09C \uD574", "\uC791\uB144\uB3C4"]
        english_keys = ["last year", "previous year"]
        return any(k in message for k in korean_keys) or any(k in lower for k in english_keys)

    def _infer_latest_report_year(self, company_name: Optional[str], company_key: Optional[str]) -> Optional[int]:
        target = company_key or company_name
        if not target:
            return None

        if search_vector_db and self.vector_db_path:
            try:
                results = search_vector_db(
                    "\uC628\uC2E4\uAC00\uC2A4 \uBC30\uCD9C\uB7C9",
                    top_k=self.search_top_k,
                    semantic_top_k=max(self.search_top_k * 5, 40),
                    vector_db_path=str(self.vector_db_path),
                    filter_company=target,
                    verbose=False,
                )
                years = []
                for item in results or []:
                    meta = item.get("metadata", {}) if isinstance(item, dict) else {}
                    year = meta.get("report_year")
                    if year is not None:
                        try:
                            years.append(int(year))
                        except Exception:
                            continue
                if years:
                    return max(years)
            except Exception:
                pass

        collection = self.chunk_collection or self.page_collection or self.collection
        if not collection:
            return None
        years = []
        try:
            offset = 0
            limit = 500
            while True:
                batch = collection.get(include=["metadatas"], limit=limit, offset=offset)
                metas = batch.get("metadatas") or []
                if not metas:
                    break
                for meta in metas:
                    if self._metadata_matches(meta, company_name, company_key, None):
                        year = meta.get("report_year") if meta else None
                        if year is not None:
                            try:
                                years.append(int(year))
                            except Exception:
                                continue
                if len(metas) < limit:
                    break
                offset += len(metas)
        except Exception:
            return None
        return max(years) if years else None

    def _format_context_entry(self, document: str, metadata: dict) -> Tuple[str, Optional[str]]:
        company = metadata.get('company_name', 'Unknown')
        year = metadata.get('report_year', '????')
        page = metadata.get('page_no') or metadata.get('page_number') or metadata.get('page') or '?'
        source_type = metadata.get('source_type', 'page_text')
        title = metadata.get('table_title') or metadata.get('figure_title') or metadata.get('section_title')

        label_map = {
            'table': '표',
            'figure': '그림',
            'page_text': '본문',
            'summary': '요약'
        }
        label = label_map.get(source_type, '본문')

        header = f"[{company} {year} 보고서 p.{page} {label}]"
        if title:
            header += f" {title}"

        snippet = f"{header}: {str(document).strip()}\n\n"
        source_line = f"- {company} {year} Report (p.{page})"
        return snippet, source_line

    def _build_where_filter(
        self,
        company_name: Optional[str],
        company_key: Optional[str],
        report_year: Optional[int],
    ) -> Optional[dict]:
        conditions: List[dict] = []
        company_candidates = self._expand_company_aliases(company_name, company_key)
        if company_candidates:
            if len(company_candidates) == 1:
                conditions.append({"company_name": company_candidates[0]})
            else:
                conditions.append(
                    {"$or": [{"company_name": candidate} for candidate in company_candidates]}
                )
        if report_year is not None:
            conditions.append({"report_year": report_year})
        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def _expand_company_aliases(
        self, company_name: Optional[str], company_key: Optional[str]
    ) -> List[str]:
        alias_map = {
            "현대건설": ["HDEC"],
            "HDEC": ["현대건설"],
            "삼성물산": ["Samsung", "Samsung C&T"],
            "Samsung": ["삼성물산"],
            "Samsung C&T": ["삼성물산"],
        }
        seeds: List[str] = []
        for value in (company_name, company_key):
            if value:
                text = str(value).strip()
                if text:
                    seeds.append(text)

        expanded: List[str] = []
        for seed in seeds:
            if seed not in expanded:
                expanded.append(seed)
            for alias in alias_map.get(seed, []):
                if alias not in expanded:
                    expanded.append(alias)
        return expanded

    @staticmethod
    def _tokenize_query(text: Optional[str]) -> List[str]:
        if not text:
            return []
        tokens = []
        for part in str(text).lower().replace("\n", " ").split(" "):
            token = part.strip(".,!?()[]{}\"':;")
            if len(token) >= 2:
                tokens.append(token)
        return tokens[:15]

    def _score_document_by_query(self, document: str, query_tokens: List[str]) -> int:
        if not query_tokens:
            return 0
        doc_lower = str(document).lower()
        return sum(1 for token in query_tokens if token in doc_lower)

    def _retrieve_context_by_metadata(
        self,
        message: Optional[str],
        company_name: Optional[str],
        company_key: Optional[str],
        report_year: Optional[int],
        limit: int = 5,
    ) -> Tuple[str, List[str]]:
        """
        Embedding query가 실패해도 company/year 메타데이터 기준으로 컨텍스트를 복구한다.
        """
        collections = [c for c in [self.chunk_collection, self.page_collection, self.collection] if c]
        if not collections:
            return "", []

        primary_where = self._build_where_filter(company_name, company_key, report_year)
        year_only_where = {"report_year": report_year} if report_year is not None else None
        company_only_where = self._build_where_filter(company_name, company_key, None)

        where_candidates: List[Optional[dict]] = []
        for where in [primary_where, company_only_where, year_only_where, None]:
            if where not in where_candidates:
                where_candidates.append(where)

        query_tokens = self._tokenize_query(message)

        for where in where_candidates:
            ranked_pairs: List[Tuple[int, str, dict]] = []
            for collection in collections:
                try:
                    kwargs = {
                        "include": ["documents", "metadatas"],
                        "limit": max(limit * 6, 30),
                    }
                    if where is not None:
                        kwargs["where"] = where
                    data = collection.get(**kwargs)
                    docs = data.get("documents") or []
                    metas = data.get("metadatas") or []
                    for doc, meta in zip(docs, metas):
                        if not isinstance(doc, str):
                            continue
                        score = self._score_document_by_query(doc, query_tokens)
                        ranked_pairs.append((score, doc, meta or {}))
                except Exception as exc:
                    print(f"⚠️ [RAG] Metadata fallback query failed: {exc}")

            if not ranked_pairs:
                continue

            ranked_pairs.sort(key=lambda x: x[0], reverse=True)
            # 질의 토큰이 있는데 전부 score 0이면 관련 문맥이 없는 것으로 본다.
            if query_tokens and ranked_pairs[0][0] <= 0:
                continue
            selected = ranked_pairs[:limit]

            context_parts: List[str] = []
            source_info: List[str] = []
            for _, doc, meta in selected:
                snippet, source_line = self._format_context_entry(doc, meta)
                context_parts.append(snippet)
                if source_line and source_line not in source_info:
                    source_info.append(source_line)

            if context_parts:
                return "".join(context_parts), source_info

        return "", []

    def _metadata_matches(
        self,
        metadata: Optional[dict],
        company_name: Optional[str] = None,
        company_key: Optional[str] = None,
        report_year: Optional[int] = None,
    ) -> bool:
        if not company_name and not company_key and report_year is None:
            return True
        if not metadata:
            return False
        meta_name = metadata.get('company_name') or metadata.get('company')
        meta_year = metadata.get('report_year')

        if report_year is not None and str(meta_year) != str(report_year):
            return False

        if not company_name and not company_key:
            return True

        if not meta_name:
            return False
        meta_norm = str(meta_name).strip().lower()

        if company_key:
            key_norm = company_key.strip().lower()
            if key_norm and (key_norm == meta_norm or key_norm in meta_norm or meta_norm in key_norm):
                return True

        if company_name:
            company_norm = company_name.strip().lower()
            if company_norm and (company_norm in meta_norm or meta_norm in company_norm):
                return True

        return False

    def _filter_doc_meta_pairs(
        self,
        pairs: List[Tuple[str, Optional[dict]]],
        company_name: Optional[str],
        company_key: Optional[str],
        report_year: Optional[int],
    ) -> List[Tuple[str, Optional[dict]]]:
        if not company_name and not company_key and report_year is None:
            return pairs
        filtered = [
            (doc, meta)
            for doc, meta in pairs
            if self._metadata_matches(meta, company_name, company_key, report_year)
        ]
        if filtered:
            return filtered
        # fallback to all if no match
        return pairs

    def _retrieve_context(
        self,
        message: str,
        company_name: Optional[str] = None,
        company_key: Optional[str] = None,
        report_year: Optional[int] = None,
    ) -> Tuple[str, List[str]]:
        if search_vector_db and self.vector_db_path:
            context, sources = self._retrieve_via_pdf_extraction(
                message, company_name, company_key, report_year
            )
            if context:
                return context, sources

        context_parts: List[str] = []
        source_info: List[str] = []

        if not self.embedding_model:
            return self._retrieve_context_by_metadata(
                message, company_name, company_key, report_year
            )

        collection = self.chunk_collection or self.page_collection or self.collection
        if not collection:
            # print("⚠️ [RAG] Vector collection이 초기화되지 않았습니다.")
            return "", []

        try:
            print(f"🔎 [RAG] Searching for: {message}")
            query_vec = self.embedding_model.encode([message]).tolist()
            results = collection.query(
                query_embeddings=query_vec,
                n_results=5,
                include=["documents", "metadatas", "distances"]
            )

            if not results or not results.get('documents'):
                print("⚠️ [RAG] No results found.")
                return "", []

            docs = results['documents'][0]
            metas = results['metadatas'][0]
            doc_meta_pairs = self._filter_doc_meta_pairs(
                list(zip(docs, metas)), company_name, company_key, report_year
            )

            if (company_name or company_key) and not doc_meta_pairs:
                return "", []

            for doc, meta in doc_meta_pairs:
                snippet, source_line = self._format_context_entry(doc, meta or {})
                context_parts.append(snippet)
                if source_line not in source_info:
                    source_info.append(source_line)

            print(f"✅ [RAG] Found {len(context_parts)} contexts.")

        except Exception as e:
            print(f"❌ [RAG Search Error] {e}")
            # fallback: dimension mismatch 등 임베딩 검색 실패 시 메타데이터 조회로 복구
            fallback_ctx, fallback_sources = self._retrieve_context_by_metadata(
                message, company_name, company_key, report_year
            )
            if fallback_ctx:
                print("✅ [RAG] Metadata fallback contexts loaded.")
                return fallback_ctx, fallback_sources

        return "".join(context_parts), source_info

    def _retrieve_via_pdf_extraction(
        self,
        message: str,
        company_name: Optional[str] = None,
        company_key: Optional[str] = None,
        report_year: Optional[int] = None,
    ) -> Tuple[str, List[str]]:
        try:
            if not search_vector_db:
                 return "", []

            results = search_vector_db(
                message,
                top_k=self.search_top_k,
                semantic_top_k=max(self.search_top_k * 5, 40),
                vector_db_path=str(self.vector_db_path) if self.vector_db_path else None,
                filter_company=company_key or company_name,
                filter_year=report_year,
                verbose=False,
            )
            if not results and (company_name or company_key or report_year):
                results = search_vector_db(  # type: ignore
                    message,
                    top_k=self.search_top_k,
                    semantic_top_k=max(self.search_top_k * 5, 40),
                    vector_db_path=str(self.vector_db_path) if self.vector_db_path else None,
                    verbose=False,
                )
        except Exception as exc:
            # print(f"❌ [RAG Integration] search_vector_db failed: {exc}")
            return "", []

        if not results:
            return "", []

        filtered_results = [
            item
            for item in results
            if self._metadata_matches(item.get("metadata"), company_name, company_key, report_year)
        ]

        if company_name or company_key or report_year is not None:
            results_to_use = filtered_results or results
            if not filtered_results:
                print("⚠️ [RAG] 선택된 필터에 맞는 결과가 없어 전체 결과로 대체합니다.")
        else:
            results_to_use = filtered_results or results

        if not results_to_use:
            return "", []

        context_parts: List[str] = []
        source_info: List[str] = []
        for item in results_to_use:
            snippet, source_line = self._format_context_entry(item.get("content", ""), item.get("metadata", {}))
            context_parts.append(snippet)
            if source_line and source_line not in source_info:
                source_info.append(source_line)
        return "".join(context_parts), source_info

    def _build_messages(
        self,
        message: str,
        context: str,
        history: List[dict],
        company_name: Optional[str] = None,
        report_year: Optional[int] = None,
        apply_scope: bool = True,
    ) -> List[dict]:
        system_prompt = (
            "You are an expert ESG consultant. "
            "Answer the user's question based on the provided Context if available. "
            "If the context provides specific data, cite the company and year. "
            "If the context is empty or irrelevant, answer using your general knowledge but mention that this is general advice. "
            "If the user does not specify a report year and multiple years exist, politely ask which 연도 자료가 필요한지 instead of assuming. "
            "Speak in polite and professional Korean."
        )

        messages: List[dict] = [{"role": "system", "content": system_prompt}]
        trimmed_history = history[-self.max_history_messages :]
        for turn in trimmed_history:
            text = (turn.get("text") or "").strip()
            if not text:
                continue
            role = "assistant" if turn.get("role") == "assistant" else "user"
            messages.append({"role": role, "content": text})

        user_content = message.strip()
        if apply_scope and (company_name or report_year):
            scope_note = company_name or "선택된 기업"
            if report_year:
                scope_note += f" {report_year}년"
            user_content += f"\n\n[선택된 범위]\n{scope_note} 자료를 우선적으로 참고하세요."

        if context:
            user_content += f"\n\n[Context]\n{context}\n\n해당 문맥을 우선 사용하여 답변하세요."
        else:
            user_content += "\n\n[Context]\n(관련 문맥 없음: 일반적인 조언)"

        messages.append({"role": "user", "content": user_content})
        return messages

    async def get_chat_response(
        self,
        message: str,
        history: List[dict],
        company_name: Optional[str] = None,
        company_key: Optional[str] = None,
        report_year: Optional[int] = None,
    ):
        """
        RAG 기반 AI 답변 생성 (Vector DB + OpenAI)
        """
        # 응답 생성 시간 성능 측정 시작
        start_time = time.perf_counter()
        # 서비스가 초기화되지 않았으면 비동기 초기화 수행
        if not self._is_initialized:
            await self.initialize()

        fast_response = self._fast_path_response(message)
        if fast_response:
            return fast_response

        is_last_year_query = self._is_last_year_query(message)
        if report_year is None and is_last_year_query and (company_name or company_key):
            inferred_year = self._infer_latest_report_year(company_name, company_key)
            if inferred_year:
                report_year = inferred_year
                message = f"{message}\n\n[Interpretation] 'last year' means data year (report_year-1) from the latest report. Provide {report_year - 1} values."

        use_rag = self._should_use_rag(message)
        context = ""
        source_info: List[str] = []
        if use_rag:
            context_start = time.perf_counter()
            context, source_info = self._retrieve_context(
                message, company_name, company_key, report_year
            )
            print(
                f"⏱️ [Perf] Context retrieval took {time.perf_counter() - context_start:.2f}s"
            )

        if use_rag and (company_name or company_key or report_year) and not context:
            target = company_name or company_key or (
                f"{report_year}년 보고서" if report_year else "선택된 범위"
            )
            return (
                f"⚠️ {target} 관련 ESG 보고서를 Vector DB에서 찾지 못했습니다. "
                "PDF 업로드 또는 벡터 DB 동기화를 먼저 진행해 주세요."
            )

        if not settings.OPENAI_API_KEY:
            return "⚠️ OpenAI API Key가 설정되지 않았습니다. .env 파일을 확인해주세요."

        messages = self._build_messages(
            message, context, history, company_name, report_year, apply_scope=use_rag
        )

        try:
            llm_start = time.perf_counter()
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model="gpt-4o",  # or gpt-3.5-turbo
                messages=messages,
                temperature=0.7,
                max_tokens=600
            )
            print(f"⏱️ [Perf] LLM completion took {time.perf_counter() - llm_start:.2f}s")
            print(f"⏱️ [Perf] Total latency {time.perf_counter() - start_time:.2f}s")

            answer = self._content_to_text(response.choices[0].message.content)

            if source_info:
                answer += "\n\n📚 **참고 문헌:**\n" + "\n".join(source_info)

            return answer

        except Exception as e:
            print(f"LLM Error: {e}")
            return "죄송합니다. 답변 생성 중 오류가 발생했습니다. (OpenAI API 연결 실패)"

    # [Integrated] 비동기 제너레이터(Theirs) + 필터링 파라미터(Ours)
    async def stream_chat_response(
        self,
        message: str,
        history: List[dict],
        company_name: Optional[str] = None,
        company_key: Optional[str] = None,
        report_year: Optional[int] = None,
    ) -> Generator[str, None, None]:
        if not self._is_initialized:
            await self.initialize()
        fast_response = self._fast_path_response(message)
        if fast_response:
            yield fast_response
            return

        is_last_year_query = self._is_last_year_query(message)
        if report_year is None and is_last_year_query and (company_name or company_key):
            inferred_year = self._infer_latest_report_year(company_name, company_key)
            if inferred_year:
                report_year = inferred_year

        use_rag = self._should_use_rag(message)
        context = ""
        source_info: List[str] = []
        if use_rag:
            context_start = time.perf_counter()
            context, source_info = self._retrieve_context(
                message, company_name, company_key, report_year
            )
            print(
                f"⏱️ [Perf] Context retrieval took {time.perf_counter() - context_start:.2f}s"
            )

        if use_rag and (company_name or company_key or report_year) and not context:
            target = company_name or company_key or (
                f"{report_year}년 보고서" if report_year else "선택된 범위"
            )
            yield (
                f"⚠️ {target} 관련 ESG 보고서를 Vector DB에서 찾지 못했습니다. "
                "PDF 업로드 또는 벡터 DB 동기화를 먼저 진행해 주세요."
            )
            return

        if not settings.OPENAI_API_KEY:
            yield "⚠️ OpenAI API Key가 설정되지 않았습니다. .env 파일을 확인해주세요."
            return

        messages = self._build_messages(
            message, context, history, company_name, report_year, apply_scope=use_rag
        )

        try:
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            stream = await client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=600,
                stream=True
            )

            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if not delta:
                    continue
                content = self._content_to_text(getattr(delta, "content", None))
                if content:
                    yield content

            if source_info:
                yield "\n\n📚 **참고 문헌:**\n" + "\n".join(source_info)

        except Exception as e:
            print(f"LLM Stream Error: {e}")
            yield "죄송합니다. 답변 생성 중 오류가 발생했습니다. (OpenAI API 연결 실패)"

    async def text_to_sql(self, question: str, db_schema: str = None):
        """
        자연어를 SQL 쿼리로 변환 (Mock)
        """
        return f"SELECT * FROM documents WHERE content LIKE '%{question}%' LIMIT 5;"

    async def generate_compare_insight(self, my_company: str, intensity_type: str, my_intensity: float, median_intensity: float, top10_intensity: float, best_company: str, is_better_than_median: bool) -> str:
        """
        경쟁사 비교 탭에서 전략적 인사이트 문구를 생성 (Few-shot prompting 방식 + Fallback)
        """
        diff_to_top10 = max(0, my_intensity - top10_intensity)
        pct_to_top10 = (diff_to_top10 / my_intensity * 100) if my_intensity > 0 else 0
        intensity_label = "탄소 집약도" if intensity_type == 'revenue' else "에너지 집약도"
        
        fallback_text = "현재 일부 오류가 있어 인사이트를 출력하지 못했습니다."

        if not settings.OPENAI_API_KEY:
            return fallback_text

        # 탄소 집약도용 예시
        carbon_examples = f"""
[예시 1 - 지표 값이 평균보다 낮아 효율성이 우수할 시]
<strong class="text-white">{my_company}</strong>은(는) 현재 업계 평균보다 우수한 탄소 배출 효율성을 보이고 있으나, 상위 10% 진입을 위해서는 {intensity_label}의 <span class="text-[#10b77f] font-bold">15.0% 추가 감축</span>이 필요합니다. 선두 기업({best_company}) 수준의 도약을 위해서는 공급망 단위의 <span class="text-white underline decoration-[#10b77f]/50 decoration-2 underline-offset-4">Scope 3 저감 및 친환경 원료 전환</span>에 집중하는 전략적 투자가 요구됩니다.

[예시 2 - 지표 값이 평균보다 높아 효율성이 저조할 시]
<strong class="text-white">{my_company}</strong>은(는) 현재 탄소 배출량이 업계 평균에 미치지 못하고 있으며, 글로벌 규제 대응을 위해서는 {intensity_label}의 <span class="text-[#10b77f] font-bold">32.5% 대폭 감축</span>이 시급합니다. 선두 기업({best_company})과 경쟁하려면 다배출 공정을 전면 재검토하고 <span class="text-white underline decoration-[#10b77f]/50 decoration-2 underline-offset-4">저탄소 에너지원 비중 확대</span>가 필요합니다.

[예시 3 - 상위권 달성 시]
<strong class="text-white">{my_company}</strong>은(는) 이미 업계 상위 10%에 진입하여 탄소 관리 부문에서 압도적인 포지션을 점하고 있습니다. 초격차 유지를 향한 한계 돌파를 위해서는 <span class="text-[#10b77f] font-bold">혁신 감축 기술 발굴</span>과 <span class="text-white underline decoration-[#10b77f]/50 decoration-2 underline-offset-4">저탄소 밸류체인 생태계 확장</span> 상용화를 주도해야 합니다.
"""

        # 에너지 집약도용 예시
        energy_examples = f"""
[예시 1 - 지표 값이 평균보다 낮아 효율성이 우수할 시]
<strong class="text-white">{my_company}</strong>은(는) 현재 업계 평균보다 우수한 에너지 사용 효율을 보이고 있으나, 상위 10% 진입을 위해서는 {intensity_label}의 <span class="text-[#10b77f] font-bold">15.0% 추가 절감</span>이 필요합니다. 선두 기업({best_company}) 수준의 도약을 위해서는 노후 설비 개체 및 <span class="text-white underline decoration-[#10b77f]/50 decoration-2 underline-offset-4">스마트 에너지 관리 시스템(FEMS) 도입</span>에 집중하는 전략적 투자가 요구됩니다.

[예시 2 - 지표 값이 평균보다 높아 효율성이 저조할 시]
<strong class="text-white">{my_company}</strong>은(는) 현재 에너지 낭비가 업계 평균을 초과하고 있어, 글로벌 탑티어 도약을 위해서는 {intensity_label}의 <span class="text-[#10b77f] font-bold">32.5% 대폭 개선</span>이 시급합니다. 선두 기업({best_company})과 같은 제조 경쟁력을 확보하려면 에너지 다소비 핵심 공정의 열효율을 높이고 <span class="text-white underline decoration-[#10b77f]/50 decoration-2 underline-offset-4">폐열 회수 기술 적용</span>이 필요합니다.

[예시 3 - 상위권 달성 시]
<strong class="text-white">{my_company}</strong>은(는) 이미 에너지 효율 부문에서 업계 상위 10%에 진입하여 압도적인 원가 경쟁력을 점하고 있습니다. 초격차 유지를 향한 한계 돌파를 위해서는 <span class="text-[#10b77f] font-bold">초고효율 차세대 설비 R&D</span>와 <span class="text-white underline decoration-[#10b77f]/50 decoration-2 underline-offset-4">AI 기반 제조 전력망 최적화</span>를 전사적으로 주도해야 합니다.
"""

        examples = carbon_examples if intensity_type == 'revenue' else energy_examples
        
        prompt = f"""당신은 날카로운 통찰력을 지닌 ESG 전략 컨설턴트입니다.
다음의 데이터를 기반으로 기업 로고 옆에 띄울 짧고 강력한 '전략적 인사이트' 2문장을 한국어로 작성해 주세요. HTML 태그(<strong class="text-white">, <span class="text-[#10b77f] font-bold">, <span class="text-white underline decoration-[#10b77f]/50 decoration-2 underline-offset-4"> 등)를 반드시 포함하여 핵심 문구를 강조해야 합니다. 마크다운의 **굵게**는 쓰지 말고 HTML만 사용하세요.

[데이터]
- 분석 대상 기업: {my_company}
- 지표 종류: {intensity_label} (낮을수록 좋음)
- {my_company}의 지표 값: {my_intensity:.2f}
- 업계 평균(Median): {median_intensity:.2f}
- 상위 10% 컷오프: {top10_intensity:.2f}
- 상위 10% 진입을 위한 필요 감축률: 약 {pct_to_top10:.1f}%
- 1위 기업(선두): {best_company}
- {my_company}이(가) 평균보다 우수한가? {'예' if is_better_than_median else '아니오'}

주어진 데이터 범위를 넘어서 특정 기업이 "재생에너지 100% 전환", "RE100 달성" 혹은 기재되지 않은 "특정 기술"을 이미 사용 중이라는 허위 사실을 지어내지 마세요. 선두 그룹(또는 압도적 포지션) 진입이나 기술적 한계를 돌파하기 위한 '일반적이고 타당한' 전략적 방향을 방향성으로 제시하세요.
{examples}
"""

        try:
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            content = self._content_to_text(response.choices[0].message.content)
            return content.strip()
        except Exception as e:
            print(f"Compare Insight GPT Error: {e}")
            return fallback_text

ai_service = AIService()
