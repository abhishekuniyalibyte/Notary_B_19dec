#!/usr/bin/env python3
"""
Track B - Milestone 1: Main CLI Entry Point
Test and demonstrate the customer registry and certificate indexing system.

Usage:
    python main.py --scan <customer_folders_path>
    python main.py --load
    python main.py --customer <customer_name>
    python main.py --stats
"""

import argparse
import sys
from pathlib import Path

from folder_scanner import FolderScanner
from storage import StorageManager
from certificate_tracker import CertificateTracker
from models import CustomerRegistry


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_section(text: str):
    """Print formatted section"""
    print(f"\n--- {text} ---")


def scan_customers(base_path: str):
    """Scan customer folders and save registry"""
    print_header("SCANNING CUSTOMER FOLDERS")

    scanner = FolderScanner(base_path)
    print(f"\nScanning: {base_path}")

    registry = scanner.scan_all_customers()

    # Display summary
    summary = scanner.get_summary(registry)
    print_section("Scan Summary")
    print(f"Total Customers: {summary['total_customers']}")
    print(f"  - Persons: {summary['total_persons']}")
    print(f"  - Companies: {summary['total_companies']}")
    print(f"Total Certificates: {summary['total_certificates']}")
    print(f"Error Certificates: {summary['total_error_certificates']}")

    # Save registry
    storage = StorageManager()
    storage.save_registry(registry)
    print(f"\n✓ Registry saved to: {storage.registry_file}")

    # Export report
    report_file = storage.storage_dir / "customer_report.json"
    storage.export_customer_report(registry, str(report_file))
    print(f"✓ Report exported to: {report_file}")

    return registry


def load_registry() -> CustomerRegistry:
    """Load existing registry"""
    storage = StorageManager()
    registry = storage.load_registry()

    if not registry:
        print("Error: No registry found. Please scan customer folders first.")
        print("Usage: python main.py --scan <customer_folders_path>")
        sys.exit(1)

    return registry


def show_statistics():
    """Display detailed statistics"""
    print_header("CUSTOMER REGISTRY STATISTICS")

    registry = load_registry()
    storage = StorageManager()
    tracker = CertificateTracker(registry)

    stats = storage.get_statistics(registry)

    print_section("Customer Types")
    for ctype, count in stats['customer_types'].items():
        print(f"  {ctype}: {count}")

    print_section("Certificates by Institution")
    if stats['institutions']:
        for inst, count in sorted(stats['institutions'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {inst}: {count}")
    else:
        print("  No institution data available")

    print_section("Certificate Status")
    for status, count in stats['certificate_status'].items():
        print(f"  {status}: {count}")

    print_section("Top Customers by Certificate Count")
    for customer_data in stats['top_customers'][:5]:
        print(f"  {customer_data['name']}: {customer_data['certificate_count']} certificates")

    # Institution analysis
    print_section("Institution Analysis")
    inst_analysis = tracker.get_institution_analysis()
    for inst, data in sorted(inst_analysis.items(), key=lambda x: x[1]['total_certificates'], reverse=True):
        print(f"\n  {inst}:")
        print(f"    Total Certificates: {data['total_certificates']}")
        print(f"    Error Certificates: {data['error_certificates']}")
        print(f"    Error Rate: {data['error_rate']:.1%}")
        print(f"    Unique Customers: {data['unique_customers']}")

    # Error report
    print_section("Error Report")
    error_report = tracker.get_error_report()
    print(f"  Total Errors: {error_report['total_error_certificates']}")
    print(f"  Customers with Errors: {error_report['customers_with_errors']}")
    print(f"  Overall Error Rate: {error_report['error_rate']:.1%}")


def show_customer_details(customer_name: str):
    """Display detailed information for a specific customer"""
    registry = load_registry()
    tracker = CertificateTracker(registry)

    customer = tracker.get_customer_by_name(customer_name)

    if not customer:
        print(f"Error: Customer '{customer_name}' not found.")
        print("\nAvailable customers:")
        for c in registry.customers[:10]:
            print(f"  - {c.name}")
        if len(registry.customers) > 10:
            print(f"  ... and {len(registry.customers) - 10} more")
        sys.exit(1)

    print_header(f"CUSTOMER DETAILS: {customer.name}")

    # Basic info
    print_section("Basic Information")
    print(f"  Name: {customer.name}")
    print(f"  Type: {customer.customer_type}")
    print(f"  ID: {customer.customer_id}")
    print(f"  Folder: {customer.folder_path}")

    # Summary
    summary = tracker.get_customer_summary(customer.customer_id)
    print_section("Certificate Summary")
    print(f"  Total Certificates: {summary['total_certificates']}")
    print(f"  Error Certificates: {summary['error_certificates']}")
    print(f"  Error Rate: {summary['error_rate']:.1%}")

    if summary['certificates_by_institution']:
        print(f"\n  By Institution:")
        for inst, count in sorted(summary['certificates_by_institution'].items(), key=lambda x: x[1], reverse=True):
            print(f"    {inst}: {count}")

    # Recent certificates
    if summary['recent_certificates']:
        print_section("Recent Certificates")
        for cert in summary['recent_certificates']:
            status_marker = "❌" if cert['status'] == "ERROR" else "✓"
            date_str = cert['date'][:10] if cert['date'] else "No date"
            inst_str = f"[{cert['institution']}]" if cert['institution'] else ""
            print(f"  {status_marker} {date_str} {inst_str} {cert['filename']}")

    # Timeline analysis
    timeline = tracker.get_timeline_analysis(customer.customer_id)
    if 'oldest_certificate' in timeline:
        print_section("Timeline Analysis")
        print(f"  Dated Certificates: {timeline['total_dated_certificates']}")
        print(f"  Oldest: {timeline['oldest_certificate'][:10]}")
        print(f"  Newest: {timeline['newest_certificate'][:10]}")
        print(f"  Time Span: {timeline['time_span_days']} days")

    # Error details
    error_history = tracker.get_error_history(customer.customer_id)
    if error_history:
        print_section("Error Certificates")
        for cert in error_history:
            inst_str = f"[{cert.institution}]" if cert.institution else ""
            print(f"  ❌ {inst_str} {cert.filename}")


def list_customers():
    """List all customers"""
    print_header("ALL CUSTOMERS")

    registry = load_registry()

    print(f"\nTotal: {registry.total_customers} customers\n")

    for customer in sorted(registry.customers, key=lambda c: c.name):
        cert_count = len(registry.get_customer_certificates(customer.customer_id))
        type_marker = "👤" if customer.customer_type == "PERSON" else "🏢"
        print(f"  {type_marker} {customer.name} ({cert_count} certificates)")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Track B Milestone 1 - Customer Registry System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan customer folders
  python main.py --scan /path/to/customer/folders

  # Show statistics
  python main.py --stats

  # List all customers
  python main.py --list

  # Show customer details
  python main.py --customer "EMARLAN"

  # Search certificates
  python main.py --search "BPS"
        """
    )

    parser.add_argument('--scan', metavar='PATH', help='Scan customer folders at specified path')
    parser.add_argument('--stats', action='store_true', help='Show detailed statistics')
    parser.add_argument('--customer', metavar='NAME', help='Show details for specific customer')
    parser.add_argument('--list', action='store_true', help='List all customers')
    parser.add_argument('--search', metavar='TERM', help='Search certificates by filename')

    args = parser.parse_args()

    # Execute command
    if args.scan:
        scan_customers(args.scan)

    elif args.stats:
        show_statistics()

    elif args.customer:
        show_customer_details(args.customer)

    elif args.list:
        list_customers()

    elif args.search:
        registry = load_registry()
        tracker = CertificateTracker(registry)
        results = tracker.search_certificates(args.search)

        print_header(f"SEARCH RESULTS: '{args.search}'")
        print(f"\nFound {len(results)} certificates\n")

        for cert in results:
            customer = tracker.get_customer_by_id(cert.customer_id)
            customer_name = customer.name if customer else "Unknown"
            status_marker = "❌" if cert.has_error_prefix else "✓"
            inst_str = f"[{cert.institution}]" if cert.institution else ""
            print(f"  {status_marker} {customer_name} / {inst_str} {cert.filename}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
