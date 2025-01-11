import argparse
import socket
from service_check_summarizer import summarize_service_check_output
from tts_utils import speak_text
from summary_utils import add_to_combined_summaries

# IMAP servers to monitor
imap_servers = {
    "Gmail": ("imap.gmail.com", 993),
    "Outlook/O365": ("outlook.office365.com", 993),
    "Yahoo": ("imap.mail.yahoo.com", 993),
    "iCloud Mail": ("imap.mail.me.com", 993),
    "AOL Mail": ("imap.aol.com", 993),
    "Zoho Mail": ("imap.zoho.com", 993),
    "Mail.com": ("imap.mail.com", 993),
    "GMX Mail": ("imap.gmx.com", 993),
    "Fastmail": ("imap.fastmail.com", 993)
}

def check_imap_server(name, server_info):
    """Attempt to connect to the IMAP server to verify availability."""
    host, port = server_info
    try:
        # Establish a socket connection
        with socket.create_connection((host, port), timeout=10) as sock:
            print(f"Successfully connected to {name} at {host}:{port}")
            return "reachable"
    except Exception as e:
        print(f"Failed to connect to {name} at {host}:{port}: {e}")
        return f"unreachable: {e}"

def main(silent=False, polite=False):
    args = argparse.Namespace(silent=silent, polite=polite)

    # Create a couple of lists to store reachable and unreachable servers
    reachable_servers = []
    unreachable_servers = []

    print("Checking IMAP server availability...")
    if not args.silent:
        speak_text( "Checking IMAP server availability.")

    print(f"This script checks the availability of {len(imap_servers)} of the most common IMAP servers.")
    if not args.silent:
        speak_text( f"This script checks the availability of {len(imap_servers)} of the most common IMAP servers.")

    print(f"IMAP is a protocol used to retrieve email messages from an email server.")

    if not args.silent:
        speak_text( "IMAP is a protocol used to retrieve email messages from an email server.")

    # Check each IMAP server
    for name, server_info in imap_servers.items():
        status = check_imap_server(name, server_info)
        if status == "reachable":
            reachable_servers.append(name)
        else:
            unreachable_servers.append((name, status))

    imap_check_results = f"Report on Reachable and Unreachable IMAP Servers:\n"

    # Report results
    print("\nReachable IMAP Servers:")
    imap_check_results += "Reachable IMAP Servers:\n"
    for server in reachable_servers:
        print(f"- {server}")
        imap_check_results += ''.join([str(x) for x in reachable_servers])

    if len(unreachable_servers) == 0:
        print("\nAll IMAP servers are reachable")
        imap_check_results += "\nAll IMAP servers are reachable\n"

    else:
        print("\nUnreachable IMAP Servers:")
        imap_check_results += "\nUnreachable IMAP Servers:\n"
        for server, error in unreachable_servers:
            print(f"- {server}: {error}")
            imap_check_results += ''.join([str(x) for x in unreachable_servers])

            # imap_check_results = f"Report on Reachable and Unreachable IMAP Servers:\n"
    # imap_check_results += ''.join([str(x) for x in reachable_servers]) + '\n' + ''.join([str(x) for x in unreachable_servers])

    imap_output_summary = summarize_service_check_output(imap_check_results)
    print(f"{imap_output_summary}")

    # Add the summary to the combined summaries
    add_to_combined_summaries(imap_output_summary)

    if not args.silent:
        speak_text("The IMAP monitoring report is as follows:")
        speak_text(f"{imap_output_summary}")

if __name__ == "__main__":
    main()
