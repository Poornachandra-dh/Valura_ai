import re
from typing import NamedTuple

class SafetyVerdict(NamedTuple):
    blocked: bool
    message: str
    category: str | None = None

RULES = {
    "insider_trading": {
        "pattern": r"(unannounced.*buy|tip.*load up|confidential.*trade|trade.*confidential|earnings before.*announcement|need to know the earnings before)",
        "message": "I cannot assist with trading based on material non-public information."
    },
    "market_manipulation": {
        "pattern": r"(pump up.*selling|coordinated buying|wash trade.*between two accounts)",
        "message": "I cannot participate in or assist with market manipulation strategies."
    },
    "money_laundering": {
        "pattern": r"(without reporting|structure deposits|layer my trades|hide trading profits)",
        "message": "I cannot advise on methods to evade financial reporting or launder money."
    },
    "guaranteed_returns": {
        "pattern": r"(guarantee me|promise me|100% certain|foolproof way)",
        "message": "I cannot guarantee returns. All investments carry risk."
    },
    "reckless_advice": {
        "pattern": r"(all my retirement.*do it|margin loan to buy|entire emergency fund|mortgage my house)",
        "message": "I cannot advise taking reckless financial positions or using inappropriate leverage."
    },
    "sanctions_evasion": {
        "pattern": r"(route trades through a shell company|sanctioned.*without it being traced)",
        "message": "I cannot assist in bypassing international sanctions."
    },
    "fraud": {
        "pattern": r"(draft a fake)",
        "message": "I cannot assist with fraudulent activities."
    }
}

_compiled_rules = {cat: re.compile(rule["pattern"], re.IGNORECASE) for cat, rule in RULES.items()}

def check(query: str) -> SafetyVerdict:
    """
    Synchronous, local safety check.
    Evaluates query against regex rules and blocks obvious harmful intent.
    """
    for category, pattern in _compiled_rules.items():
        if pattern.search(query):
            return SafetyVerdict(
                blocked=True,
                message=RULES[category]["message"],
                category=category
            )
            
    return SafetyVerdict(blocked=False, message="Passed", category=None)
