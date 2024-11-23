import dns.resolver
import time

# List of DNS root servers
dns_root_servers = {
    "A": "198.41.0.4",
    "B": "199.9.14.201",
    "C": "192.33.4.12",
    "D": "199.7.91.13",
    "E": "192.203.230.10",
    "F": "192.5.5.241",
    "G": "192.112.36.4",
    "H": "198.97.190.53",
    "I": "192.36.148.17",
    "J": "192.58.128.30",
    "K": "193.0.14.129",
    "L": "199.7.83.42",
    "M": "202.12.27.33"
}

def check_dns_server(ip, query_name="example.com"):
    """Send a DNS query to the root server."""
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5
        resolver.nameservers = [ip]

        # Perform an A record query
        answer = resolver.resolve(query_name, "A")
        return "reachable", None
    except Exception as e:
        return "unreachable", str(e)

def check_dns_root_servers(servers):
    reachable_servers = []
    unreachable_servers = []

    # First round of checks
    for name, ip in servers.items():
        status, error = check_dns_server(ip)
        if status == "reachable":
            reachable_servers.append(name)
        else:
            unreachable_servers.append((name, error))

    # Retry unreachable servers after a delay
    if unreachable_servers:
        print("\nRetrying unreachable servers...\n")
        time.sleep(5)  # Wait 5 seconds before retrying

        remaining_unreachable = []
        for name, error in unreachable_servers:
            status, retry_error = check_dns_server(dns_root_servers[name])
            if status == "reachable":
                reachable_servers.append(name)
            else:
                remaining_unreachable.append((name, retry_error))

        unreachable_servers = remaining_unreachable  # Update unreachable after retry

    return reachable_servers, unreachable_servers

if __name__ == "__main__":
    reachable, unreachable = check_dns_root_servers(dns_root_servers)
    print("Reachable DNS Root Servers:")
    for server in reachable:
        print(f"- {server}")
    
    if len(unreachable) == 0:
        print("\nDNS Root Servers reachability summary: All DNS Root Servers are reachable.")

    else:
        print("\nUnreachable DNS Root Servers:")
        for server, error in unreachable:
            print(f"- {server}: {error}")