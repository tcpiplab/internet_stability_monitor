import os
import subprocess
import requests
import json
from datetime import datetime

# Fetch the API key using the 'op' command
# api_key = subprocess.check_output(["/opt/homebrew/bin/op", "read", "op://Shared/UI.com API Credential for Ubiquiti WiFi equipment/credential"])

api_key = subprocess.check_output(["/opt/homebrew/bin/op", "read", "op://Shared/UI.com API Credential for Ubiquiti WiFi equipment/credential"]).decode('utf-8').strip()

# Make the API request
url = 'https://api.ui.com/ea/hosts'
headers = {
    'X-API-KEY': api_key,
    'Accept': 'application/json'
}

response = requests.get(url, headers=headers)

# Parse the JSON response
data = response.json()

# Extract the IP address
ip_address = data['data'][0]['ipAddress']

print(f"Our external broadband IP Address is currently {ip_address}")
subprocess.run(["say", f"Our external broadband IP Address is currently {ip_address}"])

# Check if the file exists from the previous run and compare the IP address
if os.path.exists('/tmp/ip_address.txt'):
    with open('/tmp/ip_address.txt', 'r') as file:
        previous_ip = file.read().split(',')[1].strip()

    if ip_address != previous_ip:
        print(f"IP address has changed from {previous_ip} to {ip_address}")
        subprocess.run(["say", f"IP address has changed from {previous_ip} to {ip_address}"])
    else:
        print("IP address has not changed.")
        subprocess.run(["say", "Our external broadband IP address has not changed."])

# Save the IP address to a file with today's date and time, separated by a comma
today_date_and_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
with open('/tmp/ip_address.txt', 'w') as file:
    file.write(f"{today_date_and_timestamp},{ip_address}")



