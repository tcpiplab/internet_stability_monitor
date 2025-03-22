"""Service layer for internet stability monitor.

This module provides services for monitoring and interacting with various internet
infrastructure components like DNS, SMTP, WHOIS, and other critical services.
"""

import socket
import dns.resolver
import whois
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from colorama import Fore, Style, init

from ..context import MonitorContext

# Initialize colorama
init(autoreset=True)

@dataclass
class ServiceStatus:
    """Data class representing the status of a service."""
    name: str
    is_reachable: bool
    response_time: float
    error: Optional[str] = None
    last_checked: datetime = datetime.now()

class DNSService:
    """Service for DNS-related operations."""
    
    def __init__(self):
        """Initialize the DNS service."""
        self.resolvers = {
            "Google Public DNS - Primary": "8.8.8.8",
            "Google Public DNS - Secondary": "8.8.4.4",
            "Cloudflare DNS - Primary": "1.1.1.1",
            "Cloudflare DNS - Secondary": "1.0.0.1",
            "OpenDNS - Primary": "208.67.222.222",
            "OpenDNS - Secondary": "208.67.220.220",
            "Quad9 - Primary": "9.9.9.9",
            "Quad9 - Secondary": "149.112.112.112",
            "Comodo Secure DNS - Primary": "8.26.56.26",
            "Comodo Secure DNS - Secondary": "8.20.247.20"
        }
        
        self.root_servers = {
            "A": "198.41.0.4",
            "B": "199.9.14.201",
            "C": "192.33.4.12",
            "D": "199.7.91.13",
            "E": "192.203.230.10",
            "F": "192.5.5.241",
            "G": "192.112.36.4",
            "H": "198.97.190.53",
            "I": "192.36.148.17",
            "J": "192.58.128.30",
            "K": "193.0.14.129",
            "L": "199.7.83.42",
            "M": "202.12.27.33"
        }

    def check_resolver(self, name: str, ip: str) -> ServiceStatus:
        """Check if a DNS resolver is reachable.
        
        Args:
            name: Name of the resolver
            ip: IP address of the resolver
            
        Returns:
            ServiceStatus object
        """
        start_time = time.time()
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 5
            resolver.lifetime = 5
            resolver.nameservers = [ip]
            resolver.resolve("example.com", "A")
            return ServiceStatus(
                name=name,
                is_reachable=True,
                response_time=time.time() - start_time
            )
        except Exception as e:
            return ServiceStatus(
                name=name,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=str(e)
            )

    def check_root_server(self, name: str, ip: str) -> ServiceStatus:
        """Check if a DNS root server is reachable.
        
        Args:
            name: Name of the root server
            ip: IP address of the root server
            
        Returns:
            ServiceStatus object
        """
        start_time = time.time()
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 5
            resolver.lifetime = 5
            resolver.nameservers = [ip]
            resolver.resolve(".", "NS")
            return ServiceStatus(
                name=name,
                is_reachable=True,
                response_time=time.time() - start_time
            )
        except Exception as e:
            return ServiceStatus(
                name=name,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=str(e)
            )

class EmailService:
    """Service for email-related operations."""
    
    def __init__(self):
        """Initialize the email service."""
        self.smtp_servers = {
            "Gmail": ("smtp.gmail.com", 587),
            "Outlook/O365": ("smtp.office365.com", 587),
            "Yahoo": ("smtp.mail.yahoo.com", 587),
            "iCloud Mail": ("smtp.mail.me.com", 587),
            "AOL Mail": ("smtp.aol.com", 587),
            "Zoho Mail": ("smtp.zoho.com", 587),
            "Mail.com": ("smtp.mail.com", 587),
            "GMX Mail": ("smtp.gmx.com", 587),
            "Fastmail": ("smtp.fastmail.com", 587)
        }
        
        self.imap_servers = {
            "Gmail": ("imap.gmail.com", 993),
            "Outlook/O365": ("outlook.office365.com", 993),
            "Yahoo": ("imap.mail.yahoo.com", 993),
            "iCloud Mail": ("imap.mail.me.com", 993),
            "AOL Mail": ("imap.aol.com", 993),
            "Zoho Mail": ("imap.zoho.com", 993),
            "Mail.com": ("imap.mail.com", 993),
            "GMX Mail": ("imap.gmx.com", 993),
            "Fastmail": ("imap.fastmail.com", 993)
        }

    def check_smtp_server(self, name: str, server_info: Tuple[str, int]) -> ServiceStatus:
        """Check if an SMTP server is reachable.
        
        Args:
            name: Name of the SMTP server
            server_info: Tuple of (host, port)
            
        Returns:
            ServiceStatus object
        """
        start_time = time.time()
        host, port = server_info
        try:
            with socket.create_connection((host, port), timeout=10) as sock:
                return ServiceStatus(
                    name=name,
                    is_reachable=True,
                    response_time=time.time() - start_time
                )
        except Exception as e:
            return ServiceStatus(
                name=name,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=str(e)
            )

    def check_imap_server(self, name: str, server_info: Tuple[str, int]) -> ServiceStatus:
        """Check if an IMAP server is reachable.
        
        Args:
            name: Name of the IMAP server
            server_info: Tuple of (host, port)
            
        Returns:
            ServiceStatus object
        """
        start_time = time.time()
        host, port = server_info
        try:
            with socket.create_connection((host, port), timeout=10) as sock:
                return ServiceStatus(
                    name=name,
                    is_reachable=True,
                    response_time=time.time() - start_time
                )
        except Exception as e:
            return ServiceStatus(
                name=name,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=str(e)
            )

class WHOISService:
    """Service for WHOIS-related operations."""
    
    def __init__(self):
        """Initialize the WHOIS service."""
        self.servers = {
            "whois.apnic.net": ("APNIC WHOIS server for IP address and AS number allocation in the Asia-Pacific region", "202.12.29.140"),
            "whois.ripe.net": ("RIPE NCC WHOIS server for European IP addresses and AS number registrations", "193.0.6.135"),
            "whois.arin.net": ("ARIN WHOIS server for North American IP address and ASN allocations", "199.212.0.43"),
            "whois.afrinic.net": ("AFRINIC WHOIS server for African IP address space and AS number management", "196.216.2.2"),
            "whois.lacnic.net": ("LACNIC WHOIS server for Latin American and Caribbean IP address registrations", "200.3.14.10"),
            "whois.iana.org": ("IANA WHOIS server for the root zone database", "192.0.32.59")
        }

    def check_whois_server(self, name: str, server_info: Tuple[str, str]) -> ServiceStatus:
        """Check if a WHOIS server is reachable.
        
        Args:
            name: Name of the WHOIS server
            server_info: Tuple of (description, ip)
            
        Returns:
            ServiceStatus object
        """
        start_time = time.time()
        try:
            if platform.system() in ["Darwin", "Linux"]:
                result = subprocess.run(
                    ['whois', '-h', name, server_info[1]],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10
                )
                if result.returncode == 0:
                    return ServiceStatus(
                        name=name,
                        is_reachable=True,
                        response_time=time.time() - start_time
                    )
            else:
                # Windows fallback using python-whois
                whois.whois(server_info[1])
                return ServiceStatus(
                    name=name,
                    is_reachable=True,
                    response_time=time.time() - start_time
                )
        except Exception as e:
            return ServiceStatus(
                name=name,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=str(e)
            )

class MonitorService:
    """Main service for coordinating all monitoring operations."""
    
    def __init__(self, context: MonitorContext):
        """Initialize the monitor service.
        
        Args:
            context: MonitorContext instance
        """
        self.context = context
        self.dns = DNSService()
        self.email = EmailService()
        self.whois = WHOISService()

    def check_all_services(self) -> Dict[str, List[ServiceStatus]]:
        """Check all services and return their status.
        
        Returns:
            Dictionary mapping service types to lists of ServiceStatus objects
        """
        results = {
            "dns_resolvers": [],
            "dns_root_servers": [],
            "smtp_servers": [],
            "imap_servers": [],
            "whois_servers": []
        }
        
        # Check DNS resolvers
        for name, ip in self.dns.resolvers.items():
            results["dns_resolvers"].append(self.dns.check_resolver(name, ip))
        
        # Check DNS root servers
        for name, ip in self.dns.root_servers.items():
            results["dns_root_servers"].append(self.dns.check_root_server(name, ip))
        
        # Check SMTP servers
        for name, server_info in self.email.smtp_servers.items():
            results["smtp_servers"].append(self.email.check_smtp_server(name, server_info))
        
        # Check IMAP servers
        for name, server_info in self.email.imap_servers.items():
            results["imap_servers"].append(self.email.check_imap_server(name, server_info))
        
        # Check WHOIS servers
        for name, server_info in self.whois.servers.items():
            results["whois_servers"].append(self.whois.check_whois_server(name, server_info))
        
        return results

    def get_service_summary(self) -> str:
        """Get a human-readable summary of all service statuses.
        
        Returns:
            Formatted summary string
        """
        results = self.check_all_services()
        summary = []
        
        # DNS Resolvers
        summary.append("DNS Resolvers:")
        for status in results["dns_resolvers"]:
            if status.is_reachable:
                summary.append(f"✓ {status.name} ({status.response_time:.2f}s)")
            else:
                summary.append(f"✗ {status.name}: {status.error}")
        
        # DNS Root Servers
        summary.append("\nDNS Root Servers:")
        for status in results["dns_root_servers"]:
            if status.is_reachable:
                summary.append(f"✓ {status.name} ({status.response_time:.2f}s)")
            else:
                summary.append(f"✗ {status.name}: {status.error}")
        
        # SMTP Servers
        summary.append("\nSMTP Servers:")
        for status in results["smtp_servers"]:
            if status.is_reachable:
                summary.append(f"✓ {status.name} ({status.response_time:.2f}s)")
            else:
                summary.append(f"✗ {status.name}: {status.error}")
        
        # IMAP Servers
        summary.append("\nIMAP Servers:")
        for status in results["imap_servers"]:
            if status.is_reachable:
                summary.append(f"✓ {status.name} ({status.response_time:.2f}s)")
            else:
                summary.append(f"✗ {status.name}: {status.error}")
        
        # WHOIS Servers
        summary.append("\nWHOIS Servers:")
        for status in results["whois_servers"]:
            if status.is_reachable:
                summary.append(f"✓ {status.name} ({status.response_time:.2f}s)")
            else:
                summary.append(f"✗ {status.name}: {status.error}")
        
        return "\n".join(summary) 