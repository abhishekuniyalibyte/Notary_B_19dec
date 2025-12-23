from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import pdfplumber
from groq import Groq
from pdf2image import convert_from_path
import pytesseract
import json
import tempfile

load_dotenv()

app = FastAPI(title="PDF Data Extraction API")

def extract_text_with_ocr(pdf_path: str) -> tuple:
    try:
        images = convert_from_path(pdf_path, dpi=300)
        page_count = len(images)
        text = ""
        for i, image in enumerate(images, 1):
            page_text = pytesseract.image_to_string(image, lang='spa+eng')
            if page_text.strip():
                text += f"\n--- PAGE {i} ---\n{page_text}\n"
        return text.strip(), page_count
    except Exception as e:
        return None, 0

def extract_text_from_pdf(pdf_path: str) -> tuple:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            page_count = len(pdf.pages)
            for i, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- PAGE {i} ---\n{page_text}\n"
        if not text.strip():
            return extract_text_with_ocr(pdf_path)
        return text.strip(), page_count
    except Exception as e:
        return None, 0

def extract_data_with_llm(pdf_text: str, api_key: str, page_count: int) -> dict:
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

        response = client.chat.completions.create(
            model='meta-llama/llama-4-maverick-17b-128e-instruct',
            messages=[
                {"role": "system", "content": "You are a precise data extraction assistant. Extract data EXACTLY as written from ALL pages, preserving all Spanish characters, accents, and formatting. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=4000
        )
        result_text = response.choices[0].message.content.strip()
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
            result_text = result_text.strip()
        return json.loads(result_text)
    except Exception as e:
        return None

def validate_certificate_requirements(pdf_text: str, api_key: str, page_count: int) -> dict:
    try:
        client = Groq(api_key=api_key)
        prompt = f"""Analyze this Uruguayan notarial document and validate which legal requirements are met.

Document text ({page_count} page(s)):
{pdf_text}

Determine the certificate type and mark each requirement as true (present/met) or false (missing/not met).

Return ONLY valid JSON in this EXACT format:
{{
  "certificate_type": "certificate type (certificado_firmas, acta_asamblea, poder, escritura, certificado_personeria, etc.)",
  "facts": {{
    "individualizacion_otorgantes": true or false,
    "identificacion_otorgantes": true or false,
    "firma_en_presencia": true or false,
    "lectura_del_documento": true or false,
    "existencia_persona_juridica": true or false,
    "estatuto_vigente": true or false,
    "designacion_autoridades": true or false,
    "cargo_vigente": true or false,
    "facultades_representacion_validas": true or false,
    "cumplimiento_ley_17904": true or false,
    "cumplimiento_ley_18930": true or false,
    "beneficiario_final_declarado": true or false,
    "requerimiento_expreso": true or false,
    "documentacion_verificada_por_escribano": true or false
  }},
  "conditions": {{
    "otorgante_no_sabe_o_no_puede_firmar": true or false,
    "documento_tiene_tachaduras": true or false,
    "requiere_traduccion": true or false
  }},
  "global_fields": {{
    "nombre_solicitante": true or false,
    "destinatario": true or false,
    "lugar_expedicion": true or false,
    "fecha_expedicion": true or false,
    "firma_y_sello_escribano": true or false,
    "constancia_cumplimiento_legal": true or false
  }}
}}

Mark each field as true if the requirement is present/mentioned/met in the document, false if missing or not met.
Return ONLY the JSON object, no explanations or comments."""

        response = client.chat.completions.create(
            model='meta-llama/llama-4-maverick-17b-128e-instruct',
            messages=[
                {"role": "system", "content": "You are a legal document validator for Uruguayan notarial certificates. Analyze documents and return validation results in JSON format only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=2000
        )
        result_text = response.choices[0].message.content.strip()
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
            result_text = result_text.strip()
        return json.loads(result_text)
    except Exception as e:
        return None

@app.get("/")
def read_root():
    return {"message": "PDF Data Extraction API", "endpoints": ["/extract"]}

@app.post("/extract")
async def extract_pdf(file: UploadFile = File(...)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        pdf_text, page_count = extract_text_from_pdf(tmp_path)
        if pdf_text is None:
            raise HTTPException(status_code=500, detail="Failed to extract text from PDF")

        extracted_data = extract_data_with_llm(pdf_text, api_key, page_count)
        if not extracted_data:
            raise HTTPException(status_code=500, detail="Failed to extract data with LLM")

        validation_data = validate_certificate_requirements(pdf_text, api_key, page_count)
        if not validation_data:
            raise HTTPException(status_code=500, detail="Failed to validate requirements")

        return JSONResponse(content={
            "filename": file.filename,
            "pages": page_count,
            "extracted_data": extracted_data,
            "validation_data": validation_data
        })

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
