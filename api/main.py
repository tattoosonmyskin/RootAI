"""
RootAI FastAPI application.

Endpoints
---------
GET  /health              – liveness probe
POST /authority/verify    – check whether an action is authorised
POST /pipeline/execute    – run the unified RootAI pipeline
"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager

# Ensure the repo root is on sys.path so sibling modules are importable
# when the app is launched via `uvicorn api.main:app`.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from typing import Optional

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from authority_gate import AuthorityGate
from deconstructor import deconstruct
from integrity_manager import evaluate_source_quality, verify_worm_integrity
from kg_navigator import KnowledgeGraphNavigator

# ---------------------------------------------------------------------------
# Application lifespan – initialise shared resources once at startup
# ---------------------------------------------------------------------------

_kg: Optional[KnowledgeGraphNavigator] = None


@asynccontextmanager
async def lifespan(application: FastAPI):
    global _kg
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "rootai")
    _kg = KnowledgeGraphNavigator(neo4j_uri, neo4j_user, neo4j_password)
    yield
    if _kg is not None:
        _kg.close()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="RootAI API", version="1.0.0", lifespan=lifespan)

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str


class ActionRequest(BaseModel):
    action: str
    token: Optional[str] = None


class AuthorityResponse(BaseModel):
    action: str
    authorized: bool


class PipelineRequest(BaseModel):
    query: str
    worm_path: str = "packs/secure-code.yaml"
    expected_hash: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe."""
    return HealthResponse(status="ok")


@app.post("/authority/verify", response_model=AuthorityResponse)
def authority_verify(req: ActionRequest) -> AuthorityResponse:
    """Check whether *action* is authorised with the supplied *token*."""
    gate = AuthorityGate()
    authorized = gate.verify_authority(req.action, req.token)
    return AuthorityResponse(action=req.action, authorized=authorized)


@app.post("/pipeline/execute")
def pipeline_execute(req: PipelineRequest) -> dict:
    """
    Run the RootAI unified pipeline:

    1. Deconstruct the query (Prompt Analyzer).
    2. Map terms to the Knowledge Graph (Path A).
    3. Load WORM constraints — skip integrity check when no hash is supplied
       so that the API remains useful without a pre-computed hash (Path B).
    4. Score grounding quality and return a Verified Execution Plan.
    """
    # Step 1 – Prompt Analyzer
    analysis = deconstruct(req.query)
    terms = analysis["nouns"]

    # Step 2 – Path A: Knowledge Graph Navigator (shared instance)
    kg = _kg
    semantic_map = kg.get_semantic_context(terms) if kg is not None else {}

    # Step 3 – Path B: Resource Manager / WORM
    if req.expected_hash:
        if not verify_worm_integrity(req.worm_path, req.expected_hash):
            raise HTTPException(status_code=409, detail="WORM integrity check failed")

    try:
        with open(req.worm_path, "r") as fh:
            grounding_data = yaml.safe_load(fh)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"WORM file not found: {req.worm_path}")

    # Step 4 – Reasoning Bridge & Constraint Checker
    quality_report = evaluate_source_quality(str(grounding_data), len(grounding_data))

    return {
        "intent": req.query,
        "semantic_roots": semantic_map,
        "hard_constraints": grounding_data.get("constraints", {}).get("hard", []),
        "reliability": quality_report.score,
        "hallucination_risk": "low" if quality_report.score > 0.7 else "high",
    }
