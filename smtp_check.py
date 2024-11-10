import socket

# SMTP servers to monitor
smtp_servers = {
    "Gmail": ("smtp.gmail.com", 587),
    "Outlook/O365": ("smtp.office365.com", 587),
    "Yahoo": ("smtp.mail.yahoo.com", 587),
    "iCloud Mail": ("smtp.mail.me.com", 587),
    "AOL Mail": ("smtp.aol.com", 587),
    "Zoho Mail": ("smtp.zoho.com", 587),
    "Mail.com": ("smtp.mail.com", 587),
    "GMX Mail": ("smtp.gmx.com", 587),
    "Fastmail": ("smtp.fastmail.com", 587)
}

def check_smtp_server(name, server_info):
    """Attempt to connect to the SMTP server to verify availability."""
    host, port = server_info
    try:
        # Establish a socket connection
        with socket.create_connection((host, port), timeout=10) as sock:
            print(f"Successfully connected to {name} at {host}:{port}")
            return "reachable"
    except Exception as e:
        print(f"Failed to connect to {name} at {host}:{port}: {e}")
        return f"unreachable: {e}"

if __name__ == "__main__":
    reachable_servers = []
    unreachable_servers = []

    # Check each SMTP server
    for name, server_info in smtp_servers.items():
        status = check_smtp_server(name, server_info)
        if status == "reachable":
            reachable_servers.append(name)
        else:
            unreachable_servers.append((name, status))

    # Report results
    print("\nReachable SMTP Servers:")
    for server in reachable_servers:
        print(f"- {server}")

    if len(unreachable_servers) == 0:
        print("\nAll SMTP servers are reachable.")
    else:
        print("\nUnreachable SMTP Servers:")
        for server, error in unreachable_servers:
            print(f"- {server}: {error}")