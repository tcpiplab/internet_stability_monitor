# summary_utils.py
import os


def add_to_combined_summaries(summary):

    tmp_log_dir = "/tmp/internet_stability_monitor_logs"
    combined_summaries_file = f"{tmp_log_dir}/combined_summaries.txt"

    # Create the directory if it does not exist
    if not os.path.exists(tmp_log_dir):
        os.makedirs(tmp_log_dir)

    # If the file does not exist, create it and write the summary
    if not os.path.exists(combined_summaries_file):
        with open(combined_summaries_file, "w") as file:
            file.write(summary + "\n")

    # If the file already exists, append the summary
    else:
        with open(combined_summaries_file, "a") as file:
            file.write(summary + "\n")
