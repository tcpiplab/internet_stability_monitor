from typing import Optional, List, Dict, Any, Tuple, Literal
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
def check_smtp_servers() -> str:
    """Use this to check the reachability of several important SMTP servers.

    Returns: str: The SMTP server monitoring report
    """
    return smtp_check_main(silent=True, polite=False)


@tool
def run_mac_speed_test() -> str:
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
def check_cdn_reachability() -> str:
    """Use this to check the reachability of several of the largest content delivery networks around the world.

    Returns: str: The CDN reachability report
    """
    return cdn_check_main(silent=True, polite=False)

@tool
def ping_target(target: str) -> str:
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
def check_whois_servers() -> str:
    """Use this to check the reachability of WHOIS servers.

    Returns: str: The WHOIS server monitoring report
    """
    return whois_check_main(silent=True, polite=False)

@tool
def check_tls_ca_servers() -> str:
    """Use this to check the reachability of TLS CA servers.

    Returns: str: The TLS CA server monitoring report
    """
    return tls_ca_check_main(silent=True, polite=False)

@tool
def get_os() -> str:
    """Use this to get os information.

    Returns: str: the os type
    """
    return get_os_type()

@tool
def get_local_ip() -> str:
    """Use this to get our local IP address that we're using for the local LAN, Ethernet, or WiFi network.

    Returns: str: this computer's local ip address
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

@tool
def get_external_ip() -> str:
    """Use this to get our external ip address.

    Returns: str: our external ip address
    """
    our_external_ip = get_public_ip()
    return our_external_ip

@tool
def check_external_ip_change() -> str:
    """Use this to check if the external IP address has changed since the last check.

    Returns: str: A message indicating whether the IP address has changed or not.
    """
    # Get the current external IP using the existing tool
    current_external_ip = get_public_ip()

    # Check if the external IP has changed
    external_ip_status_message = did_external_ip_change(current_external_ip)

    return external_ip_status_message


@tool
def get_isp_location() -> str:
    """Use this to get our external ISP location data based on our external IP address.

    Returns: str: JSON formatted ISP name and location data
    """
    our_external_ip = get_public_ip()
    our_isp_json = get_isp_and_location(our_external_ip)

    return our_isp_json

@tool
def check_internet_connection() -> str:
    """Use this to check if we have a working internet broadband connection, including basic DNS lookup of www.google.com.

    Returns: str: "connected" if we have an internet connection, "disconnected" if we don't
    """
    try:
        socket.create_connection(("www.google.com", 80))
        return "connected"
    except OSError:
        return "disconnected"

@tool
def check_layer_three_network() -> str:
    """Use this to check if we have a working layer 3 internet broadband connection and can reach 8.8.8.8 on port 53.

    Returns: str: "connected at layer 3" if we have an internet connection, "disconnected at layer 3" if we don't
    """
    try:
        socket.create_connection(("8.8.8.8", 53))
        return "connected at layer 3"
    except OSError:
        return "disconnected at layer 3"

@tool
def check_dns_resolvers() -> str:
    """Use this to check the reachability of several of the most popular DNS resolvers.

    Returns: str: the DNS resolver monitoring report
    """
    return monitor_dns_resolvers()


@tool
def check_dns_root_servers_reachability() -> str:
    """Use this to check the reachability of the major DNS Root Servers around the world.

    Returns: str: the DNS root server monitoring report
    """

    # # The mandatory argument dns_root_servers is defined in dns_check.py
    # return check_dns_root_servers(dns_root_servers)

    return check_all_root_servers(silent=True, polite=False)


@tool
def check_local_layer_two_network() -> str:
    """Use this to check the local LAN OSI Layer 2 network link type, speed, and status.
        For example, it will print the LAN network interfaces that are up,
        and if they are up and have a speed greater than 0 Mbps, it will also print the link type and speed.
        It will also try to guess if the network interface is Wi-Fi, Ethernet, Loopback, or Unknown.

    Returns: str: for interfaces that are up, the link name, type guess, and speed
    """
    return report_link_status_and_type()

@tool
def help_menu_and_list_tools() -> None:
    """Use this when the user inputs 'help' to guide them with a list the available tools and their descriptions.

    Output: Prints a list of available tools and their descriptions.

    Returns: None
    """
    tools_list = "\n".join([f"- {Fore.GREEN}{tool_object.name}{Style.RESET_ALL}: {tool_object.description}" for tool_object in tools])

    tools_list = f"Available tools:\n{tools_list}\nEnd of tools list."

    print(tools_list)

    return None


@tool
def get_local_date_time_and_timezone() -> List[str]:
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

@tool
def check_cache() -> str:
    """Use this to check the cache (memories) and print the keys and values from the cache file.

    Returns: str: The cache contents
    """
    # Load the cache
    cache = load_cache()

    # Print a message to indicate that the cache has been loaded
    print(f"{Fore.GREEN}Cache (memories) loaded successfully!{Style.RESET_ALL}")

    # Loop through the cache and print the keys and values from the cache file
    # for key, value in cache.items():
    #     print(f"Key: {key}, Value: {value}")

    return f"Cached Data Context: {cache}"

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
    check_smtp_servers,
    check_cache
]

# Initialize the model with the tools
model = ChatOllama(
    model="qwen2.5", # For some reason the qwen2.5 model works better than all the other models I tested
    temperature=0,
    verbose=False
).bind_tools(tools)

# Define the system prompt
system_prompt = ("""You are a helpful assistant that can run several tools and functions to troubleshoot local network 
                 and external internet infrastructure and network problems. Before you run a tool you must first try to use the information in 
                 the cache to avoid unnecessary tool executions. But if you find that you need to run a 
                 tool to respond to the user input, you can run that tool. If you find that you need to run more than
                 three different tools to respond to the user input then explain to the user why you need to run those
                 additional tools.""")

# Define the graph
graph = create_react_agent(model, tools=tools, debug=False, state_modifier=system_prompt)


def print_stream(stream, cache):
    for s in stream:
        # Skip if no messages in the current stream item
        if "messages" not in s or not s["messages"]:
            continue

        message = s["messages"][-1]

        # Debug info (can be removed once everything works)
        print(f"{Fore.CYAN}DEBUG: Message type: {type(message)}{Style.RESET_ALL}")
        message_preview = str(message)[:100] + "..." if len(str(message)) > 100 else str(message)
        print(f"{Fore.CYAN}DEBUG: Message preview: {message_preview}{Style.RESET_ALL}")

        # Handle AI messages with direct content (most important case)
        if hasattr(message, "content") and message.content:
            # Only print if it's not a tool message
            if not hasattr(message, "name"):
                print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot:{Style.RESET_ALL} {message.content}{Style.RESET_ALL}")

        # Handle AI messages with response_metadata
        if hasattr(message, "response_metadata") and message.response_metadata:
            if message.response_metadata.get("message") and message.response_metadata["message"].get("content"):
                response_string = message.response_metadata["message"]["content"]
                if response_string:  # Only print if there's actual content
                    print(f"{Fore.BLUE}{Style.BRIGHT}Chatbot:{Style.RESET_ALL} {response_string}{Style.RESET_ALL}")

        # Handle tool messages
        if hasattr(message, "__class__") and message.__class__.__name__ == "ToolMessage":
            if hasattr(message, "name") and hasattr(message, "content"):
                tool_name = message.name
                tool_content = message.content
                print(f"{Fore.GREEN}Tool {tool_name} returned: {tool_content[:50]}...{Style.RESET_ALL}")

                # Store in cache with meaningful key
                if tool_name == "get_external_ip":
                    cache = update_cache(cache, "external_ip", tool_content)
                    print(f"Cache updated with external_ip: {tool_content}")
                elif tool_name == "get_isp_location":
                    cache = update_cache(cache, "location_data", tool_content)
                    print(f"Cache updated with location_data: {tool_content}")

                # Always store with generic tool name key
                cache = update_cache(cache, tool_name, tool_content)
                print(f"Cache updated with {tool_name}: {tool_content}")
                save_cache(cache)

    return cache

def main():
    conversation_history: List[Tuple[str, str]] = []

    # Initialize the cache dictionary by loading the cache from the cache file
    cache: Dict[str, Any] = load_cache()

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

                if user_input.lower() == "/exit":
                    print("\nExiting...")
                    save_cache(cache)
                    print("Exiting and saving cache...")
                    break

                elif user_input.lower() == "/cache":
                    print(f"{Fore.YELLOW}Cache (memories): {cache}{Style.RESET_ALL}")

                elif hasattr(readline, 'add_history'):
                    # readline.add_history(f"# Previous User Input: \"{user_input}\"\n")  # Add user input to history
                    pass

                # Append user input to conversation history
                # conversation_history.append(("user", user_input))

                # Prepare inputs with conversation history and cache data
                inputs = {
                    # "messages": conversation_history,
                    # "messages": [("user", user_input)],
                    "messages": [("user", user_input),("ai", f"cache: {cache}")]
                    # "cache": cache  # Include cache data as part of the inputs
                }

                # Track tool calls to store in cache later
                # tool_results = {}

                response_stream = graph.stream(inputs, stream_mode="values", debug=False)
                # response_stream = graph.stream(inputs, stream_mode="updates")

                cache = print_stream(response_stream, cache)  # Use the print_stream function to print the response stream

                # Track tool calls to store in cache later
                tool_results = {}
                last_message = None  # Store the last message

                # response_message = None
                for s in response_stream:
                    if "messages" not in s:
                        continue

                    message = s["messages"][-1]
                    last_message = s  # Save the current message as the last one

                    # Extract tool names and results from output
                    if isinstance(message, dict) and "content" in message:
                        content_str = str(message["content"])
                        tool_match = re.search(r"Calling tool ([^(]+)\(\)", content_str)
                        if tool_match:
                            tool_name = tool_match.group(1)
                            # The next message should contain the result
                            tool_results[tool_name] = True  # Mark this tool as used
                            print(f"Tool called: {tool_name}")

                    # Look for tool results in the response
                    if str(message).find("'name': '") > 0 and str(message).find("'response': ") > 0:
                        result_pattern = re.search(r"'name': '([^']+)'.*?'response': ([^,}]+)", str(message))
                        if result_pattern:
                            tool_name = result_pattern.group(1)
                            tool_result = result_pattern.group(2)
                            tool_results[tool_name] = tool_result
                            print(f"Tool result for {tool_name}: {tool_result}")

                    # Store all tool results in cache
                for tool_name, tool_result in tool_results.items():
                    if tool_result is not True:  # Skip if we didn't capture the actual result
                        update_cache(cache, tool_name, tool_result)
                        print(f"{Fore.GREEN}Tool result for {tool_name}: {tool_result}{Style.RESET_ALL}")




                # Also store the final response - now using last_message which is safely stored
                if last_message and "messages" in last_message and last_message["messages"]:
                    final_message = last_message["messages"][-1]
                    if hasattr(final_message, "content") and final_message.content:
                        update_cache(cache, "last_response", final_message.content)

                save_cache(cache)

                    # response_message = s["messages"][-1]
                    #
                    # # Check if there are tool calls in the message
                    # if hasattr(response_message, "tool_calls") and response_message.tool_calls:
                    #     for tool_call in response_message.tool_calls:
                    #         tool_name = tool_call.name
                    #         tool_result = tool_call.response
                    #
                    #         # Store tool results in cache with meaningful keys
                    #         if tool_name == "get_external_ip":
                    #             update_cache(cache, "external_ip", tool_result)
                    #         elif tool_name == "get_isp_location":
                    #             update_cache(cache, "location_data", tool_result)
                    #         elif tool_name == "check_internet_connection":
                    #             update_cache(cache, "internet_status", tool_result)
                    #         # Add more tool result handlers as needed
                    #
                    # if isinstance(response_message, tuple):
                    #     response_message_str = response_message[1]
                    #     response_message_str = response_message_str.replace(f"\n", f"{Fore.BLUE}Chatbot: {Style.RESET_ALL}")
                    #     # Append model's response to conversation history
                    #     # conversation_history.append(("assistant", response_message_str))
                    #     # Store the last response separately instead of overwriting
                    #     update_cache(cache, "last_assistant_response", response_message_str)
                    #     save_cache(cache)
                    #     print(f"{Fore.BLUE}Chatbot: {Style.RESET_ALL}{response_message_str}")
                    # else:
                    #     response_message.pretty_print()

            except EOFError:
                print("\nExiting...")
                save_cache(cache)
                print("Exiting and saving cache...")
                break


if __name__ == "__main__":
    main()
