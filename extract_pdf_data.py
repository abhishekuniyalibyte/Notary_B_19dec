#!/usr/bin/env python3
"""
Extract structured data from PDF certificates using Groq (Llama 4 Maverick)
Usage: python3 extract_pdf_data.py /path/to/certificate.pdf
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
            model='meta-llama/llama-4-maverick-17b-128e-instruct',  # Groq's Llama 4 maverick
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
            temperature=0,  # Maximum precision
            max_tokens=4000  # Increased for multi-page documents
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


def save_extracted_data(data: dict, output_path: str):
    """Save extracted data to JSON file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved to: {output_path}")


def main():
     # Load .env file
    load_dotenv()
    if len(sys.argv) < 2:
        print("Usage: python3 extract_pdf_data.py /path/to/certificate.pdf")
        print("\nExample:")
        print('  python3 extract_pdf_data.py "Notaria_client_data/Azili SA/certificate.pdf"')
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
    print("  PDF DATA EXTRACTION - GROQ LLAMA 4")
    print("=" * 70)
    print(f"\nFile: {Path(pdf_path).name}")

    # Step 1: Extract text from PDF
    print("\n[1/3] Extracting text from PDF...")
    result = extract_text_from_pdf(pdf_path)

    if result[0] is None:
        print("✗ Failed to extract text from PDF")
        sys.exit(1)

    pdf_text, page_count = result
    print(f"✓ Extracted {len(pdf_text)} characters from {page_count} page(s)")

    # Step 2: Extract structured data with LLM
    print(f"\n[2/3] Extracting structured data with Groq Llama 4 ({page_count} pages)...")
    extracted_data = extract_data_with_llm(pdf_text, api_key, page_count)

    if not extracted_data:
        print("✗ Failed to extract data with LLM")
        sys.exit(1)

    print("✓ Data extracted successfully")

    # Step 3: Save to JSON
    print("\n[3/3] Saving extracted data...")
    output_path = Path(pdf_path).stem + "_extracted.json"
    save_extracted_data(extracted_data, output_path)

    # Display extracted data
    print("\n" + "=" * 70)
    print("  EXTRACTED DATA")
    print("=" * 70)
    print(json.dumps(extracted_data, indent=2, ensure_ascii=False))

    print("\n" + "=" * 70)
    print("✓ Extraction complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
