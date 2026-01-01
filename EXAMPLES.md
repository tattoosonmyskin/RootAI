# RootAI v3.0 - Quick Start Examples

## Example 1: Simple Reasoning Query

```python
from src.core.root_reasoner import RootReasoner
from src.core.graph_sharding import create_sample_index

# Initialize
reasoner = RootReasoner(use_gpu=False)
sharder = create_sample_index(n_roots=1000)
reasoner.set_graph_sharder(sharder)

# Query
result = reasoner.reason("What is the meaning of justice?")
print(result['answer'])
```

## Example 2: Hybrid Architecture with GPT

```python
import os
from src.core.root_reasoner import RootReasoner
from src.core.graph_sharding import create_sample_index

# Initialize with OpenAI API key
reasoner = RootReasoner(
    use_gpu=False,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    gpt_model="gpt-3.5-turbo"
)

# Set up graph index
sharder = create_sample_index(n_roots=1000)
reasoner.set_graph_sharder(sharder)

# Use hybrid reasoning: RootAI (grounding) → GPT (generation)
result = reasoner.reason_hybrid(
    "What is justice in Islamic philosophy?",
    k=5,
    use_gpt=True,
    max_tokens=200
)

print(f"Pipeline: {result['pipeline']}")
print(f"Mode: {result['mode']}")
print(f"Answer: {result['answer']}")
```

## Example 3: Semantic Grounding Layer

```python
from src.core.semantic_grounding import SemanticGroundingLayer

# Create grounding layer
grounding = SemanticGroundingLayer(template_style="conversational")

# Format semantic context from RootAI
roots = [
    {'word': 'العدالة', 'root': 'عدل', 'pos': 'NOUN'},
    {'word': 'الحكم', 'root': 'حكم', 'pos': 'NOUN'}
]

semantic_context = grounding.format_semantic_context(roots)

# Create grounded prompt for GPT
query = "What is justice?"
grounded_prompt = grounding.create_grounded_prompt(
    query,
    semantic_context,
    constraints=[
        "Base your answer on the semantic roots provided",
        "Maintain factual accuracy"
    ]
)

print(grounded_prompt)
```

## Example 4: Two-Stage Pipeline (Manual)

```python
# Stage 1: RootAI Reasoning (Semantic Grounding)
roots = reasoner.decompose(query)  # Arabic, Latin, etc.
semantic_context = reasoner.graph_retrieve(roots)  # Verified paths

# Stage 2: GPT Generation (with grounding)
from src.core.semantic_grounding import create_grounded_prompt_simple

grounded_prompt = create_grounded_prompt_simple(
    query,
    roots,
    reasoner.grounding_layer.format_semantic_context(roots, semantic_context)
)

# Generate with GPT
response = reasoner.generate_with_gpt(query, semantic_context)
print(response)
```

## Example 5: Arabic Text Processing

```python
from src.core.root_reasoner import RootReasoner

reasoner = RootReasoner()

# Decompose Arabic text
text = "العدالة أساس الحكم"  # Justice is the foundation of governance
roots = reasoner.decompose(text)

for root in roots:
    print(f"{root['word']} → root: {root['root']}")
```

## Example 6: Using the REST API

```bash
# Start server
python api/fastapi_app.py

# In another terminal, make a request:
curl -X POST http://localhost:8080/reason \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain the concept of justice in Islamic law",
    "k": 5,
    "max_tokens": 200,
    "include_analysis": true
  }'
```

## Example 7: Building Custom Index

```python
import numpy as np
from src.core.graph_sharding import GraphSharding

# Create embeddings (in production, use real Arabic embeddings)
embeddings = np.random.randn(10000, 768).astype('float32')

# Create metadata
metadata = [
    {'id': i, 'root': f'root_{i}', 'frequency': 100}
    for i in range(10000)
]

# Build index
sharder = GraphSharding(dimension=768, index_type="IVF")
sharder.build_index(embeddings, metadata)

# Save for later use
sharder.save_index('data/custom_roots.index')
```

## Example 8: Batch Processing

```python
queries = [
    "What is justice?",
    "Explain mercy in Islam",
    "Define righteousness"
]

results = []
for query in queries:
    result = reasoner.reason(query, k=5)
    results.append(result['answer'])
    
for i, answer in enumerate(results):
    print(f"\nQuery {i+1}: {queries[i]}")
    print(f"Answer: {answer}")
```

## Example 9: Using CLI

```bash
# Reason about a query
./rootai_cli.py reason "What is the meaning of life?" --verbose

# Run benchmark
./rootai_cli.py benchmark --questions 50 --gpu

# Build graph index
./rootai_cli.py index --build --roots 10000 --output data/roots.index

# Start server
./rootai_cli.py server --port 8080 --reload
```

## Example 10: Docker Deployment

```bash
# Build
docker build -t rootai:v3.0 .

# Run
docker run -p 8080:8080 -e PORT=8080 rootai:v3.0

# Test
curl http://localhost:8080/health
```

## Example 11: Load Pre-built Index

```python
from src.core.root_reasoner import RootReasoner

# Load with pre-built index
reasoner = RootReasoner(
    model_name="google/t5-v1_1-base",
    graph_index_path="data/roots.index",
    use_gpu=True
)

# Query directly
result = reasoner.reason("What is wisdom?")
print(result['answer'])
```

## Example 12: Custom Pipeline Steps

```python
# Step 1: Decompose only
roots = reasoner.decompose("الحكمة نور العقل")
print("Roots:", [r['root'] for r in roots])

# Step 2: Retrieve similar roots
enhanced = reasoner.graph_retrieve(roots, k=10)
print("Similar roots:", enhanced[0]['similar_roots'][:3])

# Step 3: Generate with context
answer = reasoner.generate("What is wisdom?", enhanced)
print("Answer:", answer)
```

## Example 13: Hybrid with Different GPT Models

```python
# Use GPT-4 for higher quality
reasoner_gpt4 = RootReasoner(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    gpt_model="gpt-4"
)

# Use GPT-3.5 for faster/cheaper responses
reasoner_gpt35 = RootReasoner(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    gpt_model="gpt-3.5-turbo"
)
```

## Example 14: Verification and Quality Control

```python
from src.core.semantic_grounding import SemanticGroundingLayer

grounding = SemanticGroundingLayer()

# Extract verification data
verification = grounding.extract_verification_data(roots, enhanced_roots)

print(f"Number of roots: {verification['num_roots']}")
print(f"Graph enhancement: {verification['has_graph_enhancement']}")
print(f"Retrieval coverage: {verification['graph_retrieval_coverage']:.2%}")
```

## Example 15: Benchmark Evaluation

```python
from benchmarks.semantic_mmlu import SemanticMMLU

benchmark = SemanticMMLU(reasoner)
result = benchmark.run_benchmark(max_questions=100)

print(f"Accuracy: {result.accuracy:.2f}%")
print(f"Target achieved: {result.accuracy >= 92.0}")
```

## Performance Tips

1. **Use GPU**: Set `use_gpu=True` for 3-5x speedup
2. **Batch requests**: Process multiple queries together
3. **Cache index**: Pre-build and save Faiss index
4. **Adjust k**: Lower k for faster retrieval
5. **Limit tokens**: Reduce max_tokens for faster generation
6. **Choose GPT model wisely**: gpt-3.5-turbo for speed, gpt-4 for quality

## Common Issues

**Q: ImportError for faiss-gpu**
```bash
pip install faiss-gpu --index-url https://download.pytorch.org/whl/cu118
```

**Q: Out of memory**
```python
# Use smaller model or CPU
reasoner = RootReasoner(use_gpu=False)
```

**Q: Slow inference**
```python
# Reduce complexity
result = reasoner.reason(query, k=3, max_new_tokens=100)
```

**Q: OpenAI API errors**
```python
# Set API key via environment variable
export OPENAI_API_KEY="your-api-key-here"

# Or pass directly (less secure)
reasoner = RootReasoner(openai_api_key="your-api-key")
```

## Next Steps

- Explore the [full API documentation](api/fastapi_app.py)
- Read the [deployment guide](DEPLOYMENT.md)
- Check [benchmark results](benchmarks/semantic_mmlu.py)
- Join the community discussions
