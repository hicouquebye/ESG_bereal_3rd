import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "backend"))
load_dotenv()

from backend.app.services.ai_service import ai_service

async def run_tests():
    await ai_service.initialize()
    print("\n--- Test 1: Ambiguity ---")
    resp1 = await ai_service.get_chat_response("온실가스 배출량 알려줘", [], company_name="현대건설")
    print("User: 온실가스 배출량 알려줘 (HDEC)")
    print("AI:", resp1)

    print("\n--- Test 2: Hallucination ---")
    resp2 = await ai_service.get_chat_response("현대건설이 RE100을 2025년에 달성했다는데 맞아?", [], company_name="현대건설", report_year=2024)
    print("User: 현대건설이 RE100을 2025년에 달성했다는데 맞아?")
    print("AI:", resp2)

    print("\n--- Test 3: Out of Domain ---")
    resp3 = await ai_service.get_chat_response("내일 서울 날씨 어때?", [])
    print("User: 내일 서울 날씨 어때?")
    print("AI:", resp3)

if __name__ == "__main__":
    asyncio.run(run_tests())
