"""
Graph Sharding Module for RootAI v3.0

This module implements efficient graph sharding using Faiss for indexing
and retrieving 1M+ Arabic root embeddings for semantic reasoning.
"""

import os
import pickle
from typing import List, Tuple, Optional, Dict
import numpy as np

try:
    import faiss
except ImportError:
    faiss = None
    print("Warning: faiss-gpu not installed. Install with: pip install faiss-gpu")


class GraphSharding:
    """
    Manages graph sharding with Faiss indexing for efficient root retrieval.
    
    Supports 1M+ root embeddings with GPU acceleration for fast semantic search.
    """
    
    def __init__(
        self,
        dimension: int = 768,
        index_type: str = "IVF",
        use_gpu: bool = True,
        nlist: int = 100,
        nprobe: int = 10
    ):
        """
        Initialize graph sharding system.
        
        Args:
            dimension: Embedding dimension (default 768 for T5)
            index_type: Faiss index type ('Flat', 'IVF', 'HNSW')
            use_gpu: Whether to use GPU acceleration
            nlist: Number of clusters for IVF index
            nprobe: Number of clusters to search
        """
        self.dimension = dimension
        self.index_type = index_type
        self.use_gpu = use_gpu
        self.nlist = nlist
        self.nprobe = nprobe
        self.index = None
        self.root_metadata = []  # Store root strings and metadata
        
    def build_index(self, embeddings: np.ndarray, metadata: Optional[List[Dict]] = None):
        """
        Build Faiss index from root embeddings.
        
        Args:
            embeddings: Array of shape (n_roots, dimension)
            metadata: Optional list of dictionaries containing root information
        """
        if faiss is None:
            raise RuntimeError("faiss-gpu not installed")
            
        n_roots = embeddings.shape[0]
        print(f"Building Faiss index for {n_roots} roots...")
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create index based on type
        if self.index_type == "Flat":
            index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine
        elif self.index_type == "IVF":
            quantizer = faiss.IndexFlatIP(self.dimension)
            index = faiss.IndexIVFFlat(quantizer, self.dimension, self.nlist)
            # Train index on embeddings
            index.train(embeddings)
            index.nprobe = self.nprobe
        elif self.index_type == "HNSW":
            index = faiss.IndexHNSWFlat(self.dimension, 32)
        else:
            raise ValueError(f"Unknown index type: {self.index_type}")
        
        # Move to GPU if available and requested
        if self.use_gpu and faiss.get_num_gpus() > 0:
            res = faiss.StandardGpuResources()
            index = faiss.index_cpu_to_gpu(res, 0, index)
            print(f"Using GPU acceleration with {faiss.get_num_gpus()} GPU(s)")
        
        # Add embeddings to index
        index.add(embeddings)
        self.index = index
        
        # Store metadata
        if metadata:
            self.root_metadata = metadata
        else:
            self.root_metadata = [{"id": i} for i in range(n_roots)]
            
        print(f"Index built successfully with {index.ntotal} roots")
        
    def search(
        self, 
        query_embeddings: np.ndarray, 
        k: int = 10
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Search for k nearest roots.
        
        Args:
            query_embeddings: Array of shape (n_queries, dimension)
            k: Number of nearest neighbors to retrieve
            
        Returns:
            distances: Array of shape (n_queries, k)
            indices: Array of shape (n_queries, k)
        """
        if self.index is None:
            raise RuntimeError("Index not built. Call build_index first.")
            
        # Normalize query embeddings
        faiss.normalize_L2(query_embeddings)
        
        # Search
        distances, indices = self.index.search(query_embeddings, k)
        
        return distances, indices
    
    def get_roots(self, indices: np.ndarray) -> List[List[Dict]]:
        """
        Retrieve root metadata for given indices.
        
        Args:
            indices: Array of shape (n_queries, k)
            
        Returns:
            List of lists of root metadata dictionaries
        """
        results = []
        for query_indices in indices:
            query_roots = []
            for idx in query_indices:
                if 0 <= idx < len(self.root_metadata):
                    query_roots.append(self.root_metadata[idx])
                else:
                    query_roots.append({"id": -1, "root": "UNKNOWN"})
            results.append(query_roots)
        return results
    
    def save_index(self, filepath: str):
        """Save Faiss index and metadata to disk."""
        if self.index is None:
            raise RuntimeError("No index to save")
            
        # Move to CPU if on GPU
        index_to_save = self.index
        if self.use_gpu and hasattr(self.index, 'index'):
            index_to_save = faiss.index_gpu_to_cpu(self.index)
        
        # Save index
        faiss.write_index(index_to_save, filepath)
        
        # Save metadata
        metadata_path = filepath.replace('.index', '_metadata.pkl')
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'root_metadata': self.root_metadata,
                'dimension': self.dimension,
                'index_type': self.index_type
            }, f)
            
        print(f"Index saved to {filepath}")
        
    def load_index(self, filepath: str):
        """Load Faiss index and metadata from disk."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Index file not found: {filepath}")
            
        # Load index
        index = faiss.read_index(filepath)
        
        # Move to GPU if requested
        if self.use_gpu and faiss.get_num_gpus() > 0:
            res = faiss.StandardGpuResources()
            index = faiss.index_cpu_to_gpu(res, 0, index)
            
        self.index = index
        
        # Load metadata
        metadata_path = filepath.replace('.index', '_metadata.pkl')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.root_metadata = data['root_metadata']
                self.dimension = data['dimension']
                self.index_type = data['index_type']
                
        print(f"Index loaded from {filepath} with {index.ntotal} roots")
        
    def add_roots(self, embeddings: np.ndarray, metadata: List[Dict]):
        """
        Add new roots to existing index.
        
        Args:
            embeddings: Array of shape (n_new_roots, dimension)
            metadata: List of dictionaries containing root information
        """
        if self.index is None:
            raise RuntimeError("Index not built. Call build_index first.")
            
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)
        self.root_metadata.extend(metadata)
        
        print(f"Added {len(metadata)} roots. Total: {self.index.ntotal}")


def create_sample_index(n_roots: int = 1000, dimension: int = 768) -> GraphSharding:
    """
    Create a sample graph sharding index for testing.
    
    Args:
        n_roots: Number of sample roots to generate
        dimension: Embedding dimension
        
    Returns:
        GraphSharding instance with sample data
    """
    print(f"Creating sample index with {n_roots} roots...")
    
    # Generate random embeddings
    embeddings = np.random.randn(n_roots, dimension).astype('float32')
    
    # Generate sample metadata
    metadata = [
        {
            'id': i,
            'root': f'root_{i}',
            'arabic_root': f'جذر_{i}',
            'frequency': np.random.randint(1, 1000)
        }
        for i in range(n_roots)
    ]
    
    # Build index
    sharder = GraphSharding(dimension=dimension, index_type="IVF", nlist=min(100, n_roots // 10))
    sharder.build_index(embeddings, metadata)
    
    return sharder


if __name__ == "__main__":
    # Demo usage
    print("RootAI v3.0 - Graph Sharding Demo")
    print("=" * 50)
    
    # Create sample index
    sharder = create_sample_index(n_roots=10000, dimension=768)
    
    # Sample query
    query = np.random.randn(1, 768).astype('float32')
    distances, indices = sharder.search(query, k=5)
    roots = sharder.get_roots(indices)
    
    print("\nTop 5 retrieved roots:")
    for i, root in enumerate(roots[0]):
        print(f"{i+1}. {root['root']} (ID: {root['id']}, similarity: {distances[0][i]:.4f})")
