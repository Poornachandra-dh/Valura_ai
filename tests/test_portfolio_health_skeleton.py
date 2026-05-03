"""
Skeleton test for the Portfolio Health agent.

Wire your agent import and remove the skip decorators.
"""
import pytest
import asyncio
import json
from src.agents.portfolio_health import handle_portfolio_health

async def run(user, llm=None):
    final_response = None
    async for chunk in handle_portfolio_health("portfolio_health", {}, user):
        data = json.loads(chunk)
        if data.get("status") == "complete":
            final_response = data
    return final_response

def test_portfolio_health_does_not_crash_on_empty_portfolio(load_user, mock_llm):
    """
    user_004 has no positions. Agent must not crash.
    """
    user = load_user("usr_004")
    response = asyncio.run(run(user, llm=mock_llm))

    assert response is not None
    assert "disclaimer" in response


def test_portfolio_health_flags_concentration(load_user, mock_llm):
    """
    user_003 has ~60% in NVDA. Agent must surface this.
    """
    user = load_user("usr_003")
    response = asyncio.run(run(user, llm=mock_llm))

    assert response["concentration_risk"]["flag"] in {"high", "warning"}


def test_portfolio_health_includes_disclaimer(load_user, mock_llm):
    user = load_user("usr_001")
    response = asyncio.run(run(user, llm=mock_llm))
    assert response["disclaimer"]
    assert "not investment advice" in response["disclaimer"].lower()
