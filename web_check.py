import requests
import time
import warnings
from urllib.parse import urljoin, urlparse

# Suppress SSL warnings for unverified requests (since we're only testing reachability)
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# List of websites to check
websites = [
    "https://www.google.com",
    "https://www.amazon.com",
    "https://www.facebook.com",
    "https://www.apple.com",
    "https://www.microsoft.com",
    "https://www.reddit.com",
    "https://www.wikipedia.org",
    "https://www.netflix.com",
    "https://www.bbc.com",
    "https://www.nytimes.com",
    # Government websites
    "https://www.usa.gov",           # US
    "https://www.canada.ca",         # Canada
    "https://www.gob.mx",            # Mexico
    "https://www.gov.br",            # Brazil
    "https://www.gov.uk",            # UK
    "https://www.gouvernement.fr",   # France
    "https://www.bund.de",           # Germany
    "https://www.belgium.be",        # Belgium
    "https://www.australia.gov.au",  # Australia
    "https://www.india.gov.in",      # India
#    "https://www.gov.za",            # South Africa (removed due to persistent connection issues)
    "https://www.japan.go.jp",       # Japan
#    "https://www.korea.go.kr",       # South Korea (removed due to persistent connection issues)
    "https://www.gov.sg"             # Singapore
]

# User agent to make requests appear like they come from a real browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}


def check_website(url):
    try:
        # Parse the URL correctly
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = urljoin(base_url, "/robots.txt")
        
        response = requests.get(robots_url, headers=headers, timeout=15, verify=False)
        
        if response.status_code == 200:
            return "reachable", response.elapsed.total_seconds()
        elif response.status_code == 404:
            # Retry with root URL if robots.txt not found
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            if response.status_code == 200:
                return "reachable", response.elapsed.total_seconds()
            else:
                return "unreachable", f"Status Code: {response.status_code}"
        else:
            return "unreachable", f"Status Code: {response.status_code}"
    except requests.exceptions.Timeout:
        return "unreachable", "Timeout reached"
    except requests.exceptions.ConnectionError as e:
        return "unreachable", str(e)
    except Exception as e:
        return "unreachable", str(e)


def check_websites(websites):
    reachable_websites = []
    unreachable_websites = []

    # First round of checks
    for url in websites:
        status, result = check_website(url)
        if status == "reachable":
            reachable_websites.append((url, result))
        else:
            unreachable_websites.append((url, result))

    # Retry unreachable websites after a delay
    if unreachable_websites:
        print("\nRetrying unreachable websites...\n")
        time.sleep(5)  # Wait 5 seconds before retrying

        remaining_unreachable = []
        for url, error in unreachable_websites:
            status, retry_result = check_website(url)
            if status == "reachable":
                reachable_websites.append((url, retry_result))
            else:
                remaining_unreachable.append((url, retry_result))

        unreachable_websites = remaining_unreachable  # Update unreachable after retry

    return reachable_websites, unreachable_websites

if __name__ == "__main__":
    reachable, unreachable = check_websites(websites)
    
    print("Reachable Websites:")
    for url, response_time in reachable:
        print(f"- {url}: Response Time: {response_time:.6f} seconds")
    
    if len(unreachable) == 0:
        print("\nSummary of reachability of major tech and friendly government websites: All websites are reachable.")
    
    else:
        print("\nUnreachable Websites:")
        for url, error in unreachable:
            print(f"- {url}: {error}")