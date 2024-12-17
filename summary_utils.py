# summary_utils.py

def add_to_combined_summaries(summary):
    with open("/tmp/internet_stability_monitor_logs/combined_summaries.txt", "a") as file:
        file.write(summary + "\n")