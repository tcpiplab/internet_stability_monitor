import os
import subprocess
import requests
import json
from datetime import datetime
from abuse_check import check_ip_reputation, analyze_ip_reputation
from service_check_summarizer import summarize_service_check_output

import argparse
def get_current_external_ip(silent):
    # Fetch the API key using the 'op' command
    router_api_key = subprocess.check_output(["/opt/homebrew/bin/op", "read",
                                              "op://Shared/UI.com API Credential for Ubiquiti WiFi equipment/credential"]).decode(
        'utf-8').strip()
    # Make the API request
    url = 'https://api.ui.com/ea/hosts'
    headers = {
        'X-API-KEY': router_api_key,
        'Accept': 'application/json'
    }
    response = requests.get(url, headers=headers)
    # Parse the JSON response
    data = response.json()
    # Extract the IP address
    ip_address = data['data'][0]['ipAddress']
    current_ip_pronouncable = ip_address.replace('.', ' dot ')
    print(f"Our external broadband IP Address is currently {ip_address}")
    if not silent:
        subprocess.run(["say", f"Our external broadband IP Address is currently {current_ip_pronouncable}"])
    # Check if the file exists from the previous run and compare the IP address
    if os.path.exists('/tmp/ip_address.txt'):
        with open('/tmp/ip_address.txt', 'r') as file:
            previous_ip = file.read().split(',')[1].strip()

        if ip_address != previous_ip:
            print(f"IP address has changed from {previous_ip} to {ip_address}")

            previous_ip_pronouncable = previous_ip.replace('.', ' dot ')

            # subprocess.run(
            if not silent:
                subprocess.run(["say", f"IP address has changed from {previous_ip_pronouncable} to {current_ip_pronouncable}"])
            print("IP address has not changed.")
            if not silent:
                subprocess.run(["say", "Our IP address has not changed."])
    # Save the IP address to a file with today's date and time, separated by a comma
    today_date_and_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    with open('/tmp/ip_address.txt', 'w') as file:
        file.write(f"{today_date_and_timestamp},{ip_address}")

    return ip_address
def main():
    global ip_reputation_output
    parser = argparse.ArgumentParser(description="Fetch and report external IP address.")
    parser.add_argument('--silent', action='store_true', help="Run without voice announcements")
    args = parser.parse_args()

    AbuseIPDB_API_KEY = subprocess.check_output(["/opt/homebrew/bin/op", "read", "op://Private/AbuseIPDB/AbuseIPDB_API_KEY"]).decode('utf-8').strip()

    external_ip = get_current_external_ip(args.silent)  # Get the current external IP

    # Check reputation of the external IP
    reputation_data = check_ip_reputation(external_ip, AbuseIPDB_API_KEY)

    # print("Reputation data:", reputation_data)

    # Analyze and display the results
    if reputation_data:

        try:
            ip_reputation_output = analyze_ip_reputation(reputation_data)
            # print("IP Reputation Analysis Output:", ip_reputation_output)

        except Exception as e:
            print("Failed to analyze IP reputation data.")
            print(e)

        try:
            ip_reputation_summary = summarize_service_check_output(ip_reputation_output)
            print(f"Received AI reputation summary: {ip_reputation_summary}")
            if not args.silent:
                subprocess.run(["say", ip_reputation_summary])
        except Exception as e:
            print("Failed to summarize service check output.")
            print(e)


    else:
        print("Failed to retrieve reputation data from Abuse IPDB API.")

if __name__ == "__main__":
    main()

