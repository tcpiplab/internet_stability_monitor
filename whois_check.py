import subprocess
import time

# List of WHOIS servers and their corresponding IP addresses
whois_servers = {
    "whois.apnic.net": "202.12.29.140",    # APNIC (Asia-Pacific)
    "whois.ripe.net": "193.0.6.135",       # RIPE (Europe)
    "whois.arin.net": "199.212.0.43",      # ARIN (North America)
    "whois.afrinic.net": "196.216.2.2",    # AFRINIC (Africa)
    "whois.lacnic.net": "200.3.14.10",     # LACNIC (Latin America)
    "whois.pir.org": "199.19.56.1",        # Public Interest Registry (ORG)
    "whois.educause.edu": "192.52.178.30", # EDUCAUSE (EDU)
    "whois.iana.org": "192.0.32.59",       # IANA (Internet Assigned Numbers Authority)
    "riswhois.ripe.net": "193.0.19.33",    # RIS (RIPE Routing Information Service)
    "whois.nic.mobi": "194.169.218.57",    # .mobi TLD
    "whois.verisign-grs.com": "199.7.59.74",  # Verisign (COM/NET)
    "whois.nic.google": "216.239.32.10"    # .google TLD
}

def run_whois_command(server, ip):
    """Run the whois command for a specific server and IP."""
    try:
        # Use the whois command with the server's IP
        result = subprocess.run(['whois', '-h', server, ip], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE, 
                                timeout=10)
        if result.returncode == 0:
            return "reachable", None
        else:
            return "unreachable", result.stderr.decode().strip()
    except Exception as e:
        return "unreachable", str(e)

def check_whois_servers(servers):
    reachable_servers = []
    unreachable_servers = []

    # First round of checks
    for server, ip in servers.items():
        status, error = run_whois_command(server, ip)
        if status == "reachable":
            reachable_servers.append(server)
        else:
            unreachable_servers.append((server, error))

    # Retry unreachable servers after a delay
    if unreachable_servers:
        print("\nRetrying unreachable servers...\n")
        time.sleep(5)  # Wait 5 seconds before retrying

        remaining_unreachable = []
        for server, error in unreachable_servers:
            status, retry_error = run_whois_command(server, whois_servers[server])
            if status == "reachable":
                reachable_servers.append(server)
            else:
                remaining_unreachable.append((server, retry_error))

        unreachable_servers = remaining_unreachable  # Update unreachable after retry

    return reachable_servers, unreachable_servers

if __name__ == "__main__":
    reachable, unreachable = check_whois_servers(whois_servers)
    print("Reachable WHOIS Servers:")
    for server in reachable:
        print(f"- {server}")
    
    if len(unreachable) == 0:
        print("\nAll WHOIS servers are reachable.")

    else:
        print("\nUnreachable WHOIS Servers:")
        for server, error in unreachable:
            print(f"- {server}: {error}")