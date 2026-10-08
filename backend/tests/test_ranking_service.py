import pytest
from models.candidate import CandidateResponse, ExperienceEntry
from models.search import ParsedRequirements
from services.ranking_service import CandidateRankingService, FeatureScores


@pytest.fixture
def ranking_service():
    return CandidateRankingService()


def test_skill_match_exact_and_partial(ranking_service):
    req_skills = ["Python", "FastAPI", "PostgreSQL", "Redis"]

    # 4/4 match
    cand_skills = ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"]
    score, matched = ranking_service.compute_skill_match(cand_skills, req_skills)
    assert score == 1.0
    assert len(matched) == 4

    # 2/4 match
    cand_skills_half = ["Python", "FastAPI", "React"]
    score_half, matched_half = ranking_service.compute_skill_match(cand_skills_half, req_skills)
    assert score_half == 0.5
    assert len(matched_half) == 2

    # 0/4 match
    cand_skills_zero = ["Java", "Spring", "Oracle"]
    score_zero, matched_zero = ranking_service.compute_skill_match(cand_skills_zero, req_skills)
    assert score_zero == 0.0
    assert len(matched_zero) == 0


def test_skill_match_edge_cases(ranking_service):
    # No required skills -> returns 1.0
    score, matched = ranking_service.compute_skill_match(["Python"], [])
    assert score == 1.0
    assert matched == []

    # Case insensitivity and whitespace normalization
    req_skills = [" Python ", "FastAPI"]
    cand_skills = ["python", "fastapi"]
    score, matched = ranking_service.compute_skill_match(cand_skills, req_skills)
    assert score == 1.0

    # Duplicate skills in requirements
    req_skills = ["Python", "python", "Python"]
    score, matched = ranking_service.compute_skill_match(["Python"], req_skills)
    assert score == 1.0


def test_experience_match_scenarios(ranking_service):
    # Within range (3-6 yrs)
    assert ranking_service.compute_experience_match(5.0, 3.0, 6.0) == 1.0

    # Below min requirement (exp=1, min=3) -> 1/3 = 0.3333
    score_below = ranking_service.compute_experience_match(1.0, 3.0, None)
    assert pytest.approx(score_below, 0.01) == 0.3333

    # Above max requirement (exp=10, max=6) -> 1 - 0.05*4 = 0.8
    score_above = ranking_service.compute_experience_match(10.0, 3.0, 6.0)
    assert score_above == 0.8

    # No requirement -> neutral 0.5
    assert ranking_service.compute_experience_match(5.0, None, None) == 0.5


def test_location_match_scenarios(ranking_service):
    # Match
    assert ranking_service.compute_location_match("Bangalore, India", "Bangalore") == 1.0
    assert ranking_service.compute_location_match("Remote", "remote") == 1.0

    # Non-match
    assert ranking_service.compute_location_match("London", "Bangalore") == 0.0

    # No location requirement -> neutral 0.5
    assert ranking_service.compute_location_match("Bangalore", None) == 0.5


def test_title_match_scenarios(ranking_service):
    exp = [{"title": "Senior Backend Engineer", "company": "Acme"}]
    
    # Strong match
    assert ranking_service.compute_title_match(exp, "", "Backend Engineer") == 1.0

    # Partial match
    score_partial = ranking_service.compute_title_match(exp, "", "Fullstack Engineer")
    assert 0.0 < score_partial < 1.0

    # Non-match
    assert ranking_service.compute_title_match(exp, "", "Data Scientist") == 0.0

    # No requirement -> 0.5
    assert ranking_service.compute_title_match(exp, "", None) == 0.5


def test_weighted_score_calculation(ranking_service):
    weights = ranking_service.weights
    # Sum of weights should equal 1.0
    assert pytest.approx(sum(weights.values()), 0.0001) == 1.0


def test_rank_candidates_ordering(ranking_service):
    req = ParsedRequirements(
        skills=["Python", "FastAPI"],
        location="Bangalore",
        min_experience=3.0,
        job_title="Backend Engineer",
    )

    hit_strong = {
        "_id": "c1",
        "_score": 2.5,
        "_source": {
            "candidate_id": "c1",
            "name": "Alice Strong",
            "email": "alice@example.com",
            "location": "Bangalore",
            "experience_years": 5.0,
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "education": "B.Tech Computer Science",
            "experience": [{"company": "Tech Corp", "title": "Senior Backend Engineer", "start_date": "2020-01-01"}],
        },
    }

    hit_weak = {
        "_id": "c2",
        "_score": 1.0,
        "_source": {
            "candidate_id": "c2",
            "name": "Bob Weak",
            "email": "bob@example.com",
            "location": "London",
            "experience_years": 1.0,
            "skills": ["Java"],
            "education": "B.A. Arts",
            "experience": [{"company": "Other Corp", "title": "Junior QA", "start_date": "2023-01-01"}],
        },
    }

    hits = [hit_weak, hit_strong]
    ranked = ranking_service.rank_candidates(hits, req, top_k=2)

    assert len(ranked) == 2
    assert ranked[0].candidate.id == "c1"
    assert ranked[1].candidate.id == "c2"
    assert ranked[0].feature_scores.final_score > ranked[1].feature_scores.final_score
    assert ranked[0].candidate.match_score is not None
    assert len(ranked[0].candidate.match_reasons) > 0


def test_rank_candidates_empty_hits(ranking_service):
    req = ParsedRequirements(skills=["Python"])
    ranked = ranking_service.rank_candidates([], req)
    assert ranked == []
