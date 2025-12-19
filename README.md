# Track B - Notarial Certificate Generation System

**Version:** Milestone 1 Complete
**Language:** python3.11 (Python 3.11.14)
**Purpose:** Document intelligence and certificate generation for Uruguayan notaries

---

## Project Overview

This system helps Uruguayan notaries automate the creation of notarial certificates by reading customer documents, extracting data, validating legal requirements, and generating properly formatted certificates in Spanish.

**Track B** is the operational layer that handles:
- Document reading and OCR
- Data extraction and normalization
- Certificate template learning
- Certificate draft generation
- Integration with legal validation (Track A)

---

## Current Status: Milestone 1

**Completed:** Project foundation with customer and certificate indexing

**Next:** Milestone 2 (Google Drive integration) and Milestone 3 (document text extraction)

---

## File Structure & Purpose

### Core Python Files

#### `models.py`
**Purpose:** Data models and schemas for the entire system

**What it does:**
- Defines the `Customer` model (person or company entity)
- Defines the `CertificateRecord` model (individual certificate with metadata)
- Defines the `CustomerRegistry` model (complete registry of all customers and certificates)
- Provides data validation using Pydantic
- Establishes the fundamental data structures used throughout the system

**Key classes:**
- `CustomerType` - Enum for PERSON or COMPANY
- `CertificateStatus` - Enum for OK, ERROR, or UNKNOWN
- `Customer` - Represents one customer with folder path
- `CertificateRecord` - Represents one certificate with all metadata
- `CustomerRegistry` - Container for all customers and certificates

---

#### `folder_scanner.py`
**Purpose:** Scans customer folders and indexes certificates

**What it does:**
- Scans a directory where each subfolder represents one customer
- Automatically detects if customer is a person or company (based on keywords and name structure)
- Recursively searches folders for certificate files (PDF, DOCX, etc.)
- Identifies ERROR-prefixed certificates (marked by notary as problematic)
- Extracts institution names from filenames (BPS, MSP, Abitab, DGI, etc.)
- Parses dates from filenames in various formats (YYYY-MM-DD, DD-MM-YYYY, YYYYMMDD)
- Generates unique IDs for customers and certificates
- Creates a complete `CustomerRegistry` with all indexed data

**Key class:**
- `FolderScanner` - Main scanner that processes folder structure and creates the registry

**Methods:**
- `scan_all_customers()` - Scans entire base directory and returns full registry
- `scan_customer_folder()` - Scans one customer's folder for certificates
- `get_summary()` - Generates summary statistics

---

#### `storage.py`
**Purpose:** Handles data persistence using JSON files

**What it does:**
- Saves the customer registry to JSON files
- Loads existing registry from disk
- Creates automatic backups before overwriting data
- Exports human-readable reports
- Generates detailed statistics about customers and certificates

**Key class:**
- `StorageManager` - Manages all file I/O operations

**Methods:**
- `save_registry()` - Saves registry to JSON (with optional backup)
- `load_registry()` - Loads registry from JSON file
- `export_customer_report()` - Creates readable report with customer details
- `get_statistics()` - Generates comprehensive statistics

**Output files:**
- `data/customer_registry.json` - Main database file
- `data/customer_report.json` - Human-readable report
- `data/backups/` - Timestamped backup files

---

#### `certificate_tracker.py`
**Purpose:** Provides tools to query and analyze certificate history

**What it does:**
- Searches for customers by name or ID
- Retrieves complete certificate history for any customer
- Filters certificates by institution, status, or date
- Generates customer summaries with statistics
- Analyzes certificate timelines (oldest, newest, frequency)
- Identifies potential duplicate certificates
- Creates institution-level analytics (error rates, customer counts)
- Generates comprehensive error reports
- Provides search functionality across all certificates

**Key class:**
- `CertificateTracker` - Query and analysis engine for certificate data

**Methods:**
- `get_customer_by_name()` - Find customer by name (partial match)
- `get_certificate_history()` - Get all certificates for a customer
- `get_error_history()` - Get ERROR certificates only
- `get_certificates_by_institution()` - Filter by institution (BPS, MSP, etc.)
- `get_customer_summary()` - Detailed customer statistics
- `get_institution_analysis()` - Institution-level analytics
- `get_timeline_analysis()` - Certificate creation timeline
- `search_certificates()` - Search by filename
- `get_error_report()` - Comprehensive error analysis

---

#### `main.py`
**Purpose:** Command-line interface (CLI) entry point

**What it does:**
- Provides a user-friendly command-line interface to interact with the system
- Executes folder scanning operations
- Displays statistics and reports
- Shows customer details
- Searches certificates
- Lists all customers

**Usage:**
```bash
# Scan customer folders
python main.py --scan /path/to/customer/folders

# View statistics
python main.py --stats

# List all customers
python main.py --list

# Show customer details
python main.py --customer "customer_name"

# Search certificates
python main.py --search "keyword"
```

**Key functions:**
- `scan_customers()` - Initiates folder scan and saves results
- `show_statistics()` - Displays comprehensive stats
- `show_customer_details()` - Shows detailed customer info
- `list_customers()` - Lists all customers with certificate counts
- `main()` - Argument parser and command dispatcher

---

### Configuration Files

#### `requirements.txt`
**Purpose:** Python dependencies

**Contents:**
```
pydantic>=2.0.0
pydantic-settings>=2.0.0
```

**What it does:**
- Specifies required Python packages
- Used by `pip install -r requirements.txt`

---

#### `.gitignore`
**Purpose:** Specifies files to exclude from version control

**Contents:**
```
Notaria_client_data
venv
```

**What it does:**
- Prevents customer data from being committed to Git
- Excludes Python virtual environment from repository

---

### Documentation Files

#### `README_MILESTONE1.md`
**Purpose:** Detailed guide for Milestone 1

**What it contains:**
- Complete installation instructions
- Usage examples for all CLI commands
- Explanation of data models
- Key features description
- Technical notes and best practices
- Next steps for Milestone 2 and 3

---

#### `client_requirements.txt`
**Purpose:** Original client requirements and specifications

**What it contains:**
- Client's pain points and goals
- Complete workflow description
- Integration requirements (Google Drive, OAuth)
- Legal knowledge base requirements
- Template and style learning specifications
- Institution-specific requirements
- Example use cases

---

#### `track_B_detail.txt`
**Purpose:** Track B scope definition

**What it contains:**
- Clear definition of what Track B is and isn't
- Track B responsibilities
- Track A/B boundary (Track B does NOT interpret law)
- Input/output specifications
- Technology stack
- Mental model: "I am the notary's document assistant"

---

#### `workflow_track_B2.md`
**Purpose:** Complete milestone-by-milestone implementation plan

**What it contains:**
- 9 milestones with detailed tasks
- Tools and libraries for each milestone
- Dependency mapping
- Execution order
- Difficulty assessment
- Track A integration strategy

**Milestones:**
1. ✅ Project base & folder model (COMPLETE)
2. Google Drive & file ingestion
3. Document text extraction (OCR + parsing)
4. Data field extraction & normalization
5. Template discovery & style learning
6. Certificate draft generation
7. Track A integration
8. Feedback loop & improvement
9. Final export & delivery

---

## Data Flow

```
Customer Folders
      ↓
[FolderScanner] → scans folders, detects customer type, finds certificates
      ↓
[CustomerRegistry] → structured data with customers + certificates
      ↓
[StorageManager] → saves to JSON, creates backups, exports reports
      ↓
[CertificateTracker] → queries, filters, analyzes certificate data
      ↓
[main.py CLI] → displays results to user
```

---

## Installation

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # OR
   venv\Scripts\activate     # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation:**
   ```bash
   python main.py --help
   ```

---

## Quick Start

1. **Scan your customer folders:**
   ```bash
   python main.py --scan /path/to/customer/folders
   ```

2. **View statistics:**
   ```bash
   python main.py --stats
   ```

3. **Explore a specific customer:**
   ```bash
   python main.py --customer "EMARLAN"
   ```

---

## What Each Component Does - Summary

| File | Purpose | Key Responsibility |
|------|---------|-------------------|
| `models.py` | Data schemas | Defines structure of customers and certificates |
| `folder_scanner.py` | Folder indexing | Scans folders, detects types, indexes certificates |
| `storage.py` | Data persistence | Saves/loads JSON, creates backups, exports reports |
| `certificate_tracker.py` | Data analysis | Queries, filters, analyzes certificate history |
| `main.py` | User interface | CLI commands for all operations |
| `requirements.txt` | Dependencies | Lists required Python packages |
| `.gitignore` | Version control | Excludes customer data and venv from Git |
| `README_MILESTONE1.md` | User guide | Detailed documentation for Milestone 1 |
| `client_requirements.txt` | Specifications | Original client requirements |
| `track_B_detail.txt` | Scope definition | Track B boundaries and responsibilities |
| `workflow_track_B2.md` | Implementation plan | 9-milestone roadmap with tasks |

---

## Key Features (Milestone 1)

✅ **Automatic customer type detection** - Distinguishes persons from companies
✅ **ERROR certificate tracking** - Flags problematic certificates
✅ **Institution recognition** - Extracts BPS, MSP, Abitab, etc.
✅ **Date extraction** - Parses dates from filenames
✅ **Certificate history** - Complete tracking per customer
✅ **Statistics & analytics** - Error rates, institution analysis, timelines
✅ **Search functionality** - Find certificates across all customers
✅ **JSON storage** - Lightweight persistence with backups
✅ **CLI interface** - Easy-to-use command-line tools

---

## Generated Data Structure

After running `--scan`, the system creates:

```
data/
├── customer_registry.json      # Main database
├── customer_report.json        # Human-readable report
└── backups/
    └── registry_backup_YYYYMMDD_HHMMSS.json
```

---

## Next Milestones

**Milestone 2:** Google Drive integration
- OAuth authentication
- File download from Drive
- Metadata extraction

**Milestone 3:** Document text extraction
- PDF text extraction (pdfplumber)
- DOCX text extraction (python-docx)
- OCR for scanned documents (Tesseract)
- Spanish text corpus building

**Milestone 4:** Data field extraction
- Entity recognition (names, IDs, dates)
- Field normalization
- Conflict resolution

**Milestone 5+:** Template learning, certificate generation, Track A integration

---

## Architecture Principles

1. **Clean separation:** Track B handles documents, Track A handles law
2. **No legal interpretation:** Track B never decides legal validity
3. **Data-driven:** All decisions based on extracted data and Track A output
4. **Incremental learning:** System improves from notary feedback
5. **Spanish-first:** All text processing optimized for Spanish
6. **Notary-centric:** System adapts to each notary's style

---

## Development Notes

- **Python 3.10+** required
- **Pydantic** for data validation
- **JSON** for lightweight storage (can upgrade to SQLite later)
- **No AI inference** in Milestone 1 (just folder scanning and indexing)
- **Milestone 2+** will add OCR, NLP, and template generation

---

## Support & Documentation

For detailed usage examples and troubleshooting, see [README_MILESTONE1.md](README_MILESTONE1.md)

For implementation roadmap, see [workflow_track_B2.md](workflow_track_B2.md)

For project scope, see [track_B_detail.txt](track_B_detail.txt)

---

## License & Usage

This system is designed for Uruguayan notaries to automate certificate generation in compliance with Uruguayan notarial law (Organic Law and Notarial Regulations).

---

**Track B - Milestone 1 Complete**

*Next: Milestone 2 - Google Drive Integration*
