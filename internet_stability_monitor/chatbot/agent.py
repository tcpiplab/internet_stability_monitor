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
    "You are a precise network diagnostics assistant. Follow these guidelines for tool usage:"
    "\n1. IMPORTANT: When a user request closely matches a specific tool's purpose, use ONLY that tool"
    "\n2. For example, if a user asks to 'check websites' or 'check significant websites', use ONLY the check_websites tool"
    "\n3. Use multiple tools ONLY when necessary to fulfill distinct parts of a complex request"
    "\n4. NEVER call the same tool twice in a row - this is especially important for DNS tools"
    "\n5. After running a tool like check_dns_root_servers_reachability, NEVER run it again immediately"
    "\n6. Avoid using the search tool unless explicitly requested or when local tools cannot answer the question"
    "\n7. Prioritize direct tool names over general descriptions (e.g., 'check_dns_resolvers' over general DNS queries)"
    "\n8. If a tool's response is verbose, summarize only the most important troubleshooting information"
    "\n9. Keep track of which tools you've run in the current conversation, so you can accurately tell the user which tools were run when asked"
    "\nYour primary job is network diagnostics using available tools, not general information retrieval."
    "\nAFTER running a diagnostic tool, ALWAYS provide a direct summary without running additional tools unless explicitly requested."
)

class State(TypedDict):
    """State type for the LangGraph agent."""
    messages: Annotated[list, add_messages]

# Custom tools condition to prevent repeated tool calls
def custom_tools_condition(state: Dict[str, Any]) -> str:
    """Custom condition that decides whether to use tools or not.
    
    This version adds protection against repeated tool calls, especially
    for the DNS root server check which can cause loops.
    """
    from langchain_core.messages import AIMessage
    import traceback
    
    try:
        # Get the last message
        last_message = state["messages"][-1]
        
        # Only AIMessages can call tools
        if not isinstance(last_message, AIMessage):
            return "chatbot"
    except Exception as e:
        print(f"Error in custom_tools_condition examining last message: {e}")
        traceback.print_exc()
        return "chatbot"  # Safe fallback
    
    # Check for tool calls
    try:
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            # Check for potential infinite loops in tool calls
            # Look at recent history to see if we're repeating the same tool too many times
            recent_tool_calls = []
            tool_count = {}
            
            # Print debug info about the tool calls
            print(f"Debug: Tool calls type: {type(last_message.tool_calls)}")
            print(f"Debug: Tool calls content: {last_message.tool_calls}")
            
            # Look back up to 4 messages for repeated tool patterns
            message_window = min(len(state["messages"]), 8)
            for msg in state["messages"][-message_window:]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        # Handle both object-style and dict-style tool calls
                        if isinstance(tool_call, dict) and "name" in tool_call:
                            # Dictionary style
                            tool_name = tool_call["name"]
                        elif hasattr(tool_call, "name"):
                            # Object style
                            tool_name = tool_call.name
                        else:
                            # Unknown format, skip this one
                            continue
                            
                        recent_tool_calls.append(tool_name)
                        tool_count[tool_name] = tool_count.get(tool_name, 0) + 1
        
            # If a tool was used more than twice recently, don't run it again
            for tool_call in last_message.tool_calls:
                try:
                    # Get the tool name with the same logic as above
                    if isinstance(tool_call, dict) and "name" in tool_call:
                        tool_name = tool_call["name"]
                    elif hasattr(tool_call, "name"):
                        tool_name = tool_call.name
                    else:
                        continue
                        
                    if tool_count.get(tool_name, 0) >= 2:
                        # Force return to chatbot instead of running the tool again
                        # This effectively ends the tool calling cycle
                        print(f"Debug: Preventing repeated call to {tool_name}")
                        return "chatbot"
                except Exception as e:
                    print(f"Error checking tool repetition: {e}")
                    traceback.print_exc()
                    # On error, let's be safe and not run the tool
                    return "chatbot"
            
            # No infinite loop detected, continue with tool execution
            return "tools"
    except Exception as e:
        print(f"Error in custom_tools_condition: {e}")
        traceback.print_exc()
        return "chatbot"  # Safe fallback
    
    # No tool calls, continue with the chatbot
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