import subprocess
from abuse_check import check_ip_reputation, analyze_ip_reputation
from service_check_summarizer import summarize_service_check_output
from report_source_location import get_public_ip
import argparse


def main():
    global ip_reputation_output
    parser = argparse.ArgumentParser(description="Fetch and report external IP address.")
    parser.add_argument('--silent', action='store_true', help="Run without voice announcements")
    args = parser.parse_args()

    AbuseIPDB_API_KEY = subprocess.check_output(["/opt/homebrew/bin/op", "read", "op://Private/AbuseIPDB/AbuseIPDB_API_KEY"]).decode('utf-8').strip()

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
                subprocess.run(["say", ip_reputation_summary])
        except Exception as e:
            print("Failed to summarize service check output.")
            print(e)


    else:
        print("Failed to retrieve reputation data from Abuse IPDB API.")

if __name__ == "__main__":
    main()

