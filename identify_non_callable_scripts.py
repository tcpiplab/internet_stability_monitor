import os

# Step 1: List all Python scripts with "check" in their names
check_scripts = [f for f in os.listdir('.') if f.endswith('.py') and 'check' in f]

# Step 2: Identify callable tools in chatbot mode
callable_tools = []
with open('chat_langchain_ollama_agent.py', 'r') as file:
    for line in file:
        if 'import' in line and 'check' in line:
            # Extract the script name from the import statement
            script_name = line.split('import')[1].strip().split(' ')[0]
            callable_tools.append(script_name + '.py')

# Step 3: Compare the lists
non_callable_scripts = set(check_scripts) - set(callable_tools)

print("Python scripts with 'check' in their names that are not callable as tools:")
for script in non_callable_scripts:
    print(f"- {script}")
