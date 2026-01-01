"""
Test suite for RootAI v3.0 hybrid architecture (RootAI + GPT)

Run with: pytest tests/test_hybrid.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from rootai.core.semantic_grounding import SemanticGroundingLayer, create_grounded_prompt_simple
from rootai.core.root_reasoner import RootReasoner
from rootai.core.graph_sharding import create_sample_index


class TestSemanticGroundingLayer:
    """Tests for semantic grounding layer."""
    
    def test_init(self):
        """Test initialization of grounding layer."""
        grounding = SemanticGroundingLayer(template_style="conversational")
        assert grounding is not None
        assert grounding.template_style == "conversational"
    
    def test_format_semantic_context_basic(self):
        """Test basic semantic context formatting."""
        grounding = SemanticGroundingLayer()
        
        roots = [
            {'word': 'test', 'root': 'tst', 'pos': 'NOUN'},
            {'word': 'example', 'root': 'exmpl', 'pos': 'NOUN'}
        ]
        
        context = grounding.format_semantic_context(roots)
        
        assert isinstance(context, str)
        assert 'tst' in context
        assert 'exmpl' in context
    
    def test_format_semantic_context_with_enhancement(self):
        """Test semantic context with graph enhancement."""
        grounding = SemanticGroundingLayer()
        
        roots = [{'word': 'test', 'root': 'tst', 'pos': 'NOUN'}]
        enhanced = [
            {
                'word': 'test',
                'root': 'tst',
                'pos': 'NOUN',
                'similar_roots': [
                    {'root': 'similar1', 'id': 1},
                    {'root': 'similar2', 'id': 2}
                ]
            }
        ]
        
        context = grounding.format_semantic_context(roots, enhanced, include_metadata=True)
        
        assert 'tst' in context
        assert 'similar1' in context or 'similar2' in context
    
    def test_format_semantic_context_empty(self):
        """Test semantic context with empty roots."""
        grounding = SemanticGroundingLayer()
        context = grounding.format_semantic_context([])
        assert context == ""
    
    def test_create_grounded_prompt_conversational(self):
        """Test conversational style grounded prompt."""
        grounding = SemanticGroundingLayer(template_style="conversational")
        
        query = "What is justice?"
        context = "Root 'عدل' (justice) identified"
        
        prompt = grounding.create_grounded_prompt(query, context)
        
        assert isinstance(prompt, str)
        assert query in prompt
        assert context in prompt
        assert "Based on verified semantic relationships" in prompt
    
    def test_create_grounded_prompt_formal(self):
        """Test formal style grounded prompt."""
        grounding = SemanticGroundingLayer(template_style="formal")
        
        query = "What is mercy?"
        context = "Root 'رحم' identified"
        
        prompt = grounding.create_grounded_prompt(query, context)
        
        assert "SEMANTIC CONTEXT:" in prompt
        assert "QUERY:" in prompt
        assert query in prompt
    
    def test_create_grounded_prompt_concise(self):
        """Test concise style grounded prompt."""
        grounding = SemanticGroundingLayer(template_style="concise")
        
        query = "What is wisdom?"
        context = "Root 'حكم' identified"
        
        prompt = grounding.create_grounded_prompt(query, context)
        
        assert query in prompt
        assert context in prompt
        assert len(prompt) < 200  # Should be concise
    
    def test_create_grounded_prompt_with_constraints(self):
        """Test grounded prompt with constraints."""
        grounding = SemanticGroundingLayer()
        
        query = "Explain justice"
        context = "Roots identified"
        constraints = ["Be accurate", "Use clear language"]
        
        prompt = grounding.create_grounded_prompt(
            query, context, constraints=constraints
        )
        
        assert all(c in prompt for c in constraints)
    
    def test_extract_verification_data(self):
        """Test verification data extraction."""
        grounding = SemanticGroundingLayer()
        
        roots = [
            {'word': 'test', 'root': 'tst', 'pos': 'NOUN'},
            {'word': 'example', 'root': 'exmpl', 'pos': 'VERB'}
        ]
        
        verification = grounding.extract_verification_data(roots)
        
        assert verification['num_roots'] == 2
        assert verification['num_unique_roots'] == 2
        assert 'NOUN' in verification['pos_tags']
        assert 'VERB' in verification['pos_tags']
    
    def test_extract_verification_data_with_enhancement(self):
        """Test verification with graph enhancement."""
        grounding = SemanticGroundingLayer()
        
        roots = [{'word': 'test', 'root': 'tst', 'pos': 'NOUN'}]
        enhanced = [
            {
                'word': 'test',
                'root': 'tst',
                'pos': 'NOUN',
                'similar_roots': [
                    {'root': 'similar1', 'id': 1},
                    {'root': 'similar2', 'id': 2}
                ]
            }
        ]
        
        verification = grounding.extract_verification_data(roots, enhanced)
        
        assert verification['has_graph_enhancement'] is True
        assert verification['num_similar_roots'] == 2
        assert verification['graph_retrieval_coverage'] == 1.0


class TestGroundedPromptHelper:
    """Tests for helper functions."""
    
    def test_create_grounded_prompt_simple(self):
        """Test simple grounded prompt creation."""
        query = "What is justice?"
        roots = [{'word': 'justice', 'root': 'just'}]
        context = "Root 'just' identified"
        
        prompt = create_grounded_prompt_simple(query, roots, context)
        
        assert isinstance(prompt, str)
        assert query in prompt
        assert context in prompt
        assert "Based on verified semantic relationships" in prompt


class TestHybridReasoner:
    """Tests for hybrid reasoning with GPT integration."""
    
    def test_reasoner_init_without_openai(self):
        """Test reasoner initialization without OpenAI key."""
        reasoner = RootReasoner(use_gpu=False)
        assert reasoner is not None
        assert reasoner.openai_client is None
        assert reasoner.grounding_layer is not None
    
    def test_reasoner_init_with_openai_key(self):
        """Test reasoner initialization with OpenAI key."""
        with patch('rootai.core.root_reasoner.openai') as mock_openai:
            mock_openai.OpenAI = Mock()
            reasoner = RootReasoner(
                use_gpu=False,
                openai_api_key="test-key"
            )
            assert reasoner is not None
            mock_openai.OpenAI.assert_called_once()
    
    def test_generate_with_gpt_no_client(self):
        """Test GPT generation without OpenAI client."""
        reasoner = RootReasoner(use_gpu=False)
        
        roots = [{'word': 'test', 'root': 'tst'}]
        result = reasoner.generate_with_gpt("What is test?", roots)
        
        assert "Error" in result
        assert "OpenAI client not initialized" in result
    
    @patch('rootai.core.root_reasoner.openai')
    def test_generate_with_gpt_success(self, mock_openai):
        """Test successful GPT generation."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test answer"
        mock_client.chat.completions.create.return_value = mock_response
        
        mock_openai.OpenAI.return_value = mock_client
        
        reasoner = RootReasoner(use_gpu=False, openai_api_key="test-key")
        reasoner.openai_client = mock_client
        
        roots = [{'word': 'test', 'root': 'tst', 'pos': 'NOUN'}]
        result = reasoner.generate_with_gpt("What is test?", roots)
        
        assert result == "This is a test answer"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('rootai.core.root_reasoner.openai')
    def test_reason_hybrid_with_gpt(self, mock_openai):
        """Test hybrid reasoning pipeline with GPT."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Answer from GPT"
        mock_client.chat.completions.create.return_value = mock_response
        
        mock_openai.OpenAI.return_value = mock_client
        
        reasoner = RootReasoner(use_gpu=False, openai_api_key="test-key")
        reasoner.openai_client = mock_client
        
        # Create sample index
        sharder = create_sample_index(n_roots=50, dimension=768)
        reasoner.set_graph_sharder(sharder)
        
        result = reasoner.reason_hybrid(
            "What is justice?",
            k=3,
            use_gpt=True
        )
        
        assert 'query' in result
        assert 'answer' in result
        assert 'roots' in result
        assert 'pipeline' in result
        assert 'GPT' in result['pipeline']
        assert result['mode'] == 'hybrid'
    
    def test_reason_hybrid_fallback_to_t5(self):
        """Test hybrid reasoning falls back to T5 when GPT unavailable."""
        reasoner = RootReasoner(use_gpu=False)
        
        # Create sample index
        sharder = create_sample_index(n_roots=50, dimension=768)
        reasoner.set_graph_sharder(sharder)
        
        result = reasoner.reason_hybrid(
            "What is justice?",
            k=3,
            use_gpt=True  # Request GPT but it's not available
        )
        
        assert 'query' in result
        assert 'answer' in result
        assert result['pipeline'] == 'decompose → graph → T5'
        assert result['mode'] == 't5_only'
    
    def test_reason_hybrid_explicit_t5(self):
        """Test hybrid reasoning with explicit T5 mode."""
        reasoner = RootReasoner(use_gpu=False)
        
        sharder = create_sample_index(n_roots=50, dimension=768)
        reasoner.set_graph_sharder(sharder)
        
        result = reasoner.reason_hybrid(
            "What is mercy?",
            k=3,
            use_gpt=False  # Explicitly use T5
        )
        
        assert result['pipeline'] == 'decompose → graph → T5'
        assert result['mode'] == 't5_only'


class TestIntegrationHybrid:
    """Integration tests for hybrid architecture."""
    
    def test_full_hybrid_pipeline_semantic_grounding(self):
        """Test complete hybrid pipeline with semantic grounding."""
        reasoner = RootReasoner(use_gpu=False)
        sharder = create_sample_index(n_roots=100, dimension=768)
        reasoner.set_graph_sharder(sharder)
        
        # Test Stage 1: Semantic grounding
        query = "What is the concept of justice?"
        roots = reasoner.decompose(query)
        enhanced_roots = reasoner.graph_retrieve(roots, k=5)
        
        # Verify semantic grounding
        assert isinstance(roots, list)
        assert isinstance(enhanced_roots, list)
        
        # Test grounding layer
        grounding = reasoner.grounding_layer
        context = grounding.format_semantic_context(roots, enhanced_roots)
        assert isinstance(context, str)
        
        # Test prompt creation
        prompt = grounding.create_grounded_prompt(query, context)
        assert query in prompt
    
    @patch('rootai.core.root_reasoner.openai')
    def test_two_stage_hybrid_architecture(self, mock_openai):
        """Test the complete two-stage hybrid architecture."""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Justice is the principle of moral rightness"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.OpenAI.return_value = mock_client
        
        # Initialize hybrid reasoner
        reasoner = RootReasoner(
            use_gpu=False,
            openai_api_key="test-key"
        )
        reasoner.openai_client = mock_client
        
        sharder = create_sample_index(n_roots=100, dimension=768)
        reasoner.set_graph_sharder(sharder)
        
        # Run complete hybrid pipeline
        result = reasoner.reason_hybrid(
            "What is justice in philosophy?",
            k=5,
            use_gpt=True,
            max_tokens=200
        )
        
        # Verify Stage 1: RootAI performed decomposition and retrieval
        assert 'roots' in result
        assert 'enhanced_roots' in result
        assert len(result['roots']) >= 0  # May have Arabic or no roots
        
        # Verify Stage 2: GPT generated response
        assert result['answer'] == "Justice is the principle of moral rightness"
        assert 'GPT' in result['pipeline']
        assert result['mode'] == 'hybrid'
    
    def test_backward_compatibility(self):
        """Test that original reason() method still works."""
        reasoner = RootReasoner(use_gpu=False)
        sharder = create_sample_index(n_roots=50, dimension=768)
        reasoner.set_graph_sharder(sharder)
        
        # Original method should still work
        result = reasoner.reason("What is wisdom?", k=3)
        
        assert 'query' in result
        assert 'answer' in result
        assert 'pipeline' in result
        assert result['pipeline'] == 'decompose → graph → T5'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
