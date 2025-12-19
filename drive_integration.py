"""
Track B - Milestone 2: Drive Integration
Integrates Google Drive file downloads with existing customer registry system.
"""

from pathlib import Path
from typing import Optional, List, Dict
import hashlib

from drive_auth import DriveAuthenticator, setup_drive_auth
from drive_manager import DriveManager
from metadata_indexer import MetadataIndex
from folder_scanner import FolderScanner
from storage import StorageManager
from models import Customer, CustomerType, CertificateRecord, CustomerRegistry, CertificateStatus


class DriveIntegration:
    """
    Integrates Google Drive downloads with customer registry system.
    Bridges between Drive files and certificate tracking.
    """

    def __init__(
        self,
        download_dir: str = "./downloaded_files",
        storage_dir: str = "./data"
    ):
        """
        Initialize Drive integration.

        Args:
            download_dir: Directory to download files from Drive
            storage_dir: Directory for registry and metadata storage
        """
        self.download_dir = Path(download_dir)
        self.storage_dir = Path(storage_dir)
        self.auth: Optional[DriveAuthenticator] = None
        self.drive_manager: Optional[DriveManager] = None
        self.metadata_index = MetadataIndex(str(self.storage_dir / "file_metadata_index.json"))
        self.storage = StorageManager(str(self.storage_dir))

    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive.

        Returns:
            True if successful, False otherwise
        """
        self.auth = setup_drive_auth()
        if not self.auth:
            return False

        self.drive_manager = DriveManager(self.auth, str(self.download_dir))
        return True

    def download_and_index(self, parent_folder_id: Optional[str] = None) -> CustomerRegistry:
        """
        Download all customer folders from Drive and create registry.

        Args:
            parent_folder_id: Drive folder ID containing customer folders (None = root)

        Returns:
            CustomerRegistry with all indexed data
        """
        if not self.drive_manager:
            raise ValueError("Not authenticated. Call authenticate() first.")

        # Download all customer folders
        print("\n" + "=" * 70)
        print("  MILESTONE 2: GOOGLE DRIVE INTEGRATION")
        print("=" * 70)

        download_stats = self.drive_manager.download_all_customer_folders(parent_folder_id)

        # Index metadata
        print("\n" + "=" * 70)
        print("  INDEXING FILE METADATA")
        print("=" * 70)

        total_indexed = self.metadata_index.index_from_drive_stats(download_stats)
        print(f"\n✓ Indexed {total_indexed} files")

        # Save metadata index
        self.metadata_index.save()
        print(f"✓ Metadata saved to: {self.metadata_index.index_file}")

        # Create customer registry from downloaded files
        print("\n" + "=" * 70)
        print("  CREATING CUSTOMER REGISTRY")
        print("=" * 70)

        registry = self._create_registry_from_downloads(download_stats)

        # Save registry
        self.storage.save_registry(registry)
        print(f"\n✓ Registry saved to: {self.storage.registry_file}")

        # Export report
        report_file = self.storage_dir / "customer_report_drive.json"
        self.storage.export_customer_report(registry, str(report_file))
        print(f"✓ Report exported to: {report_file}")

        return registry

    def _create_registry_from_downloads(self, download_stats: List[Dict]) -> CustomerRegistry:
        """
        Create CustomerRegistry from Drive download statistics.

        Args:
            download_stats: List of download statistics from DriveManager

        Returns:
            CustomerRegistry object
        """
        registry = CustomerRegistry()

        for stats in download_stats:
            folder_name = stats['folder_name']
            folder_id = stats['folder_id']
            folder_path = self.download_dir / folder_name

            # Generate customer ID
            customer_id = self._generate_customer_id(folder_name)

            # Detect customer type
            customer_type = self._detect_customer_type(folder_name)

            # Create Customer
            customer = Customer(
                customer_id=customer_id,
                name=folder_name,
                customer_type=customer_type,
                folder_path=str(folder_path),
                drive_folder_id=folder_id
            )

            registry.add_customer(customer)
            print(f"  ✓ Customer: {folder_name} ({customer_type})")

            # Create certificates from files
            for file_meta in stats.get('file_metadata', []):
                cert = self._create_certificate_from_file(customer_id, file_meta)
                if cert:
                    registry.add_certificate(cert)

        return registry

    def _generate_customer_id(self, folder_name: str) -> str:
        """Generate unique customer ID from folder name"""
        return hashlib.md5(folder_name.encode()).hexdigest()[:12]

    def _detect_customer_type(self, name: str) -> CustomerType:
        """
        Detect if customer is a person or company.

        Args:
            name: Customer name (folder name)

        Returns:
            CustomerType.PERSON or CustomerType.COMPANY
        """
        name_lower = name.lower()

        # Company keywords
        company_keywords = [
            'sociedad', 'anónima', 's.a.', 'sa', 'srl', 's.r.l.',
            'ltda', 'limitada', 'empresa', 'corporación', 'corp'
        ]

        for keyword in company_keywords:
            if keyword in name_lower:
                return CustomerType.COMPANY

        # Multiple words suggests company
        if len(name.split()) > 3:
            return CustomerType.COMPANY

        return CustomerType.PERSON

    def _create_certificate_from_file(
        self,
        customer_id: str,
        file_meta: Dict
    ) -> Optional[CertificateRecord]:
        """
        Create CertificateRecord from file metadata.

        Args:
            customer_id: Customer ID
            file_meta: File metadata dictionary

        Returns:
            CertificateRecord or None
        """
        filename = file_meta['file_name']
        file_path = file_meta['local_path']

        # Check if this is a certificate file
        if not self._is_certificate_file(filename):
            return None

        # Generate certificate ID
        cert_id = self._generate_certificate_id(customer_id, filename)

        # Extract metadata
        has_error, status = self._extract_error_status(filename)
        institution = self._extract_institution(filename)
        date = None  # Date extraction handled in Milestone 1's scanner

        certificate = CertificateRecord(
            certificate_id=cert_id,
            customer_id=customer_id,
            institution=institution,
            date=date,
            status=status,
            source_files=[file_path],
            filename=filename,
            file_path=file_path,
            has_error_prefix=has_error,
            drive_file_id=file_meta.get('file_id'),
            mime_type=file_meta.get('mime_type'),
            file_size=int(file_meta.get('size', 0))
        )

        return certificate

    def _is_certificate_file(self, filename: str) -> bool:
        """Check if file is likely a certificate"""
        filename_lower = filename.lower()

        certificate_keywords = [
            'certificado', 'certifica', 'constancia', 'personería',
            'firma', 'vigencia', 'poderes', 'bps', 'msp', 'abitab'
        ]

        return any(keyword in filename_lower for keyword in certificate_keywords)

    def _extract_error_status(self, filename: str) -> tuple:
        """Extract error status from filename"""
        has_error = filename.upper().startswith('ERROR')
        status = CertificateStatus.ERROR if has_error else CertificateStatus.OK
        return has_error, status

    def _extract_institution(self, filename: str) -> Optional[str]:
        """Extract institution name from filename"""
        filename_upper = filename.upper()

        institutions = ['BPS', 'MSP', 'ABITAB', 'DGI', 'ASSE', 'ANTEL', 'UTE', 'OSE']

        for inst in institutions:
            if inst in filename_upper:
                return inst

        return None

    def _generate_certificate_id(self, customer_id: str, filename: str) -> str:
        """Generate unique certificate ID"""
        combined = f"{customer_id}_{filename}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]

    def scan_local_downloads(self) -> CustomerRegistry:
        """
        Scan already downloaded files (without re-downloading).
        Useful for re-indexing local files.

        Returns:
            CustomerRegistry from local files
        """
        print("\n" + "=" * 70)
        print("  SCANNING LOCAL DOWNLOADS")
        print("=" * 70)

        scanner = FolderScanner(str(self.download_dir))
        registry = scanner.scan_all_customers()

        # Save registry
        self.storage.save_registry(registry)
        print(f"\n✓ Registry saved to: {self.storage.registry_file}")

        return registry

    def list_drive_folders(self, parent_folder_id: Optional[str] = None):
        """
        List available folders in Drive.

        Args:
            parent_folder_id: Parent folder ID (None = root)
        """
        if not self.drive_manager:
            raise ValueError("Not authenticated. Call authenticate() first.")

        folders = self.drive_manager.list_folders(parent_folder_id)

        print("\n" + "=" * 70)
        print("  GOOGLE DRIVE FOLDERS")
        print("=" * 70)
        print(f"\nFound {len(folders)} folders:\n")

        for folder in folders:
            print(f"  📁 {folder['name']}")
            print(f"     ID: {folder['id']}")
            print(f"     Modified: {folder.get('modifiedTime', 'Unknown')}")
            print()

    def download_specific_folder(self, folder_id: str, folder_name: Optional[str] = None) -> CustomerRegistry:
        """
        Download a specific customer folder from Drive.

        Args:
            folder_id: Google Drive folder ID
            folder_name: Name for the folder (optional, will fetch from Drive if not provided)

        Returns:
            CustomerRegistry with downloaded customer data
        """
        if not self.drive_manager:
            raise ValueError("Not authenticated. Call authenticate() first.")

        # Get folder name if not provided
        if not folder_name:
            folder_meta = self.drive_manager.get_file_metadata(folder_id)
            if folder_meta:
                folder_name = folder_meta['name']
            else:
                folder_name = f"folder_{folder_id}"

        # Download folder
        stats = self.drive_manager.download_customer_folder(folder_id, folder_name)

        # Index metadata
        self.metadata_index.index_from_drive_stats([stats])
        self.metadata_index.save()

        # Create registry
        registry = self._create_registry_from_downloads([stats])
        self.storage.save_registry(registry)

        return registry
