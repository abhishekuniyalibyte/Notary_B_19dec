"""
Track B - Milestone 1: Storage Layer
Handles persistence of customer registry using JSON files.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from models import CustomerRegistry, Customer, CertificateRecord


class StorageManager:
    """
    Manages storage and retrieval of customer registry.
    Uses JSON files for lightweight persistence.
    """

    def __init__(self, storage_dir: str = "./data"):
        """
        Initialize storage manager.

        Args:
            storage_dir: Directory to store data files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.registry_file = self.storage_dir / "customer_registry.json"
        self.backup_dir = self.storage_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

    def _serialize_registry(self, registry: CustomerRegistry) -> dict:
        """
        Convert CustomerRegistry to JSON-serializable dict.

        Args:
            registry: CustomerRegistry object

        Returns:
            Dictionary ready for JSON serialization
        """
        return {
            'customers': [customer.model_dump(mode='json') for customer in registry.customers],
            'certificates': [cert.model_dump(mode='json') for cert in registry.certificates],
            'last_updated': registry.last_updated.isoformat(),
            'total_customers': registry.total_customers,
            'total_certificates': registry.total_certificates
        }

    def _deserialize_registry(self, data: dict) -> CustomerRegistry:
        """
        Convert JSON dict back to CustomerRegistry.

        Args:
            data: Dictionary from JSON

        Returns:
            CustomerRegistry object
        """
        registry = CustomerRegistry(
            customers=[Customer(**customer) for customer in data.get('customers', [])],
            certificates=[CertificateRecord(**cert) for cert in data.get('certificates', [])],
            last_updated=datetime.fromisoformat(data.get('last_updated', datetime.now().isoformat())),
            total_customers=data.get('total_customers', 0),
            total_certificates=data.get('total_certificates', 0)
        )
        return registry

    def save_registry(self, registry: CustomerRegistry, create_backup: bool = True) -> None:
        """
        Save customer registry to JSON file.

        Args:
            registry: CustomerRegistry to save
            create_backup: Whether to create a backup of existing file
        """
        # Create backup if file exists
        if create_backup and self.registry_file.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"registry_backup_{timestamp}.json"
            backup_file.write_text(self.registry_file.read_text())

        # Save registry
        data = self._serialize_registry(registry)
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_registry(self) -> Optional[CustomerRegistry]:
        """
        Load customer registry from JSON file.

        Returns:
            CustomerRegistry object or None if file doesn't exist
        """
        if not self.registry_file.exists():
            return None

        with open(self.registry_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return self._deserialize_registry(data)

    def export_customer_report(self, registry: CustomerRegistry, output_file: str) -> None:
        """
        Export customer registry as a readable JSON report.

        Args:
            registry: CustomerRegistry to export
            output_file: Path to output file
        """
        output_path = Path(output_file)

        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_customers': registry.total_customers,
                'total_certificates': registry.total_certificates,
                'total_errors': len(registry.get_error_certificates())
            },
            'customers': []
        }

        # Add detailed customer info
        for customer in registry.customers:
            customer_certs = registry.get_customer_certificates(customer.customer_id)
            error_certs = [cert for cert in customer_certs if cert.has_error_prefix]

            customer_info = {
                'name': customer.name,
                'type': customer.customer_type,
                'folder': customer.folder_path,
                'total_certificates': len(customer_certs),
                'error_certificates': len(error_certs),
                'certificates': [
                    {
                        'filename': cert.filename,
                        'institution': cert.institution,
                        'status': cert.status,
                        'date': cert.date.isoformat() if cert.date else None,
                        'has_error': cert.has_error_prefix
                    }
                    for cert in customer_certs
                ]
            }
            report['customers'].append(customer_info)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def get_statistics(self, registry: CustomerRegistry) -> dict:
        """
        Generate detailed statistics from registry.

        Args:
            registry: CustomerRegistry object

        Returns:
            Dictionary with statistics
        """
        from collections import Counter

        # Count by customer type
        type_counts = Counter(c.customer_type for c in registry.customers)

        # Count by institution
        institution_counts = Counter(
            cert.institution for cert in registry.certificates if cert.institution
        )

        # Count by status
        status_counts = Counter(cert.status for cert in registry.certificates)

        # Customers with most certificates
        customer_cert_counts = Counter(cert.customer_id for cert in registry.certificates)
        top_customers = customer_cert_counts.most_common(10)

        # Map customer IDs to names
        customer_id_to_name = {c.customer_id: c.name for c in registry.customers}
        top_customers_with_names = [
            {'name': customer_id_to_name.get(cid, 'Unknown'), 'certificate_count': count}
            for cid, count in top_customers
        ]

        return {
            'customer_types': dict(type_counts),
            'institutions': dict(institution_counts),
            'certificate_status': dict(status_counts),
            'top_customers': top_customers_with_names,
            'total_customers': registry.total_customers,
            'total_certificates': registry.total_certificates
        }
