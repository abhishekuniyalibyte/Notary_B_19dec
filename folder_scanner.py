"""
Track B - Milestone 1: Folder Scanner
Scans customer folders and indexes certificates.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
import hashlib

from models import (
    Customer,
    CustomerType,
    CertificateRecord,
    CertificateStatus,
    CustomerRegistry
)


class FolderScanner:
    """
    Scans directory structure to identify customers and their certificates.
    Each folder = one customer (person or company).
    """

    # Common certificate file extensions
    CERTIFICATE_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}

    # Keywords that suggest a file is a certificate (Spanish)
    CERTIFICATE_KEYWORDS = [
        'certificado', 'certifica', 'constancia', 'personería',
        'firma', 'vigencia', 'poderes', 'bps', 'msp', 'abitab'
    ]

    # Keywords suggesting company vs person
    COMPANY_KEYWORDS = [
        'sociedad', 'anónima', 's.a.', 'sa', 'srl', 's.r.l.',
        'ltda', 'limitada', 'empresa', 'corporación', 'corp'
    ]

    def __init__(self, base_path: str):
        """
        Initialize scanner with base directory containing customer folders.

        Args:
            base_path: Path to directory containing customer folders
        """
        self.base_path = Path(base_path)
        if not self.base_path.exists():
            raise ValueError(f"Base path does not exist: {base_path}")
        if not self.base_path.is_dir():
            raise ValueError(f"Base path is not a directory: {base_path}")

    def _generate_customer_id(self, folder_name: str) -> str:
        """Generate unique customer ID from folder name"""
        # Use hash of folder name for consistent ID generation
        return hashlib.md5(folder_name.encode()).hexdigest()[:12]

    def _detect_customer_type(self, name: str, folder_path: Path) -> CustomerType:
        """
        Detect if customer is a person or company based on name and content.

        Args:
            name: Customer name (folder name)
            folder_path: Path to customer folder

        Returns:
            CustomerType.PERSON or CustomerType.COMPANY
        """
        name_lower = name.lower()

        # Check for company keywords in name
        for keyword in self.COMPANY_KEYWORDS:
            if keyword in name_lower:
                return CustomerType.COMPANY

        # Check if name has multiple words (companies often have longer names)
        words = name.split()
        if len(words) > 3:
            return CustomerType.COMPANY

        # Default to PERSON if uncertain
        return CustomerType.PERSON

    def _is_certificate_file(self, file_path: Path) -> bool:
        """
        Check if a file is likely a certificate.

        Args:
            file_path: Path to file

        Returns:
            True if file appears to be a certificate
        """
        # Check extension
        if file_path.suffix.lower() not in self.CERTIFICATE_EXTENSIONS:
            return False

        # Check filename for certificate keywords
        filename_lower = file_path.name.lower()
        return any(keyword in filename_lower for keyword in self.CERTIFICATE_KEYWORDS)

    def _extract_error_status(self, filename: str) -> Tuple[bool, CertificateStatus]:
        """
        Check if filename starts with ERROR prefix.

        Args:
            filename: Name of the file

        Returns:
            Tuple of (has_error_prefix, status)
        """
        has_error = filename.upper().startswith('ERROR')
        status = CertificateStatus.ERROR if has_error else CertificateStatus.OK
        return has_error, status

    def _extract_institution(self, filename: str) -> Optional[str]:
        """
        Extract institution name from filename if present.
        Common institutions: BPS, MSP, Abitab, DGI, etc.

        Args:
            filename: Name of the file

        Returns:
            Institution name or None
        """
        filename_upper = filename.upper()

        institutions = ['BPS', 'MSP', 'ABITAB', 'DGI', 'ASSE', 'ANTEL', 'UTE', 'OSE']

        for inst in institutions:
            if inst in filename_upper:
                return inst

        return None

    def _extract_date_from_filename(self, filename: str) -> Optional[datetime]:
        """
        Try to extract date from filename.
        Common formats: YYYY-MM-DD, DD-MM-YYYY, YYYYMMDD

        Args:
            filename: Name of the file

        Returns:
            Extracted datetime or None
        """
        # Pattern: YYYY-MM-DD or YYYY_MM_DD
        pattern1 = r'(\d{4})[-_](\d{2})[-_](\d{2})'
        match = re.search(pattern1, filename)
        if match:
            try:
                year, month, day = match.groups()
                return datetime(int(year), int(month), int(day))
            except ValueError:
                pass

        # Pattern: DD-MM-YYYY or DD_MM_YYYY
        pattern2 = r'(\d{2})[-_](\d{2})[-_](\d{4})'
        match = re.search(pattern2, filename)
        if match:
            try:
                day, month, year = match.groups()
                return datetime(int(year), int(month), int(day))
            except ValueError:
                pass

        # Pattern: YYYYMMDD
        pattern3 = r'(\d{8})'
        match = re.search(pattern3, filename)
        if match:
            try:
                date_str = match.group(1)
                return datetime.strptime(date_str, '%Y%m%d')
            except ValueError:
                pass

        return None

    def _generate_certificate_id(self, customer_id: str, filename: str) -> str:
        """Generate unique certificate ID"""
        combined = f"{customer_id}_{filename}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]

    def scan_customer_folder(self, folder_path: Path, customer: Customer) -> List[CertificateRecord]:
        """
        Scan a customer folder for certificates.

        Args:
            folder_path: Path to customer folder
            customer: Customer object

        Returns:
            List of CertificateRecord objects
        """
        certificates = []

        # Recursively scan folder for certificate files
        for file_path in folder_path.rglob('*'):
            if not file_path.is_file():
                continue

            if not self._is_certificate_file(file_path):
                continue

            filename = file_path.name
            has_error, status = self._extract_error_status(filename)
            institution = self._extract_institution(filename)
            date = self._extract_date_from_filename(filename)

            certificate = CertificateRecord(
                certificate_id=self._generate_certificate_id(customer.customer_id, filename),
                customer_id=customer.customer_id,
                institution=institution,
                date=date,
                status=status,
                source_files=[str(file_path)],
                filename=filename,
                file_path=str(file_path),
                has_error_prefix=has_error
            )

            certificates.append(certificate)

        return certificates

    def scan_all_customers(self) -> CustomerRegistry:
        """
        Scan base directory for all customer folders and their certificates.

        Returns:
            CustomerRegistry containing all customers and certificates
        """
        registry = CustomerRegistry()

        # Iterate through immediate subdirectories (each = one customer)
        for folder_path in self.base_path.iterdir():
            if not folder_path.is_dir():
                continue

            # Skip hidden folders
            if folder_path.name.startswith('.'):
                continue

            # Create Customer object
            customer_name = folder_path.name
            customer_id = self._generate_customer_id(customer_name)
            customer_type = self._detect_customer_type(customer_name, folder_path)

            customer = Customer(
                customer_id=customer_id,
                name=customer_name,
                customer_type=customer_type,
                folder_path=str(folder_path)
            )

            registry.add_customer(customer)

            # Scan for certificates in this customer's folder
            certificates = self.scan_customer_folder(folder_path, customer)
            for cert in certificates:
                registry.add_certificate(cert)

        return registry

    def get_summary(self, registry: CustomerRegistry) -> dict:
        """
        Generate summary statistics from registry.

        Args:
            registry: CustomerRegistry object

        Returns:
            Dictionary with summary statistics
        """
        total_persons = sum(1 for c in registry.customers if c.customer_type == CustomerType.PERSON)
        total_companies = sum(1 for c in registry.customers if c.customer_type == CustomerType.COMPANY)
        total_error_certs = len(registry.get_error_certificates())

        return {
            'total_customers': registry.total_customers,
            'total_persons': total_persons,
            'total_companies': total_companies,
            'total_certificates': registry.total_certificates,
            'total_error_certificates': total_error_certs,
            'scan_completed_at': registry.last_updated.isoformat()
        }
