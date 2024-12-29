import getpass
import os
from langchain_openai import ChatOpenAI
from typing import Literal
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from IPython.display import Image, display



def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")


_set_env("OPENAI_API_KEY")

# First we initialize the model we want to use.


model = ChatOpenAI(model="gpt-4o", temperature=0)


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


tools = [get_weather]


# Define the graph



graph = create_react_agent(model, tools=tools)



display(Image(graph.get_graph().draw_mermaid_png()))

def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()

inputs = {"messages": [("user", "what is the weather in london?")]}
print_stream(graph.stream(inputs, stream_mode="values"))


inputs = {"messages": [("user", "who built you?")]}
print_stream(graph.stream(inputs, stream_mode="values"))