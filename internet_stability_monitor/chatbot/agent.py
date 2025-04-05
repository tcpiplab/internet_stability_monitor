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
from langgraph.prebuilt import ToolNode
# We'll create our own tools_condition instead of importing the default one

# Default system prompt
DEFAULT_SYSTEM_PROMPT = (
    "You are a precise network diagnostics assistant. Follow these exact tool selection rules:"
    "\n\nTOOL SELECTION RULES:"
    "\n- For user location or IP geolocation questions: ALWAYS use get_isp_location ONLY"
    "\n- For questions about external IP: ALWAYS use get_external_ip ONLY"
    "\n- For local IP address questions: ALWAYS use get_local_ip ONLY" 
    "\n- For DNS root server questions: ALWAYS use check_dns_root_servers_reachability ONLY"
    "\n- For website reachability questions: ALWAYS use check_websites ONLY"
    "\n- NEVER use check_websites or check_internet_connection unless specifically asked about website status"
    "\n\nTOOL USAGE RULES:"
    "\n- ALWAYS use EXACTLY ONE tool for simple questions - do not chain multiple tools"
    "\n- NEVER run the same tool twice in a row"
    "\n- ALWAYS provide a direct answer after running a tool without running more tools"
    "\n- If you're unsure which tool to use, ask the user for clarification instead of guessing"
    "\n\nThe available tools include get_isp_location, get_external_ip, get_local_ip, check_websites, check_internet_connection, and several others. Choose the most appropriate one based on the rules above."
)

class State(TypedDict):
    """State type for the LangGraph agent."""
    messages: Annotated[list, add_messages]

# Global counter for total tool calls in a single query processing
TOOL_CALL_COUNTER = 0
MAX_TOOL_CALLS_PER_QUERY = 3  # Maximum number of tool calls allowed per user query

# Custom tools condition to prevent repeated tool calls and enforce tool selection rules
def custom_tools_condition(state: Dict[str, Any]) -> str:
    """Custom condition that decides whether to use tools or not.
    
    This improved version:
    1. Limits total tool calls per user query
    2. Prevents repeated tool calls
    3. Adds extra checks for correct tool selection
    """
    from langchain_core.messages import AIMessage
    import traceback
    
    # Access global counter
    global TOOL_CALL_COUNTER
    
    try:
        # Get the last message
        last_message = state["messages"][-1]
        
        # Only AIMessages can call tools
        if not isinstance(last_message, AIMessage):
            # Reset counter when we get a new human message
            if hasattr(last_message, "type") and last_message.type == "human":
                TOOL_CALL_COUNTER = 0
            return "chatbot"
    except Exception as e:
        print(f"Error examining message type: {e}")
        traceback.print_exc()
        return "chatbot"  # Safe fallback
    
    # Check for tool calls
    try:
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            # Hard limit on total tool calls per user query
            if TOOL_CALL_COUNTER >= MAX_TOOL_CALLS_PER_QUERY:
                print(f"Debug: Maximum tool call limit of {MAX_TOOL_CALLS_PER_QUERY} reached, stopping execution")
                return "chatbot"  # Stop the tool execution chain
                
            # Count unique tools requested in this message
            unique_tools = set()
            for tool_call in last_message.tool_calls:
                if isinstance(tool_call, dict) and "name" in tool_call:
                    unique_tools.add(tool_call["name"])
                elif hasattr(tool_call, "name"):
                    unique_tools.add(tool_call.name)
            
            # Warn if more than one tool requested at once (violates our rules)
            if len(unique_tools) > 1:
                print(f"Warning: Model requested {len(unique_tools)} tools at once: {unique_tools}")
                print("Only the first tool will be executed")
            
            # Print debug info about the tool calls
            print(f"Debug: Tool calls type: {type(last_message.tool_calls)}")
            print(f"Debug: Tool calls content: {last_message.tool_calls}")
            
            # Get history of all tool calls in the current conversation
            tool_history = []
            for msg in state["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        if isinstance(tool_call, dict) and "name" in tool_call:
                            tool_history.append(tool_call["name"])
                        elif hasattr(tool_call, "name"):
                            tool_history.append(tool_call.name)
            
            # Check the last tool call request
            current_tool = None
            if last_message.tool_calls:
                tool_call = last_message.tool_calls[0]  # Focus on first requested tool
                if isinstance(tool_call, dict) and "name" in tool_call:
                    current_tool = tool_call["name"]
                elif hasattr(tool_call, "name"):
                    current_tool = tool_call.name
            
            if current_tool:
                print(f"Debug: Model wants to call {current_tool}")
                
                # Check if this tool was already called in the sequence
                if current_tool in tool_history:
                    print(f"Debug: Preventing repeated call to {current_tool}")
                    return "chatbot"
                
                # Location-related queries should use get_isp_location
                if "location" in " ".join(msg.content for msg in state["messages"] if hasattr(msg, "content")).lower():
                    if current_tool != "get_isp_location" and current_tool != "get_external_ip":
                        print(f"Warning: Model using {current_tool} for location query instead of get_isp_location")
                
                # Increment our global counter and allow the tool call
                TOOL_CALL_COUNTER += 1
                return "tools"
            
            # No valid tool identified
            return "chatbot"
    except Exception as e:
        print(f"Error in custom_tools_condition: {e}")
        traceback.print_exc()
        return "chatbot"  # Safe fallback
    
    # No tool calls, reset counter and continue with the chatbot
    TOOL_CALL_COUNTER = 0
    return "chatbot"

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
        
        # Keep track of recently run tools to prevent loops
        self.recent_tools = []
        
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
            custom_tools_condition,
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