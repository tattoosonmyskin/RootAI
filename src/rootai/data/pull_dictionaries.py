#!/usr/bin/env python3
"""
Dictionary Puller - OMW/OEWN via 'wn' Python Library

Downloads Open Multilingual WordNet and Open English WordNet lexicons
using the 'wn' library (https://pypi.org/project/wn/).

Data sources:
- OEWN (Open English WordNet): https://en-word.net/ - CC-BY 4.0
- OMW (Open Multilingual WordNet): https://omwn.org/ - Open license
- OMW Arabic: https://compling.upol.cz/omw/omw - CC-BY variants

All data is CPU-safe and requires no API credentials.

Usage:
    python -m rootai.data.pull_dictionaries \
        --dest data/dictionaries/omw \
        --sets oewn:2024 omw:1.4 omw-arb:1.4

Requirements:
    pip install wn

Offline mode:
    Set ROOTAI_OFFLINE=1 to skip network downloads (for CI/offline environments)
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List

try:
    import wn
    WN_AVAILABLE = True
except ImportError:
    WN_AVAILABLE = False
    print("Error: 'wn' library not installed.")
    print("Please install with: pip install wn")
    print("See: https://pypi.org/project/wn/")


def setup_wn_directory(dest: str) -> None:
    """
    Configure 'wn' library to use specified data directory.
    
    Args:
        dest: Destination directory for WordNet data
    """
    if not WN_AVAILABLE:
        raise RuntimeError("wn library not available")
    
    dest_path = Path(dest)
    dest_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Setting wn data directory to: {dest_path.absolute()}")
    wn.config.data_home = dest_path.absolute()
    print(f"✓ Data directory configured")


def download_lexicon_set(lexicon_spec: str) -> dict:
    """
    Download a lexicon set using wn library.
    
    Args:
        lexicon_spec: Lexicon specification (e.g., "oewn:2024", "omw:1.4")
        
    Returns:
        Dictionary with download statistics
        
    Raises:
        RuntimeError: If download fails or offline mode is enabled
    """
    if not WN_AVAILABLE:
        raise RuntimeError("wn library not available")
    
    # Check for offline mode
    if os.environ.get('ROOTAI_OFFLINE', '').lower() in ('1', 'true', 'yes'):
        print(f"\n⚠ OFFLINE MODE: Skipping download of {lexicon_spec}")
        print("  Run in CI job 'omw-download' or locally without ROOTAI_OFFLINE=1")
        return {
            "lexicon": lexicon_spec,
            "success": False,
            "error": "Offline mode enabled (ROOTAI_OFFLINE=1)"
        }
    
    print(f"\nDownloading lexicon: {lexicon_spec}")
    print("-" * 60)
    
    try:
        # Download the lexicon
        wn.download(lexicon_spec)
        
        # Get lexicon info
        try:
            # Parse lexicon spec
            if ":" in lexicon_spec:
                lex_id = lexicon_spec.split(":")[0]
            else:
                lex_id = lexicon_spec
            
            # Get the downloaded lexicon
            lexicons = wn.lexicons(lang="*")
            matching = [l for l in lexicons if lex_id in l.id()]
            
            if matching:
                lex = matching[0]
                synsets = list(lex.synsets())
                words = list(lex.words())
                
                stats = {
                    "lexicon": lexicon_spec,
                    "id": lex.id(),
                    "language": lex.language(),
                    "synsets": len(synsets),
                    "words": len(words),
                    "success": True
                }
                
                print(f"✓ Downloaded: {lex.id()}")
                print(f"  Language: {lex.language()}")
                print(f"  Synsets: {len(synsets):,}")
                print(f"  Words: {len(words):,}")
                
                return stats
            else:
                # Fallback if we can't find the lexicon
                print(f"✓ Downloaded: {lexicon_spec}")
                print(f"  (Unable to retrieve detailed stats)")
                return {
                    "lexicon": lexicon_spec,
                    "success": True
                }
                
        except Exception as e:
            print(f"✓ Downloaded: {lexicon_spec}")
            print(f"  (Stats unavailable: {e})")
            return {
                "lexicon": lexicon_spec,
                "success": True
            }
            
    except Exception as e:
        print(f"✗ Failed to download: {lexicon_spec}")
        print(f"  Error: {e}")
        return {
            "lexicon": lexicon_spec,
            "success": False,
            "error": str(e)
        }


def pull_dictionaries(dest: str, lexicon_sets: List[str]) -> None:
    """
    Download multiple lexicon sets to destination directory.
    
    Args:
        dest: Destination directory for WordNet data
        lexicon_sets: List of lexicon specifications
    """
    print("=" * 70)
    print("RootAI Dictionary Puller - OMW/OEWN via 'wn'")
    print("=" * 70)
    print(f"Destination: {dest}")
    print(f"Lexicon sets: {', '.join(lexicon_sets)}")
    print("")
    
    # Check if wn is available
    if not WN_AVAILABLE:
        print("ERROR: 'wn' library not installed")
        print("Install with: pip install wn")
        print("See: https://pypi.org/project/wn/")
        sys.exit(1)
    
    # Setup directory
    setup_wn_directory(dest)
    
    # Download each lexicon set
    results = []
    for lex_spec in lexicon_sets:
        result = download_lexicon_set(lex_spec)
        results.append(result)
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    print(f"Total lexicons requested: {len(lexicon_sets)}")
    print(f"Successfully downloaded: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        print("\n✓ Downloaded lexicons:")
        for result in successful:
            if "synsets" in result:
                print(f"  - {result['lexicon']}: {result['synsets']:,} synsets, "
                      f"{result['words']:,} words ({result.get('language', 'unknown')})")
            else:
                print(f"  - {result['lexicon']}")
    
    if failed:
        print("\n✗ Failed downloads:")
        for result in failed:
            print(f"  - {result['lexicon']}: {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 70)
    print("Data location: " + str(Path(dest).absolute()))
    print("\nIMPORTANT: Review DATA_LICENSES.md for attribution requirements")
    print("=" * 70)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Download OMW/OEWN dictionaries using 'wn' library",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download OEWN and OMW core
  python -m rootai.data.pull_dictionaries --sets oewn:2024 omw:1.4
  
  # Download OEWN, OMW, and Arabic WordNet
  python -m rootai.data.pull_dictionaries --sets oewn:2024 omw:1.4 omw-arb:1.4
  
  # Custom destination
  python -m rootai.data.pull_dictionaries --dest /path/to/data --sets oewn:2024

Data sources:
  - OEWN: https://en-word.net/ (CC-BY 4.0)
  - OMW: https://omwn.org/ (Open license)
  - OMW Arabic: https://compling.upol.cz/omw/omw (CC-BY variants)

See DATA_LICENSES.md for full license information.
        """
    )
    
    parser.add_argument(
        "--dest",
        default="data/dictionaries/omw",
        help="Destination directory for WordNet data (default: data/dictionaries/omw)"
    )
    
    parser.add_argument(
        "--sets",
        nargs="+",
        default=["oewn:2024", "omw:1.4", "omw-arb:1.4"],
        help="Lexicon sets to download (default: oewn:2024 omw:1.4 omw-arb:1.4)"
    )
    
    args = parser.parse_args()
    
    pull_dictionaries(dest=args.dest, lexicon_sets=args.sets)


if __name__ == "__main__":
    main()
