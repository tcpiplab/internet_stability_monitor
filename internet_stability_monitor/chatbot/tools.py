"""
Network diagnostic tools for the chatbot.

This module defines all the LangChain tools that the chatbot can use to
diagnose network issues and retrieve system information.
"""

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