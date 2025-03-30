"""
This module retrieves and reports the geographic location and ISP information
based on the current public IP address using the ipinfo.io API.
"""

import requests
import os
from typing import Dict, Any


def get_public_ip() -> str:
    """
    Retrieve the public IP address of the current internet connection.

    Returns:
        str: The public IP address.
    """
    response = requests.get("https://api.ipify.org?format=json")
    ip_info = response.json()
    return ip_info.get("ip")


def get_isp_and_location(ip: str) -> Dict[str, Any]:
    """
    Retrieve ISP and geographic location information for a given IP address.

    Uses the ipinfo.io API. If the IPINFOIO_API_KEY environment variable is set,
    it will use that for authenticated requests, which provide higher rate limits.

    Args:
        ip (str): The IP address to look up.

    Returns:
        Dict[str, Any]: Dictionary containing ISP and location data including:
            - org: The organization/ISP
            - city: The city
            - region: The region/state
            - country: The country
            - and other data provided by ipinfo.io API
    """
    token = os.getenv("IPINFOIO_API_KEY")
    if not token:
        print("IPINFOIO_API_KEY environment variable not set")
        response = requests.get(f"https://ipinfo.io/{ip}")
    else:
        # Use the token for authenticated requests
        response = requests.get(f"https://ipinfo.io/{ip}?token={token}")

    ip_data = response.json()
    return ip_data


def main() -> str:
    """
    Main function that retrieves the public IP address and location information.

    Returns:
        str: A formatted string containing city, region, country and ISP information.
    """
    # Get the public IP address
    public_ip = get_public_ip()

    # Get ISP and location information
    ip_data = get_isp_and_location(public_ip)
    isp = ip_data.get("org", "Unknown ISP")
    isp = f"BGP Autonomous System Number {isp}"
    city = ip_data.get("city", "Unknown city")
    region = ip_data.get("region", "Unknown region")
    country = ip_data.get("country", "Unknown country")

    return f"{city}, {region}, {country}, downstream from the {isp} network"


if __name__ == "__main__":
    main()