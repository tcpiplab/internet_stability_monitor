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
import requests
import platform
import subprocess
from urllib.parse import urlparse, urljoin
from internet_stability_monitor.location import get_public_ip, get_isp_and_location
from internet_stability_monitor.context import MonitorContext

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

class InfrastructureService:
    """Service for monitoring internet infrastructure components."""
    
    def __init__(self):
        """Initialize the infrastructure service."""
        self.ixp_endpoints = {
            "DE-CIX (Frankfurt)": "https://www.de-cix.net/",
            "LINX (London)": "https://www.linx.net/",
            "AMS-IX (Amsterdam)": "https://www.ams-ix.net/",
            "NYIIX (New York)": "https://www.nyiix.net/",
            "HKIX (Hong Kong)": "https://www.hkix.net/",
            "Equinix-IX (Global)": "https://status.equinix.com/"
        }
        
        self.cdn_endpoints = {
            "Cloudflare": "https://www.cloudflare.com/robots.txt",
            "Akamai": "https://developer.akamai.com/",
            "Fastly": "https://www.fastly.com/robots.txt",
            "Amazon CloudFront": "https://d1.awsstatic.com/",
            "Google Cloud CDN": "https://www.google.com/robots.txt",
            "Microsoft Azure CDN": "https://www.microsoft.com/robots.txt"
        }
        
        self.cloud_status_pages = {
            "AWS": "https://health.aws.amazon.com/health/status",
            "Google Cloud": "https://status.cloud.google.com/",
            "Azure": "https://status.azure.com/"
        }
        
        self.ca_endpoints = {
            "DigiCert OCSP": "http://ocsp.digicert.com",
            "DigiCert CRL": "http://crl3.digicert.com/sha2-ev-server-g1.crl",
            "Let's Encrypt OCSP": "http://e6.o.lencr.org",
            "GlobalSign OCSP": "http://ocsp2.globalsign.com/rootr1",
            "Sectigo OCSP": "http://ocsp.sectigo.com",
            "Entrust OCSP": "http://ocsp.entrust.net",
            "IdenTrust OCSP": "http://ocsp.identrust.com"
        }
        
        self.significant_websites = [
            "https://www.google.com",
            "https://www.amazon.com",
            "https://www.facebook.com",
            "https://www.apple.com",
            "https://www.microsoft.com",
            "https://www.reddit.com",
            "https://www.wikipedia.org",
            "https://www.netflix.com",
            "https://www.bbc.com",
            "https://www.nytimes.com",
            "https://www.usa.gov",
            "https://www.canada.ca",
            "https://www.gob.mx",
            "https://www.gov.br",
            "https://www.gov.uk",
            "https://www.gouvernement.fr",
            "https://www.bund.de",
            "https://www.belgium.be",
            "https://www.australia.gov.au",
            "https://www.india.gov.in",
            "https://www.japan.go.jp",
            "https://www.gov.sg"
        ]
        
        self.ntp_servers = {
            "pool.ntp.org": "Pool of NTP servers",
            "time.google.com": "Google's public NTP server",
            "time.apple.com": "Apple's public NTP server",
            "time.windows.com": "Microsoft's public NTP server",
            "time.cloudflare.com": "Cloudflare's public NTP server",
            "time.nist.gov": "NIST's public NTP server",
            "time.iana.org": "IANA's public NTP server"
        }

    def check_ixp(self, name: str, url: str) -> ServiceStatus:
        """Check if an IXP is reachable.
        
        Args:
            name: Name of the IXP
            url: URL to check
            
        Returns:
            ServiceStatus object
        """
        start_time = time.time()
        try:
            response = requests.get(url, timeout=15, verify=True)
            if response.status_code == 200:
                return ServiceStatus(
                    name=name,
                    is_reachable=True,
                    response_time=time.time() - start_time
                )
            return ServiceStatus(
                name=name,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=f"Status code: {response.status_code}"
            )
        except Exception as e:
            return ServiceStatus(
                name=name,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=str(e)
            )

    def check_cdn(self, name: str, url: str) -> ServiceStatus:
        """Check if a CDN is reachable.
        
        Args:
            name: Name of the CDN
            url: URL to check
            
        Returns:
            ServiceStatus object
        """
        start_time = time.time()
        try:
            response = requests.get(url, timeout=20, verify=True)
            if response.status_code in [200, 204]:
                return ServiceStatus(
                    name=name,
                    is_reachable=True,
                    response_time=time.time() - start_time
                )
            return ServiceStatus(
                name=name,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=f"Status code: {response.status_code}"
            )
        except Exception as e:
            return ServiceStatus(
                name=name,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=str(e)
            )

    def check_cloud_status(self, name: str, url: str) -> ServiceStatus:
        """Check cloud provider status page.
        
        Args:
            name: Name of the cloud provider
            url: Status page URL
            
        Returns:
            ServiceStatus object
        """
        start_time = time.time()
        try:
            response = requests.get(url, timeout=30, verify=True)
            if response.status_code == 200:
                # Basic check for status indicators
                if "No recent issues" in response.text or "There are currently no active events" in response.text:
                    return ServiceStatus(
                        name=name,
                        is_reachable=True,
                        response_time=time.time() - start_time
                    )
                return ServiceStatus(
                    name=name,
                    is_reachable=True,
                    response_time=time.time() - start_time,
                    error="Issues detected on status page"
                )
            return ServiceStatus(
                name=name,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=f"Status code: {response.status_code}"
            )
        except Exception as e:
            return ServiceStatus(
                name=name,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=str(e)
            )

    def check_ca_endpoint(self, name: str, url: str) -> ServiceStatus:
        """Check CA OCSP/CRL endpoint.
        
        Args:
            name: Name of the CA endpoint
            url: Endpoint URL
            
        Returns:
            ServiceStatus object
        """
        start_time = time.time()
        try:
            if "Let's Encrypt" in name:
                response = requests.get(url, timeout=30, verify=True)
            else:
                response = requests.head(url, timeout=10, verify=True)
            
            if response.status_code == 200:
                return ServiceStatus(
                    name=name,
                    is_reachable=True,
                    response_time=time.time() - start_time
                )
            return ServiceStatus(
                name=name,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=f"Status code: {response.status_code}"
            )
        except Exception as e:
            return ServiceStatus(
                name=name,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=str(e)
            )

    def check_website(self, url: str) -> ServiceStatus:
        """Check if a website is reachable.
        
        Args:
            url: Website URL
            
        Returns:
            ServiceStatus object
        """
        start_time = time.time()
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            robots_url = urljoin(base_url, "/robots.txt")
            
            response = requests.get(robots_url, timeout=15, verify=True)
            if response.status_code == 200:
                return ServiceStatus(
                    name=url,
                    is_reachable=True,
                    response_time=time.time() - start_time
                )
            
            # Try root URL if robots.txt not found
            response = requests.get(url, timeout=15, verify=True)
            if response.status_code == 200:
                return ServiceStatus(
                    name=url,
                    is_reachable=True,
                    response_time=time.time() - start_time
                )
            
            return ServiceStatus(
                name=url,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=f"Status code: {response.status_code}"
            )
        except Exception as e:
            return ServiceStatus(
                name=url,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=str(e)
            )

    def check_ntp_server(self, name: str) -> ServiceStatus:
        """Check if an NTP server is reachable.
        
        Args:
            name: Name of the NTP server
            
        Returns:
            ServiceStatus object
        """
        start_time = time.time()
        try:
            if platform.system() in ["Darwin", "Linux"]:
                result = subprocess.run(
                    ['ntpdate', '-q', name],
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
                # Windows fallback using socket
                socket.create_connection((name, 123), timeout=10)
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

class NetworkDiagnosticsService:
    """Service for network diagnostics and speed testing."""
    
    def __init__(self):
        """Initialize the network diagnostics service."""
        self.platform = platform.system()

    def run_speed_test(self) -> Optional[Dict[str, str]]:
        """Run network speed test (macOS only).
        
        Returns:
            Dictionary with speed test results or None if not on macOS
        """
        if self.platform != "Darwin":
            return None
            
        try:
            process = subprocess.run(
                ["networkQuality", "-p", "-s"],
                capture_output=True,
                text=True
            )
            
            if process.stdout:
                return self._parse_network_quality_output(process.stdout)
            return None
        except FileNotFoundError:
            return None
        except Exception as e:
            return None

    def _parse_network_quality_output(self, output: str) -> Dict[str, str]:
        """Parse networkQuality command output.
        
        Args:
            output: Raw output from networkQuality command
            
        Returns:
            Dictionary with parsed results
        """
        summary = {}
        for line in output.splitlines():
            if "Uplink capacity" in line:
                summary['uplink_capacity'] = line.split(': ')[1]
            elif "Downlink capacity" in line:
                summary['downlink_capacity'] = line.split(': ')[1]
            elif "Uplink Responsiveness" in line:
                summary['uplink_responsiveness'] = line.split(': ')[1]
            elif "Downlink Responsiveness" in line:
                summary['downlink_responsiveness'] = line.split(': ')[1]
            elif "Idle Latency" in line:
                summary['idle_latency'] = line.split(': ')[1]
        return summary

    def ping(self, target: str, count: int = 4) -> ServiceStatus:
        """Ping a target host.
        
        Args:
            target: Host to ping
            count: Number of pings to send
            
        Returns:
            ServiceStatus object
        """
        start_time = time.time()
        try:
            result = subprocess.run(
                ["ping", "-c", str(count), target],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Extract average latency
            for line in result.stdout.splitlines():
                if "avg" in line:
                    avg_latency = line.split("/")[4]
                    return ServiceStatus(
                        name=target,
                        is_reachable=True,
                        response_time=time.time() - start_time,
                        error=f"Average latency: {avg_latency} ms"
                    )
            
            return ServiceStatus(
                name=target,
                is_reachable=True,
                response_time=time.time() - start_time,
                error="Ping completed but latency could not be determined"
            )
        except subprocess.CalledProcessError as e:
            return ServiceStatus(
                name=target,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=str(e)
            )
        except Exception as e:
            return ServiceStatus(
                name=target,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=str(e)
            )

    def traceroute(self, target: str) -> ServiceStatus:
        """Run traceroute to a target host.
        
        Args:
            target: Host to trace
            
        Returns:
            ServiceStatus object
        """
        start_time = time.time()
        try:
            result = subprocess.run(
                ["traceroute", target],
                capture_output=True,
                text=True,
                check=True
            )
            return ServiceStatus(
                name=target,
                is_reachable=True,
                response_time=time.time() - start_time,
                error=result.stdout
            )
        except subprocess.CalledProcessError as e:
            return ServiceStatus(
                name=target,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=str(e)
            )
        except Exception as e:
            return ServiceStatus(
                name=target,
                is_reachable=False,
                response_time=time.time() - start_time,
                error=str(e)
            )

    def check_layer_three_network(self) -> ServiceStatus:
        """Check Layer 3 network connectivity.
        
        Returns:
            ServiceStatus object
        """
        start_time = time.time()
        try:
            socket.create_connection(("8.8.8.8", 53))
            return ServiceStatus(
                name="Layer 3 Network",
                is_reachable=True,
                response_time=time.time() - start_time
            )
        except OSError as e:
            return ServiceStatus(
                name="Layer 3 Network",
                is_reachable=False,
                response_time=time.time() - start_time,
                error=str(e)
            )

class SystemService:
    """Service for system-level checks and monitoring."""
    
    def __init__(self):
        """Initialize the system service."""
        self.platform = platform.system()

    def check_ollama_status(self) -> ServiceStatus:
        """Check if Ollama is installed and running.
        
        Returns:
            ServiceStatus object
        """
        start_time = time.time()
        try:
            # Check if Ollama is installed
            if self.platform == "Darwin":
                result = subprocess.run(
                    ['which', 'ollama'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                if result.returncode != 0:
                    return ServiceStatus(
                        name="Ollama",
                        is_reachable=False,
                        response_time=time.time() - start_time,
                        error="Ollama is not installed"
                    )
            
            # Check if Ollama service is running
            if self.platform == "Darwin":
                result = subprocess.run(
                    ['ps', 'aux'],
                    stdout=subprocess.PIPE,
                    text=True
                )
                if 'ollama' not in result.stdout:
                    return ServiceStatus(
                        name="Ollama",
                        is_reachable=False,
                        response_time=time.time() - start_time,
                        error="Ollama service is not running"
                    )
            
            # Try to connect to Ollama API
            try:
                response = requests.get('http://localhost:11434/api/version', timeout=5)
                if response.status_code == 200:
                    return ServiceStatus(
                        name="Ollama",
                        is_reachable=True,
                        response_time=time.time() - start_time,
                        error=f"Version: {response.json().get('version', 'unknown')}"
                    )
            except Exception as e:
                return ServiceStatus(
                    name="Ollama",
                    is_reachable=False,
                    response_time=time.time() - start_time,
                    error=f"API connection failed: {str(e)}"
                )
            
            return ServiceStatus(
                name="Ollama",
                is_reachable=False,
                response_time=time.time() - start_time,
                error="Ollama service is not responding"
            )
        except Exception as e:
            return ServiceStatus(
                name="Ollama",
                is_reachable=False,
                response_time=time.time() - start_time,
                error=str(e)
            )

class LocationService:
    """Service for location-related operations."""
    
    def __init__(self, context: MonitorContext):
        """Initialize the location service.
        
        Args:
            context: MonitorContext instance
        """
        self.context = context

    def check_location_services(self) -> ServiceStatus:
        """Check location services and IP information.
        
        Returns:
            ServiceStatus object
        """
        start_time = time.time()
        try:
            # Update location info
            self.context.location.update_location_info()
            location_info = self.context.location.get_location_info()
            
            if not location_info.ip:
                return ServiceStatus(
                    name="Location Services",
                    is_reachable=False,
                    response_time=time.time() - start_time,
                    error="Could not determine public IP address"
                )
            
            # Check if we have basic location information
            if not location_info.country_code:
                return ServiceStatus(
                    name="Location Services",
                    is_reachable=False,
                    response_time=time.time() - start_time,
                    error="Could not determine location information"
                )
            
            return ServiceStatus(
                name="Location Services",
                is_reachable=True,
                response_time=time.time() - start_time,
                error=f"IP: {location_info.ip}, Location: {location_info.city}, {location_info.country}"
            )
        except Exception as e:
            return ServiceStatus(
                name="Location Services",
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
        self.infrastructure = InfrastructureService()
        self.network_diagnostics = NetworkDiagnosticsService()
        self.system = SystemService()
        self.location = LocationService(context)

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
            "whois_servers": [],
            "ixps": [],
            "cdns": [],
            "cloud_providers": [],
            "ca_endpoints": [],
            "websites": [],
            "ntp_servers": [],
            "system_services": [],
            "location_services": []
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
        
        # Check IXPs
        for name, url in self.infrastructure.ixp_endpoints.items():
            results["ixps"].append(self.infrastructure.check_ixp(name, url))
        
        # Check CDNs
        for name, url in self.infrastructure.cdn_endpoints.items():
            results["cdns"].append(self.infrastructure.check_cdn(name, url))
        
        # Check cloud providers
        for name, url in self.infrastructure.cloud_status_pages.items():
            results["cloud_providers"].append(self.infrastructure.check_cloud_status(name, url))
        
        # Check CA endpoints
        for name, url in self.infrastructure.ca_endpoints.items():
            results["ca_endpoints"].append(self.infrastructure.check_ca_endpoint(name, url))
        
        # Check significant websites
        for url in self.infrastructure.significant_websites:
            results["websites"].append(self.infrastructure.check_website(url))
        
        # Check NTP servers
        for name in self.infrastructure.ntp_servers:
            results["ntp_servers"].append(self.infrastructure.check_ntp_server(name))
        
        # Check system services
        results["system_services"].append(self.system.check_ollama_status())
        
        # Check location services
        # results["location_services"].append(self.location.check_location_services())
        
        # Add location check using existing functionality
        try:
            public_ip = get_public_ip()
            if public_ip:
                ip_data = get_isp_and_location(public_ip)
                
                isp = ip_data.get("org", "Unknown ISP")
                isp = f"B.G.P Autonomous System Number {isp}"
                city = ip_data.get("city", "Unknown city")
                region = ip_data.get("region", "Unknown region")
                country = ip_data.get("country", "Unknown country")
                
                results['location'] = {
                    'status': 'ok',
                    'ip': public_ip,
                    'city': city,
                    'region': region,
                    'country': country,
                    'isp': isp,
                    'full_location': f"{city}, {region}, {country}, downstream from the {isp} network"
                }
            else:
                results['location'] = {
                    'status': 'error',
                    'message': 'Could not determine IP address'
                }
        except Exception as e:
            results['location'] = {
                'status': 'error',
                'message': f'Failed to get location information: {str(e)}'
            }

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
        
        # IXPs
        summary.append("\nInternet Exchange Points:")
        for status in results["ixps"]:
            if status.is_reachable:
                summary.append(f"✓ {status.name} ({status.response_time:.2f}s)")
            else:
                summary.append(f"✗ {status.name}: {status.error}")
        
        # CDNs
        summary.append("\nContent Delivery Networks:")
        for status in results["cdns"]:
            if status.is_reachable:
                summary.append(f"✓ {status.name} ({status.response_time:.2f}s)")
            else:
                summary.append(f"✗ {status.name}: {status.error}")
        
        # Cloud Providers
        summary.append("\nCloud Providers:")
        for status in results["cloud_providers"]:
            if status.is_reachable:
                summary.append(f"✓ {status.name} ({status.response_time:.2f}s)")
            else:
                summary.append(f"✗ {status.name}: {status.error}")
        
        # CA Endpoints
        summary.append("\nCertificate Authority Endpoints:")
        for status in results["ca_endpoints"]:
            if status.is_reachable:
                summary.append(f"✓ {status.name} ({status.response_time:.2f}s)")
            else:
                summary.append(f"✗ {status.name}: {status.error}")
        
        # Websites
        summary.append("\nSignificant Websites:")
        for status in results["websites"]:
            if status.is_reachable:
                summary.append(f"✓ {status.name} ({status.response_time:.2f}s)")
            else:
                summary.append(f"✗ {status.name}: {status.error}")
        
        # NTP Servers
        summary.append("\nNTP Servers:")
        for status in results["ntp_servers"]:
            if status.is_reachable:
                summary.append(f"✓ {status.name} ({status.response_time:.2f}s)")
            else:
                summary.append(f"✗ {status.name}: {status.error}")
        
        # System Services
        summary.append("\nSystem Services:")
        for status in results["system_services"]:
            if status.is_reachable:
                summary.append(f"✓ {status.name} ({status.response_time:.2f}s)")
            else:
                summary.append(f"✗ {status.name}: {status.error}")
        
        # Location Services
        summary.append("\nLocation Services:")
        for status in results["location_services"]:
            if status.is_reachable:
                summary.append(f"✓ {status.name} ({status.response_time:.2f}s)")
            else:
                summary.append(f"✗ {status.name}: {status.error}")
        
        return "\n".join(summary) 