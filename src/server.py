import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from src.safety import check as safety_check
from src.classifier import classify_intent
from src.agents.portfolio_health import handle_portfolio_health
from src.agents.stubs import handle_stub

app = FastAPI(title="Valura AI Microservice")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Load users for demo purposes
FIXTURES_DIR = Path("fixtures/users")
USERS = {}
if FIXTURES_DIR.exists():
    for f in FIXTURES_DIR.glob("*.json"):
        try:
            with open(f, encoding="utf-8") as file:
                u = json.load(file)
                USERS[u["user_id"]] = u
        except Exception:
            pass

# In-memory session history for dedupe and follow-ups
SESSIONS = {}

async def generate_response(query: str, user_id: str, session_id: str):
    try:
        # 1. Safety Guard
        yield {"data": json.dumps({"status": "processing", "message": "Running safety checks..."})}
        safety_verdict = safety_check(query)
        
        if safety_verdict.blocked:
            error_resp = {
                "status": "error",
                "error_type": "safety_block",
                "category": safety_verdict.category,
                "message": safety_verdict.message
            }
            yield {"data": json.dumps(error_resp)}
            return

        # 2. Intent Classification
        yield {"data": json.dumps({"status": "processing", "message": "Classifying intent..."})}
        history = SESSIONS.get(session_id, [])
        classification = await classify_intent(query, history)
        
        # Save query to history
        history.append({"role": "user", "content": query})
        SESSIONS[session_id] = history
        
        yield {"data": json.dumps({
            "status": "processing", 
            "message": f"Routed to {classification.agent}",
            "intent": classification.intent,
            "entities": classification.entities.model_dump(exclude_unset=True)
        })}

        user_data = USERS.get(user_id, {})

        # 3. Agent Routing
        if classification.agent == "portfolio_health":
            async for chunk in handle_portfolio_health(classification.intent, classification.entities.model_dump(), user_data):
                # Ensure correct format for sse_starlette (it handles the "data:" prefix)
                # The generator yields strings like "data: {...}\n\n". 
                # With EventSourceResponse, we just yield dictionaries.
                chunk = chunk.replace("data: ", "").strip()
                if chunk:
                    yield {"data": chunk}
        else:
            async for chunk in handle_stub(classification.agent, classification.intent, classification.entities.model_dump()):
                chunk = chunk.replace("data: ", "").strip()
                if chunk:
                    yield {"data": chunk}

    except Exception as e:
        yield {"data": json.dumps({
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}"
        })}

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    body = await request.json()
    query = body.get("query", "")
    user_id = body.get("user_id", "usr_001")
    session_id = body.get("session_id", "default_session")
    
    return EventSourceResponse(generate_response(query, user_id, session_id))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
