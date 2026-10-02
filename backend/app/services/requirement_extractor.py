import re
from typing import Dict, List, Optional, Tuple
from app.models.search import ParsedRequirements


# Controlled Vocabulary based on candidate dataset & common tech domain
CONTROLLED_SKILLS = [
    "Python", "FastAPI", "Django", "Java", "Spring Boot",
    "JavaScript", "TypeScript", "React", "Node.js", "Express",
    "C++", "Go", "AWS", "Docker", "Kubernetes",
    "MongoDB", "PostgreSQL", "Redis", "Kafka",
    "OOP", "Databases", "Git", "Unit Testing", "Microservices",
]

CONTROLLED_LOCATIONS = [
    "Bangalore", "Bengaluru", "Hyderabad", "Chennai", "Mumbai", "Pune",
    "Delhi", "Visakhapatnam", "Kolkata", "Remote", "San Francisco", "New York",
]

# Canonical mapping for skill variations
SKILL_ALIASES: Dict[str, str] = {
    "python": "Python",
    "fastapi": "FastAPI",
    "django": "Django",
    "java": "Java",
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "express": "Express",
    "expressjs": "Express",
    "c++": "C++",
    "cpp": "C++",
    "go": "Go",
    "golang": "Go",
    "aws": "AWS",
    "docker": "Docker",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "redis": "Redis",
    "kafka": "Kafka",
    "unit testing": "Unit Testing",
    "databases": "Databases",
    "git": "Git",
    "oop": "OOP",
}

JOB_ROLE_PATTERNS = [
    r"\b(backend engineer[s]?|backend developer[s]?|frontend engineer[s]?|frontend developer[s]?|full stack engineer[s]?|full stack developer[s]?|fullstack developer[s]?|software engineer[s]?|tech lead[s]?|platform engineer[s]?|data engineer[s]?|devops engineer[s]?|principal engineer[s]?|staff engineer[s]?|trainee developer[s]?|associate engineer[s]?|developer[s]?|engineer[s]?)\b"
]



class RequirementExtractor:
    """
    Deterministic/rule-based natural language query parser for candidate sourcing.
    Converts recruiter text queries into structured criteria.
    """

    @classmethod
    def extract(cls, query: str) -> ParsedRequirements:
        if not query or not query.strip():
            return ParsedRequirements()

        clean_query = query.strip()

        skills = cls._extract_skills(clean_query)
        location = cls._extract_location(clean_query)
        min_exp, max_exp = cls._extract_experience(clean_query)
        job_title = cls._extract_job_title(clean_query)

        return ParsedRequirements(
            skills=skills,
            location=location,
            min_experience=min_exp,
            max_experience=max_exp,
            job_title=job_title,
        )

    @classmethod
    def _extract_skills(cls, query: str) -> List[str]:
        found_skills: List[str] = []
        lower_query = query.lower()

        # Sort aliases by length descending so multi-word aliases (e.g. "spring boot") match before "spring"
        sorted_aliases = sorted(SKILL_ALIASES.items(), key=lambda x: len(x[0]), reverse=True)

        for alias, canonical in sorted_aliases:
            # Use boundary check or explicit word match
            pattern = r"\b" + re.escape(alias) + r"\b"
            if alias == "c++":
                pattern = r"(?:^|\s|,)c\+\+(?:$|\s|,)"

            if re.search(pattern, lower_query):
                if canonical not in found_skills:
                    found_skills.append(canonical)

        return found_skills

    @classmethod
    def _extract_location(cls, query: str) -> Optional[str]:
        lower_query = query.lower()
        for loc in CONTROLLED_LOCATIONS:
            loc_lower = loc.lower()
            pattern = r"\b" + re.escape(loc_lower) + r"\b"
            if re.search(pattern, lower_query):
                # Normalize Bengaluru to Bangalore for dataset consistency
                if loc_lower in ["bengaluru", "bangalore"]:
                    return "Bangalore"
                return loc

        # Also check "in <City>" pattern
        in_match = re.search(r"\bin\s+([a-zA-Z]+)\b", query, re.IGNORECASE)
        if in_match:
            city_candidate = in_match.group(1).title()
            for loc in CONTROLLED_LOCATIONS:
                if loc.lower() == city_candidate.lower():
                    return loc

        return None

    @classmethod
    def _extract_experience(cls, query: str) -> Tuple[Optional[float], Optional[float]]:
        min_exp: Optional[float] = None
        max_exp: Optional[float] = None

        # Pattern: 3+ years, 3+ yrs, 3 + years, 3+years
        match_plus = re.search(r"(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)", query, re.IGNORECASE)
        if match_plus:
            min_exp = float(match_plus.group(1))
            return min_exp, max_exp

        # Pattern: with 3 years, 5 years experience, 3 yrs exp, min 4 years
        match_atleast = re.search(r"(?:with|at least|min|minimum)?\s*(\d+(?:\.\d+)?)\s*(?:\+|plus)?\s*(?:years?|yrs?)", query, re.IGNORECASE)

        # Pattern: less than 5 years, under 5 years, < 5 years
        match_less = re.search(r"(?:less than|under|<)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", query, re.IGNORECASE)

        # Pattern: between 3 and 6 years, 3-5 years
        match_range = re.search(r"(?:between|from)?\s*(\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", query, re.IGNORECASE)

        if match_range:
            min_exp = float(match_range.group(1))
            max_exp = float(match_range.group(2))
            return min_exp, max_exp

        if match_less:
            max_exp = float(match_less.group(1))
            return min_exp, max_exp

        if match_atleast:
            min_exp = float(match_atleast.group(1))
            return min_exp, max_exp

        return min_exp, max_exp

    @classmethod
    def _extract_job_title(cls, query: str) -> Optional[str]:
        for pattern in JOB_ROLE_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                title = match.group(1).lower()
                if title.endswith("s") and not title.endswith("ss"):
                    title = title[:-1]
                return title
        return None

