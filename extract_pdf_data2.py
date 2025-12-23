#!/usr/bin/env python3
"""
Extract structured data from PDF certificates using Groq (Llama 4 Maverick)
Fully compliant with Uruguayan Notarial Law Articles 248-255

Generates 2 output files:
  1. *_extracted.json - Raw extracted data from the PDF
  2. *_validation.json - Legal validation format (Articles 248-255 compliant)

Usage: python3 extract_pdf_data2.py /path/to/certificate.pdf
"""

import os
from dotenv import load_dotenv
import sys
import json
from pathlib import Path
import pdfplumber
from groq import Groq
from pdf2image import convert_from_path
import pytesseract
from PIL import Image


def extract_text_with_ocr(pdf_path: str) -> tuple:
    """Extract text from scanned PDF using OCR
    Returns: (text, page_count)
    """
    try:
        print("  - PDF appears to be scanned/image-based, using OCR...")

        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=300)
        page_count = len(images)

        text = ""
        for i, image in enumerate(images, 1):
            print(f"  - OCR processing page {i}/{page_count}...")
            # Use Tesseract OCR with Spanish language support
            page_text = pytesseract.image_to_string(image, lang='spa+eng')
            if page_text.strip():
                text += f"\n--- PAGE {i} ---\n{page_text}\n"
                print(f"  - Extracted page {i}/{page_count} ({len(page_text.strip())} chars)")
            else:
                print(f"  - Warning: Page {i} OCR returned no text")

        return text.strip(), page_count
    except Exception as e:
        print(f"Error with OCR extraction: {e}")
        print("Note: Ensure tesseract-ocr is installed: sudo apt-get install tesseract-ocr tesseract-ocr-spa poppler-utils")
        return None, 0


def extract_text_from_pdf(pdf_path: str) -> tuple:
    """Extract text from PDF using pdfplumber, fallback to OCR if needed
    Returns: (text, page_count)
    """
    try:
        # First, try standard text extraction
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            page_count = len(pdf.pages)
            print(f"  - Total pages: {page_count}")

            for i, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- PAGE {i} ---\n{page_text}\n"
                    print(f"  - Extracted page {i}/{page_count} ({len(page_text)} chars)")
                else:
                    print(f"  - Warning: Page {i} has no extractable text")

        # If no text was extracted, use OCR
        if not text.strip():
            print("\n  - No text found with standard extraction")
            return extract_text_with_ocr(pdf_path)

        return text.strip(), page_count
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None, 0


def extract_data_with_llm(pdf_text: str, api_key: str, page_count: int) -> dict:
    """Extract structured data using Groq Llama 4"""
    try:
        client = Groq(api_key=api_key)

        prompt = f"""Extract ALL data from this Uruguayan certificate EXACTLY as written.
This document has {page_count} page(s). Extract information from ALL pages.
Do not translate, do not modify. Preserve exact spelling, accents, capitalization, and punctuation.

Certificate text:
{pdf_text}

Return ONLY valid JSON with these fields (use null if field not found):
{{
  "document_type": "Type of certificate (e.g., DGI, BPS, MSP)",
  "rut": "RUT number if present",
  "denominacion": "Company/person name exactly as written",
  "constancia_number": "Certificate/constancia number",
  "fecha": "Date (preserve format)",
  "domicilio_fiscal": "Fiscal address exactly as written",
  "tipo_contribuyente": "Type of taxpayer",
  "estado": "Status/state",
  "emision": "Emission/issue date",
  "vencimiento": "Expiration date",
  "other_fields": {{}}
}}

Extract EVERY field you see across ALL {page_count} page(s). If there are additional fields not listed, add them to "other_fields".
Return ONLY the JSON, no explanations."""

        print(f"  - Sending {len(pdf_text)} characters to LLM...")

        response = client.chat.completions.create(
            model='meta-llama/llama-4-maverick-17b-128e-instruct',
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise data extraction assistant. Extract data EXACTLY as written from ALL pages, preserving all Spanish characters, accents, and formatting. Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_tokens=4000
        )

        result_text = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
            result_text = result_text.strip()

        # Parse JSON response
        extracted_data = json.loads(result_text)
        return extracted_data

    except Exception as e:
        print(f"Error with Groq API: {e}")
        return None


def validate_certificate_legal_requirements(pdf_text: str, api_key: str, page_count: int) -> dict:
    """Validate certificate requirements according to Articles 248-255 of Uruguayan Notarial Law

    Returns simplified format for Track A:
    - certificate_type
    - facts (True/False for each requirement)
    - conditions (True/False for special conditions)
    - global_fields (True/False for Article 255 fields)
    """
    try:
        client = Groq(api_key=api_key)

        prompt = f"""Analyze this Uruguayan notarial document according to Articles 248-255 of the Notarial Law.

Document text ({page_count} page(s)):
{pdf_text}

Determine the certificate type and validate ALL legal requirements.

LEGAL FRAMEWORK (Articles 248-255):
- Article 248: Certificate types (a: certificado_hechos, b: certificado_firmas, c: certificado_ratificacion)
- Article 249: Requirements for certificado_hechos
- Article 250: Requirements for certificado_firmas
- Article 251: Requirements for certificado_ratificacion
- Article 252: Conditional requirements (witnesses if otorgante can't sign)
- Article 253: Requerimiento expreso requirement
- Article 254: Witness rules (Article 145 cross-reference)
- Article 255: Global fields required in all certificates

Return ONLY valid JSON in this EXACT format:

{{
  "certificate_type": "type (certificado_hechos, certificado_firmas, certificado_ratificacion, acta_asamblea, poder, escritura, etc.)",

  "facts": {{
    "individualizacion_otorgantes": true or false,
    "identificacion_otorgantes": true or false,
    "identificacion_documento_vigente": true or false,
    "lectura_del_documento": true or false,
    "firma_en_presencia": true or false,
    "requerimiento_expreso": true or false,
    "objeto_del_certificado": true or false,
    "documento_fuente": true or false,
    "exhibicion_o_compulsa": true or false,
    "conocimiento_personal_escribano": true or false,
    "ratificacion_contenido_y_firma": true or false,
    "suscripcion_y_autorizacion": true or false,
    "existencia_persona_juridica": true or false,
    "estatuto_vigente": true or false,
    "designacion_autoridades": true or false,
    "cargo_vigente": true or false,
    "facultades_representacion_validas": true or false,
    "cumplimiento_ley_17904": true or false,
    "cumplimiento_ley_18930": true or false,
    "beneficiario_final_declarado": true or false,
    "documentacion_verificada_por_escribano": true or false,
    "testigos_idoneos_articulo_145": true or false
  }},

  "conditions": {{
    "otorgante_no_sabe_o_no_puede_firmar": true or false,
    "testigos_instrumentales_presentes": true or false,
    "impresion_digital_realizada": true or false,
    "documento_tiene_tachaduras": true or false,
    "requiere_traduccion": true or false
  }},

  "global_fields": {{
    "nombre_solicitante": true or false,
    "constancia_cumplimiento_legal": true or false,
    "destinatario": true or false,
    "lugar_expedicion": true or false,
    "fecha_expedicion": true or false,
    "firma_y_sello_escribano": true or false
  }}
}}

VALIDATION RULES:
- Mark as true if requirement is present/met/mentioned in the document
- Mark as false if requirement is missing/not met
- Consider the certificate type when evaluating which requirements apply
- certificado_firmas requires: individualizacion, identificacion, lectura, firma_en_presencia, requerimiento_expreso
- certificado_hechos requires: objeto_del_certificado, documento_fuente, exhibicion_o_compulsa
- certificado_ratificacion requires: individualizacion, identificacion, ratificacion_contenido_y_firma, suscripcion_y_autorizacion
- All certificates require Article 255 global_fields
- Conditional requirements (testigos) only apply if otorgante cannot sign

Return ONLY the JSON object, no explanations."""

        print(f"  - Validating legal requirements (Articles 248-255)...")

        response = client.chat.completions.create(
            model='meta-llama/llama-4-maverick-17b-128e-instruct',
            messages=[
                {
                    "role": "system",
                    "content": "You are a legal document validator specialized in Uruguayan Notarial Law (Articles 248-255). Return validation results as simple true/false values in JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_tokens=2500
        )

        result_text = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
            result_text = result_text.strip()

        # Parse JSON response
        validation_data = json.loads(result_text)
        return validation_data

    except Exception as e:
        print(f"Error with validation: {e}")
        return None


def save_extracted_data(data: dict, output_path: str):
    """Save extracted data to JSON file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved to: {output_path}")


def main():
    # Load .env file
    load_dotenv()
    if len(sys.argv) < 2:
        print("Usage: python3 extract_pdf_data2.py /path/to/certificate.pdf")
        print("\nExample:")
        print('  python3 extract_pdf_data2.py "Notaria_client_data/Azili SA/certificate.pdf"')
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Check file exists
    if not Path(pdf_path).exists():
        print(f"✗ File not found: {pdf_path}")
        sys.exit(1)

    # Get API key from .env
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY environment variable not set")
        print("\nSet it with:")
        print('  export GROQ_API_KEY="your-key-here"')
        sys.exit(1)

    print("=" * 70)
    print("  PDF DATA EXTRACTION - ARTICLES 248-255 COMPLIANT")
    print("=" * 70)
    print(f"\nFile: {Path(pdf_path).name}")

    # Step 1: Extract text from PDF
    print("\n[1/4] Extracting text from PDF...")
    result = extract_text_from_pdf(pdf_path)

    if result[0] is None:
        print("✗ Failed to extract text from PDF")
        sys.exit(1)

    pdf_text, page_count = result
    print(f"✓ Extracted {len(pdf_text)} characters from {page_count} page(s)")

    # Step 2: Extract structured data with LLM
    print(f"\n[2/4] Extracting structured data with Groq Llama 4 ({page_count} pages)...")
    extracted_data = extract_data_with_llm(pdf_text, api_key, page_count)

    if not extracted_data:
        print("✗ Failed to extract data with LLM")
        sys.exit(1)

    print("✓ Data extracted successfully")

    # Step 3: Validate certificate requirements (Articles 248-255)
    print(f"\n[3/4] Validating legal requirements (Articles 248-255)...")
    validation_data = validate_certificate_legal_requirements(pdf_text, api_key, page_count)

    if not validation_data:
        print("✗ Failed to validate requirements")
        sys.exit(1)

    print("✓ Legal validation completed successfully")

    # Step 4: Save both outputs
    print("\n[4/4] Saving outputs...")
    base_name = Path(pdf_path).stem

    # Save raw extracted data
    raw_output_path = base_name + "_extracted.json"
    save_extracted_data(extracted_data, raw_output_path)

    # Save validation data (Articles 248-255 compliant)
    validation_output_path = base_name + "_validation_legal.json"
    save_extracted_data(validation_data, validation_output_path)

    # Display summary
    print("\n" + "=" * 70)
    print("  VALIDATION SUMMARY")
    print("=" * 70)

    print(f"Certificate Type: {validation_data.get('certificate_type', 'N/A')}")

    if "facts" in validation_data:
        facts = validation_data["facts"]
        facts_met = sum(1 for v in facts.values() if v is True)
        facts_total = len(facts)
        print(f"Facts Met: {facts_met}/{facts_total}")

    if "global_fields" in validation_data:
        fields = validation_data["global_fields"]
        fields_met = sum(1 for v in fields.values() if v is True)
        fields_total = len(fields)
        print(f"Global Fields (Art. 255): {fields_met}/{fields_total}")

    if "conditions" in validation_data:
        conditions = validation_data["conditions"]
        if conditions.get("otorgante_no_sabe_o_no_puede_firmar"):
            print("⚠ Special Condition: Otorgante cannot sign")
            if conditions.get("testigos_instrumentales_presentes"):
                print("  ✓ Witnesses present")
            else:
                print("  ✗ Witnesses required but not present")

    print("\n" + "=" * 70)
    print("✓ Extraction complete!")
    print(f"✓ Generated 2 files:")
    print(f"  1. {raw_output_path} (raw data)")
    print(f"  2. {validation_output_path} (Track A format - Articles 248-255)")
    print("=" * 70)


if __name__ == '__main__':
    main()
