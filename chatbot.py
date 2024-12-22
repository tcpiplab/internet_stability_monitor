import subprocess
import os
from flask import Flask, request, jsonify, render_template_string
from transformers import pipeline

app = Flask(__name__)

# List of available scripts
scripts = [
    "os_utils.py",
    "check_external_ip.py",
    "mac_speed_test.py",
    "resolver_check.py",
    "whois_check.py",
    "dns_check.py",
    "ntp_check.py",
    "web_check.py",
    "cloud_check.py",
    "imap_check.py",
    "smtp_check.py",
    "tls_ca_check.py",
    "cdn_check.py",
    "ixp_check.py",
]

# Load a local LLM model
llm = pipeline("text-generation", model="gpt2", framework="pt")

def map_query_to_scripts(query):
    if "dns" in query.lower():
        return ["dns_check.py", "resolver_check.py"]
    # Add more mappings as needed
    return []

@app.route('/')
def index():
    return render_template_string('''
        <!doctype html>
        <title>Chatbot</title>
        <h1>Chat with the Chatbot</h1>
        <form action="/run_script" method="post">
            <label for="query">Enter your query:</label><br>
            <input type="text" id="query" name="query"><br><br>
            <input type="submit" value="Submit">
        </form>
    ''')

@app.route('/run_script', methods=['POST'])
def run_script():
    query = request.form.get('query')
    silent = request.form.get('silent', False)

    script_names = map_query_to_scripts(query)
    if not script_names:
        return jsonify({"error": "No matching scripts found"}), 404

    results = {}
    for script_name in script_names:
        if script_name not in scripts:
            continue

        try:
            if silent:
                result = subprocess.run(
                    ["python3", script_name, "--silent"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            else:
                result = subprocess.run(
                    ["python3", script_name],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            results[script_name] = result.stdout

        except subprocess.CalledProcessError as e:
            results[script_name] = e.stderr

    # Summarize the results using the LLM
    summary = llm(" ".join(results.values()), max_new_tokens=50, truncation=True)[0]['generated_text']

    return jsonify({"output": results, "summary": summary}), 200

@app.route('/list_scripts', methods=['GET'])
def list_scripts():
    return jsonify({"scripts": scripts}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555)