"""
Schema definitions for RootAI dictionary data

Defines canonical columns, POS tags, and data structure
for normalized dictionary outputs.
"""

from typing import Set, List

# Canonical column schema for normalized dictionary data
CANONICAL_COLUMNS: List[str] = [
    "lang",           # ISO language code (e.g., "ar", "en")
    "lemma",          # Normalized lemma/word
    "pos",            # Coarse part-of-speech tag
    "root",           # Triliteral root (Arabic only, via CAMeL Tools)
    "pattern",        # Morphological pattern (Arabic only, optional)
    "sense_gloss",    # Primary sense definition/gloss
    "sense_examples", # JSON-encoded list of usage examples
    "etymology",      # Etymology information if available
    "source",         # Data source (e.g., "kaikki.org/enwiktionary")
    "license"         # License (e.g., "CC-BY-SA/GFDL")
]

# Default POS tags to include (coarse-grained)
DEFAULT_POS: Set[str] = {
    "NOUN",
    "VERB",
    "ADJ",
    "ADV",
    "PRON",
    "DET",
    "ADP",
    "CONJ",
    "NUM",
    "INTERJ"
}

# Wiktextract POS to canonical coarse POS mapping
WIKTEXTRACT_POS_MAP = {
    # Nouns
    "noun": "NOUN",
    "name": "NOUN",
    "proper_noun": "NOUN",
    "prop": "NOUN",
    
    # Verbs
    "verb": "VERB",
    "aux": "VERB",
    
    # Adjectives
    "adj": "ADJ",
    "adjective": "ADJ",
    
    # Adverbs
    "adv": "ADV",
    "adverb": "ADV",
    
    # Pronouns
    "pron": "PRON",
    "pronoun": "PRON",
    
    # Determiners
    "det": "DET",
    "determiner": "DET",
    "article": "DET",
    
    # Adpositions
    "adp": "ADP",
    "prep": "ADP",
    "preposition": "ADP",
    "postp": "ADP",
    "postposition": "ADP",
    
    # Conjunctions
    "conj": "CONJ",
    "conjunction": "CONJ",
    "cconj": "CONJ",
    "sconj": "CONJ",
    
    # Numerals
    "num": "NUM",
    "number": "NUM",
    "numeral": "NUM",
    
    # Interjections
    "intj": "INTERJ",
    "interjection": "INTERJ",
    
    # Other
    "particle": "PART",
    "part": "PART",
    "affix": "AFFIX",
    "prefix": "AFFIX",
    "suffix": "AFFIX",
    "symbol": "SYM",
    "punct": "PUNCT",
    "punctuation": "PUNCT"
}


def normalize_pos(wiktextract_pos: str) -> str:
    """
    Normalize Wiktextract POS tag to canonical coarse POS.
    
    Args:
        wiktextract_pos: POS tag from Wiktextract (e.g., "noun", "verb")
        
    Returns:
        Canonical coarse POS tag (e.g., "NOUN", "VERB")
    """
    pos_lower = wiktextract_pos.lower().strip()
    return WIKTEXTRACT_POS_MAP.get(pos_lower, "OTHER")


def is_valid_pos(pos: str, allowed_pos: Set[str] = None) -> bool:
    """
    Check if POS tag is in allowed set.
    
    Args:
        pos: Canonical POS tag
        allowed_pos: Set of allowed POS tags (default: DEFAULT_POS)
        
    Returns:
        True if POS is allowed
    """
    if allowed_pos is None:
        allowed_pos = DEFAULT_POS
    return pos in allowed_pos
