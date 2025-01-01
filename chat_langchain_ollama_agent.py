import datetime
import platform

# Import readline for input history and completion
if platform.system() == "Windows":
    import pyreadline3 as readline
else:
    import readline
from langchain_ollama import ChatOllama
from typing import Literal
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from os_utils import get_os_type
from web_check import main as web_check_main
from report_source_location import get_public_ip, get_isp_and_location
from cdn_check import main as cdn_check_main
from tls_ca_check import main as tls_ca_check_main
from whois_check import main as whois_check_main
import socket
import check_ollama_status
from resolver_check import monitor_dns_resolvers
from dns_check import check_dns_root_servers, dns_root_servers
from check_layer_two_network import report_link_status_and_type
import subprocess
from colorama import init, Fore, Style

# Initialize the colorama module with autoreset=True
init(autoreset=True)

# Set up readline to store input history
if platform.system() != "Windows":
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set editing-mode emacs")
@tool
def check_tls_ca_servers():
    """Use this to verify the operational status of major TLS certificate authority OCSP servers.

    Returns: str: The TLS CA server reachability report
    """
    return tls_ca_check_main(silent=True, polite=False)

@tool
def check_whois_servers():
    """Use this to check the reachability of WHOIS servers.

    Returns: str: The WHOIS server reachability report
    """
    return whois_check_main(silent=True, polite=False)
@tool
def check_cdn_reachability():
    """Use this to check the reachability of several of the largest content delivery networks around the world.

    Returns: str: The CDN reachability report
    """
    return cdn_check_main(silent=True, polite=False)

@tool
def ping_target(target: str):
    """Use this to ping an IP address or hostname to determine the network latency.

    Args:
        target (str): The IP address or hostname to ping.

    Returns: str: The average latency in milliseconds, or an error message if the ping fails.
    """
    try:
        # Run the ping command
        result = subprocess.run(
            ["ping", "-c", "4", target],
            capture_output=True,
            text=True,
            check=True
        )
        # Extract the average latency from the ping output
        for line in result.stdout.splitlines():
            if "avg" in line:
                return line.split("/")[4] + " ms"
        return "Ping completed, but average latency could not be determined."
    except subprocess.CalledProcessError as e:
        return f"Ping failed: {e}"
    except Exception as e:
        return f"An error occurred: {e}"
def check_ollama():
    """Use this to check if the Ollama process is running and/or if the Ollama API is reachable."""
    return check_ollama_status.main()


@tool
def get_os():
    """Use this to get os information.

    Returns: str: the os type
    """
    return get_os_type()


@tool
def get_local_ip():
    """Use this to get our local IP address that we're using for the local LAN, Ethernet, or WiFi network.

    Returns: str: this computer's local ip address
    """

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]


@tool
def get_external_ip():
    """Use this to get our external ip address.

    Returns: str: our external ip address
    """
    our_external_ip = get_public_ip()

    return our_external_ip


@tool
def get_isp_location():
    """Use this to get our external ISP location data based on our external IP address.

    Returns: str: JSON formatted ISP name and location data
    """
    our_external_ip = get_public_ip()
    our_isp_json = get_isp_and_location(our_external_ip)

    return our_isp_json


@tool
def check_internet_connection():
    """Use this to check if we have a working internet broadband connection, including basic DNS lookup of www.google.com.

    Returns: str: "connected" if we have an internet connection, "disconnected" if we don't
    """
    try:
        socket.create_connection(("www.google.com", 80))
        return "connected"
    except OSError:
        return "disconnected"


@tool
def check_layer_three_network():
    """Use this to check if we have a working layer 3 internet broadband connection and can reach 8.8.8.8 on port 53.

    Returns: str: "connected at layer 3" if we have an internet connection, "disconnected at layer 3" if we don't
    """
    try:
        socket.create_connection(("8.8.8.8", 53))
        return "connected at layer 3"
    except OSError:
        return "disconnected at layer 3"


@tool
def check_dns_resolvers():
    """Use this to check the reachability of several of the most popular DNS resolvers.

    Returns: str: the DNS resolver monitoring report
    """
    return monitor_dns_resolvers()


@tool
def check_dns_root_servers_reachability():
    """Use this to check the reachability of the DNS Root Servers.

    Returns: str: the DNS root server monitoring report
    """

    # The mandatory argument dns_root_servers is defined in dns_check.py
    return check_dns_root_servers(dns_root_servers)


@tool
def check_local_layer_two_network():
    """Use this to check the local LAN OSI Layer 2 network link type, speed, and status.
        For example, it will print the LAN network interfaces that are up,
        and if they are up and have a speed greater than 0 Mbps, it will also print the link type and speed.
        It will also try to guess if the network interface is Wi-Fi, Ethernet, Loopback, or Unknown.

    Returns: str: for interfaces that are up, the link name, type guess, and speed
    """

    return report_link_status_and_type()


@tool
def help_menu_and_list_tools():
    """Use this when the user inputs 'help' to guide them with a list the available tools and their descriptions.

    Returns: str: a list of available tools and their descriptions
    """
    return "\n".join([f"- {Fore.GREEN}{tool_object.name}{Style.RESET_ALL}: {tool_object.description}" for tool_object in tools])


@tool
def get_local_date_time_and_timezone():
    """Use this to get the local date, time, and timezone.

    Returns: list: the local time in 24-hour format, the local date in the format YYYY-MM-DD, and the local timezone
    """

    # Return the local time in 24-hour format
    local_time = datetime.datetime.now().strftime("%H:%M")

    # Return the local date in the format YYYY-MM-DD
    local_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # Return the local timezone
    local_timezone = datetime.datetime.now().astimezone().tzinfo

    return [local_time, local_date, local_timezone]


# Define the tools
tools = [check_ollama,
         get_os,
         get_local_ip,
         check_internet_connection,
         check_layer_three_network,
         get_external_ip,
         get_isp_location,
         check_dns_resolvers,
         check_dns_root_servers_reachability,
         check_local_layer_two_network,
         help_menu_and_list_tools,
         get_local_date_time_and_timezone,
         ping_target,
         check_websites,
         check_tls_ca_servers,
         check_whois_servers,
         check_cdn_reachability]


# Initialize the model with the tools
model = ChatOllama(
    # model="llama3.1",
    model="qwen2.5", # For some reason the qwen2.5 model works better than all the other models I tested
    # model="llama3-groq-tool-use",
    temperature=0,
).bind_tools(tools)

# Define the graph
graph = create_react_agent(model, tools=tools)


def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()


def main():
    conversation_history = []

    while True:
        if not check_ollama_status.is_ollama_process_running():
            print(f"{Fore.RED}Ollama process is not running. Please start the Ollama service.{Style.RESET_ALL}")
            check_ollama_status.find_ollama_executable()
            break
        else:
            try:
                user_input = input("\nAsk a question about the localhost, network or any internet infrastructure: ")
                if hasattr(readline, 'add_history'):
                    readline.add_history(user_input)  # Add user input to history
                # Append user input to conversation history
                conversation_history.append(("user", user_input))

                # Prepare inputs with conversation history
                inputs = {"messages": conversation_history}
                response_stream = graph.stream(inputs, stream_mode="values")
                response_message = None
                for s in response_stream:
                    response_message = s["messages"][-1]
                    if isinstance(response_message, tuple):
                        print(response_message)
                    else:
                        response_message.pretty_print()
                
                # Append model's response to conversation history
                if response_message:
                    conversation_history.append(("assistant", response_message.content))

            except EOFError:
                print("\nExiting...")
                break


if __name__ == "__main__":
    main()
