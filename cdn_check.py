import requests
from datetime import datetime
import time

# List of CDNs and their respective endpoints to monitor
cdn_endpoints = {
    "Cloudflare": "https://www.cloudflare.com/robots.txt",
    "Akamai": "https://developer.akamai.com/",  # Akamai is now reachable
    "Fastly": "https://www.fastly.com/robots.txt",
    "Amazon CloudFront": "https://d1.awsstatic.com/",
    "Google Cloud CDN": "https://www.google.com/robots.txt",
    "Microsoft Azure CDN": "https://www.microsoft.com/robots.txt"  # Updated to a public Microsoft endpoint
}

# Function to monitor CDN endpoints
def monitor_cdns():
    reachable_cdns = []
    unreachable_cdns = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
        "Referer": "https://www.example.com",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9"
    }

    for cdn, url in cdn_endpoints.items():
        retry_attempts = 3
        for attempt in range(retry_attempts):
            try:
                start_time = datetime.now()
                response = requests.get(url, headers=headers, timeout=20)  # 20-second timeout for more stability
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()

                if response.status_code == 200:
                    reachable_cdns.append(f"{cdn}: Response Time: {response_time:.3f} seconds")
                    break
                elif response.status_code == 204 and cdn in ["Google Cloud CDN", "Microsoft Azure CDN"]:
                    reachable_cdns.append(f"{cdn}: Response Time: {response_time:.3f} seconds (Returned 204 No Content)")
                    break
                else:
                    if attempt == retry_attempts - 1:
                        unreachable_cdns.append(f"{cdn}: Status Code: {response.status_code}")
            except requests.RequestException as e:
                if attempt == retry_attempts - 1:
                    unreachable_cdns.append(f"{cdn}: unreachable: {str(e)}")
                time.sleep(2)  # Sleep for 2 seconds before retrying

    if len(reachable_cdns) == len(cdn_endpoints):
        print("All CDNs are reachable.")

    # Output results
    print("Reachable CDNs:")
    for cdn_info in reachable_cdns:
        print(f"- {cdn_info}")

    if len(reachable_cdns) == 0:
        print("All CDNs are unreachable!")

    if len(unreachable_cdns) == 0:
        print("All CDNs are reachable!")


    if len(unreachable_cdns) > 0:
        print("\nUnreachable CDNs:")
        for cdn_info in unreachable_cdns:
            print(f"- {cdn_info}")

if __name__ == "__main__":
    print(f"Starting CDN monitoring at {datetime.now()}\n")
    monitor_cdns()