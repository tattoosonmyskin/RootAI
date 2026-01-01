"""
RootAI v3.0 - Root-based semantic reasoning system

A hybrid AI system combining Arabic morphological analysis,
graph-based retrieval, and transformer models (T5/GPT) for
semantic reasoning.
"""

__version__ = "3.0.1"
__author__ = "RootAI Team"

from .core.root_reasoner import RootReasoner
from .core.graph_sharding import GraphSharding, create_sample_index
from .core.semantic_grounding import SemanticGroundingLayer

__all__ = [
    "RootReasoner",
    "GraphSharding",
    "create_sample_index",
    "SemanticGroundingLayer",
]
