import datetime
import platform
import re
from chatbot_cache_persister import load_cache, save_cache, update_cache, get_cached_value
from langchain.chains.question_answering.stuff_prompt import messages

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
from report_source_location import get_public_ip, get_isp_and_location
from check_if_external_ip_changed import did_external_ip_change
from cdn_check import main as cdn_check_main
from tls_ca_check import main as tls_ca_check_main
from whois_check import main as whois_check_main
import socket
import check_ollama_status
from resolver_check import monitor_dns_resolvers
from dns_check import check_dns_root_servers, dns_root_servers
from dns_check import main as check_all_root_servers
from check_layer_two_network import report_link_status_and_type
from os_utils import OS_TYPE
import subprocess
from colorama import init, Fore, Style
import mac_speed_test
from smtp_check import main as smtp_check_main

# Initialize the colorama module with autoreset=True
init(autoreset=True)

# Set up readline to store input history
if platform.system() != "Windows":
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set editing-mode emacs")


@tool
def check_smtp_servers():
    """Use this to check the reachability of several important SMTP servers.

    Returns: str: The SMTP server monitoring report
    """
    return smtp_check_main(silent=True, polite=False)


@tool
def run_mac_speed_test():
    """Use this to run the mac speed test and get a summary of the network quality.

    Returns: str: The mac speed test report or an error message if not on macOS
    """
    if OS_TYPE.lower() != "macOS".lower():
        return "The mac speed test is only available on macOS."
    return mac_speed_test.run_network_quality_test(silent=True, args=None)


@tool
def check_ollama():
    """Use this to check if the Ollama process is running and/or if the Ollama API is reachable."""
    return check_ollama_status.main()

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

@tool
def check_whois_servers():
    """Use this to check the reachability of WHOIS servers.

    Returns: str: The WHOIS server monitoring report
    """
    return whois_check_main(silent=True, polite=False)

@tool
def check_tls_ca_servers():
    """Use this to check the reachability of TLS CA servers.

    Returns: str: The TLS CA server monitoring report
    """
    return tls_ca_check_main(silent=True, polite=False)

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
def check_external_ip_change():
    """Use this to check if the external IP address has changed since the last check.

    Returns: str: A message indicating whether the IP address has changed or not.
    """
    # Get the current external IP using the existing tool
    current_external_ip = get_public_ip()

    # Check if the external IP has changed
    external_ip_status_message = did_external_ip_change(current_external_ip)

    return external_ip_status_message


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
    """Use this to check the reachability of the major DNS Root Servers around the world.

    Returns: str: the DNS root server monitoring report
    """

    # # The mandatory argument dns_root_servers is defined in dns_check.py
    # return check_dns_root_servers(dns_root_servers)

    return check_all_root_servers(silent=True, polite=False)


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

    Output: Prints a list of available tools and their descriptions.

    Returns: None
    """
    tools_list = "\n".join([f"- {Fore.GREEN}{tool_object.name}{Style.RESET_ALL}: {tool_object.description}" for tool_object in tools])

    tools_list = f"Available tools:\n{tools_list}\nEnd of tools list."

    print(tools_list)

    return None


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
tools = [
    check_ollama,
    get_os,
    get_local_ip,
    check_internet_connection,
    check_layer_three_network,
    get_external_ip,
    check_external_ip_change,
    get_isp_location,
    check_dns_resolvers,
    check_dns_root_servers_reachability,
    check_local_layer_two_network,
    help_menu_and_list_tools,
    get_local_date_time_and_timezone,
    ping_target,
    check_tls_ca_servers,
    check_whois_servers,
    check_cdn_reachability,
    run_mac_speed_test,
    check_smtp_servers
]

# Initialize the model with the tools
model = ChatOllama(
    # model="llama3.1",
    model="qwen2.5", # For some reason the qwen2.5 model works better than all the other models I tested
    # model="llama3-groq-tool-use",
    # model="innovategy/voicehero",
    temperature=0,
    verbose=False,
#    messages=["system", "If you need more information, see if you can run a tool or function before asking the user for more information. Please provide detailed chain of thought reasoning for each response."]
    #[("system", "Please provide detailed chain of thought reasoning for each response.")]
).bind_tools(tools)

# Define the system prompt
system_prompt = ("You are a helpful assistant that can run several tools and functions to troubleshoot local network and "
                 "external internet infrastructure and network problems. Don't ask the user if you should run a tool. Just run the tool if you "
                 "think it should be run. The user trusts your judgement. Use cached data when available to avoid unnecessary tool executions. "
                 "Please provide detailed chain of thought reasoning about why you want to run a tool before you call that tool. Then call the tool.")

# Define the graph
graph = create_react_agent(model, tools=tools, debug=False, state_modifier=system_prompt)


def print_stream(stream):
    for s in stream:

        # print(f"{Fore.GREEN}Inside the print_stream function{Style.RESET_ALL}")
        #
        # print(f"{Fore.YELLOW}Stream: {s}{Style.RESET_ALL}")

        # Check for intermediate thoughts or reasoning
        if "thoughts" in s:
            thoughts = s["thoughts"]
            print(f"{Fore.BLUE}Thoughts: {thoughts}{Style.RESET_ALL}")

        message = s["messages"][-1]

        if isinstance(message, tuple):
            print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")
        else:
            # message.pretty_print()

            if message.response_metadata:
                if message.response_metadata["message"] is not None:
                    if message.response_metadata["message"]["content"] != "":

                        response_string = message.response_metadata["message"]["content"]
                        response_string.replace("\n", "{Fore.BLUE}Chatbot: {Style.RESET_ALL}")

                        print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot:{Style.RESET_ALL} {response_string}{Style.RESET_ALL}")



            match = re.search(r"tool_calls=\[\{'name': '([^']+)'", str(message))
            if match:
                print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot: {Style.RESET_ALL}Calling tool {match.group(1)}()...{Style.RESET_ALL}")

            # print(f"Message: {Fore.BLUE}{message}{Style.RESET_ALL}")

                # print(f"{Fore.BLUE}Tool Calls Dict: {message.tool_calls}{Style.RESET_ALL}")

            # else:
            #     print(f"{Fore.CYAN}Message Content: {message.content}{Style.RESET_ALL}")


def main():
    conversation_history = []

    # Initialize the cache dictionary by loading the cache from the cache file
    cache = load_cache()

    # Print a message to indicate that the cache has been loaded
    print(f"{Fore.GREEN}Cache (memories) loaded successfully!{Style.RESET_ALL}")

    # Update the cache with some fundamental information
    if get_cached_value(cache, "os_type") is None:
        update_cache(cache, "os_type", f"{get_os_type()}")


    # Loop through the cache and print the keys and values from the cache file
    for key, value in cache.items():
        print(f"Key: {key}, Value: {value}")


    while True:
        if not check_ollama_status.is_ollama_process_running():
            print(f"{Fore.RED}Ollama process is not running. Please start the Ollama service.{Style.RESET_ALL}")
            check_ollama_status.find_ollama_executable()
            break
        else:
            try:
                user_input = input(f"{Fore.CYAN}\nUser: {Style.RESET_ALL}")

                if user_input.lower() == "exit":
                    print("\nExiting...")
                    save_cache(cache)
                    print("Exiting and saving cache...")
                    break

                elif hasattr(readline, 'add_history'):
                    readline.add_history(user_input)  # Add user input to history
                # Append user input to conversation history
                conversation_history.append(("user", user_input))

                # Prepare inputs with conversation history and cache data
                inputs = {
                    "messages": conversation_history,
                    "cache": cache  # Include cache data as part of the inputs
                }
                response_stream = graph.stream(inputs, stream_mode="values")

                print_stream(response_stream)  # Use the print_stream function to print the response stream

                response_message = None
                for s in response_stream:
                    response_message = s["messages"][-1]
                    if isinstance(response_message, tuple):
                        response_message_str = response_message[1]
                        response_message_str = response_message_str.replace(f"\n", f"{Fore.BLUE}Chatbot: {Style.RESET_ALL}")
                        print(f"{Fore.BLUE}Chatbot: {Style.RESET_ALL}{response_message_str}")
                    else:
                        response_message.pretty_print()
                
                # Append model's response to conversation history
                if response_message:
                    conversation_history.append(("assistant", response_message.content))

            except EOFError:
                print("\nExiting...")
                save_cache(cache)
                print("Exiting and saving cache...")
                break


if __name__ == "__main__":
    main()
