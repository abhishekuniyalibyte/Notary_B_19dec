"""
Track B - Milestone 2: File Type Detection
Detects and validates file types for certificate processing.
"""

import mimetypes
from pathlib import Path
from typing import Optional, Dict
from enum import Enum

try:
    import magic
    PYTHON_MAGIC_AVAILABLE = True
except ImportError:
    PYTHON_MAGIC_AVAILABLE = False


class FileType(str, Enum):
    """Supported file types for certificate processing"""
    PDF = "PDF"
    DOCX = "DOCX"
    DOC = "DOC"
    IMAGE_JPG = "IMAGE_JPG"
    IMAGE_PNG = "IMAGE_PNG"
    IMAGE_TIFF = "IMAGE_TIFF"
    TEXT = "TEXT"
    UNKNOWN = "UNKNOWN"


class FileDetector:
    """
    Detects file types using multiple methods:
    1. python-magic (libmagic) - most accurate
    2. mimetypes (extension-based) - fallback
    """

    # MIME type to FileType mapping
    MIME_TYPE_MAP = {
        'application/pdf': FileType.PDF,
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': FileType.DOCX,
        'application/msword': FileType.DOC,
        'image/jpeg': FileType.IMAGE_JPG,
        'image/png': FileType.IMAGE_PNG,
        'image/tiff': FileType.IMAGE_TIFF,
        'text/plain': FileType.TEXT,
    }

    # Extension to FileType mapping (fallback)
    EXTENSION_MAP = {
        '.pdf': FileType.PDF,
        '.docx': FileType.DOCX,
        '.doc': FileType.DOC,
        '.jpg': FileType.IMAGE_JPG,
        '.jpeg': FileType.IMAGE_JPG,
        '.png': FileType.IMAGE_PNG,
        '.tiff': FileType.IMAGE_TIFF,
        '.tif': FileType.IMAGE_TIFF,
        '.txt': FileType.TEXT,
    }

    def __init__(self):
        """Initialize file detector"""
        self.magic_available = PYTHON_MAGIC_AVAILABLE
        if self.magic_available:
            try:
                # Test if magic library works
                self.mime = magic.Magic(mime=True)
            except Exception as e:
                print(f"Warning: python-magic initialization failed: {e}")
                self.magic_available = False

    def detect_from_content(self, file_path: Path) -> Optional[str]:
        """
        Detect MIME type from file content using python-magic.

        Args:
            file_path: Path to file

        Returns:
            MIME type string or None
        """
        if not self.magic_available:
            return None

        try:
            mime_type = self.mime.from_file(str(file_path))
            return mime_type
        except Exception as e:
            print(f"Warning: Magic detection failed for {file_path.name}: {e}")
            return None

    def detect_from_extension(self, file_path: Path) -> Optional[str]:
        """
        Detect MIME type from file extension.

        Args:
            file_path: Path to file

        Returns:
            MIME type string or None
        """
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type

    def detect_file_type(self, file_path: Path) -> FileType:
        """
        Detect file type using best available method.

        Args:
            file_path: Path to file

        Returns:
            FileType enum
        """
        if not file_path.exists():
            return FileType.UNKNOWN

        # Try content-based detection first (most accurate)
        mime_type = None
        if self.magic_available:
            mime_type = self.detect_from_content(file_path)

        # Fallback to extension-based detection
        if not mime_type:
            mime_type = self.detect_from_extension(file_path)

        # Fallback to extension mapping if mime type detection failed
        if not mime_type:
            extension = file_path.suffix.lower()
            return self.EXTENSION_MAP.get(extension, FileType.UNKNOWN)

        # Map MIME type to FileType
        return self.MIME_TYPE_MAP.get(mime_type, FileType.UNKNOWN)

    def is_document(self, file_type: FileType) -> bool:
        """Check if file type is a document (PDF, DOCX, DOC, TEXT)"""
        return file_type in {FileType.PDF, FileType.DOCX, FileType.DOC, FileType.TEXT}

    def is_image(self, file_type: FileType) -> bool:
        """Check if file type is an image"""
        return file_type in {FileType.IMAGE_JPG, FileType.IMAGE_PNG, FileType.IMAGE_TIFF}

    def requires_ocr(self, file_type: FileType) -> bool:
        """Check if file requires OCR processing"""
        return self.is_image(file_type)

    def get_file_info(self, file_path: Path) -> Dict:
        """
        Get comprehensive file information.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file information
        """
        if not file_path.exists():
            return {
                'exists': False,
                'file_name': file_path.name,
                'file_path': str(file_path)
            }

        file_type = self.detect_file_type(file_path)
        mime_type = self.detect_from_content(file_path) or self.detect_from_extension(file_path)

        return {
            'exists': True,
            'file_name': file_path.name,
            'file_path': str(file_path),
            'file_type': file_type,
            'mime_type': mime_type,
            'size_bytes': file_path.stat().st_size,
            'size_mb': round(file_path.stat().st_size / (1024 * 1024), 2),
            'extension': file_path.suffix.lower(),
            'is_document': self.is_document(file_type),
            'is_image': self.is_image(file_type),
            'requires_ocr': self.requires_ocr(file_type),
            'detection_method': 'magic' if self.magic_available else 'extension'
        }

    def scan_directory(self, directory_path: Path) -> Dict:
        """
        Scan directory and categorize files by type.

        Args:
            directory_path: Path to directory

        Returns:
            Dictionary with file statistics
        """
        if not directory_path.is_dir():
            return {'error': 'Not a directory'}

        stats = {
            'total_files': 0,
            'by_type': {},
            'documents': 0,
            'images': 0,
            'unknown': 0,
            'files': []
        }

        for file_path in directory_path.rglob('*'):
            if not file_path.is_file():
                continue

            stats['total_files'] += 1
            file_type = self.detect_file_type(file_path)

            # Count by type
            stats['by_type'][file_type] = stats['by_type'].get(file_type, 0) + 1

            # Category counts
            if self.is_document(file_type):
                stats['documents'] += 1
            elif self.is_image(file_type):
                stats['images'] += 1
            else:
                stats['unknown'] += 1

            # Store file info
            stats['files'].append({
                'name': file_path.name,
                'path': str(file_path),
                'type': file_type
            })

        return stats


def detect_file_type(file_path: str) -> FileType:
    """
    Convenience function to detect file type.

    Args:
        file_path: Path to file (string)

    Returns:
        FileType enum
    """
    detector = FileDetector()
    return detector.detect_file_type(Path(file_path))


if __name__ == '__main__':
    """
    Test file detection standalone.
    Usage: python file_detector.py
    """
    import sys

    print("=" * 70)
    print("  File Type Detector Test")
    print("=" * 70)

    detector = FileDetector()

    if detector.magic_available:
        print("\n✓ python-magic available (content-based detection)")
    else:
        print("\n⚠ python-magic not available (using extension-based detection)")
        print("  Install with: pip install python-magic")
        print("  On Linux: sudo apt-get install libmagic1")

    if len(sys.argv) > 1:
        # Test specific file
        file_path = Path(sys.argv[1])
        print(f"\nTesting file: {file_path}")

        info = detector.get_file_info(file_path)

        print("\nFile Information:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    else:
        print("\nUsage: python file_detector.py <file_path>")
        print("Example: python file_detector.py certificate.pdf")
