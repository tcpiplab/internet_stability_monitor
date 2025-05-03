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

from typing import Dict, Any, List, Callable, Optional, TypeVar, Protocol, Pattern
from typing_extensions import TypedDict, Annotated
from dataclasses import dataclass
from abc import ABC, abstractmethod
import re

from colorama import Fore, Style
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

# Helper functions for colored output
def debug_print(message: str) -> None:
    """Print a debug message in gray color."""
    print(f"{Style.DIM}DEBUG: {message}{Style.RESET_ALL}")

def warning_print(message: str) -> None:
    """Print a warning message in yellow color."""
    print(f"{Fore.YELLOW}WARNING: {message}{Style.RESET_ALL}")
    
def error_print(message: str) -> None:
    """Print an error message in red color."""
    print(f"{Fore.RED}ERROR: {message}{Style.RESET_ALL}")

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
    last_question: Optional[str] = None  # The last question asked by the bot
    pending_tools: List[str] = None  # Tools mentioned in the last question
    
    def __post_init__(self):
        if self.intermediate_steps is None:
            self.intermediate_steps = []
        if self.pending_tools is None:
            self.pending_tools = []

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

            # Custom wrapper to handle mixed output with both actions and final answers
            try:
                # First attempt with standard parser
                result = self.agent.invoke(agent_inputs)
            except Exception as e:
                if "Parsing LLM output produced both a final answer and a parse-able action" in str(e):
                    debug_print("Detected mixed output with both action and final answer")
                    
                    # Get the raw LLM output directly from the error message
                    # The error should contain the full output that caused the parsing issue
                    # If not, we need to examine it via debug methods
                    
                    # Since we can't easily get the raw output from the LLM response that caused the error,
                    # we'll manually recreate the output based on the patterns the parser is using
                    raw_output = str(e)
                    
                    # If we can't extract useful information from the error message,
                    # call the LLM directly with a more explicit instruction
                    if "Parsing LLM output" in raw_output and len(raw_output) < 200:
                        debug_print("Error message doesn't contain full output, making direct LLM call")
                        # Create a simpler prompt to get a direct response
                        direct_messages = [
                            SystemMessage(content="You are a network diagnostics assistant that can use tools to help users."),
                            HumanMessage(content=f"Previous conversation: {state.messages[:-1]}\n\nUser question: {state.messages[-1].content}\n\nYou have these tools available: {[tool.name for tool in self.tools]}\n\nRespond in ReAct format with EITHER an Action OR a Final Answer, not both.")
                        ]
                        raw_output = self.model.invoke(direct_messages).content
                        debug_print(f"Direct LLM response: {raw_output}")
                    
                    # Get the patterns directly in case the parser doesn't expose the methods we need
                    action_pattern = r"Action: (.*?)[\n]*Action Input:[\s]*(.*)"
                    final_answer_pattern = r"Final Answer: (.*)"
                    
                    # Try to extract action first - this makes the agent more proactive
                    action_match = re.search(action_pattern, raw_output, re.DOTALL)
                    
                    try:
                        # Try to use the agent's parser methods if available
                        if hasattr(self.agent.output_parser, "get_action_match"):
                            action_match = self.agent.output_parser.get_action_match(raw_output)
                    except Exception as parser_error:
                        debug_print(f"Couldn't use agent parser methods: {parser_error}")
                    
                    if action_match:
                        # There's an action, prioritize it over the final answer
                        tool_name = action_match.group(1).strip()
                        
                        # Extract action input, providing empty dict as fallback
                        action_input = "{}"
                        try:
                            # Try to use the output parser's method if available
                            if hasattr(self.agent.output_parser, "get_action_input_match"):
                                action_input_match = self.agent.output_parser.get_action_input_match(raw_output)
                                if action_input_match:
                                    action_input = action_input_match.group(1).strip()
                            else:
                                # Use our own regex as fallback
                                action_input = action_match.group(2).strip() if len(action_match.groups()) > 1 else "{}"
                        except Exception as input_error:
                            debug_print(f"Error extracting action input: {input_error}")
                        
                        # Parse action input to dict if possible
                        try:
                            if hasattr(self.agent.output_parser, "parse_action_input"):
                                action_input_dict = self.agent.output_parser.parse_action_input(action_input)
                            else:
                                # Simple parsing fallback
                                import json
                                try:
                                    action_input_dict = json.loads(action_input)
                                except json.JSONDecodeError:
                                    action_input_dict = {"input": action_input}
                        except Exception:
                            # If parsing fails, use the raw string
                            action_input_dict = {"input": action_input}
                            
                        # Create an AgentAction manually
                        debug_print(f"Manually extracted action: {tool_name} with input: {action_input_dict}")
                        result = AgentAction(tool=tool_name, tool_input=action_input_dict, log=raw_output)
                    else:
                        # No action found, look for final answer
                        final_answer_match = re.search(final_answer_pattern, raw_output, re.DOTALL)
                        
                        try:
                            # Try to use the agent's parser methods if available
                            if hasattr(self.agent.output_parser, "get_final_answer_match"):
                                final_answer_match = self.agent.output_parser.get_final_answer_match(raw_output)
                        except Exception as parser_error:
                            debug_print(f"Couldn't use agent parser methods: {parser_error}")
                        
                        if final_answer_match:
                            answer = final_answer_match.group(1).strip()
                            debug_print(f"Manually extracted final answer: {answer}")
                            result = AgentFinish(return_values={"output": answer}, log=raw_output)
                        else:
                            # Neither found clearly - default to treating as a final answer
                            debug_print(f"Could not extract action or answer cleanly, treating as final answer")
                            result = AgentFinish(return_values={"output": raw_output}, log=raw_output)
                else:
                    # Re-raise if it's a different error
                    raise

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
                # Extract the output content
                output_content = result.return_values["output"]
                
                # Check if the response contains a question that might need follow-up
                question_markers = [
                    "would you like me to", "would you like to", "do you want me to",
                    "should i", "shall i", "do you want to", "would you prefer",
                    "would you like", "do you want", "should we", "shall we"
                ]
                
                # List of tools that might be mentioned in questions
                tool_names = [
                    "get_external_ip", "get_local_ip", "check_external_ip_change", 
                    "check_internet_connection", "check_layer_three_network",
                    "check_dns_resolvers", "check_websites", "check_dns_root_servers_reachability",
                    "check_local_layer_two_network", "check_cdn_reachability", "check_whois_servers",
                    "check_tls_ca_servers", "check_smtp_servers", "run_mac_speed_test"
                ]
                
                # Convert tool names to more readable format for text matching
                readable_tool_names = [name.replace("_", " ").replace("check ", "").replace("get ", "") for name in tool_names]
                
                # Look for question patterns
                output_lower = output_content.lower()
                is_question = False
                pending_tools = []
                
                if "?" in output_content:
                    for marker in question_markers:
                        if marker in output_lower:
                            is_question = True
                            # Try to identify mentioned tools
                            for i, readable_name in enumerate(readable_tool_names):
                                if readable_name in output_lower:
                                    pending_tools.append(tool_names[i])
                            break
                
                # Final response - mark as complete, but track if it's a question
                return {
                    "messages": state.messages + [AIMessage(content=output_content)],
                    "intermediate_steps": state.intermediate_steps,
                    "current_tool": None,
                    "tool_input": None,
                    "tool_output": None,
                    "last_question": output_content if is_question else None,
                    "pending_tools": pending_tools
                }
            elif isinstance(result, AgentAction):
                # --- Intercept and correct tool input if necessary ---
                agent_tool_input = result.tool_input
                actual_tool_input = agent_tool_input # Default to agent's provided input

                if result.tool in no_arg_tools:
                    # If the target tool takes no args, force input to {}
                    # regardless of what the agent provided (null, (), etc.)
                    debug_print(f"Overriding input for no-arg tool '{result.tool}'. Agent provided: {agent_tool_input}")
                    actual_tool_input = {}
                elif isinstance(agent_tool_input, dict) and list(agent_tool_input.keys()) == ['input']:
                    # Handle cases where agent might wrap a single string argument 
                    # in {'input': 'some_value'} for tools that expect a direct string.
                    # This might need refinement based on tool specifics.
                    debug_print(f"Unwrapping potential single string input for tool '{result.tool}'. Agent provided: {agent_tool_input}")
                    actual_tool_input = agent_tool_input['input'] 
                # Note: If tool expects complex dict input, ensure agent provides it correctly

                # Next action - use the potentially corrected actual_tool_input
                return {
                    "messages": state.messages, # Keep messages as is
                    "intermediate_steps": state.intermediate_steps,
                    "current_tool": result.tool,
                    "tool_input": actual_tool_input, # Use the corrected input
                    "tool_output": None,
                    "last_question": state.last_question,  # Preserve last question
                    "pending_tools": state.pending_tools  # Preserve pending tools
                }
            else:
                # Unexpected result type - mark as complete
                error_msg = f"Unexpected agent result type: {type(result)}"
                return {
                    "messages": state.messages + [AIMessage(content=error_msg)],
                    "intermediate_steps": state.intermediate_steps,
                    "current_tool": None,
                    "tool_input": None,
                    "tool_output": None,
                    "last_question": None,  # No question in error case
                    "pending_tools": []  # No pending tools in error case
                }
        
        def tool_node(state: State) -> Dict[str, Any]:
            """Execute the selected tool."""
            if not state.current_tool or state.tool_input is None:
                # Include last_question and pending_tools in the returned state
                return {
                    **state.__dict__,
                    "current_tool": None, 
                    "tool_input": None, 
                    "tool_output": None,
                    "last_question": state.last_question,
                    "pending_tools": state.pending_tools
                }
            
            # Prepare tool input, handling potential placeholders from the agent
            actual_tool_input = state.tool_input
            if isinstance(actual_tool_input, dict) and list(actual_tool_input.keys()) == ['input'] and actual_tool_input['input'] == '()':
                 # Check if the actual tool (from self.tools) expects arguments. 
                 # This is complex, so for now, assume empty dict if input is '()' placeholder
                 debug_print(f"Tool {state.current_tool} received placeholder input {actual_tool_input}, assuming no args needed.")
                 actual_tool_input = {} 

            debug_print(f"Executing tool: {state.current_tool} with processed input: {actual_tool_input}")
            
            # Execute the tool
            try:
                # Pass the processed input
                tool_executor_input = {"tool_name": state.current_tool, **actual_tool_input}
                result = tool_executor.invoke(tool_executor_input)
                debug_print(f"Tool {state.current_tool} result: {result}")
                
                # Record the tool call in memory
                self.memory.record_tool_call(state.current_tool, actual_tool_input, result)
                
                # Create the success action tuple for intermediate steps
                action_tuple = (AgentAction(tool=state.current_tool, tool_input=actual_tool_input, log=""), str(result))
                new_steps = state.intermediate_steps + [action_tuple]
                
                # Add debug logging to help detect patterns in tool usage
                if len(new_steps) >= 2:
                    prev_tool = new_steps[-2][0].tool if len(new_steps) >= 2 else "none"
                    debug_print(f"Tool sequence: {prev_tool} -> {state.current_tool}")

                return {
                    "messages": state.messages,
                    "intermediate_steps": new_steps,
                    "current_tool": None,
                    "tool_input": None,
                    "tool_output": str(result),
                    "last_question": state.last_question,  # Preserve last question
                    "pending_tools": state.pending_tools  # Preserve pending tools
                }
            except Exception as e:
                error_print(f"Error executing tool {state.current_tool} with input {actual_tool_input}: {e}") 
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
                    "tool_output": None,
                    "last_question": None,  # No question in error case
                    "pending_tools": []  # No pending tools in error case
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
                        warning_print(warning_msg)
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
        # Get the last conversation state if available from memory
        last_state = None
        try:
            history = self.memory.get_direct_history()
            if history and isinstance(history, dict) and "last_state" in history:
                last_state = history["last_state"]
        except Exception as e:
            debug_print(f"Error retrieving last state: {e}")
            last_state = None
        
        # Check if the user's response is a simple yes/no to a previous question
        is_continuing_conversation = False
        pending_tools = []
        modified_input = user_input
        
        # Try to get the last_state from memory cache
        if not last_state:
            try:
                cached_last_state = self.memory.get_cached_value("last_state")
                if cached_last_state and isinstance(cached_last_state, dict):
                    debug_print("Retrieved last_state from cache")
                    last_state = cached_last_state
            except Exception as e:
                debug_print(f"Error retrieving cached last_state: {e}")
                last_state = None
                
        if last_state and isinstance(last_state, dict):
            last_question = last_state.get("last_question")
            pending_tools = last_state.get("pending_tools", [])
            
            debug_print(f"Last question: {last_question is not None}, Pending tools: {pending_tools}")
            
            if last_question and pending_tools:
                # Check for affirmative responses
                affirmative_responses = ["yes", "yes please", "sure", "okay", "ok", "yep", "yeah", "please do", "go ahead"]
                negative_responses = ["no", "no thanks", "nope", "don't", "do not"]
                
                user_input_lower = user_input.lower().strip()
                
                if any(user_input_lower == resp for resp in affirmative_responses):
                    is_continuing_conversation = True
                    
                    # For tool-specific responses we'll directly run the tools
                    if len(pending_tools) == 1:
                        # If only one tool is pending, we'll call it directly
                        debug_print(f"Directly executing tool: {pending_tools[0]}")
                        modified_input = f"Please run the {pending_tools[0].replace('_', ' ')} tool and tell me the results."
                    elif len(pending_tools) == 2:
                        # If two tools are pending, we'll call both with comparison
                        debug_print(f"Directly comparing tools: {pending_tools}")
                        tool_names = " and ".join([t.replace("_", " ") for t in pending_tools])
                        modified_input = f"Please run the {tool_names} tools and compare the results."
                    else:
                        # If multiple tools, create a more general request
                        tool_names = ", ".join([t.replace("_", " ") for t in pending_tools])
                        modified_input = f"Yes, please run {tool_names} as you suggested in your previous message."
                    
                    debug_print(f"Modified input: '{modified_input}'")
                    
                elif any(user_input_lower == resp for resp in negative_responses):
                    # This is a negative response - we should acknowledge it but not run any tools
                    # Just pass through the original input with context
                    modified_input = f"No, I don't want to {', '.join([t.replace('_', ' ') for t in pending_tools])}. Please continue."
                    debug_print(f"Modified negative input: '{modified_input}'")
                    
            # Add the last question to the context even if it's not a yes/no response
            # This helps maintain conversation context
            elif last_question and user_input_lower not in ["help", "/help", "exit", "/exit", "quit", "/quit"]:
                # Add context from the last question to ensure continuity
                question_summary = last_question.split("\n")[0][:50]  # Take first line, truncate if too long
                modified_input = f"Regarding your question about '{question_summary}', my response is: {user_input}"
                debug_print(f"Added context to user input: '{modified_input}'")
                    
        # Prepare initial state
        initial_state = State(
            messages=[HumanMessage(content=modified_input)],
            intermediate_steps=[],  # Ensure intermediate_steps is initialized as empty list
            last_question=None,  # Reset the last question
            pending_tools=[]  # Reset pending tools
        )
        
        final_state: Optional[Dict[str, Any]] = None
        try:
            # Invoke the graph
            # Set recursion_limit slightly higher to allow the graph to reach END naturally
            debug_print("Invoking graph...")
            final_state = self.graph.invoke(initial_state, config={"recursion_limit": self.max_iterations + 5})
            debug_print(f"Graph invocation complete. Final state type: {type(final_state)}")
        except Exception as e:
            error_str = str(e)
            error_print(f"Error invoking graph: {error_str}")
            
            if "Parsing LLM output produced both a final answer and a parse-able action" in error_str:
                # This error is now handled by our custom parser, but provide a helpful message
                # if the error somehow propagates up to here
                return {
                    "response": "I noticed you asked about something that required me to both provide information and take an action. Let me try that again more carefully.",
                    "intermediate_steps": []
                }
            else:
                # Other errors
                return {
                    "response": f"An error occurred during graph processing: {error_str}",
                    "intermediate_steps": []
                }

        final_response_message = "No response generated."
        final_intermediate_steps = []

        if final_state: # Check if final_state is not None and is a dict (implicitly checked by .get)
            debug_print(f"Processing final state: {final_state}")
            messages = final_state.get('messages', []) # Use .get() for safety
            if messages:
                 # Ensure messages is a list before proceeding
                 if isinstance(messages, list):
                     ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
                     if ai_messages:
                         final_response_message = ai_messages[-1].content
                 else:
                     warning_print(f"Expected 'messages' to be a list, but got {type(messages)}")
            else:
                 debug_print("No 'messages' key found in final state or it was empty.")

            final_intermediate_steps = final_state.get('intermediate_steps', []) # Use .get()
            debug_print(f"Final response: {final_response_message}")
            debug_print(f"Final intermediate steps: {final_intermediate_steps}")

            # Save context only if processing was potentially successful (even if no response generated)
            try:
                debug_print("Saving context to memory...")
                
                # Save the conversation state with last_question and pending_tools
                last_state = {
                    "last_question": final_state.get("last_question"),
                    "pending_tools": final_state.get("pending_tools", [])
                }
                
                # Save to LangChain memory
                self.langchain_memory.save_context(
                    {"input": user_input},
                    {"output": final_response_message}
                )
                
                # Save to our custom memory system
                self.memory.add_interaction(user_input, final_response_message)
                
                # Store last state in the direct memory cache
                # We're using the cache system built into ChatbotMemory instead of the MemorySaver put_tuple
                self.memory.update_cache("last_state", last_state)
                
                # Save the cache
                self.memory.save_cache()
                
                debug_print(f"Context saved with last_question: {last_state['last_question'] is not None}")
                if last_state["last_question"]:
                    debug_print(f"Pending tools: {last_state['pending_tools']}")
            except Exception as e:
                 error_print(f"Error saving context to memory: {e}")

        else:
             warning_print("final_state was None after graph invocation.")

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