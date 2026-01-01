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

## Example 2: Arabic Text Processing

```python
from src.core.root_reasoner import RootReasoner

reasoner = RootReasoner()

# Decompose Arabic text
text = "العدالة أساس الحكم"  # Justice is the foundation of governance
roots = reasoner.decompose(text)

for root in roots:
    print(f"{root['word']} → root: {root['root']}")
```

## Example 3: Using the REST API

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

## Example 4: Building Custom Index

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

## Example 5: Batch Processing

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

## Example 6: Using CLI

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

## Example 7: Docker Deployment

```bash
# Build
docker build -t rootai:v3.0 .

# Run
docker run -p 8080:8080 -e PORT=8080 rootai:v3.0

# Test
curl http://localhost:8080/health
```

## Example 8: Load Pre-built Index

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

## Example 9: Custom Pipeline Steps

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

## Example 10: Benchmark Evaluation

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

## Next Steps

- Explore the [full API documentation](api/fastapi_app.py)
- Read the [deployment guide](DEPLOYMENT.md)
- Check [benchmark results](benchmarks/semantic_mmlu.py)
- Join the community discussions
