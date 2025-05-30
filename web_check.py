from typing import List, Tuple, Union
import requests
import time
import warnings
from urllib.parse import urljoin, urlparse
import argparse
from service_check_summarizer import summarize_service_check_output
from tts_utils import speak_text
from summary_utils import add_to_combined_summaries

# Suppress SSL warnings for unverified requests (since we're only testing reachability)
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# list_of_significant_websites to check
list_of_significant_websites: List[str] = [
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
    # Government list_of_significant_websites
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


def check_website(url: str, verify_ssl: bool = False) -> Tuple[str, Union[float, str]]:
    """
    Check if a website is reachable

    Args:
        url: The URL to check
        verify_ssl: Whether to verify SSL certificates (default: False)

    Returns:
        tuple: (status, result) where status is 'reachable' or 'unreachable'
              and result is either response time or error message
    """
    try:
        # Parse the URL correctly
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = urljoin(base_url, "/robots.txt")
        
        response = requests.get(robots_url, headers=headers, timeout=15, verify=verify_ssl)
        
        if response.status_code == 200:
            return "reachable", response.elapsed.total_seconds()
        elif response.status_code == 404:
            # Retry with root URL if robots.txt not found
            response = requests.get(url, headers=headers, timeout=15, verify=verify_ssl)
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


def check_significant_websites(
    websites: List[str],
    args: argparse.Namespace,
    max_retries: int = 1,
    retry_delay: int = 5
) -> Tuple[List[Tuple[str, float]], List[Tuple[str, str]]]:
    """
    Check the reachability of multiple websites with configurable retry behavior

    Args:
        websites: List of website URLs to check
        args: Command line arguments
        max_retries: Maximum number of retry attempts (default: 1)
        retry_delay: Delay between retries in seconds (default: 5)
    """

    # Initialize lists to store reachable and unreachable websites
    reachable_websites = []
    unreachable_websites = []

    # First round of checks
    for url in websites:
        status, result = check_website(url)
        if status == "reachable":
            reachable_websites.append((url, result))
        else:
            unreachable_websites.append((url, result))

    # Retry logic with configurable attempts
    retry_count = 0
    while unreachable_websites and retry_count < max_retries:
        retry_count += 1
        # print(f"\nRetry attempt {retry_count} of {max_retries}...\n")
        if not args.silent:
            speak_text(f"Retrying unreachable websites, attempt {retry_count}...")
        time.sleep(retry_delay)

        remaining_unreachable = []
        for url, error in unreachable_websites:
            status, retry_result = check_website(url)
            if status == "reachable":
                reachable_websites.append((url, retry_result))
            else:
                remaining_unreachable.append((url, retry_result))

        unreachable_websites = remaining_unreachable

    return reachable_websites, unreachable_websites


def main(silent=False, polite=False) -> str:
    """
    Check the reachability of significant websites

    Args:
        silent: Whether to disable text-to-speech output (default: False)
        polite: Whether to use more polite phrasing in output (default: False)

    Returns:
        str: Summary of website checks
    """
    # Only parse args if called from command line (with no arguments)
    if silent is False and polite is False:  # Default values, likely called from command line
        parser = argparse.ArgumentParser(description='Check the reachability of significant websites')
        parser.add_argument('--silent', action='store_true', help='Disable text-to-speech output')
        parser.add_argument('--polite', action='store_true', help='Use more polite phrasing in output')
        args = parser.parse_args()
    else:
        # Create args namespace for programmatic calls
        args = argparse.Namespace(silent=silent, polite=polite)

    intro_statement = (
        "Initiating connectivity checks on several major technology provider websites and selected government websites, "
        "verifying their current reachability. Should one of these significant sites be fully unreachable, "
        "it may suggest a broader infrastructural fault or a critical disruption in global online communications."
    )

    # print(f"{intro_statement}")
    if not args.silent:
        speak_text(f"{intro_statement}")

    reachable, unreachable = check_significant_websites(list_of_significant_websites, args)

    report_on_significant_websites = ""

    # print("Reachable Websites:")
    report_on_significant_websites += "Reachable Websites:\n"

    for url, response_time in reachable:
        # print(f"- {url}: Response Time: {response_time:.6f} seconds")
        report_on_significant_websites += f"- {url}: Response Time: {response_time:.6f} seconds"
    
    if len(unreachable) == 0:
        all_reachable_statement = ("\nSummary of reachability of major tech and government websites:\nAll websites are "
                                   "reachable.")
        # print(f"{all_reachable_statement}")
        report_on_significant_websites += all_reachable_statement
    
    else:
        # print("\nUnreachable Websites:")
        report_on_significant_websites += "\nUnreachable Websites:\n"

        for url, error in unreachable:
            # print(f"- {url}: {error}")
            report_on_significant_websites += f"- {url}: {error}"

    significant_website_checks_summary = summarize_service_check_output(report_on_significant_websites)

    # print(f"{significant_website_checks_summary}")

    # Add the summary to the combined summaries
    add_to_combined_summaries(significant_website_checks_summary)

    if not args.silent:
        speak_text( "The summary of checking significant websites is as follows:")
        speak_text(f"{significant_website_checks_summary}")

    return significant_website_checks_summary

if __name__ == "__main__":
    main()
