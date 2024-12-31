import socket
import argparse
from service_check_summarizer import summarize_service_check_output
from tts_utils import speak_text
from summary_utils import add_to_combined_summaries

# SMTP servers to monitor
smtp_servers = {
    "Gmail": ("smtp.gmail.com", 587),
    "Outlook/O365": ("smtp.office365.com", 587),
    "Yahoo": ("smtp.mail.yahoo.com", 587),
    "iCloud Mail": ("smtp.mail.me.com", 587),
    "AOL Mail": ("smtp.aol.com", 587),
    "Zoho Mail": ("smtp.zoho.com", 587),
    "Mail.com": ("smtp.mail.com", 587),
    "GMX Mail": ("smtp.gmx.com", 587), # owned and operated by United Internet, a German Internet services firm
    "Fastmail": ("smtp.fastmail.com", 587)
}

def check_smtp_server(name, server_info, args):
    """Attempt to connect to the SMTP server to verify availability."""
    host, port = server_info
    try:
        # Establish a socket connection
        with socket.create_connection((host, port), timeout=10) as sock:
            print(f"Successfully connected to {name} at {host}:{port}")
            if not args.silent:
                speak_text( f"Successfully connected to {name}.")
            return "reachable"
    except Exception as e:
        print(f"Failed to connect to {name} at {host}:{port}: {e}")
        if not args.silent:
            speak_text( f"Failed to connect to {name} server: The error was: {e}")
        return f"unreachable: {e}"

def main(silent=False, polite=False):
    args = argparse.Namespace(silent=silent, polite=polite)

    intro_statement = (
        "Verifying the operational status of several important SMTP servers, "
        "confirming that all remain accessible and not reporting major delivery interruptions. "
        "If any server proves unreachable, it may suggest a broader mail routing failure or an underlying network issue. "
        "This check runs silently and may consume up to a minute. Pray remain patient..."
    )

    print(f"{intro_statement}")
    if not args.silent:
        speak_text(f"{intro_statement}")

    reachable_servers = []
    unreachable_servers = []

    report_on_smtp_servers = ""

    # Check each SMTP server
    for name, server_info in smtp_servers.items():
        status = check_smtp_server(name, server_info, args)
        if status == "reachable":
            reachable_servers.append(name)
        else:
            unreachable_servers.append((name, status))

    # Report results
    print("\nReachable SMTP Servers:")
    report_on_smtp_servers += "Reachable SMTP Servers:\n"

    for server in reachable_servers:
        print(f"- {server}")
        report_on_smtp_servers += f"- {server}\n"

    if len(unreachable_servers) == 0:
        print("\nAll SMTP servers are reachable.")
        report_on_smtp_servers += "\nAll SMTP servers are reachable.\n"

    else:
        print("\nUnreachable SMTP Servers:")
        report_on_smtp_servers += "\nUnreachable SMTP Servers:\n"

        for server, error in unreachable_servers:
            print(f"- {server}: {error}")
            report_on_smtp_servers += f"- {server}: {error}\n"

    smtp_server_checks_summary = summarize_service_check_output(report_on_smtp_servers)

    print(f"{smtp_server_checks_summary}")

    # Add the summary to the combined summaries
    add_to_combined_summaries(smtp_server_checks_summary)

    if not args.silent:
        speak_text(f"The summary of checking important SMTP servers is as follows:")
        speak_text(f"{smtp_server_checks_summary}")

if __name__ == "__main__":
    main()
