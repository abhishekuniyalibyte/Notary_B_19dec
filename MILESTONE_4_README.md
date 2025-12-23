# Milestone 4: Data Field Extraction & Normalization

**Goal:** Convert messy extracted text data into structured, normalized facts.

## What This Does

Takes the raw extracted JSON from Milestone 3 (LLM extraction) and:
- Normalizes names (proper capitalization, spacing)
- Standardizes date formats (Spanish → ISO format)
- Formats RUT and CI (cédula) numbers
- Extracts person roles (Presidente, Secretario, etc.)
- Identifies institution type
- Detects conflicts, missing fields, and low-confidence data

## Files Created

- **[normalize_fields.py](normalize_fields.py)** - Main normalization script

## Usage

```bash
python3 normalize_fields.py <extracted_json_file>
```

### Example

```bash
python3 normalize_fields.py "Acta de Girtec S.A_extracted.json"
```

### Output

Creates: `<document_name>_normalized.json`

## Output Format

```json
{
  "normalized_fields": {
    "document_type": "ACTA DE ASAMBLEA GENERAL EXTRAORDINARIA",
    "company_name": "Girtec S.A.",
    "rut": null,
    "date": {
      "normalized": "2012-10-11",
      "original": "11 de octubre 2012",
      "confidence": "high"
    },
    "institution": "NOTARIA",
    "roles": [
      {
        "role": "Presidente",
        "name": "Eduardo Victor Bomio Claveria"
      }
    ]
  },
  "conflicts": [],
  "missing": [],
  "low_confidence": [],
  "metadata": {
    "normalized_at": "2025-12-23T12:14:06.407996",
    "total_conflicts": 0,
    "total_missing": 0,
    "total_low_confidence": 0
  }
}
```

## Features

### 1. Name Normalization
- Title case for names
- Preserves abbreviations (S.A., Dr., etc.)
- Removes extra whitespace

### 2. Date Parsing
- Handles Spanish dates: "11 de octubre 2012"
- Handles numeric dates: "11/10/2012"
- Converts to ISO format: "2012-10-11"
- Tracks confidence level

### 3. ID Normalization
- **RUT format:** `12-345678-001-2`
- **CI format:** `1.234.567-8`

### 4. Role Extraction
Automatically identifies roles from fields:
- Presidente
- Secretario
- Director
- Apoderado
- Representante Legal

### 5. Institution Detection
Identifies document source:
- DGI
- BPS
- MSP
- BCU
- ABITAB
- NOTARIA

### 6. Quality Tracking
- **Conflicts:** Inconsistent data
- **Missing:** Required fields not found
- **Low confidence:** Unparseable or suspicious values

## Dependencies

**None!** Uses only Python standard library:
- `re` (regex)
- `datetime` (date parsing)
- `json` (data handling)

## Integration

This normalized output is:
1. **Exactly what Track A validates legally** (legal requirements check)
2. **Input for Milestone 5** (template generation)

## Workflow

```
Milestone 3 Output → Milestone 4 → Milestone 5 Input
_extracted.json   →  normalize  →  _normalized.json
```

## Notes

- Spanish language support built-in
- Uruguayan document formats (RUT, CI)
- Extensible for more field types
- Simple conflict detection for future ML improvements
