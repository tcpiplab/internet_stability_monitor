import subprocess
import os
from flask import Flask, request, jsonify, render_template_string
from transformers import pipeline

app = Flask(__name__)

# List of available scripts and their descriptions
scripts = {
    "os_utils.py": "Utility functions for operating system tasks.",
    "check_external_ip.py": "Checks the external IP address of the system.",
    "mac_speed_test.py": "Performs a speed test on macOS.",
    "resolver_check.py": "Checks the reachability of several popular resolver servers.",
    "whois_check.py": "Performs a WHOIS lookup for a given domain.",
    "dns_check.py": "Checks the reachability of the DNS root servers.",
    "ntp_check.py": "Checks the reachability of NTP servers.",
    "web_check.py": "Checks the availability of a web server.",
    "cloud_check.py": "Checks the status of cloud services.",
    "imap_check.py": "Checks the reachability of IMAP servers.",
    "smtp_check.py": "Checks the reachability of SMTP servers.",
    "tls_ca_check.py": "Checks the validity of TLS certificates.",
    "cdn_check.py": "Checks the status of CDN services.",
    "ixp_check.py": "Checks the status of Internet Exchange Points.",
}

# Load a local LLM model
llm = pipeline("text-generation", model="gpt2", framework="pt")

def map_query_to_scripts(query):
    query = query.lower()
    if "dns" in query:
        return ["dns_check.py", "resolver_check.py"]
    elif "list scripts" in query:
        return ["list_scripts"]
    elif "describe" in query:
        script_name = query.replace("describe", "").strip()
        return [script_name] if script_name in scripts else []
    elif "external ip" in query or "ip address" in query:
        return ["check_external_ip.py"]
    elif "speed test" in query or "speed" in query:
        return ["mac_speed_test.py"]
    elif "whois" in query:
        return ["whois_check.py"]
    elif "ntp" in query or "time server" in query:
        return ["ntp_check.py"]
    elif "web" in query or "website" in query:
        return ["web_check.py"]
    elif "cloud" in query:
        return ["cloud_check.py"]
    elif "imap" in query or "email" in query:
        return ["imap_check.py"]
    elif "smtp" in query or "mail server" in query:
        return ["smtp_check.py"]
    elif "tls" in query or "certificate" in query:
        return ["tls_ca_check.py"]
    elif "cdn" in query:
        return ["cdn_check.py"]
    elif "ixp" in query or "exchange point" in query:
        return ["ixp_check.py"]
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

    if script_names == ["list_scripts"]:
        return jsonify({"scripts": list(scripts.keys())}), 200

    # if script_names[0] in scripts:
    #     return jsonify({"description": scripts[script_names[0]]}), 200

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
    return jsonify({"scripts": list(scripts.keys())}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555)