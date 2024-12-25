from langchain_ollama import ChatOllama
from typing import Literal
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from os_utils import get_os_type
from report_source_location import get_public_ip, get_isp_and_location
import socket

# Define the tools. They will work better if they have good docstrings.
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


# Initialize the model with the tools
model = ChatOllama(
    model="llama3.1",
    temperature=0,
).bind_tools([get_os, get_local_ip, check_internet_connection, check_layer_three_network, get_external_ip, get_isp_location])



tools = [get_os, get_local_ip, check_internet_connection, check_layer_three_network, get_external_ip, get_isp_location]


# Define the graph
graph = create_react_agent(model, tools=tools)

# display(Image(graph.get_graph().draw_mermaid_png()))


def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()


# inputs = {"messages": [("user", "What OS are we running on and also, what is our public IP address, and what is our ISP or location?")]}
# print_stream(graph.stream(inputs, stream_mode="values"))

if __name__ == "__main__":

    while True:
        user_input = input("\nAsk a question about the localhost, network or any internet infrastructure: ")

        inputs = {"messages": [("user", f"{user_input}")]}

        print_stream(graph.stream(inputs, stream_mode="values"))
