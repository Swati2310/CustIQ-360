
# CustIQ 360° — Implementation Plan

> **Multi-Agent AI System for Banking Relationship Managers**
> Unifies CASA, Lending, Wealth Management & KYC into a single intelligent customer profile.

---

## 1. Project Overview

**Problem:** Relationship Managers spend 15–30 min per customer lookup across fragmented banking modules (CASA, Lending, Wealth, KYC). This leads to missed cross-sell opportunities, slow onboarding, and no real-time financial insights.

**Goal:** Reduce lookup time to <2 minutes with AI-driven decision support.

**Core Capabilities:**
- Customer 360 Aggregator (unified profile)
- Conversational Query Engine (natural language Q&A)
- Cross-Sell Recommender
- What-If Simulator (EMI, FD penalties, loan scenarios)
- Compliance Guardrail Agent (KYC/regulatory validation)
- Proactive Alert Engine (expiry, churn-risk, dormancy warnings)

---

## 2. Tech Stack

| Layer          | Technology                                             |
|----------------|--------------------------------------------------------|
| Backend        | Python 3.11+, FastAPI                                  |
| Frontend       | React 18+ (Vite), TailwindCSS                         |
| LLM Runtime    | **Ollama** (local inference server)                    |
| Chat Model     | **Llama 3.1 8B** (fast) / **Mistral 7B** (alternative)|
| Vision Model   | **LLaVA 1.6 13B** (multimodal — document extraction)  |
| Embeddings     | **nomic-embed-text** via Ollama (768-dim, top-tier)    |
| Orchestration  | LangChain / LangGraph                                  |
| Vector DB      | FAISS (or ChromaDB as easier alternative)              |
| Database       | SQLite (dev) → PostgreSQL (prod)                       |
| Deployment     | Vercel (frontend), self-hosted / Docker (backend+Ollama)|

### Why Ollama?

- **Zero API costs** — Everything runs on your machine. No rate limits, no billing.
- **OpenAI-compatible API** — Ollama exposes `http://localhost:11434` with an API that LangChain supports natively. Switching models is a one-line config change.
- **Model flexibility** — Pull any model with `ollama pull <model>`. Swap Llama 3.1 for Mistral, Phi-3, Qwen2, or Gemma2 without code changes.
- **Privacy** — Customer banking data never leaves your machine.

### Recommended Models by Task

| Task                     | Model                  | Size  | Why                                      |
|--------------------------|------------------------|-------|------------------------------------------|
| Chat / Reasoning         | `llama3.1:8b`          | ~4.7GB| Best open-source balance of speed + quality |
| Complex reasoning        | `llama3.1:70b`         | ~40GB | Use if you have a GPU with 48GB+ VRAM    |
| Document/Image OCR       | `llava:13b`            | ~8GB  | Multimodal — reads ID proofs, salary slips|
| Embeddings               | `nomic-embed-text`     | ~275MB| Top-performing open embedding model       |
| Fast/lightweight fallback| `phi3:mini`            | ~2.3GB| For low-resource machines                 |

### Hardware Requirements

- **Minimum:** 16GB RAM, no GPU — runs `llama3.1:8b` on CPU (slower, ~5-10 tokens/sec)
- **Recommended:** 16GB RAM + GPU with 8GB+ VRAM (NVIDIA RTX 3060+) — fast inference (~30-50 tokens/sec)
- **Ideal:** 32GB RAM + 24GB VRAM (RTX 4090 / A5000) — can run 13B models comfortably

---

## 3. Project Structure

```
custiq-360/
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Settings, API keys, env vars
│   ├── requirements.txt
│   │
│   ├── data/                    # Simulated banking data
│   │   ├── seed_data.py         # Script to generate fake customers
│   │   ├── customers.json       # CASA, Lending, Wealth, KYC records
│   │   └── products.json        # Bank product catalog
│   │
│   ├── models/                  # Pydantic schemas
│   │   ├── customer.py          # Customer360 unified model
│   │   ├── product.py           # Financial product model
│   │   └── alert.py             # Alert/notification model
│   │
│   ├── services/                # Business logic
│   │   ├── aggregator.py        # Customer 360 Aggregator
│   │   ├── query_engine.py      # Conversational Query Engine
│   │   ├── recommender.py       # Cross-Sell Recommender
│   │   ├── simulator.py         # What-If Simulator
│   │   ├── compliance.py        # Compliance Guardrail Agent
│   │   └── alerts.py            # Proactive Alert Engine
│   │
│   ├── agents/                  # LangGraph multi-agent orchestration
│   │   ├── graph.py             # Main agent graph definition
│   │   ├── router.py            # Intent classifier / router agent
│   │   ├── tools.py             # Tool definitions for agents
│   │   └── prompts.py           # System prompts for each agent
│   │
│   ├── rag/                     # RAG pipeline
│   │   ├── indexer.py           # Document chunking + FAISS indexing
│   │   ├── retriever.py         # Semantic search over customer data
│   │   └── embeddings.py        # Embedding model config
│   │
│   ├── document_processing/     # Document extraction (OCR, images)
│   │   ├── extractor.py         # Extract from ID proofs, salary slips
│   │   └── vision.py            # LLaVA (Ollama) multimodal integration
│   │
│   └── api/                     # API route handlers
│       ├── customer_routes.py   # /api/customer/* endpoints
│       ├── chat_routes.py       # /api/chat  (websocket or SSE)
│       ├── simulator_routes.py  # /api/simulate/*
│       └── alert_routes.py      # /api/alerts/*
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── components/
│       │   ├── Layout/
│       │   │   ├── Sidebar.jsx
│       │   │   └── TopBar.jsx
│       │   ├── Customer360/
│       │   │   ├── ProfileCard.jsx
│       │   │   ├── AccountsSummary.jsx
│       │   │   ├── LoansSummary.jsx
│       │   │   ├── WealthSummary.jsx
│       │   │   └── KYCStatus.jsx
│       │   ├── Chat/
│       │   │   ├── ChatPanel.jsx
│       │   │   └── MessageBubble.jsx
│       │   ├── Simulator/
│       │   │   ├── EMICalculator.jsx
│       │   │   ├── FDSimulator.jsx
│       │   │   └── LoanScenario.jsx
│       │   ├── Recommendations/
│       │   │   └── CrossSellCard.jsx
│       │   ├── Alerts/
│       │   │   └── AlertBanner.jsx
│       │   └── Documents/
│       │       └── DocumentUploader.jsx
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── CustomerView.jsx
│       │   ├── SimulatorPage.jsx
│       │   └── AlertsPage.jsx
│       ├── hooks/
│       │   ├── useChat.js
│       │   └── useCustomer.js
│       └── utils/
│           └── api.js           # Axios/fetch wrapper
│
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## 4. Implementation Phases

### Phase 1 — Foundation & Data Layer (Days 1–3)

**Goal:** Backend skeleton + simulated banking data + basic API.

**Tasks:**
1. **Initialize backend** — FastAPI app, config, CORS, project scaffolding.
2. **Create simulated data** — Python script (`seed_data.py`) generating 50–100 fake customers with:
   - CASA accounts (savings, current — balances, transactions)
   - Loans (home loan, personal loan — EMI, outstanding, tenure)
   - Wealth (FDs, mutual funds, insurance policies)
   - KYC (Aadhaar, PAN, address proof — status, expiry dates)
3. **Define Pydantic models** — `Customer360`, `Account`, `Loan`, `WealthHolding`, `KYCRecord`, `Product`.
4. **Build Aggregator service** — Merge all modules into a unified `Customer360` object.
5. **Expose REST endpoints:**
   - `GET /api/customers` — list all customers
   - `GET /api/customers/{id}` — full 360 profile
   - `GET /api/customers/{id}/accounts`
   - `GET /api/customers/{id}/loans`
   - `GET /api/customers/{id}/wealth`
   - `GET /api/customers/{id}/kyc`

**Deliverable:** Working API returning unified customer profiles from simulated data.

---

### Phase 2 — RAG Pipeline & Semantic Search (Days 4–6)

**Goal:** Index customer data into FAISS, enable semantic search.

**Tasks:**
1. **Embeddings setup** — Use `nomic-embed-text` via Ollama (768-dim, runs locally). LangChain's `OllamaEmbeddings` class handles this natively.
   ```python
   from langchain_ollama import OllamaEmbeddings
   embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://localhost:11434")
   ```
2. **Indexer** — Chunk customer records into text passages, generate embeddings, store in FAISS index.
3. **Retriever** — Given a natural language query, retrieve top-k relevant customer data chunks.
4. **Product catalog index** — Separately index the bank's product catalog for cross-sell retrieval.
5. **API endpoint:** `POST /api/search` — semantic search over customer data.

**Deliverable:** Semantic search returning relevant customer info for natural language queries.

---

### Phase 3 — LLM Agents with LangGraph (Days 7–11)

**Goal:** Multi-agent orchestration — the core intelligence layer.

**Ollama + LangChain Integration Pattern:**
```python
from langchain_ollama import ChatOllama

# All agents use this same LLM instance
llm = ChatOllama(
    model="llama3.1:8b",
    base_url="http://localhost:11434",
    temperature=0.1,        # Low temp for factual banking queries
    num_ctx=8192,           # Context window — increase for long customer profiles
)
```

#### Agent 1: Router Agent
- Classifies user intent: lookup, query, simulate, recommend, compliance check.
- Routes to the appropriate specialist agent.

#### Agent 2: Conversational Query Engine
- Takes natural language questions like "What is Rajesh's total outstanding loan?"
- Uses RAG retriever to fetch context, then **Llama 3.1 via Ollama** to generate answers.
- Endpoint: `POST /api/chat`

#### Agent 3: Cross-Sell Recommender
- Analyzes customer profile (income, holdings, transaction patterns).
- Matches against product catalog using semantic similarity + rule-based filters.
- Returns ranked product recommendations with reasoning.

#### Agent 4: What-If Simulator
- **EMI Calculator:** Loan amount, rate, tenure → EMI, total interest.
- **FD Penalty Calculator:** Premature withdrawal amount, penalty rate.
- **Loan Scenario:** "What if customer takes ₹20L home loan at 8.5% for 20 years?"
- Pure computation + LLM-generated explanation.

#### Agent 5: Compliance Guardrail
- Validates every recommendation against KYC status, eligibility rules, regulatory constraints.
- Checks: KYC expiry, income eligibility, age limits, product suitability.
- Returns pass/fail with reasons.

#### Agent 6: Proactive Alert Engine
- Scans all customers daily for: KYC expiry (30/60/90 days), FD maturity, dormant accounts, churn risk signals.
- Generates prioritized alert list.

**LangGraph Wiring (graph.py):**
```
User Input → Router Agent
  ├─→ Query Engine (+ RAG retriever)
  ├─→ Recommender (+ Compliance guardrail)
  ├─→ Simulator
  └─→ Alert Engine
Each agent returns structured output → formatted response to user.
```

**Deliverable:** Working multi-agent system accessible via `/api/chat`.

---

### Phase 4 — Document Processing (Days 12–13)

**Goal:** Extract info from uploaded documents (ID proofs, salary slips, property docs).

**Tasks:**
1. **LLaVA via Ollama** — Use the `llava:13b` multimodal model for image understanding. It runs locally through Ollama just like the text models.
   ```python
   import ollama
   
   # Send an image to LLaVA for extraction
   response = ollama.chat(
       model="llava:13b",
       messages=[{
           "role": "user",
           "content": "Extract all text fields from this ID proof. Return as JSON with keys: name, dob, id_number, address.",
           "images": ["./uploaded_id_proof.jpg"]
       }]
   )
   ```
2. **Extraction pipeline + OCR fallback:**
   - Primary: LLaVA for structured extraction from images.
   - Fallback: **Tesseract OCR** (`pytesseract`) for scanned PDFs or when LLaVA struggles.
   - ID Proofs → Name, DOB, ID number, address.
   - Salary Slips → Gross salary, net salary, employer, deductions.
   - Property Docs → Property value, address, ownership details.
3. **Auto-populate KYC fields** from extracted data.
4. **Endpoint:** `POST /api/documents/extract` — upload file, return structured extraction.

**Deliverable:** Upload a document image → get structured JSON data back.

---

### Phase 5 — React Frontend (Days 14–19)

**Goal:** Build the RM-facing dashboard.

#### Page 1: Dashboard
- Customer search bar (by name, account number, phone).
- Recent lookups, active alerts count, quick stats.

#### Page 2: Customer 360 View
- **Profile header:** Name, photo placeholder, customer segment, relationship vintage.
- **Tabs/Sections:**
  - Accounts: CASA balances, recent transactions.
  - Loans: Active loans, EMI schedule, outstanding.
  - Wealth: FDs, MFs, insurance — with maturity dates.
  - KYC: Document status, expiry warnings.
- **Chat Panel (right sidebar):** Conversational interface to ask questions about this customer.
- **Recommendations strip:** Cross-sell suggestions with compliance badge (✅/⚠️).

#### Page 3: Simulator
- Interactive EMI calculator with sliders.
- FD what-if tool.
- Loan comparison table.

#### Page 4: Alerts
- Prioritized list: KYC expiry, FD maturity, dormancy, churn risk.
- Filter by type, severity, date range.

**Deliverable:** Fully functional React app connected to backend APIs.

---

### Phase 6 — Integration, Polish & Deployment (Days 20–22)

**Tasks:**
1. **End-to-end testing** — Full user flow from search → 360 view → chat → simulate → recommend.
2. **Streaming responses** — Ollama natively supports streaming. Use FastAPI's `StreamingResponse` with SSE:
   ```python
   from fastapi.responses import StreamingResponse
   import ollama
   
   async def stream_chat(prompt: str):
       for chunk in ollama.chat(model="llama3.1:8b", messages=[...], stream=True):
           yield f"data: {chunk['message']['content']}\n\n"
   ```
3. **Error handling** — Graceful fallbacks when Ollama is not running or model is loading.
4. **Loading states & UX polish** — Skeleton loaders, animations, responsive design.
5. **Docker Compose deployment** (single `docker-compose up`):
   ```yaml
   # docker-compose.yml
   services:
     ollama:
       image: ollama/ollama
       ports: ["11434:11434"]
       volumes: ["ollama_data:/root/.ollama"]
       deploy:
         resources:
           reservations:
             devices:
               - capabilities: [gpu]   # Optional: GPU passthrough
     backend:
       build: ./backend
       ports: ["8000:8000"]
       environment:
         - OLLAMA_BASE_URL=http://ollama:11434
       depends_on: [ollama]
     frontend:
       build: ./frontend
       ports: ["5173:5173"]
       depends_on: [backend]
   volumes:
     ollama_data:
   ```
6. **Environment variables** — Ollama URL, CORS origins, model names.

**Deliverable:** Deployed, working application.

---

## 5. Key API Endpoints Summary

| Method | Endpoint                        | Description                        |
|--------|----------------------------------|------------------------------------|
| GET    | `/api/customers`                | List customers (search, paginate)  |
| GET    | `/api/customers/{id}`           | Full 360 profile                   |
| POST   | `/api/chat`                     | Send message to multi-agent system |
| POST   | `/api/simulate/emi`             | EMI calculation                    |
| POST   | `/api/simulate/fd`              | FD penalty / maturity simulation   |
| POST   | `/api/simulate/loan-scenario`   | Loan scenario comparison           |
| GET    | `/api/alerts`                   | Get all active alerts              |
| POST   | `/api/documents/extract`        | Upload & extract document info     |
| POST   | `/api/search`                   | Semantic search over customer data |
| GET    | `/api/recommendations/{id}`     | Cross-sell recommendations         |

---

## 6. Data Models (Core Schemas)

```python
# Customer360 — Unified Profile
{
  "customer_id": "CUST001",
  "name": "Rajesh Kumar",
  "phone": "+91-98765-43210",
  "email": "rajesh@example.com",
  "segment": "HNI",            # Mass / Affluent / HNI
  "relationship_since": "2015-03-12",
  "accounts": [
    {
      "account_id": "SA001",
      "type": "Savings",
      "balance": 245000.00,
      "branch": "Mumbai - Andheri",
      "status": "Active"
    }
  ],
  "loans": [
    {
      "loan_id": "HL001",
      "type": "Home Loan",
      "sanctioned_amount": 5000000,
      "outstanding": 3200000,
      "emi": 42000,
      "rate": 8.5,
      "tenure_months": 240,
      "status": "Active"
    }
  ],
  "wealth": [
    {
      "holding_id": "FD001",
      "type": "Fixed Deposit",
      "amount": 1000000,
      "rate": 7.1,
      "maturity_date": "2025-06-15"
    }
  ],
  "kyc": {
    "aadhaar": { "number": "XXXX-XXXX-1234", "verified": true },
    "pan": { "number": "ABCDE1234F", "verified": true },
    "address_proof": { "type": "Passport", "expiry": "2026-01-15" },
    "risk_category": "Low",
    "last_updated": "2024-01-10"
  }
}
```

---

## 7. Environment Variables

```env
# .env.example

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama3.1:8b
OLLAMA_VISION_MODEL=llava:13b
OLLAMA_EMBED_MODEL=nomic-embed-text

# App Configuration
FAISS_INDEX_PATH=./data/faiss_index
CORS_ORIGINS=http://localhost:5173
DATABASE_URL=sqlite:///./data/custiq.db
ALERT_CHECK_INTERVAL=86400

# Optional: Increase context window for large customer profiles
OLLAMA_NUM_CTX=8192
```

---

## 8. Claude Code Quick-Start Commands

Run these in order when starting implementation:

```bash
# ============================
# STEP 0: Install & Start Ollama
# ============================
# macOS / Linux:
curl -fsSL https://ollama.com/install.sh | sh

# Windows: Download from https://ollama.com/download

# Pull required models (do this once — downloads may take a few minutes)
ollama pull llama3.1:8b          # Chat & reasoning (~4.7GB)
ollama pull nomic-embed-text     # Embeddings (~275MB)
ollama pull llava:13b            # Vision/OCR (~8GB) — optional, pull when needed

# Verify Ollama is running
curl http://localhost:11434/api/tags   # Should list your models

# ============================
# STEP 1: Create project structure
# ============================
mkdir -p custiq-360/{backend/{data,models,services,agents,rag,document_processing,api},frontend}

# ============================
# STEP 2: Initialize backend
# ============================
cd custiq-360/backend
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn langchain langchain-ollama langgraph \
    faiss-cpu chromadb ollama pydantic python-dotenv \
    pytesseract pillow python-multipart

# ============================
# STEP 3: Initialize frontend
# ============================
cd ../frontend
npm create vite@latest . -- --template react
npm install axios react-router-dom tailwindcss @tailwindcss/vite lucide-react recharts

# ============================
# STEP 4: Start development
# ============================
# Terminal 1 (Ollama — auto-starts, but verify): ollama serve
# Terminal 2 (Backend):  cd backend && uvicorn main:app --reload
# Terminal 3 (Frontend): cd frontend && npm run dev
```

---

## 9. Implementation Tips for Claude Code

- **Start with Phase 1** — Get the data layer and basic API working first. Everything else builds on it.
- **Verify Ollama first** — Before writing any LLM code, confirm `ollama list` shows your models and `curl http://localhost:11434/api/tags` returns them. Many issues come from Ollama not running.
- **Use `langchain-ollama`**, not the deprecated `langchain-community` Ollama wrapper. The import is `from langchain_ollama import ChatOllama, OllamaEmbeddings`.
- **Use fake data liberally** — The simulated data should feel realistic (Indian banking context: ₹ amounts, Indian names, Aadhaar/PAN formats).
- **Test each agent independently** — Before wiring the LangGraph graph, make sure each agent works standalone with a simple test script.
- **Keep prompts in `prompts.py`** — Centralize all system prompts so they're easy to tune. Open-source models need more explicit, structured prompts than proprietary models — use clear delimiters and examples.
- **Stream chat responses** — Ollama supports streaming natively. Use FastAPI's `StreamingResponse` with SSE for a good UX.
- **Compliance agent is critical** — Every recommendation must pass through it. Wire it as a mandatory step in the graph, not optional.
- **If responses are slow** — Try `phi3:mini` (2.3GB) for faster inference on CPU, or quantized variants like `llama3.1:8b-q4_0`.
- **ChromaDB as FAISS alternative** — If FAISS setup is tricky, ChromaDB is pip-installable and works with LangChain out of the box. Perfectly fine for this project scale.

---

## 10. Ollama Quick Reference

```bash
# Model management
ollama pull llama3.1:8b           # Download a model
ollama list                       # See installed models
ollama rm llama3.1:8b             # Remove a model
ollama show llama3.1:8b           # Model details (params, license, size)

# Run interactively (for testing prompts)
ollama run llama3.1:8b "What is a CASA account in banking?"

# API (used by LangChain under the hood)
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Explain EMI calculation formula",
  "stream": false
}'

# Check if Ollama is running
curl http://localhost:11434/api/tags
```

---

**Total estimated timeline: ~3 weeks for a working prototype.**

Good luck building CustIQ 360°! 🚀
