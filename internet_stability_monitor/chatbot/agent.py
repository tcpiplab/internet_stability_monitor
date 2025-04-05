"""
LangGraph agent setup and configuration.

This module sets up the LangGraph agent that powers the chatbot, including
the system prompt, model configuration, and graph structure.
"""

from typing import Dict, Any, List, Callable
from typing_extensions import TypedDict, Annotated

from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# Default system prompt
DEFAULT_SYSTEM_PROMPT = (
    "You are a precise network diagnostics assistant. Follow these guidelines for tool usage:"
    "\n1. IMPORTANT: When a user request closely matches a specific tool's purpose, use ONLY that tool"
    "\n2. For example, if a user asks to 'check websites' or 'check significant websites', use ONLY the check_websites tool"
    "\n3. Use multiple tools ONLY when necessary to fulfill distinct parts of a complex request"
    "\n4. Avoid using the search tool unless explicitly requested or when local tools cannot answer the question"
    "\n5. Prioritize direct tool names over general descriptions (e.g., 'check_dns_resolvers' over general DNS queries)"
    "\n6. If a tool's response is verbose, summarize only the most important troubleshooting information"
    "\n7. Keep track of which tools you've run in the current conversation, so you can accurately tell the user which tools were run when asked"
    "\nYour primary job is network diagnostics using available tools, not general information retrieval."
)

class State(TypedDict):
    """State type for the LangGraph agent."""
    messages: Annotated[list, add_messages]

class ChatbotAgent:
    """LangGraph agent for the chatbot."""
    
    def __init__(self, 
                 tools: List[Callable], 
                 memory_system,
                 model_name: str = "qwen2.5",
                 system_prompt: str = DEFAULT_SYSTEM_PROMPT):
        """Initialize the chatbot agent with tools and memory."""
        self.tools = tools
        self.memory = memory_system
        self.model_name = model_name
        self.system_prompt = system_prompt
        
        # Add search tool to the tools
        self.search_tool = TavilySearchResults(max_results=2)
        all_tools = self.tools + [self.search_tool]
        
        # Set up model with tools
        self.model = ChatOllama(model=model_name).bind_tools(all_tools)
        
        # Create the graph
        self.graph = self._create_graph()
    
    def _create_graph(self):
        """Create the LangGraph agent graph."""
        # Helper function for the chatbot node
        def chatbot(state: State):
            return {"messages": [self.model.invoke(state["messages"])]}
        
        # Build the graph
        graph_builder = StateGraph(State)
        graph_builder.add_node("chatbot", chatbot)
        
        tool_node = ToolNode(tools=self.tools + [self.search_tool])
        graph_builder.add_node("tools", tool_node)
        
        graph_builder.add_conditional_edges(
            "chatbot",
            tools_condition,
        )
        # Any time a tool is called, we return to the chatbot to decide the next step
        graph_builder.add_edge("tools", "chatbot")
        graph_builder.add_edge(START, "chatbot")
        
        # Compile the graph with the memory checkpointer
        return graph_builder.compile(checkpointer=self.memory.memory)
    
    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process a user input and return the agent's response."""
        from langchain_core.messages import HumanMessage
        
        config = self.memory.get_config()
        
        # Handle first message vs. subsequent messages
        if self.memory.is_first_message():
            # Create initial messages with system prompt
            messages = self.memory.create_initial_messages(self.system_prompt)
            # Append user message
            messages["messages"].append(HumanMessage(content=user_input))
        else:
            # Just add the user message
            messages = {"messages": [HumanMessage(content=user_input)]}
        
        # Process with the graph
        return self.graph.invoke(messages, config)
    
    def pretty_print_message(self, message: BaseMessage) -> None:
        """Pretty print a message from the agent."""
        if hasattr(message, "pretty_print"):
            message.pretty_print()
        else:
            from interface import print_ai_message
            print_ai_message(message.content if hasattr(message, "content") else str(message))