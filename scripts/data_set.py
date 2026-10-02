"""
Data import script for ScoutGrid.

Loads the synthetic candidate matching dataset from Hugging Face ("michaelozon/candidate-matching-synthetic", "resumes")
and bulk-inserts the mapped records into MongoDB using the Candidate schema.

Usage:
    d:\scout-grid\.venv\Scripts\python.exe scripts/data_set.py
"""

import os
from typing import Any, List

from datasets import load_dataset
from dotenv import load_dotenv
from pymongo import MongoClient

# ---------------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------------
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "scoutgrid")


def map_record(record: dict) -> dict:
    """
    Maps raw record fields from Hugging Face ('michaelozon/candidate-matching-synthetic'):
      - resume_id -> used to seed deterministic name/email
      - role + industry -> experience title / summary
      - years_experience -> experience_years
      - skills -> list[str]
      - education -> education
      - experience_bullets -> experience entries
    """
    resume_id = str(record.get("resume_id") or "000000").replace("R_", "")
    try:
        id_num = int(resume_id)
    except ValueError:
        id_num = hash(resume_id) % 100000

    first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Pat", "Riley", "Aarav", "Priya", "Ananya", "Rohan"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Sharma", "Verma", "Patel"]
    
    first = first_names[id_num % len(first_names)]
    last = last_names[(id_num // len(first_names)) % len(last_names)]
    name = f"{first} {last}"
    email = f"{first.lower()}.{last.lower()}{id_num}@example.com"

    locations = ["Bangalore", "Hyderabad", "Chennai", "Mumbai", "Pune", "Delhi", "Remote", "San Francisco", "New York"]
    location = locations[id_num % len(locations)]

    try:
        exp_years = float(record.get("years_experience", 0))
    except (ValueError, TypeError):
        exp_years = 0.0

    skills_raw = record.get("skills", [])
    if hasattr(skills_raw, "tolist"):
        skills = [str(s) for s in skills_raw.tolist()]
    elif isinstance(skills_raw, list):
        skills = [str(s) for s in skills_raw]
    elif isinstance(skills_raw, str):
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
    else:
        skills = ["Software Engineering"]

    edu_degree = str(record.get("education") or "BSc")
    industry = str(record.get("industry") or "Tech")
    role = str(record.get("role") or "Software Engineer")
    education = f"{edu_degree} in Computer Science ({industry})"

    bullets_raw = record.get("experience_bullets", [])
    if hasattr(bullets_raw, "tolist"):
        bullets = [str(b) for b in bullets_raw.tolist()]
    elif isinstance(bullets_raw, list):
        bullets = [str(b) for b in bullets_raw]
    else:
        bullets = [str(record.get("summary") or "Delivered software features and solutions.")]

    summary = str(record.get("summary") or "")

    cleaned_experience = []
    if bullets:
        cleaned_experience.append({
            "company": f"{industry} Dynamics",
            "title": f"{record.get('seniority', '')} {role}".strip(),
            "start_date": "2020-01-01",
            "end_date": None,
            "description": " | ".join(bullets) if len(bullets) <= 3 else " | ".join(bullets[:3]),
        })

    return {
        "name": name,
        "email": email,
        "location": location,
        "experience_years": exp_years,
        "skills": skills,
        "education": education,
        "experience": cleaned_experience,
    }



def main() -> None:
    print("Loading 'michaelozon/candidate-matching-synthetic' from Hugging Face...")
    resumes = load_dataset(
        "michaelozon/candidate-matching-synthetic",
        split="resumes"
    )

    df = resumes.to_pandas()
    print(f"Loaded {len(df)} candidates from Hugging Face.")
    print("Columns available:", list(df.columns))
    if len(df) > 0:
        print("\nSample raw record keys and values:")
        for k, v in df.iloc[0].to_dict().items():
            print(f"  {k}: {repr(v)[:100]}")



    records = [map_record(rec) for rec in df.to_dict(orient="records")]

    print(f"Connecting to MongoDB at {MONGODB_URI} / database: {MONGODB_DATABASE}...")
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]
    collection = db["candidates"]

    batch_size = 500
    total = len(records)
    inserted = 0

    print(f"Inserting {total} candidates into 'candidates' collection...")
    for start in range(0, total, batch_size):
        batch = records[start : start + batch_size]
        result = collection.insert_many(batch, ordered=False)
        inserted += len(result.inserted_ids)
        pct = (inserted / total) * 100
        print(f"  Inserted {inserted}/{total} ({pct:.1f}%)", end="\r", flush=True)

    print(f"\nDone! Successfully imported {inserted} candidates into MongoDB.")
    client.close()


if __name__ == "__main__":
    main()
