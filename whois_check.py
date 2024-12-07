import subprocess
import time
import argparse
from service_check_summarizer import summarize_service_check_output

whois_servers = {
    "whois.apnic.net": ("APNIC WHOIS server for IP address and AS number allocation in Asia-Pacific region", "202.12.29.140"),
    "whois.ripe.net": ("RIPE NCC WHOIS server for European IP addresses and AS number registrations", "193.0.6.135"),
    "whois.arin.net": ("ARIN WHOIS server for North American IP address and ASN allocations", "199.212.0.43"),
    "whois.afrinic.net": ("AFRINIC WHOIS server for African IP address space and AS number management", "196.216.2.2"),
    "whois.lacnic.net": ("LACNIC WHOIS server for Latin American and Caribbean IP address registrations", "200.3.14.10"),
    "whois.pir.org": ("Public Interest Registry WHOIS server for .ORG domain registrations", "199.19.56.1"),
    "whois.educause.edu": ("EDUCAUSE WHOIS server for .EDU domain name registrations in United States", "192.52.178.30"),
    "whois.iana.org": ("IANA WHOIS server for root zone database and global IP address allocations", "192.0.32.59"),
    "riswhois.ripe.net": ("RIPE RIS WHOIS server for BGP routing information and analysis", "193.0.19.33"),
    "whois.nic.mobi": ("Registry WHOIS server for .MOBI top-level domain registrations", "194.169.218.57"),
    "whois.verisign-grs.com": ("Verisign Global Registry WHOIS server for .COM and .NET domains", "199.7.59.74"),
    "whois.nic.google": ("Google Registry WHOIS server for Google-operated TLD registrations", "216.239.32.10")
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
    whois_results = ""

    # First round of checks
    for server, (region, ip) in servers.items():
        status, error = run_whois_command(server, ip)
        if status == "reachable":
            reachable_servers.append((server, region))
            # print(f"{server}: Reachable. {region} region")
            whois_results += f"{server}: Reachable. {region} region\n"
        else:
            unreachable_servers.append((server, error, region))
            # print(f"{server}: Unreachable: {error}. {region} region")
            whois_results += f"{server}: Unreachable: {error}. {region} region\n"

    # Retry unreachable servers after a delay
    if unreachable_servers:
        whois_results += "\nRetrying unreachable servers...\n"
        time.sleep(5)  # Wait 5 seconds before retrying

        remaining_unreachable = []
        for server, error, region in unreachable_servers:
            status, retry_error = run_whois_command(server, whois_servers[server][1])
            if status == "reachable":
                reachable_servers.append((server, region))
                # print(f"{server}: Reachable after retry. {region} region")
                whois_results += f"{server}: Reachable\n"
            else:
                remaining_unreachable.append((server, error, region))
                # print(f"{server}: Unreachable: {error}. {region} region")
                whois_results += f"{server}: Unreachable: {error}\n"

        unreachable_servers = remaining_unreachable  # Update unreachable after retry
        whois_results += "\nUnreachable servers that could not be reached even after retry:\n"
        for server, error, region in unreachable_servers:
            # print(f"{server}: Unreachable: {error}. {region} region")
            whois_results += f"- {server}: Unreachable: {error}\n"

    whois_results += "Reachable WHOIS Servers:\n"
    for server, _ in reachable_servers:
        # print(f"{server}: Reachable")
        whois_results += f"- {server}\n"

    if len(unreachable_servers) == 0:
        # print("All WHOIS servers are reachable.")
        whois_results += "\nAll WHOIS servers are reachable.\n"
    else:
        whois_results += "\nUnreachable WHOIS Servers:\n"
        for server, error, _ in unreachable_servers:
            # print(f"{server}: Unreachable: {error}")
            whois_results += f"- {server}: Unreachable\n"

    return whois_results


import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Monitor WHOIS servers.')
    parser.add_argument('--silent', action='store_true', help='Run in silent mode without voice alerts')
    args = parser.parse_args()

    output = ""
    print(f"Starting WHOIS server monitoring at {time.ctime()}\n")
    if not args.silent:
        subprocess.run(["say", "Starting WHOIS server monitoring."])
        subprocess.run(["say", "This will check the reachability of several WHOIS servers."])


    results = check_whois_servers(whois_servers)

    output += f"Starting WHOIS server monitoring at {time.ctime()}\n"
    print(results)
    # if not args.silent:
    #     subprocess.run(["say", results])

   # Send the results to service_check_summary.py and ask for a summary
    summary_output = summarize_service_check_output(results)

    # Print the summary received from service_check_summary.py
    output += f"\nSummary of WHOIS server monitoring: \n---\n{summary_output}\n---\n"
    print(summary_output)

    if not args.silent:
        subprocess.run(["say", "The WHOIS server monitoring report is as follows:"])
        subprocess.run(["say", summary_output])