# Valura AI — Team Lead Project Assignment

This repository implements the intelligence spine of the Valura AI Wealth Management Microservice. The architecture is designed to be highly reliable, blazing fast, and robust at the edges, keeping the novice investor safe while providing real-time, grounded insights.

## Quick Start

### Prerequisites
- Python 3.11+
- An OpenAI API Key

### Setup
1. Clone the repository and navigate into it:
   ```bash
   git clone <your-classroom-repo-url>
   cd <repo-name>
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Copy `.env.example` to `.env` and insert your OpenAI API key.
   ```bash
   OPENAI_API_KEY=your-api-key-here
   ```

### Running the Microservice
Start the FastAPI server:
```bash
python src/server.py
```
*(The server will start on `http://0.0.0.0:8000`)*

### Testing the Pipeline
We've included a lightweight test client to demonstrate the Server-Sent Events (SSE) streaming locally. While the server is running, open a new terminal and run:
```bash
python test_client.py
```
This will send a portfolio health query and print the incoming streaming chunks to the console.

### Running the Tests
```bash
pytest tests/ -v
```
*(All tests pass locally and in CI without hitting the OpenAI API, thanks to our robust mock logic).*

---

## Architectural Decisions & Trade-offs

### 1. Safety Guard: Deterministic Regex vs. LLM
Instead of burning latency and tokens on a safety LLM, we built a **deterministic regex/keyword engine** (`src/safety.py`). 
- **Why?** It guarantees sub-millisecond (<1ms) execution. For strict compliance rules (e.g., stopping insider trading or guaranteed returns), regex provides 100% predictability and cannot be "jailbroken" like an LLM. It achieved **95.45% harmful recall** and **100% educational passthrough** on the open set.

### 2. Intent Classifier: Strict Pydantic Output
We implemented the `gpt-4o-mini` classifier utilizing `json_object` combined with a rigorous Pydantic schema injection (`src/classifier.py`). 
- **Why?** We guarantee that the `agent` string will exactly match our routing taxonomy, and `entities` will perfectly align with the expected downstream shapes. This eliminates "hallucinated keys" breaking the pipeline.

### 3. Portfolio Health Agent: Compute First, Talk Second
Our `portfolio_health` agent calculates concentration mathematically using the user's base costs and utilizes `yfinance` to fetch live benchmark prices.
- **Why?** LLMs are terrible at math. By calculating `top_position_pct` and `total_return_pct` in Python natively, and using `yfinance` for real-time `SPY` price comparisons, we guarantee precision. We only use the LLM (or in this case, deterministic heuristics) to format the final textual observations for the user.
- **Graceful Fallbacks:** If `yfinance` is rate-limited or offline, the agent catches the error and streams the calculations based on cost-basis, rather than crashing the SSE stream.

### 4. In-Memory Session Storage
For this assignment, session history is stored in an in-memory dictionary.
- **Why?** To reduce deployment friction for the reviewer. In a production environment, this would be replaced with Redis or Postgres (via `asyncpg`).

### 5. SSE Error Handling
When a pipeline fails (e.g. safety block or unexpected exception), we yield the error as a structured SSE dictionary rather than throwing an HTTP 500 error.
- **Why?** In streaming microservices, once headers are sent, the connection is open. Standard HTTP exception handlers won't catch generator failures cleanly on the client. Our approach ensures the client UI can parse and cleanly render the failure.

---

## Defence Video

[Insert unlisted YouTube link here]

*(Note: Link will be added within 24 hours of final commit as per assignment rules).*
