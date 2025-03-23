import requests
from datetime import datetime
from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass, field
from colorama import Fore, Style, init
import os

# Initialize colorama
init(autoreset=True)

@dataclass
class LocationInfo:
    """Location information data class."""
    
    ip: str
    city: str = "Unknown"
    region: str = "Unknown"
    country: str = "Unknown"
    country_code: str = "Unknown"
    org: str = "Unknown"
    loc: str = "Unknown"
    timezone: str = "Unknown"
    last_updated: datetime = field(default_factory=datetime.now)
    
    def __str__(self) -> str:
        """Get string representation of location info."""
        if self.ip == "Unknown":
            return "No location information available"
            
        parts = []
        if self.city != "Unknown":
            parts.append(self.city)
        if self.region != "Unknown":
            parts.append(self.region)
        if self.country != "Unknown":
            parts.append(self.country)
            
        location = ", ".join(parts) if parts else "Unknown location"
        
        if self.org != "Unknown":
            return f"{location}, downstream from the {self.org} network"
        else:
            return location

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

    def _get_location_info(self, ip: str) -> Optional[Dict[str, Any]]:
        """Get location information for an IP address.
        
        Args:
            ip: IP address to look up
            
        Returns:
            Location information dictionary or None if lookup fails
        """
        try:
            # Get API token from environment variable
            token = os.environ.get("IPINFOIO_API_KEY")
            if not token:
                print(f"{Fore.YELLOW}Warning: IPINFOIO_API_KEY environment variable not set{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Please set the environment variable with your ipinfo.io API key:{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}  export IPINFOIO_API_KEY=your_api_key_here{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}You can get a free API key at https://ipinfo.io/{Style.RESET_ALL}")
                return None
                
            # Get location data from ipinfo.io
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"https://ipinfo.io/{ip}", headers=headers, verify=True)
            if response.status_code == 200:
                data = response.json()
                return {
                    "city": data.get("city", "Unknown"),
                    "region": data.get("region", "Unknown"),
                    "country": data.get("country", "Unknown"),
                    "org": data.get("org", "Unknown"),
                    "loc": data.get("loc", "Unknown"),
                    "timezone": data.get("timezone", "Unknown")
                }
            else:
                print(f"{Fore.RED}Warning: Failed to get location info for IP {ip}: {response.status_code}{Style.RESET_ALL}")
                return None
                
        except Exception as e:
            print(f"{Fore.RED}Warning: Error getting location info: {e}{Style.RESET_ALL}")
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
            org=location_data.get("org", ""),
            loc=location_data.get("loc", ""),
            timezone=location_data.get("timezone", ""),
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
            summary.append(f"ISP: {self._location_info.org}")
            if self._location_info.country_code:
                summary.append(f"Country Code: {self._location_info.country_code}")
            summary.append(f"Timezone: {self._location_info.timezone}")
            summary.append(f"Coordinates: {self._location_info.loc}")
        
        # Reputation information if available
        if self._reputation:
            summary.append("\nIP Reputation:")
            summary.append(f"Abuse Confidence Score: {self._reputation.abuse_confidence_score} (High risk if > 50)")
            summary.append(f"Usage Type: {self._reputation.usage_type}")
            if self._reputation.is_tor:
                summary.append("Warning: This IP is associated with a Tor exit node")
        
        return "\n".join(summary) 