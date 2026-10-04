"""
Comprehensive Seed Candidate Generator & Bulk Seeding Script for ScoutGrid.

Generates realistic synthetic candidate profiles with realistic skill combinations,
searchable descriptions, education, work histories, and experience distributions,
and performs efficient batch insertion into MongoDB.

Usage:
    python scripts/seed_candidates.py --count 50000
    python scripts/seed_candidates.py --count 100000 --reset --batch-size 2000
    python scripts/seed_candidates.py --count 1000 --seed 42
"""

import argparse
import os
import random
import sys
import time
from datetime import date, datetime, time as time_cls, timedelta
from typing import Any, Dict, List

from dotenv import load_dotenv
from pymongo import MongoClient

# ---------------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------------
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "scoutgrid")
DEFAULT_SEED_COUNT = int(os.environ.get("SEED_CANDIDATE_COUNT", "50000"))

# ---------------------------------------------------------------------------
# Centralized Technology Catalogue & Categories
# ---------------------------------------------------------------------------

PROGRAMMING_LANGUAGES = [
    "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "Go", "Rust",
    "Kotlin", "Swift", "Dart", "PHP", "Ruby", "Scala", "R", "MATLAB", "Objective-C",
    "Lua", "Perl", "Shell", "Bash", "SQL", "HTML", "CSS", "Solidity", "Elixir", "Haskell"
]

BACKEND_FRAMEWORKS = [
    "FastAPI", "Django", "Flask", "Spring Boot", "Spring MVC", "Spring WebFlux",
    "Express.js", "NestJS", "Koa", "Hapi", "Gin", "Fiber", "Echo", "ASP.NET Core",
    "Ruby on Rails", "Laravel", "Symfony", "Phoenix", "Actix Web", "Axum", "Rocket",
    "Micronaut", "Quarkus", "Play Framework", "Vert.x", "Dropwizard", "Node.js", "Hibernate", "Maven"
]

FRONTEND_FRAMEWORKS = [
    "React", "Next.js", "Vue.js", "Nuxt.js", "Angular", "Svelte", "SvelteKit",
    "SolidJS", "Remix", "Astro", "Qwik", "Gatsby", "jQuery", "Redux", "Redux Toolkit",
    "Zustand", "MobX", "Recoil", "TanStack Query", "React Router",
    "Tailwind CSS", "Bootstrap", "Material UI", "Ant Design", "Chakra UI",
    "shadcn/ui", "CSS", "SCSS", "Sass", "Styled Components", "Prisma", "Webpack", "HTML/CSS"
]

MOBILE_TECH = [
    "React Native", "Flutter", "Android SDK", "Jetpack Compose", "SwiftUI",
    "UIKit", "Ionic", "Expo", "Kotlin Multiplatform"
]

DATABASES = [
    "PostgreSQL", "MySQL", "MariaDB", "SQLite", "Oracle", "SQL Server", "CockroachDB", "TiDB",
    "MongoDB", "DynamoDB", "CouchDB", "Cassandra", "ScyllaDB", "Firestore",
    "OpenSearch", "Elasticsearch", "Solr", "Algolia", "Meilisearch", "Typesense",
    "Neo4j", "Amazon Neptune", "ArangoDB",
    "Pinecone", "Weaviate", "Qdrant", "Milvus", "Chroma", "pgvector", "FAISS"
]

MESSAGING_STREAMING = [
    "Redis", "Memcached", "Apache Kafka", "RabbitMQ", "NATS", "Apache Pulsar",
    "Amazon SQS", "Amazon SNS", "Google Pub/Sub", "Azure Service Bus", "ActiveMQ",
    "Celery", "BullMQ"
]

CLOUD_PLATFORMS = [
    # AWS
    "EC2", "S3", "Lambda", "ECS", "EKS", "RDS", "DynamoDB", "CloudFront", "API Gateway",
    "SQS", "SNS", "CloudWatch", "VPC", "IAM", "Route 53", "Elastic Beanstalk", "Fargate",
    # Azure
    "Azure Functions", "Azure App Service", "Azure Kubernetes Service", "Azure Blob Storage",
    "Azure Cosmos DB", "Azure SQL", "Azure Service Bus", "Azure DevOps", "Azure Monitor",
    # GCP
    "Cloud Run", "GKE", "Cloud Functions", "Cloud Storage", "BigQuery", "Cloud SQL",
    "Firestore", "Pub/Sub", "Vertex AI", "Compute Engine",
    # Cloud providers / PaaS
    "Firebase", "Vercel", "Netlify", "Cloudflare", "DigitalOcean", "Heroku", "Render", "Railway", "Fly.io", "AWS"
]

DEVOPS_INFRASTRUCTURE = [
    "Docker", "Kubernetes", "Helm", "Terraform", "Ansible", "Pulumi", "Vagrant",
    "Nginx", "HAProxy", "Traefik", "Envoy", "Istio", "ArgoCD", "Jenkins", "GitHub Actions",
    "GitLab CI/CD", "CircleCI", "Travis CI", "Prometheus", "Grafana", "OpenTelemetry",
    "ELK Stack", "Datadog", "New Relic", "Sentry", "Linux"
]

AI_ML_GENAI = [
    "PyTorch", "TensorFlow", "Keras", "scikit-learn", "XGBoost", "LightGBM", "CatBoost",
    "Pandas", "NumPy", "SciPy", "Jupyter", "MLflow", "Kubeflow", "Hugging Face",
    "Transformers", "OpenCV", "spaCy", "NLTK", "Feature Engineering",
    # GenAI & LLM
    "OpenAI", "Gemini", "Claude", "Llama", "Mistral", "LangChain", "LangGraph",
    "LlamaIndex", "DSPy", "CrewAI", "AutoGen", "Semantic Kernel", "Haystack",
    "RAG", "Agentic AI", "MCP", "Prompt Engineering", "Function Calling", "Tool Calling",
    "Fine-tuning", "Embeddings", "Vector Search", "Semantic Search"
]

ARCHITECTURE_APIS = [
    "REST API", "GraphQL", "gRPC", "WebSockets", "WebRTC", "Webhooks", "OAuth 2.0",
    "OpenID Connect", "JWT", "Microservices", "Distributed Systems", "Event-Driven Architecture",
    "Serverless", "System Design", "API Gateway", "Load Balancing", "Rate Limiting",
    "Caching", "Message Queues", "Event Streaming", "CQRS", "Event Sourcing"
]

TESTING_TOOLS = [
    "Pytest", "Jest", "Vitest", "Mocha", "Chai", "Cypress", "Playwright", "Selenium",
    "JUnit", "TestNG", "Mockito", "Postman", "k6", "Locust", "JMeter"
]

DATA_ENGINEERING = [
    "Apache Spark", "PySpark", "Apache Flink", "Apache Airflow", "dbt", "Databricks",
    "Snowflake", "BigQuery", "Redshift", "Apache Hadoop", "Hive", "Presto", "Trino", "Kafka Streams",
    "Data Warehousing", "ETL"
]

SECURITY_TOOLS = [
    "OAuth", "JWT", "OpenID Connect", "RBAC", "ABAC", "OWASP", "TLS", "HTTPS",
    "Vault", "Keycloak", "Auth0", "Okta", "AWS IAM"
]

GIT_COLLABORATION = [
    "Git", "GitHub", "GitLab", "Bitbucket", "Azure DevOps", "Jira", "Confluence", "Linear"
]

# Total Unique Technology Catalogue
ALL_TECHNOLOGY_CATALOGUE = list(set(
    PROGRAMMING_LANGUAGES + BACKEND_FRAMEWORKS + FRONTEND_FRAMEWORKS + MOBILE_TECH +
    DATABASES + MESSAGING_STREAMING + CLOUD_PLATFORMS + DEVOPS_INFRASTRUCTURE +
    AI_ML_GENAI + ARCHITECTURE_APIS + TESTING_TOOLS + DATA_ENGINEERING +
    SECURITY_TOOLS + GIT_COLLABORATION
))

# ---------------------------------------------------------------------------
# Locations & Names
# ---------------------------------------------------------------------------

LOCATIONS_INDIA = [
    "Bangalore", "Hyderabad", "Pune", "Mumbai", "Delhi", "Gurgaon", "Noida",
    "Chennai", "Kolkata", "Ahmedabad", "Jaipur", "Kochi", "Coimbatore", "Visakhapatnam"
]

LOCATIONS_INTL = [
    "San Francisco", "New York", "Seattle", "Austin", "Boston", "Toronto",
    "Vancouver", "London", "Berlin", "Amsterdam", "Singapore", "Sydney", "Melbourne", "Dubai", "Dublin"
]

LOCATIONS = LOCATIONS_INDIA * 4 + LOCATIONS_INTL  # Weighted towards Indian tech hubs

FIRST_NAMES = [
    "Aarav", "Aditya", "Akash", "Amit", "Ananya", "Ankita", "Arjun", "Aryan",
    "Deepika", "Devansh", "Divya", "Gaurav", "Harsha", "Ishaan", "Ishita",
    "Karan", "Kavya", "Kunal", "Lakshmi", "Manish", "Meera", "Mihir", "Neha",
    "Nikhil", "Nisha", "Pooja", "Priya", "Rahul", "Raj", "Riya", "Rohan",
    "Sakshi", "Saniya", "Siddharth", "Sneha", "Souvik", "Srikanth", "Suresh",
    "Tanvi", "Varun", "Vikram", "Vipul", "Vishal", "Yash", "Zara", "Alex", "David",
    "Elena", "Michael", "Sarah", "James", "Emily", "Daniel", "Sophia", "Lucas"
]

LAST_NAMES = [
    "Agarwal", "Bhat", "Chakraborty", "Chandra", "Das", "Desai", "Dubey",
    "Ghosh", "Gupta", "Iyer", "Jain", "Joshi", "Kaur", "Khan", "Kumar",
    "Malhotra", "Mehta", "Mishra", "Nair", "Pandey", "Patel", "Pillai",
    "Rao", "Reddy", "Sharma", "Singh", "Sinha", "Srivastava", "Tiwari",
    "Varma", "Verma", "Yadav", "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller"
]

COMPANIES = [
    "Infosys", "Wipro", "TCS", "HCL Technologies", "Tech Mahindra", "Accenture India",
    "Capgemini", "Cognizant", "Mphasis", "LTIMindtree", "Zoho", "Freshworks", "Paytm",
    "Swiggy", "Zomato", "Razorpay", "Ola", "Flipkart", "PhonePe", "Cred", "Meesho",
    "Unacademy", "BrowserStack", "Postman", "Hasura", "Druva", "Clevertap", "Exotel",
    "ThoughtWorks", "Sigmoid", "Delhivery", "Urban Company", "Google", "Amazon",
    "Microsoft", "Meta", "Apple", "Netflix", "Uber", "Stripe", "Atlassian", "Databricks", "Snowflake"
]

EDUCATION_DEGREES = [
    "B.Tech Computer Science", "B.Tech Information Technology", "B.E. Computer Engineering",
    "M.Tech Computer Science", "M.S. Computer Science", "MCA", "BCA", "B.Sc Computer Science",
    "B.S. Software Engineering", "Ph.D. Computer Science", "M.Tech Data Science"
]

UNIVERSITIES = [
    "IIT Bombay", "IIT Delhi", "IIT Madras", "IIT Kharagpur", "IIT Kanpur",
    "BITS Pilani", "IIIT Hyderabad", "NIT Trichy", "Anna University", "VTU",
    "Delhi Technological University", "Manipal Institute of Technology",
    "Stanford University", "Carnegie Mellon", "UC Berkeley", "MIT"
]

# ---------------------------------------------------------------------------
# Coherent Persona Archetypes
# ---------------------------------------------------------------------------

PERSONA_ARCHETYPES = [
    {
        "role": "Python Backend Engineer",
        "primary_skills": ["Python", "FastAPI", "Django", "Flask", "PostgreSQL", "Redis", "Docker", "AWS"],
        "secondary_skills": ["Kafka", "Celery", "REST API", "Microservices", "Pytest", "Git", "Kubernetes", "gRPC"],
        "descriptions": [
            "Built high-throughput APIs and scalable REST backend services processing millions of daily requests.",
            "Developed asynchronous backend services and microservices using Python FastAPI, PostgreSQL, and Redis caching.",
            "Designed event-driven backend architectures with Django, Celery worker queues, and Apache Kafka."
        ]
    },
    {
        "role": "Java Backend Engineer",
        "primary_skills": ["Java", "Spring Boot", "Spring Security", "PostgreSQL", "Kafka", "Redis", "Docker", "Kubernetes"],
        "secondary_skills": ["Hibernate", "Microservices", "AWS", "gRPC", "JUnit", "Maven", "Jenkins", "Distributed Systems"],
        "descriptions": [
            "Architected distributed Java Spring Boot microservices handling high-concurrency payment transactions.",
            "Developed enterprise backend platforms with Java, Kafka event streaming, and PostgreSQL database sharding.",
            "Implemented secure, fault-tolerant REST APIs and event-driven backend systems using Spring WebFlux."
        ]
    },
    {
        "role": "Full-Stack TypeScript Engineer",
        "primary_skills": ["TypeScript", "React", "Next.js", "Node.js", "NestJS", "PostgreSQL", "Tailwind CSS", "Docker"],
        "secondary_skills": ["Express.js", "GraphQL", "Prisma", "Redis", "AWS", "Jest", "Git", "Zustand"],
        "descriptions": [
            "Built end-to-end full-stack web applications using React, Next.js frontend and TypeScript NestJS backend.",
            "Engineered responsive SaaS user interfaces and high-performance Node.js API services.",
            "Developed interactive web platforms using TypeScript, React Query, Tailwind CSS, and GraphQL."
        ]
    },
    {
        "role": "MERN Stack Developer",
        "primary_skills": ["JavaScript", "TypeScript", "React", "Node.js", "Express.js", "MongoDB", "Redux", "HTML/CSS"],
        "secondary_skills": ["Tailwind CSS", "REST API", "JWT", "Docker", "AWS", "Git", "Webpack"],
        "descriptions": [
            "Developed responsive single-page web applications with React frontend and Express.js MongoDB backend.",
            "Built full-stack Web applications with state management, authentication, and database REST endpoints."
        ]
    },
    {
        "role": "Go Backend / Systems Engineer",
        "primary_skills": ["Go", "Gin", "gRPC", "PostgreSQL", "Redis", "Kafka", "Docker", "Kubernetes", "AWS"],
        "secondary_skills": ["Microservices", "Distributed Systems", "Prometheus", "Grafana", "Nginx", "Linux", "System Design"],
        "descriptions": [
            "Built ultra-low-latency backend microservices and gRPC networking components in Golang.",
            "Worked on distributed backend systems, load balancing, rate limiting, and high-concurrency server engines."
        ]
    },
    {
        "role": "AI / GenAI Engineer",
        "primary_skills": ["Python", "PyTorch", "Transformers", "LangChain", "OpenAI", "RAG", "Vector Search", "FastAPI"],
        "secondary_skills": ["Gemini", "LlamaIndex", "Pinecone", "Qdrant", "Hugging Face", "Prompt Engineering", "MCP", "Docker"],
        "descriptions": [
            "Architected agentic AI workflows and Retrieval-Augmented Generation (RAG) applications using LangChain and Qdrant.",
            "Built custom LLM fine-tuning pipelines, vector embeddings, and semantic candidate search services.",
            "Integrated generative AI models, function calling, and vector databases into real-time production APIs."
        ]
    },
    {
        "role": "Machine Learning Engineer",
        "primary_skills": ["Python", "PyTorch", "TensorFlow", "scikit-learn", "Pandas", "NumPy", "MLflow", "AWS"],
        "secondary_skills": ["Docker", "Kubeflow", "OpenCV", "XGBoost", "SciPy", "SQL", "Feature Engineering"],
        "descriptions": [
            "Trained and deployed predictive machine learning models into production REST endpoints with MLflow.",
            "Designed end-to-end ML data pipelines, computer vision algorithms, and automated model monitoring."
        ]
    },
    {
        "role": "Data Engineer",
        "primary_skills": ["Python", "SQL", "Apache Spark", "PySpark", "Apache Airflow", "Kafka", "Snowflake", "AWS"],
        "secondary_skills": ["BigQuery", "dbt", "PostgreSQL", "Redshift", "Docker", "Data Warehousing", "ETL"],
        "descriptions": [
            "Built automated ETL/ELT data pipelines processing multi-terabyte data streams with PySpark and Airflow.",
            "Designed cloud data warehouses on Snowflake and BigQuery with real-time Kafka data streaming."
        ]
    },
    {
        "role": "DevOps & Cloud Platform Engineer",
        "primary_skills": ["Docker", "Kubernetes", "Terraform", "AWS", "Ansible", "GitHub Actions", "Prometheus", "Grafana"],
        "secondary_skills": ["Helm", "Nginx", "Python", "Bash", "Linux", "ArgoCD", "Jenkins", "Datadog"],
        "descriptions": [
            "Managed multi-region Kubernetes clusters (EKS), automated CI/CD pipelines, and Infrastructure as Code using Terraform.",
            "Designed zero-downtime deployment pipelines, cloud network infrastructure, and observability dashboards."
        ]
    },
    {
        "role": "Mobile App Developer",
        "primary_skills": ["Flutter", "Dart", "React Native", "TypeScript", "Android SDK", "iOS", "Swift", "REST API"],
        "secondary_skills": ["Firebase", "Redux", "Jetpack Compose", "SwiftUI", "GraphQL", "SQLite", "Git"],
        "descriptions": [
            "Built cross-platform iOS and Android mobile applications using Flutter and React Native with native module integrations.",
            "Developed high-performance mobile UI features, offline synchronization, and push notifications."
        ]
    }
]

# ---------------------------------------------------------------------------
# Generator Functions
# ---------------------------------------------------------------------------

def generate_experience_timeline(total_exp: float, current_title: str) -> List[Dict[str, Any]]:
    """Generates realistic experience entries consistent with total experience years."""
    entries = []
    num_jobs = 1 if total_exp < 2.0 else (2 if total_exp < 5.0 else random.randint(2, 4))
    
    current_date = date.today()
    years_remaining = total_exp
    
    for i in range(num_jobs):
        is_current = (i == 0)
        job_years = round(random.uniform(1.0, min(years_remaining, 4.0)), 1) if not is_current else round(random.uniform(0.5, min(years_remaining, 3.5)), 1)
        if job_years <= 0.2:
            job_years = 0.5
            
        start_d = current_date - timedelta(days=int(job_years * 365))
        end_d = None if is_current else current_date
        
        start_date = datetime.combine(start_d, time_cls.min)
        end_date = datetime.combine(end_d, time_cls.min) if end_d else None
        
        company = random.choice(COMPANIES)
        title = current_title if is_current else f"Engineer at {company}"
        
        entries.append({
            "company": company,
            "title": title,
            "start_date": start_date,
            "end_date": end_date,
            "description": f"Worked as {title} developing backend services and scalable infrastructure at {company}."
        })
        
        current_date = start_d - timedelta(days=random.randint(15, 60))
        years_remaining -= job_years
        if years_remaining <= 0.3:
            break
            
    return entries


def generate_candidate(index: int, seed_id: int) -> Dict[str, Any]:
    """Generates a single realistic Candidate dictionary compatible with ScoutGrid Pydantic schema."""
    # Deterministic RNG per candidate if seed is set
    rng = random.Random(seed_id + index)
    
    first_name = rng.choice(FIRST_NAMES)
    last_name = rng.choice(LAST_NAMES)
    name = f"{first_name} {last_name}"
    email = f"{first_name.lower()}.{last_name.lower()}{index}@example.com"
    location = rng.choice(LOCATIONS)
    
    # Realistic experience distribution (0 to 15 years)
    exp_weights = [0.15, 0.25, 0.30, 0.20, 0.10]
    exp_ranges = [(0.5, 2.0), (2.1, 4.5), (4.6, 7.5), (7.6, 11.0), (11.1, 16.0)]
    selected_range = rng.choices(exp_ranges, weights=exp_weights)[0]
    experience_years = round(rng.uniform(selected_range[0], selected_range[1]), 1)
    
    # Pick persona archetype
    persona = rng.choice(PERSONA_ARCHETYPES)
    
    # Skill selection: blend persona skills + general technologies
    num_primary = rng.randint(4, len(persona["primary_skills"]))
    num_secondary = rng.randint(2, len(persona["secondary_skills"]))
    selected_skills = set(rng.sample(persona["primary_skills"], num_primary))
    selected_skills.update(rng.sample(persona["secondary_skills"], num_secondary))
    
    # Add 1-2 random global skills for realistic variation
    if rng.random() > 0.6:
        selected_skills.update(rng.sample(ALL_TECHNOLOGY_CATALOGUE, rng.randint(1, 2)))
        
    skills = list(selected_skills)
    
    # Experience entries
    title_prefix = "Senior " if experience_years >= 5.0 else ("Lead " if experience_years >= 9.0 else "")
    full_title = f"{title_prefix}{persona['role']}"
    
    exp_entries = generate_experience_timeline(experience_years, full_title)
    
    # Education
    degree = rng.choice(EDUCATION_DEGREES)
    uni = rng.choice(UNIVERSITIES)
    grad_year = 2024 - int(experience_years)
    education = f"{degree} from {uni} ({grad_year})"
    
    return {
        "name": name,
        "email": email,
        "location": location,
        "experience_years": experience_years,
        "skills": skills,
        "education": education,
        "experience": exp_entries,
    }


def batch_seed_candidates(
    client: MongoClient,
    total_count: int,
    batch_size: int = 1000,
    reset: bool = False,
    seed_val: int = 42
) -> Dict[str, Any]:
    """Generates and seeds candidate records in batches into MongoDB."""
    db = client[MONGODB_DATABASE]
    collection = db["candidates"]
    
    if reset:
        print(f"Resetting MongoDB collection '{MONGODB_DATABASE}.candidates'...")
        collection.drop()
        print("Collection dropped successfully.")
        
    initial_count = collection.count_documents({})
    print(f"Initial MongoDB candidate count: {initial_count:,}")
    print(f"Target candidate count to insert: {total_count:,} (Batch size: {batch_size:,})")
    
    start_time = time.time()
    total_inserted = 0
    
    location_stats: Dict[str, int] = {}
    skill_stats: Dict[str, int] = {}
    exp_stats: Dict[str, int] = {"0-2 yrs": 0, "2-5 yrs": 0, "5-10 yrs": 0, "10+ yrs": 0}
    
    for batch_start in range(0, total_count, batch_size):
        current_batch_size = min(batch_size, total_count - batch_start)
        batch_docs = []
        
        for idx in range(current_batch_size):
            global_idx = initial_count + batch_start + idx + 1
            doc = generate_candidate(global_idx, seed_val)
            batch_docs.append(doc)
            
            # Record statistics
            loc = doc["location"]
            location_stats[loc] = location_stats.get(loc, 0) + 1
            
            for s in doc["skills"]:
                skill_stats[s] = skill_stats.get(s, 0) + 1
                
            ey = doc["experience_years"]
            if ey <= 2.0:
                exp_stats["0-2 yrs"] += 1
            elif ey <= 5.0:
                exp_stats["2-5 yrs"] += 1
            elif ey <= 10.0:
                exp_stats["5-10 yrs"] += 1
            else:
                exp_stats["10+ yrs"] += 1

        if batch_docs:
            res = collection.insert_many(batch_docs, ordered=False)
            total_inserted += len(res.inserted_ids)
            
            elapsed = time.time() - start_time
            rate = total_inserted / elapsed if elapsed > 0 else 0
            pct = (total_inserted / total_count) * 100
            print(f"  Inserted batch: {total_inserted:,} / {total_count:,} candidates ({pct:.1f}%) | {rate:.1f} cand/sec")

    total_time = time.time() - start_time
    final_count = collection.count_documents({})
    throughput = total_inserted / total_time if total_time > 0 else 0
    
    return {
        "inserted": total_inserted,
        "total_time": total_time,
        "throughput": throughput,
        "final_count": final_count,
        "locations": location_stats,
        "skills": skill_stats,
        "experience": exp_stats,
    }


def main():
    parser = argparse.ArgumentParser(description="Seed candidate profiles into MongoDB in bulk.")
    parser.add_argument("--count", type=int, default=DEFAULT_SEED_COUNT, help=f"Number of candidates to generate (default: {DEFAULT_SEED_COUNT})")
    parser.add_argument("--batch-size", type=int, default=2000, help="Batch size for insert_many (default: 2000)")
    parser.add_argument("--reset", action="store_true", help="Drop candidates collection before seeding")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic generation (default: 42)")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print(f"SCOUTGRID BULK CANDIDATE SEEDING SYSTEM")
    print(f"Connecting to MongoDB: {MONGODB_URI}")
    print(f"Database: {MONGODB_DATABASE}")
    print("=" * 80)
    
    client = MongoClient(MONGODB_URI)
    
    stats = batch_seed_candidates(
        client=client,
        total_count=args.count,
        batch_size=args.batch_size,
        reset=args.reset,
        seed_val=args.seed
    )
    
    print("\n" + "=" * 80)
    print("SEEDING SUMMARY & STATISTICS")
    print("=" * 80)
    print(f"Candidates Inserted:      {stats['inserted']:,}")
    print(f"Total Collection Count:   {stats['final_count']:,}")
    print(f"Execution Time:           {stats['total_time']:.2f} seconds")
    print(f"Throughput:               {stats['throughput']:.2f} candidates/sec")
    print(f"Technology Categories:    15 categories covered")
    print(f"Unique Technologies:      {len(ALL_TECHNOLOGY_CATALOGUE)} technologies in catalogue")
    
    print("\n--- Top Locations ---")
    sorted_locs = sorted(stats['locations'].items(), key=lambda x: x[1], reverse=True)[:8]
    for loc, cnt in sorted_locs:
        print(f"  {loc:20s}: {cnt:,}")
        
    print("\n--- Top Technologies / Skills ---")
    sorted_skills = sorted(stats['skills'].items(), key=lambda x: x[1], reverse=True)[:10]
    for sk, cnt in sorted_skills:
        print(f"  {sk:20s}: {cnt:,}")
        
    print("\n--- Experience Distribution ---")
    for exp_range, cnt in stats['experience'].items():
        print(f"  {exp_range:20s}: {cnt:,}")
        
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
