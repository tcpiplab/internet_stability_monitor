import subprocess

import requests
import json


def check_ip_reputation(ip_address, api_key, max_age_in_days=90):
    """
    Check the reputation of an IP address using AbuseIPDB.

    Args:
        ip_address (str): The IP address to check.
        api_key (str): Your AbuseIPDB API key.
        max_age_in_days (int): The maximum age of reports in days. Default is 90.

    Returns:
        dict: Parsed JSON response from AbuseIPDB.
    """
    # API endpoint
    url = 'https://api.abuseipdb.com/api/v2/check'

    # Query parameters
    querystring = {
        'ipAddress': ip_address,
        'maxAgeInDays': str(max_age_in_days),
        'verbose': 'true'
    }

    # Headers
    headers = {
        'Accept': 'application/json',
        'Key': api_key
    }

    try:
        # Make the request
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # Raise an error for HTTP codes 4xx or 5xx

        # Parse and return the response
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error while checking IP reputation: {e}")
        return None


def analyze_ip_reputation(data):
    """
    Analyze the reputation of an IP address from the AbuseIPDB response.

    Args:
        data (dict): Parsed JSON response from AbuseIPDB.

    Returns:
        None: Prints the analysis results.
    """
    if not data or "data" not in data:
        print("Invalid or empty data received.")
        return

    ip_info = data["data"]

    # Basic Information
    print(f"IP Address: {ip_info['ipAddress']}")
    print(f"Abuse Confidence Score: {ip_info['abuseConfidenceScore']} (High risk if > 50)")
    print(f"Country: {ip_info['countryName']} ({ip_info['countryCode']})")
    print(f"ISP: {ip_info.get('isp', 'Unknown')} ({ip_info.get('domain', 'No domain')})")
    print(f"Usage Type: {ip_info.get('usageType', 'Unknown')}")
    print(f"Total Reports: {ip_info['totalReports']} from {ip_info['numDistinctUsers']} distinct users")

    # Check if the IP is whitelisted
    if ip_info["isWhitelisted"]:
        print("This IP is whitelisted.")
    else:
        print("This IP is NOT whitelisted.")

    # Tor Detection
    if ip_info["isTor"]:
        print("Warning: This IP is associated with a Tor exit node.")

    # Last Report Information
    last_reported = ip_info.get("lastReportedAt")
    if last_reported:
        print(f"Last Reported At: {last_reported}")

    # Detailed Report Comments
    if "reports" in ip_info and ip_info["reports"]:
        print("\nRecent Reports:")
        for report in ip_info["reports"]:
            print(f"  - Reported At: {report['reportedAt']}")
            print(f"    Comment: {report['comment']}")
            print(f"    Categories: {report['categories']}")
            print(f"    Reporter Country: {report['reporterCountryName']} ({report['reporterCountryCode']})\n")


# Example usage
if __name__ == "__main__":

    AbuseIPDB_API_KEY = subprocess.check_output(["/opt/homebrew/bin/op", "read", "op://Private/AbuseIPDB/AbuseIPDB_API_KEY"]).decode('utf-8').strip()

    home_ip = "10.10.10.10"  # Replace with your home broadband IP
    reputation_data = check_ip_reputation(home_ip, AbuseIPDB_API_KEY)

    if reputation_data:
        analyze_ip_reputation(reputation_data)