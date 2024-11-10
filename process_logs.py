import os
import glob
import requests
import json
from datetime import datetime
import report_source_location
import subprocess

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
    return max(list_of_files, key=os.path.getctime)

# Function to send the log content to the Ollama model
def summarize_log(log_content):
    # prompt = f"Please read the following internet stability log and summarize it in the style of a concise news radio update: {log_content}"

    # prompt = f"""You will be provided with log entries at the end of these instructions. \
    #             The logs are the result of several Python scripts running checks against critical, \
    #             remote endpoints that are providing vital internet infrastructure services. \
    #             Your job is to write a very, very concise and short "news update" style news story \
    #             reporting on the overall health of the internet based on what you see in those logs. \
    #             The style of what you write will be a short paragraph that could be read on the air \
    #             during a radio news update segment. Do not use bullet points or numbering. Do not use \
    #             Markdown. Just summarize the overall status of the internet infrastructure based soley \
    #             on the logs provided at the end of these instructions. Focus only on the key outcomes \
    #             of the tests, indicating whether the services tested are operational or are experiencing \
    #             issues. Avoid mentioning the names of the scripts, redundant descriptions, or any \
    #             superfluous details. For each category (IMAP, SMTP, CA Endpoints, CDNs, DNS Resolvers, \
    #             IXPs, etc.), if there appears to have been any connectivity problems or errors, then \
    #             you should provide a very concise status that is one, or at most two, sentences for \
    #             that entire category, followed by a brief \
    #             list of the affected hostnames. If a service category seems to be 100% reachable and \
    #             online, then do not bother to report on that service. The summary should focus on \
    #             problems and errors. Keep the news story direct, concise, and \
    #             high-level, emphasizing overall internet infrastructure stability. The tone and style \
    #             should be in the style of a concise news radio update. Do not talk about the log \
    #             entries themselves or what context or source you think they may have come from \
    #             originally. Just report on the percentage of reachable/online/normal checks you \
    #             read about in the logs. Here is the contents of the \
    #             entire log file for you to summarize: \n```\n{log_content}\n```\n"""

    # prompt = f"""You will be provided with log entries at the end of these instructions. \
    #             The logs are the result of several Python scripts running checks against critical, \
    #             remote endpoints that are providing vital internet infrastructure services. \
    #             Your job is to write a very, very concise and short "news update" style news story \
    #             reporting on the overall health of the internet based on what you see in those logs. \
    #             The style of what you write will be a short paragraph that could be read on the air \
    #             during a radio news update segment. Do not use bullet points or numbering. Do not give advice. Here is the contents of the \
    #             entire log file for you to summarize as a breaking news update: \n```\n{log_content}\n```\n"""

    location_string = report_source_location.main()

    # system_prompt = f"""You are a news writer reporting from {location_string} tasked with analyzing log entries from Python scripts that \
    #                 monitor critical remote endpoints providing vital internet infrastructure services. \
    #                 Your role is to summarize these logs into a concise, short "news update" style story \
    #                 reporting on the overall health of the internet. Write in a style suitable for a radio \
    #                 news update segment. Do not use bullet points or numbering, and do not give advice. \
    #                 Provide only a factual summary based on the log content. And remember that the \
    #                 audience for the news update that you will write is extremely knowledgeable about the\
    #                 subject matter. So you do not need to explain or define anything technical to them."""

    system_prompt = f"""I am a 1950s British radio news reporter named Alfred Boddington-Smythe reporting live \
                    from {location_string} tasked with analyzing log entries from Python scripts that \
                    monitor critical remote endpoints providing vital internet infrastructure services. \
                    
                    My role is to first introduce myself and the location I am reporting from, and then \
                    to summarize these logs into a concise, short "news update" style story \
                    reporting on the overall health of the internet, paying special attention to any servers \
                    or services that were unreachable, timed-out, or were not available. \
                    I will report in a style suitable for a classic radio \
                    news update segment. I do not use bullet points or numbering, and I do not give advice. \
                    I provide only a factual summary based on the log content. The \
                    audience listening to my news update is extremely knowledgeable about the\
                    subject matter. I do not need to explain or define anything technical to them."""

    # user_prompt = f"""Here is the contents of the entire log file for you to summarize as a breaking news \
    #                 update:\n\n####\n{log_content}"""

    user_prompt = f"""User: Here is the contents of the entire log file for you to summarize as a breaking news \
                    update that you will read live on-air after identifying yourself and your location: \
                    \n\n####\n{log_content}\n\n####\nAssistant: \"Hello, this is Alfred Boddington-Smythe reporting \
                    live from {location_string} with an update on the stability of the internet\'s underlying \
                    infrastructure...\""""



    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            headers={"Content-Type": "application/json"},
            data=json.dumps({
                # "model": "mistrallite",
                "model": "mistral",
                # "model": "llama3.1:latest",
                # "model": "alfred",
                # "model": "qwen2.5",
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": False,
            }),
        )


    # try:
    #     response = requests.post(
    #         "http://localhost:11434/api/generate",
    #         headers={"Content-Type": "application/json"},
    #         data=json.dumps({
    #             "model": "mistrallite",  # Specify the model here
    #             "prompt": prompt,
    #             "stream": False,
    #         }),
    #     )

        if response.status_code != 200:
            print(f"Failed to get summary: {response.status_code} - {response.text}")
            raise Exception(f"Error communicating with Ollama: {response.status_code} - {response.text}")

        # Extracting the "response" field from the JSON response
        response_json = response.json()
        summary = response_json.get("response", "")

        # Check if summary is empty
        if not summary:
            raise Exception("Summary was empty")

        return summary

    except Exception as e:
        print(f"An error occurred: {e}")
        return ""


def read_summary_with_tts(summary_file, location_string):
    # Construct the macos_tts_command as a list of arguments
    macos_tts_introduction = [
        "/usr/bin/say",
        "--voice", "Jamie",
        "--quality", "127",
        f"Hello, this is Alfred Boddington-Smythe reporting live from {location_string}"
    ]

    macos_tts_command = [
        "/usr/bin/say",
        "--voice", "Jamie",
        "--quality", "127",
        "--input-file", summary_file
    ]
    try:
        subprocess.run(macos_tts_introduction, check=True)
        # Run the macos_tts_command
        subprocess.run(macos_tts_command, check=True)
        print(f"Successfully read the content of {summary_file}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the macos_tts_command: {e}")
    except FileNotFoundError:
        print("The 'say' macos_tts_command was not found. Make sure you're running this on macOS.")



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