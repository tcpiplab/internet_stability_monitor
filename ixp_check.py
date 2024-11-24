import requests
from datetime import datetime
import time

import subprocess

# List of IXPs and their public-facing websites (updated Equinix URL)
ixp_endpoints = {
    "DE-CIX (Frankfurt)": "https://www.de-cix.net/",
    "LINX (London)": "https://www.linx.net/",
    "AMS-IX (Amsterdam)": "https://www.ams-ix.net/",
    "NYIIX (New York)": "https://www.nyiix.net/",
    "HKIX (Hong Kong)": "https://www.hkix.net/",
    "Equinix-IX (Global)": "https://status.equinix.com/"  # Updated URL
}

# Function to monitor IXPs
def monitor_ixps():
    reachable_ixps = []
    unreachable_ixps = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9"
    }

    for ixp, url in ixp_endpoints.items():
        retry_attempts = 3
        for attempt in range(retry_attempts):
            try:
                start_time = datetime.now()
                response = requests.get(url, headers=headers, timeout=15)  # 15-second timeout for reaching IXPs
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()

                if response.status_code == 200:
                    reachable_ixps.append(f"{ixp}: Response Time: {response_time:.3f} seconds")
                    break
                else:
                    if attempt == retry_attempts - 1:
                        unreachable_ixps.append(f"{ixp}: Status Code: {response.status_code}")
            except requests.RequestException as e:
                if attempt == retry_attempts - 1:
                    unreachable_ixps.append(f"{ixp}: unreachable: {str(e)}")
                time.sleep(2)  # Sleep for 2 seconds before retrying

    # Output results
    print("Reachable IXPs:")
    for ixp_info in reachable_ixps:
        print(f"- {ixp_info}")

    if len(unreachable_ixps) == 0:
        print("\nAll IXPs are reachable.")

    else:
        print("\nUnreachable IXPs:")
        for ixp_info in unreachable_ixps:
            print(f"- {ixp_info}")

if __name__ == "__main__":
    print(f"Starting IXP monitoring at {datetime.now()}\n")
    subprocess.run(["say", f"Starting IXP monitoring."])
    subprocess.run(["say", "This will check the reachability of several internet exchange points around the world."])
    monitor_ixps()