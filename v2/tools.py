"""
Tools module for Instability v2

This module provides a registry of network diagnostic tools and handles
their execution. It can use tools from the original codebase when available,
and provides fallback implementations for essential tools to ensure the
chatbot can function even in offline situations.
"""

import os
import sys
import socket
import subprocess
import platform
import json
from typing import Dict, Any, Callable, Optional, List
from colorama import Fore, Style

# Add parent directory to path to allow importing from original modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Attempt to import original tools
ORIGINAL_TOOLS_AVAILABLE = False
try:
    # Import core modules from original codebase
    from check_external_ip import main as check_external_ip_main
    from check_if_external_ip_changed import did_external_ip_change
    from resolver_check import monitor_dns_resolvers
    from dns_check import main as dns_check_main
    from web_check import main as web_check_main
    from check_layer_two_network import report_link_status_and_type
    from whois_check import main as whois_check_main
    from os_utils import get_os_type

    ORIGINAL_TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"{Fore.YELLOW}Warning: Some original tools not available: {e}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Fallback implementations will be used where possible.{Style.RESET_ALL}")


# Basic tool implementations (fallbacks if original tools are not available)

def get_os_info() -> str:
    """Get information about the operating system and environment"""
    if ORIGINAL_TOOLS_AVAILABLE:
        try:
            return get_os_type()
        except Exception as e:
            print(f"{Fore.YELLOW}Error using original get_os_type: {e}{Style.RESET_ALL}")

    # Fallback implementation
    system = platform.system()
    release = platform.release()
    version = platform.version()
    machine = platform.machine()
    processor = platform.processor()

    return f"{system} {release} ({version}) {machine} {processor}"


def get_local_ip() -> str:
    """Get the local IP address of this machine"""
    try:
        # Create a socket to get the local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Connect to a public IP (doesn't actually send packets)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception as e:
        return f"Error getting local IP: {e}"


def get_external_ip() -> str:
    """Get the external/public IP address"""
    if ORIGINAL_TOOLS_AVAILABLE:
        try:
            return check_external_ip_main(silent=True, polite=False)
        except Exception as e:
            print(f"{Fore.YELLOW}Error using original external IP check: {e}{Style.RESET_ALL}")

    # Fallback implementation - try multiple services
    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
        "https://ident.me"
    ]

    import urllib.request

    for service in services:
        try:
            with urllib.request.urlopen(service, timeout=3) as response:
                return response.read().decode('utf-8').strip()
        except:
            continue

    return "Could not determine external IP (offline or no connectivity)"


def check_internet_connection() -> str:
    """Check if the internet is reachable"""
    try:
        # Try to connect to a reliable server
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return "Connected"
    except Exception:
        return "Disconnected"


def check_dns_resolvers() -> str:
    """Check if DNS resolvers are working properly"""
    if ORIGINAL_TOOLS_AVAILABLE:
        try:
            return monitor_dns_resolvers()
        except Exception as e:
            print(f"{Fore.YELLOW}Error using original DNS check: {e}{Style.RESET_ALL}")

    # Fallback implementation
    resolvers = {
        "Google Public DNS": "8.8.8.8",
        "Cloudflare DNS": "1.1.1.1",
        "Quad9 DNS": "9.9.9.9",
        "OpenDNS": "208.67.222.222"
    }

    results = []
    for name, ip in resolvers.items():
        try:
            socket.create_connection((ip, 53), timeout=2)
            results.append(f"{name} ({ip}): Reachable")
        except Exception:
            results.append(f"{name} ({ip}): Unreachable")

    return "\n".join(results)


def ping_target(host: str = "8.8.8.8", target: str = None, count: int = 4) -> str:
    """Ping a target host and measure response time
    
    Args:
        host: Target host to ping (default: 8.8.8.8)
        target: Alternative parameter name for host (for compatibility)
        count: Number of ping packets to send (default: 4)
    
    Returns:
        String containing ping results
    """
    try:
        # Allow either 'host' or 'target' parameter (target takes precedence if both are provided)
        destination = target if target is not None else host
        
        # Determine command based on operating system
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", str(count), destination]
        else:
            cmd = ["ping", "-c", str(count), destination]

        # Run the ping command
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            # Extract average time from output
            output = result.stdout

            # Try to extract average time (format varies by OS)
            if "Average" in output or "average" in output:
                for line in output.split("\n"):
                    if "Average" in line or "average" in line:
                        return line.strip()

            # If we can't extract the average, return the entire output
            return output
        else:
            return f"Ping failed with exit code {result.returncode}: {result.stderr}"
    except subprocess.TimeoutExpired:
        return f"Ping to {destination} timed out after 10 seconds"
    except Exception as e:
        return f"Error pinging {destination}: {e}"


def check_dns_root_servers() -> str:
    """Check if DNS root servers are reachable"""
    if ORIGINAL_TOOLS_AVAILABLE:
        try:
            return dns_check_main(silent=True, polite=False)
        except Exception as e:
            print(f"{Fore.YELLOW}Error using original DNS root server check: {e}{Style.RESET_ALL}")

    # Fallback implementation
    root_servers = {
        "a.root-servers.net": "198.41.0.4",
        "b.root-servers.net": "199.9.14.201",
        "c.root-servers.net": "192.33.4.12",
        "d.root-servers.net": "199.7.91.13",
        "e.root-servers.net": "192.203.230.10",
        "f.root-servers.net": "192.5.5.241"
    }

    results = []
    for name, ip in root_servers.items():
        try:
            socket.create_connection((ip, 53), timeout=2)
            results.append(f"{name} ({ip}): Reachable")
        except Exception:
            results.append(f"{name} ({ip}): Unreachable")

    return "\n".join(results)


def check_websites() -> str:
    """Check if major websites are reachable"""
    if ORIGINAL_TOOLS_AVAILABLE:
        try:
            return web_check_main(silent=True, polite=False)
        except Exception as e:
            print(f"{Fore.YELLOW}Error using original website check: {e}{Style.RESET_ALL}")

    # Fallback implementation
    websites = [
        "google.com",
        "amazon.com",
        "cloudflare.com",
        "microsoft.com",
        "apple.com",
        "github.com"
    ]

    results = []
    for site in websites:
        try:
            # Try DNS resolution
            ip = socket.gethostbyname(site)

            # Try connecting to port 80 (HTTP)
            socket.create_connection((site, 80), timeout=2)
            results.append(f"{site} ({ip}): Reachable")
        except socket.gaierror:
            results.append(f"{site}: DNS resolution failed")
        except Exception as e:
            results.append(f"{site}: Error - {str(e)}")

    return "\n".join(results)


def check_local_network() -> str:
    """Check local network interfaces and link status"""
    if ORIGINAL_TOOLS_AVAILABLE:
        try:
            return report_link_status_and_type()
        except Exception as e:
            print(f"{Fore.YELLOW}Error using original network check: {e}{Style.RESET_ALL}")

    # Fallback implementation (platform-specific)
    try:
        if platform.system().lower() == "linux":
            cmd = ["ip", "addr", "show"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.stdout
        elif platform.system().lower() == "darwin":  # macOS
            cmd = ["ifconfig"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.stdout
        elif platform.system().lower() == "windows":
            cmd = ["ipconfig", "/all"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.stdout
        else:
            return f"Unsupported platform: {platform.system()}"
    except Exception as e:
        return f"Error checking local network: {e}"


def check_whois_servers() -> str:
    """Check if WHOIS servers are reachable"""
    if ORIGINAL_TOOLS_AVAILABLE:
        try:
            return whois_check_main(silent=True, polite=False)
        except Exception as e:
            print(f"{Fore.YELLOW}Error using original WHOIS check: {e}{Style.RESET_ALL}")

    # Fallback implementation
    whois_servers = [
        "whois.verisign-grs.com",  # .com and .net
        "whois.iana.org",  # IANA
        "whois.pir.org",  # .org
        "whois.nic.uk"  # .uk
    ]

    results = []
    for server in whois_servers:
        try:
            # WHOIS servers typically listen on port 43
            socket.create_connection((server, 43), timeout=2)
            results.append(f"{server}: Reachable")
        except Exception:
            results.append(f"{server}: Unreachable")

    return "\n".join(results)


# Tool registry - dict mapping tool names to functions
def get_available_tools() -> Dict[str, Callable]:
    """
    Get a dictionary of all available diagnostic tools

    Returns:
        Dict mapping tool names to their functions
    """
    tools = {
        "get_os_info": get_os_info,
        "get_local_ip": get_local_ip,
        "get_external_ip": get_external_ip,
        "check_internet_connection": check_internet_connection,
        "check_dns_resolvers": check_dns_resolvers,
        "ping_target": ping_target,
        "check_dns_root_servers": check_dns_root_servers,
        "check_websites": check_websites,
        "check_local_network": check_local_network,
        "check_whois_servers": check_whois_servers
    }

    # Add more original tools if available - example of how to add more
    if ORIGINAL_TOOLS_AVAILABLE:
        try:
            # Example of potentially importing additional tools from original codebase
            # Only if we need more tools and they exist in the original codebase
            pass
        except Exception as e:
            print(f"{Fore.YELLOW}Error adding additional tools: {e}{Style.RESET_ALL}")

    return tools


def execute_tool(tool_name: str, args: Optional[Dict[str, Any]] = None) -> Any:
    """
    Execute a specific tool with optional arguments

    Args:
        tool_name: The name of the tool to execute
        args: Optional arguments to pass to the tool

    Returns:
        The result of the tool execution
    """
    # Get available tools
    tools = get_available_tools()

    # Check if the tool exists
    if tool_name not in tools:
        raise ValueError(f"Tool '{tool_name}' not found. Available tools: {', '.join(tools.keys())}")

    # Get the tool function
    tool_func = tools[tool_name]

    # Execute with args if provided, otherwise without args
    if args:
        return tool_func(**args)
    else:
        return tool_func()


def list_tool_help() -> str:
    """
    List all available tools with their descriptions

    Returns:
        Formatted string with tool information
    """
    tools = get_available_tools()

    output = []
    output.append("Available Network Diagnostic Tools:")
    output.append("==================================")

    for name, func in tools.items():
        desc = func.__doc__.split('\n')[0].strip() if func.__doc__ else "No description available"
        output.append(f"{name}: {desc}")

    return "\n".join(output)


# Additional helper functions for working with tools

def get_tool_details(tool_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific tool

    Args:
        tool_name: The name of the tool

    Returns:
        Dictionary with tool details
    """
    tools = get_available_tools()

    if tool_name not in tools:
        raise ValueError(f"Tool '{tool_name}' not found")

    tool_func = tools[tool_name]

    # Get tool docstring
    doc = tool_func.__doc__ or "No documentation available"

    # Get source code if possible
    import inspect
    try:
        source = inspect.getsource(tool_func)
    except Exception:
        source = "Source code not available"

    details = {
        "name": tool_name,
        "description": doc,
        "source": source,
        "signature": str(inspect.signature(tool_func)),
        "is_original": False  # Default to False
    }

    # Try to determine if this is an original tool
    if ORIGINAL_TOOLS_AVAILABLE:
        module = inspect.getmodule(tool_func)
        if module and parent_dir in str(module):
            details["is_original"] = True

    return details
