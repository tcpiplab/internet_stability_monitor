import os
import glob
import requests
import json
from datetime import datetime
import report_source_location
import subprocess
from tts_utils import speak_text

# Ensure the logging directory exists
os.makedirs("/tmp/internet_stability_monitor_logs", exist_ok=True)

# Directory where logs are stored
LOG_DIR = "/tmp/internet_stability_monitor_logs"

# Function to find the most recent log file
def get_latest_log_file(log_dir):
    list_of_files = glob.glob(os.path.join(log_dir, "internet_stability_log_*"))
    if not list_of_files:
        return None
    
    # Print the name of the latest file we found
    print(f"Latest log file: {max(list_of_files, key=os.path.getctime)}")

    # If the latest log file is 0 bytes, delete it and return None
    if  os.path.getsize(max(list_of_files, key=os.path.getctime)) == 0:

        print("Latest log file is empty, deleting and returning None.")
        speak_text("Latest log file is empty, deleting and returning None.")

        print("Otherwise it would cause me to hallucinate extensively when reading out my summary report.")
        speak_text("Otherwise it would cause me to hallucinate extensively when reading out my summary report.")

        os.remove(max(list_of_files, key=os.path.getctime))

        return None

    else:
        return max(list_of_files, key=os.path.getctime)


# Function to send the log content to the Ollama model
def summarize_log(log_content):

    location_string = report_source_location.main()

    system_prompt = f"""You are a 1950s British radio news reporter named Alfred Boddington-Smythe reporting live 
                        from {location_string} tasked with analyzing log entries from Python scripts that 
                        monitor critical remote endpoints providing vital internet infrastructure services. 
                        Your role is to first introduce yourself and the location you are reporting from, and then 
                        to summarize these logs into a concise, short news-update style story,  
                        reporting on the overall health of the internet, paying special attention to any servers 
                        or services that were unreachable, timed-out, or were not available. 
                        You report in a style suitable for a classic radio 
                        news update segment. You do not use bullet points or numbering, and you do not give advice. 
                        You provide only a factual summary based on the log content. The 
                        audience listening to your news update is extremely knowledgeable about the
                        subject matter. You do not need to explain or define anything technical to them."""

    user_prompt = f"""User: Here is the contents of the entire log file from a collection of network diagnostic 
                    scripts that check the reachability and response times of various internet services. 
                    You will summarize the log file but you MUST NOT hallucinate or make up any facts or you 
                    will be penalized. You will then read your summary 
                    as a breaking news update that you will read live on-air after identifying yourself and 
                    your location: 
                    \n\nAssistant: \"Hello, this is Alfred Boddington-Smythe reporting 
                    live from {location_string} with an update on the stability of the internet's underlying 
                    infrastructure...\"\n####\n{log_content}\n\n####"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            headers={"Content-Type": "application/json"},
            data=json.dumps({
                "model": "mistral",
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": False,
                "max_tokens": 70,
                "temperature": 0.2,
            }),
        )

        if response.status_code != 200:
            print(f"Failed to get summary: {response.status_code} - {response.text}")
            raise Exception(f"Error communicating with Ollama: {response.status_code} - {response.text}")

        # Extracting the "response" field from the JSON response
        response_json = response.json()
        summary = response_json.get("response", "")

        # Check if summary is empty
        if not summary:
            raise Exception("Summary was empty")

        speak_text( "Preparing the summary of the testing outcomes. This will take a moment.")
        return summary

    except Exception as e:

        # If "[Errno 61] Connection refused" is in the error message, it's a connection issue
        if "Connection refused" in str(e):
            print("The connection to the local Ollama API was refused. You probably just need to start it.")
            return (f"There was an error while trying to get the local Ollama API to create a summary. "
                    f"Please check the logs for more information.")

        else:
            # For other types of errors, print the error message
            print(f"An error occurred when trying to get Ollama to create a summary: {e}")



        return (f"There was an error while trying to get the local Ollama API to create a summary. "
                f"Please check the logs for more information.")


def read_summary_with_tts(summary_file, location_string):

    #  Read the content of the summary file
    with open(summary_file, "r") as file:
        summary_text = file.read()

    # Use speak_text instead of /usr/bin/say on Windows and Linux
    try:
        speak_text(f"Hello, this is Alfred Boddington-Smythe reporting live from {location_string}")
        speak_text(summary_text)
        print(f"Successfully read the content of {summary_file}")
    except Exception as e:
        print(f"An error occurred while running the speak_text command: {e}")




# Main function to process the log file
def main():
    # Get the latest log file
    latest_log_file = get_latest_log_file(LOG_DIR)
    if not latest_log_file:
        print("No log file found.")
        return

    # Read the content of the log file
    with open(latest_log_file, "r") as file:
        log_content = file.read()

    # Get the summary using Ollama
    try:
        summary = summarize_log(log_content)
    except Exception as e:
        print(f"Failed to get summary: {e}")
        return

    # Save the summary to a file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    summary_file = f"/tmp/internet_stability_monitor_logs/internet_stability_summary_{timestamp}.txt"
    with open(summary_file, "w") as file:
        file.write(summary)

    print(f"Summary saved to: {summary_file}")

    location_string = report_source_location.main()

    read_summary_with_tts(summary_file, location_string)


if __name__ == "__main__":
    main()