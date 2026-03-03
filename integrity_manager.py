"""
Integrity Manager – Resource Manager utilities.

* verify_worm_integrity: SHA-256 hash check for immutable WORM storage.
* evaluate_source_quality: Reliability scoring for grounding documents.
"""

import hashlib
from typing import Dict

from pydantic import BaseModel


class ReliabilityReport(BaseModel):
    score: float
    assessment: str
    indicators: Dict[str, bool]


def evaluate_source_quality(content: str, source_count: int) -> ReliabilityReport:
    """Analyse quality based on specific data-points and structure."""
    indicators = {
        "has_citations": "[" in content and "]" in content,
        "has_specific_data": any(char.isdigit() for char in content),
        "reasonable_length": len(content) > 200,
        "has_multiple_sources": source_count > 1,
    }

    passed_checks = sum(1 for v in indicators.values() if v)
    score = passed_checks / len(indicators)
    assessment = "high" if score > 0.7 else "medium" if score > 0.4 else "low"

    return ReliabilityReport(score=score, assessment=assessment, indicators=indicators)


def verify_worm_integrity(file_path: str, expected_hash: str) -> bool:
    """Return True only when the file's SHA-256 digest matches expected_hash."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest() == expected_hash
