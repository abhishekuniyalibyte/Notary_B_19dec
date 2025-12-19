# Track B - Milestone 2: Google Drive & File Ingestion

**Status:** ✅ Complete
**Goal:** Reliably read PDFs, DOCXs, and images from Google Drive.

---

## What This Milestone Delivers

Milestone 2 extends the foundation by adding:

1. **Google Drive OAuth authentication** - Secure read-only access to Drive
2. **File downloading** - Fetch customer folders and files from Drive
3. **File type detection** - Identify PDFs, DOCX, images using MIME types
4. **Metadata indexing** - Store file metadata (size, dates, Drive IDs)
5. **Drive integration** - Seamlessly connect Drive downloads with customer registry

---

## New Files Added

### Core Modules

#### `drive_auth.py`
**Purpose:** Google Drive OAuth 2.0 authentication

**What it does:**
- Manages OAuth flow for Google Drive API
- Stores and refreshes authentication tokens
- Tests Drive connection
- Handles credentials securely

**Key class:**
- `DriveAuthenticator` - Handles all authentication logic

**Usage:**
```python
from drive_auth import setup_drive_auth

auth = setup_drive_auth()  # Opens browser for OAuth
service = auth.get_drive_service()
```

---

#### `drive_manager.py`
**Purpose:** Google Drive file operations

**What it does:**
- Lists folders in Google Drive
- Lists files within folders (recursive)
- Downloads files with progress tracking
- Filters supported file types (PDF, DOCX, images)
- Tracks download statistics

**Key class:**
- `DriveManager` - Handles all Drive file operations

**Methods:**
- `list_folders()` - List folders in Drive
- `list_files_in_folder()` - Get all files in a folder
- `download_file()` - Download single file
- `download_customer_folder()` - Download entire customer folder
- `download_all_customer_folders()` - Download all customers
- `get_folder_structure()` - Display folder tree

---

#### `file_detector.py`
**Purpose:** File type detection and validation

**What it does:**
- Detects file types using python-magic (content-based)
- Falls back to extension-based detection
- Validates supported file types
- Provides file information (size, MIME type)

**Key class:**
- `FileDetector` - Intelligent file type detection

**Supported types:**
- PDF documents
- DOCX/DOC files
- JPG/PNG/TIFF images
- Text files

---

#### `metadata_indexer.py`
**Purpose:** File metadata storage and indexing

**What it does:**
- Indexes all downloaded files with metadata
- Stores Drive IDs, file sizes, dates
- Generates statistics and reports
- Bridges Drive downloads with certificate registry

**Key class:**
- `MetadataIndex` - Maintains file metadata database

**Output:**
- `data/file_metadata_index.json` - Complete metadata index

---

#### `drive_integration.py`
**Purpose:** Integrates Drive with customer registry

**What it does:**
- Orchestrates authentication, download, and indexing
- Creates customer registry from Drive files
- Detects customer types (person vs company)
- Creates certificate records from downloaded files
- Adds Drive metadata to models

**Key class:**
- `DriveIntegration` - Main integration orchestrator

---

## Updated Files

### `models.py`
**Changes:**
- Added `drive_folder_id` to `Customer` model
- Added `drive_file_id`, `mime_type`, `file_size` to `CertificateRecord` model

### `main.py`
**New commands:**
- `--drive-auth` - Authenticate with Google Drive
- `--drive-list` - List folders in Drive
- `--drive-download` - Download customer folders
- `--drive-scan` - Scan locally downloaded files
- `--metadata-stats` - Show file metadata statistics

### `requirements.txt`
**New dependencies:**
- `google-auth` - Google authentication
- `google-auth-oauthlib` - OAuth flow
- `google-auth-httplib2` - HTTP support
- `google-api-python-client` - Drive API client
- `python-magic` - File type detection (optional)

---

## Installation

### 1. Install Dependencies

```bash
# Activate your virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install Python packages
pip install -r requirements.txt

# Install libmagic (for python-magic)
# Linux:
sudo apt-get install libmagic1

# macOS:
brew install libmagic

# Windows:
pip install python-magic-bin
```

### 2. Set Up Google Drive API

1. **Go to Google Cloud Console:**
   - Visit: https://console.cloud.google.com/

2. **Create a Project:**
   - Click "New Project"
   - Name it (e.g., "Notary Certificate System")

3. **Enable Google Drive API:**
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

4. **Create OAuth Credentials:**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: "Desktop app"
   - Name it (e.g., "Notary Desktop Client")
   - Download the JSON file

5. **Save Credentials:**
   - Rename the downloaded file to `credentials.json`
   - Place it in your project root directory: `/home/abhishek/Documents/Notary_19dec/credentials.json`

---

## Usage Guide

### Step 1: Authenticate with Google Drive

```bash
python main.py --drive-auth
```

**What happens:**
1. Opens browser for Google OAuth login
2. You grant read-only Drive access
3. Creates `token.pickle` file (stores authentication)
4. Tests connection to verify success

**First time only.** Token is saved for future use.

---

### Step 2: List Available Folders

```bash
python main.py --drive-list
```

**Output:**
```
======================================================================
  GOOGLE DRIVE FOLDERS
======================================================================

Found 5 folders:

  📁 Customer_Documents
     ID: 1a2b3c4d5e6f7g8h9i0j
     Modified: 2024-12-15T10:30:00

  📁 EMARLAN SOCIEDAD ANÓNIMA
     ID: 9i8h7g6f5e4d3c2b1a0
     Modified: 2024-12-10T14:20:00
  ...
```

---

### Step 3: Download Customer Folders

#### Option A: Download All Customer Folders

```bash
python main.py --drive-download
```

**What happens:**
1. Scans all folders in your Drive
2. Downloads each folder as a customer
3. Filters for supported file types (PDF, DOCX, images)
4. Indexes file metadata
5. Creates customer registry
6. Saves everything to `data/`

**Output directories:**
- `downloaded_files/` - All downloaded customer files
- `data/customer_registry.json` - Customer and certificate registry
- `data/file_metadata_index.json` - File metadata index
- `data/customer_report_drive.json` - Human-readable report

---

#### Option B: Download Specific Folder

```bash
python main.py --drive-download --folder-id 1a2b3c4d5e6f7g8h9i0j
```

Downloads only the specified folder.

---

### Step 4: View Statistics

#### Customer Statistics
```bash
python main.py --stats
```

Shows the same statistics as Milestone 1, but for Drive-downloaded files.

---

#### File Metadata Statistics
```bash
python main.py --metadata-stats
```

**Shows:**
- Total files indexed
- Files by type (PDF, DOCX, images)
- Total size in MB
- Per-customer file counts

---

### Step 5: Scan Local Downloads (Re-index)

If you already downloaded files and want to re-scan without re-downloading:

```bash
python main.py --drive-scan
```

Useful for:
- Re-indexing after manual file additions
- Recovering from errors
- Testing without hitting Drive API limits

---

## Workflow Example

**Complete workflow from authentication to analysis:**

```bash
# 1. Authenticate (first time only)
python main.py --drive-auth

# 2. See what's in your Drive
python main.py --drive-list

# 3. Download all customer folders
python main.py --drive-download

# 4. View customer statistics
python main.py --stats

# 5. Check file metadata
python main.py --metadata-stats

# 6. View specific customer
python main.py --customer "EMARLAN"

# 7. Search for certificates
python main.py --search "BPS"
```

---

## File Type Detection

The system detects and supports these file types:

| File Type | Extensions | MIME Type | Processing |
|-----------|-----------|-----------|------------|
| PDF | .pdf | application/pdf | ✓ Supported |
| DOCX | .docx | application/vnd.openxmlformats-officedocument.wordprocessingml.document | ✓ Supported |
| DOC | .doc | application/msword | ✓ Supported |
| JPEG | .jpg, .jpeg | image/jpeg | ✓ Supported (OCR in M3) |
| PNG | .png | image/png | ✓ Supported (OCR in M3) |
| TIFF | .tiff, .tif | image/tiff | ✓ Supported (OCR in M3) |
| Text | .txt | text/plain | ✓ Supported |

**Unsupported files are skipped** during download.

---

## Data Structure

### Downloaded Files
```
downloaded_files/
├── EMARLAN SOCIEDAD ANÓNIMA/
│   ├── certificado_bps_2024.pdf
│   ├── personeria_vigente.docx
│   └── firma_digitalizada.jpg
├── Juan Pérez/
│   ├── certificado_msp.pdf
│   └── constancia_abitab.pdf
└── ...
```

### Metadata Index
```json
{
  "indexed_at": "2024-12-19T12:00:00",
  "total_customers": 25,
  "total_files": 143,
  "customers": {
    "EMARLAN SOCIEDAD ANÓNIMA": [
      {
        "file_id": "1abc2def3ghi",
        "file_name": "certificado_bps_2024.pdf",
        "local_path": "downloaded_files/EMARLAN/certificado_bps_2024.pdf",
        "file_type": "PDF",
        "mime_type": "application/pdf",
        "size_bytes": 524288,
        "size_mb": 0.5,
        "drive_created_time": "2024-11-15T10:30:00",
        "drive_modified_time": "2024-11-20T14:45:00"
      }
    ]
  }
}
```

---

## Security & Privacy

### OAuth Scopes
- **Read-only access:** `https://www.googleapis.com/auth/drive.readonly`
- Cannot modify, delete, or create files
- Can only read files you have access to

### Token Storage
- `token.pickle` - Encrypted authentication token
- Stored locally in project directory
- **Never commit to Git** (already in `.gitignore`)

### Credentials
- `credentials.json` - OAuth client credentials
- **Never commit to Git** (should be in `.gitignore`)
- Each user needs their own credentials

---

## Troubleshooting

### "Credentials file not found"
**Solution:** Download OAuth credentials from Google Cloud Console and save as `credentials.json`.

---

### "python-magic initialization failed"
**Solution:** Install libmagic system library:
- Linux: `sudo apt-get install libmagic1`
- macOS: `brew install libmagic`
- Windows: `pip install python-magic-bin`

The system will still work with extension-based detection if python-magic fails.

---

### "Authentication failed"
**Solutions:**
1. Check that `credentials.json` is valid
2. Ensure you're logged into the correct Google account
3. Delete `token.pickle` and re-authenticate
4. Verify Drive API is enabled in Google Cloud Console

---

### "No folders found"
**Possible causes:**
- Empty Drive
- Looking at wrong parent folder
- Insufficient permissions

Use `--drive-list` to see available folders.

---

### Rate Limiting
Google Drive API has usage limits:
- 1,000 requests per 100 seconds per user
- Large downloads may take time

**Solution:** Use `--drive-scan` to re-index without re-downloading.

---

## Integration with Milestone 1

Milestone 2 is **fully compatible** with Milestone 1:

- Same data models (extended with Drive fields)
- Same customer registry format
- Same CLI interface (added Drive commands)
- All Milestone 1 commands still work

**You can:**
- Scan local folders with `--scan`
- Download from Drive with `--drive-download`
- Use both sources in the same registry

---

## Next Steps

**Milestone 3** will add:
- PDF text extraction (pdfplumber)
- DOCX text extraction (python-docx)
- OCR for scanned documents and images (Tesseract)
- Spanish text corpus building

The files downloaded in Milestone 2 will be the input for Milestone 3's text extraction.

---

## API Limits & Best Practices

### Google Drive API Quotas
- **Queries per 100 seconds per user:** 1,000
- **Queries per day:** 1,000,000,000 (effectively unlimited)

### Best Practices
1. **Authenticate once** - Token is reused automatically
2. **Use `--drive-scan`** for re-indexing (doesn't hit API)
3. **Download specific folders** when possible (`--folder-id`)
4. **Organize Drive structure** - One folder per customer

---

## Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `--drive-auth` | Authenticate with Google Drive | `python main.py --drive-auth` |
| `--drive-list` | List folders in Drive | `python main.py --drive-list` |
| `--drive-download` | Download all customer folders | `python main.py --drive-download` |
| `--drive-download --folder-id <id>` | Download specific folder | `python main.py --drive-download --folder-id 1abc` |
| `--drive-scan` | Scan local downloads | `python main.py --drive-scan` |
| `--metadata-stats` | Show file metadata stats | `python main.py --metadata-stats` |

All Milestone 1 commands (`--scan`, `--stats`, `--customer`, `--list`, `--search`) continue to work.

---

## Milestone 2 Complete ✅

You now have:
- ✅ Google Drive OAuth authentication
- ✅ File downloading from Drive
- ✅ File type detection (content and extension-based)
- ✅ Metadata indexing with Drive IDs
- ✅ Integration with customer registry
- ✅ Support for PDF, DOCX, images
- ✅ Download statistics and reports

**Ready for Milestone 3:** Document text extraction (OCR + parsing).
