#!/bin/bash
# Install OCR dependencies for extract_pdf_data.py

echo "Installing system packages for OCR..."
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-spa poppler-utils

echo ""
echo "Installing Python packages..."
pip install pdf2image pytesseract Pillow

echo ""
echo "Verifying installation..."
tesseract --version
echo ""
echo "✓ OCR dependencies installed successfully!"
echo ""
echo "You can now run: python3 extract_pdf_data.py 'path/to/scanned.pdf'"
