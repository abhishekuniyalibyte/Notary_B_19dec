# Track B - Milestone 1: Project Base & Folder Model

**Status:** ✅ Complete
**Goal:** Establish a predictable structure for customer data and certificates.

---

## What This Milestone Delivers

This milestone provides the **foundation** for Track B by implementing:

1. **Customer-to-folder mapping** - Each folder represents one customer (person or company)
2. **Customer identity abstraction** - Automatic detection of person vs company
3. **Certificate history indexing** - Complete tracking of all certificates per customer
4. **Storage layer** - JSON-based persistence with backup support
5. **Analysis tools** - Statistics, reports, and customer insights

---

## Project Structure

```
Notary_19dec/
├── models.py                    # Data models (Customer, Certificate, Registry)
├── folder_scanner.py            # Scans folders and indexes certificates
├── storage.py                   # JSON persistence layer
├── certificate_tracker.py       # Certificate history analysis tools
├── main.py                      # CLI entry point
├── requirements.txt             # Python dependencies
├── data/                        # Generated data directory
│   ├── customer_registry.json  # Main registry database
│   ├── customer_report.json    # Human-readable report
│   └── backups/                # Automatic backups
└── README_MILESTONE1.md        # This file
```

---

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify installation:**
   ```bash
   python main.py --help
   ```

---

## Usage Guide

### 1. Scan Customer Folders

Scan a directory containing customer folders (each folder = one customer):

```bash
python main.py --scan /path/to/customer/folders
```

**What this does:**
- Scans each subfolder as a customer
- Detects if customer is a person or company
- Indexes all certificates (PDF, DOCX, etc.)
- Identifies ERROR-prefixed certificates
- Extracts institution names (BPS, MSP, etc.)
- Saves registry to `data/customer_registry.json`

**Example output:**
```
=======================================================================
  SCANNING CUSTOMER FOLDERS
=======================================================================

Scanning: /path/to/customer/folders

--- Scan Summary ---
Total Customers: 25
  - Persons: 18
  - Companies: 7
Total Certificates: 143
Error Certificates: 12

✓ Registry saved to: data/customer_registry.json
✓ Report exported to: data/customer_report.json
```

---

### 2. View Statistics

Display comprehensive statistics about all customers and certificates:

```bash
python main.py --stats
```

**Shows:**
- Customer type breakdown (person vs company)
- Certificates by institution (BPS, MSP, Abitab, etc.)
- Certificate status distribution (OK vs ERROR)
- Top customers by certificate count
- Institution-level analysis (error rates, customer counts)
- Error report (which customers have the most errors)

---

### 3. List All Customers

```bash
python main.py --list
```

**Example output:**
```
=======================================================================
  ALL CUSTOMERS
=======================================================================

Total: 25 customers

  👤 Juan Pérez (5 certificates)
  🏢 EMARLAN SOCIEDAD ANÓNIMA (23 certificates)
  👤 María González (8 certificates)
  ...
```

---

### 4. View Customer Details

Get detailed information about a specific customer:

```bash
python main.py --customer "EMARLAN"
```

**Shows:**
- Basic customer information
- Total certificates and error count
- Certificates grouped by institution
- Recent certificates (last 5)
- Timeline analysis (oldest/newest, time span)
- List of all ERROR certificates

**Example output:**
```
=======================================================================
  CUSTOMER DETAILS: EMARLAN SOCIEDAD ANÓNIMA
=======================================================================

--- Basic Information ---
  Name: EMARLAN SOCIEDAD ANÓNIMA
  Type: COMPANY
  ID: a3f4b8c2d1e5
  Folder: /path/to/EMARLAN SOCIEDAD ANÓNIMA

--- Certificate Summary ---
  Total Certificates: 23
  Error Certificates: 2
  Error Rate: 8.7%

  By Institution:
    BPS: 12
    MSP: 6
    Abitab: 5

--- Recent Certificates ---
  ✓ 2024-11-15 [BPS] certificado_personeria_bps_2024.pdf
  ❌ 2024-10-20 [MSP] ERROR_certificado_vigencia_msp.pdf
  ✓ 2024-09-05 [Abitab] certificado_firma_abitab.docx
  ...
```

---

### 5. Search Certificates

Search for certificates across all customers:

```bash
python main.py --search "BPS"
```

**Example output:**
```
=======================================================================
  SEARCH RESULTS: 'BPS'
=======================================================================

Found 34 certificates

  ✓ EMARLAN SOCIEDAD ANÓNIMA / [BPS] certificado_bps_2024.pdf
  ❌ Juan Pérez / [BPS] ERROR_certificado_bps_expired.pdf
  ✓ María González / [BPS] constancia_bps_vigencia.docx
  ...
```

---

## Data Models

### Customer
```python
{
    "customer_id": "a3f4b8c2d1e5",
    "name": "EMARLAN SOCIEDAD ANÓNIMA",
    "customer_type": "COMPANY",  # or "PERSON"
    "folder_path": "/path/to/folder",
    "created_at": "2024-12-19T10:30:00"
}
```

### CertificateRecord
```python
{
    "certificate_id": "c7e9d2f1a4b3",
    "customer_id": "a3f4b8c2d1e5",
    "certificate_type": null,  # To be extracted in Milestone 4
    "institution": "BPS",
    "date": "2024-11-15T00:00:00",
    "status": "OK",  # or "ERROR"
    "source_files": ["/path/to/certificate.pdf"],
    "filename": "certificado_bps_2024.pdf",
    "file_path": "/full/path/to/certificate.pdf",
    "has_error_prefix": false,
    "indexed_at": "2024-12-19T10:30:00"
}
```

---

## Key Features

### 1. Automatic Customer Type Detection
The scanner automatically detects whether a customer is a **person** or **company** based on:
- Company keywords (sociedad, anónima, s.a., ltda, etc.)
- Name structure (companies typically have longer names)

### 2. ERROR Certificate Detection
Certificates with filenames starting with "ERROR" are automatically flagged:
- `ERROR_certificado_bps.pdf` → marked as ERROR
- Helps identify problematic certificates the notary has flagged

### 3. Institution Recognition
Automatically extracts institution names from filenames:
- BPS (Banco de Previsión Social)
- MSP (Ministerio de Salud Pública)
- Abitab
- DGI (Dirección General Impositiva)
- And more...

### 4. Date Extraction
Attempts to extract dates from filenames in various formats:
- `2024-11-15` (ISO format)
- `15-11-2024` (DD-MM-YYYY)
- `20241115` (compact format)

### 5. Storage & Backups
- Main registry saved as JSON
- Automatic backups created when updating
- Human-readable reports exported

---

## Intelligence Gathered

This milestone allows you to **understand the client's data reality**:

✅ How many customers exist
✅ How many certificates per customer
✅ Which customers have the most errors
✅ Which institutions appear most frequently
✅ Certificate volume trends over time
✅ Customer type distribution (person vs company)

---

## Next Steps

**Milestone 2** will add:
- Google Drive integration
- OAuth authentication
- File download and metadata extraction

**Milestone 3** will add:
- PDF text extraction
- DOCX text extraction
- OCR for scanned documents
- Spanish text corpus building

---

## Technical Notes

### Dependencies
- **pydantic** - Data validation and schema management
- Python 3.10+ recommended

### File Types Recognized
- `.pdf` - PDF documents
- `.docx` - Word documents
- `.doc` - Legacy Word documents
- `.txt` - Text files

### Certificate Keywords (Spanish)
The scanner looks for these keywords to identify certificates:
- certificado
- certifica
- constancia
- personería
- firma
- vigencia
- poderes

---

## Testing with Sample Data

If you have customer folders ready:

1. **Scan them:**
   ```bash
   python main.py --scan /path/to/customers
   ```

2. **Check statistics:**
   ```bash
   python main.py --stats
   ```

3. **Explore a customer:**
   ```bash
   python main.py --customer "customer_name"
   ```

---

## Output Files

After running `--scan`, you'll have:

1. **`data/customer_registry.json`** - Complete registry (used by the system)
2. **`data/customer_report.json`** - Human-readable report with full details
3. **`data/backups/`** - Timestamped backups of previous registries

---

## Milestone 1 Complete ✅

You now have:
- ✅ Customer-to-folder mapping
- ✅ Certificate history indexing
- ✅ Customer type detection (person vs company)
- ✅ ERROR certificate tracking
- ✅ Institution recognition
- ✅ Storage and backup system
- ✅ Analysis and reporting tools

**Ready for Milestone 2:** Google Drive integration and file ingestion.
