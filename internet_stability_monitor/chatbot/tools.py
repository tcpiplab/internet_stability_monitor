"""
Network diagnostic tools for the chatbot.

This module defines all the LangChain tools that the chatbot can use to
diagnose network issues and retrieve system information.
"""

import os
import requests  # Need to add this import for API calls
from typing import List, Dict, Any, Optional
import socket
import subprocess
from langchain_core.tools import tool

# Import from other modules - these would be resolved in the final implementation
from os_utils import get_os_type, OS_TYPE
from report_source_location import get_public_ip, get_isp_and_location
from check_if_external_ip_changed import did_external_ip_change
from cdn_check import main as cdn_check_main
from tls_ca_check import main as tls_ca_check_main
from whois_check import main as whois_check_main
import check_ollama_status
from resolver_check import monitor_dns_resolvers
from dns_check import check_dns_root_servers, dns_root_servers
from dns_check import main as check_all_root_servers
from check_layer_two_network import report_link_status_and_type
import mac_speed_test
from smtp_check import main as smtp_check_main
from web_check import main as web_check_main

# The memory system needs to be injected here, so we'll set it up to be passed later
# This avoids circular imports
memory_system = None

def set_memory_system(memory):
    """Set the memory system for tool result recording."""
    global memory_system
    memory_system = memory

@tool
def check_smtp_servers() -> str:
    """Use this to check the reachability of several important SMTP servers.

    Returns: str: The SMTP server monitoring report
    """
    result = smtp_check_main(silent=True, polite=False)
    if memory_system:
        memory_system.record_tool_call("check_smtp_servers", {}, result)
    return result

@tool
def run_mac_speed_test() -> str:
    """Use this to run the mac speed test and get a summary of the network quality.

    Returns: str: The mac speed test report or an error message if not on macOS
    """
    if OS_TYPE.lower() != "macOS".lower():
        result = "The mac speed test is only available on macOS."
    else:
        result = mac_speed_test.run_network_quality_test(silent=True, args=None)
    
    if memory_system:
        memory_system.record_tool_call("run_mac_speed_test", {}, result)
    return result

@tool
def check_ollama():
    """Use this to check if the Ollama process is running and/or if the Ollama API is reachable."""
    result = check_ollama_status.main()
    if memory_system:
        memory_system.record_tool_call("check_ollama", {}, result)
    return result

@tool
def check_cdn_reachability() -> str:
    """Use this to check the reachability of several of the largest content delivery networks around the world.

    Returns: str: The CDN reachability report
    """
    result = cdn_check_main(silent=True, polite=False)
    if memory_system:
        memory_system.record_tool_call("check_cdn_reachability", {}, result)
    return result

@tool
def ping_target(target: str) -> str:
    """Use this to ping an IP address or hostname to determine the network latency.

    Args:
        target (str): The IP address or hostname to ping.

    Returns: str: The average latency in milliseconds, or an error message if the ping fails.
    """
    try:
        # Run the ping command
        result = subprocess.run(
            ["ping", "-c", "4", target],
            capture_output=True,
            text=True,
            check=True
        )
        # Extract the average latency from the ping output
        for line in result.stdout.splitlines():
            if "avg" in line:
                result = line.split("/")[4] + " ms"
                if memory_system:
                    memory_system.record_tool_call("ping_target", {"target": target}, result)
                return result
        result = "Ping completed, but average latency could not be determined."
    except subprocess.CalledProcessError as e:
        result = f"Ping failed: {e}"
    except Exception as e:
        result = f"An error occurred: {e}"
    
    if memory_system:
        memory_system.record_tool_call("ping_target", {"target": target}, result)
    return result

@tool
def check_whois_servers() -> str:
    """Use this to check the reachability of WHOIS servers.

    Returns: str: The WHOIS server monitoring report
    """
    result = whois_check_main(silent=True, polite=False)
    if memory_system:
        memory_system.record_tool_call("check_whois_servers", {}, result)
    return result

@tool
def check_tls_ca_servers() -> str:
    """Use this to check the reachability of TLS CA servers.

    Returns: str: The TLS CA server monitoring report
    """
    result = tls_ca_check_main(silent=True, polite=False)
    if memory_system:
        memory_system.record_tool_call("check_tls_ca_servers", {}, result)
    return result

@tool
def get_os() -> str:
    """Use this to get os information.

    Returns: str: the os type
    """
    result = get_os_type()
    if memory_system:
        memory_system.record_tool_call("get_os", {}, result)
    return result

@tool
def get_local_ip() -> str:
    """Use this to get our local IP address that we're using for the local LAN, Ethernet, or WiFi network.

    Returns: str: this computer's local ip address
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        result = s.getsockname()[0]
    
    if memory_system:
        memory_system.record_tool_call("get_local_ip", {}, result)
    return result

@tool
def get_external_ip() -> str:
    """
    Use this to get the external ip address this computer is currently using to access the internet.
    The external ip address is the ip address of the router or modem that is connected to the internet.
    The external ip address is also known as the public ip address and is assigned by the ISP.

    Returns: str: our external ip address
    """
    result = get_public_ip()
    if memory_system:
        memory_system.record_tool_call("get_external_ip", {}, result)
    return result

@tool
def check_external_ip_change() -> str:
    """Use this to check if the external IP address has changed since the last check.

    Returns: str: A message indicating whether the IP address has changed or not.
    """
    # Get the current external IP using the existing tool
    current_external_ip = get_public_ip()

    # Check if the external IP has changed
    result = did_external_ip_change(current_external_ip)
    
    if memory_system:
        memory_system.record_tool_call("check_external_ip_change", {}, result)
    return result

@tool
def get_isp_location() -> dict[str, Any]:
    """
    Use this to get our external ISP location data based on our external IP address.
    Uses the ipinfo.io API to get the ISP name and location data.

    Returns: str: JSON formatted ISP name and location data
    """
    our_external_ip = get_public_ip()
    result = get_isp_and_location(our_external_ip)
    
    if memory_system:
        memory_system.record_tool_call("get_isp_location", {}, result)
    return result

@tool
def check_internet_connection() -> str:
    """Use this to check if we have a working internet broadband connection, including basic DNS lookup of www.google.com.

    Returns: str: "connected" if we have an internet connection, "disconnected" if we don't
    """
    try:
        socket.create_connection(("www.google.com", 80))
        result = "connected"
    except OSError:
        result = "disconnected"
    
    if memory_system:
        memory_system.record_tool_call("check_internet_connection", {}, result)
    return result

@tool
def check_layer_three_network() -> str:
    """Use this to check if we have a working layer 3 internet broadband connection and can reach 8.8.8.8 on port 53.

    Returns: str: "connected at layer 3" if we have an internet connection, "disconnected at layer 3" if we don't
    """
    try:
        socket.create_connection(("8.8.8.8", 53))
        result = "connected at layer 3"
    except OSError:
        result = "disconnected at layer 3"
    
    if memory_system:
        memory_system.record_tool_call("check_layer_three_network", {}, result)
    return result

@tool
def check_dns_resolvers() -> str:
    """Use this to check the reachability of several of the most popular DNS resolvers.

    Returns: str: the DNS resolver monitoring report
    """
    result = monitor_dns_resolvers()
    if memory_system:
        memory_system.record_tool_call("check_dns_resolvers", {}, result)
    return result

@tool
def check_websites() -> str:
    """
    Use this to check the reachability of several important websites from a hardcoded list of significant websites. 
    The list of websites it will check includes major tech companies, governments around the world, news organizations,
    social media platforms, and more. You can think of this tool as checking if the 'web' is healthy and working.
    
    Returns: str: The website monitoring report
    """
    result = web_check_main(silent=True, polite=False)
    if memory_system:
        memory_system.record_tool_call("check_websites", {}, result)
    return result

@tool
def check_dns_root_servers_reachability() -> str:
    """Use this to check the reachability of the major DNS Root Servers around the world.

    Returns: str: the DNS root server monitoring report
    """
    result = check_all_root_servers(silent=True, polite=False)
    if memory_system:
        memory_system.record_tool_call("check_dns_root_servers_reachability", {}, result)
    return result

@tool
def check_local_layer_two_network() -> str:
    """Use this to check the local LAN OSI Layer 2 network link type, speed, and status.
        For example, it will print the LAN network interfaces that are up,
        and if they are up and have a speed greater than 0 Mbps, it will also print the link type and speed.
        It will also try to guess if the network interface is Wi-Fi, Ethernet, Loopback, or Unknown.

    Returns: str: for interfaces that are up, the link name, type guess, and speed
    """
    result = report_link_status_and_type()
    if memory_system:
        memory_system.record_tool_call("check_local_layer_two_network", {}, result)
    return result


@tool
def check_ip_reputation(ip_address: str = None, input: str = None) -> str:
    """
    Use this to check the reputation of an IP address using AbuseIPDB.

    Args:
        ip_address (str): The IP address to check.
        input (str): An alternative parameter name for the IP address.

    Returns:
        str: A report on the IP's reputation including abuse confidence score, country info, and recent reports.
    """
    # Handle parameter name variation (support both 'input' and 'ip_address')
    actual_ip = ip_address or input
    if not actual_ip:
        return "Error: No IP address provided"

    print(f"Checking IP reputation for: {actual_ip}")

    try:
        # Try to get API key from memory, environment, or 1Password
        api_key = None

        if memory_system and memory_system.get_cached_value("abuseipdb_api_key"):
            api_key = memory_system.get_cached_value("abuseipdb_api_key")

        if not api_key and "ABUSEIPDB_API_KEY" in os.environ:
            api_key = os.environ["ABUSEIPDB_API_KEY"]

        if not api_key:
            try:
                # Try to get API key from 1Password CLI if available
                import subprocess
                api_key = subprocess.check_output(
                    ["/opt/homebrew/bin/op", "read", "op://Private/AbuseIPDB/AbuseIPDB_API_KEY"]).decode(
                    'utf-8').strip()
                # Cache the API key for future use
                if memory_system:
                    memory_system.update_cache("abuseipdb_api_key", api_key)
            except:
                result = "AbuseIPDB API key not found. Please set the ABUSEIPDB_API_KEY environment variable."
                if memory_system:
                    memory_system.record_tool_call("check_ip_reputation", {"ip_address": ip_address}, result)
                return result

        # Query AbuseIPDB
        url = 'https://api.abuseipdb.com/api/v2/check'
        querystring = {
            'ipAddress': actual_ip,
            'maxAgeInDays': '90',
            'verbose': 'true'
        }
        headers = {
            'Accept': 'application/json',
            'Key': api_key
        }

        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        reputation_data = response.json()

        # Analyze and format the result
        result = _analyze_ip_reputation(reputation_data)

        if memory_system:
            memory_system.record_tool_call("check_ip_reputation", {"ip_address": ip_address}, result)

        return result

    except requests.exceptions.RequestException as e:
        result = f"Error communicating with AbuseIPDB: {e}"
        if memory_system:
            memory_system.record_tool_call("check_ip_reputation", {"ip_address": ip_address}, result)
        return result
    except Exception as e:
        result = f"Error checking IP reputation: {e}"
        if memory_system:
            memory_system.record_tool_call("check_ip_reputation", {"ip_address": ip_address}, result)
        return result


def _analyze_ip_reputation(data: dict) -> str:
    """
    Helper function to analyze the reputation of an IP address from the AbuseIPDB response.

    Args:
        data (dict): Parsed JSON response from AbuseIPDB.

    Returns:
        str: The analysis results as a formatted string.
    """
    if not data or "data" not in data:
        return "Invalid or empty data received."

    ip_info = data["data"]
    ip_reputation_string = ""

    # Basic Information
    ip_reputation_string += f"IP Address: {ip_info['ipAddress']}\n"
    ip_reputation_string += f"Abuse Confidence Score: {ip_info['abuseConfidenceScore']} (High risk if > 50)\n"
    ip_reputation_string += f"Country: {ip_info['countryName']} ({ip_info['countryCode']})\n"
    ip_reputation_string += f"ISP: {ip_info.get('isp', 'Unknown')} ({ip_info.get('domain', 'No domain')})\n"
    ip_reputation_string += f"Usage Type: {ip_info.get('usageType', 'Unknown')}\n"
    ip_reputation_string += f"Total Reports: {ip_info['totalReports']} from {ip_info['numDistinctUsers']} distinct users\n"

    # Check if the IP is whitelisted
    if ip_info["isWhitelisted"]:
        ip_reputation_string += "This IP is whitelisted by the Abuse IPDB.\n"
    else:
        ip_reputation_string += "This IP is NOT whitelisted by the Abuse IPDB.\n"

    # Tor Detection
    if ip_info["isTor"]:
        ip_reputation_string += "Warning: This IP is associated with a Tor exit node.\n"

    # Last Report Information
    last_reported = ip_info.get("lastReportedAt")
    if last_reported:
        ip_reputation_string += f"Last Reported At: {last_reported}\n"

    # Detailed Report Comments
    if "reports" in ip_info and ip_info["reports"]:
        ip_reputation_string += "\nRecent Reports:\n"
        for report in ip_info["reports"]:
            ip_reputation_string += f"  - Reported At: {report['reportedAt']}\n"
            ip_reputation_string += f"    Comment: {report['comment']}\n"
            ip_reputation_string += f"    Categories: {report['categories']}\n"
            ip_reputation_string += f"    Reporter Country: {report['reporterCountryName']} ({report['reporterCountryCode']})\n\n"

    return ip_reputation_string


# Create a function to get all tools
def get_tools():
    """Get all available diagnostic tools."""
    return [
        check_ollama,
        get_os,
        get_local_ip,
        check_internet_connection,
        check_layer_three_network,
        get_external_ip,
        check_external_ip_change,
        get_isp_location,
        check_dns_resolvers,
        check_websites,
        check_dns_root_servers_reachability,
        check_local_layer_two_network,
        ping_target,
        check_tls_ca_servers,
        check_whois_servers,
        check_cdn_reachability,
        run_mac_speed_test,
        check_smtp_servers,
        check_ip_reputation,
    ]

# Function to directly invoke a tool (for command handlers)
def invoke_tool(tool, input_data=None):
    """Directly invoke a tool with optional input data."""
    if input_data is None:
        input_data = {}
        
    # Use the new invoke method instead of calling directly
    if hasattr(tool, "invoke"):
        return tool.invoke(input_data)
    # Fallback for older tools or custom functions
    elif callable(tool):
        return tool(**input_data)
        
    return None