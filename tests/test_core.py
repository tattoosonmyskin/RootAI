"""
Test suite for RootAI v3.0 core functionality

Run with: pytest tests/test_core.py -v
"""

import pytest
import numpy as np

from rootai.core.graph_sharding import GraphSharding, create_sample_index
from rootai.core.root_reasoner import RootReasoner


class TestGraphSharding:
    """Tests for graph sharding module."""
    
    def test_create_sample_index(self):
        """Test creating a sample index."""
        sharder = create_sample_index(n_roots=100, dimension=768)
        assert sharder is not None
        assert sharder.index is not None
        assert sharder.index.ntotal == 100
    
    def test_build_index(self):
        """Test building index from embeddings."""
        sharder = GraphSharding(dimension=128, use_gpu=False)
        embeddings = np.random.randn(50, 128).astype('float32')
        metadata = [{'id': i, 'root': f'root_{i}'} for i in range(50)]
        
        sharder.build_index(embeddings, metadata)
        
        assert sharder.index.ntotal == 50
        assert len(sharder.root_metadata) == 50
    
    def test_search(self):
        """Test searching for similar roots."""
        sharder = create_sample_index(n_roots=100, dimension=128)
        
        query = np.random.randn(1, 128).astype('float32')
        distances, indices = sharder.search(query, k=5)
        
        assert distances.shape == (1, 5)
        assert indices.shape == (1, 5)
        assert all(0 <= idx < 100 for idx in indices[0])
    
    def test_get_roots(self):
        """Test retrieving root metadata."""
        sharder = create_sample_index(n_roots=50, dimension=128)
        
        query = np.random.randn(1, 128).astype('float32')
        distances, indices = sharder.search(query, k=3)
        roots = sharder.get_roots(indices)
        
        assert len(roots) == 1
        assert len(roots[0]) == 3
        assert 'id' in roots[0][0]


class TestRootReasoner:
    """Tests for root reasoner module."""
    
    def test_init(self):
        """Test reasoner initialization."""
        reasoner = RootReasoner(use_gpu=False)
        assert reasoner is not None
        assert reasoner.device == "cpu"
    
    def test_decompose_arabic(self):
        """Test Arabic text decomposition."""
        reasoner = RootReasoner(use_gpu=False)
        
        text = "الحمد لله رب العالمين"
        roots = reasoner.decompose(text)
        
        assert isinstance(roots, list)
        assert len(roots) > 0
        assert all('word' in r and 'root' in r for r in roots)
    
    def test_decompose_empty(self):
        """Test decomposition with empty text."""
        reasoner = RootReasoner(use_gpu=False)
        roots = reasoner.decompose("")
        assert roots == []
    
    def test_create_embeddings(self):
        """Test embedding creation."""
        reasoner = RootReasoner(use_gpu=False)
        
        texts = ["test1", "test2", "test3"]
        embeddings = reasoner._create_embeddings(texts)
        
        assert embeddings.shape[0] == 3
        assert embeddings.shape[1] == 768  # Default T5 dimension
    
    def test_reason_basic(self):
        """Test basic reasoning pipeline."""
        reasoner = RootReasoner(use_gpu=False)
        
        # Create sample index
        sharder = create_sample_index(n_roots=50, dimension=768)
        reasoner.set_graph_sharder(sharder)
        
        # Run reasoning
        query = "What is justice?"
        result = reasoner.reason(query, k=3, max_new_tokens=50)
        
        assert 'query' in result
        assert 'answer' in result
        assert 'roots' in result
        assert 'pipeline' in result
        assert result['pipeline'] == 'decompose → graph → T5'
    
    def test_graph_retrieve(self):
        """Test graph retrieval step."""
        reasoner = RootReasoner(use_gpu=False)
        sharder = create_sample_index(n_roots=50, dimension=768)
        reasoner.set_graph_sharder(sharder)
        
        roots = [{'word': 'test', 'root': 'tst'}]
        enhanced = reasoner.graph_retrieve(roots, k=3)
        
        assert len(enhanced) == 1
        assert 'similar_roots' in enhanced[0]
        assert len(enhanced[0]['similar_roots']) == 3


class TestIntegration:
    """Integration tests."""
    
    def test_full_pipeline(self):
        """Test complete reasoning pipeline."""
        # Initialize components
        reasoner = RootReasoner(use_gpu=False)
        sharder = create_sample_index(n_roots=100, dimension=768)
        reasoner.set_graph_sharder(sharder)
        
        # Run query
        query = "Explain the concept of wisdom"
        result = reasoner.reason(query, k=5, max_new_tokens=100)
        
        # Verify result structure
        assert result['query'] == query
        assert isinstance(result['answer'], str)
        assert len(result['answer']) > 0
        assert isinstance(result['roots'], list)
        assert result['pipeline'] == 'decompose → graph → T5'
    
    def test_batch_queries(self):
        """Test processing multiple queries."""
        reasoner = RootReasoner(use_gpu=False)
        sharder = create_sample_index(n_roots=50, dimension=768)
        reasoner.set_graph_sharder(sharder)
        
        queries = [
            "What is justice?",
            "What is mercy?",
            "What is wisdom?"
        ]
        
        results = []
        for query in queries:
            result = reasoner.reason(query, k=3, max_new_tokens=50)
            results.append(result)
        
        assert len(results) == 3
        assert all('answer' in r for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
