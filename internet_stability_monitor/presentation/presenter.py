"""Presentation layer for internet stability monitor.

This module handles the display of monitoring data to users, providing both
CLI and structured output formats for the monitoring results.
"""

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from colorama import Fore, Style, init
import json
import textwrap
from tabulate import tabulate

from internet_stability_monitor.service import ServiceStatus
from internet_stability_monitor.context import MonitorContext

# Initialize colorama
init(autoreset=True)

@dataclass
class DisplayOptions:
    """Options for controlling how data is displayed."""
    use_color: bool = True
    show_timestamps: bool = True
    show_response_times: bool = True
    show_errors: bool = True
    format: str = "text"  # text, json, or table
    wrap_width: int = 80

class MonitorPresenter:
    """Handles the presentation of monitoring data."""
    
    def __init__(self, context: MonitorContext, options: Optional[DisplayOptions] = None):
        """Initialize the presenter.
        
        Args:
            context: MonitorContext instance
            options: Optional display options
        """
        self.context = context
        self.options = options or DisplayOptions()
        
    def _get_status_color(self, is_reachable: bool) -> str:
        """Get the color code for a status.
        
        Args:
            is_reachable: Whether the service is reachable
            
        Returns:
            Color code string
        """
        if not self.options.use_color:
            return ""
        return Fore.GREEN if is_reachable else Fore.RED
    
    def _get_status_symbol(self, is_reachable: bool) -> str:
        """Get the status symbol.
        
        Args:
            is_reachable: Whether the service is reachable
            
        Returns:
            Status symbol string
        """
        return "✓" if is_reachable else "✗"
    
    def _format_timestamp(self, dt: datetime) -> str:
        """Format a timestamp for display.
        
        Args:
            dt: Datetime to format
            
        Returns:
            Formatted timestamp string
        """
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def _format_response_time(self, response_time: float) -> str:
        """Format a response time for display.
        
        Args:
            response_time: Response time in seconds
            
        Returns:
            Formatted response time string
        """
        if response_time < 0.001:
            return f"{response_time*1000000:.1f}µs"
        elif response_time < 1:
            return f"{response_time*1000:.1f}ms"
        else:
            return f"{response_time:.2f}s"
    
    def _format_error(self, error: Optional[str]) -> str:
        """Format an error message for display.
        
        Args:
            error: Error message to format
            
        Returns:
            Formatted error string
        """
        if not error:
            return ""
        if not self.options.show_errors:
            return ""
        if self.options.use_color:
            return f"{Fore.RED}{error}{Style.RESET_ALL}"
        return error
    
    def format_service_status(self, status: ServiceStatus) -> str:
        """Format a single service status for display.
        
        Args:
            status: ServiceStatus to format
            
        Returns:
            Formatted status string
        """
        parts = []
        
        # Status symbol and name
        color = self._get_status_color(status.is_reachable)
        symbol = self._get_status_symbol(status.is_reachable)
        parts.append(f"{color}{symbol} {status.name}{Style.RESET_ALL}")
        
        # Timestamp
        if self.options.show_timestamps:
            parts.append(f"[{self._format_timestamp(status.last_checked)}]")
        
        # Response time
        if self.options.show_response_times:
            parts.append(f"({self._format_response_time(status.response_time)})")
        
        # Error message
        if status.error:
            parts.append(self._format_error(status.error))
        
        return " ".join(parts)
    
    def format_service_group(self, group_name: str, statuses: List[ServiceStatus]) -> str:
        """Format a group of service statuses for display.
        
        Args:
            group_name: Name of the service group
            statuses: List of ServiceStatus objects
            
        Returns:
            Formatted group string
        """
        if not statuses:
            return ""
            
        lines = [f"\n{group_name}:"]
        for status in statuses:
            lines.append(self.format_service_status(status))
        return "\n".join(lines)
    
    def format_as_text(self, results: Dict[str, List[ServiceStatus]]) -> str:
        """Format results as text.
        
        Args:
            results: Dictionary of service groups and their statuses
            
        Returns:
            Formatted text string
        """
        lines = []
        
        # Add header with timestamp
        if self.options.show_timestamps:
            lines.append(f"Internet Stability Monitor Report")
            lines.append(f"Generated: {self._format_timestamp(datetime.now())}\n")
        
        # Add system info
        system_info = self.context.get_system_summary()
        if system_info:
            lines.append("System Information:")
            lines.append(textwrap.indent(system_info, "  "))
            lines.append("")
        
        # Add network info
        is_connected, network_info = self.context.get_network_status()
        if network_info:
            lines.append("Network Information:")
            lines.append(textwrap.indent(network_info, "  "))
            lines.append("")
        
        # Add location info
        location_info = self.context.get_location_summary()
        if location_info:
            lines.append("Location Information:")
            lines.append(textwrap.indent(location_info, "  "))
            lines.append("")
        
        # Add service statuses
        for group_name, statuses in results.items():
            if statuses:
                lines.append(self.format_service_group(group_name, statuses))
        
        return "\n".join(lines)
    
    def format_as_json(self, results: Dict[str, List[ServiceStatus]]) -> str:
        """Format results as JSON.
        
        Args:
            results: Dictionary of service groups and their statuses
            
        Returns:
            Formatted JSON string
        """
        output = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self.context.get_system_summary(),
            "network_status": {
                "is_connected": is_connected,
                "status": network_info
            },
            "location_info": self.context.get_location_summary(),
            "services": {}
        }
        
        for group_name, statuses in results.items():
            output["services"][group_name] = [
                {
                    "name": status.name,
                    "is_reachable": status.is_reachable,
                    "response_time": status.response_time,
                    "error": status.error,
                    "last_checked": status.last_checked.isoformat()
                }
                for status in statuses
            ]
        
        return json.dumps(output, indent=2)
    
    def format_as_table(self, results: Dict[str, List[ServiceStatus]]) -> str:
        """Format results as a table.
        
        Args:
            results: Dictionary of service groups and their statuses
            
        Returns:
            Formatted table string
        """
        tables = []
        
        # Add header with timestamp
        if self.options.show_timestamps:
            tables.append(f"Internet Stability Monitor Report")
            tables.append(f"Generated: {self._format_timestamp(datetime.now())}\n")
        
        # Add system info
        system_info = self.context.get_system_summary()
        if system_info:
            tables.append("System Information:")
            tables.append(textwrap.indent(system_info, "  "))
            tables.append("")
        
        # Add network info
        is_connected, network_info = self.context.get_network_status()
        if network_info:
            tables.append("Network Information:")
            tables.append(textwrap.indent(network_info, "  "))
            tables.append("")
        
        # Add location info
        location_info = self.context.get_location_summary()
        if location_info:
            tables.append("Location Information:")
            tables.append(textwrap.indent(location_info, "  "))
            tables.append("")
        
        # Add service statuses
        for group_name, statuses in results.items():
            if statuses:
                table_data = []
                for status in statuses:
                    row = [
                        self._get_status_symbol(status.is_reachable),
                        status.name
                    ]
                    if self.options.show_response_times:
                        row.append(self._format_response_time(status.response_time))
                    if self.options.show_timestamps:
                        row.append(self._format_timestamp(status.last_checked))
                    if status.error:
                        row.append(status.error)
                    table_data.append(row)
                
                headers = ["Status", "Name"]
                if self.options.show_response_times:
                    headers.append("Response Time")
                if self.options.show_timestamps:
                    headers.append("Last Checked")
                if self.options.show_errors:
                    headers.append("Error")
                
                tables.append(f"\n{group_name}:")
                tables.append(tabulate(
                    table_data,
                    headers=headers,
                    tablefmt="grid"
                ))
        
        return "\n".join(tables)
    
    def format_results(self, results: Dict[str, List[ServiceStatus]]) -> str:
        """Format monitoring results according to display options.
        
        Args:
            results: Dictionary of service groups and their statuses
            
        Returns:
            Formatted results string
        """
        if self.options.format == "json":
            return self.format_as_json(results)
        elif self.options.format == "table":
            return self.format_as_table(results)
        else:
            return self.format_as_text(results) 