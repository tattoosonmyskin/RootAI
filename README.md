#
  ## RootAI Core – Secure Understanding Engine

RootAI Core is an **understanding-first reasoning layer** that sits between a user and any LLM (DeepSeek, Claude, GPT, local models, etc.). Instead of asking the model to “figure everything out,” RootAI:

1. **Deconstructs** the query into concepts, entities, and assumptions.  
2. **Grounds** those concepts in an Etymological Knowledge Graph + curated documents.  
3. **Builds a structured reasoning blueprint** (core concepts, verified facts, logical constraints).  
4. **Hands that blueprint to an LLM** as a constrained text generator.  
5. **Verifies the answer** against the blueprint before returning it.

This repo is the *SecureCode* specialization of RootAI Core: it focuses on coding, security, pentesting, and reverse‑engineering tasks, but the architecture is designed to support additional domain packs (legal, compliance, etc.) using the same core. [file:17][file:16]

> Status: **Early MVP** – core API scaffolded, components and domain packs are being implemented step‑by‑step.

---

## High‑level architecture

RootAI Core mirrors this flow:

1. **Prompt Analyzer (Semantic Deconstructor)**  
   - Breaks a user query into entities, actions, claims, and implicit assumptions.  
   - Uses dependency parsing and related NLP tools to map “who does what to whom, how, and why.” [file:17]

2. **Dual Knowledge System**  
   - **Etymological Knowledge Graph (EKG)** – graph DB of concepts and historical roots (e.g., *session*, *auth*, *inject*), used to anchor meaning.  
   - **Document Store / RAG Engine** – curated corpora (OWASP, CWE, secure coding guides, legal texts, etc.) indexed for retrieval. [file:17][file:16]

3. **Reasoning Bridge & Causal / Constraint Checker**  
   - Fuses the deconstruction + retrieved knowledge into a **Core Concept Map** and a set of **MUST / MUST‑NOT** constraints.  
   - Produces a **Verified, Structured Execution Plan** that any LLM must follow. [file:17]

4. **Standard LLM (Generation Engine)**  
   - Receives the execution plan and generates fluent text (code, explanations, reports) under those constraints.  
   - The LLM is treated as a powerful syntax engine, *not* as the source of truth. [file:16]

5. **Resource Manager (apt‑like updater)**  
   - Manages updates to the EKG and document store via a manifest (e.g., `resources.json`).  
   - Runs consistency checks (e.g., no circular graph references) so the understanding layer can be patched like software without retraining the LLM. [file:17]

This is exactly the conceptual architecture shown in the RootAI diagram: the understanding engine in the middle, the LLM on the output side. [file:18]

---

## SecureCode specialization (this repo)

The **SecureCode** flavor applies RootAI Core to security‑critical coding and pentesting tasks:

- **Secure coding assistant**  
  - Builds a blueprint for prompts like “Write a secure login API” with constraints such as:  
    - no `eval` / `exec`  
    - prepared statements for DB access  
    - HTTPS‑only assumptions  
    - proper password hashing and session handling. [file:17]

- **Bug bounty & pentest helper**  
  - Analyzes endpoints and code snippets to propose *grounded* vuln hypotheses (e.g., IDOR, session fixation), backed by CWE/OWASP references rather than hallucinations. [file:17]  
  - Generates PoC scaffolds and structured reports from a verified reasoning plan.

- **Reverse engineering support (planned)**  
  - Helps explain obfuscated code or suspicious control flows using semantic decomposition and EKG concepts (e.g., hooks, injection, shellcode). [file:17]

All of this is driven by **domain packs** that configure RootAI Core for a particular space:

- `packs/secure-code.yaml` – constraints and knowledge sources for secure coding.  
- Future packs: `pentest-bounty.yaml`, `reverse-eng.yaml`, `legal.yaml`, etc.

---

## Current project structure

> This will evolve as we implement each box in the architecture diagram. [file:17][file:16]

```text
rootai-secure/
├── api/
│   └── main.py          # FastAPI entrypoint & HTTP API
├── core/
│   ├── __init__.py      # RootAI Core package
│   └── deconstructor.py # (WIP) Semantic deconstruction
├── packs/
│   └── secure-code.yaml # Secure coding domain pack (constraints, terms)
├── docker-compose.yml   # (WIP) API + Neo4j + LLM containers
├── requirements.txt     # Python dependencies
└── README.md            # You are here
