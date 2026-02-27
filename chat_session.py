import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트 및 backend 경로 추가
root_dir = Path(__file__).resolve().parent
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "backend"))

# .env 로드
from dotenv import load_dotenv
load_dotenv()

# AI 서비스 임포트
try:
    from backend.app.services.ai_service import ai_service
except ImportError:
    # 경로 문제 대응
    from app.services.ai_service import ai_service

async def chat():
    print("="*60)
    print("      ESG 챗봇 연속 대화 테스트 (종료하려면 'exit' 입력)")
    print("="*60)
    
    # AI 서비스 초기화 (Vector DB 등 로드)
    await ai_service.initialize()
    
    history = []
    
    while True:
        user_input = input("👤 사용자: ").strip()
        
        if user_input.lower() in ["exit", "quit", "종료", "q"]:
            print("👋 대화를 종료합니다.")
            break
            
        if not user_input:
            continue

        print("🤖 AI: ", end="", flush=True)
        full_response = ""

        try:
            # 스트리밍 응답 호출
            async for chunk in ai_service.stream_chat_response(
                message=user_input,
                history=history,
                company_name="삼성전자", # 테스트용 기본값
                report_year=2023
            ):
                print(chunk, end="", flush=True)
                full_response += chunk
            
            # 대화 이력 저장 (연속성 핵심)
            history.append({"role": "user", "text": user_input})
            history.append({"role": "assistant", "text": full_response})
            
            # 대화 이력이 너무 길어지는 것 방지 (최근 10개만 유지 등 가능)
            if len(history) > 20:
                history = history[-20:]
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(chat())
    except KeyboardInterrupt:
        print("👋 종료되었습니다.")
