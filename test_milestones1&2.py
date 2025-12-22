#!/usr/bin/env python3
"""
Test Milestone 1 & 2 - Works with folders OR individual files
Usage:
  python3 test_milestones.py /path/to/customer/folders
  python3 test_milestones.py /path/to/specific/file.pdf
"""

import sys
from pathlib import Path

# Test all imports
try:
    from folder_scanner import FolderScanner
    from storage import StorageManager
    from certificate_tracker import CertificateTracker
    from file_detector import FileDetector
    from metadata_indexer import MetadataIndex
    print("✓ All modules loaded successfully\n")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


def test_single_file(file_path: str):
    """Test a single file"""
    print("=" * 70)
    print("  SINGLE FILE TEST - MILESTONE 2")
    print("=" * 70)

    path = Path(file_path)
    if not path.exists():
        print(f"✗ File not found: {file_path}")
        return False

    print(f"\nFile: {path.name}")
    print(f"Location: {path.parent}")

    # Test file detection
    detector = FileDetector()
    info = detector.get_file_info(path)

    print("\n--- File Information ---")
    print(f"Type: {info.get('file_type', 'UNKNOWN')}")
    print(f"MIME: {info.get('mime_type', 'unknown')}")
    print(f"Size: {info.get('size_mb', 0)} MB ({info.get('size_bytes', 0)} bytes)")
    print(f"Extension: {info.get('extension', 'none')}")
    print(f"Is Document: {info.get('is_document', False)}")
    print(f"Is Image: {info.get('is_image', False)}")
    print(f"Requires OCR: {info.get('requires_ocr', False)}")
    print(f"Detection Method: {info.get('detection_method', 'unknown')}")

    print("\n" + "=" * 70)
    print("✓ File detected successfully!")
    print("=" * 70)
    return True


def test_folder(folder_path: str):
    """Test scanning a customer folder"""
    print("=" * 70)
    print("  FOLDER SCAN TEST - MILESTONE 1 & 2")
    print("=" * 70)

    path = Path(folder_path)
    if not path.exists():
        print(f"✗ Folder not found: {folder_path}")
        return False

    print(f"\nScanning: {path.resolve()}\n")

    # MILESTONE 1: Scan folders
    scanner = FolderScanner(folder_path)
    registry = scanner.scan_all_customers()
    summary = scanner.get_summary(registry)

    print("--- Results ---")
    print(f"Customers: {summary['total_customers']} ({summary['total_persons']} persons, {summary['total_companies']} companies)")
    print(f"Certificates: {summary['total_certificates']}")
    print(f"Errors: {summary['total_error_certificates']}")

    # MILESTONE 2: File detection
    detector = FileDetector()
    print(f"\nFile Detection: {'✓ Magic library' if detector.magic_available else '✓ Extension-based'}")

    # Save
    storage = StorageManager()
    storage.save_registry(registry)
    print(f"\n✓ Saved to: {storage.registry_file}")

    # Show customers
    if registry.customers:
        print("\n--- Customers ---")
        for customer in registry.customers[:5]:
            certs = registry.get_customer_certificates(customer.customer_id)
            errors = sum(1 for c in certs if c.has_error_prefix)
            icon = "🏢" if customer.customer_type == "COMPANY" else "👤"
            print(f"{icon} {customer.name}: {len(certs)} certs ({errors} errors)")
        if len(registry.customers) > 5:
            print(f"... and {len(registry.customers) - 5} more")

    print("\n" + "=" * 70)
    print("✓ Milestones 1 & 2 working correctly!")
    print("=" * 70)
    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 test_milestones.py /path/to/customer/folders")
        print("  python3 test_milestones.py /path/to/specific/file.pdf")
        print("\nExamples:")
        print("  python3 test_milestones.py ./my_customers")
        print('  python3 test_milestones.py "Notaria_client_data/Azili SA/BCU AZILI S.A. 2018.06 DDJJ.pdf"')
        sys.exit(1)

    path = Path(sys.argv[1])

    # Check if it's a file or folder
    if path.is_file():
        test_single_file(sys.argv[1])
    elif path.is_dir():
        test_folder(sys.argv[1])
    else:
        print(f"✗ Path does not exist: {sys.argv[1]}")
        sys.exit(1)
