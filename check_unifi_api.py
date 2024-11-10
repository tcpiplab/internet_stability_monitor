import os
import subprocess
import requests
import json

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
