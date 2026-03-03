import re
from typing import Dict, List

# Common English function words to exclude from noun extraction
_STOPWORDS = {
    'a', 'an', 'the', 'with', 'in', 'on', 'at', 'to', 'for',
    'of', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be',
    'been', 'being', 'do', 'does', 'did', 'has', 'have', 'had',
    'will', 'would', 'could', 'should', 'may', 'might', 'shall',
    'can', 'not', 'no', 'nor', 'so', 'yet', 'both', 'either',
    'that', 'this', 'these', 'those', 'it', 'its', 'my', 'your',
    'his', 'her', 'our', 'their', 'we', 'you', 'he', 'she', 'they',
    'i', 'me', 'him', 'us', 'them', 'who', 'which', 'what', 'how',
    'when', 'where', 'why', 'all', 'each', 'every', 'some', 'any',
}


def deconstruct(query: str) -> Dict[str, List[str]]:
    """
    Prompt Analyzer: Deconstructs a user query into semantic components.
    Returns a dict with 'nouns' extracted from the query for graph lookup.
    """
    tokens = re.findall(r'[a-zA-Z]+', query.lower())
    nouns = [t for t in tokens if t not in _STOPWORDS and len(t) > 2]
    return {'nouns': nouns}
