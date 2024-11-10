import ntplib
import time
from datetime import datetime, timezone

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
    for server in servers:
        status, result = check_ntp_server(server)
        if status == "reachable":
            reachable_servers.append((server, result))
        else:
            unreachable_servers.append((server, result))

    # Retry unreachable servers after a delay
    if unreachable_servers:
        print("\nRetrying unreachable servers...\n")
        time.sleep(5)  # Wait 5 seconds before retrying

        remaining_unreachable = []
        for server, error in unreachable_servers:
            status, retry_result = check_ntp_server(server)
            if status == "reachable":
                reachable_servers.append((server, retry_result))
            else:
                remaining_unreachable.append((server, retry_result))

        unreachable_servers = remaining_unreachable  # Update unreachable after retry

    return reachable_servers, unreachable_servers

if __name__ == "__main__":
    reachable, unreachable = check_ntp_servers(ntp_servers)
    
    print("Reachable NTP Servers:")
    for server, server_time in reachable:
        print(f"- {server}: Server Time: {server_time}")
    
    if len(unreachable) == 0:
        print("\nAll NTP servers are reachable.")

    else:
        print("\nUnreachable NTP Servers:")
        for server, error in unreachable:
            print(f"- {server}: {error}")