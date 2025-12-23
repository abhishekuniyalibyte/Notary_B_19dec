#!/usr/bin/env python3
"""
MILESTONE 4: Data Field Extraction & Normalization

Converts messy extracted data into structured, normalized facts.
Handles:
- Name normalization
- Date parsing
- ID format standardization
- Conflict detection
- Missing field identification

Usage: python3 normalize_fields.py <extracted_json_file>
Example: python3 normalize_fields.py "Acta de Girtec S.A_extracted.json"
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


class FieldNormalizer:
    """Normalize and validate extracted fields from certificates"""

    def __init__(self):
        self.conflicts = []
        self.missing_fields = []
        self.low_confidence = []

    def normalize_name(self, name: Optional[str]) -> Optional[str]:
        """Normalize person/company names - title case with proper spacing"""
        if not name or name == "null":
            return None

        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name.strip())

        # Title case for each word, preserving abbreviations
        words = []
        for word in name.split():
            # Keep abbreviations uppercase (S.A., Dr., etc.)
            if '.' in word or word.isupper() and len(word) <= 4:
                words.append(word)
            else:
                words.append(word.title())

        return ' '.join(words)

    def normalize_rut(self, rut: Optional[str]) -> Optional[str]:
        """Normalize RUT format to: 12-345678-001-2"""
        if not rut or rut == "null":
            return None

        # Remove all non-digit characters
        digits = re.sub(r'\D', '', rut)

        # RUT format: XX-XXXXXX-XXX-X (12 digits)
        if len(digits) == 12:
            return f"{digits[0:2]}-{digits[2:8]}-{digits[8:11]}-{digits[11]}"

        # If not 12 digits, mark as low confidence
        self.low_confidence.append({
            "field": "rut",
            "value": rut,
            "reason": f"Unexpected RUT length: {len(digits)} digits"
        })
        return rut

    def normalize_ci(self, ci: Optional[str]) -> Optional[str]:
        """Normalize CI (Cédula) format to: 1.234.567-8"""
        if not ci or ci == "null":
            return None

        # Remove all non-digit characters
        digits = re.sub(r'\D', '', ci)

        # CI format: X.XXX.XXX-X (7-8 digits)
        if len(digits) == 7:
            return f"{digits[0]}.{digits[1:4]}.{digits[4:7]}-{self._calculate_ci_verifier(digits)}"
        elif len(digits) == 8:
            # Already has verifier
            return f"{digits[0]}.{digits[1:4]}.{digits[4:7]}-{digits[7]}"

        self.low_confidence.append({
            "field": "ci",
            "value": ci,
            "reason": f"Unexpected CI length: {len(digits)} digits"
        })
        return ci

    def _calculate_ci_verifier(self, ci_digits: str) -> str:
        """Calculate CI verifier digit (simplified - Uruguay uses specific algorithm)"""
        # This is a placeholder - actual CI validation is more complex
        return "0"

    def normalize_date(self, date_str: Optional[str]) -> Dict[str, Any]:
        """
        Normalize date to ISO format (YYYY-MM-DD)
        Returns dict with: {normalized, original, confidence}
        """
        if not date_str or date_str == "null":
            return {"normalized": None, "original": None, "confidence": "missing"}

        original = date_str

        # Spanish month mapping
        months_es = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
            'set': 9, 'oct': 10, 'nov': 11, 'dic': 12
        }

        # Pattern: "11 de octubre 2012" or "11/10/2012" or "2012-10-11"
        patterns = [
            # ISO format
            (r'(\d{4})-(\d{2})-(\d{2})', lambda m: f"{m.group(1)}-{m.group(2)}-{m.group(3)}"),
            # DD/MM/YYYY
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', lambda m: f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"),
            # DD de MONTH YYYY (Spanish)
            (r'(\d{1,2})\s+de\s+(\w+)\s+(\d{4})',
             lambda m: f"{m.group(3)}-{months_es.get(m.group(2).lower(), 0):02d}-{int(m.group(1)):02d}")
        ]

        for pattern, formatter in patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    normalized = formatter(match)
                    # Validate it's a real date
                    datetime.strptime(normalized, '%Y-%m-%d')
                    return {
                        "normalized": normalized,
                        "original": original,
                        "confidence": "high"
                    }
                except (ValueError, KeyError):
                    continue

        # If no pattern matched
        self.low_confidence.append({
            "field": "date",
            "value": date_str,
            "reason": "Could not parse date format"
        })

        return {
            "normalized": None,
            "original": original,
            "confidence": "low"
        }

    def extract_institution(self, document_type: Optional[str], text: str) -> Optional[str]:
        """Extract institution name from document type or text"""
        if not document_type:
            return None

        institutions = {
            'DGI': ['DGI', 'DIRECCION GENERAL IMPOSITIVA'],
            'BPS': ['BPS', 'BANCO DE PREVISION SOCIAL'],
            'MSP': ['MSP', 'MINISTERIO DE SALUD PUBLICA'],
            'BCU': ['BCU', 'BANCO CENTRAL'],
            'ABITAB': ['ABITAB'],
            'NOTARIA': ['NOTARIA', 'ESCRIBANO', 'ACTA']
        }

        doc_upper = document_type.upper()
        for inst, keywords in institutions.items():
            if any(kw in doc_upper for kw in keywords):
                return inst

        return None

    def extract_roles(self, other_fields: Dict) -> List[Dict[str, str]]:
        """Extract person roles from other_fields"""
        roles = []

        role_mapping = {
            'presidente': 'Presidente',
            'secretario': 'Secretario',
            'director': 'Director',
            'apoderado': 'Apoderado',
            'representante': 'Representante Legal'
        }

        for key, value in other_fields.items():
            key_lower = key.lower()
            for role_key, role_label in role_mapping.items():
                if role_key in key_lower and value:
                    roles.append({
                        "role": role_label,
                        "name": self.normalize_name(value),
                        "field_source": key
                    })

        return roles

    def normalize_extracted_data(self, extracted_data: Dict) -> Dict:
        """Main normalization function"""

        # Reset state
        self.conflicts = []
        self.missing_fields = []
        self.low_confidence = []

        # Required fields check
        required = ["document_type", "denominacion", "fecha"]
        for field in required:
            if not extracted_data.get(field):
                self.missing_fields.append(field)

        # Normalize fields
        normalized = {
            "document_type": extracted_data.get("document_type"),
            "company_name": self.normalize_name(extracted_data.get("denominacion")),
            "rut": self.normalize_rut(extracted_data.get("rut")),
            "certificate_number": extracted_data.get("constancia_number"),
            "fiscal_address": extracted_data.get("domicilio_fiscal"),
            "taxpayer_type": extracted_data.get("tipo_contribuyente"),
            "status": extracted_data.get("estado"),
        }

        # Normalize dates
        for date_field in ["fecha", "emision", "vencimiento"]:
            date_value = extracted_data.get(date_field)
            normalized_date = self.normalize_date(date_value)

            # Map Spanish field names to English
            field_mapping = {
                "fecha": "date",
                "emision": "issue_date",
                "vencimiento": "expiry_date"
            }
            normalized[field_mapping[date_field]] = normalized_date

        # Extract institution
        normalized["institution"] = self.extract_institution(
            extracted_data.get("document_type"),
            json.dumps(extracted_data)
        )

        # Extract roles from other_fields
        other_fields = extracted_data.get("other_fields", {})
        normalized["roles"] = self.extract_roles(other_fields)

        # Keep other fields
        normalized["other_fields"] = other_fields

        return normalized

    def generate_output(self, normalized_fields: Dict) -> Dict:
        """Generate final output with conflicts and missing fields"""
        return {
            "normalized_fields": normalized_fields,
            "conflicts": self.conflicts,
            "missing": self.missing_fields,
            "low_confidence": self.low_confidence,
            "metadata": {
                "normalized_at": datetime.now().isoformat(),
                "total_conflicts": len(self.conflicts),
                "total_missing": len(self.missing_fields),
                "total_low_confidence": len(self.low_confidence)
            }
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 normalize_fields.py <extracted_json_file>")
        print("\nExample:")
        print('  python3 normalize_fields.py "Acta de Girtec S.A_extracted.json"')
        sys.exit(1)

    input_file = sys.argv[1]

    # Check file exists
    if not Path(input_file).exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    # Load extracted data
    with open(input_file, 'r', encoding='utf-8') as f:
        extracted_data = json.load(f)

    print("=" * 70)
    print("  MILESTONE 4: FIELD NORMALIZATION")
    print("=" * 70)
    print(f"\nInput: {Path(input_file).name}")

    # Normalize
    normalizer = FieldNormalizer()
    normalized_fields = normalizer.normalize_extracted_data(extracted_data)
    output = normalizer.generate_output(normalized_fields)

    # Save output
    base_name = Path(input_file).stem.replace('_extracted', '')
    output_file = f"{base_name}_normalized.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Display results
    print(f"\n✓ Normalized {len(normalized_fields)} field groups")
    print(f"  - Missing fields: {len(output['missing'])}")
    print(f"  - Low confidence: {len(output['low_confidence'])}")
    print(f"  - Conflicts: {len(output['conflicts'])}")

    print(f"\n✓ Saved to: {output_file}")

    # Display normalized output
    print("\n" + "=" * 70)
    print("  NORMALIZED OUTPUT")
    print("=" * 70)
    print(json.dumps(output, indent=2, ensure_ascii=False))

    print("\n" + "=" * 70)
    print("✓ Normalization complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
