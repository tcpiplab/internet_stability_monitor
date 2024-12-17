import re

# Acronyms to be surrounded with SSML tags
ACRONYMS = [
    "dns", "ntp", "imap", "smtp", "tls", "cdn", "ca", "isp", "ixp"
]

def process_report(input_text):
    # Function to replace acronyms with SSML wrapped versions
    def replace_acronyms_with_ssml(text, acronyms):
        for acronym in acronyms:
            # Use word boundaries to avoid replacing parts of larger words
            pattern = r'\b' + re.escape(acronym) + r'\b'
            ssml_tag = f'<say-as interpret-as="characters">{acronym.upper()}</say-as>'
            text = re.sub(pattern, ssml_tag, text)
        return text

    # Process the input text
    output_text = replace_acronyms_with_ssml(input_text, ACRONYMS)

    return output_text

if __name__ == "__main__":
    # Example input text
    input_text = """
    Today's internet news update is brought to you by the Internet Health Report!

    In today's report, we have good news to share. All critical endpoints for whois, dns, ntp, web, cloud, imap, smtp, tls and cdn services are reachable. This includes the root DNS servers, all major ISPs, and all CA endpoints.

    DNS resolvers from Google, Cloudflare, OpenDNS, Quad9, Comodo Secure DNS and Equinix IX (Global) were also found to be responsive. All of these are essential for ensuring the smooth operation of the internet's infrastructure.

    In addition, all reachable CDNs, IMAP servers, SMTP servers and WHOIS servers were found to be functioning properly. This means that users can access their email and web services without issue, and domain names can be properly registered and resolved.

    All in all, it seems the internet is running smoothly!
    """

    # Process and print the result
    processed_text = process_report(input_text)
    print(f"{processed_text}")
