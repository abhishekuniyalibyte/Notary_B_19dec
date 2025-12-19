"""
Track B - Milestone 2: Metadata Indexer
Indexes file metadata from downloaded Drive files.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from file_detector import FileDetector, FileType


class FileMetadata:
    """Represents metadata for a single file"""

    def __init__(
        self,
        file_id: Optional[str],
        file_name: str,
        local_path: str,
        file_type: FileType,
        mime_type: Optional[str],
        size_bytes: int,
        created_time: Optional[str] = None,
        modified_time: Optional[str] = None,
        drive_created_time: Optional[str] = None,
        drive_modified_time: Optional[str] = None
    ):
        self.file_id = file_id
        self.file_name = file_name
        self.local_path = local_path
        self.file_type = file_type
        self.mime_type = mime_type
        self.size_bytes = size_bytes
        self.size_mb = round(size_bytes / (1024 * 1024), 2) if size_bytes else 0
        self.created_time = created_time
        self.modified_time = modified_time
        self.drive_created_time = drive_created_time
        self.drive_modified_time = drive_modified_time
        self.indexed_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'file_id': self.file_id,
            'file_name': self.file_name,
            'local_path': self.local_path,
            'file_type': self.file_type,
            'mime_type': self.mime_type,
            'size_bytes': self.size_bytes,
            'size_mb': self.size_mb,
            'created_time': self.created_time,
            'modified_time': self.modified_time,
            'drive_created_time': self.drive_created_time,
            'drive_modified_time': self.drive_modified_time,
            'indexed_at': self.indexed_at
        }


class MetadataIndex:
    """
    Maintains an index of all downloaded files with metadata.
    Bridges between Drive downloads and certificate registry.
    """

    def __init__(self, index_file: str = "./data/file_metadata_index.json"):
        """
        Initialize metadata index.

        Args:
            index_file: Path to JSON file storing metadata index
        """
        self.index_file = Path(index_file)
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        self.detector = FileDetector()
        self.metadata: Dict[str, List[FileMetadata]] = {}

    def add_file(
        self,
        customer_name: str,
        file_metadata: FileMetadata
    ):
        """
        Add file metadata to index.

        Args:
            customer_name: Name of customer (folder)
            file_metadata: FileMetadata object
        """
        if customer_name not in self.metadata:
            self.metadata[customer_name] = []

        self.metadata[customer_name].append(file_metadata)

    def index_downloaded_files(self, download_dir: Path, customer_name: str) -> int:
        """
        Index all files in a customer's download directory.

        Args:
            download_dir: Path to customer's download directory
            customer_name: Customer name

        Returns:
            Number of files indexed
        """
        if not download_dir.exists():
            return 0

        count = 0

        for file_path in download_dir.rglob('*'):
            if not file_path.is_file():
                continue

            # Detect file type
            file_type = self.detector.detect_file_type(file_path)
            mime_type = self.detector.detect_from_content(file_path) or \
                        self.detector.detect_from_extension(file_path)

            # Get file stats
            stats = file_path.stat()

            # Create metadata
            metadata = FileMetadata(
                file_id=None,  # No Drive ID for local files
                file_name=file_path.name,
                local_path=str(file_path),
                file_type=file_type,
                mime_type=mime_type,
                size_bytes=stats.st_size,
                created_time=datetime.fromtimestamp(stats.st_ctime).isoformat(),
                modified_time=datetime.fromtimestamp(stats.st_mtime).isoformat()
            )

            self.add_file(customer_name, metadata)
            count += 1

        return count

    def index_from_drive_stats(self, drive_stats: List[Dict]) -> int:
        """
        Index files from Drive download statistics.

        Args:
            drive_stats: List of download statistics from DriveManager

        Returns:
            Total number of files indexed
        """
        total = 0

        for stats in drive_stats:
            customer_name = stats['folder_name']

            for file_meta in stats.get('file_metadata', []):
                # Detect file type from local file
                local_path = Path(file_meta['local_path'])
                file_type = self.detector.detect_file_type(local_path)

                # Get local file stats
                if local_path.exists():
                    local_stats = local_path.stat()
                    created_time = datetime.fromtimestamp(local_stats.st_ctime).isoformat()
                    modified_time = datetime.fromtimestamp(local_stats.st_mtime).isoformat()
                else:
                    created_time = None
                    modified_time = None

                metadata = FileMetadata(
                    file_id=file_meta.get('file_id'),
                    file_name=file_meta['file_name'],
                    local_path=file_meta['local_path'],
                    file_type=file_type,
                    mime_type=file_meta.get('mime_type'),
                    size_bytes=int(file_meta.get('size', 0)),
                    created_time=created_time,
                    modified_time=modified_time,
                    drive_created_time=file_meta.get('created_time'),
                    drive_modified_time=file_meta.get('modified_time')
                )

                self.add_file(customer_name, metadata)
                total += 1

        return total

    def save(self):
        """Save metadata index to JSON file"""
        data = {
            'indexed_at': datetime.now().isoformat(),
            'total_customers': len(self.metadata),
            'total_files': sum(len(files) for files in self.metadata.values()),
            'customers': {}
        }

        # Convert metadata to dictionaries
        for customer_name, files in self.metadata.items():
            data['customers'][customer_name] = [f.to_dict() for f in files]

        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self) -> bool:
        """
        Load metadata index from JSON file.

        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.index_file.exists():
            return False

        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.metadata = {}

            for customer_name, files in data.get('customers', {}).items():
                self.metadata[customer_name] = [
                    FileMetadata(**file_data) for file_data in files
                ]

            return True

        except Exception as e:
            print(f"Error loading metadata index: {e}")
            return False

    def get_customer_files(self, customer_name: str) -> List[FileMetadata]:
        """Get all files for a customer"""
        return self.metadata.get(customer_name, [])

    def get_files_by_type(self, customer_name: str, file_type: FileType) -> List[FileMetadata]:
        """Get files of specific type for a customer"""
        files = self.get_customer_files(customer_name)
        return [f for f in files if f.file_type == file_type]

    def get_statistics(self) -> Dict:
        """
        Generate statistics about indexed files.

        Returns:
            Dictionary with statistics
        """
        total_files = 0
        total_size = 0
        type_counts = {}

        for files in self.metadata.values():
            for file in files:
                total_files += 1
                total_size += file.size_bytes

                file_type = str(file.file_type)
                type_counts[file_type] = type_counts.get(file_type, 0) + 1

        return {
            'total_customers': len(self.metadata),
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'files_by_type': type_counts,
            'customers_with_files': [
                {
                    'name': name,
                    'file_count': len(files),
                    'total_size_mb': round(sum(f.size_bytes for f in files) / (1024 * 1024), 2)
                }
                for name, files in self.metadata.items()
            ]
        }

    def get_summary(self) -> str:
        """Get human-readable summary"""
        stats = self.get_statistics()

        summary = f"""
Metadata Index Summary
======================
Total Customers: {stats['total_customers']}
Total Files: {stats['total_files']}
Total Size: {stats['total_size_mb']} MB

Files by Type:
"""
        for file_type, count in stats['files_by_type'].items():
            summary += f"  {file_type}: {count}\n"

        return summary

    def export_report(self, output_file: str):
        """
        Export detailed report as JSON.

        Args:
            output_file: Path to output file
        """
        stats = self.get_statistics()

        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_customers': stats['total_customers'],
                'total_files': stats['total_files'],
                'total_size_mb': stats['total_size_mb']
            },
            'files_by_type': stats['files_by_type'],
            'customers': []
        }

        # Add per-customer details
        for customer_name, files in self.metadata.items():
            customer_info = {
                'name': customer_name,
                'total_files': len(files),
                'total_size_mb': round(sum(f.size_bytes for f in files) / (1024 * 1024), 2),
                'files': [f.to_dict() for f in files]
            }
            report['customers'].append(customer_info)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
