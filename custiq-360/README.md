# CustIQ 360°  —  Customer Intelligence Platform

> An AI-powered banking relationship management platform that gives relationship managers a 360° view of every customer: accounts, loans, wealth, KYC, proactive alerts, semantic search, document intelligence, and a financial simulator — all driven by local LLMs via Ollama.

---

## Screenshot

```
┌──────────────────────────────────────────────────────────────────┐
│  CustIQ 360°  Dashboard                          [Search...]     │
│  ┌─────────────────┐  ┌──────────────────────────────────────┐  │
│  │  Customer List   │  │  Priya Sharma — Wealth Segment       │  │
│  │  ──────────────  │  │  ┌─────────┐ ┌─────────┐ ┌───────┐ │  │
│  │  Priya Sharma   ▶│  │  │Accounts │ │  Loans  │ │Wealth │ │  │
│  │  Rahul Mehta     │  │  └─────────┘ └─────────┘ └───────┘ │  │
│  │  Anita Desai     │  │  ⚠ KYC expires in 12 days           │  │
│  │  ...             │  │  💬 Chat with AI assistant           │  │
│  └─────────────────┘  └──────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

*(Replace with actual screenshot once the app is running)*

---

## Tech Stack

| Layer         | Technology                                      | Purpose                                    |
|---------------|-------------------------------------------------|--------------------------------------------|
| Frontend      | React 18, Vite, Tailwind CSS                    | SPA dashboard, responsive UI               |
| Backend       | FastAPI 0.111, Python 3.11, Uvicorn             | REST API, SSE streaming, business logic    |
| LLM Runtime   | Ollama (local)                                  | Runs all models on-device, no cloud needed |
| Chat Model    | llama3.1:8b                                     | Conversational AI, RAG, agent reasoning    |
| Vision Model  | llava:13b                                       | Document OCR / extraction fallback         |
| Embed Model   | nomic-embed-text                                | Semantic search vector embeddings          |
| Vector Store  | FAISS (faiss-cpu)                               | Similarity search over customer corpus     |
| Agent Graph   | LangGraph + LangChain                           | Multi-agent orchestration                  |
| Containerise  | Docker + Docker Compose                         | One-command deployment                     |
| Web Server    | Nginx (Alpine)                                  | Static file serving + reverse proxy        |

---

## Quick Start

Choose the option that best fits your environment:

### Option 1 — Docker Compose (Recommended)

Requires: Docker Desktop 4.x+, ~20 GB free disk (for LLM weights)

```bash
# 1. Clone the repo
git clone <repo-url>
cd custiq-360

# 2. Pull Ollama models into the named volume BEFORE starting the stack
#    (run once; models are cached in the ollama_data volume)
docker run --rm -v ollama_data:/root/.ollama ollama/ollama pull llama3.1:8b
docker run --rm -v ollama_data:/root/.ollama ollama/ollama pull llava:13b
docker run --rm -v ollama_data:/root/.ollama ollama/ollama pull nomic-embed-text

# 3. Start all services
docker compose up --build

# 4. Open in browser
#    Frontend:  http://localhost:5173
#    API docs:  http://localhost:8000/docs
```

---

### Option 2 — Local Development (Hot Reload)

Best for active development; both backend and frontend reload on file changes.

```bash
# Terminal 1 — Ollama
ollama serve

# Terminal 2 — Backend
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env            # edit as needed
uvicorn main:app --reload --port 8000

# Terminal 3 — Frontend
cd frontend
npm install
npm run dev
```

---

### Option 3 — Manual (No Docker, No venv)

Suitable for quick tests on a machine where Python/Node are globally available.

```bash
# Ollama must already be running: ollama serve

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend
npm install && npm run build
npx serve dist -l 5173
```

---

## Prerequisites

| Dependency    | Minimum Version | Install                                            |
|---------------|-----------------|----------------------------------------------------|
| Ollama        | 0.3+            | https://ollama.com/download                        |
| Python        | 3.11+           | https://www.python.org/downloads/                  |
| Node.js       | 20+             | https://nodejs.org/                                |
| npm           | 9+              | bundled with Node                                  |
| Docker        | 24+ (optional)  | https://www.docker.com/products/docker-desktop     |
| Tesseract OCR | 5+ (optional)   | `brew install tesseract` / `apt install tesseract` |

---

## Step-by-Step Local Setup

### Step 1 — Install Ollama and Pull Models

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Start the Ollama server (leave this terminal open)
ollama serve

# Pull the required models (one-time; ~14 GB total)
ollama pull llama3.1:8b       # ~4.7 GB  — chat + agent reasoning
ollama pull llava:13b         # ~8.0 GB  — vision / document extraction
ollama pull nomic-embed-text  # ~274 MB  — semantic search embeddings
```

Verify models are available:
```bash
ollama list
# NAME                   ID            SIZE    MODIFIED
# llama3.1:8b            ...           4.7 GB  ...
# llava:13b              ...           8.0 GB  ...
# nomic-embed-text       ...           274 MB  ...
```

---

### Step 2 — Backend Setup

```bash
cd custiq-360/backend

# Create and activate a virtual environment
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy the example environment file and review settings
cp ../.env.example .env

# Start the backend server (with hot-reload for development)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be live at http://localhost:8000
Interactive Swagger docs: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

---

### Step 3 — Frontend Setup

```bash
cd custiq-360/frontend

# Install Node dependencies
npm install

# Start the Vite dev server (hot module replacement enabled)
npm run dev
```

The frontend will be available at http://localhost:5173

---

### Step 4 — Build the FAISS Index

The semantic search feature requires a FAISS index to be built from the customer
corpus. Run this once after the backend is running:

```bash
# From within the backend/ directory with .venv activated
python -c "
from services.aggregator import CustomerAggregator
from rag.indexer import build_index
agg = CustomerAggregator()
agg.load_customers()
build_index(agg)
print('FAISS index built successfully.')
"
```

The index will be saved to `backend/data/faiss_index/` (configurable via
`FAISS_INDEX_PATH` in `.env`).

---

## API Endpoints

### Customer & Accounts

| Method | Endpoint                        | Description                          |
|--------|---------------------------------|--------------------------------------|
| GET    | /api/customers                  | List all customers (summary)         |
| GET    | /api/customers/{id}             | Full 360° profile for one customer   |
| GET    | /api/customers/{id}/accounts    | All accounts for a customer          |
| GET    | /api/customers/{id}/loans       | All loans for a customer             |
| GET    | /api/customers/{id}/wealth      | All wealth holdings for a customer   |
| GET    | /api/customers/{id}/kyc         | KYC details for a customer           |

### Semantic Search

| Method | Endpoint                        | Description                          |
|--------|---------------------------------|--------------------------------------|
| POST   | /api/search                     | Semantic search over customer corpus |

### Document Processing

| Method | Endpoint                        | Description                          |
|--------|---------------------------------|--------------------------------------|
| POST   | /api/documents/extract          | Upload & extract structured data     |

### Chat / Agent

| Method | Endpoint                        | Description                          |
|--------|---------------------------------|--------------------------------------|
| POST   | /api/chat                       | SSE streaming chat with LangGraph    |

### Financial Simulator

| Method | Endpoint                        | Description                                          |
|--------|---------------------------------|------------------------------------------------------|
| POST   | /api/simulate/emi               | EMI + amortisation schedule (reducing balance)       |
| POST   | /api/simulate/fd                | FD maturity amount, effective yield, TDS projection  |
| POST   | /api/simulate/loan-scenario     | Compare two loan options side-by-side                |

### Proactive Alerts

| Method | Endpoint                        | Description                          |
|--------|---------------------------------|--------------------------------------|
| GET    | /api/alerts                     | All active alerts (sorted by severity)|
| GET    | /api/alerts/{alert_id}          | Single alert by ID                   |
| GET    | /api/alerts/customer/{cust_id}  | All alerts for a specific customer   |

### System

| Method | Endpoint                        | Description                          |
|--------|---------------------------------|--------------------------------------|
| GET    | /health                         | Health check + config summary        |
| GET    | /docs                           | Swagger UI                           |
| GET    | /redoc                          | ReDoc documentation                  |

---

## Environment Variables

All environment variables live in `.env` (copy from `.env.example`).

| Variable              | Default                      | Description                                             |
|-----------------------|------------------------------|---------------------------------------------------------|
| OLLAMA_BASE_URL       | http://localhost:11434       | Ollama API base URL                                     |
| OLLAMA_CHAT_MODEL     | llama3.1:8b                  | Model used for chat, agents, and RAG                    |
| OLLAMA_VISION_MODEL   | llava:13b                    | Model used for document/image extraction                |
| OLLAMA_EMBED_MODEL    | nomic-embed-text             | Model used for generating semantic embeddings           |
| OLLAMA_NUM_CTX        | 8192                         | Context window size (tokens) for LLM calls              |
| FAISS_INDEX_PATH      | ./data/faiss_index           | Directory path for the FAISS index files                |
| CORS_ORIGINS          | http://localhost:5173        | Allowed CORS origins (comma-separated for multiple)     |
| DATABASE_URL          | sqlite:///./data/custiq.db   | SQLAlchemy-compatible DB URL (SQLite default)           |
| ALERT_CHECK_INTERVAL  | 86400                        | Alert engine background check interval in seconds       |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User (Browser)                              │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTP / WebSocket
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Nginx (port 5173 → 80)                         │
│  Static files: /usr/share/nginx/html  (React SPA build)             │
│  Reverse proxy: /api  →  backend:8000                               │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTP
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (port 8000)                       │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐   │
│  │ customer_    │  │ search_      │  │ chat_routes            │   │
│  │ routes       │  │ routes       │  │ (SSE streaming)        │   │
│  └──────────────┘  └──────────────┘  └────────────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐   │
│  │ document_    │  │ simulator_   │  │ alert_routes           │   │
│  │ routes       │  │ routes       │  │                        │   │
│  └──────────────┘  └──────────────┘  └────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Services Layer                           │   │
│  │  CustomerAggregator │ AlertEngine │ Recommender │ Compliance│   │
│  │  QueryEngine (RAG)  │ DocumentProcessor                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  LangGraph Agent Graph                      │   │
│  │  Router → [SearchAgent | RecommendAgent | ComplianceAgent   │   │
│  │           | AlertAgent | DocumentAgent]                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌────────────────────────┐   ┌─────────────────────────────┐     │
│  │  FAISS Vector Index    │   │   SQLite / JSON seed data   │     │
│  │  (nomic-embed-text)    │   │   (data/customers.json)     │     │
│  └────────────────────────┘   └─────────────────────────────┘     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTP (Ollama REST API)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Ollama (port 11434)                             │
│                                                                     │
│   ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│   │  llama3.1:8b    │  │   llava:13b       │  │ nomic-embed-    │  │
│   │  (chat / RAG)   │  │   (vision / OCR)  │  │ text (embed)    │  │
│   └─────────────────┘  └──────────────────┘  └─────────────────┘  │
│                                                                     │
│   Volume: ollama_data:/root/.ollama  (model weights persisted)      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Ollama Not Running

**Symptom:** Backend returns `ConnectionRefusedError` or `httpx.ConnectError` on any
LLM-powered endpoint (chat, search, document extraction).

**Fix:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve

# In Docker Compose, verify the ollama service is healthy
docker compose ps
# The ollama service should show "healthy" under Status
```

---

### Slow Responses / Timeouts

**Symptom:** Chat responses take > 60 seconds; frontend shows timeout errors.

**Possible causes and fixes:**

1. **Model too large for available RAM/VRAM:**
   Switch to a smaller model by updating `.env`:
   ```
   OLLAMA_CHAT_MODEL=llama3.2:3b
   ```

2. **Context window too large:**
   Reduce `OLLAMA_NUM_CTX` in `.env`:
   ```
   OLLAMA_NUM_CTX=4096
   ```

3. **No GPU acceleration:**
   Ollama auto-detects CUDA / Metal. Verify with:
   ```bash
   ollama run llama3.1:8b "say hello"
   # GPU usage should spike in Activity Monitor / nvidia-smi
   ```

4. **Docker resource limits:**
   Increase Docker Desktop memory allocation to at least 12 GB
   (Settings → Resources → Memory).

---

### FAISS Index Not Found

**Symptom:** Semantic search returns `{"detail": "FAISS index not initialised"}` or
similar, even though Ollama is running.

**Fix:**
```bash
# Ensure the backend is running, then rebuild the index
cd backend
source .venv/bin/activate
python -c "
from services.aggregator import CustomerAggregator
from rag.indexer import build_index
agg = CustomerAggregator()
agg.load_customers()
build_index(agg)
print('Done.')
"

# In Docker, exec into the running container
docker compose exec backend python -c "
from services.aggregator import CustomerAggregator
from rag.indexer import build_index
agg = CustomerAggregator()
agg.load_customers()
build_index(agg)
print('Done.')
"
```

Verify the index files exist:
```bash
ls backend/data/faiss_index/
# index.faiss   index.pkl
```

---

### Frontend Shows Blank Page After Docker Build

**Symptom:** `http://localhost:5173` loads but the page is empty or shows Nginx default.

**Fix:**
```bash
# Rebuild the frontend image (clears the build cache)
docker compose build --no-cache frontend
docker compose up frontend

# Verify the dist/ folder was created
docker compose exec frontend ls /usr/share/nginx/html
# index.html   assets/   ...
```

---

### CORS Errors in Browser Console

**Symptom:** Browser console shows `Access-Control-Allow-Origin` errors when the
frontend calls `/api/...`.

**Fix:** Check that `CORS_ORIGINS` in your `.env` (or Docker Compose environment
block) exactly matches the origin the browser uses:

```
# .env
CORS_ORIGINS=http://localhost:5173

# For production, replace with your actual domain
CORS_ORIGINS=https://custiq.example.com
```

Restart the backend after any `.env` change.

---

## Project Structure

```
custiq-360/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── customer_routes.py
│   │   ├── search_routes.py
│   │   ├── document_routes.py
│   │   ├── chat_routes.py
│   │   ├── simulator_routes.py      # Phase 5/6 — financial simulator
│   │   └── alert_routes.py          # Phase 5/6 — proactive alerts REST
│   ├── agents/
│   │   ├── graph.py
│   │   ├── prompts.py
│   │   ├── router.py
│   │   └── tools.py
│   ├── document_processing/
│   ├── models/
│   ├── rag/
│   ├── services/
│   │   ├── aggregator.py
│   │   ├── alerts.py
│   │   ├── compliance.py
│   │   ├── query_engine.py
│   │   └── recommender.py
│   ├── data/
│   │   ├── customers.json
│   │   └── faiss_index/             # generated — not committed to git
│   ├── config.py
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── nginx.conf                   # Phase 6 — Nginx config for container
│   └── Dockerfile                   # Phase 6 — multi-stage frontend build
├── docker-compose.yml               # Phase 6 — full stack orchestration
├── .env.example
└── README.md
```

---

## License

MIT — see LICENSE file for details.
