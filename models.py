"""
Track B - Milestone 1: Data Models
Customer and Certificate data structures for the notary document system.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class CustomerType(str, Enum):
    """Type of customer entity"""
    PERSON = "PERSON"
    COMPANY = "COMPANY"


class CertificateStatus(str, Enum):
    """Certificate validation status"""
    OK = "OK"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class Customer(BaseModel):
    """
    Represents a customer (person or company) with their folder structure.
    Each folder corresponds to one customer.
    """
    customer_id: str = Field(..., description="Unique identifier for the customer")
    name: str = Field(..., description="Customer name (person or company)")
    customer_type: CustomerType = Field(..., description="Type: PERSON or COMPANY")
    folder_path: str = Field(..., description="Absolute path to customer folder")
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


class CertificateRecord(BaseModel):
    """
    Represents a single certificate in a customer's history.
    ERROR prefix in filename indicates issues identified by the notary.
    """
    certificate_id: str = Field(..., description="Unique certificate identifier")
    customer_id: str = Field(..., description="Related customer ID")
    certificate_type: Optional[str] = Field(None, description="Type of certificate (e.g., personería, firma)")
    institution: Optional[str] = Field(None, description="Target institution (BPS, MSP, Abitab, etc.)")
    date: Optional[datetime] = Field(None, description="Certificate creation/issue date")
    status: CertificateStatus = Field(CertificateStatus.UNKNOWN, description="OK, ERROR, or UNKNOWN")
    source_files: List[str] = Field(default_factory=list, description="List of source file paths")
    filename: str = Field(..., description="Original certificate filename")
    file_path: str = Field(..., description="Full path to certificate file")
    has_error_prefix: bool = Field(default=False, description="Whether filename starts with ERROR")
    indexed_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


class CustomerRegistry(BaseModel):
    """
    Complete registry of all customers and their certificates.
    This is the structured output of Milestone 1.
    """
    customers: List[Customer] = Field(default_factory=list)
    certificates: List[CertificateRecord] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)
    total_customers: int = Field(default=0)
    total_certificates: int = Field(default=0)

    def add_customer(self, customer: Customer) -> None:
        """Add a customer to the registry"""
        self.customers.append(customer)
        self.total_customers = len(self.customers)
        self.last_updated = datetime.now()

    def add_certificate(self, certificate: CertificateRecord) -> None:
        """Add a certificate to the registry"""
        self.certificates.append(certificate)
        self.total_certificates = len(self.certificates)
        self.last_updated = datetime.now()

    def get_customer_certificates(self, customer_id: str) -> List[CertificateRecord]:
        """Get all certificates for a specific customer"""
        return [cert for cert in self.certificates if cert.customer_id == customer_id]

    def get_error_certificates(self) -> List[CertificateRecord]:
        """Get all certificates marked with ERROR"""
        return [cert for cert in self.certificates if cert.has_error_prefix or cert.status == CertificateStatus.ERROR]
