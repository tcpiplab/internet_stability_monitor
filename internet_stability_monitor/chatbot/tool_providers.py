"""
Tool providers for the chatbot.

This module organizes tools into logical groups that can be added to the agent.
"""

from typing import List, Any
from langchain_core.tools import BaseTool

from .tools import (
    check_smtp_servers, run_mac_speed_test, check_ollama,
    check_cdn_reachability, ping_target, check_whois_servers,
    check_tls_ca_servers, get_os, get_local_ip, get_external_ip,
    check_external_ip_change, get_isp_location, check_internet_connection,
    check_layer_three_network, check_dns_resolvers, check_websites,
    check_dns_root_servers_reachability, check_local_layer_two_network,
    check_ip_reputation
)

class NetworkToolProvider:
    """Provides network diagnostic tools."""
    
    @property
    def name(self) -> str:
        return "Network Diagnostics"
    
    @property
    def tools(self) -> List[BaseTool]:
        return [
            # Basic connectivity
            check_internet_connection,
            get_local_ip,
            get_external_ip,
            check_external_ip_change,
            get_isp_location,
            
            # Network layers
            check_local_layer_two_network,
            check_layer_three_network,
            
            # DNS tools
            check_dns_resolvers,
            check_dns_root_servers_reachability,
            
            # Service checks
            check_websites,
            check_cdn_reachability,
            check_whois_servers,
            check_tls_ca_servers,
            check_smtp_servers,

            # IP and security checks
            check_ip_reputation,

            # Performance
            ping_target,
            run_mac_speed_test,
        ]

class SystemToolProvider:
    """Provides system information tools."""
    
    @property
    def name(self) -> str:
        return "System Information"
    
    @property
    def tools(self) -> List[BaseTool]:
        return [
            get_os,
            check_ollama
        ]

def get_default_providers() -> List[Any]:
    """Get the default set of tool providers."""
    return [
        NetworkToolProvider(),
        SystemToolProvider()
    ] 