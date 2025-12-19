"""
Track B - Milestone 1: Certificate History Tracker
Provides utilities to query and analyze certificate history per customer.
"""

from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict

from models import CustomerRegistry, CertificateRecord, Customer, CertificateStatus


class CertificateTracker:
    """
    Tracks and analyzes certificate history for customers.
    Provides insights into certificate patterns, errors, and trends.
    """

    def __init__(self, registry: CustomerRegistry):
        """
        Initialize tracker with customer registry.

        Args:
            registry: CustomerRegistry containing all data
        """
        self.registry = registry

    def get_customer_by_name(self, name: str) -> Optional[Customer]:
        """
        Find customer by name (case-insensitive partial match).

        Args:
            name: Customer name or partial name

        Returns:
            Customer object or None
        """
        name_lower = name.lower()
        for customer in self.registry.customers:
            if name_lower in customer.name.lower():
                return customer
        return None

    def get_customer_by_id(self, customer_id: str) -> Optional[Customer]:
        """
        Find customer by ID.

        Args:
            customer_id: Customer ID

        Returns:
            Customer object or None
        """
        for customer in self.registry.customers:
            if customer.customer_id == customer_id:
                return customer
        return None

    def get_certificate_history(self, customer_id: str) -> List[CertificateRecord]:
        """
        Get complete certificate history for a customer, sorted by date.

        Args:
            customer_id: Customer ID

        Returns:
            List of CertificateRecord objects sorted by date (newest first)
        """
        certificates = self.registry.get_customer_certificates(customer_id)

        # Sort by date if available, otherwise by filename
        sorted_certs = sorted(
            certificates,
            key=lambda c: (c.date if c.date else datetime.min, c.filename),
            reverse=True
        )

        return sorted_certs

    def get_error_history(self, customer_id: str) -> List[CertificateRecord]:
        """
        Get certificates marked with ERROR for a customer.

        Args:
            customer_id: Customer ID

        Returns:
            List of CertificateRecord objects with errors
        """
        all_certs = self.registry.get_customer_certificates(customer_id)
        return [cert for cert in all_certs if cert.has_error_prefix or cert.status == CertificateStatus.ERROR]

    def get_certificates_by_institution(self, customer_id: str, institution: str) -> List[CertificateRecord]:
        """
        Get certificates for a specific institution.

        Args:
            customer_id: Customer ID
            institution: Institution name (e.g., BPS, MSP)

        Returns:
            List of CertificateRecord objects for that institution
        """
        all_certs = self.registry.get_customer_certificates(customer_id)
        return [cert for cert in all_certs if cert.institution and cert.institution.upper() == institution.upper()]

    def get_customer_summary(self, customer_id: str) -> Dict:
        """
        Generate detailed summary for a customer.

        Args:
            customer_id: Customer ID

        Returns:
            Dictionary with customer summary
        """
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            return {}

        certificates = self.registry.get_customer_certificates(customer_id)
        error_certs = self.get_error_history(customer_id)

        # Group by institution
        by_institution = defaultdict(int)
        for cert in certificates:
            if cert.institution:
                by_institution[cert.institution] += 1

        # Recent certificates (last 5)
        recent = sorted(
            [c for c in certificates if c.date],
            key=lambda c: c.date,
            reverse=True
        )[:5]

        return {
            'customer_id': customer.customer_id,
            'name': customer.name,
            'type': customer.customer_type,
            'folder': customer.folder_path,
            'total_certificates': len(certificates),
            'error_certificates': len(error_certs),
            'error_rate': len(error_certs) / len(certificates) if certificates else 0,
            'certificates_by_institution': dict(by_institution),
            'recent_certificates': [
                {
                    'filename': cert.filename,
                    'date': cert.date.isoformat() if cert.date else None,
                    'institution': cert.institution,
                    'status': cert.status
                }
                for cert in recent
            ]
        }

    def find_duplicate_certificates(self, customer_id: str) -> List[List[CertificateRecord]]:
        """
        Find potential duplicate certificates based on filename similarity.

        Args:
            customer_id: Customer ID

        Returns:
            List of lists, where each inner list contains potential duplicates
        """
        certificates = self.registry.get_customer_certificates(customer_id)

        # Group by similar filenames (simplified approach)
        groups = defaultdict(list)
        for cert in certificates:
            # Remove ERROR prefix and date patterns for comparison
            clean_name = cert.filename.replace('ERROR', '').strip()
            clean_name = clean_name[:30]  # Compare first 30 chars
            groups[clean_name].append(cert)

        # Return only groups with multiple certificates
        duplicates = [group for group in groups.values() if len(group) > 1]
        return duplicates

    def get_institution_analysis(self) -> Dict:
        """
        Analyze certificates across all customers by institution.

        Returns:
            Dictionary with institution-level statistics
        """
        institution_data = defaultdict(lambda: {
            'total': 0,
            'errors': 0,
            'customers': set()
        })

        for cert in self.registry.certificates:
            if cert.institution:
                inst = cert.institution
                institution_data[inst]['total'] += 1
                if cert.has_error_prefix or cert.status == CertificateStatus.ERROR:
                    institution_data[inst]['errors'] += 1
                institution_data[inst]['customers'].add(cert.customer_id)

        # Convert sets to counts
        result = {}
        for inst, data in institution_data.items():
            result[inst] = {
                'total_certificates': data['total'],
                'error_certificates': data['errors'],
                'error_rate': data['errors'] / data['total'] if data['total'] > 0 else 0,
                'unique_customers': len(data['customers'])
            }

        return result

    def get_timeline_analysis(self, customer_id: str) -> Dict:
        """
        Analyze certificate creation timeline for a customer.

        Args:
            customer_id: Customer ID

        Returns:
            Dictionary with timeline statistics
        """
        certificates = [cert for cert in self.registry.get_customer_certificates(customer_id) if cert.date]

        if not certificates:
            return {'message': 'No dated certificates found'}

        dates = [cert.date for cert in certificates]
        oldest = min(dates)
        newest = max(dates)

        # Group by year-month
        by_month = defaultdict(int)
        for cert in certificates:
            month_key = cert.date.strftime('%Y-%m')
            by_month[month_key] += 1

        return {
            'total_dated_certificates': len(certificates),
            'oldest_certificate': oldest.isoformat(),
            'newest_certificate': newest.isoformat(),
            'time_span_days': (newest - oldest).days,
            'certificates_by_month': dict(sorted(by_month.items()))
        }

    def search_certificates(self, search_term: str) -> List[CertificateRecord]:
        """
        Search all certificates by filename.

        Args:
            search_term: Term to search for in filename

        Returns:
            List of matching CertificateRecord objects
        """
        search_lower = search_term.lower()
        matches = []

        for cert in self.registry.certificates:
            if search_lower in cert.filename.lower():
                matches.append(cert)

        return matches

    def get_error_report(self) -> Dict:
        """
        Generate comprehensive error report across all customers.

        Returns:
            Dictionary with error analysis
        """
        error_certs = self.registry.get_error_certificates()

        # Group by customer
        by_customer = defaultdict(list)
        for cert in error_certs:
            by_customer[cert.customer_id].append(cert)

        # Get customer names
        customer_id_to_name = {c.customer_id: c.name for c in self.registry.customers}

        customer_errors = [
            {
                'customer_name': customer_id_to_name.get(cid, 'Unknown'),
                'customer_id': cid,
                'error_count': len(certs)
            }
            for cid, certs in by_customer.items()
        ]

        # Sort by error count
        customer_errors.sort(key=lambda x: x['error_count'], reverse=True)

        return {
            'total_error_certificates': len(error_certs),
            'customers_with_errors': len(by_customer),
            'error_rate': len(error_certs) / self.registry.total_certificates if self.registry.total_certificates > 0 else 0,
            'customers_by_error_count': customer_errors
        }
