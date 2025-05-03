"""
LangGraph agent setup and configuration.

This module sets up the LangGraph agent that powers the chatbot, including
the system prompt, model configuration, and graph structure.

The agent includes:
1. ReAct-based reasoning for network diagnostics
2. Tool providers for organizing available tools
3. Anti-recursion detection to prevent infinite loops (see route_agent function)
4. Error handling and debug logging
"""

from typing import Dict, Any, List, Callable, Optional, TypeVar, Protocol
from typing_extensions import TypedDict, Annotated
from dataclasses import dataclass
from abc import ABC, abstractmethod

from langchain_core.tools import BaseTool, tool
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# Create our own ToolExecutor since it seems to be missing
class ToolExecutor:
    """Tool executor class."""
    
    def __init__(self, tools):
        """Initialize with a list of tools."""
        self.tools = {tool.name: tool for tool in tools}
    
    def invoke(self, input_dict):
        """Invoke a tool with inputs."""
        tool_name = input_dict.pop("tool_name")
        tool = self.tools.get(tool_name)
        if tool is None:
            raise ValueError(f"Tool {tool_name} not found. Available tools: {list(self.tools.keys())}")
        return tool.invoke(input_dict)
from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.agents.agent import AgentFinish, AgentAction
from langchain import hub
from langchain.agents import create_react_agent
from langchain.agents.format_scratchpad import format_log_to_str

# Type for tool results
ToolResult = TypeVar('ToolResult')

class ToolProvider(Protocol):
    """Protocol for tool providers that can be added to the agent."""
    
    @property
    def tools(self) -> List[BaseTool]:
        """Get the tools provided by this provider."""
        ...
    
    @property
    def name(self) -> str:
        """Get the name of this tool provider."""
        ...

@dataclass
class State:
    """State type for the LangGraph agent."""
    messages: List[BaseMessage]
    current_tool: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[str] = None
    intermediate_steps: List[tuple] = None
    
    def __post_init__(self):
        if self.intermediate_steps is None:
            self.intermediate_steps = []

class ChatbotAgent:
    """Enhanced LangGraph agent with extensible tool support."""
    
    def __init__(self, 
                 tool_providers: List[ToolProvider],
                 memory_system: Any,
                 model_name: str = "qwen2.5",
                 max_iterations: int = 10) -> None:
        """Initialize the chatbot agent."""
        self.tool_providers = tool_providers
        self.memory = memory_system
        self.model_name = model_name
        self.max_iterations = max_iterations
        
        # Collect all tools from providers
        self.tools: List[BaseTool] = []
        for provider in tool_providers:
            self.tools.extend(provider.tools)
        
        # Set up the base model
        self.model = ChatOllama(model=model_name)
        
        # Create the LangChain memory
        self.langchain_memory = ConversationBufferMemory(
            return_messages=True,
            output_key="output",
            input_key="input"
        )
        
        # Get the ReAct prompt
        prompt = hub.pull("hwchase17/react-chat")
        
        # Create the agent using create_react_agent
        self.agent = create_react_agent(
            llm=self.model,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create the graph
        self.graph = self._create_graph()
    
    def _create_system_prompt(self) -> str:
        # This method can potentially be removed or adapted if needed for ReAct prompt customization
        return ""

    def _create_graph(self) -> StateGraph:
        """Create the LangGraph execution graph."""
        # Create tool executor
        tool_executor = ToolExecutor(tools=self.tools)
        
        # Define graph nodes
        def agent_node(state: State) -> Dict[str, Any]:
            """Run the agent to decide the next action."""
            
            # --- ADJUST FOR REACT AGENT ---
            # Format intermediate steps for the ReAct agent scratchpad
            scratchpad = format_log_to_str(state.intermediate_steps)

            # Prepare input for agent.invoke
            agent_inputs = {
                "input": state.messages[-1].content,
                "chat_history": state.messages[:-1],
                "agent_scratchpad": scratchpad,
                "intermediate_steps": state.intermediate_steps # Add intermediate_steps directly
            }

            # Get agent response using invoke
            result = self.agent.invoke(agent_inputs)

            # --- Define tools known to take NO arguments ---
            no_arg_tools = {
                "get_external_ip",
                "get_local_ip",
                "get_isp_location",
                "check_external_ip_change",
                "check_internet_connection",
                "check_layer_three_network",
                "check_dns_resolvers",
                "check_ollama",
                "get_os",
                "check_cdn_reachability",
                "check_whois_servers",
                "check_tls_ca_servers",
                "check_smtp_servers",
                "run_mac_speed_test", # Technically takes args, but often called without by agent
                "check_dns_root_servers_reachability",
                "check_local_layer_two_network",
                "check_websites"
            }

            # Handle the result (keep AgentFinish/AgentAction logic)
            if isinstance(result, AgentFinish):
                # Final response - mark as complete
                return {
                    "messages": state.messages + [AIMessage(content=result.return_values["output"])],
                    "intermediate_steps": state.intermediate_steps,
                    "current_tool": None,
                    "tool_input": None,
                    "tool_output": None
                }
            elif isinstance(result, AgentAction):
                # --- Intercept and correct tool input if necessary ---
                agent_tool_input = result.tool_input
                actual_tool_input = agent_tool_input # Default to agent's provided input

                if result.tool in no_arg_tools:
                    # If the target tool takes no args, force input to {}
                    # regardless of what the agent provided (null, (), etc.)
                    print(f"DEBUG: Overriding input for no-arg tool '{result.tool}'. Agent provided: {agent_tool_input}")
                    actual_tool_input = {}
                elif isinstance(agent_tool_input, dict) and list(agent_tool_input.keys()) == ['input']:
                    # Handle cases where agent might wrap a single string argument 
                    # in {'input': 'some_value'} for tools that expect a direct string.
                    # This might need refinement based on tool specifics.
                    print(f"DEBUG: Unwrapping potential single string input for tool '{result.tool}'. Agent provided: {agent_tool_input}")
                    actual_tool_input = agent_tool_input['input'] 
                # Note: If tool expects complex dict input, ensure agent provides it correctly

                # Next action - use the potentially corrected actual_tool_input
                return {
                    "messages": state.messages, # Keep messages as is
                    "intermediate_steps": state.intermediate_steps,
                    "current_tool": result.tool,
                    "tool_input": actual_tool_input, # Use the corrected input
                    "tool_output": None
                }
            else:
                # Unexpected result type - mark as complete
                error_msg = f"Unexpected agent result type: {type(result)}"
                return {
                    "messages": state.messages + [AIMessage(content=error_msg)],
                    "intermediate_steps": state.intermediate_steps,
                    "current_tool": None,
                    "tool_input": None,
                    "tool_output": None
                }
        
        def tool_node(state: State) -> Dict[str, Any]:
            """Execute the selected tool."""
            if not state.current_tool or state.tool_input is None:
                return {
                    **state.__dict__,
                    "current_tool": None, "tool_input": None, "tool_output": None
                }
            
            # Prepare tool input, handling potential placeholders from the agent
            actual_tool_input = state.tool_input
            if isinstance(actual_tool_input, dict) and list(actual_tool_input.keys()) == ['input'] and actual_tool_input['input'] == '()':
                 # Check if the actual tool (from self.tools) expects arguments. 
                 # This is complex, so for now, assume empty dict if input is '()' placeholder
                 print(f"DEBUG: Tool {state.current_tool} received placeholder input {actual_tool_input}, assuming no args needed.")
                 actual_tool_input = {} 

            print(f"DEBUG: Executing tool: {state.current_tool} with processed input: {actual_tool_input}")
            
            # Execute the tool
            try:
                # Pass the processed input
                tool_executor_input = {"tool_name": state.current_tool, **actual_tool_input}
                result = tool_executor.invoke(tool_executor_input)
                print(f"DEBUG: Tool {state.current_tool} result: {result}")
                
                # Record the tool call in memory
                self.memory.record_tool_call(state.current_tool, actual_tool_input, result)
                
                # Create the success action tuple for intermediate steps
                action_tuple = (AgentAction(tool=state.current_tool, tool_input=actual_tool_input, log=""), str(result))
                new_steps = state.intermediate_steps + [action_tuple]
                
                # Add debug logging to help detect patterns in tool usage
                if len(new_steps) >= 2:
                    prev_tool = new_steps[-2][0].tool if len(new_steps) >= 2 else "none"
                    print(f"DEBUG: Tool sequence: {prev_tool} -> {state.current_tool}")

                return {
                    "messages": state.messages,
                    "intermediate_steps": new_steps,
                    "current_tool": None,
                    "tool_input": None,
                    "tool_output": str(result)
                }
            except Exception as e:
                print(f"ERROR: Error executing tool {state.current_tool} with input {actual_tool_input}: {e}") 
                error_msg = f"Error executing {state.current_tool}: {str(e)}"
                
                # Create the failure action tuple safely
                # Use the potentially modified actual_tool_input
                failed_action_tuple = (AgentAction(tool=state.current_tool, tool_input=actual_tool_input, log=f"Tool execution failed: {error_msg}"), f"Tool execution failed: {error_msg}")
                new_steps = state.intermediate_steps + [failed_action_tuple]
                
                return {
                    "messages": state.messages + [AIMessage(content=error_msg)],
                    "intermediate_steps": new_steps,
                    "current_tool": None,
                    "tool_input": None,
                    "tool_output": None
                }
        
        # Build the graph
        workflow = StateGraph(State)
        
        # Add nodes
        workflow.add_node("agent", agent_node)
        workflow.add_node("tool", tool_node)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Define conditional routing logic
        def route_agent(state: State) -> str:
            """Determine the next step after the agent node."""
            if state.current_tool:
                # Check maximum iterations
                if len(state.intermediate_steps) >= self.max_iterations:
                    state.messages.append(AIMessage(content=f"Reached max iterations ({self.max_iterations}). Finishing."))
                    return END
                
                # Check for repetitive tool calls (infinite loop detection)
                if len(state.intermediate_steps) >= 3:
                    # Get the last 3 tool calls
                    recent_tools = [step[0].tool for step in state.intermediate_steps[-3:]]
                    
                    # Check if it's the same tool being called repeatedly
                    if len(set(recent_tools)) == 1 and recent_tools[0] == state.current_tool:
                        # We have detected the same tool being called 3+ times in a row
                        warning_msg = f"Detected repetitive calls to the same tool '{state.current_tool}'. This might indicate an infinite loop. Stopping execution."
                        print(f"WARNING: {warning_msg}")
                        state.messages.append(AIMessage(content=warning_msg))
                        return END
                
                return "tool"
            else:
                return END
        
        # Add conditional edges from agent node
        workflow.add_conditional_edges(
            "agent",
            route_agent,
            {
                "tool": "tool",
                END: END
            }
        )
        
        # Add edge from tool node back to agent node
        workflow.add_edge("tool", "agent")
        
        # Compile the graph
        return workflow.compile()
    
    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input using the LangGraph agent."""
        # Load history (if needed - LangChain memory might handle this)
        # self.langchain_memory.load_memory_variables({})
        # chat_history = self.langchain_memory.buffer_as_messages
        
        # Prepare initial state
        initial_state = State(
            messages=[HumanMessage(content=user_input)],
            intermediate_steps=[] # Ensure intermediate_steps is initialized as empty list
        )
        
        final_state: Optional[Dict[str, Any]] = None
        try:
            # Invoke the graph
            # Set recursion_limit slightly higher to allow the graph to reach END naturally
            print("DEBUG: Invoking graph...") # Debug print
            final_state = self.graph.invoke(initial_state, config={"recursion_limit": self.max_iterations + 5})
            print(f"DEBUG: Graph invocation complete. Final state type: {type(final_state)}") # Debug print
        except Exception as e:
            print(f"ERROR: Error invoking graph: {e}") # Log graph errors
            # Handle graph invocation error, return an error response
            return {
                 "response": f"An error occurred during graph processing: {e}",
                 "intermediate_steps": []
            }

        final_response_message = "No response generated."
        final_intermediate_steps = []

        if final_state: # Check if final_state is not None and is a dict (implicitly checked by .get)
            print(f"DEBUG: Processing final state: {final_state}") # Debug print
            messages = final_state.get('messages', []) # Use .get() for safety
            if messages:
                 # Ensure messages is a list before proceeding
                 if isinstance(messages, list):
                     ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
                     if ai_messages:
                         final_response_message = ai_messages[-1].content
                 else:
                     print(f"WARNING: Expected 'messages' to be a list, but got {type(messages)}")
            else:
                 print("DEBUG: No 'messages' key found in final state or it was empty.")

            final_intermediate_steps = final_state.get('intermediate_steps', []) # Use .get()
            print(f"DEBUG: Final response: {final_response_message}") # Debug print
            print(f"DEBUG: Final intermediate steps: {final_intermediate_steps}") # Debug print

            # Save context only if processing was potentially successful (even if no response generated)
            try:
                print("DEBUG: Saving context to memory...") # Debug print
                self.langchain_memory.save_context(
                    {"input": user_input},
                    {"output": final_response_message}
                )
                self.memory.add_interaction(user_input, final_response_message) # Assuming add_interaction exists
                self.memory.save_cache() # Save custom cache
                print("DEBUG: Context saved.") # Debug print
            except Exception as e:
                 print(f"ERROR: Error saving context to memory: {e}") # Log memory errors

        else:
             print("WARNING: final_state was None after graph invocation.")

        return {
            "response": final_response_message,
            "intermediate_steps": final_intermediate_steps
        }
    
    def pretty_print_message(self, message: BaseMessage) -> None:
        """Pretty print a message based on its type."""
        if isinstance(message, HumanMessage):
            print(f"User: {message.content}")
        elif isinstance(message, AIMessage):
            print(f"Chatbot: {message.content}")
        elif isinstance(message, SystemMessage):
            print(f"System: {message.content}")
        else:
            print(message)