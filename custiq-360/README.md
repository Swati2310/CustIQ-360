# CustIQ 360° — Customer Intelligence Platform

> A multi-agent AI banking dashboard that gives Relationship Managers a unified 360° view of every customer — accounts, loans, wealth, KYC, proactive alerts, semantic search, AI document extraction, financial simulator, and a streaming conversational agent — powered by Google Gemini 2.5 Flash and LangGraph.

**Live Demo:** https://cust-iq-360.vercel.app
**API Docs:** https://custiq-360-backend.onrender.com/docs

---

## Problem

Relationship Managers in banks navigate multiple core banking modules (CASA, Lending, Wealth, KYC) to understand a customer's complete financial profile — taking **15–30 minutes per lookup**. This causes missed cross-sell opportunities, no real-time personalized recommendations, and slow manual document onboarding.

## Solution

A multi-agent AI system on top of simulated core banking modules that unifies everything into a single **Customer 360° profile**. Specialized agents reduce lookup time from ~30 minutes to **under 2 minutes**.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 18, Vite, TailwindCSS, Recharts | Animated SPA dashboard |
| **Backend** | Python 3.11, FastAPI, Uvicorn | REST API, SSE streaming |
| **LLM** | Google Gemini 2.5 Flash | Chat, reasoning, vision extraction |
| **Embeddings** | gemini-embedding-001 | Semantic search vector generation |
| **Vision AI** | Gemini 2.5 Flash (multimodal) | KYC document extraction from images |
| **Agent Orchestration** | LangGraph + LangChain | Multi-agent pipeline with routing |
| **Vector Store** | FAISS (faiss-cpu) | Semantic search over customer corpus |
| **Voice** | Web Speech API (browser-native) | Voice search + voice-to-text chat |
| **Auth** | Session-based (sessionStorage) | RM login with global profiles |
| **Deployment** | Vercel (frontend) + Render (backend) | Cloud-hosted, live public URL |
| **Containerisation** | Docker + Docker Compose | One-command local deployment |
| **Web Server** | Nginx (Alpine) | Static file serving + reverse proxy |

---

## Features

### Six AI Agents
| Agent | What it does |
|---|---|
| **Customer 360 Aggregator** | Unifies CASA, Lending, Wealth, KYC into one profile |
| **Conversational Query Engine** | Natural-language Q&A via RAG + LangGraph (SSE streaming) |
| **Cross-Sell Recommender** | Ranks next-best products using LLM + rule-based scoring |
| **What-If Simulator** | EMI, FD maturity, loan comparison — instant calculations |
| **Compliance Guardrail** | Validates every recommendation against KYC, income, NPA rules |
| **Proactive Alert Engine** | KYC expiry, FD maturity, dormancy, churn-risk alerts |

### Document Intelligence
- Upload **5 KYC document types**: Aadhaar, PAN Card, Address Proof, Salary Slip, Property Doc
- Gemini Vision extracts structured fields and auto-persists to customer profile

### Voice Capabilities
- **Voice-to-Text Chat**: Speak your question — auto-transcribed and sent to the AI agent
- **Voice Customer Search**: Say a customer name — search bar auto-fills and fires

### Global RM Portal
- Login system with **9 Relationship Managers** across APAC, EMEA, and AMER regions
- RM ID format: `RM-[ISO3 country]-[sequence]` (e.g. `RM-IND-001`, `RM-GBR-001`)
- Auto currency switching based on customer's country (12 currencies supported)

### Data Coverage
- **95 synthetic customers** across 11 countries
- Countries: India, Singapore, UAE, UK, Germany, Japan, Australia, Hong Kong, Malaysia, Saudi Arabia, South Africa
- **43+ proactive alerts** generated across the customer base

---

## Live Credentials (Demo)

| Employee ID | Name | Region | Country |
|---|---|---|---|
| `RM-IND-001` | Arjun Sharma | APAC | India |
| `RM-SGP-001` | Wei Ling Tan | APAC | Singapore |
| `RM-HKG-001` | James Wong | APAC | Hong Kong |
| `RM-AUS-001` | Claire Thompson | APAC | Australia |
| `RM-GBR-001` | Sarah Mitchell | EMEA | United Kingdom |
| `RM-UAE-001` | Fatima Al-Rashid | EMEA | UAE |
| `RM-DEU-001` | Klaus Müller | EMEA | Germany |
| `RM-USA-001` | Michael Carter | AMER | United States |
| `RM-BRA-001` | Ana Oliveira | AMER | Brazil |

> Password for all accounts: contact IT Support (not shown here intentionally)

---

## Quick Start — Local Development

### Prerequisites

| Dependency | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 20+ |
| Google Gemini API Key | Free at aistudio.google.com |

### Step 1 — Clone & Configure

```bash
git clone https://github.com/Swati2310/CustIQ-360.git
cd CustIQ-360/custiq-360
```

Create `backend/.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_CHAT_MODEL=gemini-2.5-flash
GEMINI_VISION_MODEL=gemini-2.5-flash
GEMINI_EMBED_MODEL=gemini-embedding-001
FAISS_INDEX_PATH=./data/faiss_index
CORS_ORIGINS=http://localhost:5173
```

### Step 2 — Backend

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend live at: http://localhost:8000
API docs: http://localhost:8000/docs

### Step 3 — Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend live at: http://localhost:5173

---

## Docker — One-Command Local Deploy

```bash
# Add your Gemini API key to backend/.env first, then:
docker compose up --build

# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## Deployment (Production)

This project is deployed on:
- **Frontend:** Vercel — https://cust-iq-360.vercel.app
- **Backend:** Render — https://custiq-360-backend.onrender.com

### Deploy your own

**Backend on Render:**
1. New Web Service → connect `Swati2310/CustIQ-360`
2. Root Directory: `custiq-360/backend`
3. Language: Python 3
4. Build: `pip install -r requirements.txt`
5. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add env vars: `GEMINI_API_KEY`, `GEMINI_CHAT_MODEL`, `GEMINI_VISION_MODEL`, `GEMINI_EMBED_MODEL`, `CORS_ORIGINS=*`

**Frontend on Vercel:**
1. New Project → import `Swati2310/CustIQ-360`
2. Root Directory: `custiq-360/frontend`
3. Framework: Vite
4. Add env var: `VITE_API_BASE_URL=https://your-render-url.onrender.com`
5. Deploy

**After both are live:**
Update `CORS_ORIGINS` on Render to your Vercel URL (e.g. `https://cust-iq-360.vercel.app`).

> **Note:** Render free tier spins down after 15 min of inactivity. First request after idle takes ~30–50 seconds.

---

## API Endpoints

### Customers
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/customers` | List customers (search, paginate) |
| GET | `/api/customers/{id}` | Full 360° profile |
| GET | `/api/customers/{id}/accounts` | Accounts |
| GET | `/api/customers/{id}/loans` | Loans |
| GET | `/api/customers/{id}/wealth` | Wealth holdings |
| GET | `/api/customers/{id}/kyc` | KYC status |
| PATCH | `/api/customers/{id}/apply-extraction` | Apply document extraction to profile |

### AI Agents
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat` | SSE streaming chat (LangGraph multi-agent) |
| GET | `/api/recommendations/{id}` | Cross-sell recommendations with compliance |
| GET | `/api/alerts` | All proactive alerts sorted by severity |

### Simulator
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/simulate/emi` | EMI + full amortisation schedule |
| POST | `/api/simulate/fd` | FD maturity, yield, TDS projection |
| POST | `/api/simulate/loan-scenario` | Side-by-side loan comparison |

### Documents & Search
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/documents/extract` | Upload image → structured JSON (Gemini Vision) |
| POST | `/api/search` | Semantic search over customer corpus (FAISS) |

### System
| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check + loaded model info |
| GET | `/docs` | Swagger UI |

---

## Environment Variables

### Backend (`backend/.env`)
| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | — | Google Gemini API key (required) |
| `GEMINI_CHAT_MODEL` | `gemini-2.5-flash` | Model for chat and agent reasoning |
| `GEMINI_VISION_MODEL` | `gemini-2.5-flash` | Model for document/image extraction |
| `GEMINI_EMBED_MODEL` | `gemini-embedding-001` | Model for semantic embeddings |
| `FAISS_INDEX_PATH` | `./data/faiss_index` | Path to FAISS index directory |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed CORS origins (comma-separated) |

### Frontend (`frontend/.env`)
| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | *(empty — uses Vite proxy in dev)* | Backend URL for production builds |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (RM)                         │
│  React 18 + Vite + TailwindCSS                          │
│  Voice: Web Speech API (SpeechRecognition)              │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTPS / SSE
                           ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (Render)                    │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              LangGraph Agent Graph               │  │
│  │  Router → Query / Recommend / Simulate /         │  │
│  │           Comply / Alert / Fallback              │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌────────────────┐  ┌──────────────────────────────┐  │
│  │ CustomerAggre- │  │ DocumentExtractor            │  │
│  │ gator (CASA,   │  │ (Gemini Vision → KYC fields) │  │
│  │ Loans, Wealth, │  └──────────────────────────────┘  │
│  │ KYC unified)   │  ┌──────────────────────────────┐  │
│  └────────────────┘  │ AlertEngine + Recommender    │  │
│                      │ + ComplianceAgent            │  │
│  ┌────────────────┐  └──────────────────────────────┘  │
│  │ FAISS Vector   │                                     │
│  │ Index (RAG)    │  customers.json (95 customers,      │
│  └────────────────┘  11 countries, synthetic data)      │
└──────────────────────────┬──────────────────────────────┘
                           │ Google AI API
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Google Gemini 2.5 Flash                     │
│   Chat · Reasoning · Vision · Embeddings                │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
custiq-360/
├── backend/
│   ├── agents/
│   │   ├── graph.py          # LangGraph 6-node agent graph
│   │   ├── router.py         # Intent classifier
│   │   ├── prompts.py        # System prompts per agent
│   │   └── tools.py          # LangChain tool definitions
│   ├── api/
│   │   ├── customer_routes.py
│   │   ├── chat_routes.py    # SSE streaming + recommendations + alerts
│   │   ├── document_routes.py
│   │   ├── simulator_routes.py
│   │   ├── search_routes.py
│   │   └── alert_routes.py
│   ├── document_processing/
│   │   ├── vision.py         # Gemini Vision extraction per doc type
│   │   └── extractor.py      # Pipeline: Vision → OCR fallback
│   ├── models/
│   │   ├── customer.py       # Customer360 Pydantic model
│   │   ├── product.py
│   │   └── alert.py
│   ├── rag/
│   │   ├── indexer.py        # FAISS index builder (batched for rate limits)
│   │   ├── retriever.py      # Semantic search
│   │   └── embeddings.py     # gemini-embedding-001 wrapper
│   ├── services/
│   │   ├── aggregator.py     # Customer 360 unifier + document persist
│   │   ├── query_engine.py   # LangGraph chat wrapper
│   │   ├── recommender.py    # LLM + rule-based cross-sell
│   │   ├── compliance.py     # KYC / income / NPA guardrail
│   │   └── alerts.py         # KYC expiry, FD maturity, churn, dormancy
│   ├── tests/
│   │   ├── test_api.py       # 72 tests — all passing
│   │   ├── test_aggregator.py
│   │   ├── test_currency.py
│   │   └── test_data.py
│   ├── data/
│   │   ├── customers.json    # 95 synthetic customers, 11 countries
│   │   └── products.json     # Banking product catalogue
│   ├── config.py
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Chat/         # ChatPanel with voice input + SSE streaming
│       │   ├── Customer360/  # Accounts, Loans, Wealth, KYC tabs
│       │   ├── Documents/    # DocumentUploader (5 KYC doc types)
│       │   ├── Layout/       # Dark sidebar + glass TopBar with voice search
│       │   ├── Recommendations/
│       │   ├── Simulator/    # EMI, FD, LoanScenario
│       │   └── Alerts/
│       ├── context/
│       │   ├── AuthContext.jsx     # RM login, 9 global profiles
│       │   └── CurrencyContext.jsx # Auto-switch per customer country
│       ├── hooks/
│       │   ├── useChat.js          # SSE streaming hook
│       │   ├── useCustomer.js
│       │   └── useVoice.js         # Web Speech API hook (voice input)
│       ├── pages/
│       │   ├── LoginPage.jsx       # Animated glassmorphism login
│       │   ├── Dashboard.jsx       # Personalised greeting + stats
│       │   ├── CustomerView.jsx
│       │   ├── SimulatorPage.jsx
│       │   └── AlertsPage.jsx
│       └── utils/
│           ├── api.js              # Axios + fetch (VITE_API_BASE_URL aware)
│           └── format.js
├── docker-compose.yml          # Gemini-based, no Ollama dependency
└── README.md
```

---

## Tests

```bash
cd custiq-360/backend
source venv/bin/activate
pytest tests/ -v

# 72 passed in ~15s
```

Test coverage: customer data integrity, API endpoints, aggregator logic, multi-currency conversion.

---

## Troubleshooting

### Backend slow on first request (Render free tier)
Render free tier spins down after 15 minutes of inactivity. Open `https://custiq-360-backend.onrender.com/health` in your browser ~1 minute before a demo to wake it up.

### CORS errors in browser
Update `CORS_ORIGINS` on Render to exactly match your Vercel URL (no trailing slash):
```
CORS_ORIGINS=https://cust-iq-360.vercel.app
```

### Voice not working
Voice input uses the browser's `SpeechRecognition` API. It is supported in **Chrome and Edge**. It is not supported in Firefox — the mic button will be hidden automatically.

### FAISS index not found
The FAISS index is built at startup from `customers.json`. If the `data/faiss_index/` directory is missing, semantic search falls back gracefully. To rebuild manually:
```bash
cd backend && source venv/bin/activate
python -c "
from services.aggregator import CustomerAggregator
from rag.indexer import CustomerIndexer
import json
agg = CustomerAggregator(); agg.load_customers()
print('Index rebuilt for', agg.count(), 'customers')
"
```

---

## License

MIT
