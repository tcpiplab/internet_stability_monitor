import subprocess
from abuse_check import check_ip_reputation, analyze_ip_reputation
from service_check_summarizer import summarize_service_check_output
from report_source_location import get_public_ip
import argparse
from tts_utils import speak_text
from os_utils import get_os_type
import shutil
import os


def main():
    global ip_reputation_output
    parser = argparse.ArgumentParser(description="Fetch and report external IP address.")
    parser.add_argument('--silent', action='store_true', help="Run without voice announcements")
    args = parser.parse_args()

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
            raise FileNotFoundError("The `op` command could not be found. Ensure it is installed and in your PATH.")

    AbuseIPDB_API_KEY = subprocess.check_output([op_path, "read", "op://Private/AbuseIPDB/AbuseIPDB_API_KEY"]).decode('utf-8').strip()

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
            print("Failed to analyze IP reputation data.")
            print(e)

        try:
            ip_reputation_summary = summarize_service_check_output(ip_reputation_output)
            print(f"Received AI reputation summary: {ip_reputation_summary}")
            if not args.silent:
                speak_text(ip_reputation_summary)
        except Exception as e:
            print("Failed to summarize service check output.")
            print(e)


    else:
        print("Failed to retrieve reputation data from Abuse IPDB API.")

if __name__ == "__main__":
    main()

