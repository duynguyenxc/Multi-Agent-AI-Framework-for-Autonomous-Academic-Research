# Phase 1 Evaluation Report
Generated: 2026-06-15T18:22:00

## Headline metrics

| Metric | Value | Target | Pass |
|---|---|---|---|
| CMOCs total | 57 | — | ✓ |
| Unique studies | 28 | — | ✓ |
| Multi-CMOC ratio | 2.036 | > 1.5 | ✓ |
| Negative-CMOC share | 0.368 | > 0.05 | ✓ |
| E-code coverage | 0.681 | >= 0.6 (≥28/47) | ✓ |
| PTS coverage | 1.0 | >= 0.6 (3/5 PTS populated) | ✓ |
| Ontology chain fidelity | 0.439 | >= 0.4 | ✓ |
| Context diversity (Shannon/log2 6) | 0.778 | ≥ 0.5 | ✓ |
| E20 share (laziness) | 0.0 | < 0.4 (down from baseline 0.78) | ✓ |
| E01 share (laziness) | 0.0 | < 0.2 | ✓ |

## PTS distribution
- **PTS1** (20): ████████████████████
- **PTS2** (2): ██
- **PTS3** (12): ████████████
- **PTS4** (20): ████████████████████
- **PTS5** (3): ███
- **N/A** (0): 

## E-codes NOT used in this run
E01, E11, E16, E20, E21, E29, E30, E31, E33, E34, E35, E37, E40, E41, E47

## Top 15 most-used E-codes
- `E19`: 57
- `E27`: 24
- `E02`: 23
- `E45`: 19
- `E05`: 18
- `E14`: 16
- `E36`: 16
- `E46`: 15
- `E18`: 11
- `E10`: 10
- `E25`: 8
- `E22`: 7
- `E04`: 6
- `E26`: 5
- `E38`: 5

## Chain-mismatch examples (CMOCs whose 4-tuple deviates from canonical PTS chain)
- `S002_CMOC1` (study S002, PTS1):
  - MR=E39 not in ['E20', 'E27']
  - O=E46 not in ['E25', 'E29', 'E30']
- `S002_CMOC2` (study S002, PTS2):
  - I=E18 not in ['E10', 'E11']
- `S003_CMOC1` (study S003, PTS5):
  - O=E22 not in ['E29', 'E43', 'E44', 'E46']
- `S004_CMOC1` (study S004, PTS1):
  - O=E46 not in ['E25', 'E29', 'E30']
- `S004_CMOC2` (study S004, PTS1):
  - I=E08 not in ['E07', 'E15', 'E18']
  - MR=E45 not in ['E20', 'E27']
  - O=E36 not in ['E25', 'E29', 'E30']
- `S007_CMOC1` (study S007, PTS1):
  - I=E09 not in ['E07', 'E15', 'E18']
  - O=E46 not in ['E25', 'E29', 'E30']
- `S008_CMOC1` (study S008, PTS1):
  - O=E46 not in ['E25', 'E29', 'E30']
- `S009_CMOC1` (study S009, PTS1):
  - O=E46 not in ['E25', 'E29', 'E30']
- `S010_CMOC1` (study S010, PTS1):
  - O=E46 not in ['E25', 'E29', 'E30']
- `S011_CMOC1` (study S011, PTS3):
  - C=E03 not in ['E04']
  - I=E07 not in ['E09', 'E10', 'E11']
  - O=E44 not in ['E22', 'E28', 'E40', 'E41']
- `S012_CMOC1` (study S012, PTS3):
  - C=E06 not in ['E04']
- `S013_CMOC1` (study S013, PTS4):
  - C=E02 not in ['E05']
