import requests
import json

try:
    response = requests.get('http://0.0.0.0:8000/api/v1/sim/dashboard/market-trends?period=1y')
    data = response.json()
    print(json.dumps(data.get('chart_data', [])[-5:], indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
