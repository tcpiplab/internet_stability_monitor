"""
Network Tools Package for Instability v2

This package contains migrated and improved network diagnostic tools
from the original internet_stability_monitor codebase.
"""

# Import tool functions for easy access
from .check_external_ip import get_public_ip, main as check_external_ip_main
from .web_check import check_website, check_websites_reachability, main as web_check_main