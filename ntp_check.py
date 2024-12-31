import argparse
import ntplib
import time
from datetime import datetime, timezone
from service_check_summarizer import summarize_service_check_output
from tts_utils import speak_text
from summary_utils import add_to_combined_summaries

# List of well-known NTP servers
ntp_servers = [
    "time.google.com",
    "time1.google.com",
    "time2.google.com",
    "time3.google.com",
    "time4.google.com",
    "time.nist.gov",
    "time.windows.com",
    "pool.ntp.org",
    "time.apple.com",            # Apple NTP server
    "ntp2.usno.navy.mil",        # US Navy NTP server
    "tick.usno.navy.mil",        # US Military NTP server (USNO)
    "tock.usno.navy.mil"         # US Military NTP server (USNO)
]

def check_ntp_server(server):
    """Query an NTP server and check for a valid response."""
    client = ntplib.NTPClient()
    try:
        # Query the NTP server
        response = client.request(server, version=3, timeout=5)
        # Check if the response is valid by comparing local and server times
        server_time = datetime.fromtimestamp(response.tx_time, tz=timezone.utc)
        return "reachable", server_time
    except Exception as e:
        return "unreachable", str(e)

def check_ntp_servers(servers):
    reachable_servers = []
    unreachable_servers = []

    # First round of checks
    for ntp_server in servers:
        status, result = check_ntp_server(ntp_server)
        if status == "reachable":
            reachable_servers.append((ntp_server, result))
        else:
            unreachable_servers.append((ntp_server, result))

    # Retry unreachable servers after a delay
    if unreachable_servers:
        print("\nRetrying unreachable servers...\n")
        time.sleep(5)  # Wait 5 seconds before retrying

        remaining_unreachable = []
        for ntp_server, error in unreachable_servers:
            status, retry_result = check_ntp_server(ntp_server)
            if status == "reachable":
                reachable_servers.append((ntp_server, retry_result))
            else:
                remaining_unreachable.append((ntp_server, retry_result))

        unreachable_servers = remaining_unreachable  # Update unreachable after retry

    return reachable_servers, unreachable_servers

def main():
    # Accept arguments from the command line, such as --silent
    parser = argparse.ArgumentParser(description='Monitor NTP servers.')
    parser.add_argument('--silent', action='store_true', help='Run in silent mode without voice alerts')
    args = parser.parse_args()

    if not args.silent:
        speak_text( "Starting NTP server monitoring.")

    print(f"This script will check the reachability of several of the most commonly used NTP servers around the "
          f"western world.\n")

    ntp_check_results = ("NTP servers function as authoritative time sources, employing a hierarchical system of "
                         "stratum layers and precision algorithms to ensure synchronized time across distributed "
                         "computing systems. Their importance lies in the strict temporal alignment they provide, "
                         "enabling coordinated actions, event correlation, and the prevention of cascading errors in "
                         "networked environments.\n\n")



    reachable, unreachable = check_ntp_servers(ntp_servers)
    
    print("Reachable NTP Servers:")
    ntp_check_results += "Reachable NTP Servers:\n"

    for server, server_time in reachable:
        print(f"- {server}: Server Time: {server_time}")
        ntp_check_results += f"- {server}: Server Time: {server_time}\n"
    
    if len(unreachable) == 0:
        print("\nAll NTP servers are reachable.")
        ntp_check_results += "\nAll NTP servers are reachable.\n"

    else:
        print("\nUnreachable NTP Servers:")
        ntp_check_results += "\nUnreachable NTP Servers:\n"

        for server, error in unreachable:
            print(f"- {server}: {error}")
            ntp_check_results += f"- {server}: {error}\n"

    ntp_summary = summarize_service_check_output(ntp_check_results)

    print(f"{ntp_summary}")

    # Add the summary to the combined summaries
    add_to_combined_summaries(ntp_summary)

    if not args.silent:
        speak_text("The NTP server monitoring report is as follows:")
        speak_text(f"{ntp_summary}")

if __name__ == "__main__":
    main()
