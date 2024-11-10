import requests
import urllib3
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

def check_ca_endpoint(name, url):
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
            return "reachable"
        elif 300 <= response.status_code < 400:
            print(f"{name} at {url} returned status code {response.status_code} (redirect)")
            return "reachable (redirected)"
        else:
            print(f"{name} at {url} returned status code {response.status_code}")
            return "unreachable"
    except requests.RequestException as e:
        print(f"Failed to reach {name} at {url}: {e}")
        return f"unreachable: {e}"

if __name__ == "__main__":
    reachable_endpoints = []
    unreachable_endpoints = []

    # Check each CA endpoint
    for name, url in ca_endpoints.items():
        status = check_ca_endpoint(name, url)
        if "reachable" in status:
            reachable_endpoints.append((name, status))
        else:
            unreachable_endpoints.append((name, status))

    # Report results
    print("\nReachable CA Endpoints:")
    for endpoint, status in reachable_endpoints:
        print(f"- {endpoint} ({status})")

    if len(unreachable_endpoints) == 0:
        print("\nAll CA Endpoints are reachable.")

    else:
        print("\nUnreachable CA Endpoints:")
        for endpoint, error in unreachable_endpoints:
            print(f"- {endpoint}: {error}")