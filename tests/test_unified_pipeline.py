import hashlib
import os
import tempfile
import pytest

from deconstructor import deconstruct
from integrity_manager import evaluate_source_quality, verify_worm_integrity
from unified_pipeline import SecurityError


class TestDeconstruct:
    def test_returns_nouns_key(self):
        result = deconstruct("Create an auth session with JWT")
        assert "nouns" in result

    def test_filters_stopwords(self):
        result = deconstruct("Create an auth session with JWT")
        assert "an" not in result["nouns"]
        assert "with" not in result["nouns"]

    def test_extracts_meaningful_terms(self):
        result = deconstruct("Create an auth session with JWT")
        assert "auth" in result["nouns"]
        assert "session" in result["nouns"]
        assert "jwt" in result["nouns"]

    def test_returns_lowercase_terms(self):
        result = deconstruct("JWT Auth Session")
        for noun in result["nouns"]:
            assert noun == noun.lower()

    def test_empty_query(self):
        result = deconstruct("")
        assert result["nouns"] == []

    def test_filters_short_tokens(self):
        result = deconstruct("an is at to")
        assert result["nouns"] == []


class TestEvaluateSourceQuality:
    def test_high_quality_content(self):
        content = (
            "This content references [source1] and has 42 data points. " * 10
        )
        report = evaluate_source_quality(content, 3)
        assert report.score > 0.7
        assert report.assessment == "high"

    def test_low_quality_content(self):
        report = evaluate_source_quality("short", 1)
        assert report.assessment == "low"

    def test_score_between_zero_and_one(self):
        report = evaluate_source_quality("some content", 1)
        assert 0.0 <= report.score <= 1.0

    def test_indicators_present(self):
        report = evaluate_source_quality("content [ref] with 5 items " * 20, 2)
        assert "has_citations" in report.indicators
        assert "has_specific_data" in report.indicators
        assert "reasonable_length" in report.indicators
        assert "has_multiple_sources" in report.indicators


class TestVerifyWormIntegrity:
    def test_matching_hash_returns_true(self):
        content = b"secure worm content"
        expected = hashlib.sha256(content).hexdigest()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            path = f.name
        try:
            assert verify_worm_integrity(path, expected) is True
        finally:
            os.unlink(path)

    def test_wrong_hash_returns_false(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"some content")
            path = f.name
        try:
            assert verify_worm_integrity(path, "deadbeef" * 8) is False
        finally:
            os.unlink(path)


class TestSecurityError:
    def test_security_error_is_exception(self):
        assert issubclass(SecurityError, Exception)

    def test_security_error_can_be_raised(self):
        with pytest.raises(SecurityError, match="WORM Integrity Compromised!"):
            raise SecurityError("WORM Integrity Compromised!")
