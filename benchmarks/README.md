# ScoutGrid — Phase 3: MongoDB Search Benchmark Suite

This directory contains the benchmarking tools, machine-readable JSON results, and human-readable performance reports for **ScoutGrid Phase 3**.

---

## Overview

The benchmark framework measures the current MongoDB search engine without altering production application code or data.

All benchmark runs operate against a dedicated collection (`candidates_benchmark`) to protect production development data in `candidates`.

---

## Running Benchmarks

### 1. Prerequisites

Ensure MongoDB is running locally or configured via `.env` / `MONGODB_URI`:

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=scoutgrid
```

### 2. Small Benchmark (500 candidates)

Quick run for development verification and CI:

```bash
python scripts/benchmark_search.py --count 500 --warmup 2 --iterations 10
```

### 3. Medium Benchmark (10,000 candidates)

Standard benchmark evaluation size:

```bash
python scripts/benchmark_search.py --count 10000 --warmup 5 --iterations 50
```

### 4. Large Benchmark (100,000 candidates)

Scale testing:

```bash
python scripts/benchmark_search.py --count 100000 --warmup 5 --iterations 50
```

### 5. Reset Dataset

To drop and re-seed the benchmark collection:

```bash
python scripts/benchmark_search.py --count 10000 --reset
```

---

## CLI Options

| Flag | Default | Description |
|---|---|---|
| `--count` | `10000` | Target candidate document count in benchmark collection |
| `--warmup` | `5` | Warmup request iterations before timing |
| `--iterations` | `50` | Measured request iterations per query |
| `--collection` | `candidates_benchmark` | Benchmark collection name in MongoDB |
| `--reset` | `False` | Reset (drop & re-seed) benchmark collection |
| `--output-json` | `benchmarks/results/mongodb_benchmark.json` | Destination path for JSON results |
| `--output-report` | `benchmarks/reports/mongodb-search-benchmark.md` | Destination path for Markdown report |

---

## Metrics & Percentiles

* **NLP Extraction Time**: Time spent parsing natural language query into structured criteria via `RequirementExtractor`.
* **`count_documents` Time**: Time taken by MongoDB to count total matching documents.
* **`find` Time**: Time spent fetching page batch (`find().skip().limit()`).
* **Percentiles (p50 / p95 / p99)**:
  * `p50` (Median): Typical latency experienced by 50% of requests.
  * `p95`: 95% of requests complete faster than this value.
  * `p99`: Tail latency boundary (worst 1% of requests).

---

## Directory Structure

```text
benchmarks/
├── README.md               # Benchmark user guide (this file)
├── results/
│   └── mongodb_benchmark.json   # Machine-readable output data
└── reports/
    └── mongodb-search-benchmark.md # Formatted Markdown performance report
```
