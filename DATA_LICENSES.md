# Data Licenses & Attribution

This document describes the licenses and attribution requirements for external data sources used by RootAI.

## Summary

RootAI can integrate with several open lexical resources. Each has specific license requirements that **you must comply with** when using the data:

| Resource | License | Attribution Required | Share-Alike |
|----------|---------|---------------------|-------------|
| OEWN (Open English WordNet) | CC-BY 4.0 | ✓ Yes | No |
| OMW (Open Multilingual WordNet) | CC-BY / CC-BY-SA | ✓ Yes | Varies |
| OMW-Arabic (Arabic WordNet) | CC-BY / CC-BY-SA | ✓ Yes | Varies |
| Princeton WordNet | WordNet License | ✓ Yes | No |
| Wiktextract (kaikki.org) | CC-BY-SA 3.0 + GFDL | ✓ Yes | ✓ Yes |
| Wikipedia/Wiktionary dumps | CC-BY-SA 3.0 + GFDL | ✓ Yes | ✓ Yes |
| CAMeL Tools | MIT | ✓ Yes | No |
| CAMeL Tools datasets | Varies | ✓ Check each | Varies |

**⚠️ IMPORTANT**: 
- Wiktionary-derived data (Wiktextract) requires **share-alike** (CC-BY-SA 3.0)
- You must attribute all sources appropriately
- Some datasets may have additional restrictions

---

## 1. Open English WordNet (OEWN)

### License
- **CC-BY 4.0** (Creative Commons Attribution 4.0 International)
- https://creativecommons.org/licenses/by/4.0/

### Source
- Homepage: https://en-word.net/
- Repository: https://github.com/globalwordnet/english-wordnet
- License file: https://github.com/globalwordnet/english-wordnet/blob/main/LICENSE.md

### Attribution Requirements
When using OEWN data, you must:
1. **Give appropriate credit** to:
   - "Open English WordNet" as the source
   - Princeton University WordNet (original source)
2. **Provide a link** to the license (CC-BY 4.0)
3. **Indicate if changes were made**

### Recommended Attribution
```
This work uses data from Open English WordNet (https://en-word.net/),
which is based on Princeton University WordNet and licensed under CC-BY 4.0.
```

### No Share-Alike Requirement
CC-BY 4.0 does NOT require you to share your derivatives under the same license.

---

## 2. Open Multilingual WordNet (OMW)

### License
- **Open license** (freely used, modified, and shared)
- Individual wordnets may have specific licenses (mostly CC-BY or CC-BY-SA)

### Source
- Homepage: https://omwn.org/
- OMW 2.0 interface: https://compling.upol.cz/omw/omw
- OMW on GitHub: https://github.com/omwn

### Attribution Requirements
When using OMW data:
1. **Attribute the specific wordnets** you use (e.g., "Arabic WordNet")
2. **Check the license** for each language-specific wordnet
3. **Provide appropriate credit** as specified by each wordnet

### Arabic WordNet (OMW-Arabic)
- **Source**: Available via OMW interface
- **License**: CC-BY or CC-BY-SA (check specific version)
- **Attribution**: "Arabic WordNet via Open Multilingual WordNet"

### Recommended Attribution
```
This work uses data from Open Multilingual WordNet (https://omwn.org/),
including [specific wordnets]. Individual wordnets may have additional
license requirements - see https://compling.upol.cz/omw/omw for details.
```

---

## 3. Princeton WordNet

### License
- **WordNet License** (permissive, similar to BSD/MIT)
- https://wordnet.princeton.edu/license-and-commercial-use

### Source
- Homepage: https://wordnet.princeton.edu/
- Copyright: Trustees of Princeton University

### License Summary
The WordNet license allows:
- ✓ Free use for research and commercial purposes
- ✓ Modification and redistribution
- ✓ Incorporation into larger works

Requirements:
- **Retain copyright notice** in source files
- **Acknowledge** use of WordNet in publications

### Recommended Attribution
```
This work uses Princeton University WordNet®.
WordNet® is a registered trademark of Princeton University.
See https://wordnet.princeton.edu/ for more information.
```

---

## 4. Wiktextract & Wiktionary Data

### License
- **CC-BY-SA 3.0** (Creative Commons Attribution-ShareAlike 3.0)
- **GFDL** (GNU Free Documentation License)
- Dual-licensed: must comply with at least one

### Source
- Wiktextract tool: https://github.com/tatuylonen/wiktextract
- Kaikki.org raw data: https://kaikki.org/dictionary/rawdata.html
- Wikimedia dumps: https://dumps.wikimedia.org/
- License guide: https://en.wikipedia.org/wiki/Wikipedia:Database_download

### Attribution Requirements (CC-BY-SA 3.0)
When using Wiktionary-derived data, you **MUST**:
1. **Give appropriate credit**:
   - Attribute to "Wiktionary contributors"
   - Include a link to the source (e.g., https://en.wiktionary.org/)
2. **Provide a link to the license** (CC-BY-SA 3.0)
3. **Indicate if changes were made**
4. **Share derivatives under CC-BY-SA 3.0** or compatible license

### Share-Alike Requirement
⚠️ **CRITICAL**: CC-BY-SA 3.0 requires **share-alike**:
- Any derivative work must be shared under CC-BY-SA 3.0 or compatible
- This applies if you modify, transform, or build upon the data
- Mere aggregation with other works does not trigger share-alike

### Recommended Attribution
```
This work uses data derived from Wiktionary (https://en.wiktionary.org/),
which is made available under the Creative Commons Attribution-ShareAlike 3.0
License (https://creativecommons.org/licenses/by-sa/3.0/). The original data
was processed using Wiktextract (https://github.com/tatuylonen/wiktextract)
and obtained from kaikki.org (https://kaikki.org/dictionary/rawdata.html).
```

### GFDL Alternative
If you choose to comply with GFDL instead of CC-BY-SA:
- Full license text: https://www.gnu.org/licenses/fdl-1.3.html
- GFDL is more complex and typically CC-BY-SA is preferred

---

## 5. CAMeL Tools & Datasets

### CAMeL Tools License
- **MIT License**
- https://github.com/CAMeL-Lab/camel_tools/blob/master/LICENSE

### Source
- Repository: https://github.com/CAMeL-Lab/camel_tools
- Developed by: CAMeL Lab, New York University Abu Dhabi

### License Summary (MIT)
The MIT license allows:
- ✓ Free use for any purpose
- ✓ Modification and redistribution
- ✓ Commercial use

Requirements:
- **Include the copyright notice** and license text
- **No warranty** is provided

### CAMeL Tools Datasets
CAMeL Tools provides a dataset installer (`camel_data`):
```bash
# Install light datasets
camel_data -i light

# Install full datasets
camel_data -i all
```

**⚠️ WARNING**: Individual datasets may have **different licenses**:
- Check the license for each dataset before use
- Some datasets may be research-only
- Some may have attribution requirements

### Buckwalter Morphological Analyzer (LDC)
**⚠️ NOT INCLUDED / NOT REDISTRIBUTABLE**:
- Buckwalter analyzer data is from the Linguistic Data Consortium (LDC)
- **LDC data is NOT freely redistributable**
- Users must obtain their own LDC license
- Do NOT include Buckwalter data in redistributable packages

### Recommended Attribution (CAMeL Tools)
```
This work uses CAMeL Tools (https://github.com/CAMeL-Lab/camel_tools),
developed by the CAMeL Lab at New York University Abu Dhabi,
licensed under the MIT License.
```

---

## 6. RootAI Output Data Licensing

When RootAI processes external data, the license obligations carry forward:

### If Using Wiktionary/Wiktextract Data
- **Your outputs must be CC-BY-SA 3.0 or compatible**
- You must attribute Wiktionary contributors
- Include source attribution in metadata

### If Using OEWN/OMW Data
- **CC-BY 4.0 attribution required**
- No share-alike obligation
- More permissive than Wiktionary

### RootAI-Generated Content
- Content generated by RootAI's models (not derived from external data):
  - Not subject to external licenses
  - Your own terms apply
- However, if the generation was **grounded in** external data, attribution may still be required

---

## How to Comply

### 1. Track Your Data Sources
When building indexes or processing dictionaries, RootAI creates `PROVENANCE.md` files that record:
- Source URLs
- SHA256 checksums
- Processing dates
- License information

**Keep these files** and include them when redistributing data.

### 2. Include Attributions
When publishing:
- **Papers/Publications**: Cite the data sources in your references
- **Software/APIs**: Include attribution in documentation and/or UI
- **Datasets**: Include `LICENSE.txt` and `ATTRIBUTIONS.md` files

### 3. Comply with Share-Alike
If using Wiktionary data:
- License your derivative dataset under CC-BY-SA 3.0
- Include full license text
- Clearly mark any modifications

### 4. Don't Redistribute Restricted Data
- **Never redistribute** LDC Buckwalter data
- Check dataset-specific terms before redistribution

---

## Example Attribution File

Create an `ATTRIBUTIONS.md` file for your project:

```markdown
# Data Attributions

This project uses the following external data sources:

## Open English WordNet
- Source: https://en-word.net/
- License: CC-BY 4.0
- Attribution: Open English WordNet, based on Princeton WordNet

## Wiktionary (via Wiktextract)
- Source: https://kaikki.org/dictionary/rawdata.html
- License: CC-BY-SA 3.0 + GFDL
- Attribution: Wiktionary contributors (https://en.wiktionary.org/)
- Note: Derivatives shared under CC-BY-SA 3.0

## CAMeL Tools
- Source: https://github.com/CAMeL-Lab/camel_tools
- License: MIT
- Attribution: CAMeL Lab, NYU Abu Dhabi

[Add other sources as needed]
```

---

## Questions?

If you have questions about licensing:

1. **Check the original source** for authoritative guidance
2. **Consult a legal professional** for commercial/critical applications
3. **Open an issue** on the RootAI repository for clarification

## License References

- CC-BY 4.0: https://creativecommons.org/licenses/by/4.0/
- CC-BY-SA 3.0: https://creativecommons.org/licenses/by-sa/3.0/
- GFDL: https://www.gnu.org/licenses/fdl-1.3.html
- MIT: https://opensource.org/licenses/MIT
- WordNet License: https://wordnet.princeton.edu/license-and-commercial-use

---

**Last Updated**: 2026-01-01  
**RootAI Version**: 3.0.1
