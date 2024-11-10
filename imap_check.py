import socket

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

if __name__ == "__main__":
    reachable_servers = []
    unreachable_servers = []

    # Check each IMAP server
    for name, server_info in imap_servers.items():
        status = check_imap_server(name, server_info)
        if status == "reachable":
            reachable_servers.append(name)
        else:
            unreachable_servers.append((name, status))

    # Report results
    print("\nReachable IMAP Servers:")
    for server in reachable_servers:
        print(f"- {server}")

    if len(unreachable_servers) == 0:
        print("\nAll IMAP servers are reachable")
        
    else:
        print("\nUnreachable IMAP Servers:")
        for server, error in unreachable_servers:
            print(f"- {server}: {error}")