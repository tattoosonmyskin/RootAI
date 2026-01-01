# RootAI Dictionary Data

This directory contains lexical dictionary data from multiple open sources.

## Overview

RootAI can integrate with several open dictionaries for enhanced semantic reasoning:

- **OEWN** (Open English WordNet) - English lexical database
- **OMW** (Open Multilingual WordNet) - Multi-language wordnets
- **Wiktextract** (kaikki.org) - Wiktionary-derived lexicons
- **CAMeL Tools datasets** - Arabic morphology and lexicons

All data sources are **CPU-safe** and require **no API credentials**.

⚠️ **IMPORTANT**: Review [DATA_LICENSES.md](../../DATA_LICENSES.md) for license requirements and attribution obligations.

## Directory Structure

```
dictionaries/
├── omw/               # OMW/OEWN data (via 'wn' library)
├── wiktextract/       # Wiktionary-derived data (kaikki.org)
│   ├── enwiktionary.jsonl.gz   # Raw data
│   └── processed/               # Parsed tables
│       ├── lemmas_ar.csv
│       ├── lemmas_ar.parquet
│       ├── lemmas_en.csv
│       ├── lemmas_en.parquet
│       ├── stats.json
│       └── PROVENANCE.md
├── arabic_morph/      # CAMeL Tools datasets (optional)
└── checksums/         # SHA256 checksums
```

---

## Downloading Dictionaries

### Option 1: Using RootAI CLI (Recommended)

Download all dictionaries in one command:

```bash
# Download OMW/OEWN only
./rootai_cli.py dictionaries

# Download OMW/OEWN + Wiktextract
./rootai_cli.py dictionaries --wiktextract

# Custom destination and specific lexicon sets
./rootai_cli.py dictionaries \
  --dest data/dictionaries/omw \
  --sets oewn:2024 omw:1.4 omw-arb:1.4 \
  --wiktextract
```

### Option 2: Python Module (OMW/OEWN)

Download OMW and OEWN using the `wn` library:

```bash
# Install wn library
pip install wn

# Download lexicons
python -m rootai.data.pull_dictionaries \
  --dest data/dictionaries/omw \
  --sets oewn:2024 omw:1.4 omw-arb:1.4
```

Available lexicon sets:
- `oewn:2024` - Open English WordNet (latest)
- `omw:1.4` - Open Multilingual WordNet core
- `omw-arb:1.4` - Arabic WordNet via OMW
- See `wn download --help` for more options

### Option 3: Shell Script (Wiktextract)

Download Wiktionary-derived data from kaikki.org:

```bash
# Download Wiktextract raw data
bash data/fetch_dictionaries.sh
```

This downloads:
- `wiktextract/enwiktionary.jsonl.gz` (~2-5 GB compressed)
- SHA256 checksum to `checksums/enwiktionary.sha256`

---

## Parsing Wiktextract Data

After downloading Wiktextract, parse it into graph-ready tables:

### Using CLI

```bash
# Parse English and Arabic entries (default)
./rootai_cli.py wiktextract-parse \
  --input data/dictionaries/wiktextract/enwiktionary.jsonl.gz \
  --out-dir data/dictionaries/wiktextract/processed \
  --langs ar en

# With Arabic root extraction (requires camel-tools)
./rootai_cli.py wiktextract-parse \
  --input data/dictionaries/wiktextract/enwiktionary.jsonl.gz \
  --out-dir data/dictionaries/wiktextract/processed \
  --langs ar en \
  --with-roots

# CSV only (skip Parquet)
./rootai_cli.py wiktextract-parse \
  --input data/dictionaries/wiktextract/enwiktionary.jsonl.gz \
  --out-dir data/dictionaries/wiktextract/processed \
  --langs ar en \
  --formats csv
```

### Using Python Module

```bash
python -m rootai.data.parse_wiktextract \
  --input data/dictionaries/wiktextract/enwiktionary.jsonl.gz \
  --out-dir data/dictionaries/wiktextract/processed \
  --langs ar en \
  --formats csv parquet \
  --with-roots
```

### Parser Options

- `--langs` - Language codes to extract (e.g., `ar en es fr`)
- `--pos-filter` - POS tags to include (default: NOUN VERB ADJ ADV PRON DET ADP CONJ NUM INTERJ)
- `--with-roots` - Extract Arabic roots via CAMeL Tools (requires `camel-tools`)
- `--formats` - Output formats: `csv`, `parquet`, or both

### Output Files

After parsing, you'll get:

- `lemmas_{lang}.csv` - CSV table per language
- `lemmas_{lang}.parquet` - Parquet table per language (if enabled)
- `stats.json` - Statistics (row counts, POS breakdown)
- `PROVENANCE.md` - Source metadata and SHA256 checksum

---

## CAMeL Tools Datasets (Arabic)

For Arabic root extraction and morphology:

```bash
# Install CAMeL Tools
pip install camel-tools

# Install light datasets (recommended)
camel_data -i light

# Or install full datasets
camel_data -i all
```

CAMeL Tools datasets are installed to `~/.camel_tools/` by default.

⚠️ **NOTE**: Some datasets may have specific license requirements. Check before redistribution.

---

## Output Schema

Parsed dictionaries use a normalized schema:

| Column | Description | Example |
|--------|-------------|---------|
| `lang` | ISO language code | `ar`, `en` |
| `lemma` | Normalized lemma/word | `book`, `كتاب` |
| `pos` | Coarse part-of-speech | `NOUN`, `VERB` |
| `root` | Triliteral root (Arabic only) | `كتب` |
| `pattern` | Morphological pattern | `فعال` |
| `sense_gloss` | Primary definition/gloss | `A collection of pages` |
| `sense_examples` | JSON list of examples | `["I read a book"]` |
| `etymology` | Etymology info (if available) | `From Old English bōc` |
| `source` | Data source | `kaikki.org/enwiktionary` |
| `license` | License | `CC-BY-SA/GFDL` |

---

## License & Attribution

### When Using This Data

You **MUST** comply with the license requirements:

1. **Wiktextract/Wiktionary** (CC-BY-SA 3.0 + GFDL)
   - ✓ Attribute Wiktionary contributors
   - ✓ Share derivatives under CC-BY-SA 3.0
   - ✓ Include license notice

2. **OEWN** (CC-BY 4.0)
   - ✓ Attribute Open English WordNet
   - ✓ Attribute Princeton WordNet
   - No share-alike requirement

3. **OMW** (varies by wordnet)
   - ✓ Check specific wordnet license
   - ✓ Attribute appropriately

4. **CAMeL Tools** (MIT)
   - ✓ Attribute CAMeL Lab, NYU Abu Dhabi
   - Check dataset-specific licenses

See [DATA_LICENSES.md](../../DATA_LICENSES.md) for full details.

### Attribution Template

When publishing work using this data:

```
This work uses the following lexical resources:

- Open English WordNet (https://en-word.net/) - CC-BY 4.0
- Open Multilingual WordNet (https://omwn.org/) - Open license
- Wiktionary via Wiktextract (https://kaikki.org/) - CC-BY-SA 3.0 + GFDL
- CAMeL Tools (https://github.com/CAMeL-Lab/camel_tools) - MIT

See DATA_LICENSES.md for full attribution requirements.
```

---

## Performance & Resource Usage

### Disk Space

- **OMW/OEWN**: ~500 MB (varies by lexicon sets)
- **Wiktextract raw**: ~2-5 GB (compressed JSONL.gz)
- **Wiktextract parsed**: ~500 MB - 2 GB per language (CSV + Parquet)
- **CAMeL Tools datasets**: 
  - Light: ~100 MB
  - Full: ~1-2 GB

### Parsing Performance

Wiktextract parsing is **streaming** and **low-memory**:
- Memory usage: <500 MB (does not load entire file)
- Speed: ~10,000-50,000 entries/second (depends on CPU)
- English Wiktionary (~6M entries): ~5-15 minutes on modern CPU

### Network Usage

- OMW/OEWN: Downloads directly via `wn` library (HTTP)
- Wiktextract: Downloads from kaikki.org (HTTPS, resume supported)
- CAMeL Tools datasets: Downloads from CAMeL Lab servers

All downloads support **resume** for interrupted transfers.

---

## Troubleshooting

### "wn library not installed"

```bash
pip install wn
```

### "CAMeL Tools not available"

```bash
pip install camel-tools
camel_data -i light
```

### "pyarrow not available" (for Parquet)

```bash
pip install pyarrow
```

Or use `--formats csv` to skip Parquet.

### "Download failed" or "Connection timeout"

- Check your internet connection
- Try again (downloads support resume via `-C` flag in curl)
- For Wiktextract, manually download from https://kaikki.org/dictionary/rawdata.html

### "Out of memory" during parsing

- Wiktextract parser is streaming and should NOT cause OOM
- If it happens, reduce `buffer_size` in `parse_wiktextract.py` (default: 1000)
- Or parse one language at a time: `--langs ar` then `--langs en`

---

## Examples

### Complete Workflow

```bash
# 1. Download all dictionaries
./rootai_cli.py dictionaries --wiktextract

# 2. Parse Wiktextract with Arabic roots
./rootai_cli.py wiktextract-parse \
  --input data/dictionaries/wiktextract/enwiktionary.jsonl.gz \
  --out-dir data/dictionaries/wiktextract/processed \
  --langs ar en \
  --with-roots

# 3. Verify outputs
ls -lh data/dictionaries/wiktextract/processed/
cat data/dictionaries/wiktextract/processed/stats.json
```

### Using in RootAI

```python
from rootai.core.root_reasoner import RootReasoner
import pandas as pd

# Load parsed dictionary
lemmas_ar = pd.read_csv('data/dictionaries/wiktextract/processed/lemmas_ar.csv')

# Or use Parquet (faster)
lemmas_ar = pd.read_parquet('data/dictionaries/wiktextract/processed/lemmas_ar.parquet')

# Filter for specific POS
nouns = lemmas_ar[lemmas_ar['pos'] == 'NOUN']

# Get roots
roots = lemmas_ar[lemmas_ar['root'].notna()]['root'].unique()

print(f"Total Arabic nouns: {len(nouns)}")
print(f"Unique roots: {len(roots)}")
```

---

## References

- OMW: https://omwn.org/
- OEWN: https://en-word.net/
- Wiktextract: https://github.com/tatuylonen/wiktextract
- Kaikki.org: https://kaikki.org/dictionary/rawdata.html
- CAMeL Tools: https://github.com/CAMeL-Lab/camel_tools
- wn library: https://pypi.org/project/wn/

---

**Last Updated**: 2026-01-01  
**RootAI Version**: 3.0.1
