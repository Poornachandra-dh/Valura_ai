import json

async def handle_stub(agent_name: str, intent: str, entities: dict) -> str:
    """
    Generator that streams a structured stub response for unimplemented agents.
    Yields SSE-compatible string chunks.
    """
    response_obj = {
        "agent": agent_name,
        "intent": intent,
        "entities": entities,
        "message": f"The {agent_name} agent is not implemented in this build.",
        "status": "stub"
    }
    
    # We yield a single chunk for the stub, formatted as JSON data
    yield json.dumps(response_obj)
