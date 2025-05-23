import subprocess
from abuse_check import check_ip_reputation, analyze_ip_reputation
from service_check_summarizer import summarize_service_check_output
from report_source_location import get_public_ip
import argparse
from tts_utils import speak_text
from os_utils import get_os_type
import shutil
import os
from summary_utils import add_to_combined_summaries
from colorama import Fore, Style, init

# Initialize colorama for cross-platform color support
init(autoreset=True)


def main(silent=False, polite=False):
    global ip_reputation_output
    args = argparse.Namespace(silent=silent, polite=polite)

    # Try to find the `op` command
    op_path = shutil.which("op")

    # If not found, check a common fallback directory
    if op_path is None:
        fallback_path = os.path.join(
            os.environ.get("USERPROFILE", "C:\\Users\\Default"),
            "AppData",
            "Local",
            "Microsoft",
            "WinGet",
            "Links",
            "op.exe"
        )
        if os.path.exists(fallback_path):
            op_path = fallback_path
        elif get_os_type() == "Windows":  # Windows
            op_path = r"C:\Program Files\1Password CLI\op.exe"
        elif get_os_type() == "Darwin":  # macOS
            op_path = "/opt/homebrew/bin/op"
        elif get_os_type() == "Linux":
            op_path = "/usr/local/bin/op"
        else:
            raise FileNotFoundError(f"{Fore.RED}The `op` command could not be found. Ensure it is installed and in your PATH.{Style.RESET_ALL}")

    try:
        # Get the $ABUSEIPDB_API_KEY from the environment variable
        # or from 1Password

        AbuseIPDB_API_KEY = os.environ.get("ABUSEIPDB_API_KEY")

        if not AbuseIPDB_API_KEY:
            # If the environment variable is not set, read from 1Password
            AbuseIPDB_API_KEY = subprocess.check_output([op_path, "read", "op://Shared/AbuseIPDB/AbuseIPDB_API_KEY"]).decode('utf-8').strip()

    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Failed to read the AbuseIPDB API key.{Style.RESET_ALL}")
        print(f"{Fore.RED}Maybe 1Password is not running, not unlocked, or the item is missing.{Style.RESET_ALL}")
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

        # speak_text("Failed to read the AbuseIPDB API key. Please check the 1Password app.")
        # speak_text("Make sure it is running, unlocked, and the API key item is available.")
        return

    # external_ip = get_current_external_ip(args.silent)  # Get the current external IP
    external_ip = get_public_ip()

    # Check reputation of the external IP
    reputation_data = check_ip_reputation(external_ip, AbuseIPDB_API_KEY)

    # print("Reputation data:", reputation_data)

    # Analyze and display the results
    if reputation_data:

        try:
            ip_reputation_output = analyze_ip_reputation(reputation_data)
            # print("IP Reputation Analysis Output:", ip_reputation_output)

        except Exception as e:
            print(f"{Fore.RED}Failed to analyze IP reputation data.{Style.RESET_ALL}")
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")

        try:
            ip_reputation_summary = summarize_service_check_output(ip_reputation_output)
            print(f"{Style.DIM}Received AI reputation summary: '{ip_reputation_summary}'{Style.RESET_ALL}")

            # Add the summary to the combined summaries
            add_to_combined_summaries(ip_reputation_summary)

            # if not args.silent:
            #     speak_text(f"{ip_reputation_summary}")
        except Exception as e:
            print(f"{Fore.RED}Failed to summarize service check output.{Style.RESET_ALL}")
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")


    else:
        print(f"{Fore.RED}Failed to retrieve reputation data from Abuse IPDB API.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()

