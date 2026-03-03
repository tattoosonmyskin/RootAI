"""
Prompt Analyzer – deconstructs a natural-language query into its
structural components (nouns, verbs, original text).

Uses spaCy when the 'en_core_web_sm' model is available and falls
back to simple whitespace tokenisation otherwise.  The spaCy model
is loaded once at module level to avoid repeated initialisation overhead.
"""

_nlp = None


def _get_nlp():
    """Return a cached spaCy model, loading it on first call."""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
        except Exception:
            _nlp = False  # sentinel: spaCy unavailable
    return _nlp


def deconstruct(text: str) -> dict:
    """Return a dict with 'nouns', 'verbs', and 'original' keys."""
    nlp = _get_nlp()
    if nlp:
        doc = nlp(text)
        nouns = [token.text.lower() for token in doc if token.pos_ in ("NOUN", "PROPN")]
        verbs = [token.text.lower() for token in doc if token.pos_ == "VERB"]
    else:
        # Graceful fallback: treat every whitespace-separated word as a noun
        nouns = text.lower().split()
        verbs = []

    return {"nouns": nouns, "verbs": verbs, "original": text}
