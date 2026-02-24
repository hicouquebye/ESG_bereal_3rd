from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .routers import simulator, ai, dashboard, auth, profile
from .services.market_data import market_service
from .services.ai_service import ai_service
import asyncio


@asynccontextmanager
async def lifespan(application: FastAPI):
    """서버 시작/종료 시 실행되는 수명주기 핸들러"""
    # Startup: 데이터 미리 로딩
    asyncio.create_task(market_service.preload_data())
    asyncio.create_task(ai_service.initialize())
    yield
    # Shutdown: 필요 시 정리 작업


app = FastAPI(title="ESG Simulator API", lifespan=lifespan)

# CORS 설정 (React 프론트엔드 연결 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(simulator.router)
app.include_router(ai.router)
app.include_router(auth.router)
app.include_router(profile.router)

static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    return {"message": "ESG Simulator API is running"}
