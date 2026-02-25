"""
FastAPI Backend Server for ESG Dashboard
Connects React frontend with PDF_Extraction Python modules
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# 앱 컴포넌트 가져오기
from app.routers import simulator, ai, dashboard, auth, profile
from app.services.market_data import market_service



# PDF_Extraction 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "PDF_Extraction" / "src"))

# 환경 변수 로드
load_dotenv(Path(__file__).parent.parent / ".env")


@asynccontextmanager
async def lifespan(application: FastAPI):
    """서버 시작/종료 시 실행되는 수명주기 핸들러"""
    asyncio.create_task(market_service.preload_data())
    yield


app = FastAPI(
    title="ESG Dashboard API",
    description="ESG 문서 분석 및 검색을 위한 API",
    version="1.0.0",
    lifespan=lifespan
)

# React 프론트엔드 연결을 위한 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경을 위해 모든 오리진 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 앱 라우터 포함 ---
app.include_router(simulator.router)
app.include_router(ai.router)
app.include_router(dashboard.router)
app.include_router(auth.router)
app.include_router(profile.router)



# ============================================
# Response Models
# ============================================

class SearchResult(BaseModel):
    rank: int
    distance: float
    company_name: str
    report_year: str
    page_no: int
    chunk_index: int
    content_preview: str
    doc_id: str


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResult]


class HealthResponse(BaseModel):
    status: str
    message: str


class ChatRequest(BaseModel):
    message: str
    top_k: int = 3  # Number of documents to retrieve


class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    query: str


# ============================================
# API Endpoints
# ============================================

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        message="ESG Dashboard API (BACKEND_ROOT_MAIN) is running"
    )


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """API health check"""
    return HealthResponse(
        status="ok",
        message="API is healthy"
    )


@app.get("/api/search", response_model=SearchResponse)
async def search_esg(
    query: str = Query(..., description="Search query string"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results to return")
):
    """
    Search ESG documents using vector similarity search.
    
    - **query**: The search query string (e.g., "탄소배출", "환경정책")
    - **top_k**: Number of results to return (1-20, default: 5)
    """
    try:
        # Import here to avoid loading heavy models at startup
        import chromadb
        from sentence_transformers import SentenceTransformer
        
        # Configuration (must match PDF_Extraction settings)
        VECTOR_DB_DIR = str(Path(__file__).parent.parent / "PDF_Extraction" / "vector_db")
        COLLECTION_NAME = "esg_documents"
        EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
        
        # Check if vector DB exists
        if not os.path.exists(VECTOR_DB_DIR):
            raise HTTPException(
                status_code=404,
                detail=f"Vector DB not found. Please run PDF_Extraction pipeline first."
            )
        
        # Initialize ChromaDB
        client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
        
        try:
            collection = client.get_collection(COLLECTION_NAME)
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{COLLECTION_NAME}' not found: {str(e)}"
            )
        
        # Embed query
        model = SentenceTransformer(EMBEDDING_MODEL_NAME, device='cpu')
        query_vec = model.encode([query]).tolist()
        
        # Query ChromaDB
        results = collection.query(
            query_embeddings=query_vec,
            n_results=top_k
        )
        
        # Format results
        search_results = []
        if results['documents'] and results['documents'][0]:
            for idx, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][idx]
                distance = results['distances'][0][idx]
                
                search_results.append(SearchResult(
                    rank=idx + 1,
                    distance=round(distance, 4),
                    company_name=meta.get('company_name', 'Unknown'),
                    report_year=str(meta.get('report_year', 'Unknown')),
                    page_no=meta.get('page_no', 0),
                    chunk_index=meta.get('chunk_index', 0),
                    content_preview=doc[:300].replace('\n', ' '),
                    doc_id=results['ids'][0][idx]
                ))
        
        return SearchResponse(
            query=query,
            total_results=len(search_results),
            results=search_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search error: {str(e)}"
        )


@app.get("/api/companies")
async def list_companies():
    """
    List all companies in the database.
    """
    try:
        import chromadb
        
        VECTOR_DB_DIR = str(Path(__file__).parent.parent / "PDF_Extraction" / "vector_db")
        COLLECTION_NAME = "esg_documents"
        
        if not os.path.exists(VECTOR_DB_DIR):
            return {"companies": []}
        
        client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
        
        try:
            collection = client.get_collection(COLLECTION_NAME)
            # Get all metadata to extract unique companies
            all_data = collection.get(include=["metadatas"])
            
            companies = set()
            for meta in all_data['metadatas']:
                if 'company_name' in meta:
                    companies.add(meta['company_name'])
            
            return {"companies": sorted(list(companies))}
            
        except Exception:
            return {"companies": []}
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing companies: {str(e)}"
        )


@app.get("/api/stats")
async def get_stats():
    """
    Get database statistics.
    """
    try:
        import chromadb
        
        VECTOR_DB_DIR = str(Path(__file__).parent.parent / "PDF_Extraction" / "vector_db")
        COLLECTION_NAME = "esg_documents"
        
        if not os.path.exists(VECTOR_DB_DIR):
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "companies": [],
                "years": []
            }
        
        client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
        
        try:
            collection = client.get_collection(COLLECTION_NAME)
            all_data = collection.get(include=["metadatas"])
            
            companies = set()
            years = set()
            
            for meta in all_data['metadatas']:
                if 'company_name' in meta:
                    companies.add(meta['company_name'])
                if 'report_year' in meta:
                    years.add(str(meta['report_year']))
            
            return {
                "total_chunks": len(all_data['ids']),
                "total_companies": len(companies),
                "companies": sorted(list(companies)),
                "years": sorted(list(years), reverse=True)
            }
            
        except Exception:
            return {
                "total_chunks": 0,
                "total_companies": 0,
                "companies": [],
                "years": []
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting stats: {str(e)}"
        )


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_esg(request: ChatRequest):
    """
    RAG-based chat endpoint.
    Searches relevant documents and generates response using Ollama gemma3.
    
    - **message**: User's question about ESG
    - **top_k**: Number of documents to retrieve for context (default: 3)
    """
    import httpx
    import chromadb
    from sentence_transformers import SentenceTransformer
    
    try:
        # Configuration
        VECTOR_DB_DIR = str(Path(__file__).parent.parent / "PDF_Extraction" / "vector_db")
        COLLECTION_NAME = "esg_documents"
        EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
        OLLAMA_URL = "http://localhost:11434/api/generate"
        
        # Check if vector DB exists
        if not os.path.exists(VECTOR_DB_DIR):
            raise HTTPException(
                status_code=404,
                detail="Vector DB not found. Please run PDF_Extraction pipeline first."
            )
        
        # 1. Search Vector DB for relevant documents
        client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
        collection = client.get_collection(COLLECTION_NAME)
        
        # Embed the query (use CPU to save GPU memory for LLM)
        model = SentenceTransformer(EMBEDDING_MODEL_NAME, device='cpu')
        query_vec = model.encode([request.message]).tolist()
        
        # Query for similar documents
        results = collection.query(
            query_embeddings=query_vec,
            n_results=request.top_k
        )
        
        # 2. Prepare context from retrieved documents
        sources = []
        context_parts = []
        
        if results['documents'] and results['documents'][0]:
            for idx, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][idx]
                source_info = {
                    "company": meta.get('company_name', 'Unknown'),
                    "year": str(meta.get('report_year', 'Unknown')),
                    "page": meta.get('page_no', 0),
                    "content_preview": doc[:200]
                }
                sources.append(source_info)
                context_parts.append(f"[문서 {idx+1}] {meta.get('company_name', '')} {meta.get('report_year', '')}년 보고서 (p.{meta.get('page_no', '')}):\n{doc}")
        
        context = "\n\n".join(context_parts)
        
        # 3. Create prompt for LLM
        system_prompt = """당신은 ESG(환경, 사회, 거버넌스) 전문가 AI 어시스턴트입니다.
주어진 문서 내용을 바탕으로 사용자의 질문에 정확하고 친절하게 답변해주세요.
답변할 때 반드시 문서의 내용을 참고하고, 확실하지 않은 정보는 추측하지 마세요.
한국어로 답변해주세요."""

        user_prompt = f"""다음 ESG 보고서 문서들을 참고하여 질문에 답변해주세요.

=== 참고 문서 ===
{context}

=== 질문 ===
{request.message}

=== 답변 ==="""

        # 4. Call Ollama API
        async with httpx.AsyncClient(timeout=120.0) as http_client:
            ollama_response = await http_client.post(
                OLLAMA_URL,
                json={
                    "model": "qwen2.5:7b",
                    "prompt": user_prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_ctx": 4096
                    }
                }
            )
            
            if ollama_response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail=f"Ollama API error: {ollama_response.text}"
                )
            
            response_data = ollama_response.json()
            answer = response_data.get("response", "죄송합니다. 답변을 생성할 수 없습니다.")
        
        return ChatResponse(
            answer=answer.strip(),
            sources=sources,
            query=request.message
        )
        
    except HTTPException:
        raise
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Ollama 서버에 연결할 수 없습니다. Ollama가 실행 중인지 확인해주세요."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat error: {str(e)}"
        )


# Run with: uvicorn main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
