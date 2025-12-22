# File Structure & Architecture

Complete reference for all files in the Track B project.

---

## Table of Contents

- [Milestone 1 Files](#milestone-1-files)
- [Milestone 2 Files](#milestone-2-files)
- [Configuration Files](#configuration-files)
- [Documentation Files](#documentation-files)
- [Data Flow Architecture](#data-flow-architecture)
- [Directory Structure](#directory-structure)

---

## Milestone 1 Files

### `models.py`
**Purpose:** Data models and schemas for the entire system

**What it does:**
- Defines the `Customer` model (person or company entity)
- Defines the `CertificateRecord` model (individual certificate with metadata)
- Defines the `CustomerRegistry` model (complete registry of all customers and certificates)
- Provides data validation using Pydantic
- Establishes the fundamental data structures used throughout the system
- **Milestone 2:** Extended with Drive metadata fields (`drive_folder_id`, `drive_file_id`, `mime_type`, `file_size`)

**Key classes:**
- `CustomerType` - Enum for PERSON or COMPANY
- `CertificateStatus` - Enum for OK, ERROR, or UNKNOWN
- `Customer` - Represents one customer with folder path and optional Drive folder ID
- `CertificateRecord` - Represents one certificate with all metadata including Drive info
- `CustomerRegistry` - Container for all customers and certificates

---

### `folder_scanner.py`
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

### `storage.py`
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

### `certificate_tracker.py`
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

### `main.py`
**Purpose:** Command-line interface (CLI) entry point

**What it does:**
- Provides a user-friendly command-line interface to interact with the system
- Executes folder scanning operations (Milestone 1)
- **Milestone 2:** Google Drive operations (auth, list, download)
- Displays statistics and reports
- Shows customer details
- Searches certificates
- Lists all customers

**Milestone 1 Commands:**
- `--scan <path>` - Scan local customer folders
- `--stats` - Show detailed statistics
- `--list` - List all customers
- `--customer <name>` - Show customer details
- `--search <term>` - Search certificates

**Milestone 2 Commands:**
- `--drive-auth` - Authenticate with Google Drive
- `--drive-list` - List folders in Drive
- `--drive-download` - Download all customer folders
- `--drive-download --folder-id <id>` - Download specific folder
- `--drive-scan` - Scan locally downloaded files
- `--metadata-stats` - Show file metadata statistics

**Key functions:**
- Milestone 1:
  - `scan_customers()` - Initiates folder scan and saves results
  - `show_statistics()` - Displays comprehensive stats
  - `show_customer_details()` - Shows detailed customer info
  - `list_customers()` - Lists all customers with certificate counts
- Milestone 2:
  - `drive_authenticate()` - Google Drive OAuth authentication
  - `drive_list_folders()` - List folders in Drive
  - `drive_download()` - Download customer folders from Drive
  - `drive_scan_local()` - Scan locally downloaded files
  - `show_metadata_stats()` - Display file metadata statistics

---

## Milestone 2 Files

### `drive_auth.py`
**Purpose:** Google Drive OAuth 2.0 authentication

**What it does:**
- Manages OAuth flow for Google Drive API
- Stores and refreshes authentication tokens automatically
- Tests Drive connection
- Handles credentials securely with read-only access

**Key class:**
- `DriveAuthenticator` - Handles all authentication logic

**Methods:**
- `authenticate()` - Run OAuth flow or load existing token
- `get_drive_service()` - Get authenticated Drive API service
- `test_connection()` - Verify Drive API access
- `revoke_credentials()` - Delete token and reset

**Files:**
- `credentials.json` - OAuth client credentials (user provides)
- `token.pickle` - Stored authentication token (auto-generated)

---

### `drive_manager.py`
**Purpose:** Google Drive file operations

**What it does:**
- Lists folders in Google Drive
- Lists files within folders (recursive support)
- Downloads files with progress tracking
- Filters supported file types (PDF, DOCX, images)
- Tracks download statistics per customer

**Key class:**
- `DriveManager` - Handles all Drive file operations

**Methods:**
- `list_folders()` - List all folders in Drive
- `list_files_in_folder()` - Get all files in a folder (recursive)
- `is_supported_file()` - Check if file type is supported
- `download_file()` - Download single file from Drive
- `download_customer_folder()` - Download entire customer folder
- `download_all_customer_folders()` - Batch download all customers
- `search_folder_by_name()` - Find folder by name
- `get_folder_structure()` - Display folder tree

**Supported file types:**
- PDF documents
- DOCX/DOC files
- JPG/PNG/TIFF images
- Text files

---

### `file_detector.py`
**Purpose:** File type detection and validation

**What it does:**
- Detects file types using python-magic (content-based)
- Falls back to extension-based detection
- Validates supported file types
- Provides comprehensive file information

**Key class:**
- `FileDetector` - Intelligent file type detection

**Methods:**
- `detect_from_content()` - Use magic library for content detection
- `detect_from_extension()` - Use file extension for detection
- `detect_file_type()` - Best available detection method
- `is_document()` - Check if file is a document type
- `is_image()` - Check if file is an image
- `requires_ocr()` - Check if OCR processing needed
- `get_file_info()` - Complete file information
- `scan_directory()` - Scan and categorize all files

**FileType enum:**
- PDF, DOCX, DOC, IMAGE_JPG, IMAGE_PNG, IMAGE_TIFF, TEXT, UNKNOWN

---

### `metadata_indexer.py`
**Purpose:** File metadata storage and indexing

**What it does:**
- Indexes all downloaded files with metadata
- Stores Drive IDs, file sizes, modification dates
- Generates statistics and reports
- Bridges Drive downloads with certificate registry

**Key classes:**
- `FileMetadata` - Represents metadata for a single file
- `MetadataIndex` - Maintains file metadata database

**Methods:**
- `add_file()` - Add file metadata to index
- `index_downloaded_files()` - Index local files
- `index_from_drive_stats()` - Index from Drive download stats
- `save()` - Save index to JSON
- `load()` - Load index from JSON
- `get_customer_files()` - Get all files for a customer
- `get_files_by_type()` - Filter files by type
- `get_statistics()` - Generate statistics
- `export_report()` - Export detailed report

**Output:**
- `data/file_metadata_index.json` - Complete metadata index

---

### `drive_integration.py`
**Purpose:** Integrates Drive with customer registry

**What it does:**
- Orchestrates authentication, download, and indexing
- Creates customer registry from Drive files
- Detects customer types (person vs company)
- Creates certificate records from downloaded files
- Adds Drive metadata to existing models

**Key class:**
- `DriveIntegration` - Main integration orchestrator

**Methods:**
- `authenticate()` - Authenticate with Drive
- `download_and_index()` - Complete download and indexing workflow
- `download_specific_folder()` - Download one customer folder
- `scan_local_downloads()` - Re-index local files
- `list_drive_folders()` - List available folders

**Workflow:**
1. Authenticate with Google Drive
2. List and download customer folders
3. Index file metadata
4. Create customer registry
5. Save registry and metadata

---

## Configuration Files

### `requirements.txt`
**Purpose:** Python dependencies for all milestones

**Milestone 1 Dependencies:**
```
pydantic>=2.0.0
pydantic-settings>=2.0.0
```

**Milestone 2 Dependencies:**
```
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.1.1
google-api-python-client>=2.100.0
python-magic>=0.4.27  # Optional but recommended
```

**Usage:**
```bash
pip install -r requirements.txt
```

---

### `.gitignore`
**Purpose:** Specifies files to exclude from version control

**Contents:**
```
Notaria_client_data      # Customer data folder
venv                      # Python virtual environment
credentials.json          # Google OAuth credentials (M2)
token.pickle              # Authentication token (M2)
downloaded_files/         # Downloaded Drive files (M2)
data/                     # Generated data and backups
*.pyc                     # Python bytecode
__pycache__/              # Python cache
```

**Why:**
- Prevents sensitive credentials from being committed
- Excludes customer data (privacy)
- Keeps repository clean

---

## Documentation Files

### `README.md`
Main project documentation with:
- Project overview
- Milestone progress tracker
- Quick start guide
- Command reference
- Links to detailed docs

### `README_MILESTONE1.md`
Detailed guide for Milestone 1:
- Complete installation instructions
- Usage examples for all CLI commands
- Explanation of data models
- Key features description
- Technical notes and best practices

### `README_MILESTONE2.md`
Detailed guide for Milestone 2:
- Google Drive API setup instructions
- OAuth authentication walkthrough
- File download workflows
- File type detection details
- Metadata indexing explanation
- Troubleshooting guide
- Security and privacy notes

### `FILE_STRUCTURE.md` (this file)
Complete file reference:
- Detailed descriptions of all files
- Architecture documentation
- Data flow diagrams
- Directory structure

### `workflow_track_B2.md`
9-milestone implementation roadmap:
- Detailed tasks for each milestone
- Tools and libraries for each milestone
- Dependency mapping
- Execution order
- Difficulty assessment
- Track A integration strategy

### `track_B_detail.txt`
Track B scope definition:
- Clear definition of what Track B is and isn't
- Track B responsibilities
- Track A/B boundary (Track B does NOT interpret law)
- Input/output specifications
- Technology stack
- Mental model: "I am the notary's document assistant"

### `client_requirements.txt`
Original client specifications:
- Client's pain points and goals
- Complete workflow description
- Integration requirements (Google Drive, OAuth)
- Legal knowledge base requirements
- Template and style learning specifications
- Institution-specific requirements
- Example use cases

---

## Data Flow Architecture

### Milestone 1 Flow (Local Folders)
```
┌─────────────────────┐
│ Local Customer      │
│ Folders             │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ FolderScanner       │
│ - Scan folders      │
│ - Detect types      │
│ - Index files       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ CustomerRegistry    │
│ - Customers         │
│ - Certificates      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ StorageManager      │
│ - Save JSON         │
│ - Create backups    │
│ - Export reports    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ CertificateTracker  │
│ - Query data        │
│ - Analyze           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ main.py CLI         │
│ - Display results   │
└─────────────────────┘
```

### Milestone 2 Flow (Google Drive)
```
┌─────────────────────┐
│ Google Drive        │
│ Customer Folders    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ DriveAuthenticator  │
│ - OAuth 2.0         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ DriveManager        │
│ - List folders      │
│ - Download files    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ FileDetector        │
│ - Detect types      │
│ - Validate          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ MetadataIndexer     │
│ - Index metadata    │
│ - Store Drive IDs   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ DriveIntegration    │
│ - Orchestrate       │
│ - Create registry   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ CustomerRegistry    │
│ + Drive metadata    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ StorageManager      │
│ - Save all data     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ main.py CLI         │
│ - Display results   │
└─────────────────────┘
```

---

## Directory Structure

```
Notary_19dec/
│
├── Python Files (Milestone 1)
│   ├── models.py                    # Data schemas
│   ├── folder_scanner.py            # Local folder scanning
│   ├── storage.py                   # JSON persistence
│   ├── certificate_tracker.py       # Data analysis
│   └── main.py                      # CLI interface
│
├── Python Files (Milestone 2)
│   ├── drive_auth.py                # OAuth authentication
│   ├── drive_manager.py             # Drive operations
│   ├── file_detector.py             # File type detection
│   ├── metadata_indexer.py          # Metadata storage
│   └── drive_integration.py         # Integration orchestrator
│
├── Configuration
│   ├── requirements.txt             # Python dependencies
│   └── .gitignore                   # Git exclusions
│
├── Documentation
│   ├── README.md                    # Main project docs
│   ├── README_MILESTONE1.md         # M1 detailed guide
│   ├── README_MILESTONE2.md         # M2 detailed guide
│   ├── FILE_STRUCTURE.md            # This file
│   ├── workflow_track_B2.md         # Implementation roadmap
│   ├── track_B_detail.txt           # Track B scope
│   └── client_requirements.txt      # Original specs
│
├── Generated Data (not in Git)
│   └── data/
│       ├── customer_registry.json   # Main database
│       ├── customer_report.json     # Readable report
│       ├── file_metadata_index.json # File metadata (M2)
│       └── backups/                 # Auto backups
│           └── registry_backup_*.json
│
├── Downloaded Files (not in Git)
│   └── downloaded_files/            # Drive downloads (M2)
│       ├── Customer1/
│       ├── Customer2/
│       └── ...
│
└── OAuth Credentials (not in Git)
    ├── credentials.json             # OAuth client ID (M2)
    └── token.pickle                 # Auth token (M2)
```

---

## Architecture Principles

1. **Clean separation:** Track B handles documents, Track A handles law
2. **No legal interpretation:** Track B never decides legal validity
3. **Data-driven:** All decisions based on extracted data and Track A output
4. **Incremental learning:** System improves from notary feedback
5. **Spanish-first:** All text processing optimized for Spanish
6. **Notary-centric:** System adapts to each notary's style
7. **Modular design:** Each milestone builds on previous ones
8. **Testable:** Clear interfaces between components

---

## Development Guidelines

### Adding New Features
1. Update relevant models in `models.py` if schema changes needed
2. Implement feature in appropriate module
3. Add CLI command in `main.py` if user-facing
4. Update milestone README
5. Add tests (future milestone)

### Code Organization
- **models.py** - All data structures
- **{feature}_*.py** - Feature-specific modules
- **main.py** - CLI only, no business logic
- **storage.py** - All file I/O

### Naming Conventions
- **Classes:** PascalCase (e.g., `CustomerRegistry`)
- **Functions:** snake_case (e.g., `scan_customers`)
- **Files:** snake_case (e.g., `folder_scanner.py`)
- **CLI args:** kebab-case (e.g., `--drive-auth`)

---

**Last Updated:** Milestone 2 Complete
**Next:** Milestone 3 - Document Text Extraction
