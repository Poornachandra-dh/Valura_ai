import httpx
import json
import asyncio

async def test_chat():
    url = "http://localhost:8000/api/chat"
    payload = {
        "query": "how is my portfolio doing?",
        "user_id": "usr_001",
        "session_id": "session_1"
    }

    print(f"Connecting to {url}...")
    
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url, json=payload, timeout=20.0) as response:
            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                return
                
            print("Connected! Streaming response...\n")
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[len("data: "):]
                    try:
                        data = json.loads(data_str)
                        if data.get("status") == "processing":
                            print(f"[⏳] {data.get('message')}")
                        elif data.get("status") == "complete":
                            print("\n[✅] Agent Response Complete:")
                            print(json.dumps(data, indent=2))
                        elif data.get("status") == "error":
                            print(f"\n[❌] Error: {data.get('message')}")
                        elif data.get("status") == "stub":
                            print(f"\n[🚧] Stub Agent: {data.get('message')}")
                    except json.JSONDecodeError:
                        print(f"Raw: {data_str}")

if __name__ == "__main__":
    asyncio.run(test_chat())
