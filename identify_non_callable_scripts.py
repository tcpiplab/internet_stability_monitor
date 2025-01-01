#!/usr/bin/env python3
import os

# Step 1: List all Python scripts with "check" in their names
check_scripts = [f for f in os.listdir('.') if f.endswith('.py') and 'check' in f]

# Step 2: Identify callable tools in chatbot mode
callable_tools = set()

# Check for tool definitions in chat_langchain_ollama_agent.py
with open('chat_langchain_ollama_agent.py', 'r') as file:
    for line in file:
        if '@tool' in line:
            # Read the next line to get the function name
            next_line = next(file).strip()
            if 'def ' in next_line:
                # Extract the function name
                function_name = next_line.split('def ')[1].split('(')[0]
                # Convert function name to script name
                script_name = function_name.replace('_', '') + '.py'
                callable_tools.add(script_name)

# Check for imports in instability.py
with open('instability.py', 'r') as file:
    for line in file:
        if 'import' in line and 'check' in line:
            # Extract the script name from the import statement
            script_name = line.split('import')[1].strip().split(' ')[0] + '.py'
            callable_tools.add(script_name)

# Step 3: Compare the lists
non_callable_scripts = set(check_scripts) - callable_tools

print("Python scripts with 'check' in their names that are not callable as tools:")
for script in non_callable_scripts:
    print(f"- {script}")
