import dns.resolver
import time
from datetime import datetime
from service_check_summarizer import summarize_service_check_output

# List of DNS resolvers and their IP addresses
dns_resolvers = {
    "Google Public DNS - Primary": "8.8.8.8",
    "Google Public DNS - Secondary": "8.8.4.4",
    "Cloudflare DNS - Primary": "1.1.1.1",
    "Cloudflare DNS - Secondary": "1.0.0.1",
    "OpenDNS - Primary": "208.67.222.222",
    "OpenDNS - Secondary": "208.67.220.220",
    "Quad9 - Primary": "9.9.9.9",
    "Quad9 - Secondary": "149.112.112.112",
    "Comodo Secure DNS - Primary": "8.26.56.26",
    "Comodo Secure DNS - Secondary": "8.20.247.20"
}


# Function to monitor DNS resolvers
def monitor_dns_resolvers():
    reachable_resolvers = []
    unreachable_resolvers = []
    results = ""
    results +=  f"Starting DNS Resolver monitoring report at: {datetime.now()}\n"
    results += "This will check the reachability of several of the most popular DNS resolvers.\n"

    for resolver_name, resolver_ip in dns_resolvers.items():
        retry_attempts = 3
        for attempt in range(retry_attempts):
            try:
                # Create a resolver instance and set the DNS server IP address
                resolver = dns.resolver.Resolver()
                resolver.nameservers = [resolver_ip]
                resolver.timeout = 5  # Set a timeout of 5 seconds for the query
                resolver.lifetime = 10  # Total lifetime of 10 seconds for retries

                start_time = datetime.now()
                # Query for 'A' record of example.com
                answer = resolver.resolve('example.com', 'A')
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()

                # If we get an answer, consider the resolver reachable
                if answer:
                    reachable_resolvers.append(f"{resolver_name}: Response Time: {response_time:.3f} seconds")
                else:
                    unreachable_resolvers.append(f"{resolver_name}: unreachable")
                break
            except (
            dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout, dns.exception.DNSException) as e:
                if attempt == retry_attempts - 1:
                    unreachable_resolvers.append(f"{resolver_name}: unreachable: {str(e)}")
                time.sleep(2)  # Sleep for 2 seconds before retrying

    results += "Reachable DNS Resolvers:\n"
    for resolver_info in reachable_resolvers:
        results += f"- {resolver_info}\n"

    if len(unreachable_resolvers) == 0:
        results += "\nAll DNS resolvers are reachable.\n"
    else:
        results += "\nUnreachable DNS Resolvers:\n"
        for resolver_info in unreachable_resolvers:
            results += f"- {resolver_info}\n"

    return results


if __name__ == "__main__":
    print(f"Starting DNS Resolver monitoring at {datetime.now()}\n")
    resolver_check_results = monitor_dns_resolvers()

    resolver_output_summary = summarize_service_check_output(resolver_check_results)
    print(resolver_output_summary)