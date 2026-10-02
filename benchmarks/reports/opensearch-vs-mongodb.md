# ScoutGrid — Phase 4: MongoDB vs OpenSearch Search Benchmark Report

**Timestamp:** `2026-10-01T22:52:07.071960`  
**MongoDB Candidates:** `31,002`  
**OpenSearch Documents:** `31,002`  
**Warmup Iterations:** `10` | **Measured Iterations:** `50`  
**MongoDB Environment:** `Local MongoDB (localhost:27017)`  
**OpenSearch Environment:** `Aiven OpenSearch Cloud Service (HTTPS)`  

## 1. Candidate Search Latency (Page 1, Limit 20)

| Query ID | Category | Query String | Mongo Matched | OS Matched | Mongo p50 (ms) | Mongo p95 (ms) | OS p50 (ms) | OS p95 (ms) | OS Raw Engine p95 (ms) |
|---|---|---|---|---|---|---|---|---|---|
| Q1 | Skill | `Python developers` | 4,663 | 4,663 | 69.591 | 76.783 | 60.944 | 70.581 | **64.865** |
| Q2 | Skill + Location | `Python developers in Bangalore` | 573 | 573 | 82.754 | 90.777 | 59.339 | 65.576 | **62.648** |
| Q3 | Multiple Skills | `Python FastAPI developers` | 2,723 | 2,723 | 38.863 | 46.916 | 58.832 | 65.434 | **71.233** |
| Q4 | Skill + Experience | `Python backend engineers with 3+ years of experience` | 196 | 5,168 | 155.898 | 180.093 | 59.636 | 65.756 | **65.681** |
| Q5 | Skill + Location + Experience | `Python backend engineers with 3+ years of experience in Bangalore` | 27 | 638 | 99.845 | 111.3 | 59.644 | 177.219 | **67.155** |
| Q6 | Different Technology | `React developers with 2+ years of experience` | 2,043 | 2,043 | 56.715 | 60.509 | 58.599 | 63.009 | **67.39** |
| Q7 | Historical Title | `software engineers with 4+ years of experience` | 7,615 | 8,630 | 117.908 | 126.228 | 58.823 | 68.121 | **66.644** |
| Q8 | Low-Result Query | `Rust developers with 10+ years of experience in Hyderabad` | 439 | 439 | 56.414 | 61.85 | 57.719 | 65.652 | **71.212** |


## 2. Offset Pagination Latency Depth Scaling (Query Q1)

| Page Depth | Limit | Mongo p50 (ms) | Mongo p95 (ms) | OpenSearch p50 (ms) | OpenSearch p95 (ms) |
|---|---|---|---|---|---|
| Page 1 | 20 | 70.747 | 73.35 | 56.879 | 63.907 |
| Page 10 | 20 | 72.044 | 81.842 | 57.535 | 81.961 |
| Page 100 | 20 | 110.404 | 222.945 | 62.831 | 111.54 |

