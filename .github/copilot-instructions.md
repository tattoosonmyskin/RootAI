# GitHub Copilot Instructions for RootAI

## Project Overview

RootAI is an **understanding-first reasoning layer** that sits between users and LLMs (DeepSeek, Claude, GPT, local models). It deconstructs queries, grounds concepts in an Etymological Knowledge Graph, builds structured reasoning blueprints, and verifies answers before returning them.

This repository contains the **SecureCode** specialization of RootAI Core, focused on coding, security, pentesting, and reverse-engineering tasks.

## Architecture

The pipeline follows these steps:
1. **Prompt Analyzer** – deconstructs queries into entities, actions, and assumptions
2. **Dual Knowledge System** – Etymological Knowledge Graph (EKG) + Document Store/RAG Engine
3. **Reasoning Bridge** – fuses deconstruction + retrieved knowledge into a Core Concept Map
4. **Generation Engine** – standard LLM receives the execution plan (treated as syntax engine, not source of truth)
5. **Resource Manager** – manages updates to EKG and document store via manifest

## Key Files

- `authority_gate.py` – Authority gate enforcing the "irreversible boundary" for protected actions
- `authority_interceptor.py` – Authority interceptor wrapping the gate for the pipeline
- `unified_pipeline` – Main RootAI pipeline integrating all components
- `reliability_score` – Source quality evaluation and WORM integrity verification
- `rootaidashboard` – Reasoning bridge visualization
- `Etymological_Seeder` – Seeds the Neo4j etymological knowledge graph
- `Knowledge_Graph_Navigator` – Queries semantic context from the graph
- `tests/` – pytest test suite

## Security Principles

- **Authority Gate**: Protected actions (`FILE_DELETE`, `NETWORK_EXFIL`, `SYS_WRITE`) require token authorization
- **Timing-safe comparisons**: Always use `hmac.compare_digest` for token validation, never direct string equality
- **WORM integrity**: Document store integrity is verified via SHA-256 before use
- **Defense in depth**: Docker read-only mounts + hash verification for data poisoning prevention

## Code Style

- Python 3.10+
- Use `hmac.compare_digest` for all secret/token comparisons (prevents timing attacks)
- Guard module-level executable code with `if __name__ == "__main__":`
- Tests use `pytest` with `unittest.mock` for environment variable patching
- Class-based organization with docstrings on public methods
