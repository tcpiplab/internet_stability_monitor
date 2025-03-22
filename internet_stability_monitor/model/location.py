import requests
from datetime import datetime
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

@dataclass
class LocationInfo:
    """Data class representing location information."""
    ip: str
    country_code: str
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    isp: Optional[str] = None
    asn: Optional[str] = None
    organization: Optional[str] = None
    last_updated: datetime = datetime.now()

@dataclass
class IPReputation:
    """Data class representing IP reputation information."""
    ip: str
    is_public: bool
    abuse_confidence_score: int
    country_code: str
    usage_type: str
    is_tor: bool
    is_proxy: bool
    is_datacenter: bool
    is_vpn: bool
    reports: List[Dict[str, str]]
    last_updated: datetime = datetime.now()

class LocationModel:
    """Model for managing location and IP information."""
    
    def __init__(self, cache=None):
        """Initialize the location model.
        
        Args:
            cache: Optional CacheModel instance
        """
        self._location_info = LocationInfo(
            ip="",
            country_code="",
            last_updated=datetime.now()
        )
        self._reputation: Optional[IPReputation] = None
        self.cache = cache

    def _get_public_ip(self) -> str:
        """Get the public IP address.
        
        Returns:
            Public IP address
        """
        try:
            response = requests.get("https://api.ipify.org?format=json", verify=True)
            response.raise_for_status()
            return response.json().get("ip")
        except Exception as e:
            print(f"{Fore.RED}Error getting public IP: {e}{Style.RESET_ALL}")
            return ""

    def _get_location_info(self, ip: str) -> Optional[Dict]:
        """Get location information for an IP address.
        
        Args:
            ip: IP address to look up
            
        Returns:
            Dictionary containing location information
        """
        try:
            response = requests.get(
                f"https://ipinfo.io/{ip}/json",
                verify=True
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"{Fore.RED}Error getting location info: {e}{Style.RESET_ALL}")
            return None

    def _get_ip_reputation(self, ip: str, api_key: str) -> Optional[Dict]:
        """Get IP reputation information from AbuseIPDB.
        
        Args:
            ip: IP address to check
            api_key: AbuseIPDB API key
            
        Returns:
            Dictionary containing reputation information
        """
        try:
            url = 'https://api.abuseipdb.com/api/v2/check'
            headers = {
                'Accept': 'application/json',
                'Key': api_key
            }
            params = {
                'ipAddress': ip,
                'maxAgeInDays': '90',
                'verbose': 'true'
            }
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json().get("data")
        except Exception as e:
            print(f"{Fore.RED}Error getting IP reputation: {e}{Style.RESET_ALL}")
            return None

    def update_location_info(self, ip: Optional[str] = None) -> None:
        """Update location information.
        
        Args:
            ip: Optional IP address to look up. If not provided, gets public IP.
        """
        if not ip:
            ip = self._get_public_ip()
        
        if not ip:
            return
            
        location_data = self._get_location_info(ip)
        if not location_data:
            return
            
        # Parse location data
        loc = location_data.get("loc", "0,0").split(",")
        self._location_info = LocationInfo(
            ip=ip,
            city=location_data.get("city", ""),
            region=location_data.get("region", ""),
            country=location_data.get("country", ""),
            country_code=location_data.get("country", ""),
            isp=location_data.get("org", ""),
            asn=location_data.get("asn", ""),
            latitude=float(loc[0]) if len(loc) > 0 else 0.0,
            longitude=float(loc[1]) if len(loc) > 1 else 0.0,
            timezone=location_data.get("timezone", ""),
            organization=location_data.get("org", ""),
            last_updated=datetime.now()
        )

    def update_reputation(self, ip: Optional[str] = None, api_key: Optional[str] = None) -> None:
        """Update IP reputation information.
        
        Args:
            ip: Optional IP address to check. If not provided, uses current IP.
            api_key: Optional AbuseIPDB API key.
        """
        if not ip:
            ip = self._location_info.ip
            
        if not ip or not api_key:
            return
            
        reputation_data = self._get_ip_reputation(ip, api_key)
        if not reputation_data:
            return
            
        self._reputation = IPReputation(
            ip=ip,
            is_public=reputation_data.get("isPublic", False),
            abuse_confidence_score=reputation_data.get("abuseConfidenceScore", 0),
            country_code=reputation_data.get("countryCode", ""),
            usage_type=reputation_data.get("usageType", "Unknown"),
            is_tor=reputation_data.get("isTor", False),
            is_proxy=reputation_data.get("isProxy", False),
            is_datacenter=reputation_data.get("isDatacenter", False),
            is_vpn=reputation_data.get("isVpn", False),
            reports=reputation_data.get("reports", []),
            last_updated=datetime.now()
        )

    def get_location_info(self) -> LocationInfo:
        """Get current location information.
        
        Returns:
            Current LocationInfo object
        """
        return self._location_info

    def get_reputation(self) -> Optional[IPReputation]:
        """Get current IP reputation information.
        
        Returns:
            Current IPReputation object if available, None otherwise
        """
        return self._reputation

    def get_location_summary(self) -> str:
        """Get a human-readable summary of the location information.
        
        Returns:
            Formatted summary string
        """
        summary = []
        
        # Location information
        if self._location_info.ip:
            summary.append(f"IP Address: {self._location_info.ip}")
            summary.append(f"Location: {self._location_info.city}, {self._location_info.region}, {self._location_info.country}")
            summary.append(f"ISP: {self._location_info.isp}")
            if self._location_info.asn:
                summary.append(f"ASN: {self._location_info.asn}")
            summary.append(f"Timezone: {self._location_info.timezone}")
            summary.append(f"Coordinates: {self._location_info.latitude}, {self._location_info.longitude}")
        
        # Reputation information if available
        if self._reputation:
            summary.append("\nIP Reputation:")
            summary.append(f"Abuse Confidence Score: {self._reputation.abuse_confidence_score} (High risk if > 50)")
            summary.append(f"Usage Type: {self._reputation.usage_type}")
            if self._reputation.is_tor:
                summary.append("Warning: This IP is associated with a Tor exit node")
        
        return "\n".join(summary) 