import subprocess
import time
import argparse
from service_check_summarizer import summarize_service_check_output
from tts_utils import speak_text
from os_utils import get_os_type
import whois
from summary_utils import add_to_combined_summaries

# WHOIS servers and their IP addresses
# The IP addresses are hardcoded here just in case DNS resolving is down,
# but in a real-world scenario, they should be resolved dynamically
# The structure is: "whois_server_name": ("whois_server_description", "whois_server_ip")
whois_servers_dict = {
    "whois.apnic.net": (
    "APNIC WHOIS server for IP address and AS number allocation in the Asia-Pacific region", "202.12.29.140"),
    "whois.ripe.net": ("RIPE NCC WHOIS server for European IP addresses and AS number registrations", "193.0.6.135"),
    "whois.arin.net": ("ARIN WHOIS server for North American IP address and ASN allocations", "199.212.0.43"),
    "whois.afrinic.net": ("AFRINIC WHOIS server for African IP address space and AS number management", "196.216.2.2"),
    "whois.lacnic.net": (
    "LACNIC WHOIS server for Latin American and Caribbean IP address registrations", "200.3.14.10"),
    "whois.pir.org": ("Public Interest Registry WHOIS server for dot ORG domain registrations", "199.19.56.1"),
    "whois.educause.edu": (
    "EDUCAUSE WHOIS server for dot EDU domain name registrations in United States", "192.52.178.30"),
    "whois.iana.org": ("IANA WHOIS server for the root zone database and overall global IP address allocations to regional registries like ARIN and RIPE", "192.0.32.59"),
    "riswhois.ripe.net": ("RIPE RIS WHOIS server for BGP routing information and analysis", "193.0.19.33"),
    "whois.nic.mobi": ("Registry WHOIS server for dot MOBI top-level domain registrations", "194.169.218.57"),
    "whois.verisign-grs.com": ("Verisign Global Registry WHOIS server for looking up dot COM and dot NET domains", "199.7.59.74"),
    "whois.nic.google": ("Google Registry WHOIS server for Google-operated TLD registrations", "216.239.32.10"),
    "whois.nic.io": ("Internet Computer Bureau WHOIS server for .io domain registrations", "193.223.78.42"),
    "whois.nic.co": (".CO Internet S.A.S. WHOIS server for .co domain registrations", "156.154.100.224"),
    "whois.nic.xyz": ("XYZ.COM LLC WHOIS server for .xyz domain registrations", "185.24.64.96"),
    "whois.nic.club": (".CLUB Domains, LLC WHOIS server for .club domain registrations", "108.59.160.175"),
    "whois.nic.info": ("Afilias WHOIS server for .info domain registrations", "199.19.56.1"),
    "whois.nic.biz": ("Neustar WHOIS server for .biz domain registrations", "156.154.100.224"),
    "whois.nic.us": ("NeuStar, Inc. WHOIS server for .us domain registrations", "156.154.100.224"),
    "whois.nic.tv": ("Verisign WHOIS server for .tv domain registrations", "192.42.93.30"),
    "whois.nic.asia": ("DotAsia WHOIS server for .asia domain registrations", "203.119.86.101"),
    "whois.nic.me": ("doMEn WHOIS server for .me domain registrations", "185.24.64.96"),
    "whois.nic.pro": ("RegistryPro WHOIS server for .pro domain registrations", "199.7.59.74"),
    "whois.nic.museum": ("Museum Domain Management Association WHOIS server for .museum domain registrations", "130.242.24.5"),
    "whois.nic.ai": ("Government of Anguilla WHOIS server for .ai domain registrations", "209.59.119.34"),
    "whois.nic.de": ("DENIC eG WHOIS server for .de domain registrations", "81.91.164.5"),
    "whois.registry.in": ("National Internet Exchange of India WHOIS server for .in domain registrations for India", "103.132.247.21"),
    "whois.jprs.jp": ("Japan Registry Services Co., Ltd. WHOIS server for .jp domain registrations for Japan", "117.104.133.169"),
    "whois.nic.fr": ("AFNIC WHOIS server for .fr domain registrations for France", "192.134.5.73"),
    "whois.registro.br": ("Comitê Gestor da Internet no Brasil WHOIS server for .br domain registrations for Brazil", "200.160.2.3"),
    "whois.nic.uk": ("Nominet UK WHOIS server for .uk domain registrations for the UK", "213.248.242.79"),
    "whois.auda.org.au": ("auDA WHOIS server for .au domain registrations for Australia", "199.15.80.233"),
    "whois.nic.it": ("IIT - CNR WHOIS server for .it domain registrations for Italy", "192.12.192.242"),
    "whois.cira.ca": ("Canadian Internet Registration Authority WHOIS server for .ca domain registrations", "192.228.29.2"),
    "whois.kr": ("KISA WHOIS server for .kr domain registrations for South Korea", "49.8.14.101")
}


def run_whois_command(whois_server_name, whois_server_ip):
    """Run the whois command for a specific server and IP."""

    try:

        if get_os_type() == "macOS" or get_os_type() == "Linux":

            result = subprocess.run(['whois', '-h', whois_server_name, whois_server_ip],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    timeout=10)

            if result.returncode == 0:

                return "reachable", None
            else:
                return "unreachable", result.stderr.decode().strip()

        elif get_os_type() == "Windows":
            try:
                extracted_domain = whois.extract_domain(whois_server_name)
                if extracted_domain is None:
                    print(f"Failed to extract domain from {whois_server_name}")
                    speak_text(f"Failed to extract domain from {whois_server_name}")
                    speak_text("Things don't seem to be going well attempting to execute whois checks from Windows.")
                    return "unreachable", f"Failed to extract domain from {whois_server_name}"

                try:
                    whois_server_domain = extracted_domain
                    whois_domain_result = whois.whois(whois_server_domain)
                    print(whois_domain_result.text)
                    return "reachable", None
                except Exception as e:
                    print(f"Failed to run whois command for {whois_server_name} with IP {whois_server_ip}")
                    # speak_text(f"Failed to run whois command for {whois_server_name} with IP {whois_server_ip}")
                    print(f"Specifically, the error was: {e}")
                    return "unreachable", str(e)

            except Exception as e:
                print(f"No idea what went wrong here.")
                # speak_text(f"No idea what went wrong here.")
                print(f"But the error was: {e}")
                # speak_text(f"But the error was: {e}")
                return "unreachable", str(e)

    except Exception as e:
        print(f"Reached the last except block in the run_whois_command function.")
        # speak_text(f"Reached the last except block in the run_whois_command function.")
        print(f"And so the error was: {e}")
        # speak_text(f"And so the error was: {e}")
        return "unreachable", str(e)


def check_whois_servers(servers):
    reachable_servers = []
    unreachable_servers = []
    whois_results = ""

    # First round of checks
    for whois_server_name, (whois_server_description, ip) in servers.items():

        status, error = run_whois_command(whois_server_name, ip)
        if status == "reachable":
            reachable_servers.append((whois_server_name, whois_server_description))
            whois_results += f"{whois_server_name} was reachable. It is the {whois_server_description}.\n"

        else:
            unreachable_servers.append((whois_server_name, error, whois_server_description))
            whois_results += f"{whois_server_name} was unreachable. The error was: {error}. It is the {whois_server_description}.\n"

    # Retry unreachable servers after a delay
    if unreachable_servers:
        whois_results += "\nRetrying unreachable servers...\n"
        time.sleep(5)  # Wait 5 seconds before retrying

        remaining_unreachable = []
        for whois_server_name, error, whois_server_description in unreachable_servers:
            status, retry_error = run_whois_command(whois_server_name, ip)
            if status == "reachable":
                reachable_servers.append((whois_server_name, whois_server_description))
                whois_results += f"After retrying, {whois_server_name} was reachable.\n"

            else:
                remaining_unreachable.append((whois_server_name, error, whois_server_description))
                whois_results += f"After retrying, {whois_server_name} was still unreachable. The error was: {error}.\n"

        unreachable_servers = remaining_unreachable  # Update unreachable after retry
        whois_results += "\nUnreachable servers that could not be reached even after retry:\n"
        for whois_server_name, error, whois_server_description in unreachable_servers:
            whois_results += f"- {whois_server_name}: Unreachable: Error: {error}\n"

    whois_results += "Reachable WHOIS Servers:\n"
    for whois_server_name, _ in reachable_servers:
        # print(f"{server}: Reachable")
        whois_results += f"- {whois_server_name}\n"

    if len(unreachable_servers) == 0:
        whois_results += "\nAll WHOIS servers were reachable.\n"
    else:
        whois_results += "\nUnreachable WHOIS Servers:\n"
        for whois_server_name, error, _ in unreachable_servers:
            whois_results += f"- {whois_server_name}: Unreachable\n"

    return whois_results


def main(silent=False, polite=False):
    args = argparse.Namespace(silent=silent, polite=polite)

    output = ""

    # Count how many WHOIS servers are being monitored
    num_servers = str(len(whois_servers_dict))

    print(f"Starting WHOIS server monitoring at {time.ctime()}\n")
    if not args.silent:
        speak_text("Starting WHOIS server monitoring.")
        speak_text(f"This will check the reachability of {num_servers} WHOIS servers. So this could take several minutes.")

    results = check_whois_servers(whois_servers_dict)

    output += f"Starting WHOIS server monitoring at {time.ctime()}\n"
    print(f"{results}")

    # Send the results to service_check_summary.py and ask for a summary
    summary_output = summarize_service_check_output(results)

    # Print the summary received from service_check_summary.py
    output += f"\nSummary of WHOIS server monitoring: \n---\n{summary_output}\n---\n"
    print(f"{summary_output}")

    # Add the summary to the combined summaries
    add_to_combined_summaries(summary_output)

    if not args.silent:
        speak_text("The WHOIS server monitoring report is as follows:")
        speak_text(f"{summary_output}")

    return summary_output

if __name__ == "__main__":
    main()
