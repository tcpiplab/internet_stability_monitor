import dns.resolver
import time
import sys
import subprocess
from service_check_summarizer import summarize_service_check_output

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

def check_dns_server(name, ip, query_name="example.com"):
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5
        resolver.nameservers = [ip]
        resolver.resolve(query_name, "A")
        return f"- {name} ({ip})"
    except Exception as e:
        return f"- {name} ({ip}) - Error: {str(e)}"

def check_dns_root_servers(servers):
    reachable_servers = []
    unreachable_servers = []

    # First round of checks
    for name, ip in servers.items():
        result = check_dns_server(name, ip)
        if "Error:" in result:
            unreachable_servers.append(result)
        else:
            reachable_servers.append(result)

    # Retry unreachable servers after a delay, if desired
    if unreachable_servers:
        time.sleep(5)
        new_unreachable = []
        for entry in unreachable_servers:
            ip_part = entry.split('(')[1].split(')')[0]
            name_part = entry.split('- ')[1].split(' (')[0]
            retry_result = check_dns_server(name_part, ip_part)
            if "Error:" in retry_result:
                new_unreachable.append(retry_result)
            else:
                reachable_servers.append(retry_result)
        unreachable_servers = new_unreachable

    return reachable_servers, unreachable_servers

if __name__ == "__main__":
    silent = "--silent" in sys.argv

    report = ("This script checks the reachability of DNS Root Servers, which are crucial to the functioning of the "
              "internet. DNS Root Servers are responsible for providing the IP addresses of top-level domain (TLD) "
              "servers, which in turn provide the IP addresses of individual domain names. If DNS Root Servers are "
              "unreachable, it can cause widespread internet outages and disruptions.\n\n")

    reachable, unreachable = check_dns_root_servers(dns_root_servers)

    if reachable:
        report += "Reachable DNS Root Servers:\n"
        for server in reachable:
            report += server + "\n"

    if unreachable:
        report += "\nUnreachable DNS Root Servers:\n"
        for server in unreachable:
            report += server + "\n"

    if not unreachable:
        report += "\nDNS Root Servers reachability summary: All DNS Root Servers are reachable.\n"
    else:
        report += "\nDNS Root Servers reachability summary: Some DNS Root Servers are unreachable.\n"

    summary = summarize_service_check_output(report)

    # Print the final report and summary
    print(report)
    print("----- AI-Generated Summary -----")
    print(summary)

    # If not silent, use the 'say' command to speak the intro and summary
    if not silent:
        intro_lines = ("This script checks the reachability of DNS Root Servers, "
                       "which are crucial to the functioning of the internet.")
        subprocess.run(["say", intro_lines])
        subprocess.run(["say", summary])