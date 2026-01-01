#!/usr/bin/env python3
"""
Wiktextract Parser - Stream JSONL.gz → Graph-Ready CSV/Parquet

Streaming parser for Wiktionary-derived data from kaikki.org.
Normalizes entries into language-filtered tables with optional Arabic root alignment.

Data source: https://kaikki.org/dictionary/rawdata.html
License: CC-BY-SA + GFDL (Wiktionary-derived content)

Usage:
    python -m rootai.data.parse_wiktextract \
        --input data/dictionaries/wiktextract/enwiktionary.jsonl.gz \
        --out-dir data/dictionaries/wiktextract/processed \
        --langs ar en \
        --formats csv parquet \
        --with-roots

Requirements:
    - Standard library (gzip, json)
    - Optional: orjson (faster JSON parsing)
    - Optional: pyarrow (for Parquet output)
    - Optional: camel-tools (for Arabic root extraction)
"""

import argparse
import gzip
import hashlib
import json
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, TextIO, Any

# Try importing optional dependencies
try:
    import orjson
    JSON_FAST = True
except ImportError:
    JSON_FAST = False

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False

try:
    from camel_tools.morphology.database import MorphologyDB
    from camel_tools.morphology.analyzer import Analyzer
    CAMEL_AVAILABLE = True
except ImportError:
    CAMEL_AVAILABLE = False

from .schema import CANONICAL_COLUMNS, DEFAULT_POS, normalize_pos, is_valid_pos


class WiktextractParser:
    """
    Streaming parser for Wiktextract JSONL.gz files.
    
    Processes Wiktionary-derived data with low memory footprint.
    """
    
    def __init__(
        self,
        input_path: str,
        output_dir: str,
        languages: Set[str] = None,
        pos_filter: Set[str] = None,
        with_roots: bool = False,
        formats: Set[str] = None
    ):
        """
        Initialize parser.
        
        Args:
            input_path: Path to input JSONL.gz file
            output_dir: Output directory for processed files
            languages: Set of language codes to extract (e.g., {'ar', 'en'})
            pos_filter: Set of allowed POS tags (default: DEFAULT_POS)
            with_roots: Enable Arabic root extraction via CAMeL Tools
            formats: Output formats {'csv', 'parquet'} (default: both)
        """
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self.languages = languages or {'ar', 'en'}
        self.pos_filter = pos_filter or DEFAULT_POS
        self.with_roots = with_roots
        self.formats = formats or {'csv', 'parquet'}
        
        # Statistics
        self.stats = {
            'total_lines': 0,
            'parsed_lines': 0,
            'filtered_entries': 0,
            'by_language': defaultdict(int),
            'by_pos': defaultdict(int),
            'errors': 0
        }
        
        # Output buffers (per language)
        self.buffers = {lang: [] for lang in self.languages}
        self.buffer_size = 1000  # Write every N entries
        
        # CAMeL Tools analyzer
        self.analyzer = None
        if self.with_roots and CAMEL_AVAILABLE:
            try:
                print("Initializing CAMeL Tools analyzer...")
                db = MorphologyDB.builtin_db()
                self.analyzer = Analyzer(db)
                print("✓ CAMeL Tools ready for root extraction")
            except Exception as e:
                print(f"Warning: CAMeL Tools initialization failed: {e}")
                print("  Arabic roots will be left empty")
        elif self.with_roots and not CAMEL_AVAILABLE:
            print("Warning: CAMeL Tools not available (pip install camel-tools)")
            print("  Install datasets with: camel_data -i light")
            print("  Arabic roots will be left empty")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize Unicode text (NFC) and strip control characters.
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Normalize to NFC form
        text = unicodedata.normalize("NFC", text)
        
        # Remove control characters
        text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
        
        return text.strip()
    
    def extract_arabic_root(self, lemma: str) -> tuple:
        """
        Extract Arabic triliteral root using CAMeL Tools.
        
        Args:
            lemma: Arabic lemma
            
        Returns:
            Tuple of (root, pattern) or (None, None) if unavailable
        """
        if not self.analyzer:
            return None, None
        
        try:
            analyses = self.analyzer.analyze(lemma)
            if analyses:
                # Get first analysis
                analysis = analyses[0]
                root = analysis.get('root', None)
                pattern = analysis.get('pattern', None)
                return root, pattern
        except Exception:
            pass
        
        return None, None
    
    def parse_entry(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a single Wiktextract entry.
        
        Args:
            entry: JSON entry from Wiktextract
            
        Returns:
            Normalized entry dictionary or None if filtered
        """
        # Extract basic fields
        word = entry.get('word', '')
        lang = entry.get('lang_code', entry.get('lang', ''))
        pos_raw = entry.get('pos', '')
        
        if not word or not lang:
            return None
        
        # Filter by language
        if lang not in self.languages:
            return None
        
        # Normalize POS
        pos = normalize_pos(pos_raw)
        
        # Filter by POS
        if not is_valid_pos(pos, self.pos_filter):
            return None
        
        # Normalize lemma
        lemma = self.normalize_text(word)
        if not lemma:
            return None
        
        # Extract senses
        senses = entry.get('senses', [])
        sense_gloss = ""
        sense_examples = []
        
        if senses:
            # Get first sense gloss
            first_sense = senses[0]
            glosses = first_sense.get('glosses', [])
            if glosses:
                sense_gloss = self.normalize_text(glosses[0])
            
            # Collect examples from all senses (limit to 3)
            for sense in senses[:3]:
                examples = sense.get('examples', [])
                for ex in examples[:2]:
                    if isinstance(ex, dict):
                        text = ex.get('text', '')
                    else:
                        text = str(ex)
                    if text:
                        sense_examples.append(self.normalize_text(text))
        
        # Etymology
        etymology = self.normalize_text(entry.get('etymology_text', ''))
        
        # Arabic roots (if enabled and language is Arabic)
        root = None
        pattern = None
        if lang == 'ar' and self.with_roots:
            root, pattern = self.extract_arabic_root(lemma)
        
        # Build normalized entry
        normalized = {
            'lang': lang,
            'lemma': lemma,
            'pos': pos,
            'root': root or '',
            'pattern': pattern or '',
            'sense_gloss': sense_gloss,
            'sense_examples': json.dumps(sense_examples) if sense_examples else '',
            'etymology': etymology[:200] if etymology else '',  # Limit length
            'source': 'kaikki.org/enwiktionary',
            'license': 'CC-BY-SA/GFDL'
        }
        
        return normalized
    
    def parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single JSONL line.
        
        Args:
            line: JSON line string
            
        Returns:
            Parsed entry or None if invalid
        """
        try:
            if JSON_FAST:
                entry = orjson.loads(line)
            else:
                entry = json.loads(line)
            
            return self.parse_entry(entry)
        
        except Exception as e:
            self.stats['errors'] += 1
            return None
    
    def write_buffer(self, lang: str, force: bool = False):
        """
        Write buffer for a language to disk.
        
        Args:
            lang: Language code
            force: Force write even if buffer not full
        """
        buffer = self.buffers[lang]
        
        if not buffer:
            return
        
        if not force and len(buffer) < self.buffer_size:
            return
        
        # Write CSV
        if 'csv' in self.formats:
            csv_path = self.output_dir / f"lemmas_{lang}.csv"
            mode = 'a' if csv_path.exists() else 'w'
            
            with open(csv_path, mode, encoding='utf-8') as f:
                if mode == 'w':
                    # Write header
                    f.write(','.join(CANONICAL_COLUMNS) + '\n')
                
                # Write rows
                for entry in buffer:
                    row = [str(entry.get(col, '')).replace(',', ';').replace('\n', ' ') 
                           for col in CANONICAL_COLUMNS]
                    f.write(','.join(row) + '\n')
        
        # Write Parquet (append mode)
        if 'parquet' in self.formats and PARQUET_AVAILABLE:
            parquet_path = self.output_dir / f"lemmas_{lang}.parquet"
            
            # Convert buffer to PyArrow table
            data = {col: [entry.get(col, '') for entry in buffer] 
                    for col in CANONICAL_COLUMNS}
            table = pa.table(data)
            
            # Append or create
            if parquet_path.exists():
                # Read existing and concatenate
                existing = pq.read_table(parquet_path)
                table = pa.concat_tables([existing, table])
            
            pq.write_table(table, parquet_path)
        
        # Clear buffer
        self.buffers[lang].clear()
    
    def stream_parse(self):
        """
        Stream and parse the input JSONL.gz file.
        """
        print(f"Parsing: {self.input_path}")
        print(f"Languages: {', '.join(sorted(self.languages))}")
        print(f"POS filter: {len(self.pos_filter)} tags")
        print(f"Output formats: {', '.join(sorted(self.formats))}")
        print()
        
        with gzip.open(self.input_path, 'rt', encoding='utf-8', errors='replace') as f:
            for line in f:
                self.stats['total_lines'] += 1
                
                # Progress indicator
                if self.stats['total_lines'] % 10000 == 0:
                    print(f"  Processed: {self.stats['total_lines']:,} lines, "
                          f"Extracted: {self.stats['filtered_entries']:,} entries", end='\r')
                
                # Parse line
                entry = self.parse_line(line)
                
                if entry:
                    self.stats['parsed_lines'] += 1
                    lang = entry['lang']
                    
                    # Add to buffer
                    self.buffers[lang].append(entry)
                    self.stats['filtered_entries'] += 1
                    self.stats['by_language'][lang] += 1
                    self.stats['by_pos'][entry['pos']] += 1
                    
                    # Write buffer if full
                    self.write_buffer(lang)
        
        print()  # New line after progress
        
        # Flush remaining buffers
        print("Flushing buffers...")
        for lang in self.languages:
            self.write_buffer(lang, force=True)
    
    def write_stats(self):
        """Write statistics JSON file."""
        stats_path = self.output_dir / "stats.json"
        
        stats_output = {
            'total_lines': self.stats['total_lines'],
            'parsed_lines': self.stats['parsed_lines'],
            'filtered_entries': self.stats['filtered_entries'],
            'errors': self.stats['errors'],
            'by_language': dict(self.stats['by_language']),
            'by_pos': dict(self.stats['by_pos']),
            'languages': list(self.languages),
            'pos_filter': list(self.pos_filter),
            'with_roots': self.with_roots,
            'camel_available': self.analyzer is not None,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats_output, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Statistics saved: {stats_path}")
    
    def write_provenance(self):
        """Write provenance markdown file."""
        prov_path = self.output_dir / "PROVENANCE.md"
        
        # Calculate SHA256 of input
        sha256_hash = hashlib.sha256()
        with open(self.input_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        sha256 = sha256_hash.hexdigest()
        
        content = f"""# Wiktextract Parse Provenance

## Source Data
- **Source**: kaikki.org Wiktextract (Wiktionary-derived)
- **URL**: https://kaikki.org/dictionary/rawdata.html
- **License**: CC-BY-SA 3.0 + GFDL (Wikimedia content)
- **Input File**: {self.input_path.name}
- **SHA256**: {sha256}

## Processing
- **Parser**: RootAI Wiktextract Parser
- **Timestamp**: {datetime.now().isoformat()}
- **Languages**: {', '.join(sorted(self.languages))}
- **POS Filter**: {len(self.pos_filter)} tags ({', '.join(sorted(list(self.pos_filter)[:5]))}{"..." if len(self.pos_filter) > 5 else ""})
- **With Roots**: {self.with_roots}
- **CAMeL Tools**: {"Available" if self.analyzer else "Not available"}

## Output Files
"""
        
        for lang in sorted(self.languages):
            content += f"\n### {lang.upper()}\n"
            for fmt in sorted(self.formats):
                ext = fmt
                filepath = self.output_dir / f"lemmas_{lang}.{ext}"
                if filepath.exists():
                    size_mb = filepath.stat().st_size / (1024 * 1024)
                    content += f"- `lemmas_{lang}.{ext}` ({size_mb:.2f} MB)\n"
        
        content += f"""
## Statistics
- Total lines processed: {self.stats['total_lines']:,}
- Entries extracted: {self.stats['filtered_entries']:,}
- Parse errors: {self.stats['errors']:,}

See `stats.json` for detailed breakdown.

## Attribution
When using this data, you must:
1. Attribute Wiktionary contributors (CC-BY-SA 3.0)
2. Share derivatives under CC-BY-SA 3.0 or compatible license
3. Include GFDL notice if redistributing verbatim copies

See: https://en.wikipedia.org/wiki/Wikipedia:Database_download
"""
        
        with open(prov_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Provenance saved: {prov_path}")
    
    def run(self):
        """Execute the full parsing pipeline."""
        print("=" * 70)
        print("RootAI Wiktextract Parser")
        print("=" * 70)
        print()
        
        # Parse
        self.stream_parse()
        
        # Write metadata
        print()
        self.write_stats()
        self.write_provenance()
        
        # Summary
        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total lines: {self.stats['total_lines']:,}")
        print(f"Entries extracted: {self.stats['filtered_entries']:,}")
        print(f"Errors: {self.stats['errors']:,}")
        print()
        print("By language:")
        for lang, count in sorted(self.stats['by_language'].items()):
            print(f"  {lang}: {count:,}")
        print()
        print(f"Output directory: {self.output_dir.absolute()}")
        print("=" * 70)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Parse Wiktextract JSONL.gz into graph-ready tables",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse English and Arabic entries
  python -m rootai.data.parse_wiktextract \\
    --input data/dictionaries/wiktextract/enwiktionary.jsonl.gz \\
    --out-dir data/dictionaries/wiktextract/processed \\
    --langs ar en
  
  # With Arabic root extraction
  python -m rootai.data.parse_wiktextract \\
    --input data/dictionaries/wiktextract/enwiktionary.jsonl.gz \\
    --out-dir data/dictionaries/wiktextract/processed \\
    --langs ar en \\
    --with-roots
  
  # CSV only
  python -m rootai.data.parse_wiktextract \\
    --input data/dictionaries/wiktextract/enwiktionary.jsonl.gz \\
    --out-dir data/dictionaries/wiktextract/processed \\
    --formats csv

Data source: https://kaikki.org/dictionary/rawdata.html
License: CC-BY-SA 3.0 + GFDL (Wiktionary-derived)
        """
    )
    
    parser.add_argument(
        "--input",
        required=True,
        help="Input JSONL.gz file from Wiktextract"
    )
    
    parser.add_argument(
        "--out-dir",
        required=True,
        help="Output directory for processed files"
    )
    
    parser.add_argument(
        "--langs",
        nargs="+",
        default=["ar", "en"],
        help="Language codes to extract (default: ar en)"
    )
    
    parser.add_argument(
        "--pos-filter",
        nargs="+",
        default=None,
        help="POS tags to include (default: NOUN VERB ADJ ADV PRON DET ADP CONJ NUM INTERJ)"
    )
    
    parser.add_argument(
        "--with-roots",
        action="store_true",
        help="Extract Arabic roots using CAMeL Tools (requires camel-tools)"
    )
    
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=["csv", "parquet"],
        default=["csv", "parquet"],
        help="Output formats (default: csv parquet)"
    )
    
    args = parser.parse_args()
    
    # Convert to sets
    languages = set(args.langs)
    pos_filter = set(args.pos_filter) if args.pos_filter else DEFAULT_POS
    formats = set(args.formats)
    
    # Check dependencies
    if 'parquet' in formats and not PARQUET_AVAILABLE:
        print("Warning: pyarrow not available. Parquet output disabled.")
        print("  Install with: pip install pyarrow")
        formats.discard('parquet')
    
    if args.with_roots and not CAMEL_AVAILABLE:
        print("Warning: camel-tools not available. Root extraction disabled.")
        print("  Install with: pip install camel-tools")
        print("  Then install datasets with: camel_data -i light")
    
    # Run parser
    wikt_parser = WiktextractParser(
        input_path=args.input,
        output_dir=args.out_dir,
        languages=languages,
        pos_filter=pos_filter,
        with_roots=args.with_roots,
        formats=formats
    )
    
    wikt_parser.run()


if __name__ == "__main__":
    main()
