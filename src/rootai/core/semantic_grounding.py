"""
Semantic Grounding Layer for RootAI v3.0

This module implements the semantic grounding layer that bridges RootAI's
semantic reasoning with GPT's natural language generation capabilities.
It formats RootAI's structured output into grounded prompts for GPT.
"""

from typing import List, Dict, Optional
import json


class SemanticGroundingLayer:
    """
    Semantic grounding layer for RootAI + GPT hybrid architecture.
    
    This layer takes RootAI's structured semantic context (roots, graph paths,
    verified relationships) and formats them into grounded prompts for GPT,
    ensuring factual accuracy and reducing hallucinations.
    """
    
    def __init__(self, template_style: str = "conversational"):
        """
        Initialize the semantic grounding layer.
        
        Args:
            template_style: Style of prompt template ('conversational', 'formal', 'concise')
        """
        self.template_style = template_style
        
    def format_semantic_context(
        self,
        roots: List[Dict],
        enhanced_roots: Optional[List[Dict]] = None,
        include_metadata: bool = True
    ) -> str:
        """
        Format root analysis into structured semantic context.
        
        Args:
            roots: List of decomposed root dictionaries
            enhanced_roots: Optional list of graph-enhanced roots
            include_metadata: Whether to include metadata like POS tags
            
        Returns:
            Formatted semantic context string
        """
        if not roots:
            return ""
        
        context_parts = []
        
        # Use enhanced roots if available, otherwise use basic roots
        roots_to_use = enhanced_roots if enhanced_roots else roots
        
        # Extract unique roots and their semantic information
        root_info = {}
        for root_data in roots_to_use:
            root = root_data.get('root', '')
            word = root_data.get('word', '')
            pos = root_data.get('pos', '')
            
            if root and root not in root_info:
                info = {'word': word, 'root': root}
                if include_metadata and pos:
                    info['pos'] = pos
                
                # Add similar roots if available
                if 'similar_roots' in root_data:
                    similar = root_data.get('similar_roots', [])
                    if similar:
                        info['related'] = [s.get('root', '') for s in similar[:3]]
                
                root_info[root] = info
        
        # Build context string
        if root_info:
            context_parts.append("Semantic roots identified:")
            for i, (root, info) in enumerate(root_info.items(), 1):
                parts = [f"{i}. Root '{root}'"]
                if info.get('word'):
                    parts.append(f"from word '{info['word']}'")
                if info.get('pos') and include_metadata:
                    parts.append(f"({info['pos']})")
                if info.get('related'):
                    related_str = ", ".join(info['related'])
                    parts.append(f"- related: {related_str}")
                context_parts.append(" ".join(parts))
        
        return "\n".join(context_parts)
    
    def create_grounded_prompt(
        self,
        query: str,
        semantic_context: str,
        additional_context: Optional[str] = None,
        constraints: Optional[List[str]] = None
    ) -> str:
        """
        Create a grounded prompt combining semantic context with user query.
        
        This follows the pattern:
        - Present verified semantic relationships from RootAI
        - Add any additional context or constraints
        - Pose the user's question for GPT to answer
        
        Args:
            query: User's original query
            semantic_context: Formatted semantic context from RootAI
            additional_context: Optional additional context
            constraints: Optional list of constraints for GPT
            
        Returns:
            Complete grounded prompt for GPT
        """
        if self.template_style == "conversational":
            return self._create_conversational_prompt(
                query, semantic_context, additional_context, constraints
            )
        elif self.template_style == "formal":
            return self._create_formal_prompt(
                query, semantic_context, additional_context, constraints
            )
        else:  # concise
            return self._create_concise_prompt(
                query, semantic_context, additional_context, constraints
            )
    
    def _create_conversational_prompt(
        self,
        query: str,
        semantic_context: str,
        additional_context: Optional[str],
        constraints: Optional[List[str]]
    ) -> str:
        """Create conversational-style grounded prompt."""
        prompt_parts = []
        
        if semantic_context:
            prompt_parts.append("Based on verified semantic relationships:")
            prompt_parts.append(semantic_context)
            prompt_parts.append("")
        
        if additional_context:
            prompt_parts.append(additional_context)
            prompt_parts.append("")
        
        if constraints:
            prompt_parts.append("Please note:")
            for constraint in constraints:
                prompt_parts.append(f"- {constraint}")
            prompt_parts.append("")
        
        prompt_parts.append(f"Answer conversationally: {query}")
        
        return "\n".join(prompt_parts)
    
    def _create_formal_prompt(
        self,
        query: str,
        semantic_context: str,
        additional_context: Optional[str],
        constraints: Optional[List[str]]
    ) -> str:
        """Create formal-style grounded prompt."""
        prompt_parts = []
        
        prompt_parts.append("SEMANTIC CONTEXT:")
        if semantic_context:
            prompt_parts.append(semantic_context)
        else:
            prompt_parts.append("No semantic roots identified.")
        prompt_parts.append("")
        
        if additional_context:
            prompt_parts.append("ADDITIONAL CONTEXT:")
            prompt_parts.append(additional_context)
            prompt_parts.append("")
        
        if constraints:
            prompt_parts.append("CONSTRAINTS:")
            for i, constraint in enumerate(constraints, 1):
                prompt_parts.append(f"{i}. {constraint}")
            prompt_parts.append("")
        
        prompt_parts.append("QUERY:")
        prompt_parts.append(query)
        prompt_parts.append("")
        prompt_parts.append("RESPONSE:")
        
        return "\n".join(prompt_parts)
    
    def _create_concise_prompt(
        self,
        query: str,
        semantic_context: str,
        additional_context: Optional[str],
        constraints: Optional[List[str]]
    ) -> str:
        """Create concise-style grounded prompt."""
        prompt_parts = []
        
        if semantic_context:
            prompt_parts.append(f"Context: {semantic_context}")
        
        if additional_context:
            prompt_parts.append(additional_context)
        
        if constraints:
            prompt_parts.append("Constraints: " + "; ".join(constraints))
        
        prompt_parts.append(f"Q: {query}")
        prompt_parts.append("A:")
        
        return " ".join(prompt_parts)
    
    def extract_verification_data(
        self,
        roots: List[Dict],
        enhanced_roots: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Extract verification data for quality control.
        
        This provides metadata about the semantic grounding that can be used
        to assess the quality and reliability of the grounded context.
        
        Args:
            roots: List of decomposed root dictionaries
            enhanced_roots: Optional list of graph-enhanced roots
            
        Returns:
            Dictionary with verification metrics
        """
        verification = {
            'num_roots': len(roots),
            'num_unique_roots': len(set(r.get('root', '') for r in roots)),
            'has_graph_enhancement': enhanced_roots is not None,
            'languages_detected': [],
            'pos_tags': []
        }
        
        if enhanced_roots:
            verification['num_similar_roots'] = sum(
                len(r.get('similar_roots', [])) for r in enhanced_roots
            )
            verification['graph_retrieval_coverage'] = sum(
                1 for r in enhanced_roots if r.get('similar_roots')
            ) / len(enhanced_roots) if enhanced_roots else 0
        
        # Extract POS tags
        for root in roots:
            pos = root.get('pos')
            if pos and pos not in verification['pos_tags']:
                verification['pos_tags'].append(pos)
        
        return verification


def create_grounded_prompt_simple(
    query: str,
    roots: List[Dict],
    semantic_context: str
) -> str:
    """
    Simple helper function to create a grounded prompt.
    
    This is a convenience function that implements the basic pattern from
    the problem statement.
    
    Args:
        query: User query
        roots: Root analysis from RootAI
        semantic_context: Semantic context from graph retrieval
        
    Returns:
        Grounded prompt string
    """
    return f"""Based on verified semantic relationships:
{semantic_context}

Answer conversationally: {query}
"""


if __name__ == "__main__":
    # Demo usage
    print("Semantic Grounding Layer Demo")
    print("=" * 50)
    
    # Sample data
    sample_roots = [
        {'word': 'العدالة', 'root': 'عدل', 'pos': 'NOUN'},
        {'word': 'الحكم', 'root': 'حكم', 'pos': 'NOUN'},
    ]
    
    sample_enhanced = [
        {
            'word': 'العدالة',
            'root': 'عدل',
            'pos': 'NOUN',
            'similar_roots': [
                {'root': 'قسط', 'id': 1},
                {'root': 'إنصاف', 'id': 2}
            ]
        }
    ]
    
    # Create grounding layer
    grounding = SemanticGroundingLayer(template_style="conversational")
    
    # Format context
    context = grounding.format_semantic_context(sample_roots, sample_enhanced)
    print("\nFormatted Context:")
    print(context)
    
    # Create grounded prompt
    query = "What is justice in Islamic philosophy?"
    prompt = grounding.create_grounded_prompt(
        query,
        context,
        constraints=["Keep response factually accurate", "Use clear language"]
    )
    
    print("\n\nGrounded Prompt:")
    print(prompt)
    
    # Verification data
    verification = grounding.extract_verification_data(sample_roots, sample_enhanced)
    print("\n\nVerification Data:")
    print(json.dumps(verification, indent=2))
