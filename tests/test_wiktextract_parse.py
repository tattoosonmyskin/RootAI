"""
Test suite for Wiktextract parser

Run with: pytest tests/test_wiktextract_parse.py -v
"""

import pytest
import json
from pathlib import Path
import tempfile
import shutil

from rootai.data.parse_wiktextract import WiktextractParser
from rootai.data.schema import normalize_pos, is_valid_pos, DEFAULT_POS


class TestSchemaFunctions:
    """Test schema normalization functions."""
    
    def test_normalize_pos_noun(self):
        """Test POS normalization for nouns."""
        assert normalize_pos("noun") == "NOUN"
        assert normalize_pos("name") == "NOUN"
        assert normalize_pos("proper_noun") == "NOUN"
    
    def test_normalize_pos_verb(self):
        """Test POS normalization for verbs."""
        assert normalize_pos("verb") == "VERB"
        assert normalize_pos("aux") == "VERB"
    
    def test_normalize_pos_adjective(self):
        """Test POS normalization for adjectives."""
        assert normalize_pos("adj") == "ADJ"
        assert normalize_pos("adjective") == "ADJ"
    
    def test_normalize_pos_unknown(self):
        """Test POS normalization for unknown tags."""
        assert normalize_pos("unknown_pos") == "OTHER"
    
    def test_is_valid_pos(self):
        """Test POS validation."""
        assert is_valid_pos("NOUN", DEFAULT_POS)
        assert is_valid_pos("VERB", DEFAULT_POS)
        assert not is_valid_pos("OTHER", DEFAULT_POS)
        assert not is_valid_pos("AFFIX", DEFAULT_POS)


class TestWiktextractParser:
    """Test Wiktextract parser."""
    
    @pytest.fixture
    def fixture_path(self):
        """Get path to test fixture."""
        return Path(__file__).parent / "fixtures" / "wiktextract_sample.jsonl.gz"
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_fixture_exists(self, fixture_path):
        """Test that fixture file exists."""
        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"
    
    def test_parser_initialization(self, fixture_path, temp_output_dir):
        """Test parser initialization."""
        parser = WiktextractParser(
            input_path=str(fixture_path),
            output_dir=temp_output_dir,
            languages={'ar', 'en'},
            formats={'csv'}
        )
        
        assert parser.input_path == fixture_path
        assert parser.output_dir == Path(temp_output_dir)
        assert parser.languages == {'ar', 'en'}
        assert 'csv' in parser.formats
    
    def test_normalize_text(self, fixture_path, temp_output_dir):
        """Test text normalization."""
        parser = WiktextractParser(
            input_path=str(fixture_path),
            output_dir=temp_output_dir,
            languages={'en'}
        )
        
        # Test basic normalization
        assert parser.normalize_text("  hello  ") == "hello"
        assert parser.normalize_text("hello\nworld") == "hello world"
        
        # Test Unicode normalization (NFC)
        # café with combining accent vs precomposed
        text1 = "cafe\u0301"  # e + combining acute
        text2 = "café"  # precomposed é
        assert parser.normalize_text(text1) == parser.normalize_text(text2)
    
    def test_parse_entry_english(self, fixture_path, temp_output_dir):
        """Test parsing English entry."""
        parser = WiktextractParser(
            input_path=str(fixture_path),
            output_dir=temp_output_dir,
            languages={'en'}
        )
        
        entry = {
            "word": "book",
            "lang_code": "en",
            "pos": "noun",
            "senses": [{"glosses": ["A collection of pages"]}]
        }
        
        result = parser.parse_entry(entry)
        
        assert result is not None
        assert result['lang'] == 'en'
        assert result['lemma'] == 'book'
        assert result['pos'] == 'NOUN'
        assert 'collection' in result['sense_gloss'].lower()
        assert result['source'] == 'kaikki.org/enwiktionary'
        assert result['license'] == 'CC-BY-SA/GFDL'
    
    def test_parse_entry_arabic(self, fixture_path, temp_output_dir):
        """Test parsing Arabic entry."""
        parser = WiktextractParser(
            input_path=str(fixture_path),
            output_dir=temp_output_dir,
            languages={'ar'}
        )
        
        entry = {
            "word": "كتاب",
            "lang_code": "ar",
            "pos": "noun",
            "senses": [{"glosses": ["book"]}]
        }
        
        result = parser.parse_entry(entry)
        
        assert result is not None
        assert result['lang'] == 'ar'
        assert result['lemma'] == 'كتاب'
        assert result['pos'] == 'NOUN'
    
    def test_language_filter(self, fixture_path, temp_output_dir):
        """Test language filtering."""
        parser = WiktextractParser(
            input_path=str(fixture_path),
            output_dir=temp_output_dir,
            languages={'en'}  # Only English
        )
        
        # Arabic entry should be filtered out
        arabic_entry = {
            "word": "كتاب",
            "lang_code": "ar",
            "pos": "noun",
            "senses": [{"glosses": ["book"]}]
        }
        
        result = parser.parse_entry(arabic_entry)
        assert result is None  # Filtered
        
        # English entry should pass
        english_entry = {
            "word": "book",
            "lang_code": "en",
            "pos": "noun",
            "senses": [{"glosses": ["book"]}]
        }
        
        result = parser.parse_entry(english_entry)
        assert result is not None
    
    def test_pos_filter(self, fixture_path, temp_output_dir):
        """Test POS filtering."""
        parser = WiktextractParser(
            input_path=str(fixture_path),
            output_dir=temp_output_dir,
            languages={'en'},
            pos_filter={'NOUN'}  # Only nouns
        )
        
        # Verb should be filtered out
        verb_entry = {
            "word": "write",
            "lang_code": "en",
            "pos": "verb",
            "senses": [{"glosses": ["to write"]}]
        }
        
        result = parser.parse_entry(verb_entry)
        assert result is None  # Filtered
        
        # Noun should pass
        noun_entry = {
            "word": "book",
            "lang_code": "en",
            "pos": "noun",
            "senses": [{"glosses": ["book"]}]
        }
        
        result = parser.parse_entry(noun_entry)
        assert result is not None
    
    def test_full_parse_csv(self, fixture_path, temp_output_dir):
        """Test full parsing pipeline with CSV output."""
        parser = WiktextractParser(
            input_path=str(fixture_path),
            output_dir=temp_output_dir,
            languages={'ar', 'en'},
            formats={'csv'}
        )
        
        # Run parser
        parser.run()
        
        # Check output files
        ar_csv = Path(temp_output_dir) / "lemmas_ar.csv"
        en_csv = Path(temp_output_dir) / "lemmas_en.csv"
        stats_json = Path(temp_output_dir) / "stats.json"
        provenance = Path(temp_output_dir) / "PROVENANCE.md"
        
        assert en_csv.exists(), "English CSV not created"
        assert ar_csv.exists(), "Arabic CSV not created"
        assert stats_json.exists(), "Stats JSON not created"
        assert provenance.exists(), "Provenance not created"
        
        # Check stats
        with open(stats_json) as f:
            stats = json.load(f)
        
        # Verify total counts
        assert stats['total_lines'] == 6  # 6 entries in fixture
        assert stats['filtered_entries'] == 5  # 5 entries (French filtered out)
        
        # Verify language breakdown
        assert 'ar' in stats['by_language']
        assert 'en' in stats['by_language']
        assert stats['by_language']['ar'] == 2  # 2 Arabic entries (noun, verb)
        assert stats['by_language']['en'] == 3  # 3 English entries (noun, verb, adj)
        
        # Verify French was filtered out
        assert 'fr' not in stats['by_language'], "French entries should be filtered"
        
        # Verify actual content in CSV files
        with open(en_csv, encoding='utf-8') as f:
            en_lines = f.readlines()
            assert len(en_lines) == 4  # Header + 3 entries
            # Check that 'book', 'write', 'quick' are present
            content = ''.join(en_lines)
            assert 'book' in content, "English 'book' entry missing"
            assert 'write' in content, "English 'write' entry missing"
            assert 'quick' in content, "English 'quick' entry missing"
        
        with open(ar_csv, encoding='utf-8') as f:
            ar_lines = f.readlines()
            assert len(ar_lines) == 3  # Header + 2 entries
            # Check that Arabic entries are present
            content = ''.join(ar_lines)
            assert 'كتاب' in content or 'كتب' in content, "Arabic entries missing"
    
    def test_parse_with_examples(self, fixture_path, temp_output_dir):
        """Test parsing entries with examples."""
        parser = WiktextractParser(
            input_path=str(fixture_path),
            output_dir=temp_output_dir,
            languages={'en'}
        )
        
        entry = {
            "word": "book",
            "lang_code": "en",
            "pos": "noun",
            "senses": [
                {
                    "glosses": ["A collection of pages"],
                    "examples": [
                        {"text": "I read a book"},
                        {"text": "She bought a book"}
                    ]
                }
            ]
        }
        
        result = parser.parse_entry(entry)
        
        assert result is not None
        assert result['sense_examples']  # Should have examples
        
        # Parse JSON examples
        examples = json.loads(result['sense_examples'])
        assert len(examples) == 2
        assert "read a book" in examples[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
