import subprocess
import requests
import json
import io


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


# def analyze_ip_reputation(data):
#     """
#     Analyze the reputation of an IP address from the AbuseIPDB response.
#
#     Args:
#         data (dict): Parsed JSON response from AbuseIPDB.
#
#     Returns:
#         str: Prints the analysis results and returns ip_reputation_string.
#     """
#     if not data or "data" not in data:
#         print("Invalid or empty data received.")
#         return
#
#     ip_info = data["data"]
#
#     # print("ip_info:", ip_info)
#
#     # Create an StringIO object to capture all prints
#     with io.StringIO() as output:
#         # Basic Information
#         output.write(f"IP Address: {ip_info['ipAddress']}\n")
#         output.write(f"Abuse Confidence Score: {ip_info['abuseConfidenceScore']} (High risk if > 50)\n")
#         output.write(f"Country: {ip_info['countryName']} ({ip_info['countryCode']})\n")
#         output.write(f"ISP: {ip_info.get('isp', 'Unknown')} ({ip_info.get('domain', 'No domain')})\n")
#         output.write(f"Usage Type: {ip_info.get('usageType', 'Unknown')}\n")
#         output.write(f"Total Reports: {ip_info['totalReports']} from {ip_info['numDistinctUsers']} distinct users\n")
#
#         # Check if the IP is whitelisted
#         if ip_info["isWhitelisted"]:
#             output.write("This IP is whitelisted.\n")
#         else:
#             output.write("This IP is NOT whitelisted.\n")
#
#         # Tor Detection
#         if ip_info["isTor"]:
#             output.write("Warning: This IP is associated with a Tor exit node.\n")
#
#         # Last Report Information
#         last_reported = ip_info.get("lastReportedAt")
#         if last_reported:
#             output.write(f"Last Reported At: {last_reported}\n")
#
#         # Detailed Report Comments
#         if "reports" in ip_info and ip_info["reports"]:
#             output.write("\nRecent Reports:\n")
#             for report in ip_info["reports"]:
#                 output.write(f"  - Reported At: {report['reportedAt']}\n")
#                 output.write(f"    Comment: {report['comment']}\n")
#                 output.write(f"    Categories: {report['categories']}\n")
#                 output.write(
#                     f"    Reporter Country: {report['reporterCountryName']} ({report['reporterCountryCode']})\n\n")
#
#                 print(f"IP Reputation Analysis Output: {output.readlines()}")  # Print the captured output
#         # output.read().strip())  # Print the captured output
#         return output.read().strip()  # Remove trailing newline
#
#     # return ip_reputation_string


# def append_and_print(target_string, string):
#     # Append the string to the variable
#     # target_string += string + "\n"
#     target_string.join(string + "\n")
#     print(f">>> {string}")                 # Print the string
#     return target_string


def analyze_ip_reputation(data):
    """
    Analyze the reputation of an IP address from the AbuseIPDB response.

    Args:
        data (dict): Parsed JSON response from AbuseIPDB.

    Returns:
        str: Prints the analysis results.
    """
    if not data or "data" not in data:
        print("Invalid or empty data received.")
        return

    ip_info = data["data"]

    ip_reputation_string = ""

    # Basic Information
    print(f"IP Address: {ip_info['ipAddress']}")
    ip_reputation_string += f"IP Address: {ip_info['ipAddress']}\n"
    print(f"Abuse Confidence Score: {ip_info['abuseConfidenceScore']} (High risk if > 50)")
    ip_reputation_string += f"Abuse Confidence Score: {ip_info['abuseConfidenceScore']} (High risk if > 50)\n"
    print(f"Country: {ip_info['countryName']} ({ip_info['countryCode']})")
    ip_reputation_string += f"Country: {ip_info['countryName']} ({ip_info['countryCode']})\n"
    print(f"ISP: {ip_info.get('isp', 'Unknown')} ({ip_info.get('domain', 'No domain')})")
    ip_reputation_string += f"ISP: {ip_info.get('isp', 'Unknown')} ({ip_info.get('domain', 'No domain')})\n"
    print(f"Usage Type: {ip_info.get('usageType', 'Unknown')}")
    ip_reputation_string += f"Usage Type: {ip_info.get('usageType', 'Unknown')}\n"
    print(f"Total Abuse Reports: {ip_info['totalReports']} from {ip_info['numDistinctUsers']} distinct users")
    ip_reputation_string += f"Total Reports: {ip_info['totalReports']} from {ip_info['numDistinctUsers']} distinct users\n"

    # Check if the IP is whitelisted
    if ip_info["isWhitelisted"]:
        print("This IP is whitelisted by the Abuse IPDB.")
        ip_reputation_string += "This IP is whitelisted by the Abuse IPDB.\n"
    else:
        print("This IP is NOT whitelisted by the Abuse IPDB.")
        ip_reputation_string += "This IP is NOT whitelisted by the Abuse IPDB.\n"

    # Tor Detection
    if ip_info["isTor"]:
        print("Warning: This IP is associated with a Tor exit node.")
        ip_reputation_string += "Warning: This IP is associated with a Tor exit node.\n"

    # Last Report Information
    last_reported = ip_info.get("lastReportedAt")
    if last_reported:
        print(f"Last Reported At: {last_reported}")
        ip_reputation_string += f"Last Reported At: {last_reported}\n"

    # Detailed Report Comments
    if "reports" in ip_info and ip_info["reports"]:
        print("\nRecent Reports:")
        ip_reputation_string += "\nRecent Reports:\n"
        for report in ip_info["reports"]:
            print(f"  - Reported At: {report['reportedAt']}")
            ip_reputation_string += f"  - Reported At: {report['reportedAt']}\n"
            print(f"    Comment: {report['comment']}")
            ip_reputation_string += f"    Comment: {report['comment']}\n"
            print(f"    Categories: {report['categories']}")
            ip_reputation_string += f"    Categories: {report['categories']}\n"
            print(f"    Reporter Country: {report['reporterCountryName']} ({report['reporterCountryCode']})\n")
            ip_reputation_string += f"    Reporter Country: {report['reporterCountryName']} ({report['reporterCountryCode']})\n\n"

    # print(f"Returning ip_reputation_string: {ip_reputation_string}")  # Print the captured output
    return ip_reputation_string

# Example usage
# if __name__ == "__main__":
#
#     AbuseIPDB_API_KEY = subprocess.check_output(["/opt/homebrew/bin/op", "read", "op://Private/AbuseIPDB/AbuseIPDB_API_KEY"]).decode('utf-8').strip()
#
#     home_ip = "10.10.10.10"  # Replace with your home broadband IP
#     # home_ip = check_external_ip.get_current_external_ip(silent=True)
#     reputation_data = check_ip_reputation(home_ip, AbuseIPDB_API_KEY)
#
#     if reputation_data:
#         analyze_ip_reputation(reputation_data)