#!/usr/bin/env python3
"""
PDF DATA EXTRACTION ONLY
LLM is used ONLY for structured extraction, NEVER for legal decisions.

Output:
  - *_extracted.json  (Track B output)
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

import pdfplumber
from groq import Groq
from pdf2image import convert_from_path
import pytesseract


# ---------------------------------------------------------
# TEXT EXTRACTION
# ---------------------------------------------------------

def extract_text_with_ocr(pdf_path: str) -> tuple[str, int]:
    images = convert_from_path(pdf_path, dpi=300)
    text = ""

    for i, image in enumerate(images, 1):
        page_text = pytesseract.image_to_string(image, lang="spa+eng")
        if page_text.strip():
            text += f"\n--- PAGE {i} ---\n{page_text}"

    return text.strip(), len(images)


def extract_text_from_pdf(pdf_path: str) -> tuple[str, int]:
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for i, page in enumerate(pdf.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- PAGE {i} ---\n{page_text}"

    if not text.strip():
        return extract_text_with_ocr(pdf_path)

    return text.strip(), len(pdf.pages)


# ---------------------------------------------------------
# LLM EXTRACTION (NO LEGAL JUDGMENT)
# ---------------------------------------------------------

def extract_data_with_llm(pdf_text: str, api_key: str, page_count: int) -> dict:
    client = Groq(api_key=api_key)

    prompt = f"""
Extract ALL data from this Uruguayan notarial document EXACTLY as written.
Do NOT interpret law. Do NOT decide compliance. Do NOT infer truth.

Document has {page_count} pages.

Return ONLY valid JSON in this format:

{{
  "document_type": null,
  "rut": null,
  "denominacion": null,
  "constancia_number": null,
  "fecha": null,
  "domicilio_fiscal": null,
  "tipo_contribuyente": null,
  "estado": null,
  "emision": null,
  "vencimiento": null,
  "other_fields": {{}}
}}

Put any extra fields you find inside "other_fields".
Use null if missing.
Preserve Spanish exactly.
Return JSON ONLY.

DOCUMENT TEXT:
{pdf_text}
"""

    response = client.chat.completions.create(
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        messages=[
            {"role": "system", "content": "You extract text, not law."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=4000
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("```"):
        content = content.split("```")[1].replace("json", "").strip()

    return json.loads(content)


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: python extract_pdf_data.py <file.pdf>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Missing GROQ_API_KEY in .env")
        sys.exit(1)

    print("\n[1/2] Extracting text...")
    pdf_text, page_count = extract_text_from_pdf(str(pdf_path))

    print("\n[2/2] Extracting structured data (LLM)...")
    extracted_data = extract_data_with_llm(pdf_text, api_key, page_count)

    output_file = pdf_path.stem + "_extracted.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Extraction complete → {output_file}")


if __name__ == "__main__":
    main()
