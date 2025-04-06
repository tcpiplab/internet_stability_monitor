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

# Global variables for tool call tracking
TOOL_CALL_COUNTER = 0
MAX_TOOL_CALLS_PER_QUERY = 1  # Strict limit: one tool per query
EXECUTED_TOOLS = []  # List of tools that have been successfully executed
QUERY_COMPLETED = False  # Flag to indicate when we've run a tool and should stop

# Custom tools condition to prevent repeated tool calls and enforce tool selection rules
def custom_tools_condition(state: Dict[str, Any]) -> str:
    """Custom condition that decides whether to use tools or not.
    
    This improved version:
    1. Limits total tool calls per user query
    2. Prevents repeated tool calls
    3. Adds extra checks for correct tool selection
    """
    from langchain_core.messages import AIMessage, HumanMessage
    import traceback
    
    # Access all globals at the beginning of the function
    global TOOL_CALL_COUNTER, EXECUTED_TOOLS, QUERY_COMPLETED
    
    try:
        # Get the last message
        last_message = state["messages"][-1]
        
        # Reset flags for new human messages - this is critical
        if isinstance(last_message, HumanMessage):
            TOOL_CALL_COUNTER = 0
            EXECUTED_TOOLS.clear()
            QUERY_COMPLETED = False
            print("Debug: Cleared tool execution history for new human message")
            return "chatbot"
        
        # Only AIMessages can call tools
        if not isinstance(last_message, AIMessage):
            return "chatbot"  # Safe fallback for non-AI, non-human messages
    except Exception as e:
        print(f"Error examining message type: {e}")
        traceback.print_exc()
        return "chatbot"  # Safe fallback
    
    # Check for tool calls
    try:
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            # Check if we've already completed this query with a tool
            if QUERY_COMPLETED:
                print("Debug: Query already completed with a tool, stopping further tool execution")
                return END  # Return END to stop the graph execution
            
            # Hard limit on total tool calls per user query
            if TOOL_CALL_COUNTER >= MAX_TOOL_CALLS_PER_QUERY:
                print(f"Debug: Maximum tool call limit of {MAX_TOOL_CALLS_PER_QUERY} reached, stopping execution")
                QUERY_COMPLETED = True
                return END  # Return END to stop the graph execution
            
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
                
                # Only check against EXECUTED_TOOLS (tools that actually ran),
                # not against all requested tools
                if current_tool in EXECUTED_TOOLS:
                    print(f"Debug: Preventing repeated call to {current_tool} (already executed)")
                    return END  # Return END to stop the graph execution
                    
                # Find the current query to check if the correct tool is being used
                user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
                current_query = user_messages[-1].content.lower() if user_messages else ""
                
                # Strict enforcement of tool selection rules from system prompt
                expected_tool = None
                
                if "location" in current_query:
                    expected_tool = "get_isp_location"
                elif "external ip" in current_query:
                    expected_tool = "get_external_ip"
                elif "local ip" in current_query:
                    expected_tool = "get_local_ip"
                
                # If we have an expected tool but the model chose a different one, warn and block execution
                if expected_tool and current_tool != expected_tool:
                    print(f"ERROR: Model trying to use incorrect tool '{current_tool}' for query that requires '{expected_tool}'")
                    print("Blocking incorrect tool execution to enforce system prompt rules")
                    QUERY_COMPLETED = True  # Mark as completed to prevent more attempts
                    return END  # Stop execution to prevent wrong tool use
                
                # Register that we're about to execute this tool
                EXECUTED_TOOLS.append(current_tool)
                print(f"Debug: Allowing execution of {current_tool} (first time)")
                print(f"Debug: Executed tools so far: {EXECUTED_TOOLS}")
                
                # Increment our global counter, mark query as completed, and allow the tool call
                TOOL_CALL_COUNTER += 1
                QUERY_COMPLETED = True
                print("Debug: Executing tool and marking query as completed")
                return "tools"
            
            # No valid tool identified
            return END  # Return END to stop the graph execution
    except Exception as e:
        print(f"Error in custom_tools_condition: {e}")
        traceback.print_exc()
        return END  # Return END to stop the graph execution
    
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
        
        # Helper function to route after tool execution
        def route_after_tool(state: State) -> str:
            global QUERY_COMPLETED
            # If we've executed a tool, we always want to end the graph
            if QUERY_COMPLETED:
                return END
            return "chatbot"
        
        # Build the graph
        graph_builder = StateGraph(State)
        graph_builder.add_node("chatbot", chatbot)
        
        tool_node = ToolNode(tools=self.tools + [self.search_tool])
        graph_builder.add_node("tools", tool_node)
        
        graph_builder.add_conditional_edges(
            "chatbot",
            custom_tools_condition,
        )
        
        # After a tool is executed, check if we should end
        graph_builder.add_conditional_edges(
            "tools",
            route_after_tool,
        )
        
        graph_builder.add_edge(START, "chatbot")
        
        # Compile the graph with the memory checkpointer
        return graph_builder.compile(checkpointer=self.memory.memory)
    
    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process a user input and return the agent's response."""
        from langchain_core.messages import HumanMessage
        
        # Explicitly reset global flags for each new input
        global TOOL_CALL_COUNTER, EXECUTED_TOOLS, QUERY_COMPLETED
        TOOL_CALL_COUNTER = 0
        EXECUTED_TOOLS.clear()
        QUERY_COMPLETED = False
        print("Debug: Reset all tool execution flags for new user input")
        
        # Check for explicit tool selection based on keywords
        user_input_lower = user_input.lower()
        forced_tool = None
        
        # Apply tool selection rules from system prompt
        if "location" in user_input_lower:
            forced_tool = "get_isp_location"
            print(f"Debug: Enforcing tool selection rule: {forced_tool} for location query")
        elif "external ip" in user_input_lower:
            forced_tool = "get_external_ip"
            print(f"Debug: Enforcing tool selection rule: {forced_tool} for external IP query")
        elif "local ip" in user_input_lower:
            forced_tool = "get_local_ip"
            print(f"Debug: Enforcing tool selection rule: {forced_tool} for local IP query")
        
        config = self.memory.get_config()
        config["recursion_limit"] = 5  # Set a lower recursion limit
        
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
        response = self.graph.invoke(messages, config)
        
        # Debug: Print all messages for troubleshooting
        if response and "messages" in response:
            print("Debug: All response messages:")
            for i, msg in enumerate(response["messages"]):
                msg_type = type(msg).__name__
                msg_content = getattr(msg, "content", "No content")[:100] + "..." if hasattr(msg, "content") and len(getattr(msg, "content", "")) > 100 else getattr(msg, "content", "No content")
                print(f"  Message {i}: {msg_type} - {msg_content}")
        
        # Enhanced tool result extraction that's more precise and finds the latest tool call
        if response and "messages" in response:
            # Find tool calls related to the current query
            current_human_msg_idx = -1
            tool_call_idx = -1
            latest_tool_call_id = None
            latest_tool_name = None
            
            # First, find the index of the current human message
            for i, msg in enumerate(response["messages"]):
                if isinstance(msg, HumanMessage) and msg.content == user_input:
                    current_human_msg_idx = i
                    break
            
            # If we found the human message, look for tool calls after it
            if current_human_msg_idx >= 0:
                for i, msg in enumerate(response["messages"]):
                    if (i > current_human_msg_idx and 
                        hasattr(msg, "tool_calls") and 
                        msg.tool_calls):
                        
                        tool_call = msg.tool_calls[0]
                        if isinstance(tool_call, dict) and "id" in tool_call:
                            latest_tool_call_id = tool_call["id"]
                            latest_tool_name = tool_call.get("name", "unknown")
                        elif hasattr(tool_call, "id"):
                            latest_tool_call_id = tool_call.id
                            latest_tool_name = getattr(tool_call, "name", "unknown")
                            
                        tool_call_idx = i
                        print(f"Debug: Found latest tool call after current query: {latest_tool_name} with ID {latest_tool_call_id}")
                        break
            
            # Check if the correct tool was used according to rules
            if latest_tool_name and forced_tool and latest_tool_name != forced_tool:
                print(f"Warning: Wrong tool called! Used {latest_tool_name} but should have used {forced_tool}")
                print("Trying to recover and display results anyway...")
            
            # Now find the tool response for this specific tool call
            if latest_tool_call_id:
                for i, msg in enumerate(response["messages"]):
                    if (i > tool_call_idx and 
                        hasattr(msg, "tool_call_id") and 
                        msg.tool_call_id == latest_tool_call_id):
                        
                        print(f"Debug: Found most recent tool response for {latest_tool_name}: {msg.content[:100]}...")
                        print(f"\nTool Result ({latest_tool_name}): {msg.content}")
                        
                        # Find AI response after this specific tool result
                        ai_response_found = False
                        for later_msg in response["messages"]:
                            if (hasattr(later_msg, "content") and 
                                not hasattr(later_msg, "tool_calls") and 
                                not hasattr(later_msg, "tool_call_id") and
                                response["messages"].index(later_msg) > i):
                                
                                print(f"\n{later_msg.content}")
                                ai_response_found = True
                                break
                                
                        # If no AI response found, just print the last message
                        if not ai_response_found:
                            last_msg = response["messages"][-1]
                            if hasattr(last_msg, "content") and not hasattr(last_msg, "tool_calls"):
                                print(f"\n{last_msg.content}")
                        
                        return response
            
            # If no tool result found, just print the last message
            last_message = response["messages"][-1]
            if hasattr(last_message, "content") and last_message.content:
                print(f"\n{last_message.content}")
        
        return response
    
    def pretty_print_message(self, message: BaseMessage) -> None:
        """Pretty print a message from the agent."""
        # Skip printing system messages and debug information
        if hasattr(message, "type") and message.type == "system":
            return
        
        # Skip printing tool call messages
        if hasattr(message, "tool_calls") and message.tool_calls:
            return
            
        # Skip printing empty messages
        if hasattr(message, "content") and not message.content:
            return
            
        # Use pretty_print if available
        if hasattr(message, "pretty_print"):
            message.pretty_print()
        else:
            from interface import print_ai_message
            print_ai_message(message.content if hasattr(message, "content") else str(message))