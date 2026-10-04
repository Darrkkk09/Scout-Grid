# ScoutGrid — Distributed AI Candidate Sourcing Platform

ScoutGrid is a high-performance, distributed candidate sourcing system engineered to handle natural-language talent acquisition queries over tens of thousands of candidate profiles. 

It provides dual search engines — an indexed **MongoDB** source-of-truth service and a sidecar **Aiven OpenSearch** read model — complete with LLM-first natural language requirement extraction with deterministic fallbacks, hybrid semantic vector search (BM25 + k-NN Lucene vectors with Reciprocal Rank Fusion), custom benchmarking, and a React + Vite + Tailwind frontend.

---

## 🏗️ Architecture Overview

```text
                               Recruiter Query
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │ Hybrid Requirement        │
                        │ Extractor (LLM + Fallback)│
                        └─────────────┬─────────────┘
                                      │
                             ParsedRequirements
                                      │
                     ┌────────────────┴────────────────┐
                     │                                 │
                     ▼                                 ▼
             ┌───────────────┐                 ┌───────────────┐
             │  BM25 Search  │                 │ Vector Search │
             └───────┬───────┘                 └───────┬───────┘
                     │                                 │
                     └────────────────┬────────────────┘
                                      │
                                      ▼
                           Reciprocal Rank Fusion (RRF)
                                      │
                                      ▼
                           Aiven OpenSearch / MongoDB
```

* **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons.
* **Backend**: FastAPI (Python 3.11), Pydantic v2, Motor (Async MongoDB), OpenSearch-Py.
* **Database**: MongoDB 7.0 (Source of Truth).
* **Search Read Model**: Aiven OpenSearch Cloud Service with Lucene k-NN vector engine (`type: knn_vector`, `dimension: 384`, `space_type: cosinesimil`).
* **Requirement Understanding**: Dual-layer **Gemini LLM** requirement extractor with structured JSON output validation, rate limit key rotation (up to 5 API keys), retry backoffs, and deterministic rule-based fallback.
* **Search Engine**: **Hybrid Semantic Search** fusing BM25 keyword matching and k-NN vector search using Reciprocal Rank Fusion ($k=60$).

---

## 📁 Project Structure

```text
scout-grid/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application entry point & lifespan hooks
│   │   ├── database.py                 # MongoDB connection & index initialization
│   │   ├── models/
│   │   │   ├── candidate.py            # Pydantic schemas for candidate creation/responses
│   │   │   └── search.py               # Search request/response models & pagination schemas
│   │   ├── routes/
│   │   │   ├── candidates.py           # REST endpoints for candidate CRUD operations
│   │   │   └── search.py               # Dual POST /search (MongoDB) & POST /search/opensearch routes
│   │   └── services/
│   │       ├── candidate_service.py    # Candidate database operations
│   │       ├── requirement_extractor.py# Deterministic rule-based requirement extractor
│   │       ├── llm_requirement_extractor.py # Multi-key Gemini LLM requirement extractor
│   │       ├── requirement_validator.py# Pydantic & domain validator for LLM output
│   │       ├── hybrid_requirement_extractor.py # LLM-first requirement extractor with fallback
│   │       ├── embedding_service.py    # Embedding provider (Gemini / OpenAI / Local fallback)
│   │       ├── search_service.py        # MongoDB search service (Offset + Cursor pagination)
│   │       ├── opensearch_client.py    # Aiven OpenSearch client factory & SSL setup
│   │       ├── opensearch_index.py     # OpenSearch mapping definition (BM25 + k-NN vectors)
│   │       └── opensearch_search_service.py # OpenSearch BM25, k-NN vector & RRF Hybrid search
│   ├── tests/                          # Full pytest test suite (55 unit & integration tests)
│   ├── pytest.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                           # React + Vite + Tailwind UI
├── scripts/
│   ├── generate_candidates.py          # Synthetic candidate dataset generator (31k+ profiles)
│   ├── create_opensearch_index.py      # Idempotent OpenSearch candidate index creator
│   ├── index_candidates.py             # Bulk indexer for MongoDB -> OpenSearch sync
│   ├── index_candidate_embeddings.py   # Vector embedding generator & bulk OpenSearch indexer
│   ├── reindex_opensearch.py           # Safe versioned index reindexing utility
│   ├── verify_opensearch_candidates.py # OpenSearch index status & document count validator
│   ├── compare_search.py               # Accuracy comparison between MongoDB and OpenSearch
│   ├── benchmark_opensearch_vs_mongo.py# Controlled latency benchmark suite (JSON + MD reports)
│   ├── benchmark_requirement_extraction.py # Benchmark suite for rule vs LLM extraction
│   ├── benchmark_hybrid_search.py      # Latency & overlap benchmarks for BM25 vs Vector vs Hybrid RRF
│   └── evaluate_search_quality.py      # Quality evaluation suite (Precision@10, Recall@10, Hit@10)
├── benchmarks/
│   ├── reports/                        # Markdown benchmark & bottleneck analysis reports
│   └── results/                        # Machine-readable benchmark JSON exports
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

Copy `.env.example` to `.env` in the `backend/` or root folder and populate environment credentials:

```env
# Database & OpenSearch
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=scoutgrid
OPENSEARCH_HOST=your-opensearch-host.aivencloud.com
OPENSEARCH_PORT=25708
OPENSEARCH_USERNAME=vn
OPENSEARCH_PASSWORD=your_password
OPENSEARCH_SERVICE_URI=https://vn:your_password@your-opensearch-host.aivencloud.com:25708

# LLM Requirement Extractor (Gemini 2.5 Defaults)
LLM_PROVIDER=gemini
LLM_MODELS=gemini-2.5-flash-lite,gemini-2.5-flash
LLM_TIMEOUT_SECONDS=2.5
LLM_MAX_ATTEMPTS=3

# Multi-Key Gemini API Credentials (Up to 5 Keys)
GEMINI_API_KEY_1=your_api_key_1
GEMINI_API_KEY_2=your_api_key_2

# Embedding & Hybrid Semantic Search Configuration
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=text-embedding-004
EMBEDDING_DIMENSION=384
HYBRID_RRF_K=60
HYBRID_CANDIDATE_MULTIPLIER=5
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -r backend/requirements.txt

# Start FastAPI server
uvicorn app.main:app --reload --app-dir backend --port 8000
```

FastAPI server runs at **http://localhost:8000** (Swagger docs at `/docs`).

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend app runs at **http://localhost:5173**.

---

## 📊 Distributed OpenSearch, Vector Indexing & Benchmarks

### Seed Candidate Dataset

Generate 30,000+ synthetic candidate profiles directly into MongoDB:

```bash
python scripts/generate_candidates.py --count 30000
```

### Index Candidates with Vector Embeddings into OpenSearch

Generate vector embeddings and bulk index candidates into Aiven OpenSearch:

```bash
python scripts/index_candidate_embeddings.py
```

### Verify Index Status & Search Parity

```bash
# Verify document count and field mappings
python scripts/verify_opensearch_candidates.py

# Compare MongoDB vs OpenSearch matching result sets
python scripts/compare_search.py
```

### Run Benchmarks & Quality Evaluation

```bash
# Benchmark BM25 vs Vector vs Hybrid RRF latency and overlap
python scripts/benchmark_hybrid_search.py

# Evaluate Search Quality (Precision@10, Recall@10, Hit@10)
python scripts/evaluate_search_quality.py

# Latency benchmark suite (MongoDB vs OpenSearch)
python scripts/benchmark_opensearch_vs_mongo.py --warmup 10 --iterations 50
```

Reports are automatically generated under `benchmarks/reports/`:
* `opensearch-vs-mongodb.md`: Latency summary table & pagination depth comparisons.
* `opensearch-vs-mongodb-analysis.md`: In-depth bottleneck analysis & architectural recommendations.

---

## ⚡ API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status |
| `POST` | `/candidates` | Create candidate profile |
| `GET` | `/candidates/{id}` | Retrieve candidate profile |
| `GET` | `/candidates` | List candidates with pagination & filter query params |
| `POST` | `/search` | Natural language candidate search via **MongoDB** |
| `POST` | `/search/opensearch?search_mode=hybrid` | Candidate search via **OpenSearch** (`bm25`, `vector`, `hybrid`) |

### Example Natural Language Hybrid Search Payload

```json
POST /search/opensearch?search_mode=hybrid
{
  "query": "Senior Python backend engineers in Bangalore with 3+ years experience who have worked on scalable microservices",
  "page": 1,
  "limit": 20
}
```

---

## 🧪 Testing

Run pytest across all 55 backend unit and integration tests:

```bash
python -m pytest backend/tests -v
```

---

## 📜 License

MIT License. Built for ScoutGrid.

