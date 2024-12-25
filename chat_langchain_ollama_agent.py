from langchain_ollama import ChatOllama
from typing import Literal
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from os_utils import get_os_type
from report_source_location import get_public_ip

# First we initialize the model we want to use.
# model = ChatOllama(model="llama3.1", temperature=0)



# For this tutorial we will use custom tool that returns pre-defined values for weather in two cities (NYC & SF)




@tool
def get_weather(city: Literal["nyc", "sf"]):
    """Use this to get weather information."""
    if city == "nyc":
        return "It might be cloudy in nyc"
    elif city == "sf":
        return "It's always sunny in sf"
    else:
        raise AssertionError("Unknown city")

@tool
def get_os():
    """Use this to get os information."""
    return get_os_type()

@tool
def get_external_ip():
    """Use this to get our external ip address.

    Returns: str: our external ip address
    """
    our_external_ip = get_public_ip()

    return our_external_ip


model = ChatOllama(
    model="llama3.1",
    temperature=0,
).bind_tools([get_weather, get_os, get_external_ip])



tools = [get_weather, get_os, get_external_ip]


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

# inputs = {"messages": [("user", "what is the weather in paris?")]}
# print_stream(graph.stream(inputs, stream_mode="values"))


# inputs = {"messages": [("user", "who built you?")]}
# print_stream(graph.stream(inputs, stream_mode="values"))

inputs = {"messages": [("user", "What OS are we running on and also, what is our public IP address?")]}
print_stream(graph.stream(inputs, stream_mode="values"))