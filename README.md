# RootAI Core – Secure Understanding Engine

RootAI Core is an **understanding-first reasoning layer** that sits between a user and any LLM (DeepSeek, Claude, GPT, local models, etc.). Instead of asking the model to "figure everything out," RootAI:

1. **Deconstructs** the query into concepts, entities, and assumptions.  
2. **Grounds** those concepts in an Etymological Knowledge Graph + curated documents.  
3. **Builds a structured reasoning blueprint** (core concepts, verified facts, logical constraints).  
4. **Hands that blueprint to an LLM** as a constrained text generator.  
5. **Verifies the answer** against the blueprint before returning it.

This repo is the *SecureCode* specialization of RootAI Core: it focuses on coding, security, pentesting, and reverse‑engineering tasks, but the architecture is designed to support additional domain packs (legal, compliance, etc.) using the same core.

> Status: **Early MVP** – core API scaffolded, components and domain packs are being implemented step‑by‑step.

---

## High‑level architecture

RootAI Core mirrors this flow:

1. **Prompt Analyzer (Semantic Deconstructor)**  
   - Breaks a user query into entities, actions, claims, and implicit assumptions.  
   - Uses dependency parsing and related NLP tools to map "who does what to whom, how, and why."

2. **Dual Knowledge System**  
   - **Etymological Knowledge Graph (EKG)** – graph DB of concepts and historical roots (e.g., *session*, *auth*, *inject*), used to anchor meaning.  
   - **Document Store / RAG Engine** – curated corpora (OWASP, CWE, secure coding guides, legal texts, etc.) indexed for retrieval.

3. **Reasoning Bridge & Causal / Constraint Checker**  
   - Fuses the deconstruction + retrieved knowledge into a **Core Concept Map** and a set of **MUST / MUST‑NOT** constraints.  
   - Produces a **Verified, Structured Execution Plan** that any LLM must follow.

4. **Standard LLM (Generation Engine)**  
   - Receives the execution plan and generates fluent text (code, explanations, reports) under those constraints.  
   - The LLM is treated as a powerful syntax engine, *not* as the source of truth.

5. **Resource Manager (apt‑like updater)**  
   - Manages updates to the EKG and document store via a manifest (e.g., `resources.json`).  
   - Runs consistency checks (e.g., no circular graph references) so the understanding layer can be patched like software without retraining the LLM.

---

## SecureCode specialization (this repo)

The **SecureCode** flavor applies RootAI Core to security‑critical coding and pentesting tasks:

- **Secure coding assistant**  
  - Builds a blueprint for prompts like "Write a secure login API" with constraints such as:  
    - no `eval` / `exec`  
    - prepared statements for DB access  
    - HTTPS‑only assumptions  
    - proper password hashing and session handling.

- **Bug bounty & pentest helper**  
  - Analyzes endpoints and code snippets to propose *grounded* vuln hypotheses (e.g., IDOR, session fixation), backed by CWE/OWASP references rather than hallucinations.  
  - Generates PoC scaffolds and structured reports from a verified reasoning plan.

- **Reverse engineering support (planned)**  
  - Helps explain obfuscated code or suspicious control flows using semantic decomposition and EKG concepts (e.g., hooks, injection, shellcode).

All of this is driven by **domain packs** that configure RootAI Core for a particular space:

- `packs/secure-code.yaml` – constraints and knowledge sources for secure coding.  
- Future packs: `pentest-bounty.yaml`, `reverse-eng.yaml`, `legal.yaml`, etc.

---

## Current project structure

> This will evolve as we implement each box in the architecture diagram.

```text
RootAI/
├── rootai/
│   └── __init__.py                        # RootAI Core package
├── tests/
│   └── test_authority_gate.py             # Authority gate unit tests
├── Etymological_Seeder.py                 # Seeds Neo4j with etymological concepts (Path A)
├── Knowledge_Graph_Navigator.py           # Navigates the EKG for semantic context
├── unified_pipeline.py                    # Full RootAI pipeline orchestration
├── reliability_score.py                   # Quality scoring and integrity checks
├── rootaidashboard.py                     # Reasoning bridge visualization
├── poc_v2.jsx                             # React prototype (grounded AI UI)
├── red_team_simulation.py                 # Data poisoning attack simulation
├── authority_gate.py                      # Authorization enforcement (irreversible boundary)
├── authority_interceptor.py               # Authorization interception
├── main.py                                # FastAPI entrypoint & HTTP API
├── Dockerfile                             # Docker image definition
├── docker-compose.yml                     # Multi-service orchestration (API + Neo4j)
├── requirements.txt                       # Python dependencies
└── README.md                              # You are here
```

---

## Getting started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- A Neo4j instance (provided via Docker Compose)
- NVD API key (for CVE lookups)

### Running with Docker

```bash
# Copy and populate the environment file
cp .env.example .env   # set NEO4J_PASSWORD and ROOTAI_AUTH_TOKEN

# Build and start the API + Neo4j
docker-compose up --build
```

The API will be available at `http://localhost:8000`.

### Running locally

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn main:app --reload
```

### Running tests

```bash
pytest tests/
```

---

## Security principles

- **Timing-safe token comparison** – `authority_gate.py` uses `hmac.compare_digest` on SHA-256 hashes to prevent timing-based enumeration attacks.
- **WORM integrity** – domain pack YAML files are mounted read-only in Docker and verified via SHA-256 before each pipeline run.
- **Authority gate** – high-risk actions (`FILE_DELETE`, `NETWORK_EXFIL`, `SYS_WRITE`) require an explicit governance token and are blocked at the "irreversible boundary."
