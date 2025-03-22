"""Service package for internet stability monitor.

This package provides services for monitoring and interacting with various internet
infrastructure components like DNS, SMTP, WHOIS, and other critical services.
"""

from .service import (
    MonitorService,
    DNSService,
    EmailService,
    WHOISService,
    ServiceStatus
)

__all__ = [
    'MonitorService',
    'DNSService',
    'EmailService',
    'WHOISService',
    'ServiceStatus'
] 