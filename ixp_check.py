
import requests
import json
from datetime import datetime
import time
import argparse
import subprocess
from io import StringIO
from tts_utils import speak_text

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
def monitor_ixps() -> str:
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
    output_buffer = StringIO()

    # Output results
    print("Reachable IXPs:")
    for ixp_info in reachable_ixps:
        output_buffer.write(f"- {ixp_info}\n")
        print(f"- {ixp_info}")

    if len(unreachable_ixps) == 0:
        output_buffer.write("\nAll IXPs are reachable.\n")
        print("\nAll IXPs are reachable.")

    else:
        print("\nUnreachable IXPs:")
        for ixp_info in unreachable_ixps:
            output_buffer.write(f"- {ixp_info}\n")
            print(f"- {ixp_info}")

    return output_buffer.getvalue()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor IXPs.")
    parser.add_argument("--silent", action="store_true", help="Run without announcements.")
    args = parser.parse_args()

    print(f"Starting IXP monitoring at {datetime.now()}\n")
    if not args.silent:
        speak_text( f"Starting IXP monitoring.")
        speak_text( "This will check the reachability of several internet exchange points around the world.")
    output = monitor_ixps()
    payload = {
        "model": "mistral",
        "prompt": output,
        "system": "Summarize the result of the monitoring and highlight any issues",
                "stream": False,
    }
    headers = {'Content-Type': 'application/json'}

    print(f"Sending the following payload to Ollama API:\n---\n{json.dumps(payload)}\n---\n")

    # print(f"The output from the monitoring is:\n---\n{output}\n---\n")

    try:
        response = requests.post('http://localhost:11434/api/generate', headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        # print("\nFull API Response:")
        # print(response.text)

        try:

            summary = response.json().get('response', 'No summary available.')

        except json.JSONDecodeError:

            print("Failed to parse the JSON response. Please check the response format.")
            summary = "No summary available due to parsing error."

        print("\nSummary of the IXP monitoring:")

        print(f"{summary}")

        if not args.silent:
            speak_text("The summary of the IXP monitoring is as follows.")

    except requests.RequestException as e:

        print(f"Failed to get summary from Ollama API: {e}")
