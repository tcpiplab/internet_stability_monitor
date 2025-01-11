import requests
import urllib3
import argparse
from service_check_summarizer import summarize_service_check_output
from tts_utils import speak_text
from summary_utils import add_to_combined_summaries

# Disable SSL warnings because we're only checking reachability, not certificate validity
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Updated OCSP and CRL URLs of major CAs to monitor
ca_endpoints = {
    "DigiCert OCSP": "http://ocsp.digicert.com",
    "DigiCert CRL": "http://crl3.digicert.com/sha2-ev-server-g1.crl",
    "Let's Encrypt OCSP": "http://e6.o.lencr.org",  # Updated Let's Encrypt OCSP
    "GlobalSign OCSP": "http://ocsp2.globalsign.com/rootr1",
    "Sectigo OCSP": "http://ocsp.sectigo.com",
    "Entrust OCSP": "http://ocsp.entrust.net",
    "IdenTrust OCSP": "http://ocsp.identrust.com"
}

def check_ca_endpoint(name, url, args):
    """Perform a GET request to verify if the endpoint is reachable."""
    try:
        # Use GET for Let's Encrypt with a longer timeout and ignoring SSL verification
        if "Let's Encrypt" in name:
            response = requests.get(url, timeout=30, verify=False)
        elif "Entrust" in name:
            response = requests.get(url, timeout=10)
        else:
            response = requests.head(url, timeout=10)
        
        if response.status_code == 200:
            print(f"Successfully reached {name} at {url}")
            if not args.silent:
                speak_text( f"Successfully reached {name}.")
            return "reachable"
        elif 300 <= response.status_code < 400:
            print(f"{name} at {url} returned status code {response.status_code} (redirect)")
            if not args.silent:
                speak_text( f"{name} and it returned status code {response.status_code} (redirect).")
            return "reachable (redirected)"
        else:
            print(f"{name} at {url} returned status code {response.status_code}")
            if not args.silent:
                speak_text( f"The {name} server returned status code {response.status_code}. So we're "
                                       f"marking it as unreachable.")
            return "unreachable"
    except requests.RequestException as e:
        print(f"Failed to reach {name} at {url}: {e}")
        if not args.silent:
            speak_text( f"Failed to reach {name} and got some kind of error. So we're marking it as "
                                   f"unreachable. The error was: {e}")
        return f"unreachable: {e}"

def main(silent=False, polite=False):
    args = argparse.Namespace(silent=silent, polite=polite)

    intro_statement = (
        "Verifying the operational status of major TLS certificate authority OCSP servers, "
        "ensuring that each is reachable and not presenting indicators of revocation status failures. "
        "Should any server prove unreachable, it might suggest trust chain verification difficulties "
        "or a greater issue affecting the secure operation of the TLS Certificate Authority infrastructure. "
        "This examination shall proceed silently and may consume up to one minute. Stand by..."
    )

    print(f"{intro_statement}")
    if not args.silent:
        speak_text(f"{intro_statement}")

    reachable_endpoints = []
    unreachable_endpoints = []

    report_on_TLS_CA_servers = ""

    # Check each CA endpoint
    for name, url in ca_endpoints.items():
        status = check_ca_endpoint(name, url, args)
        if "reachable" in status:
            reachable_endpoints.append((name, status))
        else:
            unreachable_endpoints.append((name, status))

    # Report results
    print("\nReachable CA Endpoints:")
    report_on_TLS_CA_servers +=  "Reachable CA Endpoints:\n"

    for endpoint, status in reachable_endpoints:
        print(f"- {endpoint} ({status})")
        report_on_TLS_CA_servers += f"- {endpoint} ({status})\n"

    if len(unreachable_endpoints) == 0:
        print("\nAll CA Endpoints are reachable.")
        report_on_TLS_CA_servers += "\nAll CA Endpoints are reachable.\n"

    else:
        print("\nUnreachable CA Endpoints:")
        report_on_TLS_CA_servers += "\nUnreachable CA Endpoints:\n"

        for endpoint, error in unreachable_endpoints:
            print(f"- {endpoint}: {error}")
            report_on_TLS_CA_servers += f"- {endpoint}: {error}\n"


    tls_ca_checks_summary = summarize_service_check_output(report_on_TLS_CA_servers)
    print(f"{tls_ca_checks_summary}")

    # Add the summary to the combined summaries
    add_to_combined_summaries(tls_ca_checks_summary)

    if not args.silent:
        speak_text("The summary of checking TLS CA servers is as follows:")
        speak_text(f"{tls_ca_checks_summary}")

if __name__ == "__main__":
    main()
