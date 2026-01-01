# RootAI v3.0 Methodology & Reproducibility

## Overview

This document describes the methodology, evaluation metrics, and reproducibility procedures for RootAI v3.0, a hybrid semantic reasoning system combining Arabic morphological analysis with transformer models (T5/GPT).

## System Architecture

### Pipeline
1. **Decompose**: Arabic root extraction using CAMeL Tools morphological analysis
2. **Graph**: Faiss-based similarity retrieval of related roots
3. **Generate**: T5 or GPT-based natural language generation with semantic grounding

### Hybrid Mode (Optional)
- **Stage 1 (RootAI)**: Semantic grounding through root decomposition and graph retrieval
- **Stage 2 (GPT)**: Natural language generation using grounded context
- GPT integration is optional and gated behind `OPENAI_API_KEY` environment variable

## Evaluation Metrics

### Root Accuracy (Micro-evaluation)
- **Definition**: Percentage of correctly identified Arabic roots in morphological decomposition
- **Measurement**: Compare extracted roots against CAMeL Tools gold standard
- **Target**: ≥95% for Arabic text, N/A for non-Arabic text

### Semantic Accuracy
- **Definition**: Percentage of correct answers on semantic reasoning tasks
- **Benchmark**: Semantic MMLU (custom subset focusing on semantic understanding)
- **Target**: ≥92% (vs GPT-3.5 baseline ~67%)

### Hallucination Rate
- **Definition**: Percentage of answers containing factually incorrect or unsupported claims
- **Detection**: Manual review + automated consistency checks
- **Acceptable**: <5% for grounded responses

### Fallback Transparency
- **Definition**: When answer extraction fails, system defaults to option A (index 0)
- **Reporting**: All benchmarks report fallback count: "Fallback answers used: N"
- **Interpretation**: High fallback rate indicates poor answer generation or extraction

## Reproducibility

### Environment
```bash
# Python version
Python 3.9, 3.10, or 3.11

# Core dependencies (see requirements.txt)
camel-tools>=1.5.0
transformers>=4.30.0
faiss-cpu>=1.7.4  # or faiss-gpu for GPU

# Installation
pip install -e .[cpu]  # CPU mode
pip install -e .[gpu]  # GPU mode
```

### Seeds & Randomness
- **Random seed**: Fixed at 42 for all experiments (when applicable)
- **Faiss index**: Deterministic build with fixed embedding order
- **Model sampling**: Temperature=0.7, top_p=0.9 (configurable)

### Dataset Versions
- **Demo benchmark**: 100 synthetic questions (10 templates × 10 variations)
- **Official MMLU**: Planned - subset focused on logic, semantics, reasoning (see `experiments/mmlu_run.py`)
- **Custom tasks**: Holmes reasoning adapter (see `experiments/holmes_adapter.py`)

### Model Versions
- **T5**: `google/t5-v1_1-base` (HuggingFace)
- **CAMeL Tools**: v1.5.0 or later
- **GPT (optional)**: `gpt-3.5-turbo` or `gpt-4` via OpenAI API

### Index Construction
```bash
# Build reproducible Faiss index
python -m rootai.core.build_root_graph \
  --roots 10000 \
  --dimension 768 \
  --output data/roots.index

# Or via CLI
rootai index --build --roots 10000 --output data/roots.index
```

## Benchmark Execution

### Demo Benchmark (Synthetic)
```bash
# Quick 20-question test (CI/CD)
python benchmarks/semantic_mmlu.py

# Full 100-question test
python benchmarks/semantic_mmlu.py --max-questions 100

# Outputs: benchmark_results.json
```

### Official MMLU Subset (Future)
```bash
# Run official MMLU subset
python experiments/mmlu_run.py \
  --subset logic,semantics,reasoning \
  --seed 42 \
  --output results/mmlu_YYYYMMDD.csv

# Generates:
# - results/mmlu_YYYYMMDD.csv (results)
# - results/mmlu_prompts_YYYYMMDD.txt (prompts for review)
```

## Results Categories

### Demo Results (Synthetic)
- Source: `benchmarks/semantic_mmlu.py`
- Questions: 100 synthetic questions (10 categories)
- Purpose: Quick validation, CI/CD testing
- **Limitation**: Not representative of real-world performance

### Official Results (External Datasets)
- Source: MMLU subsets, custom reasoning tasks
- Questions: External validated benchmarks
- Purpose: Rigorous evaluation, publication
- **Status**: Planned (see `experiments/`)

## Data & Artifacts

All benchmark results are stored in `results/`:
- `results/benchmark_results.json` - Latest demo run
- `results/mmlu_YYYYMMDD.csv` - Official MMLU runs (date-stamped)
- `results/METHODOLOGY.md` - This document

## Versioning

- **RootAI Version**: 3.0.1
- **Benchmark Version**: Demo v1.0, Official TBD
- **Last Updated**: 2026-01-01

## Contact & Citation

For questions about methodology or reproducibility:
- GitHub: https://github.com/tattoosonmyskin/RootAI
- Issues: https://github.com/tattoosonmyskin/RootAI/issues

When citing this work, please reference:
```
RootAI v3.0: Root graphs + T5/GPT hybrid reasoning
https://github.com/tattoosonmyskin/RootAI
```
