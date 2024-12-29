import subprocess
from langchain.tools import Tool

def run_script(script_name: str) -> str:
    # Generic function to run a Python script and capture its output
    result = subprocess.run(["python3", script_name], capture_output=True, text=True)
    if result.returncode != 0:
        return f"Error running {script_name}: {result.stderr}"
    return result.stdout.strip()

def run_all_scripts() -> str:
    return run_script("run_all.py")

def check_dns() -> str:
    return run_script("dns_check.py")

def check_ntp() -> str:
    return run_script("ntp_check.py")

def get_external_ip() -> str:
    return run_script("check_external_ip.py")

# Create LangChain tool objects
run_all_tool = Tool(
    name="run_all",
    description="Run all scripts (DNS, NTP, IP checks).",
    func=lambda: run_all_scripts()
)

dns_tool = Tool(
    name="check_dns",
    description="Checks if DNS root servers are reachable.",
    func=lambda: check_dns()
)

ntp_tool = Tool(
    name="check_ntp",
    description="Checks if NTP servers are responding.",
    func=lambda: check_ntp()
)

ip_tool = Tool(
    name="get_external_ip",
    description="Gets the home's external IP address.",
    func=lambda: get_external_ip()
)

tools = [run_all_tool, dns_tool, ntp_tool, ip_tool]