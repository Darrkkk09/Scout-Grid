# ScoutGrid — Distributed AI Candidate Sourcing Platform

ScoutGrid is a high-performance, distributed candidate sourcing platform engineered to process natural-language talent acquisition queries across 100,000+ candidate profiles.

It features an autonomous **4-Agent Multi-Agent System (MAS)** for query expansion, search coordination, fit auditing, and candidate engagement outreach, backed by **Redis caching**, an indexed **MongoDB** source-of-truth database, and an **Aiven OpenSearch** read model (BM25 + k-NN Lucene vectors with Reciprocal Rank Fusion).

---

## 🏗️ Architecture Overview

```text
                               Frontend (React + Vite + Tailwind)
                                              │
                                              │ POST /agents/sourcing
                                              ▼
                                 FastAPI Backend (Python 3.11)
                                              │
                                              ▼
                                 Supervisor Orchestrator Agent
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
         Query Expansion Agent     Candidate Verifier Agent      Outreach Draft Agent
         (Tech Skill Graph)        (Fit Scoring & Audit)         (Tailored Drafts)
                    │                         │                         │
                    ▼                         │                         │
            Search Coordinator                │                         │
                    │                         │                         │
         ┌──────────┴──────────┐              │                         │
         ▼                     ▼              │                         │
   Aiven OpenSearch        MongoDB            │                         │
 (BM25 + Vector RRF)      (Fallback)          │                         │
         │                     │              │                         │
         └──────────┬──────────┘              │                         │
                    │                         │                         │
                    ▼                         ▼                         ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │                          Redis Caching                           │
        │      scoutgrid:search:* | scoutgrid:agent:* | scoutgrid:user:*   │
        └──────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
                                 Frontend Dashboard Response
```

* **Multi-Agent System (MAS)**: 4 specialized agents working in sync:
  1. **QueryExpansionAgent**: Skill graph term expansion (`Python` $\rightarrow$ `FastAPI, Django, PyTest`).
  2. **SearchCoordinator**: Unified retriever querying OpenSearch Hybrid (BM25 + Vector RRF) with MongoDB fallback.
  3. **CandidateVerifierAgent**: Profile audit engine computing fit scores (0–100%), skill matches, experience suitability, strengths, and gap analysis.
  4. **OutreachAgent**: Personalized recruiter email / InMail draft generator (`professional`, `casual`, `technical` tones).
* **Redis Caching Layer**: Async Redis client providing sub-10ms cache hits for search results (`scoutgrid:search:{hash}`), agent responses (`scoutgrid:agent:{hash}`), and recent user queries with graceful fallback on Redis error.
* **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons, interactive candidate cards with fit score badges, strengths/gaps breakdowns, and copyable outreach drafts.
* **Backend**: FastAPI (Python 3.11), Pydantic v2, Motor (Async MongoDB), OpenSearch-Py, Redis-Py.
* **Database**: MongoDB 7.0 (Source of Truth).
* **Search Read Model**: Aiven OpenSearch Cloud Service with Lucene k-NN vector engine (`type: knn_vector`, `dimension: 384`, `space_type: cosinesimil`).
* **Requirement Understanding**: Dual-layer **Gemini LLM** requirement extractor with structured JSON output validation, rate limit key rotation, and deterministic rule-based fallback.

---

## 📁 Project Structure

```text
scout-grid/
├── backend/
│   ├── agents/
│   │   ├── __init__.py                 # Agents package exports
│   │   ├── query_expansion_agent.py    # Tech skill graph & query taxonomy expansion
│   │   ├── candidate_verifier_agent.py  # Candidate fit auditing & gap analysis
│   │   ├── outreach_agent.py           # Tailored recruiter email draft generator
│   │   └── supervisor_agent.py         # Multi-agent sourcing pipeline orchestrator
│   ├── models/
│   │   ├── candidate.py                # Pydantic schemas for candidate profiles & experience
│   │   └── search.py                   # Search request/response models & pagination schemas
│   ├── routes/
│   │   ├── agents.py                   # POST /agents/sourcing multi-agent endpoint
│   │   ├── analytics.py                # GET /analytics/dashboard overview metrics
│   │   ├── candidates.py               # Candidate CRUD operations
│   │   └── search.py                   # Dual MongoDB & OpenSearch routes
│   ├── services/
│   │   ├── cache_service.py            # Redis async caching layer & TTL manager
│   │   ├── search_coordinator.py       # Unified OpenSearch & MongoDB retriever
│   │   ├── candidate_service.py        # Candidate database operations
│   │   ├── hybrid_requirement_extractor.py # LLM-first requirement extractor with fallback
│   │   ├── embedding_service.py        # Vector embedding provider
│   │   ├── search_service.py            # MongoDB search service (Offset + Cursor pagination)
│   │   ├── opensearch_client.py        # OpenSearch client factory & SSL setup
│   │   ├── opensearch_index.py         # OpenSearch mapping definition
│   │   └── opensearch_search_service.py # OpenSearch BM25, k-NN vector & RRF Hybrid search
│   ├── tests/                          # 76 backend unit & integration tests
│   ├── database.py                     # MongoDB connection & index initialization
│   ├── main.py                         # FastAPI application entry point & router registration
│   ├── pytest.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                           # React + Vite + Tailwind UI
│   ├── src/
│   │   ├── components/candidates/      # CandidateCard with fit scores & outreach preview
│   │   ├── pages/Candidates.jsx        # AI Multi-Agent Sourcing search page
│   │   └── services/api.js             # Axios client for REST & MAS endpoints
├── scripts/                            # Dataset generators, indexers & benchmarks
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone Repository & Setup Environment

```bash
git clone https://github.com/Darrkkk09/Scout-Grid.git
cd Scout-Grid
```

Copy `.env.example` to `.env` in the `backend/` or root folder:

```env
# Database & Redis
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=scoutgrid
REDIS_URL=redis://localhost:6379/0
SEARCH_CACHE_TTL=600
AGENT_CACHE_TTL=1800

# OpenSearch (Optional Cloud Service)
OPENSEARCH_HOST=your-opensearch-host.aivencloud.com
OPENSEARCH_PORT=25708
OPENSEARCH_USERNAME=vn
OPENSEARCH_PASSWORD=your_password

# LLM Requirement Extractor (Gemini Defaults)
LLM_PROVIDER=gemini
GEMINI_API_KEY_1=your_api_key_1
```

### 2. Local Redis & Backend Setup

Start Redis server locally:
```bash
wsl sudo service redis-server start
```

Start the FastAPI backend server:
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

FastAPI server runs at **http://localhost:8000** (Swagger documentation at `/docs`).

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend application runs at **http://localhost:5173**.

---

## ⚡ API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/agents/sourcing` | Triggers 4-Agent Sourcing Pipeline (Query Expansion, Hybrid Retrieval, Fit Audit & Outreach) |
| `POST` | `/search/opensearch?rank=true` | Candidate search via **OpenSearch** (`bm25`, `vector`, `hybrid`) |
| `POST` | `/search` | Natural language candidate search via **MongoDB** |
| `GET` | `/candidates` | List candidates with pagination & filter query params |
| `GET` | `/candidates/{id}` | Retrieve candidate profile by ID |
| `GET` | `/analytics/dashboard` | Overview dashboard analytics |
| `GET` | `/health` | Service health status |

### Example Multi-Agent Sourcing Request

```json
POST /agents/sourcing
{
  "query": "Senior Python backend engineers in Bangalore with 3+ years experience in FastAPI and microservices",
  "generate_outreach": true,
  "outreach_tone": "professional",
  "top_k": 10
}
```

---

## 🧪 Testing

Run pytest across all **76 unit and integration tests**:

```bash
python -m pytest backend/tests -v
```

---

## 📜 License

MIT License. Built for ScoutGrid.
