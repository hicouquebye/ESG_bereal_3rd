import requests
import json

base_url = "http://localhost:8000"

endpoints = [
    "/",
    "/docs",
    "/api/v1/sim/dashboard/market-trends?period=1y"
]

for ep in endpoints:
    url = base_url + ep
    print(f"Testing {url} ...")
    try:
        response = requests.get(url, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            if "json" in response.headers.get("Content-Type", ""):
                try:
                    data = response.json()
                    # Summary of data
                    if isinstance(data, list):
                        print(f"List length: {len(data)}")
                    elif isinstance(data, dict):
                        print(f"Keys: {list(data.keys())}")
                        if "chart_data" in data:
                            print(f"Chart Data Len: {len(data['chart_data'])}")
                except:
                    print("Could not parse JSON")
            else:
                 print("Not JSON content")
        else:
            print(f"Error Body: {response.text[:100]}")
    except Exception as e:
        print(f"Exception: {e}")
    print("-" * 20)
