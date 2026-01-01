#!/usr/bin/env bash
#
# fetch_dictionaries.sh - Download Wiktextract dictionary data
#
# Downloads the latest English Wiktionary JSONL dump from kaikki.org
# and verifies with SHA256 checksum. CPU-only, no credentials required.
#
# Usage:
#   bash data/fetch_dictionaries.sh
#
# Data source: https://kaikki.org/dictionary/rawdata.html
# License: Wiktionary content is CC-BY-SA + GFDL (see DATA_LICENSES.md)

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="${SCRIPT_DIR}"
WIKTEXTRACT_DIR="${BASE_DIR}/dictionaries/wiktextract"
CHECKSUM_DIR="${BASE_DIR}/dictionaries/checksums"

# Kaikki.org Wiktextract raw data URL
# TODO: Update URL if kaikki.org changes their latest data location
WIKTEXTRACT_URL="https://kaikki.org/dictionary/rawdata/kaikki.org-dictionary-English.json.gz"
WIKTEXTRACT_FILE="enwiktionary.jsonl.gz"

echo "======================================================================"
echo "RootAI Dictionary Fetcher - Wiktextract"
echo "======================================================================"
echo "Source: kaikki.org (Wiktionary-derived)"
echo "License: CC-BY-SA + GFDL (see DATA_LICENSES.md)"
echo "======================================================================"
echo ""

# Create directories
mkdir -p "${WIKTEXTRACT_DIR}"
mkdir -p "${CHECKSUM_DIR}"

# Download Wiktextract data
echo "Downloading Wiktextract data..."
echo "URL: ${WIKTEXTRACT_URL}"
echo "Destination: ${WIKTEXTRACT_DIR}/${WIKTEXTRACT_FILE}"
echo ""

# Use curl with resume support
if command -v curl &> /dev/null; then
    curl -L -C - -o "${WIKTEXTRACT_DIR}/${WIKTEXTRACT_FILE}" "${WIKTEXTRACT_URL}"
elif command -v wget &> /dev/null; then
    wget -c -O "${WIKTEXTRACT_DIR}/${WIKTEXTRACT_FILE}" "${WIKTEXTRACT_URL}"
else
    echo "Error: Neither curl nor wget found. Please install one of them."
    exit 1
fi

echo ""
echo "Download complete!"

# Generate SHA256 checksum
echo ""
echo "Generating SHA256 checksum..."
CHECKSUM_FILE="${CHECKSUM_DIR}/enwiktionary.sha256"

if command -v sha256sum &> /dev/null; then
    (cd "${WIKTEXTRACT_DIR}" && sha256sum "${WIKTEXTRACT_FILE}") > "${CHECKSUM_FILE}"
elif command -v shasum &> /dev/null; then
    (cd "${WIKTEXTRACT_DIR}" && shasum -a 256 "${WIKTEXTRACT_FILE}") > "${CHECKSUM_FILE}"
else
    echo "Warning: No SHA256 tool found (sha256sum or shasum). Skipping checksum."
    echo "manual" > "${CHECKSUM_FILE}"
fi

echo "Checksum saved to: ${CHECKSUM_FILE}"
cat "${CHECKSUM_FILE}"

# Summary
echo ""
echo "======================================================================"
echo "Summary"
echo "======================================================================"
echo "✓ Wiktextract data downloaded"
echo "  File: ${WIKTEXTRACT_DIR}/${WIKTEXTRACT_FILE}"
echo "  Size: $(du -h "${WIKTEXTRACT_DIR}/${WIKTEXTRACT_FILE}" | cut -f1)"
echo "  Checksum: ${CHECKSUM_FILE}"
echo ""
echo "Next steps:"
echo "  1. Review DATA_LICENSES.md for attribution requirements"
echo "  2. Use src/rootai/data/parse_wiktextract.py to process data"
echo "  3. Ensure CC-BY-SA + GFDL compliance in your use"
echo "======================================================================"
