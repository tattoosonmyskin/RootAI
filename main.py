from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="RootAI Secure API")


class Query(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/secure-generate")
def secure_generate(q: Query):
    """Secure code generation endpoint using the RootAI reasoning pipeline."""
    return {"query": q.query, "status": "pipeline not yet configured"}
