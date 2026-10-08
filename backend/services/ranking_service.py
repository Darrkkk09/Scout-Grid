import os
import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel

from models.candidate import CandidateResponse
from models.search import ParsedRequirements

logger = logging.getLogger(__name__)


class FeatureScores(BaseModel):
    skill_match: float
    experience_match: float
    location_match: float
    title_match: float
    semantic_score: float
    retrieval_score: float
    final_score: float


class RankedCandidate(BaseModel):
    candidate: CandidateResponse
    feature_scores: FeatureScores
    match_reasons: List[str]


class CandidateRankingService:
    """
    Deterministic Feature-Based Candidate Ranking Service.
    Ranks retrieved candidate documents using normalized feature scores:
      - Skill match
      - Experience match
      - Location match
      - Role/Title match
      - Semantic similarity score
      - Retrieval score (BM25 / vector / RRF)
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        # Default weights configuration
        self.weights = weights or {
            "skill": float(os.getenv("RANK_WEIGHT_SKILL", "0.35")),
            "experience": float(os.getenv("RANK_WEIGHT_EXPERIENCE", "0.20")),
            "semantic": float(os.getenv("RANK_WEIGHT_SEMANTIC", "0.15")),
            "location": float(os.getenv("RANK_WEIGHT_LOCATION", "0.10")),
            "title": float(os.getenv("RANK_WEIGHT_TITLE", "0.10")),
            "retrieval": float(os.getenv("RANK_WEIGHT_RETRIEVAL", "0.10")),
        }
        # Normalize weights so they sum to 1.0
        total_w = sum(self.weights.values())
        if total_w > 0:
            self.weights = {k: v / total_w for k, v in self.weights.items()}

    @staticmethod
    def normalize_skill(skill: str) -> str:
        """Normalizes skill string for comparison (lowercase, strip, collapse spaces)."""
        clean = skill.strip().lower()
        clean = re.sub(r"\s+", " ", clean)
        return clean

    def compute_skill_match(
        self, candidate_skills: List[str], required_skills: List[str]
    ) -> Tuple[float, List[str]]:
        """
        Calculates normalized skill match score in [0.0, 1.0].
        matched_required_skills / total_required_skills.
        If zero required skills, returns neutral 1.0.
        """
        if not required_skills:
            return 1.0, []

        norm_req = [self.normalize_skill(s) for s in required_skills if s and s.strip()]
        if not norm_req:
            return 1.0, []

        # Deduplicate required skills maintaining set logic
        unique_req = list(dict.fromkeys(norm_req))

        norm_cand = {self.normalize_skill(s) for s in candidate_skills if s and s.strip()}

        matched_skills = [req for req in unique_req if req in norm_cand]
        score = len(matched_skills) / len(unique_req)
        return round(score, 4), matched_skills

    def compute_experience_match(
        self,
        exp_years: float,
        min_exp: Optional[float],
        max_exp: Optional[float],
    ) -> float:
        """
        Calculates experience score based on distance from requested range.
          - within range: 1.0
          - below min_exp: exp_years / min_exp (gradual linear decrease)
          - above max_exp: 1.0 - 0.05 * (exp_years - max_exp) (gradual decrease)
          - no requirement: 0.5 (explicit neutral value)
        """
        if min_exp is None and max_exp is None:
            return 0.5

        score = 1.0

        if min_exp is not None and max_exp is not None:
            if min_exp <= exp_years <= max_exp:
                return 1.0
            elif exp_years < min_exp:
                score = exp_years / min_exp if min_exp > 0 else 1.0
            else:  # exp_years > max_exp
                diff = exp_years - max_exp
                score = max(0.0, 1.0 - 0.05 * diff)

        elif min_exp is not None:
            if exp_years >= min_exp:
                return 1.0
            else:
                score = exp_years / min_exp if min_exp > 0 else 1.0

        elif max_exp is not None:
            if exp_years <= max_exp:
                return 1.0
            else:
                diff = exp_years - max_exp
                score = max(0.0, 1.0 - 0.05 * diff)

        return round(min(1.0, max(0.0, score)), 4)

    def compute_location_match(
        self, candidate_loc: str, required_loc: Optional[str]
    ) -> float:
        """
        Calculates location match score in [0.0, 1.0].
        Exact or substring match -> 1.0, non-match -> 0.0, no requirement -> 0.5.
        """
        if not required_loc or not required_loc.strip():
            return 0.5

        req_clean = required_loc.strip().lower()
        cand_clean = (candidate_loc or "").strip().lower()

        if not cand_clean:
            return 0.0

        if req_clean in cand_clean or cand_clean in req_clean:
            return 1.0

        return 0.0

    def compute_title_match(
        self,
        candidate_experience: List[Dict[str, Any]],
        candidate_education: str,
        required_job_title: Optional[str],
    ) -> float:
        """
        Calculates job title match score in [0.0, 1.0] by comparing tokens against candidate titles.
        """
        if not required_job_title or not required_job_title.strip():
            return 0.5

        req_tokens = set(re.findall(r"\w+", required_job_title.lower()))
        if not req_tokens:
            return 0.5

        candidate_title_texts = []
        for exp in candidate_experience:
            if isinstance(exp, dict) and exp.get("title"):
                candidate_title_texts.append(str(exp["title"]).lower())
            elif hasattr(exp, "title") and getattr(exp, "title"):
                candidate_title_texts.append(str(getattr(exp, "title")).lower())

        if candidate_education:
            candidate_title_texts.append(candidate_education.lower())

        if not candidate_title_texts:
            return 0.0

        best_token_match = 0.0
        for title_text in candidate_title_texts:
            # Check exact phrase match
            if required_job_title.lower() in title_text:
                return 1.0
            
            cand_tokens = set(re.findall(r"\w+", title_text))
            if req_tokens and cand_tokens:
                matched = req_tokens.intersection(cand_tokens)
                ratio = len(matched) / len(req_tokens)
                if ratio > best_token_match:
                    best_token_match = ratio

        return round(best_token_match, 4)

    def rank_candidates(
        self,
        hits: List[Dict[str, Any]],
        requirements: ParsedRequirements,
        top_k: int = 20,
    ) -> List[RankedCandidate]:
        """
        Ranks a pool of OpenSearch candidate hits based on feature scores.
        Returns top_k RankedCandidate objects with feature breakdowns and match reasons.
        """
        if not hits:
            return []

        # Extract raw retrieval scores to perform min-max normalization
        retrieval_raw_scores = []
        for hit in hits:
            # Prefer _rrf_score if present, else _score
            score = hit.get("_rrf_score")
            if score is None:
                score = hit.get("_score", 0.0)
            retrieval_raw_scores.append(float(score or 0.0))

        min_ret_score = min(retrieval_raw_scores) if retrieval_raw_scores else 0.0
        max_ret_score = max(retrieval_raw_scores) if retrieval_raw_scores else 1.0
        score_range = max_ret_score - min_ret_score

        ranked_list: List[RankedCandidate] = []

        for hit, raw_ret_score in zip(hits, retrieval_raw_scores):
            source = hit.get("_source", {})
            cand_id = str(source.get("candidate_id", hit.get("_id", "")))
            name = source.get("name", "")
            email = source.get("email", "")
            location = source.get("location", "")
            exp_years = float(source.get("experience_years", 0.0))
            skills = source.get("skills", [])
            education = source.get("education", "")
            experience = source.get("experience", [])

            # 1. Skill Match
            skill_score, matched_skills = self.compute_skill_match(skills, requirements.skills)

            # 2. Experience Match
            exp_score = self.compute_experience_match(
                exp_years, requirements.min_experience, requirements.max_experience
            )

            # 3. Location Match
            loc_score = self.compute_location_match(location, requirements.location)

            # 4. Title Match
            title_score = self.compute_title_match(experience, education, requirements.job_title)

            # 5. Semantic Score
            # Use raw vector score if present, else default to neutral 0.5
            sem_score = hit.get("_vector_score")
            if sem_score is None:
                sem_score = 0.5
            else:
                sem_score = round(float(sem_score), 4)

            # 6. Normalized Retrieval Score
            if score_range > 1e-6:
                norm_ret_score = (raw_ret_score - min_ret_score) / score_range
            else:
                norm_ret_score = 0.5
            norm_ret_score = round(norm_ret_score, 4)

            # Calculate Weighted Final Score
            final_score = (
                self.weights["skill"] * skill_score
                + self.weights["experience"] * exp_score
                + self.weights["semantic"] * sem_score
                + self.weights["location"] * loc_score
                + self.weights["title"] * title_score
                + self.weights["retrieval"] * norm_ret_score
            )
            final_score = round(final_score, 4)

            feature_scores = FeatureScores(
                skill_match=skill_score,
                experience_match=exp_score,
                location_match=loc_score,
                title_match=title_score,
                semantic_score=sem_score,
                retrieval_score=norm_ret_score,
                final_score=final_score,
            )

            # Build Deterministic Recruiter-Facing Match Reasons
            match_reasons: List[str] = []
            if requirements.skills:
                match_reasons.append(
                    f"Matched {len(matched_skills)}/{len(requirements.skills)} required skills"
                    + (f" ({', '.join(matched_skills[:4])})" if matched_skills else "")
                )
            if requirements.min_experience is not None:
                match_reasons.append(
                    f"{exp_years} years experience (min requirement: {requirements.min_experience} yrs)"
                )
            elif requirements.max_experience is not None:
                match_reasons.append(
                    f"{exp_years} years experience (max requirement: {requirements.max_experience} yrs)"
                )
            else:
                match_reasons.append(f"{exp_years} years of experience")

            if requirements.location and loc_score > 0:
                match_reasons.append(f"Location matches '{requirements.location}'")
            
            if requirements.job_title and title_score > 0:
                match_reasons.append(f"Role matches '{requirements.job_title}'")

            cleaned_exp = []
            if isinstance(experience, list):
                for item in experience:
                    if isinstance(item, dict) and item.get("company") and item.get("title"):
                        exp_item = dict(item)
                        sd = str(exp_item.get("start_date", ""))
                        if sd and (" " in sd or "T" in sd):
                            exp_item["start_date"] = sd.split(" ")[0].split("T")[0]
                        elif not sd:
                            exp_item["start_date"] = "2020-01-01"

                        ed = str(exp_item.get("end_date", ""))
                        if ed and (" " in ed or "T" in ed):
                            exp_item["end_date"] = ed.split(" ")[0].split("T")[0]
                        elif not ed or ed.lower() == "none":
                            exp_item["end_date"] = None
                        cleaned_exp.append(exp_item)

            cand_response = CandidateResponse(
                id=cand_id,
                name=name,
                email=email,
                location=location,
                experience_years=exp_years,
                skills=skills,
                education=education,
                experience=cleaned_exp,
                match_score=final_score,
                match_reasons=match_reasons,
            )

            ranked_list.append(
                RankedCandidate(
                    candidate=cand_response,
                    feature_scores=feature_scores,
                    match_reasons=match_reasons,
                )
            )

        # Sort candidates descending by final ranking score
        ranked_list.sort(key=lambda rc: rc.feature_scores.final_score, reverse=True)

        return ranked_list[:top_k]
