import requests

def get_public_ip():
    response = requests.get("https://api.ipify.org?format=json")
    ip_info = response.json()
    return ip_info.get("ip")

def get_isp_and_location(ip):
    # You can get a free token from ipinfo.io by signing up.
    # token = "YOUR_IPINFO_TOKEN"
    # response = requests.get(f"https://ipinfo.io/{ip}?token={token}")
    response = requests.get(f"https://ipinfo.io/{ip}")
    ip_data = response.json()
    return ip_data

def main():
    # Get the public IP address
    public_ip = get_public_ip()
    # print(f"Public IP Address: {public_ip}")

    # Get ISP and location information
    ip_data = get_isp_and_location(public_ip)
    isp = ip_data.get("org", "Unknown ISP")
    city = ip_data.get("city", "Unknown city")
    region = ip_data.get("region", "Unknown region")
    country = ip_data.get("country", "Unknown country")

    # Display information
    # print(f"{city}, {region}, {country}, downstream from an edge router on the {isp} network")
    # print(f"Location: {city}, {region}, {country}")

    return f"{city}, {region}, {country}, downstream from the {isp} network"

if __name__ == "__main__":
    main()