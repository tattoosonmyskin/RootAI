"""
Root Reasoner Module for RootAI v3.0

Implements the decompose → graph → T5 pipeline for semantic reasoning
using Arabic root morphology and transformer models.
"""

from typing import List, Dict, Optional, Tuple
import re
import numpy as np

try:
    from transformers import T5Tokenizer, T5ForConditionalGeneration
    import torch
except ImportError:
    print("Warning: transformers or torch not installed. Install with:")
    print("  pip install transformers torch")
    T5Tokenizer = None
    T5ForConditionalGeneration = None
    torch = None

try:
    from camel_tools.morphology.database import MorphologyDB
    from camel_tools.morphology.analyzer import Analyzer
except ImportError:
    print("Warning: camel-tools not installed. Install with:")
    print("  pip install camel-tools")
    MorphologyDB = None
    Analyzer = None

from .graph_sharding import GraphSharding
from .semantic_grounding import SemanticGroundingLayer

try:
    import openai
except ImportError:
    print("Warning: openai not installed. Install with: pip install openai")
    openai = None


class RootReasoner:
    """
    Main reasoning engine combining root decomposition, graph retrieval, and T5/GPT generation.
    
    Pipeline:
    1. Decompose: Extract Arabic roots using morphological analysis
    2. Graph: Retrieve similar roots from Faiss index
    3. Generate: Use T5 or GPT (hybrid mode) for final answer
    
    Supports hybrid architecture:
    - Stage 1 (RootAI): Semantic grounding through root decomposition and graph retrieval
    - Stage 2 (GPT): Natural language generation with grounded context
    """
    
    def __init__(
        self,
        model_name: str = "google/t5-v1_1-base",
        graph_index_path: Optional[str] = None,
        use_gpu: bool = True,
        max_length: int = 512,
        openai_api_key: Optional[str] = None,
        gpt_model: str = "gpt-3.5-turbo"
    ):
        """
        Initialize the root reasoner.
        
        Args:
            model_name: HuggingFace T5 model name
            graph_index_path: Path to pre-built Faiss index
            use_gpu: Whether to use GPU acceleration
            max_length: Maximum sequence length for T5
            openai_api_key: Optional OpenAI API key for GPT integration
            gpt_model: GPT model to use (e.g., 'gpt-3.5-turbo', 'gpt-4')
        """
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.max_length = max_length
        self.device = "cuda" if use_gpu and torch and torch.cuda.is_available() else "cpu"
        self.gpt_model = gpt_model
        
        # Initialize components
        self.tokenizer = None
        self.model = None
        self.analyzer = None
        self.graph_sharder = None
        self.grounding_layer = SemanticGroundingLayer(template_style="conversational")
        
        # Set up OpenAI if API key provided
        self.openai_client = None
        if openai_api_key and openai:
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
        elif openai_api_key and not openai:
            print("Warning: OpenAI API key provided but openai package not installed")
        
        # Load T5 model
        self._load_t5_model()
        
        # Load morphological analyzer
        self._load_analyzer()
        
        # Load graph index if provided
        if graph_index_path:
            self.load_graph_index(graph_index_path)
        
    def _load_t5_model(self):
        """Load T5 tokenizer and model."""
        if T5Tokenizer is None or T5ForConditionalGeneration is None:
            print("T5 components not available. Install transformers and torch.")
            return
            
        print(f"Loading T5 model: {self.model_name}")
        self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(self.model_name)
        
        if self.device == "cuda":
            self.model = self.model.to(self.device)
            print(f"Model loaded on {self.device}")
        else:
            print("Model loaded on CPU")
            
    def _load_analyzer(self):
        """Load CAMeL Tools morphological analyzer."""
        if MorphologyDB is None or Analyzer is None:
            print("CAMeL Tools not available. Root extraction will be limited.")
            return
            
        try:
            print("Loading Arabic morphological analyzer...")
            db = MorphologyDB.builtin_db()
            self.analyzer = Analyzer(db)
            print("Analyzer loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load analyzer: {e}")
            self.analyzer = None
            
    def load_graph_index(self, index_path: str):
        """Load pre-built graph sharding index."""
        print(f"Loading graph index from {index_path}")
        self.graph_sharder = GraphSharding(dimension=768, use_gpu=self.use_gpu)
        self.graph_sharder.load_index(index_path)
        
    def set_graph_sharder(self, sharder: GraphSharding):
        """Set graph sharder instance."""
        self.graph_sharder = sharder
        
    def decompose(self, text: str) -> List[Dict]:
        """
        Step 1: Decompose Arabic text into roots using morphological analysis.
        
        Args:
            text: Input Arabic text
            
        Returns:
            List of root dictionaries with analysis
        """
        if not text or not text.strip():
            return []
            
        # Extract Arabic words
        arabic_pattern = re.compile(r'[\u0600-\u06FF]+')
        words = arabic_pattern.findall(text)
        
        roots = []
        
        if self.analyzer:
            # Use CAMeL Tools for proper morphological analysis
            for word in words:
                try:
                    analyses = self.analyzer.analyze(word)
                    if analyses:
                        # Get the best analysis
                        analysis = analyses[0]
                        root = analysis.get('root', word)
                        roots.append({
                            'word': word,
                            'root': root,
                            'pos': analysis.get('pos', 'UNKNOWN'),
                            'gloss': analysis.get('gloss', '')
                        })
                    else:
                        roots.append({'word': word, 'root': word, 'pos': 'UNKNOWN'})
                except Exception as e:
                    # Fallback for problematic words
                    roots.append({'word': word, 'root': word, 'pos': 'UNKNOWN'})
        else:
            # Fallback: Use simple heuristic root extraction
            for word in words:
                root = self._extract_root_heuristic(word)
                roots.append({'word': word, 'root': root, 'pos': 'UNKNOWN'})
        
        return roots
    
    def _extract_root_heuristic(self, word: str) -> str:
        """
        Simple heuristic root extraction (fallback method).
        
        Removes common prefixes and suffixes to approximate root.
        """
        # Remove common prefixes
        prefixes = ['ال', 'و', 'ف', 'ب', 'ل', 'ك']
        for prefix in prefixes:
            if word.startswith(prefix):
                word = word[len(prefix):]
                
        # Remove common suffixes
        suffixes = ['ة', 'ه', 'ها', 'هم', 'ون', 'ين', 'ات']
        for suffix in suffixes:
            if word.endswith(suffix):
                word = word[:-len(suffix)]
                
        # Return first 3 characters as approximate root (triliteral)
        return word[:3] if len(word) >= 3 else word
    
    def graph_retrieve(
        self, 
        roots: List[Dict], 
        k: int = 5,
        query_text: Optional[str] = None
    ) -> List[Dict]:
        """
        Step 2: Retrieve relevant roots from graph using Faiss.
        
        Args:
            roots: List of root dictionaries from decomposition
            k: Number of similar roots to retrieve per root
            query_text: Optional query text for semantic embedding
            
        Returns:
            List of retrieved root information with similarities
        """
        if not self.graph_sharder:
            print("Warning: No graph index loaded. Skipping retrieval.")
            return roots
            
        if not roots:
            return []
        
        # For this implementation, we'll create embeddings from roots
        # In production, you'd use a proper Arabic embedding model
        root_texts = [r['root'] for r in roots]
        
        # Create simple embeddings (in production, use proper model)
        embeddings = self._create_embeddings(root_texts)
        
        # Search in graph
        distances, indices = self.graph_sharder.search(embeddings, k=k)
        retrieved_roots = self.graph_sharder.get_roots(indices)
        
        # Combine original roots with retrieved similar roots
        enhanced_roots = []
        for i, root in enumerate(roots):
            enhanced_root = root.copy()
            enhanced_root['similar_roots'] = retrieved_roots[i]
            enhanced_root['similarities'] = distances[i].tolist()
            enhanced_roots.append(enhanced_root)
            
        return enhanced_roots
    
    def _create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Create embeddings for texts using T5 encoder.
        
        Args:
            texts: List of text strings
            
        Returns:
            Embeddings array of shape (n_texts, dimension)
        """
        if not self.model or not self.tokenizer:
            # Fallback to random embeddings
            return np.random.randn(len(texts), 768).astype('float32')
            
        # Tokenize
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt"
        )
        
        if self.device == "cuda":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Get encoder hidden states
        with torch.no_grad():
            outputs = self.model.encoder(**inputs)
            # Use mean pooling of last hidden state
            embeddings = outputs.last_hidden_state.mean(dim=1)
            
        return embeddings.cpu().numpy().astype('float32')
    
    def generate(
        self,
        query: str,
        context_roots: List[Dict],
        max_new_tokens: int = 200,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> str:
        """
        Step 3: Generate final answer using T5 with root-enhanced context.
        
        Args:
            query: Input question/query
            context_roots: Root analysis with retrieved similar roots
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            
        Returns:
            Generated answer text
        """
        if not self.model or not self.tokenizer:
            return "Error: T5 model not loaded"
            
        # Build prompt with root context
        prompt = self._build_prompt(query, context_roots)
        
        # Tokenize
        inputs = self.tokenizer(
            prompt,
            max_length=self.max_length,
            truncation=True,
            return_tensors="pt"
        )
        
        if self.device == "cuda":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                num_beams=1
            )
        
        # Decode
        answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return answer
    
    def _build_prompt(self, query: str, context_roots: List[Dict]) -> str:
        """
        Build T5 prompt with root-enhanced context.
        
        Args:
            query: Input query
            context_roots: Root analysis and retrieved similar roots
            
        Returns:
            Formatted prompt string
        """
        # Extract key information from roots
        root_info = []
        for root_data in context_roots[:5]:  # Limit to top 5
            root = root_data.get('root', '')
            word = root_data.get('word', '')
            if root and word:
                root_info.append(f"{word} (root: {root})")
        
        # Build prompt
        if root_info:
            context = "Root context: " + ", ".join(root_info) + ". "
        else:
            context = ""
            
        prompt = f"{context}Question: {query} Answer:"
        
        return prompt
    
    def generate_with_gpt(
        self,
        query: str,
        context_roots: List[Dict],
        max_tokens: int = 200,
        temperature: float = 0.7,
        template_style: str = "conversational"
    ) -> str:
        """
        Generate answer using GPT with RootAI's semantic grounding.
        
        This implements Stage 2 of the hybrid architecture, using GPT for
        natural language generation while maintaining factual accuracy through
        RootAI's semantic constraints.
        
        Args:
            query: Input question/query
            context_roots: Root analysis with retrieved similar roots from RootAI
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            template_style: Style of prompt template ('conversational', 'formal', 'concise')
            
        Returns:
            Generated answer text from GPT
        """
        if not self.openai_client:
            return "Error: OpenAI client not initialized. Provide API key or use T5 generation."
        
        # Use semantic grounding layer to create prompt
        grounding = SemanticGroundingLayer(template_style=template_style)
        semantic_context = grounding.format_semantic_context(
            context_roots,
            enhanced_roots=context_roots,
            include_metadata=True
        )
        
        # Create grounded prompt
        grounded_prompt = grounding.create_grounded_prompt(
            query,
            semantic_context,
            constraints=[
                "Base your answer on the semantic relationships provided",
                "Maintain factual accuracy",
                "Be clear and conversational"
            ]
        )
        
        try:
            # Call GPT API
            response = self.openai_client.chat.completions.create(
                model=self.gpt_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that provides accurate answers based on semantic context. Use the provided semantic roots and relationships to ground your responses."
                    },
                    {
                        "role": "user",
                        "content": grounded_prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            answer = response.choices[0].message.content
            return answer
            
        except Exception as e:
            return f"Error calling GPT API: {str(e)}"
    
    def reason_hybrid(
        self,
        query: str,
        k: int = 5,
        max_tokens: int = 200,
        use_gpt: bool = True,
        temperature: float = 0.7
    ) -> Dict:
        """
        Hybrid reasoning pipeline: RootAI (semantic grounding) → GPT (generation).
        
        This implements the two-stage hybrid architecture:
        - Stage 1: RootAI performs semantic decomposition and graph retrieval
        - Stage 2: GPT generates fluent responses guided by RootAI's grounding
        
        Args:
            query: Input question/query
            k: Number of similar roots to retrieve
            max_tokens: Maximum tokens to generate
            use_gpt: Whether to use GPT (True) or T5 (False) for generation
            temperature: Sampling temperature for generation
            
        Returns:
            Dictionary with reasoning steps and final answer
        """
        # Stage 1: RootAI Reasoning - Semantic Grounding
        # Step 1.1: Decompose query to semantic roots
        roots = self.decompose(query)
        
        # Step 1.2: Graph retrieve for verified semantic relationships
        enhanced_roots = self.graph_retrieve(roots, k=k, query_text=query)
        
        # Stage 2: GPT Generation (or T5 fallback)
        if use_gpt and self.openai_client:
            answer = self.generate_with_gpt(
                query,
                enhanced_roots,
                max_tokens=max_tokens,
                temperature=temperature
            )
            pipeline = 'decompose → graph → GPT (hybrid)'
        else:
            # Fallback to T5 if GPT not available
            answer = self.generate(
                query,
                enhanced_roots,
                max_new_tokens=max_tokens,
                temperature=temperature
            )
            pipeline = 'decompose → graph → T5'
        
        return {
            'query': query,
            'roots': roots,
            'enhanced_roots': enhanced_roots,
            'answer': answer,
            'pipeline': pipeline,
            'mode': 'hybrid' if use_gpt and self.openai_client else 't5_only'
        }
    
    def reason(
        self,
        query: str,
        k: int = 5,
        max_new_tokens: int = 200
    ) -> Dict:
        """
        Full reasoning pipeline: decompose → graph → T5.
        
        Args:
            query: Input question/query
            k: Number of similar roots to retrieve
            max_new_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with reasoning steps and final answer
        """
        # Step 1: Decompose
        roots = self.decompose(query)
        
        # Step 2: Graph retrieve
        enhanced_roots = self.graph_retrieve(roots, k=k, query_text=query)
        
        # Step 3: Generate
        answer = self.generate(query, enhanced_roots, max_new_tokens=max_new_tokens)
        
        return {
            'query': query,
            'roots': roots,
            'enhanced_roots': enhanced_roots,
            'answer': answer,
            'pipeline': 'decompose → graph → T5'
        }


def demo_reasoner():
    """Demo the root reasoner."""
    print("RootAI v3.0 - Root Reasoner Demo")
    print("=" * 50)
    
    # Initialize reasoner
    reasoner = RootReasoner(use_gpu=False)
    
    # Test query (Arabic)
    query = "ما هو معنى الحياة؟"  # "What is the meaning of life?"
    
    print(f"\nQuery: {query}")
    print("\nStep 1: Decomposing query...")
    roots = reasoner.decompose(query)
    print(f"Extracted {len(roots)} roots:")
    for root in roots:
        print(f"  - {root['word']} → {root['root']}")
    
    # Note: Graph retrieval would require a pre-built index
    print("\nStep 2: Graph retrieval (requires pre-built index)")
    print("Step 3: T5 generation (requires full model)")
    
    # Full pipeline
    print("\nFull reasoning pipeline:")
    result = reasoner.reason(query)
    print(f"Answer: {result['answer']}")


if __name__ == "__main__":
    demo_reasoner()
