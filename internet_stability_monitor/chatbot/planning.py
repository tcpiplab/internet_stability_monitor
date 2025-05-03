"""
Planning system for the chatbot.

This module handles the planning and synthesis of multi-step operations
for complex network diagnostics queries.
"""

from typing import Dict, Any, List
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama

SYNTHESIS_PROMPT = """You are a network diagnostics expert. Analyze the following information and provide a very concise, natural, informative response.

Query: {query}

Current Results:
{current_results}

Recent History:
{history}

Previous Results:
{previous_results}

Provide a clear, concise, and natural response that directly answers the user's question. 
Do not over-explain. The user is very technical and will understand the information you provide.

Response:"""

class PlanningSystem:
    """Handles planning and synthesis for complex queries."""
    
    def __init__(self):
        """Initialize the planning system."""
        self.current_plan = None
        self.current_results = []
        self.llm = ChatOllama(model="qwen2.5")
        self.result_history = []
    
    def create_plan(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a plan for addressing the user's query.
        
        Args:
            query: The user's question or request
            context: Current conversation context and memory
            
        Returns:
            Dict containing the plan details
        """
        # Store the context for later synthesis
        self.current_context = context
        
        # Analyze the query to determine required steps
        plan = {
            "query": query,
            "steps": [],
            "required_tools": [],
            "reasoning": "",
            "needs_tools": False
        }
        
        # Basic query analysis
        query_lower = query.lower()
        
        # System information queries
        if any(word in query_lower for word in ["os", "system", "operating system"]):
            plan["steps"].append("Get operating system information")
            plan["required_tools"].append("get_os")
            plan["needs_tools"] = True
            
        # NAT and network translation queries
        elif "nat" in query_lower or any(word in query_lower for word in ["network address translation", "port forwarding"]):
            plan["steps"].extend([
                "Get local IP information",
                "Get external IP information",
                "Compare IPs to determine NAT status"
            ])
            plan["required_tools"].extend(["get_local_ip", "get_external_ip"])
            plan["needs_tools"] = True
            
        # Process status queries
        elif any(word in query_lower for word in ["ollama", "process", "running"]):
            plan["steps"].append("Check Ollama process status")
            plan["required_tools"].append("check_ollama")
            plan["needs_tools"] = True
            
        # Time and timezone queries
        elif any(word in query_lower for word in ["time", "date", "timezone"]):
            plan["steps"].append("Get local time and timezone information")
            plan["required_tools"].append("get_local_date_time_and_timezone")
            plan["needs_tools"] = True
            
        # Location queries
        elif "location" in query_lower or "where" in query_lower:
            plan["steps"].append("Get location information")
            plan["required_tools"].append("get_isp_location")
            plan["needs_tools"] = True
            
        # Network connectivity checks
        elif any(word in query_lower for word in ["internet", "connection", "online", "connectivity"]):
            plan["steps"].append("Verify internet connectivity")
            plan["required_tools"].append("check_internet_connection")
            plan["needs_tools"] = True
            
        # DNS queries
        elif any(word in query_lower for word in [" dns", "resolver", "nameserver"]):
            plan["steps"].append("Check DNS resolver status")
            plan["required_tools"].append("check_dns_resolvers")
            plan["needs_tools"] = True
            
        # Website checks
        elif any(word in query_lower for word in ["website", "site", "web", "url"]):
            plan["steps"].append("Check website reachability")
            plan["required_tools"].append("check_websites")
            plan["needs_tools"] = True
            
        # IP address queries
        elif any(word in query_lower for word in ["ip", "address"]):
            if "external" in query_lower or "public" in query_lower:
                plan["steps"].append("Get external IP information")
                plan["required_tools"].extend(["get_external_ip", "get_isp_location"])
            else:
                plan["steps"].append("Get local IP information")
                plan["required_tools"].append("get_local_ip")
            plan["needs_tools"] = True
            
        # Network layer checks
        elif "layer" in query_lower:
            if "two" in query_lower or "2" in query_lower:
                plan["steps"].append("Check local network layer 2 status")
                plan["required_tools"].append("check_local_layer_two_network")
            elif "three" in query_lower or "3" in query_lower:
                plan["steps"].append("Check network layer 3 connectivity")
                plan["required_tools"].append("check_layer_three_network")
            plan["needs_tools"] = True
            
        # Speed test queries
        elif any(word in query_lower for word in ["speed", "performance", "bandwidth"]):
            plan["steps"].append("Run network speed test")
            plan["required_tools"].append("run_mac_speed_test")
            plan["needs_tools"] = True
            
        # Infrastructure checks
        elif any(word in query_lower for word in ["cdn", "cdns", "content delivery"]):
            plan["steps"].append("Check CDN reachability")
            plan["required_tools"].append("check_cdn_reachability")
            plan["needs_tools"] = True
        elif "tls" in query_lower or "certificate" in query_lower:
            plan["steps"].append("Check TLS CA servers")
            plan["required_tools"].append("check_tls_ca_servers")
            plan["needs_tools"] = True
        elif "whois" in query_lower:
            plan["steps"].append("Check WHOIS servers")
            plan["required_tools"].append("check_whois_servers")
            plan["needs_tools"] = True
        elif "smtp" in query_lower or "mail" in query_lower:
            plan["steps"].append("Check SMTP servers")
            plan["required_tools"].append("check_smtp_servers")
            plan["needs_tools"] = True
            
        # Tool name direct matches (fallback)
        else:
            # Check if any tool name is directly mentioned
            tool_names = [
                "get_os", "check_ollama", "get_local_ip", "check_internet_connection",
                "check_layer_three_network", "get_external_ip", "check_external_ip_change",
                "get_isp_location", "check_dns_resolvers", "check_websites",
                "check_dns_root_servers_reachability", "check_local_layer_two_network",
                "ping_target", "check_tls_ca_servers", "check_whois_servers",
                "check_cdn_reachability", "run_mac_speed_test", "check_smtp_servers",
                "check_cache", "get_local_date_time_and_timezone"
            ]
            
            for tool in tool_names:
                if tool.lower().replace("_", " ") in query_lower:
                    plan["steps"].append(f"Run {tool}")
                    plan["required_tools"].append(tool)
                    plan["needs_tools"] = True
                    break
        
        # Add reasoning about the plan
        if plan["steps"]:
            plan["reasoning"] = f"Based on the query '{query}', I'll need to: " + \
                              ", then ".join(plan["steps"])
        else:
            plan["reasoning"] = "No specific diagnostics needed for this query."
        
        self.current_plan = plan
        return plan
    
    def evaluate_tool_needs(self, plan: Dict[str, Any]) -> List[str]:
        """Determine which tools are needed for the plan.
        
        Args:
            plan: The current execution plan
            
        Returns:
            List of required tool names
        """
        return plan.get("required_tools", [])
    
    def synthesize_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """Synthesize tool results into a coherent response.
        
        Args:
            results: List of tool execution results
            query: The original user query
            
        Returns:
            Synthesized response string
        """
        if not results:
            return "I wasn't able to gather any diagnostic information."
        
        # Store current results for history
        self.current_results = results
        self.result_history.append({
            "query": query,
            "results": results,
            "plan": self.current_plan
        })
        
        # Keep only last 5 interactions for context
        self.result_history = self.result_history[-5:]
        
        # Format current results
        current_results_str = "\n".join(
            f"{r['tool']}: {r['result']}" for r in results
        )
        
        # Format history and previous results
        history = []
        previous_results = []
        for past in self.result_history[:-1]:  # Exclude current interaction
            history.append(f"Query: {past['query']}")
            for r in past['results']:
                previous_results.append(f"{r['tool']}: {r['result']}")
        
        # Prepare the prompt
        prompt = SYNTHESIS_PROMPT.format(
            query=query,
            current_results=current_results_str,
            history="\n".join(history) if history else "No relevant history",
            previous_results="\n".join(previous_results) if previous_results else "No previous results"
        )
        
        try:
            # Get LLM response
            response = self.llm.invoke(prompt).content
            
            # Add plan context if available
            if self.current_plan and self.current_plan["reasoning"]:
                return f"{self.current_plan['reasoning']}\n\n{response}"
            
            return response
            
        except Exception as e:
            # Fallback to basic response if LLM fails
            response_parts = []
            if self.current_plan and self.current_plan["reasoning"]:
                response_parts.append(self.current_plan["reasoning"])
            
            for result in results:
                if "tool" in result and "result" in result:
                    response_parts.append(f"\n{result['tool']} showed: {result['result']}")
            
            return " ".join(response_parts)
    
    def get_current_plan(self) -> Dict[str, Any]:
        """Get the current execution plan."""
        return self.current_plan or {}
    
    def get_current_results(self) -> List[Dict[str, Any]]:
        """Get the current tool execution results."""
        return self.current_results

    def route_agent(self, state: State) -> str:
        """Determine the next step after the agent node."""
        if state.current_tool:
            # Check recursion limit before executing tool
            if len(state.intermediate_steps) >= self.max_iterations:
                 # Force end if max iterations reached, add a message
                 # Note: Modifying state directly here might not be ideal,
                 # consider adding the message in the agent_node or main loop
                 state.messages.append(AIMessage(content=f"Reached max iterations ({self.max_iterations}). Finishing."))
                 return END
            return "tool"
        else:
            # Agent generated AgentFinish, go to END
            return END