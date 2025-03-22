import psutil
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

@dataclass
class NetworkInterface:
    """Data class representing a network interface."""
    name: str
    is_up: bool
    speed: int
    link_type: str
    addresses: List[str]
    last_updated: datetime

@dataclass
class NetworkState:
    """Data class representing the overall network state."""
    external_ip: Optional[str]
    external_ip_changed: bool
    last_ip_change: Optional[datetime]
    interfaces: Dict[str, NetworkInterface]
    last_updated: datetime

class NetworkModel:
    """Model for managing network state information."""
    
    def __init__(self, ip_history_file: Optional[str] = None):
        """Initialize the network model.
        
        Args:
            ip_history_file: Optional path to the IP history file. If not provided,
                           defaults to /tmp/ip_address.txt
        """
        self.ip_history_file = ip_history_file or '/tmp/ip_address.txt'
        self._state = NetworkState(
            external_ip=None,
            external_ip_changed=False,
            last_ip_change=None,
            interfaces={},
            last_updated=datetime.now()
        )
        self._load_ip_history()

    def _load_ip_history(self) -> None:
        """Load IP history from file."""
        try:
            if Path(self.ip_history_file).exists():
                with open(self.ip_history_file, 'r') as file:
                    timestamp_str, ip = file.read().strip().split(',')
                    self._state.external_ip = ip
                    self._state.last_ip_change = datetime.strptime(
                        timestamp_str, 
                        "%Y-%m-%d_%H-%M-%S"
                    )
        except Exception as e:
            print(f"{Fore.YELLOW}Could not load IP history: {e}{Style.RESET_ALL}")

    def _save_ip_history(self) -> None:
        """Save current IP to history file."""
        try:
            if self._state.external_ip:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                with open(self.ip_history_file, 'w') as file:
                    file.write(f"{timestamp},{self._state.external_ip}")
        except Exception as e:
            print(f"{Fore.RED}Error saving IP history: {e}{Style.RESET_ALL}")

    def _guess_link_type(self, ifname: str) -> str:
        """Guess the link type based on interface name.
        
        Args:
            ifname: Interface name
            
        Returns:
            Guessed link type (Wi-Fi, Ethernet, Loopback, or Unknown)
        """
        pattern_wifi = r"(wi-?fi|wlan|wlp|airport)"
        pattern_eth = r"(eth|en|ethernet)"
        pattern_lo = r"^(lo)$"

        if re.search(pattern_wifi, ifname, re.IGNORECASE):
            return "Wi-Fi"
        elif re.search(pattern_eth, ifname, re.IGNORECASE):
            return "Ethernet"
        elif re.search(pattern_lo, ifname, re.IGNORECASE):
            return "Loopback"
        return "Unknown"

    def update_network_state(self, new_external_ip: Optional[str] = None) -> None:
        """Update the network state with current information.
        
        Args:
            new_external_ip: Optional new external IP address
        """
        # Update external IP if provided
        if new_external_ip and new_external_ip != self._state.external_ip:
            self._state.external_ip_changed = True
            self._state.last_ip_change = datetime.now()
            self._state.external_ip = new_external_ip
            self._save_ip_history()
        else:
            self._state.external_ip_changed = False

        # Update interface information
        self._state.interfaces.clear()
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()

        for ifname, ifinfo in stats.items():
            if ifinfo.is_up and ifinfo.speed > 0:
                interface = NetworkInterface(
                    name=ifname,
                    is_up=ifinfo.isup,
                    speed=ifinfo.speed,
                    link_type=self._guess_link_type(ifname),
                    addresses=[addr.address for addr in addrs.get(ifname, [])],
                    last_updated=datetime.now()
                )
                self._state.interfaces[ifname] = interface

        self._state.last_updated = datetime.now()

    def get_network_state(self) -> NetworkState:
        """Get the current network state.
        
        Returns:
            Current NetworkState object
        """
        return self._state

    def get_active_interfaces(self) -> List[NetworkInterface]:
        """Get list of active network interfaces.
        
        Returns:
            List of active NetworkInterface objects
        """
        return list(self._state.interfaces.values())

    def get_external_ip_info(self) -> Tuple[Optional[str], bool, Optional[datetime]]:
        """Get external IP information.
        
        Returns:
            Tuple of (external_ip, changed, last_change_time)
        """
        return (
            self._state.external_ip,
            self._state.external_ip_changed,
            self._state.last_ip_change
        )

    def get_interface_info(self, ifname: str) -> Optional[NetworkInterface]:
        """Get information about a specific interface.
        
        Args:
            ifname: Name of the interface
            
        Returns:
            NetworkInterface object if found, None otherwise
        """
        return self._state.interfaces.get(ifname)

    def is_interface_active(self, ifname: str) -> bool:
        """Check if an interface is active.
        
        Args:
            ifname: Name of the interface
            
        Returns:
            True if interface is active, False otherwise
        """
        return ifname in self._state.interfaces

    def get_network_summary(self) -> str:
        """Get a human-readable summary of the network state.
        
        Returns:
            Formatted summary string
        """
        summary = []
        
        # External IP information
        if self._state.external_ip:
            summary.append(f"External IP: {self._state.external_ip}")
            if self._state.external_ip_changed:
                summary.append(f"IP changed at: {self._state.last_ip_change}")
        
        # Interface information
        if self._state.interfaces:
            summary.append("\nActive Interfaces:")
            for iface in self._state.interfaces.values():
                summary.append(
                    f"- {iface.name}: {iface.link_type} "
                    f"(Speed: {iface.speed} Mbps)"
                )
        else:
            summary.append("\nNo active network interfaces found.")
        
        return "\n".join(summary) 