# ScoutGrid — Distributed AI Candidate Sourcing Platform

ScoutGrid is a high-performance, distributed candidate sourcing system engineered to handle natural-language talent acquisition queries over tens of thousands of candidate profiles. 

It provides dual search engines — an indexed **MongoDB** source-of-truth service and a sidecar **Aiven OpenSearch** read model — complete with deterministic natural language requirement extraction, custom benchmarking, and a React + Vite + Tailwind frontend.

---

## 🏗️ Architecture Overview

```text
                               ┌──────────────────────────┐
                               │   React + Vite Frontend  │
                               └────────────┬─────────────┘
                                            │ HTTP
                               ┌────────────▼─────────────┐
                               │   FastAPI Search Engine  │
                               └────────────┬─────────────┘
                                            │
                             Parsed Requirements Extraction
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    │                                               │
                    ▼                                               ▼
     ┌──────────────────────────────┐                ┌──────────────────────────────┐
     │   MongoDB Candidates Store   │                │   Aiven OpenSearch Engine    │
     │      (Source of Truth)       │──(Sync Bulk)──>│     (Search Read Model)      │
     └──────────────────────────────┘                └──────────────────────────────┘
```

* **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons.
* **Backend**: FastAPI (Python 3.11), Pydantic v2, Motor (Async MongoDB), OpenSearch-Py.
* **Database**: MongoDB 7.0 (Source of Truth).
* **Search Engine**: Aiven OpenSearch Cloud Service (Sidecar Search Read Model).
* **NLP Extractor**: Rule-based deterministic requirement extractor parsing skills, location, experience range, and job roles.

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
│   │       ├── requirement_extractor.py# Natural language query requirement parser
│   │       ├── search_service.py        # MongoDB search service (Offset + Cursor pagination)
│   │       ├── opensearch_client.py    # Aiven OpenSearch client factory & SSL setup
│   │       ├── opensearch_index.py     # OpenSearch mapping definition & candidate transformers
│   │       └── opensearch_search_service.py # OpenSearch structured bool query engine
│   ├── tests/                          # Full pytest test suite (40 unit & integration tests)
│   ├── pytest.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                           # React + Vite + Tailwind UI
├── scripts/
│   ├── generate_candidates.py          # Synthetic candidate dataset generator (31k+ profiles)
│   ├── create_opensearch_index.py      # Idempotent OpenSearch candidate index creator
│   ├── index_candidates.py             # Bulk indexer for MongoDB -> OpenSearch sync
│   ├── verify_opensearch_candidates.py # OpenSearch index status & document count validator
│   ├── compare_search.py               # Accuracy comparison between MongoDB and OpenSearch
│   └── benchmark_opensearch_vs_mongo.py# Controlled latency benchmark suite (JSON + MD reports)
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
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=scoutgrid

OPENSEARCH_HOST=your-opensearch-host.aivencloud.com
OPENSEARCH_PORT=25708
OPENSEARCH_USERNAME=vn
OPENSEARCH_PASSWORD=your_password
OPENSEARCH_SERVICE_URI=https://vn:your_password@your-opensearch-host.aivencloud.com:25708
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

## 📊 Distributed OpenSearch & Benchmark Tools

### Seed Candidate Dataset

Generate 30,000+ synthetic candidate profiles directly into MongoDB:

```bash
python scripts/generate_candidates.py --count 30000
```

### Index Candidates into OpenSearch

Sync candidates from MongoDB to Aiven OpenSearch using the bulk API:

```bash
python scripts/index_candidates.py --limit 31002
```

### Verify Index Status & Search Parity

```bash
# Verify document count and field mappings
python scripts/verify_opensearch_candidates.py

# Compare MongoDB vs OpenSearch matching result sets
python scripts/compare_search.py
```

### Execute Benchmark Suite

Run controlled latency benchmarks (10 warmup, 50 measured iterations):

```bash
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
| `POST` | `/search/opensearch` | Natural language candidate search via **OpenSearch** |

### Example Natural Language Search Payload

```json
POST /search/opensearch
{
  "query": "Python backend engineers with 3+ years of experience in Bangalore",
  "page": 1,
  "limit": 20
}
```

---

## 🧪 Testing

Run pytest across all backend unit and integration tests:

```bash
python -m pytest backend/tests -v
```

---

## 📜 License

MIT License. Built for ScoutGrid.
