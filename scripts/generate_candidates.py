"""
Synthetic candidate generator for ScoutGrid.

Generates fictional candidate profiles and bulk-inserts them into MongoDB.
Does NOT scrape any external website.

Usage:
    python scripts/generate_candidates.py --count 10000
    python scripts/generate_candidates.py --count 500 --batch-size 200
"""

import argparse
import os
import random
import sys
from datetime import date, timedelta
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient

# ---------------------------------------------------------------------------
# Load .env from project root (one level up from scripts/)
# ---------------------------------------------------------------------------
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "scoutgrid")

# ---------------------------------------------------------------------------
# Data pools
# ---------------------------------------------------------------------------

FIRST_NAMES = [
    "Aarav", "Aditya", "Akash", "Amit", "Ananya", "Ankita", "Arjun", "Aryan",
    "Deepika", "Devansh", "Divya", "Gaurav", "Harsha", "Ishaan", "Ishita",
    "Karan", "Kavya", "Kunal", "Lakshmi", "Manish", "Meera", "Mihir", "Neha",
    "Nikhil", "Nisha", "Pooja", "Priya", "Rahul", "Raj", "Riya", "Rohan",
    "Sakshi", "Saniya", "Siddharth", "Sneha", "Souvik", "Srikanth", "Suresh",
    "Tanvi", "Varun", "Vikram", "Vipul", "Vishal", "Yash", "Zara",
]

LAST_NAMES = [
    "Agarwal", "Bhat", "Chakraborty", "Chandra", "Das", "Desai", "Dubey",
    "Ghosh", "Gupta", "Iyer", "Jain", "Joshi", "Kaur", "Khan", "Kumar",
    "Malhotra", "Mehta", "Mishra", "Nair", "Pandey", "Patel", "Pillai",
    "Rao", "Reddy", "Sharma", "Singh", "Sinha", "Srivastava", "Tiwari",
    "Varma", "Verma", "Yadav",
]

LOCATIONS = [
    "Bangalore", "Hyderabad", "Chennai", "Mumbai", "Pune",
    "Delhi", "Visakhapatnam", "Kolkata",
]

ALL_SKILLS = [
    "Python", "FastAPI", "Django", "Java", "Spring Boot",
    "JavaScript", "TypeScript", "React", "Node.js", "Express",
    "C++", "Go", "AWS", "Docker", "Kubernetes",
    "MongoDB", "PostgreSQL", "Redis", "Kafka",
]

SKILL_GROUPS: list[list[str]] = [
    ["Python", "FastAPI", "MongoDB", "Docker"],
    ["Python", "Django", "PostgreSQL", "AWS"],
    ["Java", "Spring Boot", "PostgreSQL", "Kafka"],
    ["JavaScript", "TypeScript", "React", "Node.js", "Express"],
    ["Go", "Docker", "Kubernetes", "AWS"],
    ["Python", "FastAPI", "Redis", "Kafka", "Docker"],
    ["C++", "Python", "AWS"],
    ["Java", "Kafka", "Redis", "Docker", "Kubernetes"],
    ["TypeScript", "React", "Node.js", "PostgreSQL"],
    ["Python", "MongoDB", "Redis", "FastAPI"],
]

EDUCATION_LEVELS = [
    "B.Tech Computer Science",
    "B.Tech Information Technology",
    "B.E. Computer Engineering",
    "M.Tech Computer Science",
    "M.S. Computer Science",
    "MCA",
    "BCA",
    "B.Sc Computer Science",
]

COMPANIES = [
    "Infosys", "Wipro", "TCS", "HCL Technologies", "Tech Mahindra",
    "Accenture India", "Capgemini India", "Cognizant", "Mphasis", "LTIMindtree",
    "Zoho", "Freshworks", "Paytm", "Swiggy", "Zomato", "Razorpay",
    "Ola", "Flipkart", "PhonePe", "Cred", "Meesho", "Unacademy",
    "BrowserStack", "Postman", "Hasura", "Druva", "Clevertap", "Exotel",
    "ThoughtWorks", "Sigmoid", "Delhivery", "Urban Company",
]

TITLES_BY_EXPERIENCE: dict[str, list[str]] = {
    "junior": [
        "Junior Software Engineer", "Software Engineer I", "Associate Engineer",
        "Trainee Developer", "Junior Backend Developer",
    ],
    "mid": [
        "Software Engineer", "Software Engineer II", "Backend Developer",
        "Full Stack Developer", "Platform Engineer",
    ],
    "senior": [
        "Senior Software Engineer", "Senior Backend Engineer",
        "Tech Lead", "Staff Engineer", "Principal Engineer",
    ],
}

JOB_DESCRIPTIONS = [
    "Designed and maintained RESTful APIs serving millions of requests per day.",
    "Improved database query performance by optimising indexes and query plans.",
    "Led the migration of monolithic services to microservices architecture.",
    "Built real-time data pipelines using Kafka and stream processing frameworks.",
    "Developed React-based dashboards used by internal analytics teams.",
    "Automated CI/CD pipelines using GitHub Actions and Docker.",
    "Implemented caching strategies with Redis to reduce API latency.",
    "Collaborated with data scientists to deploy ML models into production.",
    "Conducted code reviews and mentored junior engineers.",
    "Scaled the platform to handle 10x traffic growth during peak seasons.",
    "Integrated third-party payment gateways and compliance workflows.",
    "Built a distributed job scheduling system to handle background tasks.",
    "Wrote integration and unit tests to maintain >85% code coverage.",
    "Refactored legacy codebase to improve maintainability and test coverage.",
    "Designed relational database schemas for core product features.",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 0)))


def _pick_title(experience_years: float) -> str:
    if experience_years < 2:
        return random.choice(TITLES_BY_EXPERIENCE["junior"])
    if experience_years < 5:
        return random.choice(TITLES_BY_EXPERIENCE["mid"])
    return random.choice(TITLES_BY_EXPERIENCE["senior"])


def _build_experience(experience_years: float) -> list[dict[str, Any]]:
    """
    Build a plausible list of job experience entries that sums to roughly
    experience_years.
    """
    if experience_years < 0.5:
        return []

    entries: list[dict[str, Any]] = []
    today = date.today()
    remaining = experience_years
    current_end = today

    while remaining > 0.25:
        duration_years = min(random.uniform(0.5, 3.0), remaining)
        duration_days = int(duration_years * 365)
        start = current_end - timedelta(days=duration_days)

        entries.append({
            "company": random.choice(COMPANIES),
            "title": _pick_title(duration_years),
            "start_date": start.isoformat(),
            "end_date": current_end.isoformat() if current_end != today else None,
            "description": random.choice(JOB_DESCRIPTIONS),
        })

        # Small gap between jobs (0–30 days)
        gap = random.randint(0, 30)
        current_end = start - timedelta(days=gap)
        remaining -= duration_years

    entries.reverse()  # Chronological order
    return entries


def _build_skills() -> list[str]:
    base = random.choice(SKILL_GROUPS).copy()
    # Occasionally add 1-2 extra random skills
    extras = random.sample(ALL_SKILLS, k=random.randint(0, 2))
    combined = list(dict.fromkeys(base + extras))  # Deduplicate, preserve order
    return combined


def generate_candidate(index: int) -> dict[str, Any]:
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    name = f"{first} {last}"

    # Use index to guarantee unique emails even if name collision occurs
    email_local = f"{first.lower()}.{last.lower()}{index}"
    domain = random.choice(["gmail.com", "yahoo.com", "outlook.com", "protonmail.com"])
    email = f"{email_local}@{domain}"

    experience_years = round(random.uniform(0, 15), 1)

    return {
        "name": name,
        "email": email,
        "location": random.choice(LOCATIONS),
        "experience_years": experience_years,
        "skills": _build_skills(),
        "education": random.choice(EDUCATION_LEVELS),
        "experience": _build_experience(experience_years),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic ScoutGrid candidates")
    parser.add_argument("--count", type=int, default=10_000, help="Number of candidates to generate")
    parser.add_argument("--batch-size", type=int, default=500, help="MongoDB bulk insert batch size")
    args = parser.parse_args()

    print(f"Connecting to MongoDB: {MONGODB_URI} / database: {MONGODB_DATABASE}")
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]
    collection = db["candidates"]

    total = args.count
    batch_size = args.batch_size
    inserted = 0

    print(f"Generating {total:,} synthetic candidates in batches of {batch_size}...")

    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        batch = [generate_candidate(batch_start + i) for i in range(batch_end - batch_start)]
        collection.insert_many(batch, ordered=False)
        inserted += len(batch)
        pct = inserted / total * 100
        print(f"  Inserted {inserted:,} / {total:,}  ({pct:.1f}%)", end="\r", flush=True)

    print(f"\nDone. {inserted:,} candidates inserted into '{MONGODB_DATABASE}.candidates'.")
    client.close()


if __name__ == "__main__":
    main()
