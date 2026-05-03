import json
import os
from typing import Literal, List, Optional
from pydantic import BaseModel, Field
import openai

AgentType = Literal[
    "portfolio_health", "market_research", "investment_strategy", "financial_planning",
    "financial_calculator", "risk_assessment", "product_recommendation",
    "predictive_analysis", "customer_support", "general_query"
]

class Entities(BaseModel):
    tickers: Optional[List[str]] = Field(None, description="Array of strings, uppercase, exchange-suffixed where relevant (AAPL, ASML.AS, 7203.T)")
    amount: Optional[float] = Field(None, description="number, in the unit of currency")
    currency: Optional[str] = Field(None, description="ISO 4217 string (USD, EUR, GBP, JPY)")
    rate: Optional[float] = Field(None, description="decimal (0.08 for 8%)")
    period_years: Optional[int] = Field(None, description="integer")
    frequency: Optional[Literal["daily", "weekly", "monthly", "yearly"]] = Field(None)
    horizon: Optional[Literal["6_months", "1_year", "5_years"]] = Field(None)
    time_period: Optional[Literal["today", "this_week", "this_month", "this_year"]] = Field(None)
    topics: Optional[List[str]] = Field(None, description="Array of strings")
    sectors: Optional[List[str]] = Field(None, description="Array of strings")
    index: Optional[Literal["S&P 500", "FTSE 100", "NIKKEI 225", "MSCI World"]] = Field(None)
    action: Optional[Literal["buy", "sell", "hold", "hedge", "rebalance"]] = Field(None)
    goal: Optional[Literal["retirement", "education", "house", "FIRE", "emergency_fund"]] = Field(None)

class ClassificationResult(BaseModel):
    intent: str = Field(description="A short description of the user's intent")
    agent: AgentType = Field(description="The agent to route the query to")
    entities: Entities = Field(default_factory=Entities)
    informational_safety_verdict: str = Field(description="Informational safety verdict")

from dotenv import load_dotenv

load_dotenv(override=True)

def get_client():
    return openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "mock-key"))

async def classify_intent(query: str, history: List[dict] = None, llm_mock: dict = None) -> ClassificationResult:
    """
    Calls the LLM to classify intent, extract entities and route to the correct agent.
    """
    if llm_mock:
        return ClassificationResult.model_validate(llm_mock)

    client = get_client()
    
    schema = ClassificationResult.model_json_schema()
    
    system_prompt = (
        "You are the intent classifier for Valura AI Wealth Management. "
        "Your job is to route the user's query to the correct agent and extract entities.\n\n"
        "Agent Taxonomy:\n"
        "- portfolio_health: structured assessment of the user's portfolio (concentration, performance, benchmarking, observations)\n"
        "- market_research: factual/recent info about an instrument, sector, or market event\n"
        "- investment_strategy: advice/strategy questions: should I buy/sell/rebalance, allocation guidance\n"
        "- financial_planning: long-term planning: retirement, goals, savings rate\n"
        "- financial_calculator: deterministic numerical computation: DCA returns, mortgage, tax, future value, FX conversion\n"
        "- risk_assessment: risk metrics, exposure analysis, what-if scenarios\n"
        "- product_recommendation: recommend specific products/funds matching user profile\n"
        "- predictive_analysis: forward-looking analysis: forecasts, trend extrapolation\n"
        "- customer_support: platform issues, account questions, how-to-use-app\n"
        "- general_query: educational, conversational, definitions, greetings\n\n"
        "Rules:\n"
        "- If it's a single ticker with no verb (e.g. 'AAPL'), route to market_research.\n"
        "- If it's a multi-intent query, route to the primary intent.\n"
        "- Resolve pronouns and context from the conversation history if present.\n"
        f"You MUST output ONLY a valid JSON object matching this schema:\n{json.dumps(schema, indent=2)}"
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": query})

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0
        )
        content = response.choices[0].message.content
        return ClassificationResult.model_validate_json(content)
    except Exception as e:
        print(f"\n[CLASSIFIER ERROR] LLM failed: {str(e)}\nMake sure your OPENAI_API_KEY is set in .env!\n")
        return ClassificationResult(
            intent=f"Failed to classify: {str(e)}",
            agent="general_query",
            entities=Entities(),
            informational_safety_verdict="Error during classification"
        )
