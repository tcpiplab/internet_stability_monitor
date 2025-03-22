"""Context layer for internet stability monitor.

This module provides a high-level interface that coordinates between different models
to manage the overall application state and provide unified access to system, network,
and location information.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from colorama import Fore, Style, init

from internet_stability_monitor.model import (
    CacheModel,
    NetworkModel,
    NetworkInterface,
    NetworkState,
    SystemModel,
    SystemInfo,
    LocationModel,
    LocationInfo,
    IPReputation
)

# Initialize colorama
init(autoreset=True)

@dataclass
class SystemContext:
    """Data class representing the overall system context."""
    last_updated: datetime
    system_info: Optional[Dict] = None
    network_state: Optional[NetworkState] = None
    location_info: Optional[LocationInfo] = None
    ip_reputation: Optional[IPReputation] = None

class MonitorContext:
    """Context class for coordinating between different models."""
    
    def __init__(self, cache_file: Optional[str] = None):
        """Initialize the monitor context.
        
        Args:
            cache_file: Optional path to the cache file
        """
        self.cache = CacheModel(cache_file)
        self.network = NetworkModel()
        self.system = SystemModel()
        self.location = LocationModel(self.cache)
        self._context = SystemContext(last_updated=datetime.now())

    def update_all(self) -> None:
        """Update all models with current information."""
        # Update system information
        self._context.system_info = self.system.get_system_info()
        
        # Update network state
        self.network.update_network_state()
        self._context.network_state = self.network.get_network_state()
        
        # Update location information
        if self._context.network_state and self._context.network_state.external_ip:
            self.location.update_location_info(self._context.network_state.external_ip)
            self._context.location_info = self.location.get_location_info()
            
            # Update IP reputation if we have an API key
            api_key = self.cache.get("abuseipdb_api_key")
            if api_key:
                self.location.update_reputation(api_key=api_key)
                self._context.ip_reputation = self.location.get_reputation()
        
        self._context.last_updated = datetime.now()

    def get_system_summary(self) -> str:
        """Get a comprehensive system summary.
        
        Returns:
            Formatted summary string
        """
        self.update_all()
        summary = []
        
        # System information
        if self._context.system_info:
            summary.append("System Information:")
            summary.append(self.system.get_system_summary())
        
        # Network information
        if self._context.network_state:
            summary.append("\nNetwork Information:")
            summary.append(self.network.get_network_summary())
        
        # Location information
        if self._context.location_info:
            summary.append("\nLocation Information:")
            summary.append(self.location.get_location_summary())
        
        return "\n".join(summary)

    def get_network_status(self) -> Tuple[bool, str]:
        """Get the current network status.
        
        Returns:
            Tuple of (is_connected, status_message)
        """
        self.update_all()
        
        if not self._context.network_state:
            return False, "No network state information available"
            
        if not self._context.network_state.interfaces:
            return False, "No active network interfaces found"
            
        if not self._context.network_state.external_ip:
            return False, "No external IP address available"
            
        return True, "Network is connected and functioning"

    def get_system_health(self) -> Tuple[bool, str]:
        """Get the current system health status.
        
        Returns:
            Tuple of (is_healthy, status_message)
        """
        self.update_all()
        
        if not self._context.system_info:
            return False, "No system information available"
            
        # Check memory usage
        memory_usage = 1 - (self._context.system_info.memory_available / 
                          self._context.system_info.memory_total)
        if memory_usage > 0.9:  # 90% memory usage
            return False, "System memory usage is critically high"
            
        # Check disk space
        for partition in self._context.system_info.disk_partitions:
            if partition['fstype'] != 'tmpfs':  # Skip temporary filesystems
                try:
                    usage = psutil.disk_usage(partition['mountpoint'])
                    if usage.percent > 90:  # 90% disk usage
                        return False, f"Disk usage is critically high on {partition['device']}"
                except Exception:
                    continue
        
        return True, "System is healthy"

    def get_security_status(self) -> Tuple[bool, str]:
        """Get the current security status.
        
        Returns:
            Tuple of (is_secure, status_message)
        """
        self.update_all()
        
        if not self._context.ip_reputation:
            return False, "No IP reputation information available"
            
        if self._context.ip_reputation.abuse_confidence_score > 50:
            return False, "IP has high abuse confidence score"
            
        if self._context.ip_reputation.is_tor:
            return False, "IP is associated with a Tor exit node"
            
        return True, "No security issues detected"

    def get_context(self) -> SystemContext:
        """Get the current system context.
        
        Returns:
            Current SystemContext object
        """
        self.update_all()
        return self._context

    def save_context(self) -> None:
        """Save the current context to cache."""
        self.update_all()
        self.cache.update("last_context_update", self._context.last_updated.isoformat())
        self.cache.save()

    def load_context(self) -> None:
        """Load the last saved context from cache."""
        last_update = self.cache.get("last_context_update")
        if last_update:
            self._context.last_updated = datetime.fromisoformat(last_update)

    def get_location_summary(self) -> str:
        """Get a summary of location information.
        
        Returns:
            Formatted summary string
        """
        self.update_all()
        if not self._context.location_info:
            return "No location information available"
        return self.location.get_location_summary() 