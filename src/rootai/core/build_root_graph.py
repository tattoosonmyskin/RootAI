#!/usr/bin/env python3
"""
Root Graph Builder - Reproducible Faiss Index Construction

This module provides tools for building reproducible Faiss indexes
from Arabic root embeddings using CAMeL Tools or fallback methods.
"""

import argparse
import pickle
import sys
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np

try:
    from camel_tools.morphology.database import MorphologyDB
    from camel_tools.morphology.analyzer import Analyzer
    CAMEL_AVAILABLE = True
except ImportError:
    CAMEL_AVAILABLE = False
    print("Warning: camel-tools not available. Using fallback embeddings.")

try:
    from transformers import T5Tokenizer, T5ForConditionalGeneration
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not available. Using random embeddings.")

from ..graph_sharding import GraphSharding


def generate_sample_roots(n_roots: int = 1000, seed: int = 42) -> List[Dict]:
    """
    Generate sample root metadata for testing.
    
    Args:
        n_roots: Number of roots to generate
        seed: Random seed for reproducibility
        
    Returns:
        List of root metadata dictionaries
    """
    np.random.seed(seed)
    
    roots = []
    for i in range(n_roots):
        root = {
            'id': i,
            'root': f'root_{i:04d}',
            'frequency': np.random.randint(1, 1000),
            'pos_tags': ['NOUN', 'VERB', 'ADJ'][np.random.randint(0, 3)],
            'source': 'synthetic'
        }
        roots.append(root)
    
    return roots


def create_embeddings_with_t5(
    roots: List[Dict],
    model_name: str = "google/t5-v1_1-base",
    device: str = "cpu"
) -> np.ndarray:
    """
    Create embeddings for roots using T5 model.
    
    Args:
        roots: List of root metadata
        model_name: HuggingFace T5 model name
        device: Device to run model on
        
    Returns:
        Numpy array of embeddings (n_roots, dimension)
    """
    if not TRANSFORMERS_AVAILABLE:
        print("Transformers not available, using random embeddings")
        return create_random_embeddings(len(roots), 768)
    
    print(f"Loading T5 model: {model_name}")
    tokenizer = T5Tokenizer.from_pretrained(model_name)
    model = T5ForConditionalGeneration.from_pretrained(model_name)
    model = model.to(device)
    model.eval()
    
    embeddings = []
    
    print(f"Creating embeddings for {len(roots)} roots...")
    for i, root in enumerate(roots):
        if (i + 1) % 100 == 0:
            print(f"  Progress: {i + 1}/{len(roots)}")
        
        # Use root string as input
        root_text = root['root']
        inputs = tokenizer(root_text, return_tensors="pt", padding=True, truncation=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model.encoder(**inputs)
            # Use mean pooling of encoder outputs
            embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
        
        embeddings.append(embedding[0])
    
    return np.array(embeddings, dtype='float32')


def create_random_embeddings(n_roots: int, dimension: int = 768, seed: int = 42) -> np.ndarray:
    """
    Create random embeddings for fallback/testing.
    
    Args:
        n_roots: Number of embeddings to create
        dimension: Embedding dimension
        seed: Random seed
        
    Returns:
        Numpy array of random embeddings
    """
    np.random.seed(seed)
    embeddings = np.random.randn(n_roots, dimension).astype('float32')
    # Normalize embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / (norms + 1e-8)
    return embeddings


def load_camel_roots(max_roots: Optional[int] = None) -> List[Dict]:
    """
    Load actual Arabic roots from CAMeL Tools database.
    
    Args:
        max_roots: Maximum number of roots to load (None for all)
        
    Returns:
        List of root metadata from CAMeL Tools
        
    TODO: Implement actual CAMeL Tools root extraction
    """
    if not CAMEL_AVAILABLE:
        print("CAMeL Tools not available. Using synthetic roots.")
        return generate_sample_roots(max_roots or 1000)
    
    print("TODO: Implement CAMeL Tools root extraction")
    print("For now, using synthetic roots.")
    return generate_sample_roots(max_roots or 1000)


def build_index(
    n_roots: int = 1000,
    dimension: int = 768,
    use_camel: bool = True,
    use_gpu: bool = False,
    seed: int = 42,
    output_index: str = "data/roots.index",
    output_metadata: str = "data/roots_metadata.pkl"
) -> None:
    """
    Build and save a Faiss index with root embeddings.
    
    Args:
        n_roots: Number of roots to include
        dimension: Embedding dimension
        use_camel: Whether to use CAMeL Tools (fallback to synthetic if unavailable)
        use_gpu: Whether to use GPU for embedding creation
        seed: Random seed for reproducibility
        output_index: Path to save Faiss index
        output_metadata: Path to save metadata pickle
    """
    print("=" * 70)
    print("RootAI v3.0 - Root Graph Builder")
    print("=" * 70)
    print(f"Roots: {n_roots}")
    print(f"Dimension: {dimension}")
    print(f"Use CAMeL: {use_camel}")
    print(f"Use GPU: {use_gpu}")
    print(f"Seed: {seed}")
    print(f"Output Index: {output_index}")
    print(f"Output Metadata: {output_metadata}")
    print()
    
    # Load or generate roots
    print("Step 1: Loading roots...")
    if use_camel:
        roots = load_camel_roots(max_roots=n_roots)
    else:
        roots = generate_sample_roots(n_roots=n_roots, seed=seed)
    print(f"  Loaded {len(roots)} roots")
    
    # Create embeddings
    print("\nStep 2: Creating embeddings...")
    device = "cuda" if use_gpu and TRANSFORMERS_AVAILABLE else "cpu"
    
    if TRANSFORMERS_AVAILABLE:
        embeddings = create_embeddings_with_t5(roots, device=device)
    else:
        embeddings = create_random_embeddings(len(roots), dimension, seed)
    
    print(f"  Created embeddings: {embeddings.shape}")
    
    # Build Faiss index
    print("\nStep 3: Building Faiss index...")
    sharder = GraphSharding(dimension=dimension, use_gpu=use_gpu)
    sharder.build_index(embeddings, roots)
    print(f"  Index built with {sharder.index.ntotal} vectors")
    
    # Save index and metadata
    print("\nStep 4: Saving index and metadata...")
    
    # Create output directories if needed
    Path(output_index).parent.mkdir(parents=True, exist_ok=True)
    Path(output_metadata).parent.mkdir(parents=True, exist_ok=True)
    
    # Save index
    sharder.save_index(output_index)
    print(f"  ✓ Index saved to {output_index}")
    
    # Save metadata
    with open(output_metadata, 'wb') as f:
        pickle.dump(roots, f)
    print(f"  ✓ Metadata saved to {output_metadata}")
    
    print("\n" + "=" * 70)
    print("Index building complete!")
    print("=" * 70)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Build reproducible Faiss index for RootAI"
    )
    parser.add_argument(
        "--roots",
        type=int,
        default=1000,
        help="Number of roots to include in index (default: 1000)"
    )
    parser.add_argument(
        "--dimension",
        type=int,
        default=768,
        help="Embedding dimension (default: 768 for T5-base)"
    )
    parser.add_argument(
        "--output",
        default="data/roots.index",
        help="Output path for Faiss index (default: data/roots.index)"
    )
    parser.add_argument(
        "--metadata",
        default="data/roots_metadata.pkl",
        help="Output path for metadata (default: data/roots_metadata.pkl)"
    )
    parser.add_argument(
        "--use-camel",
        action="store_true",
        help="Use CAMeL Tools for actual Arabic roots (falls back to synthetic if unavailable)"
    )
    parser.add_argument(
        "--gpu",
        action="store_true",
        help="Use GPU for embedding creation"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    
    args = parser.parse_args()
    
    build_index(
        n_roots=args.roots,
        dimension=args.dimension,
        use_camel=args.use_camel,
        use_gpu=args.gpu,
        seed=args.seed,
        output_index=args.output,
        output_metadata=args.metadata
    )


if __name__ == "__main__":
    main()
