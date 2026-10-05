from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from app.database import connect_to_mongo, close_mongo_connection
from app.routes import analytics, candidates, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    import logging
    from app.services.llm_requirement_extractor import LLMRequirementExtractor
    extractor = LLMRequirementExtractor()
    if not extractor.is_configured():
        logging.getLogger(__name__).warning(
            "LLM extraction is unconfigured (no Gemini API keys found). Automatically falling back to deterministic RequirementExtractor."
        )
    yield
    await close_mongo_connection()


app = FastAPI(
    title="ScoutGrid Candidate Service",
    description="Distributed AI Candidate Sourcing Platform — Task 2: Candidate Search Engine",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(candidates.router, prefix="/candidates", tags=["candidates"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])



@app.get("/", tags=["root"])
async def root():
    return {"service": "ScoutGrid Candidate Service", "version": "0.1.0"}


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
