import sys
import asyncio
sys.path.append('/home/dmin/ESG_Wep/backend')
from app.services.market_data import market_service

async def main():
    res = await market_service.get_dual_market_history('1y')
    print("Length of result:", len(res))
    if len(res) > 0:
        print("Last 5 items:", res[-5:])

if __name__ == '__main__':
    asyncio.run(main())
